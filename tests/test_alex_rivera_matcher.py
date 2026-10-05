from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

from alex_rivera import ALEX, EVERY_JUDGMENT, EXAMPLE, MATCHER, name
from cascade_pod import match, store
from examples import ROOT, pod_file

REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
PROV = Namespace("http://www.w3.org/ns/prov#")
QUERIES = ROOT / "queries" / "v1-draft"


def test_the_matcher_needs_no_file_names_or_event_list():
    e4_import = "urn:uuid:73627b29-8dd1-494f-9d5f-89b7b72d235d"
    pod = ALEX.story_store("oxigraph", "E4").triples()
    matcher = match.Matcher(pod, match.References(EXAMPLE / "references"), ALEX.event("E5")["at"], ALEX.address,
                            "oxigraph")
    written = Graph()
    for path, octets in matcher.take(e4_import).items():
        written += store.parsed_text(octets, ALEX.address + path)
    expected = {j: row for j, row in EVERY_JUDGMENT.items() if row.event == "E5"}
    assert sorted(expected) == ["J3", "J4", "J5", "J6", "J7"]
    assert set(written.subjects(RDF.type, JDG.Judgment)) == {name(j) for j in expected}
    for j, row in expected.items():
        assert set(written.objects(name(j), PROV.hadMember)) == {name(m) for m in row.members}, j
        assert written.value(name(j), JDG.justification) == JDG[row.justification], j


def test_every_matcher_judgment_in_alexs_pod_used_one_rule_list_whose_one_row_for_its_justification_says_what_ran():
    lists = {URIRef(f"urn:uuid:{path.stem}"): rows for path in sorted((EXAMPLE / "references").glob("*.ttl"))
             for rows in [store.parsed(path)] if (None, RDF.type, REC.MatcherRule) in rows}
    judged = 0
    for path in ALEX.files():
        graph = pod_file(ALEX, path) if path.startswith("judgments/") else Graph()
        for judgment in graph.subjects(PROV.wasAttributedTo, URIRef(MATCHER)):
            [used] = [u for u in graph.objects(judgment, PROV.used) if u in lists]
            rows = [r for r in lists[used].subjects(REC.justifiedAs, graph.value(judgment, JDG.justification))]
            assert len(rows) == 1, path
            assert (QUERIES / str(lists[used].value(rows[0], REC.query))).is_file(), path
            judged += 1
    assert judged == sum(1 for row in EVERY_JUDGMENT.values() if row.author == "matcher")
