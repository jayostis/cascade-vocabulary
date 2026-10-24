"""The contract's files as the tests read them: its queries, the order the root crate runs the derivations in, and the
files pod-layout.ttl says a query writes."""

import base64
import itertools
import json
import re
from functools import cache
from pathlib import Path

from rdflib import Graph, Literal, Namespace

ROOT = Path(__file__).absolute().parent.parent
QUERIES = ROOT / "queries"
LAYOUT = ROOT / "runtime" / "pod-layout.ttl"
KITS = sorted(kit for kit in (ROOT / "conformance").iterdir() if (kit / f"{kit.name}.feature").is_file())
PROV = Namespace("http://www.w3.org/ns/prov#")
CASCADE = Namespace("https://ns.cascadeprotocol.org/cascade#")
SOLID = Namespace("http://www.w3.org/ns/solid/terms#")
BASE = "https://pod.invalid/"


def file_stem(name):
    """N9: a file's name from the name of what it holds, a urn:uuid: name's UUID or an ni: name's hash in lower-case hex."""
    if name.startswith("urn:uuid:"):
        return name.removeprefix("urn:uuid:")
    digest = name.removeprefix("ni:///sha-256;")
    return base64.urlsafe_b64decode(digest + "=" * (-len(digest) % 4)).hex()


def query(relative):
    return (QUERIES / relative).read_text(encoding="utf-8")


TOKEN = re.compile(r'#[^\n]*|<[^<>"{}|^`\\\x00-\x20]*>|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|\{')


def values_bound(text, records):
    """The query with VALUES ?record { ... } opening its outermost group: how a runtime whose engine takes no initial
    binding binds ?record to the records a matcher run compares (M4)."""
    found = next(match for match in TOKEN.finditer(text) if match.group() == "{")
    block = " ".join(f"<{record}>" for record in records)
    return f"{text[:found.end()]} VALUES ?record {{ {block} }}{text[found.end():]}"


def prose(text):
    """A query's leading comment, as one paragraph."""
    lines = itertools.takewhile(lambda line: line.startswith("#"), text.splitlines())
    return " ".join(line.lstrip("#").strip() for line in lines)


@cache
def named(folder):
    return {path.stem: path.relative_to(QUERIES).as_posix() for path in sorted((QUERIES / folder).glob("*.rq"))}


@cache
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
    """Each file a query writes, by its path in a pod, with that query's path under QUERIES, the class it lists if it is
    a view or None, and whether the layout marks it written always."""
    graph = Graph().parse(LAYOUT, publicID=BASE)
    return {str(graph.value(placement, SOLID.instance))[len(BASE):]:
            (str(by), graph.value(placement, SOLID.forClass), (placement, CASCADE.writtenAlways, Literal(True)) in graph)
            for placement, by in graph.subject_objects(CASCADE.writtenByQueryPath)}


def built():
    """Each file a query writes, by its path in a pod, with that query's path under QUERIES."""
    return {path: by for path, (by, *_) in written().items()}
