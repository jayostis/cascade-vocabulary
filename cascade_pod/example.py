"""An example: its pod's folder and address, its story's events and the files each adds, the view its type index lists
each kind in and the folder its records are filed in, and its pod in a store."""

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path, PurePosixPath

from . import Failure, derive, derived_files, turtle, vocabulary
from .pod import FOLDERS, NOT_RDF, TYPE_INDEX
from .store import ENGINES, Store, parsed
from .turtle import REC, SOLID


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
        """Each view file the type index lists a kind's entries in, by its name, which is that of the view that builds
        it."""
        return {PurePosixPath(path).stem: path for path in self._views.values()}

    @cached_property
    def records_folders(self):
        """Each kind the type index lists in a view, by the folder its records are filed in, named for that view."""
        return {kind: f"{FOLDERS['records']}/{PurePosixPath(path).stem}" for kind, path in self._views.items()}

    @cached_property
    def _views(self):
        index = parsed(self.pod / TYPE_INDEX, self.address + TYPE_INDEX)
        containers = tuple(str(folder) for registration, folder in index.subject_objects(SOLID.instanceContainer)
                           if index.value(registration, SOLID.forClass) == REC.View)
        return {index.value(registration, SOLID.forClass): str(file)[len(self.address):]
                for registration, file in index.subject_objects(SOLID.instance) if str(file).startswith(containers)}

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

    def story_store(self, engine, through=None):
        """A store holding each file the story adds through the event, and none the build writes, each in a graph of
        its own."""
        store = ENGINES[engine]()
        for path in self.files(through):
            if not path.startswith(NOT_RDF):
                store.load(self.pod / path, self.address + path)
        return store

    def build(self, engine, lens, through=None):
        """The pod as every tool and question sees it, in its store: each file through the event, the lens's derived
        state and the files built from them, each in a graph of its own and all of them in the default graph."""
        store = self.story_store(engine, through)
        derived = derive.derive(store, lens)
        return Build(store, derived, derived_files.add(self, store, through))

    def derived_turtle(self, engine):
        """Each derived file of the whole pod under the default lens, as Turtle, by its path within pod/."""
        return {path: turtle.write(triples, self.address + path)
                for path, triples in self.build(engine, vocabulary.DEFAULT_LENS).files.items()}


@dataclass(frozen=True)
class Build:
    store: Store
    derived: derive.Derived
    files: dict
