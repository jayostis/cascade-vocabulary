"""The one Turtle writer. Subjects in IRI order, then any blank node no statement leads to; predicates in IRI order;
values in the order they are written; a blank node inside the statement that leads to it; an IRI under the file's own
folder relative to the file."""

import re
from collections import defaultdict
from urllib.parse import urljoin

from rdflib import BNode, URIRef
from rdflib.namespace import RDF, XSD

from . import Failure

PREFIXES = {
    "bridge": "https://ns.cascadeprotocol.org/bridge/v1-draft#",
    "cascade": "https://ns.cascadeprotocol.org/core/v1#",
    "clinical": "https://ns.cascadeprotocol.org/clinical/v1#",
    "config": "tag:rdf4j.org,2023:config/",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "graphdb": "http://www.ontotext.com/config/graphdb#",
    "health": "https://ns.cascadeprotocol.org/health/v1#",
    "jdg": "https://ns.cascadeprotocol.org/judgments/v1-draft#",
    "ldp": "http://www.w3.org/ns/ldp#",
    "npx": "http://purl.org/nanopub/x/",
    "pav": "http://purl.org/pav/",
    "pim": "http://www.w3.org/ns/pim/space#",
    "prov": "http://www.w3.org/ns/prov#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rec": "https://ns.cascadeprotocol.org/records/v1-draft#",
    "solid": "http://www.w3.org/ns/solid/terms#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
LOCAL_NAME = re.compile(r"[A-Za-z](?:[A-Za-z0-9_.-]*[A-Za-z0-9_-])?")


def prefixed(iri):
    """The IRI as prefix:name by the prefix table, or None."""
    for prefix, namespace in PREFIXES.items():
        if iri.startswith(namespace) and LOCAL_NAME.fullmatch(iri[len(namespace):]):
            return f"{prefix}:{iri[len(namespace):]}"
    return None


def _string(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    return f'"{escaped}"'


def _literal(literal, iri):
    if literal.language:
        return f"{_string(str(literal))}@{literal.language}"
    if literal.datatype is None or literal.datatype == XSD.string:
        return _string(str(literal))
    return f"{_string(str(literal))}^^{iri(str(literal.datatype))}"


def term(node):
    """The node as N-Triples writes it."""
    if isinstance(node, URIRef):
        return f"<{node}>"
    if isinstance(node, BNode):
        return f"_:{node}"
    return _literal(node, lambda iri: f"<{iri}>")


def ntriples(triples):
    return "".join(sorted({" ".join(term(t) for t in triple) + " .\n" for triple in triples}))


def _relative(iri, base):
    """The shortest form of the IRI relative to the file that reads back as the IRI, or None."""
    folder = base[: base.rindex("/") + 1]
    if iri == base or iri.startswith(base + "#"):
        written = iri[len(base):]
    elif iri.startswith(folder):
        rest = iri[len(folder):]
        written = rest if rest and ":" not in rest.split("/")[0] else "./" + rest
    else:
        return None
    return written if urljoin(base, written) == iri else None


def write(triples, base=None):
    return _Document(set(triples), base).text().encode("utf-8")


class _Document:
    def __init__(self, triples, base):
        self.base, self.used = base, set()
        self.statements = defaultdict(lambda: defaultdict(list))
        for s, p, o in triples:
            self.statements[s][p].append(o)
        objects = [o for _, _, o in triples if isinstance(o, BNode)]
        if len(objects) != len(set(objects)):
            raise Failure("a blank node is the object of more than one triple")
        self.named = sorted((s for s in self.statements if not isinstance(s, BNode)), key=str)
        self.anonymous = [s for s in self.statements if isinstance(s, BNode) and s not in objects]
        reached = set()

        def reach(node):
            for values in self.statements.get(node, {}).values():
                for value in values:
                    if isinstance(value, BNode) and value not in reached:
                        reached.add(value)
                        reach(value)

        for subject in self.named + self.anonymous:
            reach(subject)
        if {s for s in self.statements if isinstance(s, BNode)} - reached - set(self.anonymous):
            raise Failure("a blank node no statement leads to is the object of another")

    def text(self):
        blocks = [self._block(self._node(s), s) for s in self.named]
        blocks += sorted(self._block("[]", s) for s in self.anonymous)
        head = "".join(f"@prefix {prefix}: <{PREFIXES[prefix]}> .\n" for prefix in sorted(self.used))
        return head + ("\n" if head else "") + "\n\n".join(blocks) + "\n"

    def _block(self, written, subject):
        lines = [written]
        statements = self._predicates(subject)
        for index, (predicate, values) in enumerate(statements):
            end = " ." if index == len(statements) - 1 else " ;"
            if len(values) == 1:
                lines.append(f"  {predicate} {values[0]}{end}")
            else:
                lines.append(f"  {predicate}")
                lines += [f"    {value}{end if i == len(values) - 1 else ' ,'}" for i, value in enumerate(values)]
        return "\n".join(lines)

    def _predicates(self, subject):
        return [("a" if p == RDF.type else self._iri(str(p)), sorted(self._node(o) for o in objects))
                for p, objects in sorted(self.statements[subject].items(), key=lambda item: str(item[0]))]

    def _node(self, node):
        if isinstance(node, URIRef):
            return self._iri(str(node))
        if isinstance(node, BNode):
            return "[ " + " ; ".join(f"{p} {', '.join(values)}" for p, values in self._predicates(node)) + " ]"
        return _literal(node, self._iri)

    def _iri(self, iri):
        relative = _relative(iri, self.base) if self.base else None
        if relative is not None:
            return f"<{relative}>"
        written = prefixed(iri)
        if written is None:
            return f"<{iri}>"
        self.used.add(written.split(":", 1)[0])
        return written
