from functools import cache
from pathlib import Path

import pytest
from rdflib import URIRef

from contract import QUERIES, built, derivations, named, query, questions
from engines import ENGINES
from manifests import entries, failure, lens_name
from pods import ADDRESS, FIXTURES, built_once, every_fixture, on_its_worker

LENSES = sorted(named("lenses"))
JUDGMENT = "https://ns.cascadeprotocol.org/judgments/v1-draft#Judgment"
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
    """Whether the fixture holds a judgment. A lens writes rec:counts and nothing else
    (test_every_lens_writes_rec_counts_and_nothing_else), so lenses differ only in which judgments count: over a pod
    with no judgment every lens adds the same triples, and every later step reads the same pod."""
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
