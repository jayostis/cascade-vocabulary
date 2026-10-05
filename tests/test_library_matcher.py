import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

import recomputed
from alex_rivera import ALEX, EVERY_JUDGMENT, EXAMPLE, MATCHER, name
from cascade_pod import Failure, match, store
from examples import ROOT, pod_file

REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
PROV = Namespace("http://www.w3.org/ns/prov#")
QUERIES = ROOT / "queries" / "v1-draft"
PREFIXES = """@prefix jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
"""
RULES, RULES_1 = "urn:uuid:00000000-0000-4000-8000-000000000001", "urn:uuid:00000000-0000-4000-8000-000000000002"


def rule(justification, query, digest=None):
    digest = digest or recomputed.ni_name((QUERIES / query).read_bytes())
    return f'[] a rec:MatcherRule ; rec:justifiedAs jdg:{justification} ; rec:appliesTo "Allergy" ; ' \
           f'rec:query "{query}" ; rec:queryHash <{digest}> .\n'


def tables(folder, rows, ships_with=RULES_1):
    folder.mkdir(exist_ok=True)
    (folder / "references.ttl").write_text(
        PREFIXES + f'<{RULES}> a rec:ReferenceSeries ; rdfs:label "Rules" ; rec:shipsWith <{ships_with}> .\n'
                   f'<{RULES_1}> a prov:Entity ; prov:specializationOf <{RULES}> .\n', encoding="utf-8")
    (folder / f"{RULES_1[len('urn:uuid:'):]}.ttl").write_text(PREFIXES + rows, encoding="utf-8")
    return match.References(folder)


def test_a_series_that_ships_with_a_version_it_does_not_list_is_a_failure_not_a_traceback(tmp_path):
    references = tables(tmp_path, rule("SameCode", "matcher/same-code.rq"), ships_with="urn:uuid:0")
    with pytest.raises(Failure, match="ships with"):
        references.current(URIRef(RULES), Graph())


REFUSED = {
    "a query that does not hash to its rule's hash":
        rule("SameCode", "matcher/same-code.rq", recomputed.ni_name(b"")),
    "a query outside matcher/": rule("SameCode", "views/allergies.rq"),
    "a rule without its hash":
        '[] a rec:MatcherRule ; rec:justifiedAs jdg:SameCode ; rec:query "matcher/same-code.rq" .\n',
    "two rules giving one justification":
        rule("SameCode", "matcher/same-code.rq") + rule("SameCode", "matcher/same-code-and-date.rq"),
}


@pytest.mark.parametrize("case", sorted(REFUSED))
def test_a_rule_list_the_matcher_cannot_trust_refuses_the_run_as_a_failure_not_a_traceback(case, tmp_path):
    with pytest.raises(Failure):
        match.Matcher(set(), tables(tmp_path, REFUSED[case]), "2026-01-01T00:00:00Z", "https://pod.example/", "rdflib")


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


def rule_lists():
    """Every version of a rule list in the repository, by its file, with its rows."""
    folders = [*ROOT.glob("example-pods/*/references"), *ROOT.glob("runtime/vectors/*/scripted-input/references")]
    found = {}
    for path in (path for folder in folders for path in sorted(folder.glob("*.ttl"))):
        rows = store.parsed(path)
        if (None, RDF.type, REC.MatcherRule) in rows:
            found[path.relative_to(ROOT).as_posix()] = rows
    return found


def test_every_rule_names_a_comparison_whose_bytes_hash_to_its_hash_but_the_one_a_vector_breaks():
    lists = rule_lists()
    assert len(lists) == 5
    mismatched = set()
    for path, rows in lists.items():
        for row in rows.subjects(RDF.type, REC.MatcherRule):
            query = str(rows.value(row, REC.query))
            assert query.startswith("matcher/"), path
            if recomputed.ni_name((QUERIES / query).read_bytes()) != str(rows.value(row, REC.queryHash)):
                mismatched.add((path.split("/")[2], query))
    assert mismatched == {("refusals", "matcher/same-code.rq")}


def test_every_matcher_judgment_in_alexs_pod_used_one_rule_list_whose_one_row_for_its_justification_says_what_ran():
    lists = {URIRef(f"urn:uuid:{path.rsplit('/', 1)[1][:-len('.ttl')]}"): rows for path, rows in rule_lists().items()
             if path.startswith("example-pods/alex-rivera/")}
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
