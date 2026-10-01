import base64
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import pytest
import rdflib
from pyshacl import validate
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH

from cascade_pod.pod import NOT_RDF, VIEW_FILES, Example

ROOT = Path(__file__).absolute().parent.parent
ONTOLOGIES = ROOT / "ontologies"
ALEX = Example(ROOT / "example-pods" / "alex-rivera")

rdflib.NORMALIZE_LITERALS = False

HEALTH = "https://ns.cascadeprotocol.org/health/v1#"
REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
PROV = "http://www.w3.org/ns/prov#"
MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
SPECIALIZATION_OF = URIRef(PROV + "specializationOf")

SHAPES_OF_KIND = {
    "version": ("health", "clinical"),
    "record": ("health", "clinical", "records"),
    "revision": ("records",),
    "subject": ("records",),
    "judgment": ("judgments",),
    "reference-series": ("records",),
    "reference-version": ("records",),
    "view": ("health", "clinical", "core"),
}
NO_SHAPE_TARGETS = (
    "clinical/labels.ttl",
    "index.ttl",
    "manifest.ttl",
    "profile/card.ttl",
    "profile/extended.ttl",
    "settings/preferences",
    "settings/privateTypeIndex.ttl",
    "settings/publicTypeIndex.ttl",
    "provenance/activities/",
    "provenance/documents/",
    "provenance/imports/",
)
NOT_CHECKED_FOR_CONFORMANCE = (
    "clinical/labels.ttl",
)


def every_rdf_file():
    return sorted(p for p in ALEX.files() + ALEX.derived if not p.startswith(NOT_RDF))


def shapes_file(vocabulary):
    return next(ONTOLOGIES.glob(f"{vocabulary}/*/{vocabulary}.shapes.ttl"))


@lru_cache(maxsize=None)
def shapes():
    graph = Graph()
    for path in sorted(ONTOLOGIES.glob("*/*/*.shapes.ttl")):
        graph.parse(path, format="turtle")
    return graph


@lru_cache(maxsize=None)
def ontology():
    graph = Graph()
    for path in sorted(ONTOLOGIES.glob("*/*/*.ttl")):
        if not path.name.endswith(".shapes.ttl"):
            graph.parse(path, format="turtle")
    return graph


@lru_cache(maxsize=None)
def loaded(relative):
    return Graph().parse(ALEX.pod / relative, format="turtle", publicID=ALEX.address + relative)


@lru_cache(maxsize=None)
def types():
    found = defaultdict(set)
    for relative in every_rdf_file():
        for node, kind in loaded(relative).subject_objects(RDF.type):
            found[node].add(kind)
    return found


def unshaped(relative):
    return relative in NO_SHAPE_TARGETS or relative.startswith(tuple(p for p in NO_SHAPE_TARGETS if p.endswith("/")))


def named_for(relative):
    stem = Path(relative).stem
    if len(stem) == 64:
        return URIRef("ni:///sha-256;" + base64.urlsafe_b64encode(bytes.fromhex(stem)).decode().rstrip("="))
    return URIRef("urn:uuid:" + stem)


def things(relative, graph):
    if relative in VIEW_FILES.values():
        return set(graph.subjects(MERGED_FROM, None))
    thing = named_for(relative)
    return {thing} if (thing, None, None) in graph else set()


def kind_of(relative, graph):
    if unshaped(relative):
        return None
    if relative in VIEW_FILES.values():
        return "view"
    [thing] = things(relative, graph) or [None]
    if relative.startswith("records/"):
        if (thing, SPECIALIZATION_OF, None) in graph:
            return "version"
        return "revision" if (thing, RDF.type, URIRef(REC + "Revision")) in graph else "record"
    if relative.startswith("subject/"):
        return "subject"
    if relative.startswith("judgments/"):
        return "judgment"
    if relative.startswith("references/"):
        return "reference-version" if (thing, SPECIALIZATION_OF, None) in graph else "reference-series"
    return None


def series_of(relative):
    graph = loaded(relative)
    return graph.value(named_for(relative), SPECIALIZATION_OF) or named_for(relative)


@lru_cache(maxsize=None)
def defining_file():
    found = {}
    for relative in every_rdf_file():
        for thing in things(relative, loaded(relative)):
            found.setdefault(thing, relative)
    return found


def unit(relative):
    """A file with the files that define what it describes but is not named for, and a reference series with its
    versions, which its shape reaches through an inverse path."""
    if relative.startswith("references/"):
        series = series_of(relative)
        return [r for r in every_rdf_file() if r.startswith("references/") and series_of(r) == series]
    others = {defining_file().get(s) for s in loaded(relative).subjects()} - {None, relative}
    return [relative, *sorted(others)]


def with_types(graph):
    data = Graph()
    data += graph
    for node in set(graph.subjects()) | set(graph.objects()):
        for kind in types().get(node, ()):
            data.add((node, RDF.type, kind))
    return data


def violations(graph):
    """Every result about a node the graph itself describes, and not about a node it only names."""
    conforms, report, _ = validate(with_types(graph), shacl_graph=shapes(), ont_graph=ontology(), advanced=True)
    rdflib.NORMALIZE_LITERALS = False
    own = set(graph.subjects())
    return sorted((str(report.value(r, SH.focusNode)), str(report.value(r, SH.resultPath)), str(report.value(r, SH.resultMessage)))
                  for r in report.subjects(RDF.type, SH.ValidationResult) if report.value(r, SH.focusNode) in own)


def unit_graph(relative):
    graph = Graph()
    for part in unit(relative):
        graph += loaded(part)
    return graph


