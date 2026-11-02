"""No section of a kit's C-CDA goes wholly unread: a section with text either has an entry that references into its text,
or the saved Bridge output of its download holds that text as a note."""

import re
import xml.etree.ElementTree as ElementTree

import pytest
from rdflib import Graph

from contract import CASCADE, ROOT

V3 = "{urn:hl7-org:v3}"
DOWNLOADS = sorted(ROOT.glob("conformance/*/scripted-input/*/downloads/*.xml")) + sorted(ROOT.glob("runtime/scripted-input/*/downloads/*.xml"))


def words(text):
    return " ".join(text.split())


def saved_graphs(download):
    return sorted(download.parent.parent.glob(f"bridge/**/{download.stem}/graph.ttl"))


def saved_texts(download):
    """The narrative text of every record in the saved Bridge output of the download, whitespace as one space."""
    return [words(str(text)) for graph in saved_graphs(download)
            for text in Graph().parse(graph, format="turtle").objects(None, CASCADE.narrativeText)]


def cdas():
    """Each download that is a C-CDA and has a saved output, with its document."""
    for download in DOWNLOADS:
        try:
            document = ElementTree.parse(download).getroot()
        except ElementTree.ParseError:
            continue
        if document.tag == f"{V3}ClinicalDocument" and saved_graphs(download):
            yield download, document


def unread_sections(document, kept):
    """Each section with text that no entry references into and whose text no saved note holds."""
    pointed = {reference.get("value", "").strip().removeprefix("#")
               for entry in document.iter(f"{V3}entry") for reference in entry.iter(f"{V3}reference")}
    for section in document.iter(f"{V3}section"):
        text = section.find(f"{V3}text")
        if section.get("nullFlavor") or text is None or not words("".join(text.itertext())):
            continue
        ids = {element.get("ID") for element in text.iter() if element.get("ID")}
        if not ids & pointed and words("".join(text.itertext())) not in kept:
            yield words(" ".join(section.findtext(f"{V3}title", default="a section").split()))


CASES = [(download.relative_to(ROOT).as_posix(), document) for download, document in cdas()]


def test_the_kits_c_cda_downloads_with_saved_output_are_found():
    assert len(CASES) >= 12


@pytest.mark.parametrize("name, document", CASES, ids=[name for name, _ in CASES])
def test_no_section_of_the_download_goes_wholly_unread(name, document):
    kept = saved_texts(ROOT / name)
    assert not list(unread_sections(document, kept)), re.sub(r"\s+", " ", name)
