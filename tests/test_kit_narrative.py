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


def letters(text):
    """The text with all its white space dropped: a table's cells are lines in a note and run together in the markup."""
    return "".join(text.split())


def saved_texts(download):
    """The narrative text of every record in the saved Bridge output of the download, white space dropped."""
    return [letters(str(text)) for graph in saved_graphs(download)
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


ROOTS = "2.16.840.1.113883.10.20.22."
MEDICATIONS, RESULTS = {ROOTS + "2.1", ROOTS + "2.1.1"}, {ROOTS + "2.3", ROOTS + "2.3.1"}
DIRECT = {"substanceAdministration": ROOTS + "4.52", "procedure": ROOTS + "4.14", "act": ROOTS + "4.202"}


def templates(element):
    return {template.get("root") for template in element.findall(f"{V3}templateId")}


def records_statements(section):
    """The statements of a section's entries that the adapter makes a record of: an allergy, a problem in a concern act,
    an immunization, a procedure, a note activity, a medication on a list of what the person takes, a report in a Results
    section (in/sparql/document-table.rq). A concern act, a vital sign, a social history observation and a planned order
    are none."""
    for entry in section.findall(f"{V3}entry"):
        for statement in entry:
            kind, roots = statement.tag.removeprefix(V3), templates(statement)
            if DIRECT.get(kind) in roots:
                yield statement
            if kind == "substanceAdministration" and ROOTS + "4.16" in roots and templates(section) & MEDICATIONS \
                    and statement.get("moodCode") in ("INT", "EVN") and statement.get("negationInd") != "true":
                yield statement
            if kind == "organizer" and ROOTS + "4.1" in roots and templates(section) & RESULTS:
                yield statement
            if kind == "act":
                for holder in [statement, *statement.findall(f"{V3}entryRelationship")]:
                    for observation in holder.findall(f"{V3}observation"):
                        observed = templates(observation)
                        if ROOTS + "4.7" in observed or (ROOTS + "4.4" in observed and ROOTS + "4.3" in roots):
                            yield observation


def unread_sections(document, kept):
    """Each section with text that no statement the adapter makes a record of references into and whose text no saved note
    holds."""
    pointed = {reference.get("value", "").strip().removeprefix("#")
               for section in document.iter(f"{V3}section") for statement in records_statements(section)
               for reference in statement.iter(f"{V3}reference")}
    for section in document.iter(f"{V3}section"):
        text = section.find(f"{V3}text")
        if section.get("nullFlavor") or text is None or not words("".join(text.itertext())):
            continue
        ids = {element.get("ID") for element in text.iter() if element.get("ID")}
        if not ids & pointed and letters("".join(text.itertext())) not in kept:
            yield words(" ".join(section.findtext(f"{V3}title", default="a section").split()))


CASES = [(download.relative_to(ROOT).as_posix(), document) for download, document in cdas()]


def document(sections):
    return ElementTree.fromstring(f'<ClinicalDocument xmlns="urn:hl7-org:v3"><component><structuredBody>{sections}</structuredBody></component></ClinicalDocument>')


SECTION = ('<component><section><templateId root="{section}"/><title>{title}</title>'
           '<text><table><tbody><tr ID="ROW-1"><td>130/82 mm[Hg]</td></tr></tbody></table></text>'
           '<entry>{entry}</entry></section></component>')
VITAL_SIGN = ('<organizer><templateId root="2.16.840.1.113883.10.20.22.4.26"/><component><observation>'
              '<templateId root="2.16.840.1.113883.10.20.22.4.27"/><text><reference value="#ROW-1"/></text></observation></component></organizer>')
ALLERGY = ('<act><templateId root="2.16.840.1.113883.10.20.22.4.30"/><entryRelationship><observation>'
           '<templateId root="2.16.840.1.113883.10.20.22.4.7"/><text><reference value="#ROW-1"/></text></observation></entryRelationship></act>')
CONCERN_ONLY = ('<act><templateId root="2.16.840.1.113883.10.20.22.4.3"/><text><reference value="#ROW-1"/></text>'
                '<entryRelationship><observation><templateId root="2.16.840.1.113883.10.20.22.4.4"/></observation></entryRelationship></act>')
PLANNED_MEDICATION = ('<substanceAdministration moodCode="RQO"><templateId root="2.16.840.1.113883.10.20.22.4.16"/>'
                      '<text><reference value="#ROW-1"/></text></substanceAdministration>')


class TestNarrativeAccountedFor:
    """C-CDA sections a kit's saved output accounts for · conformance/*/scripted-input/*/downloads/,
    runtime/scripted-input/*/downloads/

    A kit carries C-CDA downloads and, beside each, the records an adapter made of it. Every section of a download
    that has text for a person to read is accounted for in that output: a record's statement references into the
    section's text, or a note holds the text.
    """

    class TestGivenTheDownloadsWithSavedOutput:
        """given the C-CDA downloads that have saved output"""

        def test_leaves_no_section_with_text_wholly_unread(self):
            assert len(CASES) >= 12
            unread = {re.sub(r"\s+", " ", name): sections for name, document in CASES
                      if (sections := list(unread_sections(document, saved_texts(ROOT / name))))}
            assert unread == {}


class TestChecksOfTheNarrativeCheck:
    """Checks of the check on a kit's narrative · tests/test_kit_narrative.py

    The rule above is checked by a function of this module. These cases show it a section that is read and sections that
    are not, so a rule that every kit keeps is known to be checked.
    """

    class TestUnreadSections:
        """`unread_sections()`"""

        def test_returns_nothing_for_a_section_that_an_allergy_observation_references_into(self):
            sections = SECTION.format(section="2.16.840.1.113883.10.20.22.2.6.1", title="Allergies", entry=ALLERGY)
            assert list(unread_sections(document(sections), kept=[])) == []

        @pytest.mark.parametrize("section, title, entry", [
            ("2.16.840.1.113883.10.20.22.2.4.1", "Vital Signs", VITAL_SIGN),
            ("2.16.840.1.113883.10.20.22.2.5.1", "Problems", CONCERN_ONLY),
            ("2.16.840.1.113883.10.20.22.2.1.1", "Medications", PLANNED_MEDICATION),
        ], ids=["a vital sign", "a concern act", "a medication in the request mood"])
        def test_returns_a_section_whose_text_is_referenced_only_from(self, section, title, entry):
            sections = SECTION.format(section=section, title=title, entry=entry)
            assert list(unread_sections(document(sections), kept=[])) == [title]
