import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

import pytest
from pyparsing import ParseException, ParseResults
from rdflib import RDF, Graph, URIRef, Variable
from rdflib.paths import Path as PropertyPath
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

import contract
from contract import ROOT
from engines import TOKEN, marked_groups, opened, prepared

CASCADE = "https://ns.cascadeprotocol.org/cascade#"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def every_query():
    return sorted(p.relative_to(contract.QUERIES).as_posix() for p in contract.QUERIES.rglob("*.rq"))


def nodes(tree):
    if isinstance(tree, CompValue):
        yield tree
        for value in tree.values():
            yield from nodes(value)
    elif isinstance(tree, (list, tuple, ParseResults)):
        for value in tree:
            yield from nodes(value)


def is_subquery(part):
    return part.name == "GroupOrUnionGraphPattern" and [g.name for g in part["graph"]] == ["SubSelect"]


def has_a_subselect_after_a_pattern(tree):
    for group in nodes(tree):
        if group.name == "GroupGraphPatternSub":
            parts = list(group.get("part") or [])
            first_other = next((i for i, part in enumerate(parts) if not is_subquery(part)), len(parts))
            if any(is_subquery(part) for part in parts[first_other:]):
                return True
    return False


QUERY_FORMS = ("SelectQuery", "ConstructQuery", "AskQuery", "DescribeQuery", "SubSelect")
EXISTS_FORMS = ("Builtin_EXISTS", "Builtin_NOTEXISTS")
NESTED = {
    "nested-not-exists": "SELECT * WHERE { ?a ?b ?c FILTER NOT EXISTS { ?a ?b ?d FILTER NOT EXISTS { ?d ?e ?f } } }",
    "union-joined": "SELECT * WHERE { ?x ?y ?a { ?a ?b ?c } UNION { ?a ?d ?c } }",
    "union-in-a-group": "SELECT * WHERE { { { ?a ?b ?c } UNION { ?a ?d ?c } } }",
    "subquery-in-optional": "SELECT * WHERE { ?a ?b ?c OPTIONAL { ?a ?q ?r { SELECT ?r WHERE { ?r ?s ?t } } } }",
    "graph-in-a-group": "SELECT * WHERE { ?a ?b ?c OPTIONAL { GRAPH ?g { ?a ?d ?e } } }",
}


def nested_forms(tree):
    everything = list(nodes(tree))
    wheres = {id(n["where"]) for n in everything if n.name in QUERY_FORMS and n.get("where") is not None}
    branches = {id(branch) for n in everything if id(n) in wheres for part in n.get("part") or []
                if part.name == "GroupOrUnionGraphPattern" for branch in part["graph"]}
    found = []
    for node in everything:
        if node.name in EXISTS_FORMS and any(m.name in EXISTS_FORMS for m in nodes(node["graph"])):
            found.append("nested-not-exists")
        if node.name == "GroupGraphPatternSub":
            parts = list(node.get("part") or [])
            unions = [p for p in parts if p.name == "GroupOrUnionGraphPattern" and len(p["graph"]) > 1]
            if unions and len(parts) > 1:
                found.append("union-joined")
            elif unions and id(node) not in wheres:
                found.append("union-in-a-group")
            if any(p.name == "GraphGraphPattern" for p in parts) and not {id(node)} & (wheres | branches):
                found.append("graph-in-a-group")
        if node.name == "OptionalGraphPattern" and any(m.name == "SubSelect" for m in nodes(node["graph"])):
            found.append("subquery-in-optional")
    return found


def leaves(tree):
    if isinstance(tree, (CompValue, dict)):
        for value in tree.values():
            yield from leaves(value)
    elif isinstance(tree, (list, tuple, ParseResults)):
        for value in tree:
            yield from leaves(value)
    else:
        yield tree


