"""An example: its pod's folder and address, its story's events and the files each adds, the view the layout lists each
kind in and the folder its records are filed in, and its pod in a store. A fixture: a few files laid out like a pod,
built the same way."""

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path, PurePosixPath

from rdflib.namespace import RDF

from . import Failure, derive, derived_files, store, turtle, vocabulary
from .pod import LAYOUT, LAYOUT_GRAPH, NOT_RDF
from .store import ENGINES, Store
from .turtle import PROV


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
        """Each view file the layout lists a kind's entries in, by its name, which is that of the view that builds it."""
        return {PurePosixPath(view.written_by).stem: view.file for view in LAYOUT.views.values()}

    @cached_property
    def records_folders(self):
        """Each kind the layout lists in a view, by where its records are filed."""
        return {kind: LAYOUT.place(kind) for kind in LAYOUT.views}

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

    def activity(self, name):
        """The import or entry session the event made, or None if it filed none."""
        event = self.event(name)
        if "import" in event:
            return event["import"]
        folder = LAYOUT.place(PROV.Activity).folder
        found = {str(session) for path in event["adds"] if path.startswith(folder)
                 for session in store.parsed(self.pod / path).subjects(RDF.type, PROV.Activity)}
        if len(found) > 1:
            raise Failure(f"{name} filed {len(found)} entry sessions, not one")
        return found.pop() if found else None

    def files(self, event=None):
        return sorted(path for e in self.through(event) for path in e["adds"])

    def added_by(self, event=None):
        return {path: e["event"] for e in self.through(event) for path in e["adds"]}

    def story_store(self, engine, through=None):
        """A store holding each file the story adds through the event, and none the build writes, each in a graph of
        its own."""
        return loaded(engine, self.pod, self.address, self.files(through))

    def build(self, engine, lens, through=None):
        """The pod as every tool and question sees it, in its store: each file through the event, the lens's derived
        state and the files built from them, each in a graph of its own and all of them in the default graph, and the
        layout read with the pod's address as its base, in a graph of its own and the default graph."""
        return built(self.story_store(engine, through), lens, self.address,
                     lambda store: derived_files.add(self, store, through))

    def derived_turtle(self, engine):
        """Each derived file of the whole pod under the default lens, as Turtle, by its path within pod/."""
        return {path: turtle.write(triples, self.address + path)
                for path, triples in self.build(engine, vocabulary.DEFAULT_LENS).files.items()}


@dataclass(frozen=True)
class Fixture:
    """A folder of Turtle files laid out like a pod at FIXTURE_ADDRESS, beside the test manifest of what queries give
    over it. It has no story, and is built as a pod is at one step, less the manifest of the build."""
    manifest: Path

    @property
    def folder(self):
        return self.manifest.parent

    @property
    def name(self):
        return self.folder.name

    @property
    def address(self):
        return FIXTURE_ADDRESS

    def files(self):
        return sorted(path.relative_to(self.folder).as_posix() for path in self.folder.rglob("*.ttl")
                      if path != self.manifest)

    def build(self, engine, lens):
        return built(loaded(engine, self.folder, self.address, self.files()), lens, self.address,
                     lambda store: derived_files.built(store, self.address))


FIXTURE_ADDRESS = "https://pod.example/"


def loaded(engine, folder, address, paths):
    """A store holding each RDF file at a path under `folder`, in a graph named by `address` and the path."""
    store = ENGINES[engine]()
    for path in paths:
        if not path.startswith(NOT_RDF):
            store.load(folder / path, address + path)
    return store


def built(store, lens, address, add_files):
    derived = derive.derive(store, lens)
    files = add_files(store)
    store.add(LAYOUT.triples(address), LAYOUT_GRAPH)
    return Build(store, derived, files)


@dataclass(frozen=True)
class Build:
    store: Store
    derived: derive.Derived
    files: dict
