import json
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SH, XSD

ROOT = Path(__file__).resolve().parent.parent
ONTOLOGIES = sorted(ROOT.glob("ontologies/**/*.ttl"))
SHAPES = [path for path in ONTOLOGIES if path.name.endswith(".shapes.ttl")]
COPIED = [path for path in ONTOLOGIES if path.parts[-3] in ("core", "health", "clinical")]
SOURCE_COMMIT = (
    "https://github.com/the-cascade-protocol/spec/blob/d819bc2c045266f9f79ebf9398cbbb82a6156d27/"
)
FOAF_RELEASE = "http://xmlns.com/foaf/spec/20140114.rdf"
CASCADE = "https://ns.cascadeprotocol.org/"
PROV = Namespace("http://www.w3.org/ns/prov#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
HEALTH = Namespace("https://ns.cascadeprotocol.org/health/v1#")
CLINICAL = Namespace("https://ns.cascadeprotocol.org/clinical/v1#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
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


def members(graph, node):
    if isinstance(node, URIRef):
        return {node}
    return set(Collection(graph, graph.value(node, OWL.unionOf)))


def failed_on(results, result):
    where = results.value(result, SH.resultPath) or results.value(result, SH.sourceShape)
    return where, results.value(result, SH.sourceConstraintComponent)


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
        and term != ontology
        and not any(str(s).startswith((SOURCE_COMMIT, FOAF_RELEASE)) for s in graph.objects(term, DCTERMS.source))
    ]
    assert unsourced == []


def test_every_predicate_a_shape_constrains_is_declared_or_is_prov_o():
    paths = set(union(SHAPES).objects(None, SH.path))
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
    undeclared = {c for c in named if str(c).startswith(CASCADE) and (c, RDF.type, None) not in vocabulary}
    assert undeclared == set()


def test_every_datatype_a_shape_accepts_is_in_its_predicates_range():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    outside = set()
    for shape, predicate in shapes.subject_objects(SH.path):
        ranges = [members(vocabulary, r) for r in vocabulary.objects(predicate, RDFS.range)]
        accepted = set(shapes.objects(shape, SH.datatype)) | {
            datatype
            for alternatives in shapes.objects(shape, SH["or"])
            for alternative in Collection(shapes, alternatives)
            for datatype in shapes.objects(alternative, SH.datatype)
        }
        datatype_ranges = [r for r in ranges if all(str(m).startswith(str(XSD)) for m in r)]
        outside |= {(predicate, d) for d in accepted for r in datatype_ranges if d not in r}
    assert outside == set()


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


FAILS_ON = {
    "a-condition-version-with-an-immunization-status": (HEALTH.status, SH.InConstraintComponent),
    "a-patient-version-with-an-empty-given-name": (FOAF.givenName, SH.MinLengthConstraintComponent),
    "a-procedure-version-with-a-date-as-a-string": (CLINICAL.procedureDate, SH.OrConstraintComponent),
    "a-record-with-a-source-url-that-is-a-string": (REC.sourceUrl, SH.NodeKindConstraintComponent),
    "a-record-with-two-source-urls": (REC.sourceUrl, SH.MaxCountConstraintComponent),
    "a-revision-without-an-arrival-time": (PROV.generatedAtTime, SH.MinCountConstraintComponent),
    "a-same-judgment-naming-a-subject": (JDG.verdict, SH.HasValueConstraintComponent),
    "a-subject-holding-data": (FOAF.givenName, SH.ClosedConstraintComponent),
    "an-about-judgment-naming-neither-a-subject-nor-a-basis": (JDG.AboutVerdictShape, SH.OrConstraintComponent),
    "an-about-judgment-without-a-basis": (JDG.AboutVerdictShape, SH.OrConstraintComponent),
    "an-allergy-version-with-a-criticality-outside-fhir-r4": (CLINICAL.criticality, SH.InConstraintComponent),
    "an-allergy-version-with-two-allergens": (HEALTH.allergen, SH.MaxCountConstraintComponent),
    "an-immunization-version-with-a-condition-status": (HEALTH.status, SH.InConstraintComponent),
}


@pytest.mark.parametrize("path", sorted((ROOT / "tests/fails").glob("*.ttl")), ids=lambda p: p.stem)
def test_fails_on_exactly_the_constraint_it_is_named_for(path):
    _, results, report = conforms(path)
    failures = [failed_on(results, r) for r in set(results.subjects(SH.resultSeverity, None))]
    assert failures == [FAILS_ON[path.stem]], report
