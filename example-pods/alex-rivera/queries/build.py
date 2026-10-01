"""Builds Alex Rivera's views, labels, index and manifest from the finished pod.

python3 example-pods/alex-rivera/queries/build.py --engine oxigraph|rdflib [--out <directory>]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple

EXAMPLE = Path(__file__).absolute().parent.parent
ROOT = EXAMPLE.parent.parent
QUERIES = ROOT / "queries" / "v1-draft"
POD = EXAMPLE / "pod"
POD_BASE = "https://pod.alex-rivera.example/"
NOT_RDF = ("attachments/", ".well-known/")
XSD_STRING = "http://www.w3.org/2001/XMLSchema#string"
VIEW_FILES = {
    "allergies": "clinical/allergies.ttl",
    "conditions": "clinical/conditions.ttl",
    "immunizations": "clinical/immunizations.ttl",
    "procedures": "clinical/procedures.ttl",
    "patients": "clinical/patient-profile.ttl",
}
LABEL_FILE = "clinical/labels.ttl"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
PROV_USED = "http://www.w3.org/ns/prov#used"
REC_VIEW = "https://ns.cascadeprotocol.org/records/v1-draft#View"
CURRENT_REFERENCE_VERSIONS = "questions/pod/Which reference versions are current.rq"


def events():
    return json.loads((EXAMPLE / "events.json").read_text(encoding="utf-8"))


def pod_files(through=None):
    """Every pod file events E1 to `through` add, the last event when it is None."""
    files = []
    for event in events()["events"]:
        files += event["adds"]
        if event["event"] == through:
            break
    else:
        if through is not None:
            raise ValueError(f"no event {through}")
    return sorted(files)


def rdf_files(through=None):
    return [path for path in pod_files(through) if not path.startswith(NOT_RDF)]


def query_text(relative):
    return (QUERIES / relative).read_text(encoding="utf-8")


def named(folder):
    return {path.stem: path.relative_to(QUERIES).as_posix() for path in sorted((QUERIES / folder).glob("*.rq"))}


def positions():
    """Each query the root crate gives a position, by its path under QUERIES."""
    crate = json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    return {(ROOT / entity["@id"]).relative_to(QUERIES).as_posix(): entity["position"]
            for entity in crate["@graph"] if "position" in entity}


def derivations(lens):
    steps = [*named("derivations").values(), named("lenses")[lens]]
    return sorted(steps, key=positions().__getitem__)


# Terms are ("iri", value), ("blank", id) or ("literal", lexical form, datatype, language), whichever engine made them.

class Oxigraph:
    def __init__(self):
        import pyoxigraph
        self.ox = pyoxigraph
        self.store = pyoxigraph.Store()

    def load(self, path, base):
        self.store.load(path.read_bytes(), format=self.ox.RdfFormat.TURTLE, base_iri=base,
                        to_graph=self.ox.DefaultGraph())

    def _term(self, term):
        if isinstance(term, self.ox.NamedNode):
            return ("iri", term.value)
        if isinstance(term, self.ox.BlankNode):
            return ("blank", term.value)
        return ("literal", term.value, term.datatype.value if not term.language else None, term.language)

    def _node(self, term):
        if term[0] == "iri":
            return self.ox.NamedNode(term[1])
        if term[0] == "blank":
            return self.ox.BlankNode(term[1])
        if term[3]:
            return self.ox.Literal(term[1], language=term[3])
        return self.ox.Literal(term[1], datatype=self.ox.NamedNode(term[2] or XSD_STRING))

    def construct(self, query):
        return {tuple(self._term(t) for t in (x.subject, x.predicate, x.object)) for x in self.store.query(query)}

    def triples(self):
        return {tuple(self._term(t) for t in (x.subject, x.predicate, x.object))
                for x in self.store.quads_for_pattern(None, None, None, self.ox.DefaultGraph())}

    def add(self, triples):
        self.store.extend([self.ox.Quad(*(self._node(t) for t in triple), self.ox.DefaultGraph()) for triple in triples])

    def select(self, query):
        solutions = self.store.query(query)
        names = [v.value for v in solutions.variables]
        return [{name: self._term(row[name]) for name in names if row[name] is not None} for row in solutions]


class Rdflib:
    def __init__(self):
        import rdflib
        rdflib.NORMALIZE_LITERALS = False
        self.rdflib = rdflib
        self.graph = rdflib.Graph()

    def load(self, path, base):
        self.graph.parse(data=path.read_bytes(), format="turtle", publicID=base)

    def _term(self, term):
        rdflib = self.rdflib
        if isinstance(term, rdflib.URIRef):
            return ("iri", str(term))
        if isinstance(term, rdflib.BNode):
            return ("blank", str(term))
        datatype = str(term.datatype) if term.datatype else (None if term.language else XSD_STRING)
        return ("literal", str(term), datatype, term.language)

    def _node(self, term):
        rdflib = self.rdflib
        if term[0] == "iri":
            return rdflib.URIRef(term[1])
        if term[0] == "blank":
            return rdflib.BNode(term[1])
        if term[3]:
            return rdflib.Literal(term[1], lang=term[3])
        return rdflib.Literal(term[1], datatype=None if term[2] == XSD_STRING else rdflib.URIRef(term[2]))

    def construct(self, query):
        return {tuple(self._term(t) for t in triple) for triple in self.graph.query(query)}

    def triples(self):
        return {tuple(self._term(t) for t in triple) for triple in self.graph}

    def add(self, triples):
        for triple in triples:
            self.graph.add(tuple(self._node(t) for t in triple))

    def select(self, query):
        result = self.graph.query(query)
        names = [str(v) for v in result.vars]
        return [{name: self._term(row[name]) for name in names if row[name] is not None} for row in result]


ENGINES = {"oxigraph": Oxigraph, "rdflib": Rdflib}


def loaded(engine, through=None):
    store = ENGINES[engine]()
    for path in rdf_files(through):
        store.load(POD / path, POD_BASE + path)
    return store


def derive(store, lens):
    """The triples the lens's derivations add to the store, apart from those it already held."""
    held = store.triples()
    for relative in derivations(lens):
        store.add(store.construct(query_text(relative)))
    return store.triples() - held


