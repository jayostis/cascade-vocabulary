import pytest
from pyshacl import validate
from rdflib import Graph, URIRef

from contract import LAYOUT, ROOT

SOLID = "http://www.w3.org/ns/solid/terms#"
SHAPES = ROOT / "ontologies" / "records" / "v1-draft" / "records.shapes.ttl"


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
