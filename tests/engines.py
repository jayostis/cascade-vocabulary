"""Two SPARQL engines behind one interface, each taking and giving rdflib terms; a string literal has no datatype.
Every triple added under a graph's name is in the default graph as well, unless it is added to that graph alone or
loaded from TriG, and queries read the default graph.
"""

import copy
import hashlib
import os
import pickle
import re
import sys
import time
import warnings
from collections import OrderedDict
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from types import MethodType

import pyoxigraph
import pyparsing
import rdflib
from rdflib.namespace import XSD
from rdflib.plugins.sparql.algebra import translateQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.processor import SPARQLProcessor


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


def rebuilt_comp_value(cls, attributes, evaluator):
    copied = cls.__new__(cls)
    OrderedDict.__init__(copied)
    copied.__dict__.update(attributes)
    if evaluator:
        copied._evalfn = MethodType(evaluator, copied)
    return copied


def reduce_comp_value(self):
    """A CompValue takes its name to construct, so neither copy nor pickle can rebuild one by the default."""
    attributes = {name: value for name, value in self.__dict__.items() if name != "_evalfn"}
    evaluator = getattr(self.__dict__.get("_evalfn"), "__func__", None)
    return rebuilt_comp_value, (type(self), attributes, evaluator), None, None, iter(OrderedDict.items(self))


CompValue.__reduce__ = reduce_comp_value

PARSES = None


def use_parse_store(folder):
    """Stores the parses under the folder, in one named by what a stored parse depends on: the versions of rdflib,
    pyparsing and Python, and this file, which rebuilds a parse."""
    global PARSES
    key = hashlib.sha256(
        "\0".join([rdflib.__version__, pyparsing.__version__, sys.version]).encode() + Path(__file__).read_bytes()
    ).hexdigest()[:16]
    PARSES = Path(folder) / f"parses-{key}"
    PARSES.mkdir(parents=True, exist_ok=True)


def stored(query):
    return PARSES / (hashlib.sha256(query.encode()).hexdigest() + ".pickle")


def read_stored(query):
    if PARSES is None:
        return None
    try:
        return pickle.loads(stored(query).read_bytes())
    except OSError:  # a file another process is replacing is not yet stored
        return None


def parse(query):
    with literals_as_written():
        return parseQuery(query)


def parse_and_store(query):
    """A query whose parse raises is stored as None, so the test that reads it raises the error, not the collection."""
    try:
        tree = parse(query)
    except Exception:
        tree = None
    path = stored(query)
    part = path.with_name(f"{path.name}.{os.getpid()}.part")
    part.write_bytes(pickle.dumps(tree))
    try:
        os.replace(part, path)
    except OSError:  # another process stored the query as this one did
        part.unlink(missing_ok=True)


