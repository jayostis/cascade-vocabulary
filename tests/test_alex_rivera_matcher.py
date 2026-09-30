import json
import shutil
import subprocess
import sys
from pathlib import Path

import rdflib
from rdflib import Graph, URIRef

rdflib.NORMALIZE_LITERALS = False

ROOT = Path(__file__).absolute().parent.parent
MATCHER_FOLDER = ROOT / "example-pods" / "alex-rivera" / "matcher"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(MATCHER_FOLDER))
import match  # noqa: E402
import recomputed  # noqa: E402

JDG = "https://ns.cascadeprotocol.org/judgments/v1-draft#"
PROV = "http://www.w3.org/ns/prov#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
SUBJECT = "urn:example:subject"
RXNORM, SNOMED = "http://www.nlm.nih.gov/research/umls/rxnorm/", "http://snomed.info/sct/"
PREFIXES = """@prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#> .
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""
KINDS = {"allergies": "health:AllergyRecord", "conditions": "health:ConditionRecord",
         "immunizations": "health:ImmunizationRecord", "procedures": "clinical:Procedure"}


def record(key):
    return f"urn:example:record:{key}"


def version(key):
    return f"urn:example:version:{key}"


class SmallPod:
    def __init__(self, root):
        self.root, self.events, self.arrivals = root, [{"event": "E1", "subject": SUBJECT, "adds": []}], 0

    def event(self, name):
        self.events.append({"event": name, "adds": []})
        return self

    def write(self, path, text):
        target = self.root / "pod" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(PREFIXES + text, encoding="utf-8")
        self.events[-1]["adds"].append(path)

    def record(self, key, folder, content, profile="urn:example:profile:a"):
        self.arrivals += 1
        patient = f" ;\n  rec:patient <{profile}>" if profile else ""
        self.write(f"records/{folder}/{key}.ttl", f"""
<{record(key)}> a {KINDS[folder]} .
<urn:example:revision:{key}> a rec:Revision ;
  rec:revisionOf <{record(key)}> ;
  rec:version <{version(key)}> ;
  prov:generatedAtTime "2026-01-01T00:00:{self.arrivals:02d}Z"^^xsd:dateTime .
<{version(key)}> prov:specializationOf <{record(key)}> ;
  {content}{patient} .