def binds_record_outermost(tree):
    """Whether a triple pattern of the query's outermost group, outside any sub-select, MINUS, OPTIONAL or UNION, holds
    ?record: then a VALUES block opening that group binds it as an initial binding does (M4)."""
    [query] = [node for node in nodes(tree) if node.name == "SelectQuery"]
    blocks = [part for part in query["where"].get("part") or [] if part.name == "TriplesBlock"]
    return Variable("record") in set(leaves(blocks))


BOUND_RECORD = URIRef("urn:cascade:bound-record")


def keeps_every_row_of_a_record(subselect):
    """Whether a sub-select gives each record's rows whatever other records it is given: it cuts no rows off with
    LIMIT, OFFSET or HAVING, and groups, if it groups or aggregates at all, by ?record."""
    if "limitoffset" in subselect or "having" in subselect:
        return False
    grouped = "groupby" in subselect
    aggregated = any(node.name.startswith("Aggregate_") for node in nodes(subselect.get("projection")))
    return not (grouped or aggregated) or Variable("record") in set(leaves(subselect.get("groupby")))


def marked_groups_bind_record(text):
    """Whether every `# bound: ?record` line marks a group, and each group marked is inside a sub-select that keeps
    every row of a record and holds ?record in a triple pattern of its own, outside any nested pattern, so the VALUES
    block opening it binds ?record there as the one opening the outermost group does (M4)."""
    marks = len(re.findall(r"^\s*#\s*bound:", text, re.MULTILINE))
    if marks != len(marked_groups(text)):
        return False
    try:
        tree = parseQuery(opened(text, marked_groups(text), [BOUND_RECORD]))
    except ParseException:
        return False
    groups = []

    def walk(node, subselect):
        if isinstance(node, CompValue):
            parts = (node.get("part") or []) if node.name == "GroupGraphPatternSub" else []
            if any(part.name == "InlineData" and BOUND_RECORD in set(leaves(part)) for part in parts):
                blocks = [part for part in parts if part.name == "TriplesBlock"]
                groups.append(subselect is not None and keeps_every_row_of_a_record(subselect)
                              and Variable("record") in set(leaves(blocks)))
            for value in node.values():
                walk(value, node if node.name == "SubSelect" else subselect)
        elif isinstance(node, (list, tuple, ParseResults)):
            for value in node:
                walk(value, subselect)

    walk(tree, None)
    return len(groups) == marks and all(groups)


ENTRY_PLACEHOLDER = 'CONCAT("urn:cascade:entry:", SHA256(MIN(STR('


def iris(tree):
    if isinstance(tree, URIRef):
        yield tree
    elif isinstance(tree, PropertyPath):
        yield from iris(vars(tree))
    elif isinstance(tree, dict):
        for value in tree.values():
            yield from iris(value)
    elif isinstance(tree, (list, tuple, set, frozenset, ParseResults)):
        for value in tree:
            yield from iris(value)


@lru_cache(maxsize=None)
def reads(relative):
    return set(iris(prepared(contract.query(relative)).algebra["p"]))


@lru_cache(maxsize=None)
def writes(relative):
    template = prepared(contract.query(relative)).algebra["template"]
    return {o if p == RDF.type else p for s, p, o in template}


@lru_cache(maxsize=None)
def parsed(relative):
    return parseQuery(contract.query(relative))


def declared(relative):
    prolog, _ = parsed(relative)
    return [(declaration["prefix"], str(declaration["iri"])) for declaration in prolog]


@lru_cache(maxsize=None)
def namespaces_by_prefix():
    bindings = [binding for relative in every_query() for binding in declared(relative)]
    for path in ROOT.glob("ontologies/**/*.ttl"):
        graph = Graph(bind_namespaces="none").parse(path)
        bindings += [(prefix, str(namespace)) for prefix, namespace in graph.namespaces()]
    found = {}
    for prefix, namespace in bindings:
        found.setdefault(prefix, set()).add(namespace)
    return found


RECORDS = "derivations/records.rq"


