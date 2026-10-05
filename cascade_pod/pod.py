"""How a pod is laid out on disk: the folder each kind of file is filed in, the files at fixed paths, and a file's path
from the name of the thing it holds."""

import base64

from . import Failure

WRITER_FOLDERS = {
    "subject": "subject",
    "records": "records",
    "activities": "provenance/activities",
    "documents": "provenance/documents",
    "imports": "provenance/imports",
    "attachments": "attachments",
}
MATCHER_FOLDERS = {
    "judgments": "judgments",
    "references": "references",
}
FOLDERS = WRITER_FOLDERS | MATCHER_FOLDERS
OWNED_POD_FOLDERS = sorted({folder.split("/")[0] for folder in WRITER_FOLDERS.values()})
NOT_RDF = (FOLDERS["attachments"] + "/", ".well-known/")
TYPE_INDEX = "settings/privateTypeIndex.ttl"
LABEL_FILE = "clinical/labels.ttl"
INDEX_FILE = "index.ttl"
MANIFEST_FILE = "manifest.ttl"


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


def attachment(document):
    return f"{FOLDERS['attachments']}/sha-256/{stem(document)}"


def save(files, folder):
    """Writes each file's bytes at its path under the folder."""
    for path, octets in sorted(files.items()):
        target = folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)
