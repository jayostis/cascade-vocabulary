"""The ontologies and standard queries this repository publishes, as its root crate lists them."""

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parent.parent
QUERIES = ROOT / "queries" / "v1-draft"
DEFAULT_LENS = "everyday"


def _crate():
    return json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]


def ontologies():
    """Each ontology file, by the IRI of the ontology it holds."""
    return {entity["about"]["@id"]: ROOT / entity["@id"] for entity in _crate()
            if entity["@id"].startswith("ontologies/") and not entity["@id"].endswith(".shapes.ttl")}


def load(store):
    for iri, path in ontologies().items():
        store.load(path, iri)


def query(relative):
    return (QUERIES / relative).read_text(encoding="utf-8")


def prose(text):
    """A query's leading comment, as one paragraph."""
    lines = itertools.takewhile(lambda line: line.startswith("#"), text.splitlines())
    return " ".join(line.lstrip("#").strip() for line in lines)


def named(folder):
    return {path.stem: path.relative_to(QUERIES).as_posix() for path in sorted((QUERIES / folder).glob("*.rq"))}


def questions():
    """Each question's path under QUERIES, by its path under questions/ without the suffix."""
    folder = QUERIES / "questions"
    return {path.relative_to(folder).with_suffix("").as_posix(): path.relative_to(QUERIES).as_posix()
            for path in sorted(folder.rglob("*.rq"))}


def positions():
    """Each query the root crate gives a position, by its path under QUERIES."""
    return {(ROOT / entity["@id"]).relative_to(QUERIES).as_posix(): entity["position"]
            for entity in _crate() if "position" in entity}


def derivations(lens):
    steps = [*named("derivations").values(), named("lenses")[lens]]
    return sorted(steps, key=positions().__getitem__)


def title(folder):
    """The name the root crate gives a folder of this repository, or None."""
    try:
        relative = Path(folder).absolute().relative_to(ROOT).as_posix() + "/"
    except ValueError:
        return None
    return next((entity["name"] for entity in _crate() if entity["@id"] == relative and "name" in entity), None)
