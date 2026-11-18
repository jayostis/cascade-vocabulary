import hashlib
from collections import Counter
from functools import cache
from pathlib import Path
from time import perf_counter

import pytest
from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef

from contract import CASCADE, PROV, QUERIES, ROOT, built, derivations, named, query, questions
from engines import ENGINES, Oxigraph, bound_to_records, marked_groups
from group_budget import group_of, over_budget, unseen
from manifests import Entry, entries, failure, lens_name, row
from pods import ADDRESS, FIXTURES, built_once, every_fixture, on_its_worker

LENSES = sorted(named("lenses"))
JUDGMENT = "https://ns.cascadeprotocol.org/cascade#Judgment"
ASKED = {**questions(), **{f"matcher/{name}": relative for name, relative in named("matcher").items()}}
ORDERED = {(QUERIES / relative).resolve() for relative in ASKED.values() if "ORDER BY" in query(relative)}


def entry_id(fixture, entry):
    """What a case's id says once of the fixture and its entry. Ignoring a leading `matcher-` and `the-`, an entry whose
    words run inside the fixture's is the fixture's name; a fixture whose words run inside the entry's is the entry's
    name, behind `matcher-` for a matcher fixture; any other pair is joined. No name is cut."""
    def words(name):
        return name.removeprefix("matcher-").removeprefix("the-").split("-")

    def runs_inside(inner, outer):
        return any(outer[start:start + len(inner)] == inner for start in range(len(outer) - len(inner) + 1))

    said, entered = words(fixture.name), words(entry.name)
    if runs_inside(entered, said):
        return fixture.name
    if runs_inside(said, entered):
        return f"matcher-{entry.name}" if fixture.name.startswith("matcher-") and not entry.name.startswith("matcher-") else entry.name
    return f"{fixture.name}-{entry.name}"


SLOW_ON_RDFLIB = ("matcher-same-variation-through-table", "matcher-same-result-by-value-and-unit",
                  "matcher-same-product-code", "matcher-same-note-type-and-text")


def slow_on_rdflib(fixture):
    """Whether a case of the fixture takes seconds on rdflib, which evaluates a comparison once for each record it is
    bound to: the fixture's cases are each a part of its group, built again on the worker that draws one."""
    return fixture.name.startswith(SLOW_ON_RDFLIB)


ENTRIES = [on_its_worker(fixture, entry, id=entry_id(fixture, entry), says=f"{fixture.comment} {entry.comment}",
                         part=entry.name if slow_on_rdflib(fixture) else None)
           for fixture in FIXTURES for entry in entries(fixture.manifest)]


@cache
def answers(fixture, lens):
    """The rows of every question and every matcher comparison."""
    held = built_once(fixture, "oxigraph", lens).store
    return {name: held.select(query(relative)) for name, relative in ASKED.items()}


def listing_most_unlisted_queries_first():
    """The fixtures, each after the ones that list the most queries no fixture before it lists, then those that list
    none, the more a fixture lists first: a fixture lists a query to show what it gives."""
    listed = {}
    for case in ENTRIES:
        listed.setdefault(case.values[0], set()).add(Path(case.values[1].query).resolve())
    ordered, unlisted = [], {(QUERIES / relative).resolve() for relative in ASKED.values()}
    while unlisted:
        fixture = max(listed, key=lambda fixture: len(listed[fixture] & unlisted), default=None)
        if fixture is None or not listed[fixture] & unlisted:
            break
        ordered.append(fixture)
        unlisted -= listed.pop(fixture)
    return ordered + sorted((fixture for fixture in FIXTURES if fixture not in ordered),
                            key=lambda fixture: -len(listed.get(fixture, ())))


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
             for suffix in ("-bound-per-side", "-key-joined-first", "-others-by-code-and-instant", "-others-by-code-and-day")
             if name.endswith(suffix) and name.removesuffix(suffix) in named("matcher")}
CURRENT_VERSIONS = "SELECT DISTINCT ?record WHERE { ?record <http://purl.org/pav/hasCurrentVersion> [] }"