class Built(NamedTuple):
    store: object
    derived: set
    views: dict
    labels: set


def build(engine, lens="everyday", through=None):
    """The pod's store with the lens's derived state, its views and the labels added."""
    store = loaded(engine, through)
    derived = derive(store, lens)
    views = {view: store.construct(query_text(relative)) for view, relative in named("views").items()}
    for triples in views.values():
        store.add(triples)
    labels = store.construct(query_text("labels.rq"))
    store.add(labels)
    return Built(store, derived, views, labels)


# Writing

def _escaped(text):
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def ntriples_term(term):
    if term[0] == "iri":
        return f"<{term[1]}>"
    if term[0] == "blank":
        raise ValueError(f"a blank node, _:{term[1]}, reached a written file")
    text = f'"{_escaped(term[1])}"'
    if term[3]:
        return f"{text}@{term[3]}"
    return text if term[2] == XSD_STRING else f"{text}^^<{term[2]}>"


def ntriples(triples):
    return sorted({" ".join(ntriples_term(t) for t in triple) + " ." for triple in triples})


def turtle(triples, reference_versions):
    mark = [f"<> <{RDF_TYPE}> <{REC_VIEW}> ."] + sorted(f"<> <{PROV_USED}> <{v}> ." for v in reference_versions)
    return ("\n".join(mark + ntriples(triples)) + "\n").encode("utf-8")


def index_ttl(files):
    folders = sorted({path.split("/", 1)[0] for path in files if "/" in path and not path.startswith(".")})
    contains = ",\n".join(f"        </{folder}/>" for folder in folders)
    return (f"""@prefix dct: <http://purl.org/dc/terms/> .
@prefix ldp: <http://www.w3.org/ns/ldp#> .

<./>
    a ldp:Container, ldp:BasicContainer ;
    dct:title "Pod Root Container" ;
    ldp:contains
{contains} .
""").encode("utf-8")


def manifest_ttl(created):
    return (f"""@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<#manifest> a cascade:ExportManifest ;
    dct:title "Alex Rivera's example pod" ;
    dct:created "{created}"^^xsd:dateTime ;
    cascade:schemaVersion "1.8" ;
    prov:wasGeneratedBy [
        a prov:Activity ;
        prov:startedAtTime "{created}"^^xsd:dateTime ;
        prov:wasAssociatedWith [
            a prov:SoftwareAgent ;
            rdfs:label "build.py"
        ]
    ] .
""").encode("utf-8")


def written(engine):
    """Every file the build writes, by its path within pod/."""
    built = build(engine)
    used = [row["version"][1] for row in built.store.select(query_text(CURRENT_REFERENCE_VERSIONS))]
    files = {VIEW_FILES[view]: turtle(triples, used) for view, triples in built.views.items()}
    files[LABEL_FILE] = turtle(built.labels, used)
    manifest = events()
    everything = pod_files() + manifest["derived"]
    missing = sorted((set(files) | {"index.ttl", "manifest.ttl"}) - set(manifest["derived"]))
    if missing:
        raise ValueError(f"events.json lists none of these under derived: {missing}")
    files["index.ttl"] = index_ttl(everything)
    files["manifest.ttl"] = manifest_ttl(manifest["events"][-1]["at"])
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", choices=sorted(ENGINES), required=True)
    parser.add_argument("--out", type=Path, default=POD)
    arguments = parser.parse_args()
    for relative, octets in sorted(written(arguments.engine).items()):
        target = arguments.out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