def kinds_of_record():
    """Each row of the table in the derivation that says what a record is."""
    return [row for node in nodes(prepared(contract.query(RECORDS)).algebra) if node.name == "values"
            for row in node["res"]]


def record_types():
    """Each type the derivation that says what a record is lists, by the name of the view that writes it, if one does."""
    listed = {row[Variable("type")] for row in kinds_of_record()}
    views = {kind: name for name, view in contract.named("views").items() for kind in writes(view)}
    return {kind: views.get(kind) for kind in listed}


def kinds_named_out_of_place(relative, text):
    """The record types the query names though it is not about that one kind: only the derivation that lists them, a
    view, and a question named for a view, in the singular or the plural, may name its kind."""
    if relative == RECORDS:
        return set()
    views = record_types()
    named = set(iris(prepared(text).algebra)) & set(views)

    def singular(name):
        return "-" + "-".join(word.removesuffix("s") for word in words(name)) + "-"

    return {kind for kind in named if singular(views[kind]) not in singular(Path(relative).stem)}


KINDS = ("entry", "record", "judgment", "profile")
DERIVED_ABSENCES = {URIRef("http://purl.org/dc/terms/replaces"), URIRef("http://www.w3.org/ns/prov#invalidated"),
                    URIRef("http://www.w3.org/ns/prov#wasRevisionOf")}
RESTATING = {
    "not-exists": "SELECT ?j WHERE { ?j ?p ?o FILTER NOT EXISTS { ?s <http://purl.org/dc/terms/replaces> ?j } }",
    "minus": "SELECT ?j WHERE { ?j ?p ?o MINUS { ?s <http://www.w3.org/ns/prov#invalidated> ?j } }",
    "optional-bound": """SELECT ?r WHERE { ?r ?p ?o OPTIONAL { ?later <http://www.w3.org/ns/prov#wasRevisionOf> ?r }
                         FILTER (!BOUND(?later)) }""",
}


def every_question():
    return list(contract.questions().values())


def restated_absences(text):
    algebra = prepared(text).algebra
    bound = {node["arg"] for node in nodes(algebra) if node.name == "Builtin_BOUND"}
    found = []
    for node in nodes(algebra):
        if node.name == "Builtin_NOTEXISTS" and DERIVED_ABSENCES & set(iris(node["graph"])):
            found.append("not-exists")
        if node.name == "Minus" and DERIVED_ABSENCES & set(iris(node["p2"])):
            found.append("minus")
        if node.name == "LeftJoin" and DERIVED_ABSENCES & set(iris(node["p2"])) and bound & node["p2"]["_vars"]:
            found.append("optional-bound")
    return found


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def missing_prose(relative, text):
    """Why the query's leading comment does not do its job, or None: there is none, or it opens with the query's
    name."""
    prose = contract.prose(text)
    if not prose:
        return "no prose"
    name = words(Path(relative).stem)
    if words(prose)[:len(name)] == name:
        return "prose opening with its name"
    return None


def short(term):
    return None if term is None else str(term).rsplit("#", 1)[-1].removeprefix("urn:x:")


def reasons():
    """The named individuals of the vocabulary the derivations that leave records out name, but for the verdicts they
    read, which say what they are in an rdfs:comment."""
    graph = Graph().parse(ROOT / "ontologies" / "cascade.ttl")
    declared = {s for s in graph.subjects(RDF.type, URIRef("http://www.w3.org/2002/07/owl#NamedIndividual"))
                if (s, URIRef("http://www.w3.org/2000/01/rdf-schema#comment"), None) not in graph}
    named = {iri for relative in every_query() if relative.startswith("derivations/excluded-")
             for iri in iris(prepared(contract.query(relative)).algebra)}
    return frozenset(named & declared)


PUBLISHED = json.loads((ROOT / "tests" / "published-bytes.json").read_text())
PUBLISHED_FILES = ("runtime/rule-list/[0-9a-f]*.ttl", "queries/matcher/*.rq")


