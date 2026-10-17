"""Every person under people/ is a person.json the schema accepts, in a folder named by its id, and every source of
theirs, and every download of their kit, agrees with it on name, birth date and gender except where it declares the
difference."""

import json
import xml.etree.ElementTree as ElementTree

import pytest
from jsonschema import Draft202012Validator
from rdflib import Graph, Namespace
from rdflib.namespace import FOAF

from contract import KITS, ROOT

PEOPLE = ROOT / "people"
SCHEMA = json.loads((PEOPLE / "person.schema.json").read_text(encoding="utf-8"))
PIM = Namespace("http://www.w3.org/ns/pim/space#")
HL7 = {"cda": "urn:hl7-org:v3"}
CDA_GENDER = {"F": "female", "M": "male", "UN": "unknown"}
FIELDS = ("name", "birthDate", "gender")


def people():
    return sorted(path for path in PEOPLE.iterdir() if path.is_dir())


def official(names):
    return next((name for name in names if name.get("use") == "official"), names[0]) if names else None


def from_fhir(bundle):
    """Each Patient version in a FHIR Bundle, as (its id, its name, birth date and gender where it states them)."""
    patients = [entry["resource"] for entry in bundle.get("entry", [])
                if entry.get("resource", {}).get("resourceType") == "Patient"]
    for patient in patients:
        name = official(patient.get("name", []))
        stated = {"name": name and {"family": name.get("family"), "given": name.get("given", [])},
                  "birthDate": patient.get("birthDate"), "gender": patient.get("gender")}
        yield patient.get("id"), {field: value for field, value in stated.items() if value is not None}


def from_cda(path):
    """A C-CDA document's patient, as (its record target's id, its name, birth date and gender)."""
    role = header(path, "recordTarget").find("cda:patientRole", HL7)
    patient = role.find("cda:patient", HL7)
    names = patient.findall("cda:name", HL7)
    stated = {}
    if names:
        name = next((name for name in names if name.get("use") == "L"), names[0])
        stated["name"] = {"family": name.findtext("cda:family", namespaces=HL7),
                          "given": [given.text for given in name.findall("cda:given", HL7)]}
    birth = patient.find("cda:birthTime", HL7)
    if birth is not None and birth.get("value"):
        stated["birthDate"] = day(birth.get("value"))
    gender = patient.find("cda:administrativeGenderCode", HL7)
    if gender is not None and gender.get("code") in CDA_GENDER:
        stated["gender"] = CDA_GENDER[gender.get("code")]
    return role.find("cda:id", HL7).get("extension"), stated


def header(path, element):
    """A C-CDA header element, read as soon as it ends, so a download cut off later in its body is still read."""
    parser = ElementTree.XMLPullParser(events=("end",))
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        parser.feed(line)
        for _, found in parser.read_events():
            if found.tag == f"{{{HL7['cda']}}}{element}":
                return found
    raise AssertionError(f"{path} has no {element}")


def day(timestamp):
    return f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"


def shown(value):
    return " ".join([*value["given"], value["family"]]) if isinstance(value, dict) else value


def sources(folder, root):
    """Each source of a person, as (its name, the file, the patients it states): their own sources, then their kit's
    downloads."""
    for source in sorted(path for path in (folder / "sources").glob("*") if path.is_dir()):
        if (source / "fhir.json").is_file():
            path = source / "fhir.json"
            yield source.name, path, list(from_fhir(json.loads(path.read_text(encoding="utf-8"))))
        for path in sorted((source / "ccda").glob("*.xml")):
            yield source.name, path, [from_cda(path)]
    kit = json.loads((folder / "person.json").read_text(encoding="utf-8")).get("kit")
    for downloads in sorted((root / kit / "scripted-input").glob("*/downloads")) if kit else []:
        for path in sorted(downloads.glob("*/bundle.json")):
            yield path.parent.name, path, list(from_fhir(json.loads(path.read_text(encoding="utf-8"))))
        for path in sorted(downloads.glob("*.xml")):
            yield path.stem, path, [from_cda(path)]


