import base64
import filecmp
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime

import pytest
from pyshacl import validate
from rdflib import BNode, Graph, URIRef
from rdflib.compare import isomorphic

import recomputed
from cascade_pod import match, names, store, turtle, vocabulary
from cascade_pod.pod import LAYOUT
from examples import ROOT, every_example, every_example_and, pod_file, run_matcher

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
CASCADE = "https://ns.cascadeprotocol.org/core/v1#"
PROV = "http://www.w3.org/ns/prov#"
BRIDGE = "https://ns.cascadeprotocol.org/bridge/v1-draft#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
REVISION, REVISION_OF, VERSION = URIRef(REC + "Revision"), URIRef(REC + "revisionOf"), URIRef(REC + "version")
SPECIALIZATION_OF, WAS_REVISION_OF = URIRef(PROV + "specializationOf"), URIRef(PROV + "wasRevisionOf")
DERIVED_FROM, GENERATED_BY, USED = URIRef(PROV + "wasDerivedFrom"), URIRef(PROV + "wasGeneratedBy"), URIRef(PROV + "used")
ARRIVED_AS = URIRef(BRIDGE + "arrivedAs")


def pod_files(example):
    return sorted(p.relative_to(example.pod).as_posix() for p in example.pod.rglob("*") if p.is_file())


def ttl_files(example, *folders):
    return [f for f in pod_files(example) if f.startswith(folders) and f.endswith(".ttl")]


def revisions(example):
    found = {}
    for relative in ttl_files(example, "records/"):
        graph = pod_file(example, relative)
        for subject in graph.subjects(RDF_TYPE, REVISION):
            found[str(subject)] = graph
    return found


def versions(example):
    found = {}
    for relative in ttl_files(example, "records/"):
        graph = pod_file(example, relative)
        for subject in graph.subjects(SPECIALIZATION_OF, None):
            found[str(subject)] = (relative, graph)
    return found


def conversions(example):
    return sorted(example.folder.glob("conversions/*/*"))


def _term(term):
    if isinstance(term, URIRef):
        return ("iri", str(term))
    return ("literal", str(term), str(term.datatype) if term.datatype else recomputed.XSD_STRING)


def _hex(ni):
    encoded = ni[len("ni:///sha-256;"):]
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()


def _stem(name):
    return name[len("urn:uuid:"):] if name.startswith("urn:uuid:") else _hex(name)


def expected_path(relative, name):
    stem = _stem(name)
    return f"{relative.rsplit('/', 2)[0]}/{stem[:2]}/{stem}.ttl"


def pod_graph(example):
    graph = Graph()
    for relative in ttl_files(example, "subject/", "records/", "provenance/"):
        graph += pod_file(example, relative)
    return graph


def _closure(graph, node):
    found = Graph()
    if isinstance(node, BNode):
        for p, o in graph.predicate_objects(node):
            found.add((node, p, o))
            found += _closure(graph, o)
    return found


def crate(example):
    return json.loads((example.folder / "ro-crate-metadata.json").read_text(encoding="utf-8"))


def _references(value):
    if isinstance(value, dict):
        return {value["@id"]} if set(value) == {"@id"} else set().union(*map(_references, value.values()))
    if isinstance(value, list):
        return set().union(*map(_references, value))
    return set()


def test_the_example_holds_data_only():
    examples = ROOT / "example-pods"
    assert sorted(p.relative_to(examples).as_posix() for pattern in ("*.py", "*.rq") for p in examples.rglob(pattern)) == []


@every_example
def test_the_storys_events_are_in_time_order(example):
    times = [datetime.fromisoformat(event["at"]) for event in example.events]
    assert times == sorted(times)


@every_example
def test_every_pod_file_is_listed_once_under_one_event_or_under_derived_and_every_listed_path_exists(example):
    listed = [p for e in example.events for p in e["adds"]] + example.derived
    assert [p for p, n in Counter(listed).items() if n > 1] == []
    assert sorted(set(pod_files(example)) - set(listed)) == []
    assert sorted(set(listed) - set(pod_files(example))) == []


@every_example
def test_every_version_file_passed_through_recomputed_versions_gives_its_own_name(example):
    for name, (relative, graph) in versions(example).items():
        named, _ = recomputed.versions(recomputed.parsed_ntriples(graph.serialize(format="nt")))
        assert list(named) == [name], relative
        content = {tuple(URIRef(names.THIS_VERSION + str(t)[len(name):]) if str(t).split("#")[0] == name else t
                         for t in triple) for triple in graph}
        assert names.content(content) == name, relative


@every_example
def test_every_revision_is_named_by_the_hash_of_its_own_triples_with_a_placeholder_for_its_iri(example):
    for name, graph in revisions(example).items():
        content = {tuple(("iri", "urn:cascade:this-revision") if t == ("iri", name) else t for t in map(_term, triple))
                   for triple in graph}
        assert recomputed.ni_name(recomputed.canonical_nquads(content).encode("utf-8")) == name
        assert names.content({(URIRef(names.THIS_REVISION) if s == URIRef(name) else s, p, o) for s, p, o in graph}) == name