class TestQueryForm:
    """The form every query is written in · queries/**/*.rq

    Every query the vocabulary carries is one SPARQL file that a runtime runs as it is written. Each is written in the
    same form, so a runtime's engine, a reader and a tool that edits a query's text all find the same thing in every file.

    @rule naming N13
    """

    class TestGivenAnyQuery:
        def test_puts_every_sub_select_first_in_its_group(self):
            """puts every sub-select first in its group"""
            offenders = sorted(relative for relative in every_query() if has_a_subselect_after_a_pattern(parsed(relative)))
            assert offenders == []

        def test_is_one_flat_pattern(self):
            """is one flat pattern, with none of the five nested forms

            The five are a NOT EXISTS inside a NOT EXISTS, a UNION joined to other patterns, a UNION inside an inner group, a
            GRAPH inside an inner group, and a sub-select inside an OPTIONAL.
            """
            offenders = {relative: forms for relative in every_query() if (forms := nested_forms(parsed(relative)))}
            assert offenders == {}

        def test_declares_exactly_the_prefixes_it_uses_in_alphabetical_order(self):
            """declares exactly the prefixes it uses, in alphabetical order"""
            offenders = {}
            for relative in every_query():
                _, query = parsed(relative)
                used = sorted({node["prefix"] for node in nodes(query) if node.name == "pname"})
                declared_here = [prefix for prefix, _ in declared(relative)]
                if declared_here != used:
                    offenders[relative] = {"declared": declared_here, "used": used}
            assert offenders == {}

        def test_writes_with_its_prefix_every_iri_of_a_namespace_the_queries_declare(self):
            prefixes = {prefix for other in every_query() for prefix, _ in declared(other)}
            declared_namespaces = tuple(namespace for prefix in prefixes for namespace in namespaces_by_prefix()[prefix])
            spelled_out = {relative: sorted({str(iri) for iri in iris(parsed(relative)[1])
                                             if str(iri).startswith(declared_namespaces)})
                           for relative in every_query()}
            assert {relative: found for relative, found in spelled_out.items() if found} == {}

        def test_opens_with_prose_that_does_not_begin_with_its_own_name(self):
            offenders = {relative: why for relative in every_query()
                         if (why := missing_prose(relative, contract.query(relative)))}
            assert offenders == {}

        def test_names_a_view_entry_only_by_n13s_placeholder(self):
            """names a view entry only by N13's placeholder"""
            offenders = []
            for relative in every_query():
                text = contract.query(relative)
                if text.count('CONCAT("urn:cascade:entry:"') != text.count(ENTRY_PLACEHOLDER):
                    offenders.append(relative)
            assert offenders == []

    class TestGivenTheQueriesAndTheOntologyFilesTogether:
        def test_binds_each_prefix_to_one_namespace(self):
            assert {prefix: bound for prefix, bound in namespaces_by_prefix().items() if len(bound) > 1} == {}


class TestDerivationOrder:
    """The order a runtime runs the derivations and a lens in · queries/derivations/, queries/lenses/, ro-crate-metadata.json

    A derivation is a query whose answer a runtime adds to a pod's derived state before any view or question reads it. The
    root crate gives each one its position, and a lens runs last among them at one position.
    """

    class TestGivenTheRootCrate:
        def test_gives_every_derivation_and_lens_a_position(self):
            positions = contract.positions()
            derivations = list(contract.named("derivations").values())
            lenses = list(contract.named("lenses").values())
            assert sorted(positions) == sorted(derivations + lenses)

        def test_gives_every_lens_the_same_position(self):
            positions = contract.positions()
            assert len({positions[lens] for lens in contract.named("lenses").values()}) == 1

        def test_numbers_the_positions_from_1_with_no_gap(self):
            positions = contract.positions()
            derivations = list(contract.named("derivations").values())
            lenses = list(contract.named("lenses").values())
            steps = sorted(positions[step] for step in derivations + lenses[:1])
            assert steps == list(range(1, len(steps) + 1))

    class TestGivenALens:
        @pytest.mark.parametrize("lens", sorted(contract.named("lenses")))
        def test_reads_in_no_derivation_a_term_a_later_one_writes(self, lens):
            """reads, in no derivation, a term a later one writes"""
            steps = contract.derivations(lens)
            found = {(step, later, str(term)) for i, step in enumerate(steps) for later in steps[i + 1:]
                     for term in reads(step) & writes(later)}
            assert found == set()

        @pytest.mark.parametrize("lens", sorted(contract.named("lenses")))
        def test_writes_counts_under_lens_and_nothing_else(self, lens):
            """writes `cascade:countsUnderLens` and nothing else"""
            assert writes(contract.named("lenses")[lens]) == {URIRef(CASCADE + "countsUnderLens")}


