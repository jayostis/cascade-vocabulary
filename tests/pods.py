"""A fixture: a few Turtle files laid out like a pod, beside the test manifest of what queries give over it. It is built
as runtime/rules.md says a pod is queried at a step: each file a graph named by the pod's address and its path, the
lens's derived state, the files a query writes, each view naming its entries as a runtime's dataset does (N13), and the
layout. A .trig file holds table versions' rows, each in the graph its version names, as the matcher reads them (M13)."""

from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path

import pytest
from rdflib import URIRef
from rdflib.namespace import RDF

from contract import LAYOUT, PROV, CASCADE, ROOT, derivations, query, questions, written
from engines import ENGINES, Store, parsed

ADDRESS = "https://pod.example/"
DERIVED = "urn:cascade:derived:"
ENTRY = "urn:cascade:entry:"
LAYOUT_GRAPH = "urn:cascade:pod-layout"


@dataclass(frozen=True)
class Build:
    store: Store
    added_by_step: dict
    files: dict

    @cached_property
    def derived(self):
        return set().union(*self.added_by_step.values())


@dataclass(frozen=True)
class Fixture:
    manifest: Path

    @property
    def folder(self):
        return self.manifest.parent

    @property
    def name(self):
        return self.folder.name

    def files(self):
        return sorted(path.relative_to(self.folder).as_posix() for path in self.folder.rglob("*.ttl")
                      if path != self.manifest)

    def build(self, engine, lens):
        store = ENGINES[engine]()
        for path in self.files():
            store.load(self.folder / path, ADDRESS + path)
        for path in sorted(self.folder.glob("*.trig")):
            store.load_graphs(path, ADDRESS + path.name)
        added = derive(store, lens)
        files = write(store)
        store.add(layout(), LAYOUT_GRAPH)
        return Build(store, added, files)


@cache
def layout():
    return parsed(LAYOUT, ADDRESS)


def derive(store, lens):
    """Runs each derivation and the lens in turn, adding its triples to the store and then all of them as the lens's
    graph, and returns the triples each added by its path."""
    held, added = store.triples(), {}
    for relative in derivations(lens):
        added[relative] = store.construct(query(relative)) - held
        store.add(added[relative])
        held |= added[relative]
    store.add(set().union(*added.values()), DERIVED + lens)
    return added


def write(store):
    """Adds each file a query writes as its own graph, the views first so the others can read them, and returns their
    triples by path. Each is marked a cascade:View, built with the current reference versions. A view is written only when
    the layout marks it written always or the pod holds a record of its class."""
    current = [row["version"] for row in store.select(query(questions()["pod/Which reference versions are current"]))]
    marked = lambda path, triples: triples | {(URIRef(ADDRESS + path), RDF.type, CASCADE.View)} | {
        (URIRef(ADDRESS + path), PROV.used, v) for v in current}
    views, others = {}, {}
    for path, (by, kind, always) in written().items():
        if kind is None:
            others[path] = by
        elif always or store.ask(f"ASK {{ ?record a <{kind}> }}"):
            views[path] = store.construct(query(by))
    files = {path: marked(path, triples) for path, triples in resolved(views).items()}
    for path, triples in sorted(files.items()):
        store.add(triples, ADDRESS + path)
    for path, by in sorted(others.items()):
        files[path] = marked(path, store.construct(query(by)))
        store.add(files[path], ADDRESS + path)
    return files


def resolved(views):
    """Each view's triples with every entry placeholder resolved against the address of the view that gives the entry its
    members, or of the view naming it where none does, as a runtime's dataset holds a view it writes <#hex> (N13)."""
    owner = {str(s): ADDRESS + path for path, triples in views.items()
             for s, p, _ in triples if p == CASCADE.mergedFrom and str(s).startswith(ENTRY)}

    def rename(term, path):
        text = str(term)
        return URIRef(owner.get(text, ADDRESS + path) + "#" + text.removeprefix(ENTRY)) if text.startswith(ENTRY) else term

    return {path: {(rename(s, path), p, rename(o, path)) for s, p, o in triples} for path, triples in views.items()}


FIXTURES = [Fixture(manifest) for manifest in sorted((ROOT / "tests" / "fixtures").glob("*/manifest.ttl"))]


def on_its_worker(fixture, *values, id, marks=()):
    """A case about the fixture, run on the worker that builds it, so each fixture is built once a run."""
    return pytest.param(fixture, *values, id=id, marks=[pytest.mark.xdist_group(fixture.name), *marks])


every_fixture = pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES])


@cache
def built_once(fixture, engine, lens):
    return fixture.build(engine, lens)
