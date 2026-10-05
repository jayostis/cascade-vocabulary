"""A wrong pod fails the vocabulary's shapes. Each case under shape-cases/ is a small file of one kind the shapes check,
valid or broken one way, and its manifest says what validating it reports, in the SHACL test suite's terms: each result
as the node shape that reported it, directly or through one of its properties, and the result's path."""

from functools import cache

from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH

from contract import REC, ROOT
from manifests import MF, path
from pods import FIXTURES

SHT = Namespace("http://www.w3.org/ns/shacl-test#")
HEALTH = Namespace("https://ns.cascadeprotocol.org/health/v1#")
CASES = ROOT / "tests" / "shape-cases"
KIT = ROOT / "conformance" / "alex-rivera"
TARGETS = (SH.targetClass, SH.targetSubjectsOf, SH.targetObjectsOf, SH.targetNode)
BROKEN_ELSEWHERE = {REC.PlacementShape: "test_pod_layout.py breaks the layout's entries"}
UNDECLARED_ON_PURPOSE = {HEALTH.NoSuchRecord: "the refusals vector files a record of a type no folder holds"}


@cache
def parsed(file):
    return Graph().parse(file, format="turtle")


@cache
def shapes():
    graph = Graph()
    for file in sorted(ROOT.glob("ontologies/*/*/*.shapes.ttl")):
        graph += parsed(file)
    return graph


@cache
def ontology():
    graph = Graph()
    for file in sorted(ROOT.glob("ontologies/*/*/*.ttl")):
        if not file.name.endswith(".shapes.ttl"):
            graph += parsed(file)
    return graph


def path_of(graph, node):
    if node is None or isinstance(node, URIRef):
        return node
    inverse = graph.value(node, SH.inversePath)
    if inverse is not None:
        return ("^", path_of(graph, inverse))
    return tuple(path_of(graph, step) for step in Collection(graph, node))


@cache
def cases():
    """Each case's file, by its name, with the (node shape, path) of each result its manifest says it reports."""
    manifest = parsed(CASES / "manifest.ttl")
    found = {}
    for entry in manifest.subjects(RDF.type, SHT.Validate):
        result = manifest.value(entry, MF.result)
        found[str(entry).rpartition("#")[2]] = (
            path(manifest.value(manifest.value(entry, MF.action), SHT.dataGraph)),
            frozenset((shape, path_of(manifest, manifest.value(r, SH.resultPath)))
                      for r in manifest.objects(result, SH.result) for shape in manifest.objects(r, SH.sourceShape)))
    return found


def node_shape(shape):
    return shape if (shape, RDF.type, SH.NodeShape) in shapes() else shapes().value(None, SH.property, shape)


@cache
def reported():
    """What validating every case reports, by case, from one validation of all of them: each file's own nodes are its
    alone, as its IRIs are relative to it."""
    data, owner = Graph(), {}
    for name, (file, _) in cases().items():
        data += parsed(file)
        owner |= {node: name for node in parsed(file).subjects()}
    _, report, _ = validate(data, shacl_graph=shapes())
    found = {name: set() for name in cases()}
    for result in report.objects(None, SH.result):
        found[owner[report.value(result, SH.focusNode)]].add(
            (node_shape(report.value(result, SH.sourceShape)), path_of(report, report.value(result, SH.resultPath))))
    return found


def test_each_valid_case_conforms_and_each_break_reports_its_shape_and_path_and_nothing_else():
    assert {file for file in CASES.rglob("*.ttl") if file.name != "manifest.ttl"} == {f for f, _ in cases().values()}
    wrong = {name: {"expected": sorted(map(str, expected)), "reported": sorted(map(str, reported()[name]))}
             for name, (_, expected) in cases().items() if reported()[name] != expected}
    assert wrong == {}


def targets(shape, data):
    found = {node for kind in shapes().objects(shape, SH.targetClass) for node in data.subjects(RDF.type, kind)}
    found |= {node for p in shapes().objects(shape, SH.targetSubjectsOf) for node in data.subjects(p, None)}
    found |= {node for p in shapes().objects(shape, SH.targetObjectsOf) for node in data.objects(None, p)}
    return found | set(shapes().objects(shape, SH.targetNode))


def targeting():
    return {shape for shape in shapes().subjects(RDF.type, SH.NodeShape)
            if any((shape, t, None) in shapes() for t in TARGETS)}


def test_every_shape_that_targets_pod_data_has_a_valid_case_and_a_break():
    valid = {shape for name, (file, expected) in cases().items() if not expected
             for shape in targeting() if targets(shape, parsed(file))}
    broken = {shape for _, expected in cases().values() for shape, _ in expected}
    assert sorted(targeting() - set(BROKEN_ELSEWHERE) - (valid & broken)) == []


def namespaces():
    return tuple(str(n) for n in ontology().subjects(RDF.type, OWL.Ontology))


def constrained_by_one_shape():
    """Each property of this vocabulary that one targeting node shape alone constrains, with that shape. A property
    more than one class's content carries is no class's target."""
    shapes_of = {}
    for shape in targeting():
        for property_shape in shapes().objects(shape, SH.property):
            p = shapes().value(property_shape, SH.path)
            if isinstance(p, URIRef) and str(p).startswith(namespaces()):
                shapes_of.setdefault(p, set()).add(shape)
    return {p: shape for p, (shape, *more) in shapes_of.items() if not more}


def untargeted(data):
    """Each subject of a kind the shapes cover that no shape it needs takes as a focus node: an instance of a class of
    this vocabulary that no shape targets by that class, or a subject of a property one shape alone constrains that
    the shape does not target."""
    focus = {shape: targets(shape, data) for shape in targeting()}
    by_class = {(kind, node) for shape in targeting() for kind in shapes().objects(shape, SH.targetClass)
                for node in focus[shape]}
    found = {(str(node), str(kind)) for node, kind in data.subject_objects(RDF.type)
             if str(kind).startswith(namespaces()) and (kind, node) not in by_class}
    for p, shape in constrained_by_one_shape().items():
        found |= {(str(node), str(p)) for node in data.subjects(p, None) if node not in focus[shape]}
    return found


def fixture_pod(fixture):
    graph = Graph()
    for relative in fixture.files():
        graph += parsed(fixture.folder / relative)
    return graph


def test_every_subject_of_a_kind_the_shapes_cover_in_a_fixture_or_a_valid_case_is_a_focus_node_of_its_shape():
    pods = {fixture.name: fixture_pod(fixture) for fixture in FIXTURES}
    pods |= {name: parsed(file) for name, (file, expected) in cases().items() if not expected}
    assert {name: sorted(found) for name, data in pods.items() if (found := untargeted(data))} == {}


def written():
    yield from (fixture.folder / relative for fixture in FIXTURES for relative in fixture.files())
    yield from (file for file, expected in cases().values() if not expected)
    yield from ROOT.glob("runtime/vectors/*/scripted-input/**/*.ttl")
    yield from (KIT / "scripted-input").rglob("*.ttl")
    yield from (KIT / "expected").glob("*.ttl")


def test_every_term_a_pod_writes_in_a_namespace_of_this_vocabulary_is_declared_in_it():
    declared = set(ontology().subjects(RDF.type, None)) | set(UNDECLARED_ON_PURPOSE)
    undeclared = {(str(term), file.relative_to(ROOT).as_posix()) for file in written() for triple in parsed(file)
                  for term in triple
                  if isinstance(term, URIRef) and str(term).startswith(namespaces()) and term not in declared}
    assert sorted(undeclared) == []
