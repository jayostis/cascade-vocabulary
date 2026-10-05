import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest
from pyparsing import ParseResults
from rdflib import RDF, Graph, URIRef, Variable
from rdflib.paths import Path as PropertyPath
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

from cascade_pod import derive, store, vocabulary
from cascade_pod.pod import LABEL_FILE, NOT_RDF
from cascade_pod.store import Oxigraph
from examples import EXAMPLES, ROOT, every_example, every_example_and, queries_held

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"


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
def test_every_query_parses_on_rdflib_and_on_pyoxigraph(relative):
    text = vocabulary.query(relative)
    prepareQuery(text)
    Oxigraph().store.query(text)


@pytest.mark.parametrize("relative", every_query())
def test_every_subquery_comes_first_in_its_group(relative):
    for group in nodes(parseQuery(vocabulary.query(relative))):
        if group.name == "GroupGraphPatternSub":
            parts = list(group.get("part") or [])
            first_other = next((i for i, part in enumerate(parts) if not is_subquery(part)), len(parts))
            assert not any(is_subquery(part) for part in parts[first_other:]), relative


@pytest.mark.parametrize("relative", sorted(vocabulary.named("views").values()))
def test_every_view_reads_only_members_of_its_own_kind_from_entries(relative):
    patterns = [t for node in nodes(prepareQuery(vocabulary.query(relative)).algebra["p"]) if node.name == "BGP"
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


def reads(relative):
    return set(iris(prepareQuery(vocabulary.query(relative)).algebra["p"]))


def writes(relative):
    template = prepareQuery(vocabulary.query(relative)).algebra["template"]
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
    return [row for node in nodes(prepareQuery(vocabulary.query(RECORDS)).algebra) if node.name == "values"
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
    named = set(iris(prepareQuery(text).algebra)) & set(views)
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
    algebra = prepareQuery(text).algebra
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
    assert prepareQuery(vocabulary.query(relative)).algebra.name == "SelectQuery"


def test_every_question_is_filed_under_the_pod_or_a_kind():
    assert {Path(relative).parent.name for relative in every_question()} == {"pod", *KINDS}


@pytest.mark.parametrize("relative", [q for q in every_question() if Path(q).parent.name in KINDS])
def test_every_question_outside_pod_returns_the_column_of_its_kind(relative):
    columns = [str(v) for v in prepareQuery(vocabulary.query(relative)).algebra["PV"]]
    assert Path(relative).parent.name in columns


@pytest.mark.parametrize("relative", every_question())
def test_every_label_column_labels_a_column_of_the_question(relative):
    columns = {str(v) for v in prepareQuery(vocabulary.query(relative)).algebra["PV"]}
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


ENGINES = sorted(store.ENGINES)
LENSES = sorted(vocabulary.named("lenses"))
NEEDS_REVIEW = [relative for name, relative in vocabulary.questions().items() if name.endswith("/What needs review")]


def derived_state_views_and_reviews(example, engine, lens, through):
    held = example.story_store(engine, through)
    derived = derive.derive(held, lens).triples
    views = {view: held.construct(vocabulary.query(r)) for view, r in vocabulary.named("views").items()}
    reviews = {relative: held.select(vocabulary.query(relative)) for relative in NEEDS_REVIEW}
    return derived, views, reviews


@pytest.mark.parametrize("lens", LENSES)
@every_example_and("event", lambda example: [e["event"] for e in example.events])
def test_the_derived_state_each_view_and_what_needs_review_are_the_same_on_oxigraph_and_rdflib(example, event, lens):
    assert (derived_state_views_and_reviews(example, "oxigraph", lens, event)
            == derived_state_views_and_reviews(example, "rdflib", lens, event))


@lru_cache(maxsize=None)
def answers(example, engine, lens, through=None):
    held = example.build(engine, lens, through).store
    return {name: held.select(vocabulary.query(relative)) for name, relative in vocabulary.questions().items()}


@pytest.mark.parametrize("lens", LENSES)
@every_example
def test_every_question_gives_the_same_rows_in_the_same_order_on_oxigraph_and_rdflib(example, lens):
    assert answers(example, "oxigraph", lens) == answers(example, "rdflib", lens)


def test_every_question_has_an_answer_at_some_event():
    unanswered = set(vocabulary.questions())
    for example in EXAMPLES:
        for event in example.events:
            for lens in LENSES:
                unanswered -= {name for name, found in answers(example, "oxigraph", lens, event["event"]).items() if found}
    assert unanswered == set()


def final_graph(example):
    graph = Graph()
    for path in example.files() + example.derived:
        if not path.startswith(NOT_RDF):
            graph.parse(example.pod / path, format="turtle", publicID=example.address + path)
    return graph


RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


@every_example
def test_everything_labelled_has_exactly_one_label(example):
    graph = final_graph(example)
    labels = Counter(str(s) for s in graph.subjects(URIRef(RDFS_LABEL), None))
    kinds = "VALUES ?type { %s }" % " ".join(f"<{kind}>" for kind in sorted(record_types()))
    found = graph.query("""
        PREFIX cascade: <https://ns.cascadeprotocol.org/core/v1#>
        PREFIX jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX rec: <https://ns.cascadeprotocol.org/records/v1-draft#>
        SELECT DISTINCT ?thing WHERE {
          { %s ?thing a ?type ; ^rec:revisionOf [] }
          UNION { %s ?record a ?type ; ^rec:revisionOf [] . ?thing prov:specializationOf ?record }
          UNION { ?thing a rec:Revision }
          UNION { [] a rec:Revision ; prov:wasDerivedFrom ?thing }
          UNION { ?thing a jdg:Judgment }
          UNION { ?thing prov:specializationOf/a rec:ReferenceSeries }
          UNION { ?thing cascade:mergedFrom [] }
          UNION { [] a jdg:Judgment ; jdg:verdict jdg:About ; prov:hadMember ?thing }
          UNION { ?thing a rec:Subject }
        }""" % (kinds, kinds))
    everything = {str(row[0]) for row in found}
    assert everything
    assert {thing: labels[thing] for thing in everything if labels[thing] != 1} == {}
    address = example.address + LABEL_FILE
    own = Graph().parse(example.pod / LABEL_FILE, publicID=address)
    predicates = {(str(s) == address, str(p)) for s, p, _ in own}
    assert predicates - {(True, "http://www.w3.org/ns/prov#used")} == {(False, RDFS_LABEL), (True, str(RDF.type))}


@every_example
def test_no_two_labelled_things_share_a_label(example):
    graph = Graph().parse(example.pod / LABEL_FILE, publicID=example.address + LABEL_FILE)
    things = Counter(str(label) for label in graph.objects(None, URIRef(RDFS_LABEL)))
    assert {label: n for label, n in things.items() if n > 1} == {}


UNIT_PREFIXES = """
@prefix jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#> .
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
@prefix : <urn:x:> .
"""


def answer(engine, question, turtle, tmp_path):
    path = tmp_path / f"{engine}.ttl"
    path.write_text(UNIT_PREFIXES + turtle, encoding="utf-8")
    held = store.ENGINES[engine]()
    held.load(path, "urn:x:")
    return [{name: str(term) for name, term in row.items()}
            for row in held.select(vocabulary.query(vocabulary.questions()[question]))]


@pytest.mark.parametrize("engine", ENGINES)
def test_a_profile_named_by_two_hospitals_records_gives_each_hospitals_row_the_number_of_its_own_records(engine, tmp_path):
    found = answer(engine, "profile/Whose it is counted as", """
        :about a jdg:Judgment ; rec:counts true ; jdg:verdict jdg:About ; prov:hadMember :p ; jdg:subject :s .
        :v1 rec:patient :p ; prov:specializationOf :r1 . :rev1 rec:version :v1 ; prov:wasDerivedFrom :d1 .
        :v2 rec:patient :p ; prov:specializationOf :r2 . :rev2 rec:version :v2 ; prov:wasDerivedFrom :d2 .
        :v3 rec:patient :p ; prov:specializationOf :r3 . :rev3 rec:version :v3 ; prov:wasDerivedFrom :d2 .
        :d1 prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Meridian" ] ] .
        :d2 prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Larkspur" ] ] .
    """, tmp_path)
    assert sorted((row["hospital"], row["records"]) for row in found) == [("Larkspur", "2"), ("Meridian", "1")]


@pytest.mark.parametrize("engine", ENGINES)
def test_an_entry_lists_a_pair_still_joined_by_what_the_derivations_judged_currently_different(engine, tmp_path):
    found = answer(engine, "entry/What needs review", """
        :a rec:inEntry :entry ; jdg:currentlyDifferent :b .
        :b rec:inEntry :entry ; jdg:currentlyDifferent :a .
    """, tmp_path)
    assert [(row["entry"], row["record"], row["otherRecord"]) for row in found] == [("urn:x:entry", "urn:x:a", "urn:x:b")]


@pytest.mark.parametrize("engine", ENGINES)
def test_every_row_of_a_judgment_says_whether_it_counts_beside_what_happened_to_it(engine, tmp_path):
    found = answer(engine, "judgment/Whether it counts", """
        :old a jdg:Judgment .
        :new a jdg:Judgment ; rec:counts true ; npx:supersedes :old .
    """, tmp_path)
    assert sorted((row["judgment"], row["counts"], row.get("happened", "")) for row in found) == [
        ("urn:x:new", "true", ""), ("urn:x:old", "false", ""), ("urn:x:old", "false", "superseded")]


ENTERED_BY_THE_PERSON = """
    @prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
    @prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    :subject a rec:Subject .
    :condition a health:ConditionRecord .
    :conditionVersion prov:specializationOf :condition ; rec:patient :subject ; health:status "active" .
    :conditionRevision a rec:Revision ; rec:revisionOf :condition ; rec:version :conditionVersion ;
        prov:generatedAtTime "2027-01-01T00:00:00Z"^^xsd:dateTime .
    :allergy a health:AllergyRecord .
    :allergyVersion prov:specializationOf :allergy ; rec:patient :subject ; clinical:status "active" .
    :allergyRevision a rec:Revision ; rec:revisionOf :allergy ; rec:version :allergyVersion ;
        prov:generatedAtTime "2027-01-01T00:00:00Z"^^xsd:dateTime .
"""


@pytest.mark.parametrize("lens", LENSES)
@pytest.mark.parametrize("engine", ENGINES)
def test_a_status_the_person_entered_sets_a_conditions_entry_and_never_an_allergys(engine, lens, tmp_path):
    path = tmp_path / "pod.ttl"
    path.write_text(UNIT_PREFIXES + ENTERED_BY_THE_PERSON, encoding="utf-8")
    held = store.ENGINES[engine]()
    held.load(path, "urn:x:")
    derived = derive.derive(held, lens).triples
    assert {str(o) for _, p, o in derived if p == URIRef(REC + "statusFrom")} == {"urn:x:condition"}


@every_example
def test_how_many_of_each_kind_counts_what_the_pods_files_state_and_no_type_only_the_derivations_state(example):
    held = example.build("oxigraph", vocabulary.DEFAULT_LENS).store
    derived_only = {o for s, p, o in held.triples(derive.DERIVED + vocabulary.DEFAULT_LENS) if p == RDF.type}
    counted = {row["type"] for row in answers(example, "oxigraph", vocabulary.DEFAULT_LENS)["pod/How many of each kind"]}
    assert derived_only and not counted & derived_only
