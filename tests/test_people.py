import json
import xml.etree.ElementTree as ElementTree

import pytest
from jsonschema import Draft202012Validator
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import FOAF

from contract import KITS, ROOT

PEOPLE = ROOT / "people"
SCHEMA = json.loads((PEOPLE / "person.schema.json").read_text(encoding="utf-8"))
PIM = Namespace("http://www.w3.org/ns/pim/space#")
HL7 = {"cda": "urn:hl7-org:v3"}
CDA_GENDER = {"F": "female", "M": "male", "UN": "other"}
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


def strays(folder, root):
    """Each entry of a person's sources that is not a source file, and each source that holds none, as (where, reason)."""
    where = lambda path: path.relative_to(root).as_posix()
    rule = "a source holds fhir.json and ccda/<day>.xml"
    found = []
    for source in sorted((folder / "sources").glob("*")):
        if not source.is_dir():
            found.append((where(source), f"is not a source folder: {rule}"))
            continue
        holds = False
        for entry in sorted(source.iterdir()):
            if entry.name == "fhir.json" and entry.is_file():
                holds = True
            elif entry.name == "ccda" and entry.is_dir():
                for day_file in sorted(entry.iterdir()):
                    if day_file.is_file() and day_file.suffix == ".xml":
                        holds = True
                    else:
                        found.append((where(day_file), f"is not a source file: {rule}"))
            else:
                found.append((where(entry), f"is not a source file: {rule}"))
        if not holds:
            found.append((where(source), f"holds no source file: {rule}"))
    return found


def labelled(pid):
    return f"Patient {pid}" if pid is not None else "a Patient with no id"


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
    found += strays(folder, root)
    for source, path, patients in sources(folder, root):
        records = {pid if pid is not None else index for index, (pid, _) in enumerate(patients)}
        if not patients:
            found.append((where(path), "holds no Patient"))
        elif len(records) > 1:
            found.append((where(path), f"holds {len(records)} Patients: a source holds one"))
        for pid, stated in patients:
            for field, value in stated.items():
                if value == person[field]:
                    continue
                if declared.get((source, field)) == value:
                    seen.add((source, field))
                else:
                    found.append((where(path), f"{labelled(pid)} says {field} {shown(value)}, "
                                               f"person.json says {shown(person[field])}"))
    found += [(where(card), f"declares a difference in {field} at {source} that its Patient does not show")
              for source, field in sorted(set(declared) - seen)]
    if "kit" in person and not (root / person["kit"]).is_dir():
        found.append((where(card), f"names the kit {person['kit']}, which is not there"))
    elif "subject" in person:
        rows = root / person["kit"] / "scripted-input" / "people.ttl"
        graph = Graph().parse(rows)
        iri = URIRef(person["subject"]["iri"])
        if (iri, FOAF.name, None) not in graph:
            found.append((where(card), f"has the subject {iri}, which {where(rows)} has no row for"))
        else:
            row = {"name": graph.value(iri, FOAF.name), "storage": graph.value(iri, PIM.storage)}
            found += [(where(card), f"has the subject {key} {value}, but {where(rows)} says {row[key]}")
                      for key, value in person["subject"].items() if key != "iri" and str(row[key]) != value]
    return found


def story_keys(told):
    """Why a story's keys are refused (settlements §1.7): nothing when they are whole."""
    missing, stray = {"hospital", "story", "findings"} - set(told), set(told) - {"hospital", "story", "findings",
                                                                               "pulls", "ccda"}
    return [*(f"lacks {key}" for key in sorted(missing)), *(f"has {key}, which a story does not" for key in sorted(stray))]


def sandbox_stories():
    """Each sandbox story of a person, as (the story's file, what it tells, its person's folder)."""
    return [(story, json.loads(story.read_text(encoding="utf-8")), story.parent.parent)
            for story in sorted(PEOPLE.glob("*/expected/story.json"))]


