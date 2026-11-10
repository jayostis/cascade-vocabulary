"""The vocabulary's ontology file and its shapes file as the tests read them, parsed once, and the messages a kind's row
shape gives about rows."""

from functools import cache

from pyshacl import validate
from rdflib import Graph
from rdflib.namespace import SH

from contract import CASCADE, ROOT


@cache
def terms():
    return Graph().parse(ROOT / "ontologies" / "cascade.ttl")


@cache
def shapes():
    return Graph().parse(ROOT / "ontologies" / "cascade.shapes.ttl")


def row_messages(kind, rows):
    """The messages the kind's row shape gives about the rows, every subject of them a focus node."""
    shape = terms().value(kind, CASCADE.rowShape)
    targeted = Graph() + shapes()
    for subject in set(rows.subjects()):
        targeted.add((shape, SH.targetNode, subject))
    _, report, _ = validate(rows, shacl_graph=targeted)
    return {str(message) for message in report.objects(None, SH.resultMessage)}
