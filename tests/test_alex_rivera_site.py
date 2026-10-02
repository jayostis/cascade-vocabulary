import shlex
import subprocess
import sys

import pytest
from rdflib import URIRef

from cascade_pod import site, store
from cascade_pod.derived_files import VIEW_FILES
from cascade_pod.pod import fanned, stem
from examples import ROOT
from test_alex_rivera_handles import ALEX
from test_alex_rivera_handles import name as name_of
from test_site import blocks, page_of, pages_of, site_files

MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
REVISION_OF = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#revisionOf")
DERIVED_FROM = URIRef("http://www.w3.org/ns/prov#wasDerivedFrom")
PENICILLIN = "urn:cascade:entry:a6ab153490000f8a538712abb75758f2280c92237cd33dc6eee4b8f00e8c2210"


@pytest.fixture(scope="module")
def pages():
    return pages_of(site_files(ALEX))


def asked(command):
    arguments = shlex.split(command)
    result = subprocess.run([sys.executable, *arguments[1:]], capture_output=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    return [dict(cell[1:].split("=", 1) for cell in line.split("\t"))
            for line in result.stdout.decode("utf-8").splitlines()]


SAMPLE = [("index.html", "What each folder holds"), ("index.html", "How many of each kind"),
          ("index.html", "What each import brought in"), ("not-shown.html", "Why it is in no view"),
          (page_of(PENICILLIN), "Where it came from")]


@pytest.mark.parametrize("page, title", SAMPLE)
def test_every_run_it_yourself_command_prints_the_rows_the_block_shows(pages, page, title):
    [block] = [b for b in blocks(pages[page]) if b["title"] == title]
    printed = asked(block["command"])
    about = [code[1:] for code in block["codes"] if code.startswith("?")]
    if about:
        printed = [row for row in printed if row.get(about[0]) == f"<{PENICILLIN}>"]
    shown = [{column: cell["value"] for column, cell in row.items()} for row in block["rows"]]
    assert shown and shown == [{c: row[c] for c in block["columns"] if c in row} for row in printed]


def stored_documents(record, graph):
    """The copy of each stored document a revision of the record was derived from, and of the Turtle describing it."""
    documents = {d for revision in graph.subjects(REVISION_OF, record) for d in graph.objects(revision, DERIVED_FROM)}
    return {path for d in documents if (ALEX.pod / "attachments" / "sha-256" / stem(str(d))).is_file()
            for path in (f"pod/attachments/sha-256/{stem(str(d))}", "pod/" + fanned("provenance/documents", str(d)))}


def test_an_entrys_page_reaches_each_members_source_file_and_its_turtle_by_links_alone(pages):
    graph = ALEX.loaded("rdflib").graph()
    entries = {entry for path in VIEW_FILES.values()
               for entry in store.parsed(ALEX.pod / path, ALEX.address + path).subjects(MERGED_FROM, None)}
    unreached = []
    for path in VIEW_FILES.values():
        view = store.parsed(ALEX.pod / path, ALEX.address + path)
        for entry, member in view.subject_objects(MERGED_FROM):
            if page_of(member) not in pages[page_of(entry)].hrefs:
                unreached.append((str(entry), str(member)))
            elif not stored_documents(member, graph) <= set(pages[page_of(member)].hrefs):
                unreached.append((str(entry), str(member), "document"))
    assert entries and unreached == []
    assert stored_documents(name_of("H2F-ALG-PCN"), graph)


def test_an_entrys_page_puts_each_chosen_value_beside_the_member_it_came_from(pages):
    [shows] = [b for b in blocks(pages[page_of(PENICILLIN)]) if b["title"] == "What it shows"]
    allergen = "<https://ns.cascadeprotocol.org/health/v1#allergen>"
    assert [(row["value"]["value"], row["from"]["value"]) for row in shows["rows"]
            if row["field"]["value"] == allergen] == [('"Penicillin"', name_of("H2F-ALG-PCN").n3())]


def test_a_block_about_one_thing_says_its_command_prints_every_things_rows(pages):
    record = str(name_of("H2F-ALG-PCN"))
    [block] = [b for b in blocks(pages[page_of(record)]) if b["title"] == "Which judgments name it"]
    assert (f"It prints the rows for every record; this block keeps those whose ?record is {record}."
            in block["paras"])


def test_the_pipeline_page_asks_the_same_question_under_each_lens_side_by_side(pages):
    shown = {("--lens export" in b["command"], len(b["rows"])) for b in blocks(pages["pipeline.html"])
             if b["title"] == "My immunizations"}
    assert shown == {(False, 1), (True, 2)}


def test_a_turtle_link_opens_a_file_the_thing_arrived_in_and_a_thing_only_named_has_none(pages):
    [folders] = [b for b in blocks(pages["index.html"]) if b["title"] == "What each folder holds"]
    assert not [href for row in folders["rows"] if "type" in row for href in row["type"]["hrefs"]]
    profile = str(name_of("H1-PAT"))
    cells = [cell for page in pages.values() for block in blocks(page) for row in block["rows"] for cell in row.values()
             if cell["value"] == f"<{profile}>"]
    assert cells and not [href for cell in cells for href in cell["hrefs"] if href.startswith(site.COPY)]
