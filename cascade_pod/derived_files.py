"""The files a pod's derived state gives it: a view of each type, the labels, the index and the manifest."""

from rdflib import BNode, Literal, URIRef

from . import Failure, turtle, vocabulary
from .store import date_time

CASCADE, DCT, LDP, PROV, RDF, RDFS, REC = (
    turtle.PREFIXES[p] for p in ("cascade", "dct", "ldp", "prov", "rdf", "rdfs", "rec"))
TYPE = URIRef(RDF + "type")
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
    return triples | {(view, TYPE, URIRef(REC + "View"))} | {(view, URIRef(PROV + "used"), v) for v in reference_versions}


def index(address, files):
    root = URIRef(address)
    folders = sorted({path.split("/", 1)[0] for path in files if "/" in path and not path.startswith(".")})
    return {(root, TYPE, URIRef(LDP + "Container")), (root, TYPE, URIRef(LDP + "BasicContainer")),
            (root, URIRef(DCT + "title"), Literal("Pod Root Container")),
            *((root, URIRef(LDP + "contains"), URIRef(f"{address}{folder}/")) for folder in folders)}


def manifest(address, title, created):
    manifest, activity, agent = URIRef(address + "#manifest"), BNode("activity"), BNode("agent")
    at = date_time(created)
    return {(manifest, TYPE, URIRef(CASCADE + "ExportManifest")), (manifest, URIRef(DCT + "title"), Literal(title)),
            (manifest, URIRef(DCT + "created"), at), (manifest, URIRef(CASCADE + "schemaVersion"), Literal("1.8")),
            (manifest, URIRef(PROV + "wasGeneratedBy"), activity), (activity, TYPE, URIRef(PROV + "Activity")),
            (activity, URIRef(PROV + "startedAtTime"), at), (activity, URIRef(PROV + "wasAssociatedWith"), agent),
            (agent, TYPE, URIRef(PROV + "SoftwareAgent")), (agent, URIRef(RDFS + "label"), Literal("cascade_pod"))}