def worker_place():
    """This worker's number and the number of workers; outside xdist, the only one of one."""
    number = os.environ.get("PYTEST_XDIST_WORKER", "").removeprefix("gw")
    return (int(number), int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", 1))) if number.isdigit() else (0, 1)


def warm(queries, wait=120):
    """Has every query's parse stored: each worker parses the queries at its own place in the list, waits once for the
    others' to appear, and parses any still missing itself. A run finds what an earlier one stored."""
    if PARSES is None:
        return
    queries = sorted(set(queries))
    number, count = worker_place()
    for query in queries[number::count]:
        if not stored(query).is_file():
            parse_and_store(query)
    deadline = time.monotonic() + wait
    missing = [query for query in queries if not stored(query).is_file()]
    while missing and time.monotonic() < deadline:
        time.sleep(0.2)
        missing = [query for query in missing if not stored(query).is_file()]
    for query in missing:
        parse_and_store(query)


@lru_cache(maxsize=None)
def parse_once(query):
    """The one parse of a query text in this process, from the store when a worker has stored it; translating mutates
    a tree, so a caller that translates copies it."""
    tree = read_stored(query)
    return parse(query) if tree is None else tree  # a text that does not parse is stored as None, and raises here


@lru_cache(maxsize=None)
def prepared(query):
    """A query translated once from its shared parse, with no prefix but those it declares."""
    with literals_as_written():
        translated = translateQuery(copy.deepcopy(parse_once(query)), None, {})
    translated._original_args = (query, {}, None)
    return translated


@lru_cache(maxsize=None)
def translated_once(query, base, namespaces, normalized):
    return translateQuery(parseQuery(query), base, dict(namespaces) if namespaces else None)


def parse_each_query_once():
    """pyshacl hands a SPARQL constraint's text to rdflib for every focus node, and rdflib parses it each time; a query
    evaluates the same from one translation."""
    evaluate = SPARQLProcessor.query

    def query(self, strOrQuery, initBindings=None, initNs=None, base=None, DEBUG=False):
        if isinstance(strOrQuery, str):
            strOrQuery = translated_once(
                strOrQuery, base, tuple(sorted(initNs.items())) if initNs else None, rdflib.NORMALIZE_LITERALS
            )
        return evaluate(self, strOrQuery, initBindings, initNs, base, DEBUG)

    SPARQLProcessor.query = query


TOKEN = re.compile(r'''"""(?:[^"\\]|\\.|"(?!""))*"""|\'\'\'(?:[^'\\]|\\.|'(?!''))*\'\'\'|#[^\n]*|<(?:[^<>"{}|^`\\\s0-9?$=!&|()+-][^<>"{}|^`\\\s]*)?>'''
                   r'''|"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|\\.|\{''')
MARK = re.compile(r"#\s*bound:\s*\?record\s*")
BEFORE_BRACE = re.compile(r"\s*(?:WHERE\s*)?", re.IGNORECASE)


def marked_groups(query):
    """Just after the brace of each group a `# bound: ?record` line marks, with nothing but WHERE between them (M4a)."""
    found, mark = [], None
    for token in TOKEN.finditer(query):
        if token.group() != "{":
            mark = token.end() if MARK.fullmatch(token.group()) else None
            continue
        if mark is not None and BEFORE_BRACE.fullmatch(query, mark, token.start()):
            found.append(token.end())
        mark = None
    return found


def opened(query, places, records):
    """The query with a VALUES ?record block of the records just after each of the places."""
    block = " VALUES ?record { " + " ".join(f"<{record}>" for record in records) + " }"
    for at in sorted(set(places), reverse=True):
        query = query[:at] + block + query[at:]
    return query


def bound_to_records(query, records):
    """The query as an engine with no initial binding runs it bound to the records (M4a): a VALUES ?record block opening
    its outermost group and each group it marks."""
    outermost = next(token.end() for token in TOKEN.finditer(query) if token.group() == "{")
    return opened(query, [outermost, *marked_groups(query)], records)


class Store:
    def answer(self, query, records=()):
        """The query's columns, and its rows with each bound column's term: given records, the rows of the query
        evaluated with ?record bound to each in turn, as a matcher run binds it."""
        names, solutions = self._solutions(query, records)
        return names, [{name: self._term(row[name]) for name in names if row[name] is not None} for row in solutions]

    def select(self, query):
        return self.answer(query)[1]


class Oxigraph(Store):
    def __init__(self):
        self.store = pyoxigraph.Store()

    def load(self, path, graph):
        parsed = pyoxigraph.parse(path.read_bytes(), format=pyoxigraph.RdfFormat.TURTLE, base_iri=graph)
        self._extend([(q.subject, q.predicate, q.object) for q in parsed], graph)

    def load_graphs(self, path, base):
        self.store.extend(pyoxigraph.parse(path.read_bytes(), format=pyoxigraph.RdfFormat.TRIG, base_iri=base))

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

    def _solutions(self, query, records=()):
        if not records:
            solutions = self.store.query(query)
            return [v.value for v in solutions.variables], solutions
        found = [self.store.query(query, substitutions={pyoxigraph.Variable("record"): pyoxigraph.NamedNode(record)})
                 for record in records]
        return [v.value for v in found[0].variables], [row for solutions in found for row in solutions]

    def ask(self, query):
        return bool(self.store.query(query))

    def gives_a_row(self, query):
        """Whether the SELECT gives a row, found without making the others; so an error the query raises after its
        first row is not seen."""
        return next(iter(self.store.query(query)), None) is not None

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

    def load_graphs(self, path, base):
        with literals_as_written():
            quads = list(rdflib.Dataset().parse(data=path.read_bytes(), format="trig", publicID=base).quads())
        default = rdflib.graph.DATASET_DEFAULT_GRAPH_ID
        self.dataset.addN((*map(plain, (s, p, o)), self.graph(None if g == default else str(g))) for s, p, o, g in quads)

    def add(self, triples, graph=None, alone=False):
        self._extend(list(triples), graph, alone)

    def _extend(self, triples, graph, alone=False):
        graphs = ([] if alone else [self.graph()]) + ([self.graph(graph)] if graph else [])
        self.dataset.addN((*triple, g) for triple in triples for g in graphs)

    def _solutions(self, query, records=()):
        """The query's columns, and its rows or triples, each made while literals are kept as written."""
        bindings = [{"record": rdflib.URIRef(record)} for record in records] or [{}]
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", r"Dataset\.\w+ is deprecated", DeprecationWarning)
            with literals_as_written():
                results = [self.dataset.query(prepared(query), initBindings=bound) for bound in bindings]
                return [str(v) for v in results[0].vars or ()], [row for result in results for row in result]

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
