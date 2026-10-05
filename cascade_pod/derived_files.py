"""The files a pod's derived state gives it: each file a query writes, the type index and the manifest."""

from rdflib import BNode, Literal, URIRef
from rdflib.namespace import RDF, RDFS

from . import Failure, vocabulary
from .pod import LAYOUT
from .store import date_time
from .turtle import CASCADE, DCT, PROV, REC, SOLID


def add(example, store, through=None):
    """Adds to a store holding the example's pod through the event and its derived state each file built from them,
    as that file's graph, and returns their triples by path within pod/."""
    files = built(store, example.address)
    made = {LAYOUT.manifest: manifest(example.address + LAYOUT.manifest, example.title,
                                      example.through(through)[-1]["at"])}
    _add(store, example.address, made)
    files |= made
    unlisted, unmade = sorted(set(files) - set(example.derived)), sorted(set(example.derived) - set(files))
    if unlisted or unmade:
        raise Failure(f"events.json's derived does not list {unlisted} and lists {unmade}, which nothing builds")
    return files


def built(store, address):
    """Adds to a store holding the files of a pod at `address` and its derived state each file a query writes and the
    type index, as that file's graph, and returns their triples by path within the pod. The views are built first, so
    the other files a query writes can read them."""
    current = vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"])
    used = [row["version"] for row in store.select(current)]
    views = {view.file for view in LAYOUT.views.values()}
    files = {}
    for paths in (sorted(views), sorted(set(LAYOUT.built) - views)):
        made = {path: marked(address + path, store.construct(vocabulary.query(LAYOUT.built[path])), used)
                for path in paths}
        _add(store, address, made)
        files |= made
    index = {LAYOUT.type_index: type_index(address)}
    _add(store, address, index)
    return files | index


def _add(store, address, files):
    for path, triples in files.items():
        store.add(triples, address + path)


def marked(address, triples, reference_versions):
    """A view's triples, with the file marked as a view built with these reference versions."""
    view = URIRef(address)
    return triples | {(view, RDF.type, REC.View)} | {(view, PROV.used, v) for v in reference_versions}


def type_index(address):
    """The type index of a pod at `address`: a registration for each view the layout lists, giving its class, file and
    title, and one for the views folder, each named for the file or folder it registers."""
    index = URIRef(address + LAYOUT.type_index)
    triples = {(index, RDF.type, SOLID.TypeIndex), (index, RDF.type, SOLID.UnlistedDocument)}
    folder = LAYOUT.views_placement
    registered = [(view, SOLID.instance, view.file) for view in LAYOUT.views.values()]
    for placement, listing, path in registered + [(folder, SOLID.instanceContainer, folder.folder)]:
        registration = URIRef(f"{index}#{path.rstrip('/').rsplit('/', 1)[-1].removesuffix('.ttl')}")
        triples |= {(registration, RDF.type, SOLID.TypeRegistration), (registration, SOLID.forClass, placement.kind),
                    (registration, listing, URIRef(address + path)),
                    (registration, DCT.title, Literal(placement.title))}
    return triples


def manifest(address, title, created):
    manifest, activity, agent = URIRef(address + "#manifest"), BNode("activity"), BNode("agent")
    at = date_time(created)
    return {(manifest, RDF.type, CASCADE.ExportManifest), (manifest, DCT["title"], Literal(title)),
            (manifest, DCT.created, at), (manifest, CASCADE.schemaVersion, Literal("1.8")),
            (manifest, PROV.wasGeneratedBy, activity), (activity, RDF.type, PROV.Activity),
            (activity, PROV.startedAtTime, at), (activity, PROV.wasAssociatedWith, agent),
            (agent, RDF.type, PROV.SoftwareAgent), (agent, RDFS.label, Literal("cascade_pod"))}
