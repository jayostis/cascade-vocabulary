"""Two SPARQL engines behind one interface, each taking and giving rdflib terms; a string literal has no datatype.
Every triple added under a graph's name is in the default graph as well, unless it is added to that graph alone, and
queries read the default graph.
"""

import warnings
from contextlib import contextmanager
from functools import lru_cache

import pyoxigraph
import rdflib
from rdflib.namespace import XSD
from rdflib.plugins.sparql import prepareQuery


@contextmanager
def literals_as_written():
    was, rdflib.NORMALIZE_LITERALS = rdflib.NORMALIZE_LITERALS, False
    try:
        yield
    finally:
        rdflib.NORMALIZE_LITERALS = was


def literal(value, datatype=None, lang=None):
    return rdflib.Literal(value, datatype=datatype, lang=lang, normalize=False)


def parsed(path, base=None):
    with literals_as_written():
        return rdflib.Graph().parse(data=path.read_bytes(), format="turtle", publicID=base)


def plain(node):
    if isinstance(node, rdflib.Literal) and node.datatype == XSD.string:
        return literal(str(node))
    return node


@lru_cache(maxsize=None)
def prepared(query):
    """A query parsed once, with no prefix but those it declares."""
    with literals_as_written():
        return prepareQuery(query)


class Store:
    def answer(self, query):
        """The query's columns, and its rows with each bound column's term."""
        names, solutions = self._solutions(query)
        return names, [{name: self._term(row[name]) for name in names if row[name] is not None} for row in solutions]

    def select(self, query):
        return self.answer(query)[1]


class Oxigraph(Store):
    def __init__(self):
        self.store = pyoxigraph.Store()

    def load(self, path, graph):
        parsed = pyoxigraph.parse(path.read_bytes(), format=pyoxigraph.RdfFormat.TURTLE, base_iri=graph)
        self._extend([(q.subject, q.predicate, q.object) for q in parsed], graph)

    def add(self, triples, graph=None, alone=False):
        self._extend([tuple(self._node(t) for t in triple) for triple in triples], graph, alone)

    def _extend(self, triples, graph, alone=False):
        graphs = ([] if alone else [pyoxigraph.DefaultGraph()]) + ([pyoxigraph.NamedNode(graph)] if graph else [])
        self.store.extend([pyoxigraph.Quad(*triple, g) for triple in triples for g in graphs])

    @staticmethod
    def _term(term):
        if isinstance(term, pyoxigraph.NamedNode):
            return rdflib.URIRef(term.value)
        if isinstance(term, pyoxigraph.BlankNode):
            return rdflib.BNode(term.value)
        if term.language:
            return literal(term.value, lang=term.language)
        return plain(literal(term.value, datatype=rdflib.URIRef(term.datatype.value)))

    @staticmethod
    def _node(term):
        if isinstance(term, rdflib.URIRef):
            return pyoxigraph.NamedNode(str(term))
        if isinstance(term, rdflib.BNode):
            return pyoxigraph.BlankNode(str(term))
        if term.language:
            return pyoxigraph.Literal(str(term), language=term.language)
        return pyoxigraph.Literal(str(term), datatype=pyoxigraph.NamedNode(str(term.datatype or XSD.string)))

    def construct(self, query):
        return {tuple(self._term(t) for t in (x.subject, x.predicate, x.object)) for x in self.store.query(query)}

    def _solutions(self, query):
        solutions = self.store.query(query)
        return [v.value for v in solutions.variables], solutions

    def ask(self, query):
        return bool(self.store.query(query))

    def triples(self, graph=None):
        named = pyoxigraph.NamedNode(graph) if graph else pyoxigraph.DefaultGraph()
        return {tuple(self._term(t) for t in (x.subject, x.predicate, x.object))
                for x in self.store.quads_for_pattern(None, None, None, named)}


class Rdflib(Store):
    _term = staticmethod(plain)

    def __init__(self):
        self.dataset = rdflib.Dataset()

    def graph(self, name=None):
        return self.dataset.graph(rdflib.URIRef(name)) if name else self.dataset.default_graph

    def load(self, path, graph):
        self._extend([tuple(map(plain, triple)) for triple in parsed(path, graph)], graph)

    def add(self, triples, graph=None, alone=False):
        self._extend(list(triples), graph, alone)

    def _extend(self, triples, graph, alone=False):
        graphs = ([] if alone else [self.graph()]) + ([self.graph(graph)] if graph else [])
        self.dataset.addN((*triple, g) for triple in triples for g in graphs)

    def _solutions(self, query):
        """The query's columns, and its rows or triples, each made while literals are kept as written."""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", r"Dataset\.\w+ is deprecated", DeprecationWarning)
            with literals_as_written():
                result = self.dataset.query(prepared(query))
                return [str(v) for v in result.vars or ()], list(result)

    def ask(self, query):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", r"Dataset\.\w+ is deprecated", DeprecationWarning)
            return bool(self.dataset.query(prepared(query)).askAnswer)

    def construct(self, query):
        _, found = self._solutions(query)
        return {tuple(map(plain, triple)) for triple in found}

    def triples(self, graph=None):
        return {tuple(map(plain, triple)) for triple in self.graph(graph)}


ENGINES = {"oxigraph": Oxigraph, "rdflib": Rdflib}
