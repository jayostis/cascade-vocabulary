from rdflib.namespace import RDF

import recomputed
from alex_rivera import EXAMPLE, PROV, REC, arrivals, final_pod, handles, source_name, sources
from cascade_pod import store


def test_each_records_first_revision_came_from_what_its_row_in_expected_handles_says_its_source_calls_it():
    graph = final_pod()
    for handle, row in sources()["records"].items():
        record = handles()[handle]
        first = arrivals(graph, record)[0]
        if "server" in row:
            assert str(graph.value(record, REC.sourceUrl)) == f"{row['server']}/{row['type']}/{row['id']}", handle
        elif "download" in row:
            octets = (EXAMPLE / row["download"]).read_bytes()
            assert str(graph.value(first, PROV.wasDerivedFrom)) == recomputed.ni_name(octets), handle
        else:
            [activity] = store.parsed(EXAMPLE / row["entry"]).subjects(RDF.type, PROV.Activity)
            assert graph.value(first, PROV.wasGeneratedBy) == activity, handle


def test_every_handle_in_expected_handles_names_one_thing_in_the_pod_and_every_record_and_profile_has_one_handle():
    graph = final_pod()
    named = {handle: source_name(row) for kind in ("records", "profiles") for handle, row in sources()[kind].items()}
    records = set(graph.objects(None, REC.revisionOf))
    profiles = set(graph.objects(None, REC.patient)) - set(graph.subjects(RDF.type, REC.Subject))
    assert records | profiles == set(named.values())
    named |= {handle: handles()[handle] for kind in ("series", "judgments") for handle in sources()[kind]}
    assert len(set(named.values())) == len(named)
    assert [handle for kind in ("series", "judgments") for handle in sources()[kind]
            if (named[handle], None, None) not in graph] == []
