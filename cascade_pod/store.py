"""Two SPARQL engines behind one interface.

A term is ("iri", value), ("blank", id) or ("literal", lexical form, datatype, language), whichever engine made it.
Every triple added under a graph's name is in the default graph as well, and queries read the default graph.
"""

import warnings

import pyoxigraph
import rdflib

XSD_STRING = "http://www.w3.org/2001/XMLSchema#string"


def keep_literals_as_written():
    rdflib.NORMALIZE_LITERALS = False


keep_literals_as_written()


def iri(value):
    return ("iri", value)


def blank(name):
    return ("blank", name)


def literal(text, datatype=XSD_STRING):
    return ("literal", text, datatype, None)


def parsed(path, base=None):
    return parsed_text(path.read_bytes(), base)


def parsed_text(octets, base=None):
    keep_literals_as_written()
    return rdflib.Graph().parse(data=octets, format="turtle", publicID=base)


def from_rdflib(node):
    if isinstance(node, rdflib.URIRef):
        return ("iri", str(node))
    if isinstance(node, rdflib.BNode):
        return ("blank", str(node))
    datatype = str(node.datatype) if node.datatype else (None if node.language else XSD_STRING)
    return ("literal", str(node), datatype, node.language)


def to_rdflib(term):
    if term[0] == "iri":
        return rdflib.URIRef(term[1])
    if term[0] == "blank":
        return rdflib.BNode(term[1])
    if term[3]:
        return rdflib.Literal(term[1], lang=term[3])
    return rdflib.Literal(term[1], datatype=None if term[2] == XSD_STRING else rdflib.URIRef(term[2]))


class Oxigraph:
    def __init__(self):
        self.store = pyoxigraph.Store()

    def load(self, path, graph):
        parsed = pyoxigraph.parse(path.read_bytes(), format=pyoxigraph.RdfFormat.TURTLE, base_iri=graph)
        self._extend([(q.subject, q.predicate, q.object) for q in parsed], graph)

    def add(self, triples, graph=None):
        self._extend([tuple(self._node(t) for t in triple) for triple in triples], graph)

    def _extend(self, triples, graph):
        graphs = [pyoxigraph.DefaultGraph()] + ([pyoxigraph.NamedNode(graph)] if graph else [])
        self.store.extend([pyoxigraph.Quad(*triple, g) for triple in triples for g in graphs])

    def _term(self, term):
        if isinstance(term, pyoxigraph.NamedNode):
            return ("iri", term.value)
        if isinstance(term, pyoxigraph.BlankNode):
            return ("blank", term.value)
        return ("literal", term.value, term.datatype.value if not term.language else None, term.language)

    def _node(self, term):
        if term[0] == "iri":
            return pyoxigraph.NamedNode(term[1])
        if term[0] == "blank":
            return pyoxigraph.BlankNode(term[1])
        if term[3]:
            return pyoxigraph.Literal(term[1], language=term[3])
        return pyoxigraph.Literal(term[1], datatype=pyoxigraph.NamedNode(term[2] or XSD_STRING))

    def construct(self, query):
        return {tuple(self._term(t) for t in (x.subject, x.predicate, x.object)) for x in self.store.query(query)}

    def select(self, query):
        solutions = self.store.query(query)
        names = [v.value for v in solutions.variables]
        return [{name: self._term(row[name]) for name in names if row[name] is not None} for row in solutions]

    def triples(self):
        return {tuple(self._term(t) for t in (x.subject, x.predicate, x.object))
                for x in self.store.quads_for_pattern(None, None, None, pyoxigraph.DefaultGraph())}

    def graphs(self):
        return sorted(graph.value for graph in self.store.named_graphs())

    def ntriples(self, graph):
        return self.store.dump(format=pyoxigraph.RdfFormat.N_TRIPLES, from_graph=pyoxigraph.NamedNode(graph))


class Rdflib:
    def __init__(self):
        keep_literals_as_written()
        self.dataset = rdflib.Dataset()

    def graph(self, name=None):
        return self.dataset.graph(rdflib.URIRef(name)) if name else self.dataset.default_graph

    def load(self, path, graph):
        self._extend(parsed(path, graph), graph)

    def add(self, triples, graph=None):
        self._extend([tuple(to_rdflib(t) for t in triple) for triple in triples], graph)

    def _extend(self, triples, graph):
        graphs = [self.graph()] + ([self.graph(graph)] if graph else [])
        self.dataset.addN((*triple, g) for triple in triples for g in graphs)

    def _query(self, query):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", r"Dataset\.\w+ is deprecated", DeprecationWarning)
            result = self.dataset.query(query)
            return [str(v) for v in result.vars or ()], list(result)

    def construct(self, query):
        _, found = self._query(query)
        return {tuple(from_rdflib(t) for t in triple) for triple in found}

    def select(self, query):
        names, rows = self._query(query)
        return [{name: from_rdflib(row[name]) for name in names if row[name] is not None} for row in rows]

    def triples(self):
        return {tuple(from_rdflib(t) for t in triple) for triple in self.graph()}

    def graphs(self):
        return sorted(str(g.identifier) for g in self.dataset.graphs() if g.identifier != rdflib.graph.DATASET_DEFAULT_GRAPH_ID)

    def ntriples(self, graph):
        return self.graph(graph).serialize(format="nt", encoding="utf-8")


ENGINES = {"oxigraph": Oxigraph, "rdflib": Rdflib}