""")

    def judgment(self, key, body):
        self.write(f"judgments/{key}.ttl", f"<urn:example:judgment:{key}> a jdg:Judgment ;\n  {body} .\n")

    def about(self, key, profile="urn:example:profile:a"):
        self.judgment(key, f"jdg:verdict jdg:About ; jdg:subject <{SUBJECT}> ; jdg:basis jdg:OwnerStatement ; "
                           f"prov:hadMember <{profile}>")

    def reference(self, path, content):
        target = self.root / "pod" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        self.events[-1]["adds"].append(path)

    def match(self, takes=None):
        (self.root / "events.json").write_text(json.dumps({"events": self.events}), encoding="utf-8")
        out = self.root / "out"
        shutil.rmtree(out, ignore_errors=True)
        command = [sys.executable, str(MATCHER_FOLDER / "match.py"), "--example", str(self.root),
                   "--read-through", self.events[-1]["event"], "--at", "2026-02-01T00:00:00Z", "--out", str(out)]
        result = subprocess.run(command + (["--takes", takes] if takes else []), capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        return {p.relative_to(out).as_posix(): p for p in out.rglob("*") if p.is_file()}


def sames(written):
    found = set()
    for relative, path in written.items():
        if relative.startswith("judgments/"):
            graph = Graph().parse(path, format="turtle")
            [judgment] = graph.subjects(RDF_TYPE, URIRef(JDG + "Judgment"))
            members = frozenset(str(m)[len(record("")):] for m in graph.objects(judgment, URIRef(PROV + "hadMember")))
            found.add((members, str(graph.value(judgment, URIRef(JDG + "justification")))[len(JDG):]))
    return found


def pod_of_two(tmp_path, folder, first, second, **later):
    pod = SmallPod(tmp_path)
    pod.about("about-a")
    pod.record("first", folder, first)
    pod.event("E2")
    pod.record("second", folder, second, **later)
    return pod


def test_same_code_joins_two_records_with_one_code(tmp_path):
    pod = pod_of_two(tmp_path, "allergies", f"health:allergenCode <{RXNORM}10180>", f"health:allergenCode <{RXNORM}10180>")
    pod.record("third", "allergies", f"health:allergenCode <{RXNORM}7980>")
    assert sames(pod.match("E2")) == {(frozenset({"first", "second"}), "SameCode")}


def test_same_code_ignores_a_procedures_date(tmp_path):
    pod = pod_of_two(tmp_path, "procedures",
                     'clinical:snomedCode "73761001" ; clinical:procedureDate "2025-03-01"^^xsd:date',
                     'clinical:snomedCode "73761001" ; clinical:procedureDate "2026-09-01"^^xsd:date')
    assert sames(pod.match("E2")) == {(frozenset({"first", "second"}), "SameCode")}


def test_same_cvx_code_needs_the_same_administration_date(tmp_path):
    pod = pod_of_two(tmp_path, "immunizations",
                     'health:vaccineCode "150" ; health:administrationDate "2025-10-01"^^xsd:date',
                     'health:vaccineCode "150" ; health:administrationDate "2025-10-01"^^xsd:date')
    pod.record("later", "immunizations",
               'health:vaccineCode "150" ; health:administrationDate "2025-10-02"^^xsd:date')
    assert sames(pod.match("E2")) == {(frozenset({"first", "second"}), "SameCodeAndDate")}


def test_the_ingredient_map_pairs_only_its_rows_under_its_current_version(tmp_path):
    pod = pod_of_two(tmp_path, "allergies", f"health:allergenCode <{SNOMED}373270004>", f"health:allergenCode <{RXNORM}7980>")
    pod.record("unpaired", "allergies", f"health:allergenCode <{SNOMED}91936005>")
    written = pod.match("E2")
    assert sames(written) == {(frozenset({"first", "second"}), "SameMappedCode")}
    references = match.References()
    ingredient_map = references.by_key["ingredient-map"]
    old, new = ingredient_map["versions"]
    assert match.fanned("references", old["name"]) in written and match.fanned("references", new["name"]) not in written

    pod.reference(match.fanned("references", ingredient_map["name"]), match.series_file(ingredient_map))
    pod.reference(match.fanned("references", old["name"]), match.version_file(ingredient_map, old))
    pod.event("E3")
    pod.reference(match.fanned("references", new["name"]), match.version_file(ingredient_map, new))
    pod.record("third", "allergies", f"health:allergenCode <{RXNORM}7980>")
    assert sames(pod.match("E3")) == {(frozenset({"third", "second"}), "SameCode")}


def test_a_vaccine_group_needs_two_different_codes_and_one_date(tmp_path):
    cvx = 'health:vaccineCode "{}" ; health:administrationDate "2025-10-{}"^^xsd:date'
    pod = pod_of_two(tmp_path, "immunizations", cvx.format(141, "01"), cvx.format(150, "01"))
    pod.record("other-day", "immunizations", cvx.format(141, "02"))
    pod.record("same-code", "immunizations", cvx.format(141, "01"))
    assert sames(pod.match("E2")) == {
        (frozenset({"first", "second"}), "SameMappedCodeAndDate"),
        (frozenset({"same-code", "first"}), "SameCodeAndDate"),
        (frozenset({"same-code", "second"}), "SameMappedCodeAndDate"),
    }


def test_a_record_nobody_is_named_for_is_never_taken(tmp_path):
    code = f"health:allergenCode <{RXNORM}10180>"
    pod = pod_of_two(tmp_path, "allergies", code, code, profile="urn:example:profile:nobodys")
    pod.record("no-patient", "allergies", code, profile=None)
    assert pod.match("E2") == {}


def test_a_retracted_about_stops_the_matcher_taking_that_profiles_new_records(tmp_path):
    code = f"health:allergenCode <{RXNORM}10180>"
    pod = pod_of_two(tmp_path, "allergies", code, code, profile="urn:example:profile:b")
    pod.about("about-b", profile="urn:example:profile:b")
    assert sames(pod.match("E2")) == {(frozenset({"first", "second"}), "SameCode")}
    pod.judgment("retraction", "npx:retracts <urn:example:judgment:about-b>")
    assert pod.match("E2") == {}


def test_the_matcher_reads_no_persons_same_or_different(tmp_path):
    pod = pod_of_two(tmp_path, "allergies", f"health:allergenCode <{RXNORM}10180>", f"health:allergenCode <{RXNORM}10180>")
    pod.record("third", "allergies", f"health:allergenCode <{RXNORM}7980>")
    pod.judgment("different", f"jdg:verdict jdg:Different ; prov:hadMember <{record('first')}> , <{record('second')}>")
    pod.judgment("same", f"jdg:verdict jdg:Same ; prov:hadMember <{record('first')}> , <{record('third')}>")
    assert sames(pod.match("E2")) == {(frozenset({"first", "second"}), "SameCode")}


def test_a_matcher_judgments_name_is_the_record_name_of_its_inputs(tmp_path):
    pod = pod_of_two(tmp_path, "allergies", f"health:allergenCode <{SNOMED}373270004>", f"health:allergenCode <{RXNORM}7980>")
    [(relative, path)] = [(r, p) for r, p in pod.match("E2").items() if r.startswith("judgments/")]
    graph = Graph().parse(path, format="turtle")
    [judgment] = graph.subjects(RDF_TYPE, URIRef(JDG + "Judgment"))
    rules, ingredient_map = (match.References().by_key[key]["versions"][0]["name"] for key in ("rules", "ingredient-map"))
    inputs = [match.MATCHER, JDG + "SameMappedCode", *sorted([record("first"), record("second")]),
              *sorted([rules, ingredient_map, version("first"), version("second")])]
    assert str(judgment) == recomputed.record_name(inputs)
    assert relative == match.fanned("judgments", str(judgment))
