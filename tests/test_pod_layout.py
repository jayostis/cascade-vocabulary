import ast
import re
from pathlib import PurePosixPath

import pytest
from pyshacl import validate
from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from cascade_pod import store, vocabulary
from cascade_pod.pod import LAYOUT, LAYOUT_FILE
from examples import ROOT, every_example, pod_file
from test_queries import answers

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
JDG = "https://ns.cascadeprotocol.org/judgments/v1-draft#"
SOLID = "http://www.w3.org/ns/solid/terms#"
OUT_OF_PLACE = "pod/Which files are out of place"
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
    graph = Graph().parse(LAYOUT_FILE, publicID="https://pod.example/")
    if breaking:
        breaking(graph)
    conforms, _, report = validate(graph, shacl_graph=Graph().parse(SHAPES), advanced=True)
    assert conforms == (breaking is None), report


def path_constants(source):
    """Each string in the source, other than an IRI, that spells a folder or a file the layout gives, or a folder above
    one, from its start or after a slash."""
    paths = {p.file or p.folder for p in LAYOUT.placements if p.file or p.folder}
    folders = {f"{part}/" for path in paths for part in ["/".join(path.split("/")[:i]) for i in
                                                         range(1, path.count("/") + 1)]}
    spelled = {p.rstrip("/") for p in paths if "/" in p.rstrip("/") or not p.endswith("/")} | folders | paths
    pattern = re.compile("(^|/)(" + "|".join(map(re.escape, sorted(spelled, key=len, reverse=True))) + ")")
    return sorted({node.value for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Constant)
                   and isinstance(node.value, str) and "://" not in node.value and pattern.search(node.value)})


def test_the_layout_check_finds_a_folder_or_a_file_spelled_in_a_string():
    assert path_constants('A = "records/allergies"\nB = f"{x}/manifest.ttl"\nC = "subject"\nD = "subject/x"\n'
                          'E = "clinical-records/"\nF = "https://ns.example/judgments/"\n') == [
        "/manifest.ttl", "records/allergies", "subject/x"]


def test_no_module_keeps_a_layout_of_its_own():
    modules = sorted((ROOT / "cascade_pod").glob("*.py"))
    assert {m.name: found for m in modules if (found := path_constants(m.read_text(encoding="utf-8")))} == {}


@every_example
def test_no_file_of_an_example_is_out_of_place(example):
    assert answers(example, "oxigraph", vocabulary.DEFAULT_LENS)[OUT_OF_PLACE] == []


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
def test_a_moved_revision_and_a_moved_judgment_are_each_out_of_place_where_the_layout_files_them(misplaced, engine):
    for example, moves in misplaced:
        found = sorted((str(row["file"]), str(row["thing"]), str(row["place"]))
                       for row in answers(example, engine, vocabulary.DEFAULT_LENS)[OUT_OF_PLACE])
        things = {target: str(pod_file(example, target).value(predicate=RDF.type, object=URIRef(kind)))
                  for target, kind in zip(moves.values(), (REC + "Revision", JDG + "Judgment"))}
        assert found == sorted((example.address + target, things[target],
                                example.address + str(PurePosixPath(path).parent.parent) + "/")
                               for path, target in moves.items())
