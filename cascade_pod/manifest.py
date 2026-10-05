"""Runs a W3C test manifest of runtime cases on an engine and reports each case's outcome in EARL."""

import json
import tempfile
import traceback
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF, XSD

from . import story, turtle, vocabulary
from .store import literal
from .turtle import DCT, REC

MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
QT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")
EARL = Namespace("http://www.w3.org/ns/earl#")
DOAP = Namespace("http://usefulinc.com/ns/doap#")


@dataclass(frozen=True)
class Entry:
    iri: str
    name: str
    story: Path
    step: str
    lens: Path
    query: object
    result: object
    type: str = str(REC.ReplayTest)


def path(iri):
    """The local file an IRI the manifest gives names, or None."""
    if iri is None:
        return None
    parts = urlparse(str(iri))
    return Path(url2pathname(parts.path)) if parts.scheme == "file" else None


def entries(manifest):
    """Each entry the manifest at `manifest` lists, in its order."""
    graph = Graph().parse(Path(manifest), format="turtle")
    [head] = graph.subjects(RDF.type, MF.Manifest)
    found = []
    for entry in Collection(graph, graph.value(head, MF.entries)):
        action = graph.value(entry, MF.action)
        step = graph.value(action, REC.step)
        found.append(Entry(
            iri=str(entry), name=str(graph.value(entry, MF.name)),
            story=path(graph.value(action, REC.story)), step=None if step is None else str(step),
            lens=path(graph.value(action, REC.lens)), query=path(graph.value(action, QT.query)),
            result=path(graph.value(entry, MF.result)), type=str(graph.value(entry, RDF.type))))
    return found


def steps(story_file):
    """The name of each step of the story at `story_file`, in its order."""
    return story.steps(story_file)


def lens_name(file):
    lenses = {(vocabulary.QUERIES / relative).resolve(): name for name, relative in vocabulary.named("lenses").items()}
    if file is None or Path(file).resolve() not in lenses:
        raise ValueError(f"{file} is no lens's query file")
    return lenses[Path(file).resolve()]


def expected(result):
    """The rows, as their variables and a multiset of rows, or the boolean, that a .srj file holds."""
    answer = json.loads(Path(result).read_text(encoding="utf-8"))
    if "boolean" in answer:
        return answer["boolean"]
    return set(answer["head"].get("vars", [])), Counter(row({name: term(value) for name, value in binding.items()})
                                                        for binding in answer["results"]["bindings"])


def term(value):
    if value["type"] == "uri":
        return URIRef(value["value"])
    if value["type"] in ("literal", "typed-literal"):
        if "xml:lang" in value:
            return literal(value["value"], lang=value["xml:lang"])
        datatype = value.get("datatype")
        return literal(value["value"], None if datatype in (None, str(XSD.string)) else URIRef(datatype))
    raise ValueError(f"an expected row holds a {value['type']}, which no comparison can match exactly")


def row(binding):
    return frozenset((name, turtle.term(node)) for name, node in binding.items())


class Run:
    """One run of a manifest's entries on one engine, each story replayed once and each pod built once per step and
    lens."""

    def __init__(self, engine, scratch):
        self.engine, self.scratch = engine, Path(scratch)
        self.replays, self.builds = {}, {}

    def replay(self, story_file):
        key = Path(story_file).resolve()
        if key not in self.replays:
            try:
                self.replays[key] = story.Replay(key, self.scratch / str(len(self.replays))).run()
            except Exception:
                self.replays[key] = traceback.format_exc()
        if isinstance(self.replays[key], str):
            raise RuntimeError(f"the story could not be replayed:\n{self.replays[key]}")
        return self.replays[key]

    def build(self, entry):
        replay = self.replay(entry.story)
        lens = lens_name(entry.lens)
        if entry.step not in story.steps(entry.story):
            raise ValueError(f"the story has no step {entry.step}")
        key = (replay.story_file, entry.step, lens)
        if key not in self.builds:
            store = replay.example().build(self.engine, lens, entry.step).store
            store.add(replay.steps_graph(entry.step), story.STEPS_GRAPH, alone=True)
            self.builds[key] = store
        return self.builds[key]

    def outcome(self, entry):
        """The entry's outcome, and why, if it did not pass."""
        if entry.type != str(REC.ReplayTest):
            return EARL.inapplicable, f"{entry.type} is no type of entry this runner knows"
        try:
            store = self.build(entry)
            query = Path(entry.query).read_text(encoding="utf-8")
            wanted = expected(entry.result)
            if isinstance(wanted, bool):
                found = store.ask(query)
                return (EARL.passed, None) if found == wanted else (EARL.failed, f"expected {wanted}, found {found}")
            names, rows = store.answer(query)
            found = Counter(row(binding) for binding in rows)
            return compared(wanted, set(names), found)
        except Exception:
            return EARL.failed, traceback.format_exc()


def compared(wanted, names, found):
    variables, rows = wanted
    if variables != names:
        return EARL.failed, f"expected the variables {sorted(variables)}, found {sorted(names)}"
    if rows == found:
        return EARL.passed, None
    missing, unexpected = rows - found, found - rows
    return EARL.failed, "\n".join([*(f"missing: {shown(r)}" for r in sorted(missing.elements(), key=shown)),
                                   *(f"unexpected: {shown(r)}" for r in sorted(unexpected.elements(), key=shown))])


def shown(found_row):
    return " ".join(f"?{name}={node}" for name, node in sorted(found_row))


def run(manifest, engine):
    """The EARL report of running every entry of the manifest at `manifest` on `engine`."""
    report, runtime = Graph(), BNode()
    report.bind("earl", EARL)
    report.add((runtime, RDF.type, EARL.TestSubject))
    report.add((runtime, DOAP.name, Literal(f"cascade_pod on {engine}")))
    with tempfile.TemporaryDirectory() as scratch:
        replaying = Run(engine, scratch)
        for entry in entries(manifest):
            outcome, why = replaying.outcome(entry)
            assertion, result = BNode(), BNode()
            report.add((assertion, RDF.type, EARL.Assertion))
            report.add((assertion, EARL.test, URIRef(entry.iri)))
            report.add((assertion, EARL.subject, runtime))
            report.add((assertion, EARL.mode, EARL.automatic))
            report.add((assertion, EARL.result, result))
            report.add((result, RDF.type, EARL.TestResult))
            report.add((result, EARL.outcome, outcome))
            if why:
                report.add((result, DCT.description, Literal(why)))
    return report

