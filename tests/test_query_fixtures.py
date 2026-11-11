from collections import Counter
from functools import cache
from pathlib import Path

import pytest
from rdflib import OWL, RDF, RDFS, Graph, URIRef

from contract import CASCADE, PROV, QUERIES, ROOT, built, derivations, named, query, questions
from engines import ENGINES, Oxigraph, bound_to_records, marked_groups
from manifests import Entry, entries, failure, lens_name, row
from pods import ADDRESS, FIXTURES, built_once, every_fixture, on_its_worker

LENSES = sorted(named("lenses"))
JUDGMENT = "https://ns.cascadeprotocol.org/cascade#Judgment"
ASKED = {**questions(), **{f"matcher/{name}": relative for name, relative in named("matcher").items()}}
ORDERED = {(QUERIES / relative).resolve() for relative in ASKED.values() if "ORDER BY" in query(relative)}
def entry_id(fixture, entry):
    """What a case's id says once of the fixture and its entry. A matcher fixture's entries are named for the fixture's
    own words, so an entry that begins with them is the id; one that begins or ends with two words or more of them adds
    what it does not repeat to the fixture's name; any other entry is joined to the fixture's name."""
    said, words = fixture.name.removeprefix("matcher-").split("-"), entry.name.split("-")
    if words[:len(said)] == said:
        return entry.name
    size = range(min(len(said), len(words)), 1, -1)
    begun = next((n for n in size if said[:n] == words[:n]), 0)
    ended = next((n for n in size if said[-n:] == words[-n:]), 0)
    left = words[begun:] if begun else words[:len(words) - ended]
    return "-".join([fixture.name, *(left if left != ["the"] else [])])


ENTRIES = [on_its_worker(fixture, entry, id=entry_id(fixture, entry), says=f"{fixture.comment} {entry.comment}")
           for fixture in FIXTURES for entry in entries(fixture.manifest)]


@cache
def answers(fixture, lens):
    """The rows of every question and every matcher comparison."""
    held = built_once(fixture, "oxigraph", lens).store
    return {name: held.select(query(relative)) for name, relative in ASKED.items()}


def lenses_that_differ(fixture):
    """Each lens whose derived state over the fixture no lens before it gives: under the others every query reads the
    same pod."""
    found = {}
    for lens in LENSES:
        found.setdefault(frozenset(built_once(fixture, "oxigraph", lens).derived), lens)
    return sorted(found.values())


def holds_a_judgment(fixture):
    """Whether the fixture holds a judgment. A lens writes cascade:countsUnderLens and nothing else
    (TestDerivationOrder in test_queries.py), so lenses differ only in which judgments count: over a
    pod with no judgment every lens adds the same triples, and every later step reads the same pod."""
    return built_once(fixture, "oxigraph", LENSES[0]).store.ask(f"ASK {{ ?j a <{JUDGMENT}> }}")


SYMMETRIC = sorted(Graph().parse(ROOT / "ontologies" / "cascade.ttl").subjects(RDF.type, OWL.SymmetricProperty))


SHOWN_AND_LEFT_OUT_ALIKE = """
    PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
    SELECT ?record WHERE {
      ?record a cascade:Record .
      BIND (EXISTS { ?record cascade:inEntry [] } AS ?shown)
      BIND (EXISTS { ?record cascade:leftOutFor [] } AS ?leftOut)
      FILTER (?shown = ?leftOut)
    }"""


VOCABULARY = Graph().parse(ROOT / "ontologies" / "cascade.ttl")
ACTIVITIES = [PROV.Activity, *VOCABULARY.transitive_subjects(RDFS.subClassOf, PROV.Activity)]


def used_by_no_activity(store):
    kinds = " ".join(f"<{kind}>" for kind in dict.fromkeys(ACTIVITIES))
    return store.select(f"SELECT DISTINCT ?s WHERE {{ ?s <{PROV.used}> [] "
                        f"FILTER NOT EXISTS {{ VALUES ?kind {{ {kinds} }} ?s a ?kind }} }}")


MARKED = {name: relative for name, relative in named("matcher").items() if marked_groups(query(relative))}
MADE_FROM = {relative: named("matcher")[name.removesuffix(suffix)] for name, relative in named("matcher").items()
             for suffix in ("-bound-per-side", "-key-joined-first") if name.endswith(suffix)}
CURRENT_VERSIONS = "SELECT DISTINCT ?record WHERE { ?record <http://purl.org/pav/hasCurrentVersion> [] }"


