import json

import pytest

from rdflib import URIRef
from rdflib.namespace import FOAF, RDF

from cascade_pod import Failure, names, write
from cascade_pod.example import Example
from cascade_pod.store import parsed

SUBJECT = "urn:uuid:00000000-0000-4000-8000-000000000001"
PREFIXES = """@prefix bridge: <https://ns.cascadeprotocol.org/bridge/v1-draft#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix pav: <http://purl.org/pav/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""
PEANUTS = '{"allergy": "peanuts"}'


class Story:
    def __init__(self, root):
        self.root = root
        self.events = [{"event": "E1", "at": "2026-01-01T00:00:00Z", "subject": SUBJECT, "adds": []}]

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
                            "import": names.new_id()})
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


def test_a_file_the_bridge_has_not_converted_stops_the_run_and_prints_the_command_to_convert_it(tmp_path, capsys):
    code, example = Story(tmp_path).export("E2", {"a": (PEANUTS, None, None)}).write()
    assert code == 1
    printed = capsys.readouterr()
    assert "cascade-bridge convert" in printed.out and "downloads/e2/apple_health_export/clinical-records/a.json" in printed.out
    assert "1 conversions to run" in printed.err
    assert (tmp_path / "conversions" / "e2" / "a" / "facts.ttl").is_file()
    assert [p for p in example.pod.rglob("*") if p.is_file()] == []


PIM, SOLID = "http://www.w3.org/ns/pim/space#", "http://www.w3.org/ns/solid/terms#"


def test_creating_a_pod_files_the_subject_and_a_shell_that_says_only_where_the_root_and_the_type_index_are(tmp_path):
    code, example = Story(tmp_path).write()
    assert code == 0
    files = sorted(p.relative_to(example.pod).as_posix() for p in example.pod.rglob("*") if p.is_file())
    assert files == sorted(example.events[0]["adds"])
    graphs = {path: parsed(example.pod / path, example.address + path) for path in files}
    owner = URIRef(example.address + "profile/card.ttl#me")
    preferences = URIRef(example.address + "settings/preferences")
    assert set(graphs["profile/card.ttl"]) == {
        (owner, RDF.type, FOAF.Person), (owner, RDF.type, URIRef("http://www.w3.org/ns/prov#Person")),
        (owner, URIRef(PIM + "storage"), URIRef(example.address)), (owner, URIRef(PIM + "preferencesFile"), preferences)}
    assert set(graphs["settings/preferences"]) == {
        (preferences, RDF.type, URIRef(PIM + "ConfigurationFile")),
        (owner, URIRef(SOLID + "privateTypeIndex"), URIRef(example.address + "settings/privateTypeIndex.ttl"))}
    assert [path for path in files if path not in graphs or path.startswith("subject/")] == [
        f"subject/{SUBJECT[9:11]}/{SUBJECT[9:]}.ttl"]


def test_an_entry_of_a_type_the_pod_files_nowhere_is_refused_in_one_line(tmp_path):
    entry = """<urn:uuid:00000000-0000-4000-8000-000000000009> a prov:Activity ;
  prov:startedAtTime "2026-01-01T00:00:00Z"^^xsd:dateTime .
<urn:cascade:output-0> a <urn:example:NoSuchRecord> .
<urn:cascade:output-0-version> prov:specializationOf <urn:cascade:output-0> .
"""
    with pytest.raises(Failure, match="entries/e2.ttl: urn:uuid:.* is of no type the pod files: urn:example:NoSuchRecord"):
        Story(tmp_path).entry("E2", entry).write()
