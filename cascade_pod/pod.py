"""An example's pod: its address, its story's events and the files each adds, where its type index files each kind of
thing, and the pod in a store."""

import base64
import json
from functools import cached_property
from pathlib import Path, PurePosixPath

from rdflib import Namespace

from . import Failure, derive, derived_files, turtle, vocabulary
from .store import ENGINES, parsed
from .turtle import PREFIXES

SOLID = Namespace(PREFIXES["solid"])
TYPE_INDEX = "settings/privateTypeIndex.ttl"
NOT_RDF = ("attachments/", ".well-known/")


def stem(name):
    if name.startswith("urn:uuid:"):
        return name[len("urn:uuid:"):]
    if name.startswith("ni:///sha-256;"):
        encoded = name[len("ni:///sha-256;"):]
        return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()
    raise Failure(f"no file name for {name}")


def save(files, folder):
    """Writes each file's bytes at its path under the folder."""
    for path, octets in sorted(files.items()):
        target = folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)


def fanned(folder, name):
    named = stem(name)
    return f"{folder}/{named[:2]}/{named}.ttl"


class Example:
    def __init__(self, folder):
        self.folder = Path(folder).absolute()
        self.name = self.folder.name
        self.pod = self.folder / "pod"
        if not (self.folder / "events.json").is_file():
            raise Failure(f"{self.folder} has no events.json")
        story = json.loads((self.folder / "events.json").read_text(encoding="utf-8"))
        self.address, self.events, self.derived = story["address"], story["events"], story["derived"]

    @property
    def title(self):
        crate = json.loads((self.folder / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        return next(entity["name"] for entity in crate["@graph"] if entity["@id"] == "./")

    @cached_property
    def view_files(self):
        """Each file the type index lists a kind's entries in, by its name, which is that of the view that builds it."""
        return {PurePosixPath(path).stem: path for path in self._registered(SOLID.instance).values()}

    @cached_property
    def folders(self):
        """Each class the type index files things of in a folder, by class."""
        return {kind: path.rstrip("/") for kind, path in self._registered(SOLID.instanceContainer).items()}

    def _registered(self, where):
        index = parsed(self.pod / TYPE_INDEX, self.address + TYPE_INDEX)
        return {index.value(registration, SOLID.forClass): str(place)[len(self.address):]
                for registration, place in index.subject_objects(where)}

    def event(self, name):
        found = next((event for event in self.events if event["event"] == name), None)
        if found is None:
            raise Failure(f"no event {name}")
        return found

    def through(self, event=None):
        """The events up to and including `event`, every event when it is None."""
        if event is None:
            return self.events
        return self.events[: self.events.index(self.event(event)) + 1]

    def files(self, event=None):
        return sorted(path for e in self.through(event) for path in e["adds"])

    def added_by(self, event=None):
        return {path: e["event"] for e in self.through(event) for path in e["adds"]}

    def load(self, store, event=None):
        for path in self.files(event):
            if not path.startswith(NOT_RDF):
                store.load(self.pod / path, self.address + path)

    def loaded(self, engine, through=None):
        store = ENGINES[engine]()
        self.load(store, through)
        return store

    def store(self, engine, lens, through=None):
        """The pod as every tool and question sees it: each file through the event, the lens's derived state and the
        files built from them, each in a graph of its own and all of them in the default graph."""
        return self._with_derived_files(engine, lens, through)[0]

    def derived_turtle(self, engine):
        """Each derived file of the whole pod under the default lens, as Turtle, by its path within pod/."""
        _, files = self._with_derived_files(engine, vocabulary.DEFAULT_LENS)
        return {path: turtle.write(triples, self.address + path)
                for path, triples in files.items()}

    def _with_derived_files(self, engine, lens, through=None):
        store = self.loaded(engine, through)
        derive.derive(store, lens)
        return store, derived_files.add(self, store, through)
