import json

import pytest
from rdflib import URIRef

from cascade_pod import Failure, names, store, write
from cascade_pod.pod import TYPE_INDEX, Example

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
PROV = "http://www.w3.org/ns/prov#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
REVISION, VERSION, WAS_REVISION_OF = URIRef(REC + "Revision"), URIRef(REC + "version"), URIRef(PROV + "wasRevisionOf")
SUBJECT = "urn:uuid:00000000-0000-4000-8000-000000000001"
RECORD = "urn:uuid:00000000-0000-4000-8000-000000000002"
ALLERGIES_TYPE_INDEX = """@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix solid: <http://www.w3.org/ns/solid/terms#> .
<#allergy-records> solid:forClass health:AllergyRecord ; solid:instanceContainer </records/allergies/> .
"""
PREFIXES = """@prefix bridge: <https://ns.cascadeprotocol.org/bridge/v1-draft#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix pav: <http://purl.org/pav/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""


def version(allergen):
    return names.document(allergen.encode("utf-8"))


def conversion(text, *arrivals, label="Apple Health export", stray=""):
    """What the Bridge made of a file of `text`: an arrival of one allergy record for each (allergen, source version)."""
    document = names.document(text.encode("utf-8"))
    lines = [PREFIXES, f"<{document}> a prov:Entity .",
             f'_:import a prov:Activity ; prov:used <{document}> ; rdfs:label "{label}" ; '
             f'prov:startedAtTime "2026-01-01T00:00:00Z"^^xsd:dateTime .',
             stray]
    for index, (allergen, source_version) in enumerate(arrivals):
        lines += [f"<{RECORD}> a health:AllergyRecord .",
                  f'<{version(allergen)}> prov:specializationOf <{RECORD}> ; health:allergen "{allergen}" .',
                  f"_:arrival{index} bridge:arrivedAs <{version(allergen)}> ; prov:wasGeneratedBy _:import ."]
        if source_version is not None:
            lines.append(f'_:arrival{index} pav:version "{source_version}" .')
    return "\n".join(lines) + "\n"


class Story:
    def __init__(self, root):
        self.root = root
        self.events = [{"event": "E1", "at": "2026-01-01T00:00:00Z", "subject": SUBJECT, "adds": []}]
        (root / "pod" / TYPE_INDEX).parent.mkdir(parents=True, exist_ok=True)
        (root / "pod" / TYPE_INDEX).write_text(ALLERGIES_TYPE_INDEX, encoding="utf-8")

    def export(self, event, files):
        """An export at `event` of each named file, given as (its text, the Bridge's graph or None, its findings or None)."""
        export = self.root / "downloads" / event.lower() / "apple_health_export"
        (export / "clinical-records").mkdir(parents=True)
        (export / "export.xml").write_text("<HealthData/>\n", encoding="utf-8")
        for name, (text, graph, findings) in files.items():
            (export / "clinical-records" / f"{name}.json").write_text(text, encoding="utf-8")
            made = self.root / "conversions" / event.lower() / name
            for file, content in (("graph.ttl", graph), ("findings.ttl", findings)):
                if content is not None:
                    made.mkdir(parents=True, exist_ok=True)
                    (made / file).write_text(content, encoding="utf-8")
        self.events.append({"event": event, "at": "2026-01-01T00:00:00Z", "adds": [],
                            "export": export.relative_to(self.root).as_posix(),
                            "import": f"urn:uuid:00000000-0000-4000-8000-0000000000{len(self.events):02d}"})
        return self

    def entry(self, event, text):
        (self.root / "entries").mkdir(exist_ok=True)
        (self.root / "entries" / f"{event.lower()}.ttl").write_text(PREFIXES + text, encoding="utf-8")
        self.events.append({"event": event, "at": "2026-01-01T00:00:00Z", "adds": [], "entry": f"entries/{event.lower()}.ttl"})
        return self

    def write(self):
        story = {"address": "https://pod.example/", "events": self.events, "derived": []}
        (self.root / "events.json").write_text(json.dumps(story), encoding="utf-8")
        code = write.run(Example(self.root))
        return code, Example(self.root)


def versions_revised(example):
    """The version each revision in the pod sets, in the order the revisions follow one another."""
    revisions = {}
    for path in (example.pod / "records").rglob("*.ttl"):
        graph = store.parsed(path)
        for revision in graph.subjects(RDF_TYPE, REVISION):
            revisions[graph.value(revision, WAS_REVISION_OF)] = (revision, str(graph.value(revision, VERSION)))
    found, last = [], None
    while last in revisions:
        last, set_version = revisions[last]
        found.append(set_version)
    return found


def added_at(example, event):
    return next(e["adds"] for e in example.events if e["event"] == event)


PEANUTS = '{"allergy": "peanuts"}'
PEANUTS_AGAIN = '{"allergy": "peanuts", "updated": true}'


def test_a_file_whose_bytes_the_pod_already_holds_brings_nothing_new(tmp_path):
    story = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS, ("Peanuts", "1")), None)})
    code, example = story.export("E3", {"a": (PEANUTS, None, None)}).write()
    assert code == 0
    assert added_at(example, "E3") == []
    assert not (tmp_path / "conversions" / "e3").exists()


