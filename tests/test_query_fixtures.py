from collections import Counter
from functools import cache
from pathlib import Path

import pytest
from rdflib import RDF, URIRef

from contract import CASCADE, PROV, QUERIES, built, derivations, named, query, questions
from engines import ENGINES, bound_to_records, marked_groups
from manifests import Entry, entries, failure, lens_name, row
from pods import ADDRESS, FIXTURES, built_once, every_fixture, on_its_worker

LENSES = sorted(named("lenses"))
JUDGMENT = "https://ns.cascadeprotocol.org/cascade#Judgment"
ASKED = {**questions(), **{f"matcher/{name}": relative for name, relative in named("matcher").items()}}
ORDERED = {(QUERIES / relative).resolve() for relative in ASKED.values() if "ORDER BY" in query(relative)}
ENTRIES = [on_its_worker(fixture, entry, id=f"{fixture.name}-{entry.name}")
           for fixture in FIXTURES for entry in entries(fixture.manifest)]


@cache
def answers(fixture, lens):
    """The rows of every question and every matcher comparison."""
    held = built_once(fixture, "oxigraph", lens).store
    return {name: held.select(query(relative)) for name, relative in ASKED.items()}


@pytest.mark.parametrize("fixture, entry", ENTRIES)
def test_the_entry_gives_its_expected_rows_on_each_engine_and_an_ordered_question_gives_them_in_one_order(fixture, entry):
    stores = {engine: built_once(fixture, engine, lens_name(entry.lens)).store for engine in sorted(ENGINES)}
    failed = {engine: why for engine, store in stores.items() if (why := failure(entry, store))}
    assert not failed, "\n\n".join(f"on {engine}:\n{why}" for engine, why in failed.items())
    if Path(entry.query).resolve() in ORDERED:
        text = Path(entry.query).read_text(encoding="utf-8")
        one, other = (store.select(text) for store in stores.values())
        assert one == other


def lenses_that_differ(fixture):
    """Each lens whose derived state over the fixture no lens before it gives: under the others every query reads the
    same pod."""
    found = {}
    for lens in LENSES:
        found.setdefault(frozenset(built_once(fixture, "oxigraph", lens).derived), lens)
    return sorted(found.values())


def holds_a_judgment(fixture):
    """Whether the fixture holds a judgment. A lens writes cascade:countsUnderLens and nothing else
    (test_every_lens_writes_counts_under_lens_and_nothing_else), so lenses differ only in which judgments count: over a
    pod with no judgment every lens adds the same triples, and every later step reads the same pod."""
    return built_once(fixture, "oxigraph", LENSES[0]).store.ask(f"ASK {{ ?j a <{JUDGMENT}> }}")


@every_fixture
def test_oxigraph_and_rdflib_agree_on_the_derived_state_and_the_files_built_from_it(fixture):
    judged = holds_a_judgment(fixture)
    assert judged or lenses_that_differ(fixture) == LENSES[:1]
    for lens in LENSES if judged else LENSES[:1]:
        one, other = (built_once(fixture, engine, lens) for engine in sorted(ENGINES))
        assert one.added_by_step == other.added_by_step, lens
        assert one.files == other.files, lens


@every_fixture
def test_the_derived_state_is_not_empty_and_shares_no_triple_with_the_fixtures_files(fixture):
    for lens in LENSES:
        build = built_once(fixture, "oxigraph", lens)
        files = set().union(*(build.store.triples(ADDRESS + path) for path in fixture.files()))
        assert build.derived and build.derived.isdisjoint(files), lens


SHOWN_AND_LEFT_OUT_ALIKE = """
    PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
    SELECT ?record WHERE {
      ?record a cascade:Record .
      BIND (EXISTS { ?record cascade:inEntry [] } AS ?shown)
      BIND (EXISTS { ?record cascade:leftOutFor [] } AS ?leftOut)
      FILTER (?shown = ?leftOut)
    }"""


@every_fixture
def test_a_record_is_in_no_view_exactly_when_the_derivations_recorded_a_reason(fixture):
    for lens in LENSES:
        assert built_once(fixture, "oxigraph", lens).store.select(SHOWN_AND_LEFT_OUT_ALIKE) == [], lens


def test_every_derivation_lens_view_and_the_labels_add_a_triple_and_every_question_and_comparison_gives_a_row():
    quiet = {*derivations(LENSES[0]), *named("lenses").values(), *built().values(), *ASKED.values()}
    for fixture in FIXTURES:
        for lens in LENSES:
            build = built_once(fixture, "oxigraph", lens)
            quiet -= {step for step, added in build.added_by_step.items() if added}
            quiet -= {built()[path] for path, triples in build.files.items()
                      if any(subject != URIRef(ADDRESS + path) for subject, _, _ in triples)}
            if lens in lenses_that_differ(fixture):
                quiet -= {ASKED[name] for name, rows in answers(fixture, lens).items() if rows}
    assert quiet == set()


