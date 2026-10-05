import pytest
from rdflib import URIRef
from rdflib.namespace import RDF

from cascade_pod.pod import LAYOUT
from examples import EXAMPLES, moved, pod_file

REVISION = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#Revision")
JUDGMENT = URIRef("https://ns.cascadeprotocol.org/judgments/v1-draft#Judgment")


def misplacing(example):
    """Moves that put one revision in another kind's records folder and one judgment in the reference series' folder."""
    folders = [LAYOUT.place(kind).folder for kind in LAYOUT.views]
    revision = next(path for path in example.files() for folder in folders if path.startswith(folder)
                    and (None, RDF.type, REVISION) in pod_file(example, path))
    [own] = [folder for folder in folders if revision.startswith(folder)]
    other = next(folder for folder in folders if folder != own)
    judgments = LAYOUT.place(JUDGMENT).folder
    judgment = next(path for path in example.files() if path.startswith(judgments))
    references = LAYOUT.place(URIRef("https://ns.cascadeprotocol.org/records/v1-draft#ReferenceSeries")).folder
    return {revision: other + revision[len(own):], judgment: references + judgment[len(judgments):]}


@pytest.fixture(scope="session")
def misplaced(tmp_path_factory):
    """For each example, a copy of it with one revision in another kind's records folder, one judgment in the
    reference series' folder, and a file another app wrote that holds nothing the layout places; with the moves, by the
    path each file moved from."""
    found = []
    for example in EXAMPLES:
        moves = misplacing(example)
        copy = moved(example, moves, tmp_path_factory.mktemp("misplaced"),
                     added={"elsewhere/notes.ttl": "<urn:x:note> a <urn:x:Note> .\n"})
        found.append((copy, moves))
    return found