@every_example
def test_each_revision_sets_a_version_of_its_record_and_follows_an_earlier_revision_of_the_same_record(example):
    all_versions, all_revisions = versions(example), revisions(example)
    for name, graph in all_revisions.items():
        record, version = graph.value(URIRef(name), REVISION_OF), graph.value(URIRef(name), VERSION)
        assert all_versions[str(version)][1].value(version, SPECIALIZATION_OF) == record
        earlier = graph.value(URIRef(name), WAS_REVISION_OF)
        if earlier is not None:
            before = all_revisions[str(earlier)]
            assert before.value(earlier, REVISION_OF) == record
            at = URIRef(PROV + "generatedAtTime")
            assert str(before.value(earlier, at)) < str(graph.value(URIRef(name), at))


@every_example
def test_every_file_holds_exactly_the_triples_of_its_thing_and_is_at_the_path_its_name_gives(example):
    for relative in ttl_files(example, "subject/", "records/", "provenance/"):
        graph = pod_file(example, relative)
        named = {s for s in graph.subjects() if not isinstance(s, BNode)}
        things = {URIRef(str(s).split("#")[0]) for s in named}
        assert len(things) == 1, relative
        thing = next(iter(things))
        assert relative == expected_path(relative, str(thing))
        if named != {thing}:
            assert graph.value(thing, SPECIALIZATION_OF) is not None, relative
        for node in {s for s in graph.subjects() if isinstance(s, BNode)}:
            assert len(list(graph.subject_predicates(node))) == 1, relative


@every_example
def test_each_stored_conversion_is_in_the_pod_less_its_arrivals_with_the_import_named_by_its_uuid(example):
    pod = pod_graph(example)
    imports = {e["event"].lower(): URIRef(e["import"]) for e in example.events if "import" in e}
    stored = {p.name for p in (example.pod / "attachments" / "sha-256").iterdir()}
    for folder in conversions(example):
        graph = store.parsed(folder / "graph.ttl")
        document = next(graph.subjects(RDF_TYPE, URIRef(PROV + "Entity")))
        if _hex(str(document)) not in stored:
            text = "".join((example.pod / r).read_text(encoding="utf-8") for r in ttl_files(example, ""))
            assert str(document) not in text, folder
            continue
        activity = next(graph.subjects(USED, document))
        expected = Graph()
        for s, p, o in graph:
            if graph.value(s, ARRIVED_AS) is not None:
                continue
            expected.add((imports[folder.parent.name] if s == activity else s, p, o))
        found = Graph()
        for s in {s for s in expected.subjects() if not isinstance(s, BNode)}:
            for p, o in pod.predicate_objects(s):
                if p == USED and s == imports[folder.parent.name] and o != document:
                    continue
                found.add((s, p, o))
                found += _closure(pod, o)
        assert isomorphic(expected, found), folder


@every_example
def test_each_revision_holds_its_arrivals_triples(example):
    arrivals = {}
    for folder in conversions(example):
        graph = store.parsed(folder / "graph.ttl")
        for arrival in graph.subjects(ARRIVED_AS, None):
            key = (str(graph.value(arrival, ARRIVED_AS)), str(graph.value(arrival, DERIVED_FROM)))
            arrivals[key] = {(p, o) for p, o in graph.predicate_objects(arrival) if p not in (ARRIVED_AS, GENERATED_BY)}
    for name, graph in revisions(example).items():
        revision = URIRef(name)
        if graph.value(revision, DERIVED_FROM) is None:
            continue
        key = (str(graph.value(revision, VERSION)), str(graph.value(revision, DERIVED_FROM)))
        assert arrivals[key] <= set(graph.predicate_objects(revision)), name


@every_example
def test_running_the_writer_once_on_a_copy_reproduces_the_example_byte_for_byte(example, tmp_path):
    copy = tmp_path / example.name
    shutil.copytree(example.folder, copy, ignore=shutil.ignore_patterns("__pycache__"))
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "write", str(copy)],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    differences = []

    def compare(comparison, where):
        differences.extend(where + name for name in
                           comparison.left_only + comparison.right_only + comparison.diff_files + comparison.funny_files)
        for sub, nested in comparison.subdirs.items():
            compare(nested, f"{where}{sub}/")

    compare(filecmp.dircmp(example.folder, copy, ignore=["__pycache__"]), "")
    assert differences == []


def matcher_runs(example):
    return [event["event"] for event in example.events if "read_through" in event]


