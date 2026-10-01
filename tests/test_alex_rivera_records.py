import base64
import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import rdflib
from pyshacl import validate
from rdflib import BNode, Graph, URIRef
from rdflib.compare import isomorphic

rdflib.NORMALIZE_LITERALS = False

ROOT = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import recomputed  # noqa: E402
from cascade_pod import write  # noqa: E402

EXAMPLE = ROOT / "example-pods" / "alex-rivera"
POD = EXAMPLE / "pod"
POD_BASE = "https://pod.alex-rivera.example/"
RECOMPUTED_SHA256 = "409b3dd5420a1a6f9707c802fa1bd7ed26e4d0c98119519968faa698344608f3"

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
PROV = "http://www.w3.org/ns/prov#"
BRIDGE = "https://ns.cascadeprotocol.org/bridge/v1-draft#"
PAV = "http://purl.org/pav/"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
REVISION, REVISION_OF, VERSION = URIRef(REC + "Revision"), URIRef(REC + "revisionOf"), URIRef(REC + "version")
SPECIALIZATION_OF, WAS_REVISION_OF = URIRef(PROV + "specializationOf"), URIRef(PROV + "wasRevisionOf")
DERIVED_FROM, GENERATED_BY, USED = URIRef(PROV + "wasDerivedFrom"), URIRef(PROV + "wasGeneratedBy"), URIRef(PROV + "used")
ARRIVED_AS = URIRef(BRIDGE + "arrivedAs")
OWNED = ("subject/", "records/", "provenance/", "attachments/")

FILES_PER_EVENT = {"E1": 1, "E2": 46, "E3": 4, "E4": 31, "E6": 31, "E7": 0, "E10": 16, "E12": 31, "E15": 4}
CONVERSIONS_PER_EVENT = {"e2": 9, "e4": 6, "e6": 8, "e7": 1, "e10": 4, "e12": 7, "e15": 2}
TWO_VERSIONS = {"H1-ALG-SULFA", "H1-ALG-LATEX", "H1-ALG-CODEINE", "H1-CON-BRONCH", "H1-CON-BACK"}
PROFILES = {"H1-PAT", "H1P-PAT", "H2O-PAT", "H2F-PAT"}


def manifest():
    return json.loads((EXAMPLE / "events.json").read_text(encoding="utf-8"))


def handles():
    return json.loads((EXAMPLE / "handles.json").read_text(encoding="utf-8"))


def pod_files():
    return sorted(p.relative_to(POD).as_posix() for p in POD.rglob("*") if p.is_file())


def load(relative):
    return Graph().parse(POD / relative, format="turtle", publicID=POD_BASE + relative)


def ttl_files(*folders):
    return [f for f in pod_files() if f.startswith(folders) and f.endswith(".ttl")]


def revisions():
    found = {}
    for relative in ttl_files("records/"):
        graph = load(relative)
        for subject in graph.subjects(RDF_TYPE, REVISION):
            found[str(subject)] = graph
    return found


def versions():
    found = {}
    for relative in ttl_files("records/"):
        graph = load(relative)
        for subject in graph.subjects(SPECIALIZATION_OF, None):
            found[str(subject)] = (relative, graph)
    return found


def added_by():
    return {path: event["event"] for event in manifest()["events"] for path in event["adds"]}


def name_of(handle):
    return handles()[handle]["name"]


def revisions_of(record):
    return {name: graph for name, graph in revisions().items() if str(graph.value(URIRef(name), REVISION_OF)) == record}


def _term(term):
    if isinstance(term, URIRef):
        return ("iri", str(term))
    return ("literal", str(term), str(term.datatype) if term.datatype else recomputed.XSD_STRING)


def test_recomputed_py_less_its_first_line_is_the_source_file_at_the_commit_it_names():
    lines = (ROOT / "tests" / "recomputed.py").read_bytes().split(b"\n", 1)
    assert lines[0].startswith(b"# https://github.com/jayostis/cascade-bridge-spec/blob/2249a3aec0aa9dfe6a8c5b8a5cabf8855c97c190/")
    assert hashlib.sha256(lines[1]).hexdigest() == RECOMPUTED_SHA256


def test_every_pod_file_is_listed_once_under_one_event_or_under_derived_and_every_listed_path_exists():
    listed = [p for e in manifest()["events"] for p in e["adds"]] + manifest()["derived"]
    assert [p for p, n in Counter(listed).items() if n > 1] == []
    assert sorted(set(pod_files()) - set(listed)) == []
    assert sorted(set(listed) - set(pod_files())) == []


def test_each_event_adds_the_scenarios_count_of_records_layer_files():
    counts = Counter(event for path, event in added_by().items() if path.startswith(OWNED))
    assert {e: counts.get(e, 0) for e in FILES_PER_EVENT} == FILES_PER_EVENT
    assert set(counts) <= set(FILES_PER_EVENT)