PATIENT = {"resourceType": "Patient", "id": "p1", "name": [{"family": "Quill", "given": ["Hedda"]}],
           "birthDate": "1980-01-02", "gender": "female"}
HEDDA = {"id": "hedda-quill", "name": {"family": "Quill", "given": ["Hedda"]}, "birthDate": "1980-01-02",
         "gender": "female"}
SUBJECT = {"iri": "urn:uuid:00000000-0000-4000-8000-000000000001", "name": "Hedda",
           "storage": "https://pod.hedda-quill.example/"}
ROW = "<urn:uuid:00000000-0000-4000-8000-000000000009> <http://xmlns.com/foaf/0.1/name> \"Zed\" .\n" \
      "<urn:uuid:00000000-0000-4000-8000-000000000001> <http://xmlns.com/foaf/0.1/name> \"Hedda\" ; " \
      "<http://www.w3.org/ns/pim/space#storage> <https://pod.hedda-quill.example/> .\n"
FHIR = "people/hedda-quill/sources/north/fhir.json"
CARD = "people/hedda-quill/person.json"
NO_ID = {key: value for key, value in PATIENT.items() if key != "id"}
RULE = "a source holds fhir.json and ccda/<day>.xml"


def a_person_folder(tmp_path, person, patients, extra=()):
    """A person's folder under `tmp_path`: their `person.json`, one source `north` that holds a FHIR bundle of the
    patients (none when `patients` is None), and each file of `extra` written under `sources/`."""
    folder = tmp_path / "people" / "hedda-quill"
    (folder / "sources" / "north").mkdir(parents=True)
    (folder / "person.json").write_text(json.dumps(person), encoding="utf-8")
    if patients is not None:
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": [{"resource": p} for p in patients]}
        (folder / "sources" / "north" / "fhir.json").write_text(json.dumps(bundle), encoding="utf-8")
    for name in extra:
        (folder / "sources" / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / "sources" / name).write_text("{}", encoding="utf-8")
    return folder


class TestPeople:
    """People the kits and the sandbox stories are about · people/

    Each made-up person has a folder: a `person.json` that says who they are, and their sources, the files each hospital
    holds about them. A kit or a sandbox story is told about one of them, so every file must agree on who that is.
    """

    class TestGivenAPerson:
        """given a person"""

        @pytest.mark.parametrize("folder", people(), ids=lambda folder: folder.name)
        def test_is_whole(self, folder):
            """is whole: its `person.json`, its folder, its sources and its kit's row agree, but for the differences it declares

            The person's `person.json` is checked against its schema and its folder's name. Each patient in each of their
            sources, and in the downloads of their kit, is compared with it on name, birth date and gender, and the kit's
            `people.ttl` row with its subject. A difference is accepted only where `person.json` declares it and the
            source shows it. The reasons found, one for each break, must be none.
            """
            assert refusals(folder) == []

    class TestGivenAnyKit:
        """given any kit"""

        def test_is_the_kit_of_a_person(self):
            """is the kit of a person

            The kits are the folders of `conformance/` that hold a feature of their own name. Each is compared with the kits
            the people's `person.json` files name; a kit that no person names is listed.
            """
            named = {json.loads((folder / "person.json").read_text(encoding="utf-8")).get("kit") for folder in people()}
            assert sorted({kit.relative_to(ROOT).as_posix() for kit in KITS} - named) == []

    class TestGivenAnySandboxStoryOfAPerson:
        """given any sandbox story of a person"""

        def test_has_only_the_keys_of_a_story(self):
            """has only the keys of a story

            Each person's `expected/story.json` is read with `story_keys()`. A story that lacks a key every story has, or
            holds a key no story has, is listed with the reasons.
            """
            stories = sandbox_stories()
            assert stories
            offenders = {story.relative_to(ROOT).as_posix(): reasons for story, told, _ in stories
                         if (reasons := story_keys(told))}
            assert offenders == {}

        def test_names_a_hospital_that_is_a_source_of_its_person(self):
            """names a hospital that is a source of its person

            The hospital a story names is looked for as a source of the same person, a folder under `sources/` that holds
            a `fhir.json`. A story whose hospital has none is listed.
            """
            stories = sandbox_stories()
            assert stories
            offenders = sorted(story.relative_to(ROOT).as_posix() for story, told, folder in stories
                               if not (folder / "sources" / told["hospital"] / "fhir.json").is_file())
            assert offenders == []

        def test_names_no_c_cda_document_that_its_person_lacks(self):
            """names no C-CDA document that its person lacks

            A story that names a `ccda` document gives its path under its person's folder. A story whose document is no
            file there is listed.
            """
            stories = sandbox_stories()
            assert stories
            offenders = sorted(story.relative_to(ROOT).as_posix() for story, told, folder in stories
                               if "ccda" in told and not (folder / told["ccda"]).is_file())
            assert offenders == []

    class TestGivenAnyCcdaDocumentOfASource:
        """given any C-CDA document of a source"""

        def test_is_named_by_the_day_of_its_effective_time(self):
            """is named by the day of its effective time

            Each document under a source's `ccda/` is named for the day, as `YYYY-MM-DD`, of the `effectiveTime` in its
            header. A document whose file name is another day is listed with the day its header gives.
            """
            documents = sorted(PEOPLE.glob("*/sources/*/ccda/*.xml"))
            assert documents
            offenders = {path.relative_to(ROOT).as_posix(): day(header(path, "effectiveTime").get("value"))
                         for path in documents if path.stem != day(header(path, "effectiveTime").get("value"))}
            assert offenders == {}


