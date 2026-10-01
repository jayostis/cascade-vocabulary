"""The files a pod's derived state gives it: a view of each type, the labels, the index and the manifest."""

from . import Failure, turtle, vocabulary
from .store import blank, iri, literal

CASCADE, DCT, LDP, PROV, RDF, RDFS, REC, XSD = (
    turtle.PREFIXES[p] for p in ("cascade", "dct", "ldp", "prov", "rdf", "rdfs", "rec", "xsd"))
TYPE = iri(RDF + "type")
VIEW_FILES = {
    "allergies": "clinical/allergies.ttl",
    "conditions": "clinical/conditions.ttl",
    "immunizations": "clinical/immunizations.ttl",
    "procedures": "clinical/procedures.ttl",
    "patients": "clinical/patient-profile.ttl",
}
LABEL_FILE = "clinical/labels.ttl"


def add(example, store, through=None):
    """Adds to a store holding the example's pod through the event and its derived state each file built from them,
    as that file's graph, and returns their triples by path within pod/."""
    current = vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"])
    used = [row["version"][1] for row in store.select(current)]
    files = {VIEW_FILES[view]: store.construct(vocabulary.query(relative))
             for view, relative in vocabulary.named("views").items()}
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