PERSONS_JUDGMENTS = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
    SELECT ?judgment WHERE { ?judgment a cascade:Judgment ; prov:wasAttributedTo/a prov:Person }"""


MATCHER_FIXTURES = [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES if fixture.name.startswith("matcher-")]
COMPARISONS_MADE_FROM = [
    on_its_worker(fixture, [relative], id=f"{fixture.name}-{Path(relative).stem}", part=Path(relative).stem)
    for fixture in FIXTURES if slow_on_rdflib(fixture) for relative in MADE_FROM
] + [on_its_worker(fixture, list(MADE_FROM), id=fixture.name)
     for fixture in FIXTURES if fixture.name.startswith("matcher-") and not slow_on_rdflib(fixture)]
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

    class TestGivenAnImmunizationASecondSourceJoins:
        """given `a-second-source-joins-an-immunization`, its pod built with and without each original"""

        JOINS = next(fixture for fixture in FIXTURES if fixture.name == "a-second-source-joins-an-immunization")
        PORTAL, DOWNLOAD = URIRef("urn:x:mmrFromPortal"), URIRef("urn:x:mmrFromDownload")

        @staticmethod
        def entry_named_from(member):
            return URIRef(f"{ADDRESS}clinical/immunizations.ttl#{hashlib.sha256(str(member).encode()).hexdigest()}")

        def asked(self, question, record, without):
            store = built_once(self.JOINS, "oxigraph", LENSES[0], frozenset(without)).store
            return store.select(bound_to_records(query(questions()[question]), [str(record)]))

        def shows(self, record, *without):
            return {(row["record"], row["entry"]) for row in self.asked("record/Which entry shows it", record, without)}

        @pytest.mark.xdist_group(JOINS.name)
        def test_shows_the_first_record_in_the_entry_renamed_for_both_records_once_the_second_joins(self):
            """shows the first record, once the second source joins, in the entry renamed from the record that sorts first, which holds both"""
            before = self.shows(self.PORTAL, "download.ttl", "judgments.ttl")
            after = self.shows(self.PORTAL) | self.shows(self.DOWNLOAD)
            renamed = self.entry_named_from(self.DOWNLOAD)
            assert before == {(self.PORTAL, self.entry_named_from(self.PORTAL))}
            assert after == {(self.PORTAL, renamed), (self.DOWNLOAD, renamed)}

        @pytest.mark.xdist_group(JOINS.name)
        def test_shows_a_record_whose_original_was_removed_in_no_entry_and_gives_no_reason(self):
            """shows a record whose original was removed in no entry once the pod is rebuilt, and gives no reason it is in none

            So the pod no longer holds it, which a record hidden from every view, with its reason, is not.
            """
            removed = ("portal.ttl",)
            assert self.shows(self.PORTAL, *removed) == set()
            assert self.asked("record/Why it is in no view", self.PORTAL, removed) == []
            assert self.shows(self.DOWNLOAD, *removed) == {(self.DOWNLOAD, self.entry_named_from(self.DOWNLOAD))}

    class TestGivenTheFixturesTogether:
        def test_leaves_no_query_without_a_fixture_over_which_it_adds_a_triple_or_gives_a_row(self):
            """leaves no query without a fixture over which it adds a triple or gives a row

            Takes every derivation, lens, view and question or comparison, and strikes off each that, over some fixture,
            adds a triple to the derived state, makes a view file hold a subject of its own, or (under a lens that
            matters there) gives rows; any query left unstruck is never shown to do anything by a fixture. A fixture that
            holds no judgment is read under the first lens only, for every lens gives it one derived state, and a question
            is run only until some fixture strikes it off. The fixtures are taken in the order that reaches every query a
            manifest lists soonest, and no more are built once none is left.
            """
            quiet = {*derivations(LENSES[0]), *named("lenses").values(), *built().values(), *ASKED.values()}
            for fixture in listing_most_unlisted_queries_first():
                if not quiet:
                    break
                judged = holds_a_judgment(fixture)
                differing = lenses_that_differ(fixture) if judged else LENSES[:1]
                for lens in LENSES if judged else LENSES[:1]:
                    build = built_once(fixture, "oxigraph", lens)
                    quiet -= {step for step, added in build.added_by_step.items() if added}
                    quiet -= {built()[path] for path, triples in build.files.items()
                              if any(subject != URIRef(ADDRESS + path) for subject, _, _ in triples)}
                    if lens in differing:
                        quiet -= {relative for relative in set(ASKED.values()) & quiet if build.store.gives_a_row(query(relative))}
            assert quiet == set()

    class TestGivenThreeHundredMachineDifferents:
        """given three hundred counting Differents of a machine, half of them over a pair a person judged Same, built in the test"""

        def test_gives_the_pairs_no_person_judged_same_within_five_seconds(self):
            """gives the pairs no person judged Same, as `derivations/different-pairs.rq`, within five seconds

            A form of the query that tests, for each Different, a person's Same over its pair under a filter takes about
            twenty seconds at this size on Oxigraph and grows with its cube; the query takes about a tenth of a second.
            """
            urn = lambda name: URIRef(f"urn:x:{name}")
            triples = [(urn("matcher"), RDF.type, PROV.SoftwareAgent), (urn("person"), RDF.type, PROV.Person)]
            for n in range(300):
                pair = urn(f"r{n}a"), urn(f"r{n}b")
                different = urn(f"different{n}")
                triples += [(different, CASCADE.countsUnderLens, Literal(True)), (different, CASCADE.verdict, CASCADE.Different),
                            (different, PROV.wasAttributedTo, urn("matcher")), *((different, PROV.hadMember, m) for m in pair)]
                if n % 2:
                    same = urn(f"same{n}")
                    triples += [(same, CASCADE.countsUnderLens, Literal(True)), (same, CASCADE.verdict, CASCADE.Same),
                                (same, PROV.wasAttributedTo, urn("person")), *((same, PROV.hadMember, m) for m in pair)]
            store = Oxigraph()
            store.add(triples)
            started = perf_counter()
            pairs = store.construct(query("derivations/different-pairs.rq"))
            assert perf_counter() - started < 5
            assert {(a, b) for a, _, b in pairs} == {(urn(f"r{n}{x}"), urn(f"r{n}{y}")) for n in range(0, 300, 2)
                                                     for x, y in (("a", "b"), ("b", "a"))}


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
        def test_reads_a_statements_member_not_in_the_pod_exactly_when_the_pod_states_nothing_of_it(self, fixture):
            """reads a statement's member as not in the pod exactly when the pod states nothing of it

            For each row of `record/Where each record a statement names is now`, under each lens that differs, the row
            reads "not in the pod" when every triple with the member as subject is one a derivation added, and "in no
            entry" when one is not, so a predicate a derivation comes to add about a member must join the query's list.
            It finds only a predicate that some fixture's absent member receives.
            """
            text = query(questions()["record/Where each record a statement names is now"])
            for lens in lenses_that_differ(fixture):
                build = built_once(fixture, "oxigraph", lens)
                added = {tuple(map(str, triple)) for triple in build.derived}
                for found in build.store.select(text):
                    outcome = str(found["outcome"])
                    if outcome not in ("not in the pod", "in no entry"):
                        continue
                    member = str(found["record"])
                    every = build.store.select(f"SELECT ?p ?o WHERE {{ {{ <{member}> ?p ?o }} "
                                               f"UNION {{ GRAPH ?g {{ <{member}> ?p ?o }} }} }}")
                    stated = {(member, str(each["p"]), str(each["o"])) for each in every} - added
                    assert bool(stated) == (outcome == "in no entry"), (lens, member, outcome, stated)

        @every_fixture
        def test_gives_each_derivation_the_same_answer_with_the_views_in_the_pod(self, fixture):
            """gives each derivation the same answer with the views in the pod

            The pod is built, which writes its views into it, and every derivation is run again over it: none adds a
            triple the pod does not already hold, as none does when it reads only statements and other derivations.
            """
            store = built_once(fixture, "oxigraph", LENSES[0]).store
            held = store.triples()
            assert [relative for relative in named("derivations").values()
                    if not store.construct(query(relative)) <= held] == []

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
            assert MARKED and MADE_FROM and records
            for name, relative in MARKED.items():
                text = query(relative)
                unbound = Counter(row(found) for found in store.select(text) if str(found["record"]) in records)
                assert rows_of(store, bound_to_records(text, records)) == unbound, name

        @pytest.mark.parametrize("fixture, relatives", COMPARISONS_MADE_FROM)
        def test_gives_the_rows_of_the_comparison_it_was_made_from(self, fixture, relatives):
            """gives, bound per side or joined on its key first, the rows of the comparison it was made from

            Bound and unbound, on each engine; on rdflib only where the pair gives rows over the fixture, for two texts
            that agree on no rows show nothing, and rdflib parses each bound text again for every fixture. Over a fixture
            whose pairs take rdflib seconds, each pair is a case of its own.
            """
            oxigraph = built_once(fixture, "oxigraph", LENSES[0]).store
            records = every_other_current_record(oxigraph)
            assert MADE_FROM and records
            giving_rows = []
            for relative in relatives:
                for texts in ((query(relative), query(MADE_FROM[relative])),
                              (bound_to_records(query(relative), records), bound_to_records(query(MADE_FROM[relative]), records))):
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
    """Checks of the fixtures' own tools · tests/engines.py, tests/manifests.py, tests/group_budget.py

    The fixtures are built and compared by code in `tests/`. These cases show that code what it must catch.
    """

    class TestOverBudget:
        """`group_budget.over_budget()`"""

        CASES = [("t.py::a[x]@one", 12.0), ("t.py::b[x]@one", 9.0), ("t.py::c[y]@two", 15.0), ("t.py::d", 99.0)]

        def test_adds_the_seconds_of_the_cases_of_a_group_and_lists_the_groups_over_longest_first(self):
            """adds the seconds of the cases of a group and lists the groups over the budget, longest first"""
            assert over_budget(self.CASES, 10) == [("one", 21.0), ("two", 15.0)]

        def test_counts_no_case_that_names_no_group_and_no_group_the_budget_does_not_name(self):
            """counts no case that names no group, and no group the budget does not name"""
            assert over_budget(self.CASES, 10, ["two"]) == [("two", 15.0)]
            assert over_budget([("t.py::d", 99.0)], 10) == []

        def test_lists_no_group_that_takes_exactly_the_budget(self):
            """lists no group that takes exactly the budget"""
            assert over_budget(self.CASES, 21.0) == []

        def test_takes_no_text_after_an_at_sign_in_a_parameter_for_a_group(self):
            """takes no text after an `@` inside a case's parameter for its group"""
            assert group_of("t.py::x[a@b]") is None
            assert group_of("t.py::x[a@b]@one") == "one"

        def test_lists_each_part_of_a_group_the_budget_names_by_itself(self):
            """lists each part of a group the budget names by itself, not the group's parts added up"""
            parts = [("t.py::a@one/x", 12.0), ("t.py::b@one/y", 9.0), ("t.py::c@one", 3.0), ("t.py::d@two/z", 30.0)]
            assert over_budget(parts, 10, ["one"]) == [("one/x", 12.0)]

        def test_names_a_group_no_case_ran_in_and_a_run_with_no_group_at_all(self):
            """names a listed group no case ran in, and says so of a run with no group at all, which no budget checks"""
            parts = [("t.py::a@one/x", 1.0), ("t.py::b@two", 1.0)]
            assert unseen(parts, ["one", "two"]) == []
            assert unseen(parts, ["one", "tow"]) == ["tow"]
            assert unseen(parts) == []
            assert unseen([("t.py::d", 99.0)]) == ["any group"]
            assert unseen([("t.py::d", 99.0)], ["one"]) == ["one"]

    class TestGivesARow:
        """`Oxigraph.gives_a_row()`"""

        def test_is_true_of_a_select_with_a_row_and_false_of_one_with_none(self):
            """is true of a select that gives a row and false of one that gives none"""
            store = Oxigraph()
            store.add([(URIRef("urn:x:a"), RDF.type, CASCADE.Record)])
            assert store.gives_a_row(f"SELECT ?s WHERE {{ ?s a <{CASCADE.Record}> }}")
            assert not store.gives_a_row(f"SELECT ?s WHERE {{ ?s a <{CASCADE.Judgment}> }}")

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
        """`entry_id()`"""

        def test_joins_no_two_names_when_one_contains_the_other_and_keeps_each_id_unique_and_under_120_characters(self):
            """joins no fixture name to an entry name when one contains the other, keeps each id under 120 characters, and gives no two cases one id"""
            def bare(name):
                return name.removeprefix("matcher-").removeprefix("the-")
            ids = [case.id for case in ENTRIES]
            joined = [case.id for case in ENTRIES
                      if case.id == f"{case.values[0].name}-{case.values[1].name}"
                      and (f"-{bare(case.values[1].name)}-" in f"-{bare(case.values[0].name)}-"
                           or f"-{bare(case.values[0].name)}-" in f"-{bare(case.values[1].name)}-")]
            assert not joined and not [i for i in ids if len(i) >= 120] and len(set(ids)) == len(ids)
