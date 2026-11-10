import re

import pytest
from pyshacl import validate
from rdflib import Graph, URIRef

from contract import KITS, LAYOUT, ROOT
from ontologies import shapes

SOLID = "http://www.w3.org/ns/solid/terms#"


def placement(graph, predicate):
    return next(graph.subjects(URIRef(predicate), None))


def naming_a_file_and_a_folder(graph):
    graph.add((placement(graph, SOLID + "instance"), URIRef(SOLID + "instanceContainer"), URIRef("urn:x:folder/")))


def naming_neither(graph):
    graph.remove((placement(graph, SOLID + "instanceContainer"), URIRef(SOLID + "instanceContainer"), None))


def conforms_to_its_shapes(graph):
    conforms, _, report = validate(graph, shacl_graph=Graph() + shapes(), advanced=True)
    return conforms, report


class TestWhereAPodKeepsItsFiles:
    """Where a pod keeps its files · runtime/pod-layout.ttl, conformance/*/expected/*.ttl

    The layout says, for each class of thing a pod holds, the file or the folder it is kept in; a runtime reads it with
    the pod's address as its base. A placement is one such line of the layout, and it names a file or a folder, never
    both.
    """

    class TestGivenTheLayout:
        def test_conforms_to_its_shapes(self):
            """conforms to its shapes

            The layout is read with a pod's address as its base and checked against the shapes in
            `ontologies/cascade.shapes.ttl`; the shapes' own report is the message if it does not conform.
            """
            conforms, report = conforms_to_its_shapes(Graph().parse(LAYOUT, publicID="https://pod.example/"))
            assert conforms, report

    class TestGivenTheLayoutWithOnePlacementChanged:
        @pytest.mark.parametrize("breaking", [naming_a_file_and_a_folder, naming_neither],
                                 ids=["a file and a folder", "neither"])
        def test_fails_its_shapes_when_the_placement_names(self, breaking):
            """fails its shapes when the placement names

            One placement of the layout is changed to name both a file and a folder, or to name neither; the layout is
            then checked against the shapes and must not conform.
            """
            graph = Graph().parse(LAYOUT, publicID="https://pod.example/")
            breaking(graph)
            conforms, _ = conforms_to_its_shapes(graph)
            assert not conforms

    class TestGivenAnyViewAKitExpects:
        def test_holds_no_iri_at_its_pods_address(self):
            """holds no IRI at its pod's address

            Each IRI a view file holds, as its bytes write it, is compared with the address of the pod its kit is
            about, which `people.ttl` gives as the kit's storage; a view that holds an IRI under that address fails,
            as only that pod's address could match it.
            """
            holding = []
            for kit in KITS:
                address = re.search(r"pim:storage <([^>]+)>",
                                    (kit / "scripted-input" / "people.ttl").read_text(encoding="utf-8"))[1]
                holding += [view.relative_to(ROOT).as_posix() for view in sorted((kit / "expected").glob("*.ttl"))
                            if f"<{address}" in view.read_text(encoding="utf-8")]
            assert KITS and holding == []
