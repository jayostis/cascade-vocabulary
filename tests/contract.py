"""The contract's files as the tests read them: its queries, the order the root crate runs the derivations in, and the
files pod-layout.ttl says a query writes."""

import itertools
import json
from functools import cache
from pathlib import Path

from rdflib import Graph, Namespace

ROOT = Path(__file__).absolute().parent.parent
QUERIES = ROOT / "queries" / "v1-draft"
LAYOUT = ROOT / "runtime" / "pod-layout.ttl"
CASCADE = Namespace("https://ns.cascadeprotocol.org/core/v1#")
PROV = Namespace("http://www.w3.org/ns/prov#")
REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
SOLID = Namespace("http://www.w3.org/ns/solid/terms#")
BASE = "https://pod.invalid/"


def query(relative):
    return (QUERIES / relative).read_text(encoding="utf-8")


def prose(text):
    """A query's leading comment, as one paragraph."""
    lines = itertools.takewhile(lambda line: line.startswith("#"), text.splitlines())
    return " ".join(line.lstrip("#").strip() for line in lines)


def named(folder):
    return {path.stem: path.relative_to(QUERIES).as_posix() for path in sorted((QUERIES / folder).glob("*.rq"))}


def questions():
    """Each question's path under QUERIES, by its path under questions/ without the suffix."""
    folder = QUERIES / "questions"
    return {path.relative_to(folder).with_suffix("").as_posix(): path.relative_to(QUERIES).as_posix()
            for path in sorted(folder.rglob("*.rq"))}


@cache
def positions():
    """Each query the root crate gives a position, by its path under QUERIES."""
    crate = json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]
    return {(ROOT / entity["@id"]).relative_to(QUERIES).as_posix(): entity["position"]
            for entity in crate if "position" in entity}


def derivations(lens):
    return sorted([*named("derivations").values(), named("lenses")[lens]], key=positions().__getitem__)


@cache
def written():
    """Each file a query writes, by its path in a pod, with that query's path under QUERIES, and the class it lists if it
    is a view, or None."""
    graph = Graph().parse(LAYOUT, publicID=BASE)
    return {str(graph.value(placement, SOLID.instance))[len(BASE):]: (str(by), graph.value(placement, SOLID.forClass))
            for placement, by in graph.subject_objects(REC.writtenBy)}


def built():
    """Each file a query writes, by its path in a pod, with that query's path under QUERIES."""
    return {path: by for path, (by, _) in written().items()}