class TestKindsOfRecord:
    """Kinds of record in the queries · queries/derivations/records.rq, queries/views/

    `derivations/records.rq` lists each kind of record with its word, and a view of its own lists the records of each
    kind. Every other query says `cascade:Record`, so a kind added later reaches it with no edit.
    """

    class TestGivenTheRecordsDerivation:
        """given `derivations/records.rq`"""

        def test_gives_each_kind_of_record_a_word_no_other_has(self):
            words = [str(row[Variable("kind")]) for row in kinds_of_record()]
            assert sorted(words) == sorted(set(words))

    class TestGivenAnyQuery:
        def test_names_a_record_type_only_when_it_is_about_that_one_kind(self):
            offenders = {relative: sorted(map(str, kinds)) for relative in every_query()
                         if (kinds := kinds_named_out_of_place(relative, contract.query(relative)))}
            assert offenders == {}

    class TestGivenAnyView:
        def test_types_every_record_it_reads_through_in_entry(self):
            """types every record it reads through `cascade:inEntry`

            Each is typed by a class the view names, not necessarily the view's own.
            """
            offenders = {}
            for relative in sorted(contract.named("views").values()):
                patterns = [t for node in nodes(prepared(contract.query(relative)).algebra["p"]) if node.name == "BGP"
                            for t in node["triples"]]
                typed = {s for s, p, o in patterns if p == RDF.type and isinstance(o, URIRef)}
                untyped = {s for s, p, o in patterns if p == URIRef(CASCADE + "inEntry")} - typed
                if untyped:
                    offenders[relative] = sorted(map(str, untyped))
            assert offenders == {}

    class TestGivenTheReasonsARecordIsInNoView:
        def test_names_each_reason_in_one_derivation_and_in_no_other_query(self):
            declared = reasons()
            named = {short(reason): [] for reason in declared}
            for relative in every_query():
                for reason in declared & set(iris(prepared(contract.query(relative)).algebra)):
                    named[short(reason)].append(relative)
            assert named == {
                "EnteredInErrorAtSource": ["derivations/excluded-at-source.rq"],
                "RefutedAtSource": ["derivations/excluded-at-source.rq"],
                "JudgedErroneous": ["derivations/excluded-by-judgment.rq"],
                "ImportJudgedErroneous": ["derivations/excluded-with-their-activity.rq"],
                "PatientProfileNotClaimed": ["derivations/excluded-for-their-patient.rq"],
                "NoPatient": ["derivations/excluded-for-their-patient.rq"],
            }

        def test_reads_in_why_it_is_in_no_view_only_the_recorded_reasons(self):
            """reads, in `record/Why it is in no view`, only the recorded reasons and their `rdfs:label`s"""
            terms = {URIRef(CASCADE + term) for term in ("Record", "leftOutFor", "leftOutReason", "leftOutBecauseOf")}
            assert reads(contract.questions()["record/Why it is in no view"]) == terms | {RDF.type, URIRef(RDFS_LABEL)}


