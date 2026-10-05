"""Replays a story into a pod of its own, one step at a time: the writer files its creation, imports and entries, the
matcher its runs, and a person's judgment or a reference version is filed at the path its name gives. A step that ends
in a Failure writes nothing, and the replay goes on. The matcher's files are all saved, as a runtime would save them,
though only those new to the pod are listed as its step's."""

import copy
import json
import shutil
from pathlib import Path

from rdflib import URIRef
from rdflib.namespace import RDF

from . import Failure, match, names, store, turtle, vocabulary, write
from .example import Example
from .pod import LAYOUT, save
from .turtle import JDG, PROV, REC

STEPS_GRAPH = "urn:cascade:steps"
STEP = "urn:cascade:step:"
KINDS = ("creation", "import", "entry", "judgment", "reference", "matcher")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def steps(story):
    return [step["name"] for step in read(story)["steps"]]


def kind(step):
    found = [key for key in KINDS if key in step]
    if len(found) != 1:
        raise ValueError(f"step {step.get('name')} is not one of {', '.join(KINDS)}")
    return found[0]


class Replay:
    """A story replayed into `folder`, as an example in the form the tools read."""

    def __init__(self, story, folder, engine="rdflib"):
        self.engine = engine
        self.story_file = Path(story)
        self.source = self.story_file.parent
        self.story = read(story)
        self.folder = Path(folder)
        self.address = self.story["address"]
        self.events = []
        self.derived = []
        self.filing = None
        self.activities = {}

    def run(self):
        if self.folder.exists():
            shutil.rmtree(self.folder)
        (self.folder / "pod").mkdir(parents=True)
        name = vocabulary.title(self.source) or self.source.name
        (self.folder / "ro-crate-metadata.json").write_text(
            json.dumps({"@graph": [{"@id": "./", "name": name}]}), encoding="utf-8")
        if (self.source / "scripted-input" / "references").is_dir():
            shutil.copytree(self.source / "scripted-input" / "references", self.folder / "references")
        self._tell()
        self.filing = write.Filing(self.example())
        for step in self.story["steps"]:
            self._replay(step)
        return self

    def example(self):
        return Example(self.folder)

    def _tell(self):
        story = {"address": self.address, "events": self.events, "derived": self.derived}
        (self.folder / "events.json").write_text(json.dumps(story, indent=2), encoding="utf-8")

    def _replay(self, step):
        event = {"event": step["name"], "at": step["when"], "adds": []}
        self.events.append(event)
        happened = kind(step)
        try:
            written = getattr(self, "_" + happened)(step, event)
        except Failure:
            written = {}
        fresh = {path: octets for path, octets in written.items() if not (self.folder / "pod" / path).exists()}
        save(written if happened == "matcher" else fresh, self.folder / "pod")
        event["adds"] = sorted(fresh)
        if happened == "creation":
            self.derived = LAYOUT.derived
        self._tell()

    def _filed(self, event, file):
        """What `file` files for the event, in a copy of the filing that replaces it only if it does not fail."""
        trial = copy.deepcopy(self.filing, {id(self.filing.example): self.filing.example})
        file(trial, event)
        self.filing = trial
        return {path: octets for path, (by, octets) in trial.files.items() if by == event["event"]}

    def _creation(self, step, event):
        event["subject"] = self.story["subject"]
        return self._filed(event, write.file_subject)

    def _import(self, step, event):
        export = self.folder / "exports" / step["name"] / "apple_health_export"
        shutil.copytree(self.source / step["import"]["export"], export)
        converted = self.folder / "conversions" / step["name"].lower()
        converted.mkdir(parents=True)
        if (self.source / step["import"]["converted"]).is_dir():
            shutil.copytree(self.source / step["import"]["converted"], converted, dirs_exist_ok=True)
        event["export"] = export.relative_to(self.folder).as_posix()
        event["import"] = names.new_id()

        def file(filing, event):
            to_convert = write.file_export(filing, event, {})
            if to_convert:
                raise ValueError(f"step {event['event']} has no saved Bridge output for:\n" + "\n".join(to_convert))

        filed = self._filed(event, file)
        self.activities[step["name"]] = event["import"]
        return filed

    def _entry(self, step, event):
        entry = self.folder / "entries" / f"{step['name']}.ttl"
        entry.parent.mkdir(exist_ok=True)
        shutil.copyfile(self.source / step["entry"], entry)
        event["entry"] = entry.relative_to(self.folder).as_posix()
        sessions = []
        filed = self._filed(event, lambda filing, event: sessions.append(write.file_entry(filing, event)))
        self.activities[step["name"]] = str(sessions[-1])
        return filed

    def _judgment(self, step, event):
        octets = (self.source / step["judgment"]).read_bytes()
        judgments = list(store.parsed_text(octets).subjects(RDF.type, JDG.Judgment))
        if len(judgments) != 1:
            raise ValueError(f"{step['judgment']} holds {len(judgments)} judgments, not one")
        return {LAYOUT.place(JDG.Judgment).path(judgments[0]): octets}

    def _reference(self, step, event):
        references = match.References(self.folder / "references")
        if not references.is_version(step["reference"]):
            raise ValueError(f"step {step['name']} names {step['reference']}, a version references.ttl does not list")
        path = LAYOUT.version(LAYOUT.place(REC.ReferenceSeries), step["reference"])
        return {path: turtle.write(references.description(step["reference"]), self.address + path)}

    def _matcher(self, step, event):
        if len(self.events) < 2:
            raise ValueError(f"step {step['name']} is a matcher step with no step before it to read through")
        read_through = self.events[-2]["event"]
        pod = self.example().story_store(self.engine, read_through).triples()
        matcher = match.Matcher(pod, match.References(self.folder / "references"), step["when"], self.address,
                                self.engine)
        takes = step["matcher"].get("takes")
        event |= {"read_through": read_through, **({"takes": takes} if takes else {})}
        return matcher.take(self.activities.get(takes)) if takes else matcher.recheck()


def steps_graph(example, through):
    """What each step of a replayed example through `through` wrote: each file that was new to the pod."""
    return {(URIRef(STEP + event["event"]), PROV.generated, URIRef(example.address + path))
            for event in example.through(through) for path in event["adds"]}


def replayed(kit, out, engine="oxigraph"):
    """The example a kit's story replays into `out`, with the files the build writes for its last step under the
    default lens. A folder at `out` that is not an earlier replay is left as it is."""
    kit, out = Path(kit), Path(out)
    if not (kit / "story.json").is_file():
        raise Failure(f"{kit} has no story.json")
    if out.is_dir() and any(out.iterdir()) and not (out / "events.json").is_file():
        raise Failure(f"{out} holds files and no earlier replay; nothing changed")
    example = Replay(kit / "story.json", out, engine).run().example()
    save(example.derived_turtle(engine), example.pod)
    return example
