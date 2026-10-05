import json

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SH, XSD

from cascade_pod.vocabulary import QUERIES
from examples import ROOT

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


def test_the_crate_lists_every_ontology_file_and_every_query_and_nothing_else():
    entities = {entity["@id"]: entity for entity in json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]}
    listed = {part["@id"]: entities[part["@id"]]["encodingFormat"] for part in entities["./"]["hasPart"]}
    files = (sorted(ROOT.glob("ontologies/**/*.ttl")) + sorted(QUERIES.rglob("*.rq"))
             + sorted(path for path in (ROOT / "runtime").rglob("*") if path.is_file()))
    assert listed == {path.relative_to(ROOT).as_posix(): FORMATS[path.suffix] for path in files}
