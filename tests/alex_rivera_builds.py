import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pyoxigraph
import pytest
import rdflib
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import XSD

rdflib.NORMALIZE_LITERALS = False

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
POD = EXAMPLE / "pod"
EXPECTED = EXAMPLE / "expected"
POD_BASE = "https://pod.alex-rivera.example/"
HANDLE_NS = "urn:example:alex-rivera:handle:"
sys.path.insert(0, str(EXAMPLE / "queries"))
import build as example_build  # noqa: E402

ENGINES = ("oxigraph", "rdflib")
LENSES = ("everyday", "export")
NOT_RDF = ("attachments/", ".well-known/solid")

MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
IN_ENTRY = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#inEntry")


def manifest():
    return json.loads((EXAMPLE / "events.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def handle_table():
    return json.loads((EXAMPLE / "handles.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _handles_by_name():
    return {row["name"]: handle for handle, row in handle_table().items()}


def name(handle):
    row = handle_table().get(handle)
    if row is None:
        pytest.fail(f"handle {handle} is not in handles.json")
    return URIRef(row["name"])


def handle(term):
    found = _handles_by_name().get(str(term))
    if found is None:
        pytest.fail(f"{term} has no handle in handles.json")
    return found


def events():
    return manifest()["events"]


def adds(event):
    for row in events():
        if row["event"] == event:
            return row["adds"]
    pytest.fail(f"events.json lists no event {event}")


def files_through(event):
    files = []
    for row in events():
        files.extend(row["adds"])
        if row["event"] == event:
            return tuple(files)
    pytest.fail(f"events.json lists no event {event}")


def is_rdf(relative):
    return not relative.startswith(NOT_RDF)


def load_pod_file(relative):
    return Graph().parse(POD / relative, format="turtle", publicID=POD_BASE + relative)


@lru_cache(maxsize=None)
def _pod(files):
    graph = Graph()
    for relative in files:
        if is_rdf(relative):
            graph += load_pod_file(relative)
    return graph


def pod(event):
    return _pod(files_through(event))


def _string_typed(term):
    if isinstance(term, Literal) and term.datatype is None and term.language is None:
        return Literal(str(term), datatype=XSD.string)
    return term


def _from_oxigraph(term):
    if isinstance(term, pyoxigraph.NamedNode):
        return URIRef(term.value)
    if isinstance(term, pyoxigraph.BlankNode):
        return BNode(term.value)
    if term.language:
        return Literal(term.value, lang=term.language)
    return _string_typed(Literal(term.value, datatype=URIRef(term.datatype.value)))


class Oxigraph:
    def __init__(self):
        self.store = pyoxigraph.Store()

    def load(self, relative):
        self.store.load(path=str(POD / relative), format=pyoxigraph.RdfFormat.TURTLE, base_iri=POD_BASE + relative)

    def derive(self, text):
        triples = list(self.store.query(text))
        self.store.extend(pyoxigraph.Quad(t.subject, t.predicate, t.object, pyoxigraph.DefaultGraph()) for t in triples)

    def construct(self, text):
        written = pyoxigraph.serialize(list(self.store.query(text)), format=pyoxigraph.RdfFormat.N_TRIPLES)
        return Graph().parse(data=written.decode("utf-8"), format="nt")

    def select(self, text):
        solutions = self.store.query(text)
        variables = solutions.variables
        return [
            {v.value: _from_oxigraph(row[v]) for v in variables if row[v] is not None}
            for row in solutions
        ]

    def state(self):
        dumped = self.store.dump(format=pyoxigraph.RdfFormat.N_TRIPLES, from_graph=pyoxigraph.DefaultGraph())
        return Graph().parse(data=dumped.decode("utf-8"), format="nt")


class Rdflib:
    def __init__(self):
        self.graph = Graph()

    def load(self, relative):
        self.graph.parse(POD / relative, format="turtle", publicID=POD_BASE + relative)

    def derive(self, text):
        self.graph += self.graph.query(text).graph

    def construct(self, text):
        result = Graph()
        result += self.graph.query(text).graph
        return result

    def select(self, text):
        return [
            {key: _string_typed(value) for key, value in row.asdict().items()}
            for row in self.graph.query(text)
        ]

    def state(self):
        return self.graph


@dataclass(frozen=True)
class Build:
    state: Graph
    views: dict
    reviews: dict


@lru_cache(maxsize=None)
def _build(engine, lens, files):
    store = {"oxigraph": Oxigraph, "rdflib": Rdflib}[engine]()
    for relative in files:
        if is_rdf(relative):
            store.load(relative)
    for relative in example_build.derivations(lens):
        store.derive(example_build.query_text(relative))
    views = {view: store.construct(example_build.query_text(r)) for view, r in example_build.named("views").items()}
    reviews = {review: store.select(example_build.query_text(r)) for review, r in example_build.named("review").items()}
    return Build(store.state(), views, reviews)


def build(engine, lens, event):
    return _build(engine, lens, files_through(event))


def comparable(term):
    if isinstance(term, BNode):
        pytest.fail(f"a view names a blank node, {term}, as an object")
    if isinstance(term, URIRef):
        found = _handles_by_name().get(str(term))
        return URIRef(HANDLE_NS + found) if found is not None else term
    return _string_typed(term)


def _member_handle(term):
    if str(term).startswith(HANDLE_NS):
        return str(term)[len(HANDLE_NS):]
    found = _handles_by_name().get(str(term))
    if found is None:
        pytest.fail(f"entry member {term} is not in the handle table")
    return found


def entries(graph):
    found = {}
    for subject in set(graph.subjects(MERGED_FROM, None)):
        members = frozenset(_member_handle(m) for m in graph.objects(subject, MERGED_FROM))
        if members in found:
            pytest.fail(f"two entries have the members {sorted(members)}")
        found[members] = {(p, comparable(o)) for p, o in graph.predicate_objects(subject)}
    return found


def values(pairs, predicate):
    return {o for p, o in pairs if p == predicate}


def members_shown(build):
    return {member for graph in build.views.values() for key in entries(graph) for member in key}


def entry_holding(build, view, member):
    held = [key for key in entries(build.views[view]) if member in key]
    assert len(held) == 1, f"{member} is in {len(held)} entries of the {view} view"
    return held[0]


def entry_members(build, entry):
    members = set(build.state.subjects(IN_ENTRY, entry))
    for graph in build.views.values():
        members.update(graph.objects(entry, MERGED_FROM))
    return frozenset(_member_handle(m) for m in members)


def listed_entries(build, review):
    return {entry_members(build, row["entry"]) for row in build.reviews[review]}


def listed_judgments(build):
    return {handle(row["judgment"]) for row in build.reviews["changed-since-judged"]}


def listed_pairs(build):
    pairs = set()
    for row in build.reviews["different-pairs-joined"]:
        assert str(row["a"]) < str(row["b"]), f"?a {row['a']} is not the smaller of the pair by STR"
        pairs.add((handle(row["a"]), handle(row["b"]), entry_members(build, row["entry"])))
    return pairs


def describe(key, expected, actual):
    lines = [f"entry {sorted(key)}:"]
    lines += [f"  missing {p.n3()} {o.n3()}" for p, o in sorted(expected - actual, key=str)]
    lines += [f"  should not have {p.n3()} {o.n3()}" for p, o in sorted(actual - expected, key=str)]
    return "\n".join(lines)


def view_differences(expected, actual):
    report = []
    for key in sorted(set(expected) | set(actual), key=sorted):
        if key not in actual:
            report.append(f"entry {sorted(key)} is missing")
        elif key not in expected:
            report.append(f"entry {sorted(key)} should not be there")
        elif expected[key] != actual[key]:
            report.append(describe(key, expected[key], actual[key]))
    return report
