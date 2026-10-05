"""Runs a W3C test manifest of runtime cases on an engine and reports each case's outcome in EARL."""

from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph


@dataclass(frozen=True)
class Entry:
    iri: str
    name: str
    story: Path
    step: str
    lens: Path
    query: object
    result: object


def entries(manifest):
    """Each entry the manifest at `manifest` lists, in its order."""
    return []


def steps(story):
    """The name of each step of the story at `story`, in its order."""
    return []


def run(manifest, engine):
    """The EARL report of running every entry of the manifest at `manifest` on `engine`."""
    return Graph()
