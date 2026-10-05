"""How a pod is laid out on disk, as runtime/pod-layout.ttl says: the folder or file each kind of thing is filed in,
and the path of the file holding a thing from its name."""

import base64
from dataclasses import dataclass

from rdflib import URIRef
from rdflib.namespace import RDF

from . import Failure, store, vocabulary
from .turtle import CASCADE, DCT, PROV, REC, SOLID

LAYOUT_FILE = vocabulary.ROOT / "runtime" / "pod-layout.ttl"
LAYOUT_GRAPH = "urn:cascade:pod-layout"
BASE = "https://pod.invalid/"


def stem(name):
    if name.startswith("urn:uuid:"):
        return name[len("urn:uuid:"):]
    if name.startswith("ni:///sha-256;"):
        encoded = name[len("ni:///sha-256;"):]
        return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()
    raise Failure(f"no file name for {name}")


@dataclass(frozen=True)
class Placement:
    kind: URIRef | None
    file: str | None
    folder: str | None
    filed_with: URIRef | None
    for_subjects_of: URIRef | None
    fan_out: int
    written_by: str | None
    title: str | None
    stores_bytes: bool

    def path(self, name, folder=None):
        """The path of the file holding the thing named `name`: this placement's file, or else a file in `folder` or
        this placement's own, under the subfolder its fan-out gives."""
        if self.file is not None:
            return self.file
        named = stem(str(name))
        fanned = f"{named[:self.fan_out]}/" if self.fan_out else ""
        return f"{folder or self.folder}{fanned}{named}{'' if self.stores_bytes else '.ttl'}"


class Layout:
    def __init__(self, path=LAYOUT_FILE):
        self.file = path
        graph = store.parsed(path, BASE)

        def value(node, predicate):
            return graph.value(node, predicate)

        def relative(node, predicate):
            found = value(node, predicate)
            return None if found is None else str(found)[len(BASE):]

        def text(node, predicate):
            found = value(node, predicate)
            return None if found is None else str(found)

        self.placements = [
            Placement(kind=value(node, SOLID.forClass), file=relative(node, SOLID.instance),
                      folder=relative(node, SOLID.instanceContainer), filed_with=value(node, REC.filedWith),
                      for_subjects_of=value(node, REC.forSubjectsOf), fan_out=int(text(node, REC.fanOut) or 0),
                      written_by=text(node, REC.writtenBy), title=text(node, DCT.title),
                      stores_bytes=bool(value(node, REC.storesBytes)))
            for node in sorted(graph.subjects(RDF.type, REC.Placement), key=lambda node: str(graph.value(
                node, SOLID.instance) or graph.value(node, SOLID.instanceContainer) or graph.value(node, REC.filedWith)))]
        [views] = [p for p in self.placements if p.kind == REC.View]
        self.views_placement, self.views_folder = views, views.folder

    def triples(self, address):
        """The layout read with `address`, a pod's root, as its base."""
        return store.parsed(self.file, address)

    def in_views(self, placement):
        return (placement.file or placement.folder or "").startswith(self.views_folder)

    def place(self, kind, stating=()):
        """Where a thing of the class `kind` that states the predicates `stating` is filed, outside the views."""
        matching = [p for p in self.placements if p.kind == kind and not self.in_views(p)]
        found = [p for p in matching if p.for_subjects_of in stating] or [p for p in matching if p.for_subjects_of is None]
        if len(found) != 1:
            raise Failure(f"the layout files a {kind} in {len(found)} places, not one")
        return found[0]

    def filed_with(self, predicate, value, name):
        """The path of the file holding the thing named `name` that states `predicate` of a thing filed by the
        placement `value`."""
        [placement] = [p for p in self.placements if p.filed_with == predicate]
        return placement.path(name, value.folder)

    def version(self, of, name):
        return self.filed_with(PROV.specializationOf, of, name)

    def revision(self, of, name):
        return self.filed_with(REC.revisionOf, of, name)

    @property
    def stored_bytes(self):
        [placement] = [p for p in self.placements if p.stores_bytes]
        return placement

    @property
    def built(self):
        """Each file a query writes, by its path, with that query's path under queries/v1-draft/."""
        return {p.file: p.written_by for p in self.placements if p.written_by is not None}

    @property
    def views(self):
        """Each view a query writes, by the class of the things it lists."""
        return {p.kind: p for p in self.placements if p.written_by is not None and p.kind is not None}

    @property
    def type_index(self):
        return self.place(SOLID.TypeIndex).file

    @property
    def manifest(self):
        return self.place(CASCADE.ExportManifest).file

    @property
    def derived(self):
        """Each file the build writes."""
        return sorted([*self.built, self.type_index, self.manifest])


LAYOUT = Layout()
NOT_RDF = LAYOUT.stored_bytes.folder


def save(files, folder):
    """Writes each file's bytes at its path under the folder."""
    for path, octets in sorted(files.items()):
        target = folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)