class TestChecksOfThePersonChecks:
    """Checks of the checks on a person · tests/test_people.py

    The rules above are checked by two functions of this module. These cases give each a made-up folder or story that
    breaks a rule, or a difference a person rightly declares, so a rule that every person keeps is known to be checked.
    """

    class TestRefusals:
        """`refusals()`"""

        @pytest.mark.parametrize("person, patients, extra, where, reason", [
            ({**HEDDA, "birthDate": "1980-02-01"}, [PATIENT], (), FHIR,
             "Patient p1 says birthDate 1980-01-02, person.json says 1980-02-01"),
            ({**HEDDA, "differences": [{"source": "north", "field": "gender", "value": "male", "reason": "Entered wrong.",
                                        "expectedMatch": "probable"}]}, [PATIENT], (), CARD,
             "declares a difference in gender at north that its Patient does not show"),
            ({**HEDDA, "id": "hedda-quil"}, [PATIENT], (), CARD, "has the id hedda-quil, but its folder is hedda-quill"),
            ({**HEDDA, "kit": "conformance/hedda", "subject": {**SUBJECT, "name": "Heddy"}}, [PATIENT], (), CARD,
             "has the subject name Heddy, but conformance/hedda/scripted-input/people.ttl says Hedda"),
            ({**HEDDA, "kit": "conformance/hedda", "subject": {**SUBJECT, "iri": "urn:uuid:00000000-0000-4000-8000-000000000002"}},
             [PATIENT], (), CARD, "has the subject urn:uuid:00000000-0000-4000-8000-000000000002, which "
                                  "conformance/hedda/scripted-input/people.ttl has no row for"),
            ({**HEDDA, "kit": "conformance/hedda"}, [PATIENT], (), CARD, "'subject' is a dependency of 'kit'"),
            ({**HEDDA, "kit": "conformance/nobody", "subject": SUBJECT}, [PATIENT], (), CARD,
             "names the kit conformance/nobody, which is not there"),
            ({**HEDDA, "gender": "woman"}, [PATIENT], (), CARD, "'woman' is not one of ['male', 'female', 'other', 'unknown']"),
            (HEDDA, [], (), FHIR, "holds no Patient"),
            (HEDDA, [PATIENT, {**PATIENT, "id": "p2"}], (), FHIR, "holds 2 Patients: a source holds one"),
            (HEDDA, [NO_ID, dict(NO_ID)], (), FHIR, "holds 2 Patients: a source holds one"),
            ({**HEDDA, "gender": "male"}, [NO_ID], (), FHIR, "a Patient with no id says gender female, person.json says male"),
            (HEDDA, [PATIENT], ("north/patient.json",), "people/hedda-quill/sources/north/patient.json",
             f"is not a source file: {RULE}"),
            (HEDDA, [PATIENT], ("north/ccda/2025-01-01.txt",), "people/hedda-quill/sources/north/ccda/2025-01-01.txt",
             f"is not a source file: {RULE}"),
            (HEDDA, None, (), "people/hedda-quill/sources/north", f"holds no source file: {RULE}"),
        ], ids=["an undeclared birth date", "a declared difference not shown", "a folder not its id",
                "a subject not the people.ttl row", "a subject with no people.ttl row", "a kit without a subject",
                "a kit not there", "a field the schema refuses", "no Patient", "two Patients", "two Patients with no id",
                "a Patient with no id", "a file that is not a source", "a ccda entry that is not xml", "a source with no file"])
        def test_returns_one_reason_and_its_file_for(self, tmp_path, person, patients, extra, where, reason):
            """returns one reason, and the file it is about, for

            A made-up person folder under a temporary folder is broken in one way, named by the case. `refusals()` over it
            returns that one reason, with the path of the file it is about, and no other.
            """
            folder = a_person_folder(tmp_path, person, patients, extra)
            (tmp_path / "conformance" / "hedda" / "scripted-input").mkdir(parents=True)
            (tmp_path / "conformance" / "hedda" / "scripted-input" / "people.ttl").write_text(ROW, encoding="utf-8")
            assert refusals(folder, tmp_path) == [(where, reason)]

        def test_returns_nothing_for_a_declared_difference_that_the_source_shows(self, tmp_path):
            """returns nothing for a declared difference that the source shows

            A person's `person.json` declares that the source `north` spells the family name `Quil`, and the source's
            official name is `Quil`, beside a nickname that differs. `refusals()` over that folder returns nothing.
            """
            person = {**HEDDA, "differences": [{"source": "north", "field": "name",
                                                "value": {"family": "Quil", "given": ["Hedda"]},
                                                "reason": "The hospital dropped a letter.", "expectedMatch": "probable"}]}
            patient = {**PATIENT, "name": [{"use": "nickname", "family": "Q", "given": ["H"]},
                                           {"use": "official", "family": "Quil", "given": ["Hedda"]}]}
            assert refusals(a_person_folder(tmp_path, person, [patient]), tmp_path) == []

    class TestStoryKeys:
        """`story_keys()`"""

        @pytest.mark.parametrize("told, reasons", [
            ({"hospital": "h", "story": "s", "findings": []}, []),
            ({"hospital": "h", "story": "s", "findings": [], "pulls": [], "ccda": "x"}, []),
            ({"hospital": "h", "story": "s", "findings": [], "patient": "pt-9"}, ["has patient, which a story does not"]),
            ({"hospital": "h", "story": "s", "findngs": []}, ["lacks findings", "has findngs, which a story does not"]),
        ], ids=["whole", "with pulls and ccda", "a leftover patient", "a misspelled key"])
        def test_returns_the_reasons_a_storys_keys_are_refused(self, told, reasons):
            """returns the reasons a story's keys are refused, and none when they are whole

            Given the keys of a story that are whole, that add `pulls` and `ccda`, that keep a `patient` no story has, or
            that misspell `findings`, `story_keys()` returns the reasons for each: a key lacked and a key that is not a
            story's, or none at all.
            """
            assert story_keys(told) == reasons
