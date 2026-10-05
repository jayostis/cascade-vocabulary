"""The W3C test manifests of the contract, in runtime/rules.md's test format: each entry's action and result, and what
its query gives over a store."""

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF, XSD

from contract import QUERIES, REC, named
from engines import literal

MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
QT = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")


@dataclass(frozen=True)
class Entry:
    iri: str
    name: str
    types: frozenset
    story: Path | None
    step: str | None
    lens: Path | None
    query: Path | None
    result: Path | None


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
            iri=str(entry), name=str(graph.value(entry, MF.name)), types=frozenset(graph.objects(entry, RDF.type)),
            story=path(graph.value(action, REC.story)), step=None if step is None else str(step),
            lens=path(graph.value(action, REC.lens)), query=path(graph.value(action, QT.query)),
            result=path(graph.value(entry, MF.result))))
    return found


def lens_name(file):
    lenses = {(QUERIES / relative).resolve(): name for name, relative in named("lenses").items()}
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
    return frozenset((name, node.n3()) for name, node in binding.items())


def failure(entry, store):
    """Why the entry's query over the store does not give its result, or None when it does."""
    query = Path(entry.query).read_text(encoding="utf-8")
    wanted = expected(entry.result)
    if isinstance(wanted, bool):
        found = store.ask(query)
        return None if found == wanted else f"expected {wanted}, found {found}"
    variables, rows = wanted
    names, solutions = store.answer(query)
    if variables != set(names):
        return f"expected the variables {sorted(variables)}, found {sorted(names)}"
    found = Counter(row(binding) for binding in solutions)
    if rows == found:
        return None
    return "\n".join([*(f"missing: {shown(r)}" for r in sorted((rows - found).elements(), key=shown)),
                      *(f"unexpected: {shown(r)}" for r in sorted((found - rows).elements(), key=shown))])


def shown(found_row):
    return " ".join(f"?{name}={node}" for name, node in sorted(found_row))