def test_a_file_the_bridge_has_not_converted_stops_the_run_and_prints_the_command_to_convert_it(tmp_path, capsys):
    code, example = Story(tmp_path).export("E2", {"a": (PEANUTS, None, None)}).write()
    assert code == 1
    printed = capsys.readouterr()
    assert "cascade-bridge convert" in printed.out and "downloads/e2/apple_health_export/clinical-records/a.json" in printed.out
    assert "1 conversions to run" in printed.err
    assert (tmp_path / "conversions" / "e2" / "a" / "facts.ttl").is_file()
    assert [p for p in example.pod.rglob("*") if p.is_file()] == [example.pod / TYPE_INDEX]


def test_a_statement_of_no_record_version_arrival_document_or_import_is_refused(tmp_path):
    graph = conversion(PEANUTS, ("Peanuts", "1"), stray="<urn:example:stray> <urn:example:says> <urn:example:nothing> .")
    with pytest.raises(Failure, match="holds triples of no record, version, arrival, document or import"):
        Story(tmp_path).export("E2", {"a": (PEANUTS, graph, None)}).write()


def test_an_arrival_its_source_says_is_a_version_already_seen_writes_no_revision(tmp_path):
    story = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS, ("Peanuts", "1")), None)})
    code, example = story.export("E3", {"a": (PEANUTS_AGAIN, conversion(PEANUTS_AGAIN, ("Tree nuts", "1")), None)}).write()
    assert code == 0
    assert versions_revised(example) == [version("Peanuts")]
    assert added_at(example, "E3") == []


def test_an_arrival_whose_content_is_the_version_the_record_is_at_writes_no_revision(tmp_path):
    story = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS, ("Peanuts", "1")), None)})
    code, example = story.export("E3", {"a": (PEANUTS_AGAIN, conversion(PEANUTS_AGAIN, ("Peanuts", "2")), None)}).write()
    assert code == 0
    assert versions_revised(example) == [version("Peanuts")]
    assert added_at(example, "E3") == []


def test_an_arrival_of_new_content_under_a_new_source_version_writes_a_revision_after_the_last_and_keeps_its_file(tmp_path):
    story = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS, ("Peanuts", "1")), None)})
    code, example = story.export("E3", {"a": (PEANUTS_AGAIN, conversion(PEANUTS_AGAIN, ("Tree nuts", "2")), None)}).write()
    assert code == 0
    assert versions_revised(example) == [version("Peanuts"), version("Tree nuts")]
    assert any(path.startswith("attachments/") for path in added_at(example, "E3"))


def test_arrivals_whose_source_names_no_version_are_told_apart_by_their_content_alone(tmp_path):
    story = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS, ("Peanuts", None)), None)})
    code, example = story.export("E3", {"a": (PEANUTS_AGAIN, conversion(PEANUTS_AGAIN, ("Tree nuts", None)), None)}).write()
    assert code == 0
    assert versions_revised(example) == [version("Peanuts"), version("Tree nuts")]


def test_a_file_the_bridge_raised_findings_on_is_kept_though_it_writes_no_revision(tmp_path):
    findings = "<urn:example:finding> a <urn:example:Finding> .\n"
    code, example = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS), findings)}).write()
    assert code == 0
    assert versions_revised(example) == []
    assert [path.split("/")[0] for path in added_at(example, "E2")] == ["attachments", "provenance", "provenance"]


def test_a_file_that_writes_no_revision_and_has_no_findings_is_not_kept(tmp_path):
    code, example = Story(tmp_path).export("E2", {"a": (PEANUTS, conversion(PEANUTS), "")}).write()
    assert code == 0
    assert added_at(example, "E2") == []


def test_an_import_that_describes_itself_differently_in_two_files_of_one_export_is_refused(tmp_path):
    files = {"a": (PEANUTS, conversion(PEANUTS, ("Peanuts", "1")), None),
             "b": (PEANUTS_AGAIN, conversion(PEANUTS_AGAIN, ("Tree nuts", "2"), label="Another export"), None)}
    with pytest.raises(Failure, match="disagree on the import's label, start or association"):
        Story(tmp_path).export("E2", files).write()


def test_an_entry_of_a_type_the_pod_files_nowhere_is_refused_in_one_line(tmp_path):
    entry = """<urn:uuid:00000000-0000-4000-8000-000000000009> a prov:Activity ;
  prov:startedAtTime "2026-01-01T00:00:00Z"^^xsd:dateTime .
<urn:cascade:output-0> a <urn:example:NoSuchRecord> .
<urn:cascade:output-0-version> prov:specializationOf <urn:cascade:output-0> .
"""
    with pytest.raises(Failure, match="entries/e2.ttl: urn:uuid:.* is of no type the pod files: urn:example:NoSuchRecord"):
        Story(tmp_path).entry("E2", entry).write()
