import json
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SH

ROOT = Path(__file__).resolve().parent.parent
ONTOLOGIES = sorted(ROOT.glob("ontologies/**/*.ttl"))
SHAPES = [path for path in ONTOLOGIES if path.name.endswith(".shapes.ttl")]
COPIED = [path for path in ONTOLOGIES if path.parts[-3] in ("core", "health", "clinical")]
SOURCE_COMMIT = (
    "https://github.com/the-cascade-protocol/spec/blob/d819bc2c045266f9f79ebf9398cbbb82a6156d27/"
)
PROV = Namespace("http://www.w3.org/ns/prov#")
DECLARES_A_PREDICATE = (RDF.Property, OWL.DatatypeProperty, OWL.ObjectProperty, OWL.AnnotationProperty)


def relative(path):
    return path.relative_to(ROOT).as_posix()


def union(paths):
    graph = Graph()
    for path in paths:
        graph.parse(path)
    return graph


def declared():
    vocabulary = union(ONTOLOGIES)
    return {s for kind in DECLARES_A_PREDICATE for s in vocabulary.subjects(RDF.type, kind)}


def conforms(path):
    result, results, report = validate(Graph().parse(path), shacl_graph=union(SHAPES))
    return result, results, report


@pytest.mark.parametrize("path", ONTOLOGIES, ids=relative)
def test_every_turtle_file_parses(path):
    assert len(Graph().parse(path)) > 0


@pytest.mark.parametrize("path", SHAPES, ids=relative)
def test_every_shapes_file_loads_as_shacl_that_shacl_accepts(path):
    result, _, report = validate(Graph(), shacl_graph=Graph().parse(path), meta_shacl=True)
    assert result, report


@pytest.mark.parametrize("path", COPIED, ids=relative)
def test_every_copied_term_names_the_commit_it_was_copied_from(path):
    graph = Graph().parse(path)
    ontology = next(graph.subjects(RDF.type, OWL.Ontology), None)
    unsourced = [
        term
        for term in set(graph.subjects())
        if isinstance(term, URIRef)
        and str(term).startswith("https://ns.cascadeprotocol.org/")
        and term != ontology
        and not any(str(s).startswith(SOURCE_COMMIT) for s in graph.objects(term, DCTERMS.source))
    ]
    assert unsourced == []


def test_every_predicate_a_shape_constrains_is_declared_or_is_prov_o():
    paths = set(union(SHAPES).objects(None, SH.path))
    undeclared = {p for p in paths - declared() if not str(p).startswith(str(PROV))}
    assert undeclared == set()


def test_the_crate_lists_every_turtle_file_and_nothing_else():
    crate = json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    root = next(entity for entity in crate["@graph"] if entity["@id"] == "./")
    listed = {part["@id"] for part in root["hasPart"]}
    assert listed == {relative(path) for path in ONTOLOGIES}


@pytest.mark.parametrize("path", sorted((ROOT / "tests/conforms").glob("*.ttl")), ids=lambda p: p.stem)
def test_conforms(path):
    result, _, report = conforms(path)
    assert result, report


@pytest.mark.parametrize("path", sorted((ROOT / "tests/conforms").glob("*.ttl")), ids=lambda p: p.stem)
def test_every_predicate_a_conforming_example_writes_is_declared_or_is_prov_o(path):
    written = set(Graph().parse(path).predicates()) - {RDF.type}
    undeclared = {p for p in written - declared() if not str(p).startswith(str(PROV))}
    assert undeclared == set()


@pytest.mark.parametrize("path", sorted((ROOT / "tests/fails").glob("*.ttl")), ids=lambda p: p.stem)
def test_fails_on_exactly_one_constraint(path):
    _, results, report = conforms(path)
    assert len(set(results.subjects(SH.resultSeverity, None))) == 1, report
