"""A fixture: a few Turtle files laid out like a pod, beside the test manifest of what queries give over it. It is built
as runtime/rules.md says a pod is queried at a step: each file a graph named by the pod's address and its path, the
lens's derived state, the files a query writes, and the layout."""

from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path

import pytest
from rdflib import URIRef
from rdflib.namespace import RDF

from contract import LAYOUT, PROV, REC, ROOT, derivations, query, questions, written
from engines import ENGINES, Store, parsed

ADDRESS = "https://pod.example/"
DERIVED = "urn:cascade:derived:"
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
        added = derive(store, lens)
        files = write(store)
        store.add(parsed(LAYOUT, ADDRESS), LAYOUT_GRAPH)
        return Build(store, added, files)


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
    triples by path. Each is marked a rec:View, built with the current reference versions. A view is written only when
    the pod holds a record of its class."""
    current = [row["version"] for row in store.select(query(questions()["pod/Which reference versions are current"]))]
    files = {}
    for path, (by, kind) in sorted(written().items(), key=lambda item: (item[1][1] is None, item[0])):
        if kind is not None and not store.ask(f"ASK {{ ?record a <{kind}> }}"):
            continue
        file = URIRef(ADDRESS + path)
        triples = store.construct(query(by)) | {(file, RDF.type, REC.View)} | {(file, PROV.used, v) for v in current}
        store.add(triples, ADDRESS + path)
        files[path] = triples
    return files


FIXTURES = [Fixture(manifest) for manifest in sorted((ROOT / "tests" / "fixtures").glob("*/manifest.ttl"))]


def on_its_worker(fixture, *values, id, marks=()):
    """A case about the fixture, run on the worker that builds it, so each fixture is built once a run."""
    return pytest.param(fixture, *values, id=id, marks=[pytest.mark.xdist_group(fixture.name), *marks])


every_fixture = pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES])


@cache
def built_once(fixture, engine, lens):
    return fixture.build(engine, lens)
