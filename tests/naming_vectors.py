"""The naming vectors as the tests read them: the manifest under tests/vectors/naming/, each vector, the base addresses
it holds, and the second, independent computation of a list rule's name."""

from dataclasses import dataclass
from functools import cache

from rdflib import BNode, Graph, Namespace
from rdflib.collection import Collection
from rdflib.namespace import RDF

import naming
from contract import ROOT
from manifests import path

VECTORS = ROOT / "tests" / "vectors" / "naming"
MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
QT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")
BRIDGE = Namespace("https://ns.cascadeprotocol.org/bridge/v1-draft#")
CASCADE = Namespace(naming.CASCADE)


@dataclass(frozen=True)
class Vector:
    name: str
    rule: str
    inputs: tuple
    query: object
    input: object
    expected: str
    canonical: object

    def __str__(self):
        return self.name


def listed(graph, head):
    return tuple(listed(graph, item) if isinstance(item, BNode) or item == RDF.nil else str(item)
                 for item in Collection(graph, head))


@cache
def manifest():
    graph = Graph().parse(VECTORS / "manifest.ttl", format="turtle")
    [head] = graph.subjects(RDF.type, MF.Manifest)
    return graph, list(Collection(graph, graph.value(head, MF.entries)))


def vectors():
    graph, entries = manifest()
    found = []
    for entry in entries:
        if (entry, RDF.type, BRIDGE.NamingTest) not in graph:
            continue
        action, result = graph.value(entry, MF.action), graph.value(entry, MF.result)
        inputs = graph.value(action, BRIDGE.nameInputs)
        found.append(Vector(
            name=str(graph.value(entry, MF.name)), rule=str(graph.value(entry, BRIDGE.namingRule)).removeprefix(CASCADE),
            inputs=() if inputs is None else listed(graph, inputs), query=path(graph.value(action, QT.query)),
            input=path(graph.value(action, BRIDGE.input)), expected=str(graph.value(result, BRIDGE.expectedName)),
            canonical=path(graph.value(result, BRIDGE.canonicalContent))))
    return found


def base_urls():
    graph, entries = manifest()
    return [(str(graph.value(entry, MF.name)), str(graph.value(graph.value(entry, MF.action), CASCADE.serverBaseUrl)),
             str(graph.value(graph.value(entry, MF.result), CASCADE.serverBaseUrl)))
            for entry in entries if (entry, RDF.type, BRIDGE.BaseUrlNormalisationTest) in graph]


def refused_base_urls():
    graph, entries = manifest()
    return [(str(graph.value(entry, MF.name)), str(graph.value(graph.value(entry, MF.action), CASCADE.serverBaseUrl)))
            for entry in entries if (entry, RDF.type, BRIDGE.BaseUrlRefusalTest) in graph]


def flattened(inputs):
    return [part for item in inputs
            for part in ([str(len(set(item))), *sorted(set(item))] if isinstance(item, tuple) else [item])]


def v8_query(rule, count):
    escaped = "".join(f', "|", REPLACE(REPLACE(?input{n}, "%", "%25"), "\\\\|", "%7C")' for n in range(1, count + 1))
    projected = " ".join(f"?input{n}" for n in range(1, count + 1))
    return f"""SELECT {projected} ?name WHERE {{
      BIND (SHA256(CONCAT("{naming.NAMESPACE}|{naming.CASCADE}{rule}"{escaped})) AS ?hash)
      BIND (REPLACE(REPLACE(REPLACE(REPLACE(SUBSTR(?hash, 17, 1), "[048c]", "8"), "[159d]", "9"), "[26ae]", "a"),
                    "[37bf]", "b") AS ?variant)
      BIND (IRI(CONCAT("urn:uuid:", SUBSTR(?hash, 1, 8), "-", SUBSTR(?hash, 9, 4), "-8", SUBSTR(?hash, 14, 3), "-",
                       ?variant, SUBSTR(?hash, 18, 3), "-", SUBSTR(?hash, 21, 12))) AS ?name)
    }}"""
