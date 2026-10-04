import json
import shutil

import pytest
from rdflib import Graph, URIRef

import recomputed
from cascade_pod import Failure, match, turtle
from cascade_pod.pod import Example, fanned
from examples import run_matcher

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


def uuid(n):
    return f"urn:uuid:00000000-0000-4000-8000-{n:012d}"


SERIES = [
    {"key": "rules", "name": uuid(1), "label": "Matcher rules", "ships_with": "1",
     "versions": [{"name": uuid(2), "version": "1", "table": "rules-1.csv"}]},
    {"key": "ingredient-map", "name": uuid(3), "label": "Ingredient map", "ships_with": "1",
     "versions": [{"name": uuid(4), "version": "1", "table": "ingredient-map-1.csv"},
                  {"name": uuid(5), "version": "2", "revises": "1", "table": "ingredient-map-2.csv"}]},
    {"key": "cvx-vaccine-groups", "name": uuid(6), "label": "Vaccine groups", "ships_with": "1",
     "versions": [{"name": uuid(7), "version": "1", "table": "cvx-vaccine-groups-1.csv"}]},
]
TABLES = {
    "rules-1.csv": "rule,applies_to,justification,table\nR1,allergies conditions procedures,SameCode,\n"
                   "R2,immunizations,SameCodeAndDate,\nR3,allergies,SameMappedCode,ingredient-map\n"
                   "R4,immunizations,SameMappedCodeAndDate,cvx-vaccine-groups\n",
    "ingredient-map-1.csv": f"snomed,rxnorm\n{SNOMED}373270004,{RXNORM}7980\n",
    "ingredient-map-2.csv": "snomed,rxnorm\n",
    "cvx-vaccine-groups-1.csv": "cvx,group\n141,INFLUENZA\n150,INFLUENZA\n",
}


def reference_tables(folder):
    folder.mkdir(parents=True)
    (folder / "references.json").write_text(json.dumps({"series": SERIES}), encoding="utf-8")
    for name, text in TABLES.items():
        (folder / name).write_text(text, encoding="utf-8")


def record(key):
    return f"urn:example:record:{key}"


def version(key):
    return f"urn:example:version:{key}"


class SmallPod:
    def __init__(self, root):
        self.root, self.events, self.arrivals = root, [{"event": "E1", "subject": SUBJECT, "adds": []}], 0
        reference_tables(root / "references")

    def tell(self):
        story = {"address": "https://pod.example/", "events": self.events, "derived": []}
        (self.root / "events.json").write_text(json.dumps(story), encoding="utf-8")

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
        self.tell()
        out = self.root / "out"
        shutil.rmtree(out, ignore_errors=True)
        return run_matcher(self.root, self.events[-1]["event"], "2026-02-01T00:00:00Z", out, takes)


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
    references = match.References(pod.root / "references")
    ingredient_map = references.by_key["ingredient-map"]
    old, new = ingredient_map["versions"]
    assert fanned("references", old["name"]) in written and fanned("references", new["name"]) not in written

    pod.reference(fanned("references", ingredient_map["name"]), turtle.write(match.series_triples(ingredient_map)))
    pod.reference(fanned("references", old["name"]), turtle.write(match.version_triples(ingredient_map, old)))
    pod.event("E3")
    pod.reference(fanned("references", new["name"]), turtle.write(match.version_triples(ingredient_map, new)))
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
    rules, ingredient_map = (match.References(pod.root / "references").by_key[key]["versions"][0]["name"]
                             for key in ("rules", "ingredient-map"))
    inputs = [match.MATCHER, JDG + "SameMappedCode", *sorted([record("first"), record("second")]),
              *sorted([rules, ingredient_map, version("first"), version("second")])]
    assert str(judgment) == recomputed.record_name(inputs)
    assert relative == fanned("judgments", str(judgment))


def rechecked_after_the_ingredient_map_keeps_its_row(pod, monkeypatch):
    references = match.References(pod.root / "references").by_key["ingredient-map"]
    old, new = references["versions"]
    written = pod.match("E2")
    [same] = [r for r in written if r.startswith("judgments/")]
    for relative, path in written.items():
        pod.reference(relative, path.read_bytes())
    pod.event("E3")
    pod.reference(fanned("references", new["name"]), turtle.write(match.version_triples(references, new)))
    yield str(next(Graph().parse(written[same], format="turtle").subjects(RDF_TYPE, URIRef(JDG + "Judgment"))))
    pod.tell()
    kept = match.References.table
    monkeypatch.setattr(match.References, "table",
                        lambda self, version: kept(self, old if version["name"] == new["name"] else version))
    matcher = match.Matcher(match.Reading(Example(pod.root), "E3"), "2026-03-01T00:00:00Z")
    matcher.recheck()
    yield {relative for relative in matcher.files if relative.startswith("judgments/")}


def mapped_pair(tmp_path, **later):
    return pod_of_two(tmp_path, "allergies", f"health:allergenCode <{SNOMED}373270004>",
                      f"health:allergenCode <{RXNORM}7980>", **later)


def test_a_recheck_rederives_a_same_whose_table_was_revised_and_still_joins_its_members(tmp_path, monkeypatch):
    steps = rechecked_after_the_ingredient_map_keeps_its_row(mapped_pair(tmp_path), monkeypatch)
    next(steps)
    assert len(next(steps)) == 1


def test_a_recheck_never_rederives_a_same_the_person_retracted(tmp_path, monkeypatch):
    pod = mapped_pair(tmp_path)
    steps = rechecked_after_the_ingredient_map_keeps_its_row(pod, monkeypatch)
    pod.judgment("retraction", f"npx:retracts <{next(steps)}>")
    assert next(steps) == set()


def test_a_recheck_never_rederives_a_same_the_person_superseded(tmp_path, monkeypatch):
    pod = mapped_pair(tmp_path)
    steps = rechecked_after_the_ingredient_map_keeps_its_row(pod, monkeypatch)
    pod.judgment("replacement", f"jdg:verdict jdg:Different ; prov:hadMember <{record('first')}> , "
                                f"<{record('second')}> ; npx:supersedes <{next(steps)}>")
    assert next(steps) == set()


def test_a_recheck_never_joins_a_record_whose_about_was_retracted(tmp_path, monkeypatch):
    pod = mapped_pair(tmp_path, profile="urn:example:profile:b")
    pod.about("about-b", profile="urn:example:profile:b")
    steps = rechecked_after_the_ingredient_map_keeps_its_row(pod, monkeypatch)
    next(steps)
    pod.judgment("retraction", "npx:retracts <urn:example:judgment:about-b>")
    assert next(steps) == set()


def test_a_series_that_ships_with_a_version_it_does_not_list_is_a_failure_not_a_traceback(tmp_path):
    pod = SmallPod(tmp_path)
    references = match.References(pod.root / "references")
    references.by_key["rules"]["ships_with"] = "no such version"
    pod.tell()
    with pytest.raises(Failure):
        references.current("rules", match.Reading(Example(tmp_path), "E1"))
