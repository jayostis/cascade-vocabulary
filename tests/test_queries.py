import re
from functools import lru_cache
from pathlib import Path

import pytest
from pyparsing import ParseResults
from rdflib import RDF, Graph, URIRef, Variable
from rdflib.paths import Path as PropertyPath
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

from cascade_pod import vocabulary
from cascade_pod.store import prepared
from examples import ROOT, queries_held

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def every_query():
    return sorted(p.relative_to(vocabulary.QUERIES).as_posix() for p in vocabulary.QUERIES.rglob("*.rq"))


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


QUERY_FORMS = ("SelectQuery", "ConstructQuery", "AskQuery", "DescribeQuery", "SubSelect")
EXISTS_FORMS = ("Builtin_EXISTS", "Builtin_NOTEXISTS")
NESTED = {
    "nested-not-exists": "SELECT * WHERE { ?a ?b ?c FILTER NOT EXISTS { ?a ?b ?d FILTER NOT EXISTS { ?d ?e ?f } } }",
    "union-joined": "SELECT * WHERE { ?x ?y ?a { ?a ?b ?c } UNION { ?a ?d ?c } }",
    "union-in-a-group": "SELECT * WHERE { { { ?a ?b ?c } UNION { ?a ?d ?c } } }",
    "subquery-in-optional": "SELECT * WHERE { ?a ?b ?c OPTIONAL { ?a ?q ?r { SELECT ?r WHERE { ?r ?s ?t } } } }",
    "graph-in-a-group": "SELECT * WHERE { ?a ?b ?c OPTIONAL { GRAPH ?g { ?a ?d ?e } } }",
}


def nested_forms(text):
    everything = list(nodes(parseQuery(text)))
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


@pytest.mark.parametrize("relative", every_query())
def test_every_subquery_comes_first_in_its_group(relative):
    for group in nodes(parsed(relative)):
        if group.name == "GroupGraphPatternSub":
            parts = list(group.get("part") or [])
            first_other = next((i for i, part in enumerate(parts) if not is_subquery(part)), len(parts))
            assert not any(is_subquery(part) for part in parts[first_other:]), relative


@pytest.mark.parametrize("relative", sorted(vocabulary.named("views").values()))
def test_every_view_reads_only_members_of_its_own_kind_from_entries(relative):
    patterns = [t for node in nodes(prepared(vocabulary.query(relative)).algebra["p"]) if node.name == "BGP"
                for t in node["triples"]]
    typed = {s for s, p, o in patterns if p == RDF.type and isinstance(o, URIRef)}
    assert {s for s, p, o in patterns if p == URIRef(REC + "inEntry")} <= typed


@pytest.mark.parametrize("relative", every_query())
def test_every_query_is_one_flat_pattern(relative):
    assert nested_forms(vocabulary.query(relative)) == []


@pytest.mark.parametrize("form", sorted(NESTED))
def test_the_flat_pattern_check_refuses_each_nested_form(form):
    assert nested_forms(NESTED[form]) == [form]


def test_the_flat_pattern_check_accepts_a_union_whose_branches_are_each_complete():
    assert nested_forms("""SELECT * WHERE {
      { ?a ?b ?c FILTER NOT EXISTS { ?a ?b ?d } OPTIONAL { ?a ?e ?f } }
      UNION { { SELECT ?a WHERE { ?a ?b ?c } } ?a ?d ?c }
    }""") == []


def test_the_flat_pattern_check_accepts_a_graph_around_a_whole_pattern():
    assert nested_forms("""SELECT * WHERE {
      { GRAPH ?g { ?a ?b ?c OPTIONAL { ?a ?e ?f } } ?g ?h ?i }
      UNION { VALUES ?a { <urn:x:a> } GRAPH ?g { ?a ?d ?c } }
    }""") == []


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
    return set(iris(prepared(vocabulary.query(relative)).algebra["p"]))


@lru_cache(maxsize=None)
def writes(relative):
    template = prepared(vocabulary.query(relative)).algebra["template"]
    return {o if p == RDF.type else p for s, p, o in template}


@pytest.mark.parametrize("lens", sorted(vocabulary.named("lenses")))
def test_no_derivation_reads_a_term_a_later_derivation_writes(lens):
    steps = vocabulary.derivations(lens)
    found = {(step, later, str(term)) for i, step in enumerate(steps) for later in steps[i + 1:]
             for term in reads(step) & writes(later)}
    assert found == set()


@pytest.mark.parametrize("lens", sorted(vocabulary.named("lenses")))
def test_every_lens_writes_rec_counts_and_nothing_else(lens):
    assert writes(vocabulary.named("lenses")[lens]) == {URIRef(REC + "counts")}


def test_each_derivation_has_a_position_of_its_own_and_every_lens_the_same_one():
    positions = vocabulary.positions()
    derivations = list(vocabulary.named("derivations").values())
    lenses = list(vocabulary.named("lenses").values())
    assert sorted(positions) == sorted(derivations + lenses)
    assert len({positions[lens] for lens in lenses}) == 1
    steps = sorted(positions[step] for step in derivations + lenses[:1])
    assert steps == list(range(1, len(steps) + 1))


