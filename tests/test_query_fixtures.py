from collections import Counter
from functools import cache

import pytest
from rdflib import URIRef

from cascade_pod import manifest, vocabulary
from cascade_pod.pod import LAYOUT
from cascade_pod.store import ENGINES
from examples import FIXTURES, built, every_fixture, on_its_worker

LENSES = sorted(vocabulary.named("lenses"))
ASKED = {**vocabulary.questions(), **{f"matcher/{name}": relative for name, relative in vocabulary.named("matcher").items()}}
WRONG = {
    ("patient-profile-view", "whose-it-is-counted-as-with-no-record"):
        "rdflib gives the grouped subquery of 'Whose it is counted as' one group over no solutions, so with no version "
        "naming a patient it returns a row for every About; Oxigraph returns none",
}
ENTRIES = [on_its_worker(fixture, entry, id=f"{fixture.name}-{entry.name}",
                         marks=[pytest.mark.xfail(strict=True, reason=WRONG[fixture.name, entry.name])]
                         if (fixture.name, entry.name) in WRONG else [])
           for fixture in FIXTURES for entry in manifest.entries(fixture.manifest)]


@cache
def answers(fixture, engine, lens):
    """The rows of every question and every matcher comparison."""
    held = built(fixture, engine, lens).store
    return {name: held.select(vocabulary.query(relative)) for name, relative in ASKED.items()}


@pytest.mark.parametrize("fixture, entry", ENTRIES)
def test_the_entry_gives_its_expected_rows_on_each_engine(fixture, entry):
    outcomes = {engine: manifest.answered(entry, built(fixture, engine, manifest.lens_name(entry.lens)).store)
                for engine in sorted(ENGINES)}
    failed = {engine: why for engine, (outcome, why) in outcomes.items() if outcome != manifest.EARL.passed}
    assert not failed, "\n\n".join(f"on {engine}:\n{why}" for engine, why in failed.items())


ENGINES_DISAGREE = {
    ("patient-profile-view", "profile/Whose it is counted as"): WRONG["patient-profile-view",
                                                                      "whose-it-is-counted-as-with-no-record"],
    ("records-of-every-kind", "record/What each version says"):
        "SPARQL leaves open the order of two literals differing only in a language tag, and the engines choose apart",
}


def lenses_that_differ(fixture):
    """Each lens whose derived state over the fixture no lens before it gives: under the others every query reads the
    same pod."""
    found = {}
    for lens in LENSES:
        found.setdefault(frozenset(built(fixture, "oxigraph", lens).derived.triples), lens)
    return sorted(found.values())


def comparable(name, rows):
    """The rows in their order where the query orders them, and as a multiset where it leaves the order open."""
    if "ORDER BY" in vocabulary.query(ASKED[name]):
        return rows
    return Counter(frozenset(row.items()) for row in rows)


@every_fixture
def test_oxigraph_and_rdflib_agree_on_the_derived_state_the_files_built_from_it_and_every_questions_rows(fixture):
    known = {question for name, question in ENGINES_DISAGREE if name == fixture.name}
    for lens in LENSES:
        one, other = (built(fixture, engine, lens) for engine in sorted(ENGINES))
        assert one.derived.added_by_step == other.derived.added_by_step, lens
        assert one.files == other.files, lens
    for lens in lenses_that_differ(fixture):
        one, other = (answers(fixture, engine, lens) for engine in sorted(ENGINES))
        assert {name for name in one if comparable(name, one[name]) != comparable(name, other[name])} == known, lens


@every_fixture
def test_the_derived_state_is_not_empty_and_shares_no_triple_with_the_fixtures_files(fixture):
    for lens in LENSES:
        build = built(fixture, "oxigraph", lens)
        files = set().union(*(build.store.triples(fixture.address + path) for path in fixture.files()))
        assert build.derived.triples and build.derived.triples.isdisjoint(files), lens


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
        assert built(fixture, "oxigraph", lens).store.select(SHOWN_AND_LEFT_OUT_ALIKE) == [], lens


def test_every_derivation_lens_view_and_the_labels_add_a_triple_and_every_question_and_comparison_gives_a_row():
    quiet = {*vocabulary.derivations(LENSES[0]), *vocabulary.named("lenses").values(), *LAYOUT.built.values(),
             *ASKED.values()}
    for fixture in FIXTURES:
        for lens in LENSES:
            build = built(fixture, "oxigraph", lens)
            quiet -= {step for step, added in build.derived.added_by_step.items() if added}
            quiet -= {LAYOUT.built[path] for path, triples in build.files.items() if path in LAYOUT.built
                      and any(subject != URIRef(fixture.address + path) for subject, _, _ in triples)}
            if lens in lenses_that_differ(fixture):
                quiet -= {ASKED[name] for name, rows in answers(fixture, "oxigraph", lens).items() if rows}
    assert quiet == set()
