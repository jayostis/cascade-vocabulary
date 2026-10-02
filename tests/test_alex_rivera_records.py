import hashlib
from collections import Counter

from rdflib import URIRef

import recomputed
from alex_rivera_builds import arrivals, final_pod, handles, source_name, sources
from cascade_pod import names, store
from cascade_pod.pod import Example
from examples import ROOT
from test_example_pod import conversions, pod_files, revisions, versions

EXAMPLE = ROOT / "example-pods" / "alex-rivera"
ALEX = Example(EXAMPLE)
POD = EXAMPLE / "pod"

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
PROV = "http://www.w3.org/ns/prov#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
REVISION_OF, VERSION = URIRef(REC + "revisionOf"), URIRef(REC + "version")
WAS_REVISION_OF = URIRef(PROV + "wasRevisionOf")
DERIVED_FROM, GENERATED_BY = URIRef(PROV + "wasDerivedFrom"), URIRef(PROV + "wasGeneratedBy")
REC_SOURCE_URL = URIRef(REC + "sourceUrl")
OWNED = ("subject/", "records/", "provenance/", "attachments/")

FILES_PER_EVENT = {"E1": 1, "E2": 46, "E3": 4, "E4": 31, "E6": 31, "E7": 0, "E10": 16, "E12": 31, "E15": 4}
CONVERSIONS_PER_EVENT = {"e2": 9, "e4": 6, "e6": 8, "e7": 1, "e10": 4, "e12": 7, "e15": 2}
TWO_VERSIONS = {"H1-ALG-SULFA", "H1-ALG-LATEX", "H1-ALG-CODEINE", "H1-CON-BRONCH", "H1-CON-BACK"}


def added_by():
    return {path: event["event"] for event in ALEX.events for path in event["adds"]}


def name_of(handle):
    return str(handles()[handle])


def revisions_of(record):
    return {name: graph for name, graph in revisions(ALEX).items() if str(graph.value(URIRef(name), REVISION_OF)) == record}


def test_each_event_adds_the_scenarios_count_of_records_layer_files():
    counts = Counter(event for path, event in added_by().items() if path.startswith(OWNED))
    assert {e: counts.get(e, 0) for e in FILES_PER_EVENT} == FILES_PER_EVENT
    assert set(counts) <= set(FILES_PER_EVENT)


def test_each_records_first_revision_came_from_what_its_row_in_expected_handles_says_its_source_calls_it():
    graph = final_pod()
    for handle, row in sources()["records"].items():
        record = handles()[handle]
        first = arrivals(graph, record)[0]
        if "server" in row:
            assert str(graph.value(record, REC_SOURCE_URL)) == f"{row['server']}/{row['type']}/{row['id']}", handle
        elif "download" in row:
            octets = (EXAMPLE / row["download"]).read_bytes()
            assert str(graph.value(first, DERIVED_FROM)) == recomputed.ni_name(octets), handle
        else:
            [activity] = store.parsed(EXAMPLE / row["entry"]).subjects(RDF_TYPE, URIRef(PROV + "Activity"))
            assert graph.value(first, GENERATED_BY) == activity, handle


def test_every_file_under_attachments_is_named_by_the_hex_digest_of_its_bytes():
    for relative in pod_files(ALEX):
        if relative.startswith("attachments/"):
            octets = (POD / relative).read_bytes()
            assert relative == "attachments/sha-256/" + hashlib.sha256(octets).hexdigest()
            assert recomputed.ni_name(octets) == names.document(octets)
            assert recomputed.ni_name(octets) in {str(term) for term in handles().values()}


def test_each_record_has_the_scenarios_versions_and_revisions():
    for handle in sources()["records"]:
        found = revisions_of(name_of(handle))
        versions_seen = {str(g.value(URIRef(n), VERSION)) for n, g in found.items()}
        expected = (2, 3) if handle == "H1-CON-BACK" else (2, 2) if handle in TWO_VERSIONS else (1, 1)
        assert (len(versions_seen), len(found)) == expected, handle


def test_h1_con_back_r3_sets_its_v1_again_after_r2():
    r3 = revisions(ALEX)[name_of("H1-CON-BACK r3")]
    assert str(r3.value(URIRef(name_of("H1-CON-BACK r3")), VERSION)) == name_of("H1-CON-BACK v1")
    assert str(r3.value(URIRef(name_of("H1-CON-BACK r3")), WAS_REVISION_OF)) == name_of("H1-CON-BACK r2")


def test_h1_con_htn_has_one_revision_and_none_of_its_later_files_is_stored():
    assert len(revisions_of(name_of("H1-CON-HTN"))) == 1
    later = EXAMPLE / "downloads" / "x-e6" / "apple_health_export" / "clinical-records" / "Condition-cond-htn-1.json"
    assert not (POD / "attachments" / "sha-256" / hashlib.sha256(later.read_bytes()).hexdigest()).exists()


def test_importing_x_e6_again_at_e7_writes_nothing():
    assert "import" not in next(e for e in ALEX.events if e["event"] == "E7")
    assert [p for p, e in added_by().items() if e == "E7"] == []


def test_nothing_is_written_for_h1_alg_latex_at_e15():
    latex = name_of("H1-ALG-LATEX")
    for relative in [p for p, e in added_by().items() if e == "E15" and p.endswith(".ttl")]:
        assert latex not in (POD / relative).read_text(encoding="utf-8"), relative


def test_u_imm_tdap_is_named_from_its_document_with_no_patient_and_one_revision():
    assert name_of("U-IMM-TDAP") == recomputed.record_name([name_of("D-U-IMM-TDAP r1"), ""])
    assert len(revisions_of(name_of("U-IMM-TDAP"))) == 1
    _, graph = versions(ALEX)[name_of("U-IMM-TDAP v1")]
    assert graph.value(URIRef(name_of("U-IMM-TDAP v1")), URIRef(REC + "patient")) is None


def test_every_conversion_holds_its_facts_graph_and_findings_and_each_event_has_the_scenarios_count():
    for folder in conversions(ALEX):
        assert sorted(p.name for p in folder.iterdir()) == ["facts.ttl", "findings.ttl", "graph.ttl"], folder
    counts = Counter(folder.parent.name for folder in conversions(ALEX))
    assert dict(counts) == CONVERSIONS_PER_EVENT


def test_every_handle_in_expected_handles_names_one_thing_in_the_pod_and_every_record_and_profile_has_one_handle():
    graph = final_pod()
    named = {handle: source_name(row) for kind in ("records", "profiles") for handle, row in sources()[kind].items()}
    records = set(graph.objects(None, REVISION_OF))
    profiles = set(graph.objects(None, URIRef(REC + "patient"))) - set(graph.subjects(RDF_TYPE, URIRef(REC + "Subject")))
    assert records | profiles == set(named.values())
    named |= {handle: handles()[handle] for kind in ("series", "judgments") for handle in sources()[kind]}
    assert len(set(named.values())) == len(named)
    assert [handle for kind in ("series", "judgments") for handle in sources()[kind]
            if (named[handle], None, None) not in graph] == []
