import json

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SH, XSD

from contract import QUERIES, ROOT

ONTOLOGIES = sorted(ROOT.glob("ontologies/**/*.ttl"))
SHAPES = [path for path in ONTOLOGIES if path.name.endswith(".shapes.ttl")]
COPIED = [
    path for path in ONTOLOGIES if path.parts[-3] in ("core", "health", "clinical")
]
SOURCE_COMMIT = "https://github.com/the-cascade-protocol/spec/blob/d819bc2c045266f9f79ebf9398cbbb82a6156d27/"
FOAF_RELEASE = "http://xmlns.com/foaf/spec/20140114.rdf"
CASCADE = "https://ns.cascadeprotocol.org/"
PROV = Namespace("http://www.w3.org/ns/prov#")
FORMATS = {
    ".json": "application/json",
    ".md": "text/markdown",
    ".rq": "application/sparql-query",
    ".srj": "application/sparql-results+json",
    ".ttl": "text/turtle",
    ".xml": "application/xml",
}
DECLARES_A_PREDICATE = (
    RDF.Property,
    OWL.DatatypeProperty,
    OWL.ObjectProperty,
    OWL.AnnotationProperty,
)


def relative(path):
    return path.relative_to(ROOT).as_posix()


def union(paths):
    graph = Graph()
    for path in paths:
        graph.parse(path)
    return graph


def declared():
    vocabulary = union(ONTOLOGIES)
    return {
        s for kind in DECLARES_A_PREDICATE for s in vocabulary.subjects(RDF.type, kind)
    }


def members(graph, node):
    if isinstance(node, URIRef):
        return {node}
    return set(Collection(graph, graph.value(node, OWL.unionOf)))


def predicates(graph, path):
    if isinstance(path, URIRef):
        return {path}
    inverse = graph.value(path, SH.inversePath)
    if inverse is not None:
        return predicates(graph, inverse)
    return {p for step in Collection(graph, path) for p in predicates(graph, step)}


@pytest.mark.parametrize("path", ONTOLOGIES, ids=relative)
def test_every_turtle_file_parses(path):
    assert len(Graph().parse(path)) > 0


@pytest.mark.parametrize("path", SHAPES, ids=relative)
def test_every_shapes_file_loads_as_shacl_that_shacl_accepts(path):
    result, _, report = validate(
        Graph(), shacl_graph=Graph().parse(path), meta_shacl=True
    )
    assert result, report


@pytest.mark.parametrize("path", COPIED, ids=relative)
def test_every_copied_term_names_the_commit_it_was_copied_from(path):
    graph = Graph().parse(path)
    ontology = next(graph.subjects(RDF.type, OWL.Ontology), None)
    unsourced = [
        term
        for term in set(graph.subjects())
        if isinstance(term, URIRef)
        and term != ontology
        and not any(
            str(s).startswith((SOURCE_COMMIT, FOAF_RELEASE))
            for s in graph.objects(term, DCTERMS.source)
        )
    ]
    assert unsourced == []


def test_every_predicate_a_shape_constrains_is_declared_or_is_prov_o():
    shapes = union(SHAPES)
    paths = {p for path in shapes.objects(None, SH.path) for p in predicates(shapes, path)}
    undeclared = {p for p in paths - declared() if not str(p).startswith(str(PROV))}
    assert undeclared == set()


def test_every_package_class_a_term_names_is_declared_here():
    vocabulary = union(ONTOLOGIES)
    named = {
        member
        for predicate in (RDFS.domain, RDFS.range, RDFS.subClassOf)
        for node in vocabulary.objects(None, predicate)
        for member in members(vocabulary, node)
    }
    undeclared = {
        c
        for c in named
        if str(c).startswith(CASCADE) and (c, RDF.type, None) not in vocabulary
    }
    assert undeclared == set()


def test_every_datatype_a_shape_accepts_is_in_its_predicates_range():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    outside = set()
    for shape, predicate in shapes.subject_objects(SH.path):
        ranges = [
            members(vocabulary, r) for r in vocabulary.objects(predicate, RDFS.range)
        ]
        accepted = set(shapes.objects(shape, SH.datatype)) | {
            datatype
            for alternatives in shapes.objects(shape, SH["or"])
            for alternative in Collection(shapes, alternatives)
            for datatype in shapes.objects(alternative, SH.datatype)
        }
        datatype_ranges = [
            r for r in ranges if all(str(m).startswith(str(XSD)) for m in r)
        ]
        outside |= {
            (predicate, d) for d in accepted for r in datatype_ranges if d not in r
        }
    assert outside == set()


def crate():
    return {entity["@id"]: entity for entity in json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]}


def parts(entities, dataset):
    """Each file a dataset has as a part, or as a part of a dataset that is one of its parts."""
    found = {}
    for part in entities[dataset]["hasPart"]:
        entity = entities[part["@id"]]
        found |= parts(entities, part["@id"]) if entity["@type"] == "Dataset" else {part["@id"]: entity["encodingFormat"]}
    return found


def test_the_crate_lists_every_ontology_query_runtime_and_conformance_file_and_nothing_else():
    files = (sorted(ROOT.glob("ontologies/**/*.ttl")) + sorted(QUERIES.rglob("*.rq"))
             + sorted(path for folder in ("runtime", "conformance") for path in (ROOT / folder).rglob("*") if path.is_file()))
    assert parts(crate(), "./") == {path.relative_to(ROOT).as_posix(): FORMATS[path.suffix] for path in files}


def references(value):
    if isinstance(value, dict):
        return {value["@id"]} if set(value) == {"@id"} else set().union(*map(references, value.values()))
    if isinstance(value, list):
        return set().union(*map(references, value))
    return set()


def test_every_is_based_on_and_citation_in_the_crate_is_on_a_file_that_exists():
    described = [path for path, entity in crate().items() if "isBasedOn" in entity or "citation" in entity]
    assert described and [path for path in described if path != "./" and not (ROOT / path).is_file()] == []


def test_every_entity_in_the_crate_is_reached_from_its_metadata_descriptor():
    entities, reached, todo = crate(), set(), ["ro-crate-metadata.json"]
    while todo:
        found = todo.pop()
        if found in entities and found not in reached:
            reached.add(found)
            todo.extend(references(entities[found]))
    assert sorted(set(entities) - reached) == []