def test_every_record_is_named_by_recomputed_record_name_of_its_inputs_in_the_handle_table():
    for handle, row in handles().items():
        if "inputs" in row:
            assert row["name"] == recomputed.record_name(row["inputs"]), handle


def test_every_version_file_passed_through_recomputed_versions_gives_its_own_name():
    for name, (relative, graph) in versions().items():
        named, _ = recomputed.versions(recomputed.parsed_ntriples(graph.serialize(format="nt")))
        assert list(named) == [name], relative


def test_every_file_under_attachments_is_named_by_the_hex_digest_of_its_bytes():
    for relative in pod_files():
        if relative.startswith("attachments/"):
            octets = (POD / relative).read_bytes()
            assert relative == "attachments/sha-256/" + hashlib.sha256(octets).hexdigest()
            assert recomputed.ni_name(octets) in {row["name"] for row in handles().values()}


def test_every_revision_is_named_by_the_hash_of_its_own_triples_with_a_placeholder_for_its_iri():
    for name, graph in revisions().items():
        content = {tuple(("iri", "urn:cascade:this-revision") if t == ("iri", name) else t for t in map(_term, triple))
                   for triple in graph}
        assert recomputed.ni_name(recomputed.canonical_nquads(content).encode("utf-8")) == name


def test_each_revision_sets_a_version_of_its_record_and_follows_an_earlier_revision_of_the_same_record():
    all_versions, all_revisions = versions(), revisions()
    for name, graph in all_revisions.items():
        record, version = graph.value(URIRef(name), REVISION_OF), graph.value(URIRef(name), VERSION)
        assert all_versions[str(version)][1].value(version, SPECIALIZATION_OF) == record
        earlier = graph.value(URIRef(name), WAS_REVISION_OF)
        if earlier is not None:
            before = all_revisions[str(earlier)]
            assert before.value(earlier, REVISION_OF) == record
            at = URIRef(PROV + "generatedAtTime")
            assert str(before.value(earlier, at)) < str(graph.value(URIRef(name), at))


def test_each_record_has_the_scenarios_versions_and_revisions():
    for handle, row in handles().items():
        if "first" not in row:
            continue
        found = revisions_of(row["name"])
        versions_seen = {str(g.value(URIRef(n), VERSION)) for n, g in found.items()}
        expected = (2, 3) if handle == "H1-CON-BACK" else (2, 2) if handle in TWO_VERSIONS else (1, 1)
        assert (len(versions_seen), len(found)) == expected, handle


def test_h1_con_back_r3_sets_its_v1_again_after_r2():
    r3 = revisions()[name_of("H1-CON-BACK r3")]
    assert str(r3.value(URIRef(name_of("H1-CON-BACK r3")), VERSION)) == name_of("H1-CON-BACK v1")
    assert str(r3.value(URIRef(name_of("H1-CON-BACK r3")), WAS_REVISION_OF)) == name_of("H1-CON-BACK r2")


def test_h1_con_htn_has_one_revision_and_none_of_its_later_files_is_stored():
    assert len(revisions_of(name_of("H1-CON-HTN"))) == 1
    later = EXAMPLE / "downloads" / "x-e6" / "apple_health_export" / "clinical-records" / "Condition-cond-htn-1.json"
    assert not (POD / "attachments" / "sha-256" / hashlib.sha256(later.read_bytes()).hexdigest()).exists()


def test_importing_x_e6_again_at_e7_writes_nothing():
    assert "import" not in next(e for e in manifest()["events"] if e["event"] == "E7")
    assert [p for p, e in added_by().items() if e == "E7"] == []


def test_nothing_is_written_for_h1_alg_latex_at_e15():
    latex = name_of("H1-ALG-LATEX")
    for relative in [p for p, e in added_by().items() if e == "E15" and p.endswith(".ttl")]:
        assert latex not in (POD / relative).read_text(encoding="utf-8"), relative


def test_u_imm_tdap_is_named_from_its_document_with_no_patient_and_one_revision():
    row = handles()["U-IMM-TDAP"]
    assert row["inputs"] == [name_of("D-U-IMM-TDAP r1"), ""]
    assert len(revisions_of(row["name"])) == 1
    _, graph = versions()[name_of("U-IMM-TDAP v1")]
    assert graph.value(URIRef(name_of("U-IMM-TDAP v1")), URIRef(REC + "patient")) is None


def _hex(ni):
    encoded = ni[len("ni:///sha-256;"):]
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()


def _stem(name):
    return name[len("urn:uuid:"):] if name.startswith("urn:uuid:") else _hex(name)


def expected_path(relative, name):
    stem = _stem(name)
    return f"{relative.rsplit('/', 2)[0]}/{stem[:2]}/{stem}.ttl"