class TestNamedQuestions:
    """Named questions an app asks a pod · queries/questions/

    A named question is a SELECT an app runs by its name, such as `pod/My active allergies`. It reads the derived state
    and the views, and never works out again what a derivation has recorded.
    """

    class TestGivenTheFolders:
        """given the folders of `queries/questions/`"""

        def test_holds_pod_and_one_folder_for_each_of_the_four_kinds(self):
            """holds `pod` and one folder for each of the four kinds

            A question outside `pod` is about one thing of its kind: an `entry`, a `record`, a `judgment` or a `profile`.
            """
            assert {Path(relative).parent.name for relative in every_question()} == {"pod", *KINDS}

    class TestGivenAnyQuestion:
        def test_is_a_select(self):
            offenders = sorted(relative for relative in every_question()
                               if prepared(contract.query(relative)).algebra.name != "SelectQuery")
            assert offenders == []

        def test_returns_for_every_label_column_the_column_it_is_named_for(self):
            """returns, for every column ending in `Label`, the column it is named for"""
            offenders = {}
            for relative in every_question():
                columns = {str(v) for v in prepared(contract.query(relative)).algebra["PV"]}
                labelled = {column[:-len("Label")] for column in columns if column.endswith("Label")}
                if not labelled <= columns:
                    offenders[relative] = sorted(labelled - columns)
            assert offenders == {}

        def test_asks_for_no_absence_the_derivations_already_record(self):
            """asks for no absence the derivations already record

            The absences are those `dct:replaces`, `prov:invalidated` and `prov:wasRevisionOf` say, asked for by a NOT EXISTS,
            a MINUS, or an OPTIONAL filtered to unbound.
            """
            offenders = {relative: restated for relative in every_question()
                         if (restated := restated_absences(contract.query(relative)))}
            assert offenders == {}

    class TestGivenAQuestionFiledUnderAKind:
        def test_returns_a_column_named_for_the_kind(self):
            offenders = sorted(relative for relative in every_question() if Path(relative).parent.name in KINDS
                               and Path(relative).parent.name not in
                               [str(v) for v in prepared(contract.query(relative)).algebra["PV"]])
            assert offenders == []


class TestMatcherComparisons:
    """Matcher comparisons a runtime binds to records · queries/matcher/, runtime/rule-list/

    A comparison is a query the matcher runs with `?record` bound to the records it compares. A runtime whose engine takes
    no initial binding writes a `VALUES ?record` block after the query's first brace and after each group marked
    `# bound: ?record`, so every comparison is written to take that block.

    @rule matcher M4
    @rule matcher M7
    """

    class TestGivenAnyComparison:
        def test_binds_record_in_a_triple_pattern_of_its_outermost_group(self):
            """binds `?record` in a triple pattern of its outermost group"""
            offenders = sorted(relative for relative in contract.named("matcher").values()
                               if not binds_record_outermost(parsed(relative)))
            assert offenders == []

        def test_opens_its_outermost_group_with_the_querys_first_brace(self):
            """opens its outermost group with the query's first brace"""
            offenders = []
            for relative in contract.named("matcher").values():
                head, where, _ = contract.query(relative).partition("\nWHERE {")
                if not where or "{" in head:
                    offenders.append(relative)
            assert sorted(offenders) == []

        def test_marks_only_a_group_inside_a_sub_select_that_keeps_every_row_of_a_record(self):
            """marks only a group inside a sub-select that keeps every row of a record and binds `?record` in a triple
            pattern of its own"""
            offenders = sorted(relative for relative in contract.named("matcher").values()
                               if not marked_groups_bind_record(contract.query(relative)))
            assert offenders == []

    class TestGivenAPublishedRuleListOrComparison:
        def test_keeps_the_bytes_it_was_published_with(self):
            """keeps the bytes it was published with

            A judgment names its rule's query by the hash of its bytes, so an edit in place makes every pod's judgments
            stale: a changed rule is a new file.
            """
            held = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PUBLISHED}
            edited = sorted(name for name in PUBLISHED if held[name] != PUBLISHED[name])
            assert not edited, f"publish a new file instead of editing {edited}"

        def test_is_listed_in_published_bytes(self):
            """is listed in `tests/published-bytes.json`"""
            listed = {p.relative_to(ROOT).as_posix() for pattern in PUBLISHED_FILES for p in ROOT.glob(pattern)}
            assert listed <= set(PUBLISHED), \
                f"a new rule list or matcher query is listed in tests/published-bytes.json: {sorted(listed - set(PUBLISHED))}"