MARKED = {name: relative for name, relative in named("matcher").items() if marked_groups(query(relative))}
CURRENT_VERSIONS = "SELECT DISTINCT ?record WHERE { ?record <http://purl.org/pav/hasCurrentVersion> [] }"


@pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES
                                     if fixture.name.startswith("matcher-")])
def test_a_comparison_bound_in_the_groups_it_marks_gives_its_unbound_rows_of_the_records_bound(fixture):
    store = built_once(fixture, "oxigraph", LENSES[0]).store
    records = sorted(str(found["record"]) for found in store.select(CURRENT_VERSIONS))[::2]
    assert MARKED and records
    for name, relative in MARKED.items():
        text = query(relative)
        unbound = Counter(row(found) for found in store.select(text) if str(found["record"]) in records)
        assert Counter(row(found) for found in store.select(bound_to_records(text, records))) == unbound, name


def test_each_engine_loads_the_default_graph_of_a_trig_file_into_its_default_graph_against_one_base(tmp_path):
    path = tmp_path / "rows.trig"
    path.write_text("<a> <urn:x:b> <urn:x:c> . <g> { <urn:x:d> <urn:x:e> <f> . }", encoding="utf-8")
    loaded = {}
    for name, engine in ENGINES.items():
        store = engine()
        store.load_graphs(path, ADDRESS + "rows.trig")
        loaded[name] = (store.triples(), store.triples(ADDRESS + "g"))
    assert {name: [len(graph) for graph in graphs] for name, graphs in loaded.items()} == {name: [1, 1] for name in ENGINES}
    assert loaded["oxigraph"] == loaded["rdflib"]


@pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES
                                     if fixture.folder.name == "conditions-whose-dates-cannot-tell"])
def test_my_active_conditions_lists_the_conditions_by_name_then_entry(fixture):
    lens = lenses_that_differ(fixture)[0]
    rows = answers(fixture, lens)["pod/My active conditions"]
    keys = [(str(row["condition"]), str(row["entry"])) for row in rows]
    assert len(keys) > 1 and keys == sorted(keys)


def test_an_entry_fails_when_its_query_returns_other_variables_than_its_result_names(tmp_path):
    query, result = tmp_path / "q.rq", tmp_path / "r.srj"
    query.write_text("SELECT ?a WHERE { ?a ?b ?c }", encoding="utf-8")
    result.write_text('{"head": {"vars": ["z"]}, "results": {"bindings": []}}', encoding="utf-8")
    entry = Entry(iri="urn:x:e", name="e", types=frozenset(), lens=None, query=query, result=result)
    assert "variables" in (failure(entry, ENGINES["oxigraph"]()) or "")


PERSONS_JUDGMENTS = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
    SELECT ?judgment WHERE { ?judgment a cascade:Judgment ; prov:wasAttributedTo/a prov:Person }"""


@every_fixture
def test_the_ladder_reads_a_persons_judgment_exactly_when_the_everyday_lens_counts_it(fixture):
    store = ENGINES["oxigraph"]()
    for path in fixture.files():
        store.load(fixture.folder / path, ADDRESS + path)
    judgments = {row["judgment"] for row in store.select(PERSONS_JUDGMENTS)}
    probe = lambda judgment, role: URIRef(f"urn:probe:{role}:{judgment}")
    store.add({triple for judgment in judgments for triple in (
        (judgment, CASCADE.verdict, CASCADE.Erroneous), (judgment, PROV.hadMember, probe(judgment, "wrong")),
        (probe(judgment, "wrong"), RDF.type, CASCADE.Revision),
        (judgment, CASCADE.verdict, CASCADE.Before), (judgment, CASCADE.earlierMember, probe(judgment, "earlier")),
        (judgment, PROV.hadMember, probe(judgment, "later")),
        (judgment, CASCADE.verdict, CASCADE.ClockDiscounted), (judgment, PROV.hadMember, probe(judgment, "act")),
        (probe(judgment, "discounted"), PROV.wasGeneratedBy, probe(judgment, "act")),
        (probe(judgment, "discounted"), RDF.type, CASCADE.Revision))})
    read = store.construct(query("derivations/revision-judgments.rq"))
    counted = {judgment for judgment, _, _ in store.construct(query(named("lenses")["everyday"]))} & judgments
    assert {j for j in judgments if (probe(j, "wrong"), CASCADE.revisionJudgedErroneousBy, j) in read} == counted
    assert {j for j in judgments if (probe(j, "earlier"), CASCADE.judgedBefore, probe(j, "later")) in read} == counted
    assert {j for j in judgments if (probe(j, "discounted"), CASCADE.observationTimeDiscountedBy, j) in read} == counted