def test_every_file_holds_exactly_the_triples_of_its_thing_and_is_at_the_path_its_name_gives():
    for relative in ttl_files("subject/", "records/", "provenance/"):
        graph = load(relative)
        named = {s for s in graph.subjects() if not isinstance(s, BNode)}
        things = {URIRef(str(s).split("#")[0]) for s in named}
        assert len(things) == 1, relative
        thing = next(iter(things))
        assert relative == expected_path(relative, str(thing))
        if named != {thing}:
            assert graph.value(thing, SPECIALIZATION_OF) is not None, relative
        for node in {s for s in graph.subjects() if isinstance(s, BNode)}:
            assert len(list(graph.subject_predicates(node))) == 1, relative


def conversions():
    for folder in sorted((EXAMPLE / "conversions").glob("*/*")):
        yield folder


def test_every_conversion_holds_its_facts_graph_and_findings_and_each_event_has_the_scenarios_count():
    for folder in conversions():
        assert sorted(p.name for p in folder.iterdir()) == ["facts.ttl", "findings.ttl", "graph.ttl"], folder
    counts = Counter(folder.parent.name for folder in conversions())
    assert dict(counts) == CONVERSIONS_PER_EVENT


def pod_graph():
    graph = Graph()
    for relative in ttl_files("subject/", "records/", "provenance/"):
        graph += load(relative)
    return graph


def test_each_stored_conversion_is_in_the_pod_less_its_arrivals_with_the_import_named_by_its_uuid():
    pod = pod_graph()
    imports = {e["event"].lower(): URIRef(e["import"]) for e in manifest()["events"] if "import" in e}
    stored = {p.name for p in (POD / "attachments" / "sha-256").iterdir()}
    for folder in conversions():
        graph = Graph().parse(folder / "graph.ttl", format="turtle")
        document = next(graph.subjects(RDF_TYPE, URIRef(PROV + "Entity")))
        if _hex(str(document)) not in stored:
            text = "".join((POD / r).read_text(encoding="utf-8") for r in ttl_files(""))
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


def _closure(graph, node):
    found = Graph()
    if isinstance(node, BNode):
        for p, o in graph.predicate_objects(node):
            found.add((node, p, o))
            found += _closure(graph, o)
    return found


def test_each_revision_holds_its_arrivals_triples():
    arrivals = {}
    for folder in conversions():
        graph = Graph().parse(folder / "graph.ttl", format="turtle")
        for arrival in graph.subjects(ARRIVED_AS, None):
            key = (str(graph.value(arrival, ARRIVED_AS)), str(graph.value(arrival, DERIVED_FROM)))
            arrivals[key] = {(p, o) for p, o in graph.predicate_objects(arrival) if p not in (ARRIVED_AS, GENERATED_BY)}
    for name, graph in revisions().items():
        revision = URIRef(name)
        if graph.value(revision, DERIVED_FROM) is None:
            continue
        key = (str(graph.value(revision, VERSION)), str(graph.value(revision, DERIVED_FROM)))
        assert arrivals[key] <= set(graph.predicate_objects(revision)), name


def test_every_name_in_the_handle_table_names_a_pod_file_but_a_profiles_and_every_thing_has_a_handle():
    names = {row["name"] for row in handles().values()}
    for handle, row in handles().items():
        if handle in PROFILES:
            continue
        stem = _stem(row["name"])
        assert any(Path(f).name in (stem, f"{stem}.ttl") for f in pod_files()), handle
    things = set()
    for relative in ttl_files("records/", "provenance/"):
        things |= {str(s).split("#")[0] for s in load(relative).subjects() if not isinstance(s, BNode)}
    assert sorted(things - names) == []


def test_the_records_layer_conforms_to_the_records_shapes():
    shapes = Graph().parse(ROOT / "ontologies" / "records" / "v1-draft" / "records.shapes.ttl", format="turtle")
    conforms, _, report = validate(pod_graph(), shacl_graph=shapes, advanced=True)
    assert conforms, report


def test_running_the_writer_once_on_a_copy_reproduces_the_example_byte_for_byte(tmp_path):
    copy = tmp_path / "alex-rivera"
    shutil.copytree(EXAMPLE, copy, ignore=shutil.ignore_patterns("__pycache__"))
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "write", str(copy)],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    differences = []

    def compare(comparison, where):
        differences.extend(where + name for name in
                           comparison.left_only + comparison.right_only + comparison.diff_files + comparison.funny_files)
        for sub, nested in comparison.subdirs.items():
            compare(nested, f"{where}{sub}/")

    compare(filecmp.dircmp(EXAMPLE, copy, ignore=["__pycache__"]), "")
    assert differences == []


def test_every_filed_entry_activity_gets_its_own_handle():
    filing = write.Filing(None)
    filing.activities = {"entries/a1.ttl": "urn:example:activity:1", "entries/a2.ttl": "urn:example:activity:2"}
    table = write.handle_table({}, [{"event": "E1", "subject": "urn:example:subject"}], filing)
    assert {table[h]["name"] for h in ("A1", "A2")} == {"urn:example:activity:1", "urn:example:activity:2"}