class TestChecksOfTheQueryChecks:
    """Checks of the checks on a query's text · tests/test_queries.py

    Each rule above is checked by a function of this module. These cases show each function a query that breaks its rule,
    so a rule that every query keeps is known to be checked.
    """

    class TestBindsRecordOutermost:
        """`binds_record_outermost()`"""

        @pytest.mark.parametrize("form", [
            "SELECT ?record ?other WHERE { ?other ?p ?c { SELECT ?record ?c WHERE { ?record ?p ?c } } }",
            "SELECT ?record ?other WHERE { ?other ?p ?c OPTIONAL { ?record ?p ?c } }",
            "SELECT ?record ?other WHERE { ?other ?p ?c MINUS { ?record ?p ?c } }",
        ], ids=["a sub-select", "an OPTIONAL", "a MINUS"])
        def test_returns_false_for_record_bound_only_inside(self, form):
            """returns false for `?record` bound only inside"""
            assert not binds_record_outermost(parseQuery(form))

    class TestMarkedGroupsBindRecord:
        """`marked_groups_bind_record()`"""

        @pytest.mark.parametrize("form", [
            "SELECT ?record WHERE {\n  # bound: ?record\n  ?record ?p ?o { ?o ?q ?r }\n}",
            "SELECT ?record\n# bound: ?record\nWHERE { ?record ?p ?o }",
            "SELECT ?record WHERE { { SELECT ?record ?c\n  # bound: ?record\n  WHERE { OPTIONAL { ?record ?p ?c } } } ?record ?p ?c }",
            "SELECT ?record WHERE {\n  # bound: ?record\n  { SELECT ?record WHERE { ?record ?p ?c } } ?record ?p ?c }",
            "SELECT ?record WHERE { { SELECT (SAMPLE(?r) AS ?record) ?c\n  # bound: ?record\n  WHERE { ?record ?p ?c ; ?q ?r }\n"
            "  GROUP BY ?c } ?record ?p ?c }",
        ], ids=["a mark on a group in no sub-select", "a mark on no group", "a sub-select binding ?record only in an OPTIONAL",
                "a mark on the brace of a sub-select", "a sub-select grouped by another variable"])
        def test_returns_false_for(self, form):
            assert not marked_groups_bind_record(form)

    class TestEnginesToken:
        """`engines.TOKEN`"""

        def test_matches_no_iri_in_a_less_than_comparison(self):
            iris = [token.group() for token in TOKEN.finditer("FILTER (?x <3&&?y>1) ?s <urn:a#b> <> ?o FILTER (?a<=?b&&?b>=?c)")
                    if token.group().startswith("<")]
            assert iris == ["<urn:a#b>", "<>"]

    class TestNestedForms:
        """`nested_forms()`"""

        @pytest.mark.parametrize("form", sorted(NESTED))
        def test_returns_the_name_of(self, form):
            assert nested_forms(parseQuery(NESTED[form])) == [form]

        def test_returns_nothing_for_a_union_whose_branches_are_each_complete(self):
            assert nested_forms(parseQuery("""SELECT * WHERE {
              { ?a ?b ?c FILTER NOT EXISTS { ?a ?b ?d } OPTIONAL { ?a ?e ?f } }
              UNION { { SELECT ?a WHERE { ?a ?b ?c } } ?a ?d ?c }
            }""")) == []

        def test_returns_nothing_for_a_graph_around_a_whole_pattern(self):
            assert nested_forms(parseQuery("""SELECT * WHERE {
              { GRAPH ?g { ?a ?b ?c OPTIONAL { ?a ?e ?f } } ?g ?h ?i }
              UNION { VALUES ?a { <urn:x:a> } GRAPH ?g { ?a ?d ?c } }
            }""")) == []

    class TestKindsNamedOutOfPlace:
        """`kinds_named_out_of_place()`"""

        def test_returns_a_type_named_by_a_derivation_or_by_a_question_of_another_kind(self):
            allergy = URIRef("https://ns.cascadeprotocol.org/cascade#AllergyOrIntolerance")
            query = f"SELECT ?r WHERE {{ ?r a <{allergy}> }}"
            assert kinds_named_out_of_place("derivations/entries.rq", query) == {allergy}
            assert kinds_named_out_of_place("questions/pod/My active conditions.rq", query) == {allergy}
            medication = URIRef("https://ns.cascadeprotocol.org/cascade#PrescribedOrReportedMedication")
            query = f"SELECT ?r WHERE {{ ?r a <{medication}> }}"
            assert kinds_named_out_of_place("questions/pod/My procedures.rq", query) == {medication}

        def test_returns_nothing_for_a_view_or_a_question_named_for_the_kind(self):
            """returns nothing for a view or a question named for the kind, singular or plural"""
            allergy = URIRef("https://ns.cascadeprotocol.org/cascade#AllergyOrIntolerance")
            query = f"SELECT ?r WHERE {{ ?r a <{allergy}> }}"
            assert kinds_named_out_of_place("questions/pod/My active allergies.rq", query) == set()
            assert kinds_named_out_of_place("views/allergies.rq", query) == set()
            lab = URIRef("https://ns.cascadeprotocol.org/cascade#LaboratoryTestResult")
            assert kinds_named_out_of_place("questions/pod/My lab results.rq", f"SELECT ?r WHERE {{ ?r a <{lab}> }}") == set()
            medication = URIRef("https://ns.cascadeprotocol.org/cascade#PrescribedOrReportedMedication")
            query = f"SELECT ?r WHERE {{ ?r a <{medication}> }}"
            assert kinds_named_out_of_place("questions/pod/My medication history.rq", query) == set()

    class TestRestatedAbsences:
        """`restated_absences()`"""

        @pytest.mark.parametrize("form", sorted(RESTATING))
        def test_returns_the_name_of(self, form):
            assert restated_absences(RESTATING[form]) == [form]

        def test_returns_nothing_for_a_term_the_query_only_reads(self):
            assert restated_absences("""SELECT ?j ?by WHERE {
              ?j ?p ?o OPTIONAL { ?by <http://purl.org/dc/terms/replaces> ?j } FILTER (BOUND(?o)) }""") == []

    class TestMissingProse:
        """`missing_prose()`"""

        def test_returns_no_prose_for_a_query_with_no_leading_comment(self):
            """returns `no prose` for a query with no leading comment"""
            assert missing_prose("pod/Which file states each thing.rq", "SELECT ?s WHERE { ?s ?p ?o }") == "no prose"

        def test_returns_prose_opening_with_its_name(self):
            """returns `prose opening with its name` for a comment that begins with the file's name"""
            query = "SELECT ?s WHERE { ?s ?p ?o }"
            assert missing_prose("pod/Which file states each thing.rq", "# Which file states each thing.\n" + query) == \
                "prose opening with its name"
            assert missing_prose("derivations/same-pairs.rq", "# Same pairs: ...\n" + query) == "prose opening with its name"

        def test_returns_none_for_prose_that_opens_otherwise(self):
            """returns None for prose that opens otherwise"""
            query = "SELECT ?s WHERE { ?s ?p ?o }"
            assert missing_prose("pod/Which file states each thing.rq", "# Each file is its own graph.\n" + query) is None