@every_example_and("run", matcher_runs)
def test_each_matcher_run_in_the_story_writes_exactly_the_files_its_event_adds_with_the_same_graphs(example, run, tmp_path):
    event = example.event(run)
    written = sorted(run_matcher(example.folder, event["read_through"], event["at"], tmp_path, event.get("takes")))
    assert written == sorted(event["adds"])
    for relative in written:
        assert isomorphic(store.parsed(tmp_path / relative, example.address + relative),
                          pod_file(example, relative)), relative


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
@every_example
def test_the_build_rewrites_every_committed_view_and_the_labels_byte_for_byte(example, engine, tmp_path):
    subprocess.run([sys.executable, "-m", "cascade_pod", "build", str(example.folder), "--engine", engine,
                    "--out", str(tmp_path)], check=True, cwd=ROOT)
    written = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert written == sorted(example.derived)
    for relative in written:
        assert (tmp_path / relative).read_bytes() == (example.pod / relative).read_bytes(), relative


@every_example
def test_every_committed_view_is_marked_rebuildable_and_lists_only_the_kind_the_layout_registers_it_for(example):
    held = example.build("oxigraph", vocabulary.DEFAULT_LENS).store
    current = {row["version"] for row in held.select(vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"]))}
    for relative in sorted(LAYOUT.built):
        address = URIRef(example.address + relative)
        graph = Graph().parse(example.pod / relative, format="turtle", publicID=str(address))
        assert (address, RDF_TYPE, URIRef(REC + "View")) in graph, relative
        assert set(graph.objects(address, URIRef("http://www.w3.org/ns/prov#used"))) == current, relative
    solid = "http://www.w3.org/ns/solid/terms#"
    index = pod_file(example, LAYOUT.type_index)
    for registration, listed in index.subject_objects(URIRef(solid + "instance")):
        view = pod_file(example, listed[len(example.address):])
        kinds = {view.value(entry, RDF_TYPE) for entry in view.subjects(URIRef(CASCADE + "mergedFrom"), None)}
        assert kinds <= {index.value(registration, URIRef(solid + "forClass"))}, listed
    registered = {(index.value(registration, URIRef(solid + "forClass")), str(listed)[len(example.address):],
                   str(index.value(registration, URIRef("http://purl.org/dc/terms/title"))))
                  for listing in ("instance", "instanceContainer")
                  for registration, listed in index.subject_objects(URIRef(solid + listing))}
    views = LAYOUT.views_placement
    assert registered == {(view.kind, view.file, view.title) for view in LAYOUT.views.values()} | {
        (views.kind, views.folder, views.title)}
    assert set(example.derived).isdisjoint(example.files())


@every_example
def test_every_is_based_on_and_citation_in_the_crate_is_on_a_file_that_exists(example):
    described = [e["@id"] for e in crate(example)["@graph"] if "isBasedOn" in e or "citation" in e]
    assert described and [f for f in described if not (example.folder / f).is_file()] == []


@every_example
def test_every_entity_in_the_crate_is_reached_from_its_metadata_descriptor(example):
    entities = {entity["@id"]: entity for entity in crate(example)["@graph"]}
    reached, todo = set(), ["ro-crate-metadata.json"]
    while todo:
        found = todo.pop()
        if found in entities and found not in reached:
            reached.add(found)
            todo.extend(_references(entities[found]))
    assert sorted(set(entities) - reached) == []


@every_example
def test_the_records_layer_conforms_to_the_records_shapes(example):
    shapes = Graph().parse(ROOT / "ontologies" / "records" / "v1-draft" / "records.shapes.ttl", format="turtle")
    conforms, _, report = validate(pod_graph(example), shacl_graph=shapes, advanced=True)
    assert conforms, report


def written_by_a_tool(example):
    """Each Turtle file a tool writes, by its path, with the address it is written at."""
    found = {path: example.address + path for path in example.files() + example.derived
             if path.startswith(("subject/", "records/", "provenance/", "references/")) or path in example.derived}
    for path in example.files():
        if path.startswith("judgments/"):
            if (None, PROV_ATTRIBUTED_TO, match.MATCHER) in store.parsed(example.pod / path):
                found[path] = example.address + path
    return {example.pod / path: address for path, address in found.items()} | {
        path: None for path in example.folder.glob("conversions/*/*/facts.ttl")}


PROV_ATTRIBUTED_TO = URIRef("http://www.w3.org/ns/prov#wasAttributedTo")


def rewritten(path, address):
    return turtle.write(store.parsed(path, address), address)


@every_example
def test_the_one_writer_check_finds_a_file_in_another_layout(example, tmp_path):
    view = example.pod / "clinical" / "allergies.ttl"
    other = tmp_path / "allergies.nt"
    other.write_bytes(store.parsed(view, "https://pod.example/clinical/allergies.ttl").serialize(format="nt", encoding="utf-8"))
    assert rewritten(other, "https://pod.example/clinical/allergies.ttl") != other.read_bytes()


@every_example
def test_every_turtle_file_a_tool_writes_comes_from_the_one_writer(example):
    files = written_by_a_tool(example)
    assert files
    assert [path for path, address in files.items() if rewritten(path, address) != path.read_bytes()] == []