PERSONS_JUDGMENTS = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
    SELECT ?judgment WHERE { ?judgment a cascade:Judgment ; prov:wasAttributedTo/a prov:Person }"""


MATCHER_FIXTURES = [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES if fixture.name.startswith("matcher-")]
ORDERED_ENTRIES = [case for case in ENTRIES if Path(case.values[1].query).resolve() in ORDERED]


def rows_of(store, text):
    return Counter(row(found) for found in store.select(text))


def every_other_current_record(store):
    return sorted(str(found["record"]) for found in store.select(CURRENT_VERSIONS))[::2]


class TestWhatEachQueryGives:
    """What each query gives over a small pod · tests/fixtures/*/manifest.ttl

    A fixture is a few Turtle files laid out as a pod, with a manifest of the rows that queries give over it. Each fixture
    shows one behaviour, and a runtime whose engine gives other rows over the same files has that behaviour wrong.
    """

    class TestGivenAQueryAFixturesManifestLists:
        """given a query that a fixture's manifest lists"""

        @pytest.mark.parametrize("fixture, entry", ENTRIES)
        def test_gives_the_rows_the_manifest_expects_on_each_engine(self, fixture, entry):
            """gives the rows the manifest expects, on each engine

            For each query a fixture's manifest lists, the fixture is built on Oxigraph and on rdflib under the entry's
            lens, the query is run on each, and its rows are compared with the entry's expected result; an engine that
            gives other rows fails.
            """
            stores = {engine: built_once(fixture, engine, lens_name(entry.lens)).store for engine in sorted(ENGINES)}
            failed = {engine: why for engine, store in stores.items() if (why := failure(entry, store))}
            assert not failed, "\n\n".join(f"on {engine}:\n{why}" for engine, why in failed.items())

        @pytest.mark.parametrize("fixture, entry", ORDERED_ENTRIES)
        def test_gives_an_ordered_querys_rows_in_one_order_on_both_engines(self, fixture, entry):
            """gives an ordered query's rows in one order on both engines

            For each manifest entry whose query has an ORDER BY, the rows from Oxigraph and from rdflib are compared as
            lists: they must be equal row for row, not only as sets.
            """
            stores = {engine: built_once(fixture, engine, lens_name(entry.lens)).store for engine in sorted(ENGINES)}
            text = Path(entry.query).read_text(encoding="utf-8")
            one, other = (store.select(text) for store in stores.values())
            assert one == other

    class TestGivenConditionsWhoseDatesCannotTell:
        """given `conditions-whose-dates-cannot-tell`"""

        @pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES
                                             if fixture.folder.name == "conditions-whose-dates-cannot-tell"])
        def test_lists_the_rows_of_my_active_conditions_by_condition_then_entry(self, fixture):
            """lists the rows of `pod/My active conditions` by condition, then by entry"""
            lens = lenses_that_differ(fixture)[0]
            rows = answers(fixture, lens)["pod/My active conditions"]
            keys = [(str(row["condition"]), str(row["entry"])) for row in rows]
            assert len(keys) > 1 and keys == sorted(keys)

    class TestGivenTheFixturesTogether:
        def test_leaves_no_query_without_a_fixture_over_which_it_adds_a_triple_or_gives_a_row(self):
            """leaves no query without a fixture over which it adds a triple or gives a row

            Takes every derivation, lens, view and question or comparison, and strikes off each that, over some fixture,
            adds a triple to the derived state, makes a view file hold a subject of its own, or (under a lens that
            matters there) gives rows; any query left unstruck is never shown to do anything by a fixture.
            """
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


class TestDerivedStateOnTwoEngines:
    """Derived state two engines build alike · queries/derivations/, queries/lenses/, queries/views/

    A pod's derived state is what the derivations and a lens add to it, and the views are written from it. The suite builds
    every fixture on Oxigraph and on rdflib, so a query that only one engine reads as written shows here.
    """

    class TestGivenAnyFixture:
        @every_fixture
        def test_builds_the_same_derived_state_and_the_same_files_on_both_engines(self, fixture):
            """builds the same derived state and the same files on both engines

            Each fixture is built on Oxigraph and on rdflib, under every lens if it holds a judgment and under the first
            otherwise; the triples each derivation adds, and the files written, are compared between the two builds.
            """
            judged = holds_a_judgment(fixture)
            for lens in LENSES if judged else LENSES[:1]:
                one, other = (built_once(fixture, engine, lens) for engine in sorted(ENGINES))
                assert one.added_by_step == other.added_by_step, lens
                assert one.files == other.files, lens

        @every_fixture
        def test_differs_between_the_lenses_only_when_the_pod_holds_a_judgment(self, fixture):
            """differs between the lenses only when the pod holds a judgment

            A fixture with no judgment must have one derived state under every lens, so the lenses that differ over it
            are the first lens alone.
            """
            assert holds_a_judgment(fixture) or lenses_that_differ(fixture) == LENSES[:1]

        @every_fixture
        def test_adds_only_triples_that_no_file_of_the_pod_states(self, fixture):
            """adds only triples that no file of the pod states

            For each lens, the triples the derivations add are compared with the triples of the fixture's own files: the
            added set is not empty, and shares no triple with them.
            """
            for lens in LENSES:
                build = built_once(fixture, "oxigraph", lens)
                files = set().union(*(build.store.triples(ADDRESS + path) for path in fixture.files()))
                assert build.derived and build.derived.isdisjoint(files), lens


class TestWhatIsTrueOfAnyPod:
    """What is true of any pod once its derivations have run · queries/derivations/, ontologies/cascade.ttl

    Some things hold of every pod, whatever it holds: a runtime or an app may rely on each without checking. They are
    asserted over every fixture, so a new fixture that breaks one fails.
    """

    class TestGivenAnyFixture:
        @every_fixture
        def test_holds_each_symmetric_property_both_ways(self, fixture):
            """holds each symmetric property both ways

            A runtime may then find what a record reaches through currentlySame by union-find, as an entry.
            """
            assert SYMMETRIC
            for lens in LENSES:
                store = built_once(fixture, "oxigraph", lens).store
                for predicate in SYMMETRIC:
                    one_way = f"SELECT ?a ?b WHERE {{ ?a <{predicate}> ?b FILTER NOT EXISTS {{ ?b <{predicate}> ?a }} }}"
                    assert store.select(one_way) == [], (lens, str(predicate))

        @every_fixture
        def test_leaves_a_record_out_of_every_view_exactly_when_a_derivation_recorded_a_reason(self, fixture):
            """leaves a record out of every view exactly when a derivation recorded a reason

            Under each lens, a record that is in a view (`cascade:inEntry`) and one that has a recorded reason to be
            left out (`cascade:leftOutFor`) are the same as each other: none has both or neither.
            """
            for lens in LENSES:
                assert built_once(fixture, "oxigraph", lens).store.select(SHOWN_AND_LEFT_OUT_ALIKE) == [], lens

        @every_fixture
        def test_holds_no_qualified_attribution(self, fixture):
            """holds no `prov:qualifiedAttribution`

            So no role sits on an attribution, which PROV does not allow: a role sits on the act that generated the
            document or judgment.
            """
            store = built_once(fixture, "oxigraph", LENSES[0]).store
            assert not store.ask(f"ASK {{ ?s <{PROV.qualifiedAttribution}> ?attribution }}")

        @every_fixture
        def test_states_prov_used_only_of_an_act(self, fixture):
            """states `prov:used` only of an act

            An entity says what it came from with prov:wasDerivedFrom: prov:used has an activity for its domain, and a
            subclass of prov:Activity is one.
            """
            assert used_by_no_activity(built_once(fixture, "oxigraph", LENSES[0]).store) == []

        @every_fixture
        def test_reads_a_persons_judgment_exactly_when_the_everyday_lens_counts_it(self, fixture):
            """reads a person's judgment in `derivations/revision-judgments.rq` exactly when the everyday lens counts it

            Each person-attributed judgment gets probe triples for three verdicts (erroneous, before, clock-discounted);
            the judgments `revision-judgments.rq` writes a result for are compared with those the everyday lens marks as
            counted, and must be the same set for each verdict.
            """
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


class TestMatcherComparisons:
    """Matcher comparisons a runtime binds to records · queries/matcher/, runtime/rule-list/"""

    class TestGivenAMatcherFixture:
        """given a fixture named `matcher-…`"""

        @pytest.mark.parametrize("fixture", MATCHER_FIXTURES)
        def test_gives_bound_in_the_groups_it_marks_the_rows_it_gives_unbound(self, fixture):
            """gives, bound in the groups it marks, the rows it gives unbound for the same records"""
            store = built_once(fixture, "oxigraph", LENSES[0]).store
            records = every_other_current_record(store)
            assert MARKED and records
            for name, relative in MARKED.items():
                text = query(relative)
                unbound = Counter(row(found) for found in store.select(text) if str(found["record"]) in records)
                assert rows_of(store, bound_to_records(text, records)) == unbound, name

        @pytest.mark.parametrize("fixture", MATCHER_FIXTURES)
        def test_gives_the_rows_of_the_comparison_it_was_made_from(self, fixture):
            """gives, bound per side or joined on its key first, the rows of the comparison it was made from

            Bound and unbound, on each engine; on rdflib only where the pair gives rows over the fixture, for two texts
            that agree on no rows show nothing, and rdflib parses each bound text again for every fixture.
            """
            oxigraph = built_once(fixture, "oxigraph", LENSES[0]).store
            records = every_other_current_record(oxigraph)
            assert MADE_FROM and records
            giving_rows = []
            for relative, made_from in MADE_FROM.items():
                for texts in ((query(relative), query(made_from)),
                              (bound_to_records(query(relative), records), bound_to_records(query(made_from), records))):
                    new, old = (rows_of(oxigraph, text) for text in texts)
                    assert new == old, ("oxigraph", relative)
                    if new:
                        giving_rows.append((relative, texts))
            if giving_rows:
                held = built_once(fixture, "rdflib", LENSES[0]).store
                for relative, texts in giving_rows:
                    new, old = (rows_of(held, text) for text in texts)
                    assert new == old, ("rdflib", relative)


class TestChecksOfTheFixtureTools:
    """Checks of the fixtures' own tools · tests/engines.py, tests/manifests.py

    The fixtures are built and compared by code in `tests/`. These cases show that code what it must catch.
    """

    class TestUsedByNoActivity:
        """`used_by_no_activity()`"""

        def test_returns_nothing_for_an_act_typed_only_as_a_subclass_of_prov_activity(self):
            """returns nothing for an act typed only as a subclass of `prov:Activity`"""
            act, thing = URIRef("urn:cascade:act:1"), URIRef("urn:cascade:thing:1")
            store = Oxigraph()
            store.add([(act, RDF.type, CASCADE.MatcherRun), (act, PROV.used, thing)])
            assert used_by_no_activity(store) == []

        def test_returns_a_thing_that_uses_something_and_is_no_act(self):
            """returns a thing that uses something and is no act

            Given an act that uses a thing and that thing using the act in turn, `used_by_no_activity()` returns exactly
            one subject: the thing.
            """
            act, thing = URIRef("urn:cascade:act:1"), URIRef("urn:cascade:thing:1")
            store = Oxigraph()
            store.add([(act, RDF.type, CASCADE.MatcherRun), (act, PROV.used, thing), (thing, PROV.used, act)])
            assert len(used_by_no_activity(store)) == 1

    class TestLoadGraphs:
        """`Store.load_graphs()`"""

        def test_loads_a_trig_files_default_graph_and_its_named_graph_alike_on_each_engine(self, tmp_path):
            """loads a TriG file's default graph and its named graph alike on each engine, against one base"""
            path = tmp_path / "rows.trig"
            path.write_text("<a> <urn:x:b> <urn:x:c> . <g> { <urn:x:d> <urn:x:e> <f> . }", encoding="utf-8")
            loaded = {}
            for name, engine in ENGINES.items():
                store = engine()
                store.load_graphs(path, ADDRESS + "rows.trig")
                loaded[name] = (store.triples(), store.triples(ADDRESS + "g"))
            assert {name: [len(graph) for graph in graphs] for name, graphs in loaded.items()} == {name: [1, 1] for name in ENGINES}
            assert loaded["oxigraph"] == loaded["rdflib"]

    class TestFailure:
        """`manifests.failure()`"""

        def test_returns_a_sentence_naming_the_variables(self, tmp_path):
            """returns a sentence naming the variables for a query whose columns are not its result's"""
            query, result = tmp_path / "q.rq", tmp_path / "r.srj"
            query.write_text("SELECT ?a WHERE { ?a ?b ?c }", encoding="utf-8")
            result.write_text('{"head": {"vars": ["z"]}, "results": {"bindings": []}}', encoding="utf-8")
            entry = Entry(iri="urn:x:e", name="e", types=frozenset(), lens=None, query=query, result=result)
            assert "variables" in (failure(entry, ENGINES["oxigraph"]()) or "")

    class TestQueryFixtureIds:
        """The ids of the cases over a fixture's manifest"""

        def test_says_each_fixture_once_and_keeps_each_id_under_100_characters(self):
            """says no phrase twice in an id, keeps it under 100 characters, and gives no two cases one id"""
            ids = [case.id for case in ENTRIES]
            said_twice = [i for i in ids if any(count > 1 for count in Counter(zip(*(i.split("-")[n:] for n in range(3)))).values())]
            assert not said_twice and not [i for i in ids if len(i) >= 100] and len(set(ids)) == len(ids)
