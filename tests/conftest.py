import pytest
from rdflib import URIRef
from rdflib.namespace import RDF

from cascade_pod.pod import LAYOUT
from examples import EXAMPLES, moved, pod_file

REVISION = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#Revision")
SOLID = "http://www.w3.org/ns/solid/terms#"
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


def another_apps_file(example):
    """A file another app wrote: a thing of a class the layout does not place, and a type registration filing a kind
    of record the layout places somewhere else."""
    kind = next(iter(LAYOUT.views))
    return (f"<urn:x:note> a <urn:x:Note> .\n<#records> a <{SOLID}TypeRegistration> ; <{SOLID}forClass> <{kind}> ;\n"
            f"  <{SOLID}instanceContainer> <{example.address}elsewhere/> .\n")


@pytest.fixture(scope="session")
def misplaced(tmp_path_factory):
    """For each example, a copy of it with one revision in another kind's records folder, one judgment in the
    reference series' folder, and a file another app wrote that holds nothing the layout places; with the moves, by the
    path each file moved from."""
    found = []
    for example in EXAMPLES:
        moves = misplacing(example)
        copy = moved(example, moves, tmp_path_factory.mktemp("misplaced"),
                     added={"elsewhere/notes.ttl": another_apps_file(example)})
        found.append((copy, moves))
    return found