@lru_cache(maxsize=None)
def parsed(relative):
    return parseQuery(vocabulary.query(relative))


def declared(relative):
    prolog, _ = parsed(relative)
    return [(declaration["prefix"], str(declaration["iri"])) for declaration in prolog]


@lru_cache(maxsize=None)
def namespaces():
    bindings = [binding for relative in every_query() for binding in declared(relative)]
    for path in ROOT.glob("ontologies/**/*.ttl"):
        graph = Graph(bind_namespaces="none").parse(path)
        bindings += [(prefix, str(namespace)) for prefix, namespace in graph.namespaces()]
    found = {}
    for prefix, namespace in bindings:
        found.setdefault(prefix, set()).add(namespace)
    return found


def test_every_prefix_names_the_same_namespace_in_every_query_and_every_vocabulary_file():
    assert {prefix: bound for prefix, bound in namespaces().items() if len(bound) > 1} == {}


@pytest.mark.parametrize("relative", every_query())
def test_every_query_declares_exactly_the_prefixes_it_uses_in_alphabetical_order(relative):
    _, query = parsed(relative)
    used = {node["prefix"] for node in nodes(query) if node.name == "pname"}
    assert [prefix for prefix, _ in declared(relative)] == sorted(used)


@pytest.mark.parametrize("relative", every_query())
def test_no_query_spells_out_an_iri_in_a_namespace_the_queries_declare(relative):
    prefixes = {prefix for other in every_query() for prefix, _ in declared(other)}
    declared_namespaces = tuple(namespace for prefix in prefixes for namespace in namespaces()[prefix])
    _, query = parsed(relative)
    assert {str(iri) for iri in iris(query) if str(iri).startswith(declared_namespaces)} == set()


RECORDS = "derivations/records.rq"


def kinds_of_record():
    """Each row of the table in the derivation that says what a record is."""
    return [row for node in nodes(prepared(vocabulary.query(RECORDS)).algebra) if node.name == "values"
            for row in node["res"]]


def record_types():
    """Each type the derivation that says what a record is lists, by the name of the view that writes it, if one does."""
    listed = {row[Variable("type")] for row in kinds_of_record()}
    views = {kind: name for name, view in vocabulary.named("views").items() for kind in writes(view)}
    return {kind: views.get(kind) for kind in listed}


def test_no_two_kinds_of_record_share_a_word():
    words = [str(row[Variable("kind")]) for row in kinds_of_record()]
    assert sorted(words) == sorted(set(words))


def kinds_named_out_of_place(relative, text):
    """The record types the query names though it is not about that one kind: only the derivation that lists them, a
    view, and a question named for a view may name its kind."""
    if relative == RECORDS:
        return set()
    views = record_types()
    named = set(iris(prepared(text).algebra)) & set(views)
    return {kind for kind in named if views[kind] not in words(Path(relative).stem)}


def test_the_kind_check_refuses_a_record_type_named_by_a_query_not_about_that_one_kind():
    allergy = URIRef("https://ns.cascadeprotocol.org/health/v1#AllergyRecord")
    query = f"SELECT ?r WHERE {{ ?r a <{allergy}> }}"
    assert kinds_named_out_of_place("derivations/entries.rq", query) == {allergy}
    assert kinds_named_out_of_place("questions/pod/My active conditions.rq", query) == {allergy}
    assert kinds_named_out_of_place("questions/pod/My active allergies.rq", query) == set()
    assert kinds_named_out_of_place("views/allergies.rq", query) == set()


@pytest.mark.parametrize("relative", every_query())
def test_a_query_names_a_record_type_only_when_it_is_about_that_one_kind(relative):
    assert kinds_named_out_of_place(relative, vocabulary.query(relative)) == set()


KINDS = ("entry", "record", "judgment", "profile")
DERIVED_ABSENCES = {URIRef("http://purl.org/nanopub/x/supersedes"), URIRef("http://purl.org/nanopub/x/retracts"),
                    URIRef("http://www.w3.org/ns/prov#wasRevisionOf")}
RESTATING = {
    "not-exists": "SELECT ?j WHERE { ?j ?p ?o FILTER NOT EXISTS { ?s <http://purl.org/nanopub/x/supersedes> ?j } }",
    "minus": "SELECT ?j WHERE { ?j ?p ?o MINUS { ?s <http://purl.org/nanopub/x/retracts> ?j } }",
    "optional-bound": """SELECT ?r WHERE { ?r ?p ?o OPTIONAL { ?later <http://www.w3.org/ns/prov#wasRevisionOf> ?r }
                         FILTER (!BOUND(?later)) }""",
}


def every_question():
    return list(vocabulary.questions().values())


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


