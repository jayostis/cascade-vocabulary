import base64
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH

from cascade_pod.pod import NOT_RDF
from examples import ROOT, pod_file

ONTOLOGIES = ROOT / "ontologies"

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
    "manifest.ttl",
    "profile/card.ttl",
    "settings/preferences",
    "settings/privateTypeIndex.ttl",
    "provenance/activities/",
    "provenance/documents/",
    "provenance/imports/",
)
NOT_CHECKED_FOR_CONFORMANCE = (
    "clinical/labels.ttl",
)


def every_rdf_file(example):
    return sorted(p for p in example.files() + example.derived if not p.startswith(NOT_RDF))


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
def loaded(example, relative):
    return pod_file(example, relative)


@lru_cache(maxsize=None)
def types(example):
    found = defaultdict(set)
    for relative in every_rdf_file(example):
        for node, kind in loaded(example, relative).subject_objects(RDF.type):
            found[node].add(kind)
    return found


def unshaped(relative):
    return relative in NO_SHAPE_TARGETS or relative.startswith(tuple(p for p in NO_SHAPE_TARGETS if p.endswith("/")))


def named_for(relative):
    stem = Path(relative).stem
    if len(stem) == 64:
        return URIRef("ni:///sha-256;" + base64.urlsafe_b64encode(bytes.fromhex(stem)).decode().rstrip("="))
    return URIRef("urn:uuid:" + stem)


def is_view(graph):
    return (None, RDF.type, URIRef(REC + "View")) in graph


def things(relative, graph):
    if is_view(graph):
        return set(graph.subjects(MERGED_FROM, None))
    thing = named_for(relative)
    return {thing} if (thing, None, None) in graph else set()


def kind_of(relative, graph):
    if unshaped(relative):
        return None
    if is_view(graph):
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


def with_types(example, graph):
    data = Graph()
    data += graph
    for node in set(graph.subjects()) | set(graph.objects()):
        for kind in types(example).get(node, ()):
            data.add((node, RDF.type, kind))
    return data


def violations(example, graph):
    """Every result about a node the graph itself describes, and not about a node it only names."""
    conforms, report, _ = validate(with_types(example, graph), shacl_graph=shapes(), ont_graph=ontology(), advanced=True)
    own = set(graph.subjects())
    return sorted((str(report.value(r, SH.focusNode)), str(report.value(r, SH.resultPath)), str(report.value(r, SH.resultMessage)))
                  for r in report.subjects(RDF.type, SH.ValidationResult) if report.value(r, SH.focusNode) in own)


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


def test_every_term_alexs_pod_writes_in_a_namespace_of_this_vocabulary_is_declared_in_it(alex):
    namespaces = tuple(str(n) for n in ontology().subjects(RDF.type, OWL.Ontology))
    declared = set(ontology().subjects(RDF.type, None))
    written = {(str(term), relative) for relative in every_rdf_file(alex) for triple in loaded(alex, relative)
               for term in triple if isinstance(term, URIRef) and str(term).startswith(namespaces)}
    assert sorted((term, relative) for term, relative in written if URIRef(term) not in declared) == []


def checked(example):
    """Every file of the pod the shapes check, read together."""
    graph = Graph()
    for relative in every_rdf_file(example):
        if relative not in NOT_CHECKED_FOR_CONFORMANCE:
            graph += loaded(example, relative)
    return graph


def test_every_file_of_alexs_pod_conforms_to_the_vocabularys_shapes(alex):
    assert violations(alex, checked(alex)) == []


def unshaped_by_its_kind(example, relative, focus):
    """Why the file is not checked by the shapes for its kind, or None."""
    kind = kind_of(relative, loaded(example, relative))
    if unshaped(relative):
        return None if kind is None else f"it is of a kind, {kind}, yet named as one no shape targets"
    if kind is None:
        return "it is neither of a kind a shape checks nor named as one no shape targets"
    mine = things(relative, loaded(example, relative))
    if not mine:
        return "it describes nothing named for it"
    unshaped_things = [str(thing) for thing in sorted(mine, key=str)
                       if not any(thing in focus.get(s, ()) for s in defined_in(SHAPES_OF_KIND[kind]))]
    return f"{unshaped_things} are focus nodes of no {'/'.join(SHAPES_OF_KIND[kind])} shape" if unshaped_things else None


def test_every_file_of_alexs_pod_is_a_focus_node_of_the_shapes_for_its_kind(alex):
    focus = focus_nodes(with_types(alex, checked(alex)))
    found = {relative: unshaped_by_its_kind(alex, relative, focus) for relative in every_rdf_file(alex)}
    assert {relative: why for relative, why in found.items() if why} == {}


def first_of(example, kind, test=lambda graph, thing: True):
    for relative in every_rdf_file(example):
        graph = loaded(example, relative)
        if kind_of(relative, graph) == kind:
            for thing in sorted(things(relative, graph), key=str):
                if test(graph, thing):
                    return relative, thing
    raise AssertionError(f"the pod has no {kind} to break")


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
               replacing(URIRef(REC + "sourceUrl"), Literal("https://fhir.example/"))),
    "revision": (lambda g, t: True, without(URIRef(REC + "version"))),
    "subject": (lambda g, t: True, adding(URIRef("http://xmlns.com/foaf/0.1/name"), Literal("A name"))),
    "judgment": (lambda g, t: True, without(URIRef(PROV + "generatedAtTime"))),
    "reference-series": (lambda g, t: True, without(URIRef("http://www.w3.org/2000/01/rdf-schema#label"))),
    "reference-version": (lambda g, t: True, without(URIRef("http://purl.org/pav/version"))),
    "view": (lambda g, t: (t, ALLERGEN, None) in g, adding(ALLERGEN, Literal("Latex"))),
}


def test_every_kind_a_shape_checks_has_a_way_to_break_it():
    assert sorted(BREAKS) == sorted(SHAPES_OF_KIND)


@pytest.mark.parametrize("kind", sorted(BREAKS))
def test_each_kind_of_pod_file_fails_its_shapes_when_broken(kind, alex):
    applies, breaking = BREAKS[kind]
    relative, thing = first_of(alex, kind, applies)
    graph = checked(alex)
    breaking(graph, thing)
    assert violations(alex, graph) != [], relative
