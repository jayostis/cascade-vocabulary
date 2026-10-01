import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import XSD

from cascade_pod import derive, store, vocabulary
from cascade_pod.pod import NOT_RDF, VIEW_FILES, Example

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
ALEX = Example(EXAMPLE)
POD = ALEX.pod
EXPECTED = EXAMPLE / "expected"
POD_BASE = ALEX.address
HANDLE_NS = "urn:example:alex-rivera:handle:"

ENGINES = ("oxigraph", "rdflib")
LENSES = ("everyday", "export")

MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
IN_ENTRY = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#inEntry")


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
    return ALEX.events


def adds(event):
    for row in events():
        if row["event"] == event:
            return row["adds"]
    pytest.fail(f"events.json lists no event {event}")


def files_through(event):
    return tuple(ALEX.files(event))


def is_rdf(relative):
    return not relative.startswith(NOT_RDF)


def load_pod_file(relative):
    return store.parsed(POD / relative, POD_BASE + relative)


def graph(triples):
    found = Graph()
    for triple in triples:
        found.add(tuple(store.to_rdflib(t) for t in triple))
    return found


@lru_cache(maxsize=None)
def pod(event):
    engine = store.Rdflib()
    ALEX.load(engine, event)
    return engine.graph()


def _string_typed(term):
    if isinstance(term, Literal) and term.datatype is None and term.language is None:
        return Literal(str(term), datatype=XSD.string)
    return term


@dataclass(frozen=True)
class Build:
    state: Graph
    views: dict
    needs_review: dict


@lru_cache(maxsize=None)
def build(engine, lens, event):
    built = derive.build(ALEX, engine, lens, event)
    needs_review = {kind: [{key: store.to_rdflib(value) for key, value in row.items()}
                           for row in built.store.select(vocabulary.query(vocabulary.questions()[f"{kind}/What needs review"]))]
                    for kind in ("entry", "judgment")}
    views = {view: graph(built.files[path]) for view, path in VIEW_FILES.items()}
    return Build(graph(built.store.triples()), views, needs_review)


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


def entries_needing(build, needs):
    return [row for row in build.needs_review["entry"] if str(row["needs"]) == needs]


def listed_entries(build, needs):
    return {entry_members(build, row["entry"]) for row in entries_needing(build, needs)}


def listed_judgments(build):
    return {handle(row["judgment"]) for row in build.needs_review["judgment"]}


def listed_pairs(build):
    pairs = set()
    for row in entries_needing(build, "judged different, still joined"):
        record, other = row["record"], row["otherRecord"]
        assert str(record) < str(other), f"?record {record} is not the smaller of the pair by STR"
        pairs.add((handle(record), handle(other), entry_members(build, row["entry"])))
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