@pytest.mark.parametrize("form", sorted(RESTATING))
def test_the_restating_check_refuses_each_way_of_asking_for_an_absence(form):
    assert restated_absences(RESTATING[form]) == [form]


def test_the_restating_check_accepts_a_term_the_query_only_reads():
    assert restated_absences("""SELECT ?j ?by WHERE {
      ?j ?p ?o OPTIONAL { ?by <http://purl.org/nanopub/x/supersedes> ?j } FILTER (BOUND(?o)) }""") == []


@pytest.mark.parametrize("relative", every_question())
def test_no_question_restates_a_derivation(relative):
    assert restated_absences(vocabulary.query(relative)) == []


@pytest.mark.parametrize("relative", every_question())
def test_every_question_is_a_select(relative):
    assert prepared(vocabulary.query(relative)).algebra.name == "SelectQuery"


def test_every_question_is_filed_under_the_pod_or_a_kind():
    assert {Path(relative).parent.name for relative in every_question()} == {"pod", *KINDS}


@pytest.mark.parametrize("relative", [q for q in every_question() if Path(q).parent.name in KINDS])
def test_every_question_outside_pod_returns_the_column_of_its_kind(relative):
    columns = [str(v) for v in prepared(vocabulary.query(relative)).algebra["PV"]]
    assert Path(relative).parent.name in columns


@pytest.mark.parametrize("relative", every_question())
def test_every_label_column_labels_a_column_of_the_question(relative):
    columns = {str(v) for v in prepared(vocabulary.query(relative)).algebra["PV"]}
    labelled = {column[:-len("Label")] for column in columns if column.endswith("Label")}
    assert labelled <= columns


def test_the_held_query_check_finds_a_query_in_a_string_and_nothing_else():
    source = 'TEXT = """SELECT ?s WHERE { ?s ?p ?o }"""\nNAME = "SELECT"\n'
    assert queries_held(source) == ["SELECT ?s WHERE { ?s ?p ?o }"]


@pytest.mark.parametrize("tool", sorted(p.relative_to(ROOT).as_posix()
                                         for folder in ("cascade_pod", "example-pods") for p in (ROOT / folder).rglob("*.py")))
def test_no_tool_holds_a_query(tool):
    assert queries_held((ROOT / tool).read_text(encoding="utf-8")) == []


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def missing_prose(relative, text):
    """Why the query's leading comment does not do its job, or None: there is none, or it opens with the query's
    name."""
    prose = vocabulary.prose(text)
    if not prose:
        return "no prose"
    name = words(Path(relative).stem)
    if words(prose)[:len(name)] == name:
        return "prose opening with its name"
    return None


def test_the_prose_check_refuses_a_query_with_no_prose_or_prose_opening_with_its_name():
    query = "SELECT ?s WHERE { ?s ?p ?o }"
    assert missing_prose("pod/Which file states each thing.rq", query) == "no prose"
    assert missing_prose("pod/Which file states each thing.rq", "# Which file states each thing.\n" + query) == \
        "prose opening with its name"
    assert missing_prose("derivations/same-pairs.rq", "# Same pairs: ...\n" + query) == "prose opening with its name"
    assert missing_prose("pod/Which file states each thing.rq", "# Each file is its own graph.\n" + query) is None


@pytest.mark.parametrize("relative", every_query())
def test_every_query_has_prose_that_does_not_open_with_its_name(relative):
    assert missing_prose(relative, vocabulary.query(relative)) is None


def short(term):
    return None if term is None else str(term).rsplit("#", 1)[-1].removeprefix("urn:x:")


def reasons():
    graph = Graph().parse(ROOT / "ontologies" / "records" / "v1-draft" / "records.ttl")
    return frozenset(s for s in graph.subjects(RDF.type, URIRef("http://www.w3.org/2002/07/owl#NamedIndividual"))
                     if str(s).startswith(REC))


def test_each_reason_a_record_is_in_no_view_is_named_by_one_derivation_and_by_no_other_query():
    declared = reasons()
    named = {short(reason): [] for reason in declared}
    for relative in every_query():
        for reason in declared & set(iris(prepared(vocabulary.query(relative)).algebra)):
            named[short(reason)].append(relative)
    assert named == {
        "EnteredInErrorAtSource": ["derivations/excluded-at-source.rq"],
        "RefutedAtSource": ["derivations/excluded-at-source.rq"],
        "JudgedErroneous": ["derivations/excluded-by-judgment.rq"],
        "ImportJudgedErroneous": ["derivations/excluded-with-their-activity.rq"],
        "PatientNotClaimed": ["derivations/excluded-for-their-patient.rq"],
        "NoPatient": ["derivations/excluded-for-their-patient.rq"],
    }


def test_why_it_is_in_no_view_reads_only_the_recorded_reasons_and_labels():
    terms = {URIRef(REC + term) for term in ("Record", "leftOutFor", "reason", "because")}
    assert reads(vocabulary.questions()["record/Why it is in no view"]) == terms | {RDF.type, URIRef(RDFS_LABEL)}
