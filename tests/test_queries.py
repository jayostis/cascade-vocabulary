import json
import sys
from pathlib import Path

import pytest
from pyparsing import ParseResults
from rdflib import RDF, URIRef
from rdflib.paths import Path as PropertyPath
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

ROOT = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(ROOT / "example-pods" / "alex-rivera" / "queries"))
import build  # noqa: E402

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
RDF_TYPE = RDF.type
IN_ENTRY = URIRef(REC + "inEntry")
FORMATS = {".rq": "application/sparql-query", ".ttl": "text/turtle"}


def every_query():
    return sorted(p.relative_to(build.QUERIES).as_posix() for p in build.QUERIES.rglob("*.rq"))


def in_the_crate(relative):
    return (build.QUERIES / relative).relative_to(ROOT).as_posix()


def crate():
    return {entity["@id"]: entity for entity in json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]}


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
}


def nested_forms(text):
    everything = list(nodes(parseQuery(text)))
    wheres = {id(n["where"]) for n in everything if n.name in QUERY_FORMS and n.get("where") is not None}
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
        if node.name == "OptionalGraphPattern" and any(m.name == "SubSelect" for m in nodes(node["graph"])):
            found.append("subquery-in-optional")
    return found



@pytest.mark.parametrize("relative", every_query())
def test_every_query_parses_on_rdflib_and_on_pyoxigraph(relative):
    text = build.query_text(relative)
    prepareQuery(text)
    build.Oxigraph().store.query(text)


@pytest.mark.parametrize("relative", every_query())
def test_every_subquery_comes_first_in_its_group(relative):
    for group in nodes(parseQuery(build.query_text(relative))):
        if group.name == "GroupGraphPatternSub":
            parts = list(group.get("part") or [])
            first_other = next((i for i, part in enumerate(parts) if not is_subquery(part)), len(parts))
            assert not any(is_subquery(part) for part in parts[first_other:]), relative


@pytest.mark.parametrize("relative", every_query())
def test_every_query_reading_in_entry_names_its_type(relative):
    algebra = prepareQuery(build.query_text(relative)).algebra
    patterns = [t for node in nodes(algebra["p"]) if node.name == "BGP" for t in node["triples"]]
    bound_by_values = {v for node in nodes(algebra["p"]) if node.name == "values" for row in node["res"] for v in row}
    typed = {s for s, p, o in patterns if p == RDF_TYPE and (isinstance(o, URIRef) or o in bound_by_values)}
    readers = {s for s, p, o in patterns if p == IN_ENTRY}
    assert readers <= typed, relative



@pytest.mark.parametrize("relative", every_query())
def test_every_query_is_one_flat_pattern(relative):
    assert nested_forms(build.query_text(relative)) == []


@pytest.mark.parametrize("form", sorted(NESTED))
def test_the_flat_pattern_check_refuses_each_nested_form(form):
    assert nested_forms(NESTED[form]) == [form]


def test_the_flat_pattern_check_accepts_a_union_whose_branches_are_each_complete():
    assert nested_forms("""SELECT * WHERE {
      { ?a ?b ?c FILTER NOT EXISTS { ?a ?b ?d } OPTIONAL { ?a ?e ?f } }
      UNION { { SELECT ?a WHERE { ?a ?b ?c } } ?a ?d ?c }
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
    return set(iris(prepareQuery(build.query_text(relative)).algebra["p"]))


def writes(relative):
    template = prepareQuery(build.query_text(relative)).algebra["template"]
    return {o if p == RDF_TYPE else p for s, p, o in template}


@pytest.mark.parametrize("lens", sorted(build.named("lenses")))
def test_no_derivation_reads_a_term_a_later_derivation_writes(lens):
    steps = build.derivations(lens)
    found = {(step, later, str(term)) for i, step in enumerate(steps) for later in steps[i + 1:]
             for term in reads(step) & writes(later)}
    assert found == set()


@pytest.mark.parametrize("lens", sorted(build.named("lenses")))
def test_every_lens_writes_rec_counts_and_nothing_else(lens):
    assert writes(build.named("lenses")[lens]) == {URIRef(REC + "counts")}


def test_each_derivation_has_a_position_of_its_own_and_every_lens_the_same_one():
    positions = {key: entity["position"] for key, entity in crate().items() if "position" in entity}
    derivations = [in_the_crate(r) for r in build.named("derivations").values()]
    lenses = [in_the_crate(r) for r in build.named("lenses").values()]
    assert sorted(positions) == sorted(derivations + lenses)
    assert len({positions[lens] for lens in lenses}) == 1
    steps = sorted(positions[step] for step in derivations + lenses[:1])
    assert steps == list(range(1, len(steps) + 1))


def test_the_crate_lists_every_ontology_file_and_every_query_and_nothing_else():
    entities = crate()
    listed = {part["@id"]: entities[part["@id"]]["encodingFormat"] for part in entities["./"]["hasPart"]}
    files = sorted(ROOT.glob("ontologies/**/*.ttl")) + sorted(build.QUERIES.rglob("*.rq"))
    assert listed == {path.relative_to(ROOT).as_posix(): FORMATS[path.suffix] for path in files}
