from collections import Counter
from functools import cache

import pytest
from rdflib import URIRef

from contract import built, derivations, named, query, questions
from engines import ENGINES
from manifests import entries, failure, lens_name
from pods import ADDRESS, FIXTURES, built_once, every_fixture, on_its_worker

LENSES = sorted(named("lenses"))
ASKED = {**questions(), **{f"matcher/{name}": relative for name, relative in named("matcher").items()}}
ENTRIES = [on_its_worker(fixture, entry, id=f"{fixture.name}-{entry.name}")
           for fixture in FIXTURES for entry in entries(fixture.manifest)]


@cache
def answers(fixture, engine, lens):
    """The rows of every question and every matcher comparison."""
    held = built_once(fixture, engine, lens).store
    return {name: held.select(query(relative)) for name, relative in ASKED.items()}


@pytest.mark.parametrize("fixture, entry", ENTRIES)
def test_the_entry_gives_its_expected_rows_on_each_engine(fixture, entry):
    failed = {engine: why for engine in sorted(ENGINES)
              if (why := failure(entry, built_once(fixture, engine, lens_name(entry.lens)).store))}
    assert not failed, "\n\n".join(f"on {engine}:\n{why}" for engine, why in failed.items())


def lenses_that_differ(fixture):
    """Each lens whose derived state over the fixture no lens before it gives: under the others every query reads the
    same pod."""
    found = {}
    for lens in LENSES:
        found.setdefault(frozenset(built_once(fixture, "oxigraph", lens).derived), lens)
    return sorted(found.values())


def comparable(name, rows):
    """The rows in their order where the query orders them, and as a multiset where it leaves the order open."""
    if "ORDER BY" in query(ASKED[name]):
        return rows
    return Counter(frozenset(row.items()) for row in rows)


@every_fixture
def test_oxigraph_and_rdflib_agree_on_the_derived_state_the_files_built_from_it_and_every_questions_rows(fixture):
    for lens in LENSES:
        one, other = (built_once(fixture, engine, lens) for engine in sorted(ENGINES))
        assert one.added_by_step == other.added_by_step, lens
        assert one.files == other.files, lens
    for lens in lenses_that_differ(fixture):
        one, other = (answers(fixture, engine, lens) for engine in sorted(ENGINES))
        assert {name for name in one if comparable(name, one[name]) != comparable(name, other[name])} == set(), lens


@every_fixture
def test_the_derived_state_is_not_empty_and_shares_no_triple_with_the_fixtures_files(fixture):
    for lens in LENSES:
        build = built_once(fixture, "oxigraph", lens)
        files = set().union(*(build.store.triples(ADDRESS + path) for path in fixture.files()))
        assert build.derived and build.derived.isdisjoint(files), lens


SHOWN_AND_LEFT_OUT_ALIKE = """
    PREFIX rec: <https://ns.cascadeprotocol.org/records/v1-draft#>
    SELECT ?record WHERE {
      ?record a rec:Record .
      BIND (EXISTS { ?record rec:inEntry [] } AS ?shown)
      BIND (EXISTS { ?record rec:leftOutFor [] } AS ?leftOut)
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
                quiet -= {ASKED[name] for name, rows in answers(fixture, "oxigraph", lens).items() if rows}
    assert quiet == set()


def test_each_engine_loads_the_default_graph_of_a_trig_file_into_its_default_graph(tmp_path):
    path = tmp_path / "rows.trig"
    path.write_text("<urn:x:a> <urn:x:b> <urn:x:c> . <urn:x:g> { <urn:x:d> <urn:x:e> <urn:x:f> . }", encoding="utf-8")
    loaded = {}
    for name, engine in ENGINES.items():
        store = engine()
        store.load_graphs(path)
        loaded[name] = (store.triples(), store.triples("urn:x:g"))
    assert {name: [len(graph) for graph in graphs] for name, graphs in loaded.items()} == {name: [1, 1] for name in ENGINES}
    assert loaded["oxigraph"] == loaded["rdflib"]
