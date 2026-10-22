"""Every naming vector under tests/vectors/naming/ is reproduced by tests/naming.py, and independently of it by its
rule's query on Oxigraph or, for a content name, by Oxigraph's RDFC-1.0 and its SHA256."""

import base64
import re
from dataclasses import dataclass
from functools import cache

import pytest
from pyoxigraph import CanonicalizationAlgorithm, Dataset, RdfFormat, Store, Variable, parse, serialize
from pyoxigraph import Literal as OxigraphLiteral
from rdflib import BNode, Graph, Namespace, URIRef
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
NO_QUERY = {"VersionNamingRule", "RevisionNamingRule", "FindingNamingRule", "TableVersionNamingRule",
            "DocumentNamingRule", "ClaimNamingRule", "SnapshotNamingRule"}


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


def reference_name(vector):
    if vector.rule == "DocumentNamingRule":
        return naming.document_name(vector.input.read_bytes())
    if vector.input is not None:
        triples = naming.content(vector.input.read_text(encoding="utf-8"))
        assert naming.canonical_nquads(triples) == vector.canonical.read_text(encoding="utf-8"), vector
        return naming.content_name(triples)
    return naming.named(vector.rule, list(vector.inputs))


@pytest.mark.parametrize("vector", vectors(), ids=str)
def test_every_vector_is_the_name_the_reference_implementation_gives(vector):
    assert reference_name(vector) == vector.expected


def sparql_sha256(text):
    [solution] = Store().query("SELECT ?text (SHA256(?text) AS ?hash) {}", substitutions={
        Variable("text"): OxigraphLiteral(text)})
    return solution["hash"].value


def ni_from_hex(hexed):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(bytes.fromhex(hexed)).decode().rstrip("=")


@pytest.mark.parametrize("vector", [v for v in vectors() if v.query is not None], ids=str)
def test_every_vector_of_a_rule_with_a_query_is_what_the_query_gives_on_oxigraph(vector):
    substitutions = {Variable(f"input{n}"): OxigraphLiteral(value) for n, value in enumerate(vector.inputs, 1)}
    solutions = Store().query(vector.query.read_text(encoding="utf-8"), substitutions=substitutions)
    assert [solution["name"].value for solution in solutions] == [vector.expected]


@pytest.mark.parametrize("vector", [v for v in vectors() if v.input is not None], ids=str)
def test_every_content_vector_is_what_oxigraphs_rdfc_and_sha256_give(vector):
    if vector.rule == "DocumentNamingRule":
        text = vector.input.read_bytes().decode("utf-8")
    else:
        dataset = Dataset(parse(vector.input.read_bytes(), format=RdfFormat.N_TRIPLES))
        dataset.canonicalize(CanonicalizationAlgorithm.RDFC_1_0)
        text = "".join(sorted(serialize(dataset, format=RdfFormat.N_QUADS).decode("utf-8").splitlines(keepends=True)))
        assert text == vector.canonical.read_text(encoding="utf-8")
    assert ni_from_hex(sparql_sha256(text)) == vector.expected


def test_every_rule_has_vectors_and_a_query_unless_sparql_cannot_compute_it():
    assert {vector.rule for vector in vectors()} == set(naming.RULES)
    with_query = {vector.rule for vector in vectors() if vector.query is not None}
    assert with_query == set(naming.RULES) - NO_QUERY
    assert {file.stem for file in VECTORS.glob("*.rq")} == with_query
    assert all(vector.query is not None for vector in vectors() if vector.rule in with_query)


def test_an_input_holding_a_bar_and_one_split_at_it_have_two_names():
    by_name = {vector.name: vector for vector in vectors()}
    one, other = by_name["record-from-document-pipe-in-selector"], by_name["record-from-document-pipe-in-document"]
    assert "|".join(one.inputs) == "|".join(other.inputs)
    assert one.expected != other.expected


def test_no_name_shows_its_inputs():
    shapes = [r"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-8[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
              r"ni:///sha-256;[A-Za-z0-9_-]{43}", r"[a-z/-]+\.ttl#[0-9a-f]{64}"]
    assert [v.expected for v in vectors() if not any(re.fullmatch(shape, v.expected) for shape in shapes)] == []


@pytest.mark.parametrize("name, given, expected", base_urls(), ids=[case[0] for case in base_urls()])
def test_every_base_url_vector_is_normalised_as_rfc_3986_section_6_says(name, given, expected):
    assert naming.normalised_base_url(given) == expected


def test_a_base_url_carrying_userinfo_is_refused():
    with pytest.raises(ValueError, match="userinfo"):
        naming.server_name("https://user:secret@fhir.example.org/r4")


def test_a_code_joins_its_stem_as_encode_for_uri_writes_it():
    codes = ["NM_000249.4:c.2042C>T", "NM_000249.4:c.(116+1_117-1)_(380+1_381-1)del", "E11.65", "08", "Ñ \U0001F95C~"]
    [solution] = Store().query("SELECT " + " ".join(f'(ENCODE_FOR_URI("{c}") AS ?c{n})' for n, c in enumerate(codes))
                               + " {}")
    assert [naming.code_iri("s/", c) for c in codes] == ["s/" + solution[f"c{n}"].value for n in range(len(codes))]


def test_a_content_name_refuses_a_blank_node():
    with pytest.raises(ValueError, match="blank node"):
        naming.version_name({(BNode(), URIRef("urn:x:p"), URIRef("urn:x:o"))})