# Focus nodes, computed from the shapes' targets and the sh:node a targeted shape's property reaches

def path_values(path, nodes, data):
    if isinstance(path, URIRef):
        return {o for n in nodes for o in data.objects(n, path)}
    inverse = shapes().value(path, SH.inversePath)
    if inverse is not None:
        return {s for n in nodes for s in data.subjects(inverse, n)}
    for step in Collection(shapes(), path):
        nodes = path_values(step, nodes, data)
    return nodes


def focus_nodes(data):
    graph, found = shapes(), defaultdict(set)
    for shape in set(graph.subjects(RDF.type, SH.NodeShape)):
        for kind in graph.objects(shape, SH.targetClass):
            found[shape] |= set(data.subjects(RDF.type, kind))
        for predicate in graph.objects(shape, SH.targetSubjectsOf):
            found[shape] |= set(data.subjects(predicate, None))
        for predicate in graph.objects(shape, SH.targetObjectsOf):
            found[shape] |= set(data.objects(None, predicate))
        found[shape] |= set(graph.objects(shape, SH.targetNode))
    for shape in list(found):
        for property_shape in graph.objects(shape, SH.property):
            for reached in graph.objects(property_shape, SH.node):
                found[reached] |= path_values(graph.value(property_shape, SH.path), found[shape], data)
    return found


def defined_in(vocabularies):
    graph = Graph()
    for vocabulary in vocabularies:
        graph.parse(shapes_file(vocabulary), format="turtle")
    return set(graph.subjects(RDF.type, SH.NodeShape)) | set(graph.objects(None, SH.node))


def test_every_term_the_pod_writes_in_a_namespace_of_this_vocabulary_is_declared_in_it():
    namespaces = tuple(str(n) for n in ontology().subjects(RDF.type, OWL.Ontology))
    declared = set(ontology().subjects(RDF.type, None))
    written = {(str(term), relative) for relative in every_rdf_file() for triple in loaded(relative)
               for term in triple if isinstance(term, URIRef) and str(term).startswith(namespaces)}
    assert sorted((term, relative) for term, relative in written if URIRef(term) not in declared) == []


@pytest.mark.parametrize("relative", [r for r in every_rdf_file() if r not in NOT_CHECKED_FOR_CONFORMANCE])
def test_every_pod_file_conforms_to_the_vocabularys_shapes(relative):
    assert violations(unit_graph(relative)) == []


@pytest.mark.parametrize("relative", every_rdf_file())
def test_every_pod_file_is_a_focus_node_of_the_shapes_for_its_kind(relative):
    graph = unit_graph(relative)
    kind = kind_of(relative, loaded(relative))
    if unshaped(relative):
        assert kind is None
        return
    assert kind is not None, f"{relative} is neither of a kind a shape checks nor named as one no shape targets"
    focus = focus_nodes(with_types(graph))
    mine = things(relative, loaded(relative))
    assert mine, f"{relative} describes nothing named for it"
    for thing in sorted(mine, key=str):
        shaping = sorted(str(s) for s in defined_in(SHAPES_OF_KIND[kind]) if thing in focus.get(s, ()))
        assert shaping, f"{thing} in {relative} is a focus node of no {'/'.join(SHAPES_OF_KIND[kind])} shape"


def first_of(kind, test=lambda graph, thing: True):
    for relative in every_rdf_file():
        graph = loaded(relative)
        if kind_of(relative, graph) == kind:
            for thing in sorted(things(relative, graph), key=str):
                if test(graph, thing):
                    return relative, thing
    raise AssertionError(f"no {kind} to break")


def without(predicate):
    def broken(graph, thing):
        assert (thing, predicate, None) in graph
        graph.remove((thing, predicate, None))
    return broken


def replacing(predicate, value):
    def broken(graph, thing):
        assert (thing, predicate, None) in graph
        graph.set((thing, predicate, value))
    return broken


def adding(predicate, value):
    def broken(graph, thing):
        graph.add((thing, predicate, value))
    return broken


CATEGORY, ALLERGEN = URIRef(HEALTH + "allergyCategory"), URIRef(HEALTH + "allergen")
BREAKS = {
    "version": (lambda g, t: (t, CATEGORY, None) in g, replacing(CATEGORY, Literal("drug"))),
    "record": (lambda g, t: (t, URIRef(REC + "sourceUrl"), None) in g,
               replacing(URIRef(REC + "sourceUrl"), Literal("https://fhir.meridian.example/"))),
    "revision": (lambda g, t: True, without(URIRef(REC + "version"))),
    "subject": (lambda g, t: True, adding(URIRef("http://xmlns.com/foaf/0.1/name"), Literal("Alex Rivera"))),
    "judgment": (lambda g, t: True, without(URIRef(PROV + "generatedAtTime"))),
    "reference-series": (lambda g, t: True, without(URIRef("http://www.w3.org/2000/01/rdf-schema#label"))),
    "reference-version": (lambda g, t: True, without(URIRef("http://purl.org/pav/version"))),
    "view": (lambda g, t: (t, ALLERGEN, None) in g, adding(ALLERGEN, Literal("Latex"))),
}


def test_every_kind_a_shape_checks_has_a_way_to_break_it():
    assert sorted(BREAKS) == sorted(SHAPES_OF_KIND)


@pytest.mark.parametrize("kind", sorted(BREAKS))
def test_each_kind_of_pod_file_fails_its_shapes_when_broken(kind):
    applies, breaking = BREAKS[kind]
    relative, thing = first_of(kind, applies)
    graph = unit_graph(relative)
    assert violations(graph) == []
    breaking(graph, thing)
    assert violations(graph) != [], relative
