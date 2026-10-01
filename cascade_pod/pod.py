"""An example's pod: its address, its story's events and the files each adds, and where each kind of thing is filed."""

import base64
import json
from pathlib import Path

from . import Failure

CLINICAL = "https://ns.cascadeprotocol.org/clinical/v1#"
HEALTH = "https://ns.cascadeprotocol.org/health/v1#"
RECORD_FOLDERS = {
    HEALTH + "AllergyRecord": "allergies",
    HEALTH + "ConditionRecord": "conditions",
    HEALTH + "ImmunizationRecord": "immunizations",
    CLINICAL + "Procedure": "procedures",
}
VIEW_FILES = {
    "allergies": "clinical/allergies.ttl",
    "conditions": "clinical/conditions.ttl",
    "immunizations": "clinical/immunizations.ttl",
    "procedures": "clinical/procedures.ttl",
    "patients": "clinical/patient-profile.ttl",
}
LABEL_FILE = "clinical/labels.ttl"
NOT_RDF = ("attachments/", ".well-known/")


def stem(name):
    if name.startswith("urn:uuid:"):
        return name[len("urn:uuid:"):]
    if name.startswith("ni:///sha-256;"):
        encoded = name[len("ni:///sha-256;"):]
        return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()
    raise Failure(f"no file name for {name}")


def fanned(folder, name):
    named = stem(name)
    return f"{folder}/{named[:2]}/{named}.ttl"


class Example:
    def __init__(self, folder):
        self.folder = Path(folder).absolute()
        self.name = self.folder.name
        self.pod = self.folder / "pod"
        story = json.loads((self.folder / "events.json").read_text(encoding="utf-8"))
        self.address, self.events, self.derived = story["address"], story["events"], story["derived"]

    @property
    def title(self):
        crate = json.loads((self.folder / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        return next(entity["name"] for entity in crate["@graph"] if entity["@id"] == "./")

    def through(self, event=None):
        """The events up to and including `event`, every event when it is None."""
        names = [e["event"] for e in self.events]
        if event is None:
            return self.events
        if event not in names:
            raise Failure(f"no event {event}")
        return self.events[: names.index(event) + 1]

    def files(self, event=None):
        return sorted(path for e in self.through(event) for path in e["adds"])

    def load(self, store, event=None):
        for path in self.files(event):
            if not path.startswith(NOT_RDF):
                store.load(self.pod / path, self.address + path)