def refusals(folder, root=ROOT):
    """Why a person folder is refused, as (where, reason): nothing when it is whole."""
    where = lambda path: path.relative_to(root).as_posix()
    card = folder / "person.json"
    try:
        person = json.loads(card.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [(where(card), "is not there")]
    except ValueError as error:
        return [(where(card), f"is not JSON: {error}")]
    found = [(where(card), error.message) for error in Draft202012Validator(SCHEMA).iter_errors(person)]
    if found:
        return found
    if person["id"] != folder.name:
        found.append((where(card), f"has the id {person['id']}, but its folder is {folder.name}"))
    declared = {(d["source"], d["field"]): d["value"] for d in person.get("differences", [])}
    seen = set()
    for source, path, patients in sources(folder, root):
        if not patients:
            found.append((where(path), "holds no Patient"))
        elif len({pid for pid, _ in patients}) > 1:
            found.append((where(path), f"holds {len({pid for pid, _ in patients})} Patients: a source holds one"))
        for pid, stated in patients:
            for field, value in stated.items():
                if value == person[field]:
                    continue
                if declared.get((source, field)) == value:
                    seen.add((source, field))
                else:
                    found.append((where(path), f"Patient {pid} says {field} {shown(value)}, "
                                               f"person.json says {shown(person[field])}"))
    found += [(where(card), f"declares a difference in {field} at {source} that its Patient does not show")
              for source, field in sorted(set(declared) - seen)]
    if "kit" in person and not (root / person["kit"]).is_dir():
        found.append((where(card), f"names the kit {person['kit']}, which is not there"))
    elif "subject" in person:
        rows = root / person["kit"] / "scripted-input" / "people.ttl"
        graph = Graph().parse(rows)
        iri = next(graph.subjects(FOAF.name, None), None)
        row = {"iri": iri, "name": graph.value(iri, FOAF.name), "storage": graph.value(iri, PIM.storage)}
        found += [(where(card), f"has the subject {key} {value}, but {where(rows)} says {row[key]}")
                  for key, value in person["subject"].items() if row[key] is None or str(row[key]) != value]
    return found


@pytest.mark.parametrize("folder", people(), ids=lambda folder: folder.name)
def test_a_person_is_whole_and_every_source_agrees_with_them(folder):
    assert refusals(folder) == []


def test_every_kit_follows_a_person():
    kits = {json.loads((folder / "person.json").read_text(encoding="utf-8")).get("kit") for folder in people()}
    assert {kit.relative_to(ROOT).as_posix() for kit in KITS} <= kits


def test_a_story_names_a_source_and_a_document_of_its_person():
    for story in sorted(PEOPLE.glob("*/expected/story.json")):
        told, folder = json.loads(story.read_text(encoding="utf-8")), story.parent.parent
        assert (folder / "sources" / told["hospital"] / "fhir.json").is_file(), story
        assert "ccda" not in told or (folder / told["ccda"]).is_file(), story


def test_a_source_document_is_named_by_the_day_of_its_effective_time():
    for path in sorted(PEOPLE.glob("*/sources/*/ccda/*.xml")):
        assert path.stem == day(header(path, "effectiveTime").get("value")), path


PATIENT = {"resourceType": "Patient", "id": "p1", "name": [{"family": "Quill", "given": ["Hedda"]}],
           "birthDate": "1980-01-02", "gender": "female"}
HEDDA = {"id": "hedda-quill", "name": {"family": "Quill", "given": ["Hedda"]}, "birthDate": "1980-01-02",
         "gender": "female"}
SUBJECT = {"iri": "urn:uuid:00000000-0000-4000-8000-000000000001", "name": "Hedda",
           "storage": "https://pod.hedda-quill.example/"}
ROW = "<urn:uuid:00000000-0000-4000-8000-000000000001> <http://xmlns.com/foaf/0.1/name> \"Hedda\" ; " \
      "<http://www.w3.org/ns/pim/space#storage> <https://pod.hedda-quill.example/> .\n"


@pytest.mark.parametrize("person, patients, where, reason", [
    ({**HEDDA, "birthDate": "1980-02-01"}, [PATIENT], "people/hedda-quill/sources/north/fhir.json",
     "Patient p1 says birthDate 1980-01-02, person.json says 1980-02-01"),
    ({**HEDDA, "differences": [{"source": "north", "field": "gender", "value": "male", "reason": "Entered wrong.",
                                "expectedMatch": "probable"}]}, [PATIENT], "people/hedda-quill/person.json",
     "declares a difference in gender at north that its Patient does not show"),
    ({**HEDDA, "id": "hedda-quil"}, [PATIENT], "people/hedda-quill/person.json",
     "has the id hedda-quil, but its folder is hedda-quill"),
    ({**HEDDA, "kit": "conformance/hedda", "subject": {**SUBJECT, "name": "Heddy"}}, [PATIENT],
     "people/hedda-quill/person.json", "has the subject name Heddy, but conformance/hedda/scripted-input/people.ttl says Hedda"),
    ({**HEDDA, "kit": "conformance/nobody"}, [PATIENT], "people/hedda-quill/person.json",
     "names the kit conformance/nobody, which is not there"),
    ({**HEDDA, "gender": "woman"}, [PATIENT], "people/hedda-quill/person.json",
     "'woman' is not one of ['male', 'female', 'other', 'unknown']"),
    (HEDDA, [], "people/hedda-quill/sources/north/fhir.json", "holds no Patient"),
    (HEDDA, [PATIENT, {**PATIENT, "id": "p2"}], "people/hedda-quill/sources/north/fhir.json",
     "holds 2 Patients: a source holds one"),
], ids=["an undeclared birth date", "a declared difference not shown", "a folder not its id",
        "a subject not the people.ttl row", "a kit not there", "a field the schema refuses", "no Patient", "two Patients"])
def test_a_person_is_refused_for_each_reason(tmp_path, person, patients, where, reason):
    folder = tmp_path / "people" / "hedda-quill"
    (folder / "sources" / "north").mkdir(parents=True)
    (folder / "person.json").write_text(json.dumps(person), encoding="utf-8")
    bundle = {"resourceType": "Bundle", "type": "collection", "entry": [{"resource": p} for p in patients]}
    (folder / "sources" / "north" / "fhir.json").write_text(json.dumps(bundle), encoding="utf-8")
    (tmp_path / "conformance" / "hedda" / "scripted-input").mkdir(parents=True)
    (tmp_path / "conformance" / "hedda" / "scripted-input" / "people.ttl").write_text(ROW, encoding="utf-8")
    assert refusals(folder, tmp_path) == [(where, reason)]


def test_a_declared_difference_the_source_shows_is_accepted(tmp_path):
    folder = tmp_path / "people" / "hedda-quill"
    (folder / "sources" / "north").mkdir(parents=True)
    person = {**HEDDA, "differences": [{"source": "north", "field": "name", "value": {"family": "Quil", "given": ["Hedda"]},
                                        "reason": "The hospital dropped a letter.", "expectedMatch": "probable"}]}
    (folder / "person.json").write_text(json.dumps(person), encoding="utf-8")
    patient = {**PATIENT, "name": [{"use": "nickname", "family": "Q", "given": ["H"]},
                                   {"use": "official", "family": "Quil", "given": ["Hedda"]}]}
    bundle = {"resourceType": "Bundle", "type": "collection", "entry": [{"resource": patient}]}
    (folder / "sources" / "north" / "fhir.json").write_text(json.dumps(bundle), encoding="utf-8")
    assert refusals(folder, tmp_path) == []
