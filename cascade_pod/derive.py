"""Runs a lens over an example's pod: the derivations in order, then the views and the labels."""

from typing import NamedTuple

from . import Failure, vocabulary
from .pod import LABEL_FILE, VIEW_FILES
from .store import ENGINES, XSD_STRING

DERIVED = "urn:cascade:derived:"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
PROV_USED = "http://www.w3.org/ns/prov#used"
REC_VIEW = "https://ns.cascadeprotocol.org/records/v1-draft#View"


def loaded(example, engine, through=None):
    store = ENGINES[engine]()
    example.load(store, through)
    return store


def derive(store, lens):
    """The triples the lens's derivations add to the store, apart from those it already held."""
    held = store.triples()
    for relative in vocabulary.derivations(lens):
        store.add(store.construct(vocabulary.query(relative)))
    derived = store.triples() - held
    store.add(derived, DERIVED + lens)
    return derived


class Built(NamedTuple):
    store: object
    derived: set
    views: dict
    labels: set


def build(example, engine, lens="everyday", through=None):
    """The pod's store with the lens's derived state, its views and the labels added."""
    store = loaded(example, engine, through)
    derived = derive(store, lens)
    views = {view: store.construct(vocabulary.query(relative)) for view, relative in vocabulary.named("views").items()}
    for triples in views.values():
        store.add(triples)
    labels = store.construct(vocabulary.query("labels.rq"))
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


def manifest_ttl(title, created):
    return (f"""@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<#manifest> a cascade:ExportManifest ;
    dct:title "{title}" ;
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


def written(example, engine):
    """Every file the build writes, by its path within pod/."""
    built = build(example, engine)
    current = vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"])
    used = [row["version"][1] for row in built.store.select(current)]
    files = {VIEW_FILES[view]: turtle(triples, used) for view, triples in built.views.items()}
    files[LABEL_FILE] = turtle(built.labels, used)
    missing = sorted((set(files) | {"index.ttl", "manifest.ttl"}) - set(example.derived))
    if missing:
        raise Failure(f"events.json lists none of these under derived: {missing}")
    files["index.ttl"] = index_ttl(example.files() + example.derived)
    files["manifest.ttl"] = manifest_ttl(example.title, example.events[-1]["at"])
    return files


def write(example, engine, out=None):
    for relative, octets in sorted(written(example, engine).items()):
        target = (out or example.pod) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)
    return 0
