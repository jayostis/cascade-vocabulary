import re

import pytest
from pyshacl import validate
from rdflib import Graph, URIRef

from contract import KITS, LAYOUT, ROOT

SOLID = "http://www.w3.org/ns/solid/terms#"
SHAPES = ROOT / "ontologies" / "cascade.shapes.ttl"


def entry(graph, predicate):
    return next(graph.subjects(URIRef(predicate), None))


def naming_a_file_and_a_folder(graph):
    graph.add((entry(graph, SOLID + "instance"), URIRef(SOLID + "instanceContainer"), URIRef("urn:x:folder/")))


def naming_neither(graph):
    graph.remove((entry(graph, SOLID + "instanceContainer"), URIRef(SOLID + "instanceContainer"), None))


@pytest.mark.parametrize("breaking", [None, naming_a_file_and_a_folder, naming_neither],
                         ids=["as-is", "file-and-folder", "neither"])
def test_the_layout_conforms_to_its_shapes_until_an_entry_names_both_a_file_and_a_folder_or_neither(breaking):
    graph = Graph().parse(LAYOUT, publicID="https://pod.example/")
    if breaking:
        breaking(graph)
    conforms, _, report = validate(graph, shacl_graph=Graph().parse(SHAPES), advanced=True)
    assert conforms == (breaking is None), report


def test_no_view_a_kit_expects_holds_its_pods_address():
    """The kit's check 6, on the views a kit expects: each IRI a view file holds, as its bytes write it."""
    holding = []
    for kit in KITS:
        address = re.search(r"pim:storage <([^>]+)>", (kit / "scripted-input" / "people.ttl").read_text(encoding="utf-8"))[1]
        holding += [view.relative_to(ROOT).as_posix() for view in sorted((kit / "expected").glob("*.ttl"))
                    if f"<{address}" in view.read_text(encoding="utf-8")]
    assert KITS and holding == []
