"""The files a pod's derived state gives it: a view of each type, the labels, the index and the manifest."""

from rdflib import BNode, Literal, URIRef
from rdflib.namespace import RDF, RDFS

from . import Failure, vocabulary
from .store import date_time
from .turtle import CASCADE, DCT, LDP, PROV, REC

LABEL_FILE = "clinical/labels.ttl"


def add(example, store, through=None):
    """Adds to a store holding the example's pod through the event and its derived state each file built from them,
    as that file's graph, and returns their triples by path within pod/."""
    current = vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"])
    used = [row["version"] for row in store.select(current)]
    views = vocabulary.named("views")
    files = {path: store.construct(vocabulary.query(views[view])) for view, path in example.view_files.items()}
    files = {path: marked(example.address + path, triples, used) for path, triples in files.items()}
    _add(store, example, files)
    files[LABEL_FILE] = marked(example.address + LABEL_FILE, store.construct(vocabulary.query("labels.rq")), used)
    files["index.ttl"] = index(example.address, example.files(through) + example.derived)
    files["manifest.ttl"] = manifest(example.address + "manifest.ttl", example.title, example.through(through)[-1]["at"])
    _add(store, example, {path: files[path] for path in (LABEL_FILE, "index.ttl", "manifest.ttl")})
    unlisted, unmade = sorted(set(files) - set(example.derived)), sorted(set(example.derived) - set(files))
    if unlisted or unmade:
        raise Failure(f"events.json's derived does not list {unlisted} and lists {unmade}, which nothing builds")
    return files


def _add(store, example, files):
    for path, triples in files.items():
        store.add(triples, example.address + path)


def marked(address, triples, reference_versions):
    """A view's triples, with the file marked as a view built with these reference versions."""
    view = URIRef(address)
    return triples | {(view, RDF.type, REC.View)} | {(view, PROV.used, v) for v in reference_versions}


def index(address, files):
    root = URIRef(address)
    folders = sorted({path.split("/", 1)[0] for path in files if "/" in path and not path.startswith(".")})
    return {(root, RDF.type, LDP.Container), (root, RDF.type, LDP.BasicContainer),
            (root, DCT["title"], Literal("Pod Root Container")),
            *((root, LDP.contains, URIRef(f"{address}{folder}/")) for folder in folders)}


def manifest(address, title, created):
    manifest, activity, agent = URIRef(address + "#manifest"), BNode("activity"), BNode("agent")
    at = date_time(created)
    return {(manifest, RDF.type, CASCADE.ExportManifest), (manifest, DCT["title"], Literal(title)),
            (manifest, DCT.created, at), (manifest, CASCADE.schemaVersion, Literal("1.8")),
            (manifest, PROV.wasGeneratedBy, activity), (activity, RDF.type, PROV.Activity),
            (activity, PROV.startedAtTime, at), (activity, PROV.wasAssociatedWith, agent),
            (agent, RDF.type, PROV.SoftwareAgent), (agent, RDFS.label, Literal("cascade_pod"))}
