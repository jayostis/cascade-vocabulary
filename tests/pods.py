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

from contract import LAYOUT, PROV, CASCADE, QUERIES, ROOT, derivations, named, query, questions, written
from engines import ENGINES, Store, parsed
from naming import ni_name

ADDRESS = "https://pod.example/"
DERIVED = "urn:cascade:derived:"
ENTRY = "urn:cascade:entry:"
KEPT = "membersJoinedByCurrentTableVersion"
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
    """Runs each derivation and the lens in turn, the claims M7 keeps across table versions just before the lens, adding
    its triples to the store and then all of them as the lens's graph, and returns the triples each added by its path."""
    held, added = store.triples(), {}
    for relative in derivations(lens):
        if relative == named("lenses")[lens]:
            added[KEPT] = kept(store) - held
            store.add(added[KEPT])
            held |= added[KEPT]
        added[relative] = store.construct(query(relative)) - held
        store.add(added[relative])
        held |= added[relative]
    store.add(set().union(*added.values()), DERIVED + lens)
    return added


STALE_CLAIMS = """
PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
PREFIX pav: <http://purl.org/pav/>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT DISTINCT ?claim ?now ?hash ?member WHERE {
  ?claim prov:wasAttributedTo cascade:CascadeMatcher ; cascade:verdict cascade:Same ; cascade:matcherRule ?rule ;
         prov:used ?input ; prov:hadMember ?member .
  ?assertion cascade:assertedClaim ?claim .
  FILTER NOT EXISTS { ?retraction prov:invalidated ?assertion }
  ?input prov:specializationOf ?series .
  ?series a cascade:ReferenceSeries ; pav:hasCurrentVersion ?now .
  FILTER (?now != ?input)
  ?ruleList pav:hasCurrentVersion ?current .
  ?row cascade:rowOfRuleListVersion ?current ; cascade:matcherRule ?rule ; cascade:queryHash ?hash .
}"""


@cache
def comparisons():
    return {ni_name(path.read_bytes()): path.read_text(encoding="utf-8")
            for path in sorted((QUERIES / "matcher").glob("*.rq"))}


def kept(store):
    """M7: each matcher claim with an assertion no retraction invalidates that used a version of a series whose current
    version is another, and whose rule's query in the current rule list, over that current version's rows, joins one of
    its members to each of the others."""
    claims = {}
    for row in store.select(STALE_CLAIMS):
        claims.setdefault((row["claim"], row["now"], str(row["hash"])), set()).add(row["member"])
    joined = {}
    for _, _, hash in claims:
        if hash not in joined:
            text = comparisons().get(hash)
            joined[hash] = set() if text is None else {
                (row["record"], row["other"], row.get("origin")) for row in store.select(text)}
    return {(claim, CASCADE.membersJoinedByCurrentTableVersion, now) for (claim, now, hash), members in claims.items()
            if any(all((one, other, now) in joined[hash] for other in members - {one}) for one in members)}


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
