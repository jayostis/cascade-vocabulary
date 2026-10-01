"""Runs a lens over an example's pod: the derivations in order, then the views and the labels."""

from typing import NamedTuple

from . import Failure, turtle, vocabulary
from .pod import LABEL_FILE, VIEW_FILES
from .store import ENGINES, blank, iri, literal, to_rdflib

CASCADE, DCT, LDP, PROV, RDF, RDFS, REC, XSD = (
    turtle.PREFIXES[p] for p in ("cascade", "dct", "ldp", "prov", "rdf", "rdfs", "rec", "xsd"))
TYPE = iri(RDF + "type")
DERIVED = "urn:cascade:derived:"


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
    files: dict


def build(example, engine, lens="everyday", through=None):
    """The pod in a store, as every tool and question sees it: each file of the pod through the event, the views,
    the labels, the index and the manifest built from them, the lens's derived state and the vocabulary, each in a
    graph of its own and all of them in the default graph."""
    store = loaded(example, engine, through)
    derived = derive(store, lens)
    current = vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"])
    used = [row["version"][1] for row in store.select(current)]
    views = {VIEW_FILES[view]: store.construct(vocabulary.query(relative))
             for view, relative in vocabulary.named("views").items()}
    files = {path: marked(example.address + path, triples, used) for path, triples in views.items()}
    _add(store, example, files)
    files[LABEL_FILE] = marked(example.address + LABEL_FILE, store.construct(vocabulary.query("labels.rq")), used)
    files["index.ttl"] = index(example.address, example.files(through) + example.derived)
    files["manifest.ttl"] = manifest(example.address + "manifest.ttl", example.title, example.through(through)[-1]["at"])
    _add(store, example, {path: files[path] for path in (LABEL_FILE, "index.ttl", "manifest.ttl")})
    vocabulary.load(store)
    return Built(store, derived, files)


def _add(store, example, files):
    for path, triples in files.items():
        store.add(triples, example.address + path)


def marked(address, triples, reference_versions):
    """A view's triples, with the file marked as a view built with these reference versions."""
    view = iri(address)
    return triples | {(view, TYPE, iri(REC + "View"))} | {(view, iri(PROV + "used"), iri(v)) for v in reference_versions}


def index(address, files):
    root = iri(address)
    folders = sorted({path.split("/", 1)[0] for path in files if "/" in path and not path.startswith(".")})
    return {(root, TYPE, iri(LDP + "Container")), (root, TYPE, iri(LDP + "BasicContainer")),
            (root, iri(DCT + "title"), literal("Pod Root Container")),
            *((root, iri(LDP + "contains"), iri(f"{address}{folder}/")) for folder in folders)}


def manifest(address, title, created):
    manifest, activity, agent = iri(address + "#manifest"), blank("activity"), blank("agent")
    at = literal(created, XSD + "dateTime")
    return {(manifest, TYPE, iri(CASCADE + "ExportManifest")), (manifest, iri(DCT + "title"), literal(title)),
            (manifest, iri(DCT + "created"), at), (manifest, iri(CASCADE + "schemaVersion"), literal("1.8")),
            (manifest, iri(PROV + "wasGeneratedBy"), activity), (activity, TYPE, iri(PROV + "Activity")),
            (activity, iri(PROV + "startedAtTime"), at), (activity, iri(PROV + "wasAssociatedWith"), agent),
            (agent, TYPE, iri(PROV + "SoftwareAgent")), (agent, iri(RDFS + "label"), literal("cascade_pod"))}


def written(example, engine):
    """Every file the build writes, by its path within pod/."""
    files = build(example, engine).files
    unlisted = sorted(set(files) - set(example.derived))
    if unlisted:
        raise Failure(f"events.json lists none of these under derived: {unlisted}")
    return {path: turtle.write({tuple(map(to_rdflib, t)) for t in triples}, example.address + path)
            for path, triples in files.items()}


def write(example, engine, out=None):
    for relative, octets in sorted(written(example, engine).items()):
        target = (out or example.pod) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)
    return 0
