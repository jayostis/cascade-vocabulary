import ast
import hashlib
import json
import re
import shlex
import subprocess
import sys
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import pytest
from rdflib import Literal, URIRef
from rdflib.namespace import XSD

from cascade_pod import graphdb, site, turtle, vocabulary
from cascade_pod.derived_files import LABEL_FILE, VIEW_FILES
from cascade_pod.pod import Example, fanned, save, stem
from examples import EXAMPLES, ROOT, pod_file
from test_library_graphdb import GraphDB
from test_queries import queries_held

MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
REVISION_OF = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#revisionOf")
DERIVED_FROM = URIRef("http://www.w3.org/ns/prov#wasDerivedFrom")


class Page(HTMLParser):
    """A page's links and ids, and each block on it: its title, its query's path and text, how to run it, and its rows
    as each shown column's term in N-Triples with the links in that cell."""

    def __init__(self, text):
        super().__init__()
        self.hrefs, self.ids, self.blocks = [], set(), []
        self._in, self._text, self._block, self._cell = [], "", None, None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._in.append(tag)
        self._text = ""
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "section":
            self._block = {"rows": [], "columns": [], "codes": [], "pres": [], "paras": []}
            self.blocks.append(self._block)
        elif tag == "a":
            self.hrefs.append(attrs["href"])
            if self._cell is not None:
                self._cell["hrefs"].append(attrs["href"])
        elif tag == "tr" and self._block is not None and "thead" not in self._in:
            self._block["rows"].append({})
        elif tag == "td":
            self._cell = {"label": attrs["data-label"][1:], "value": None, "hrefs": []}
        elif tag == "code" and "pre" in self._in:
            self._pre = ""
        elif tag == "p":
            self._para = ""
        elif tag == "data" and self._cell is not None:
            self._cell["value"] = attrs["value"]

    def handle_endtag(self, tag):
        text = self._text.strip()
        if self._block is not None:
            if tag == "h2" and "title" not in self._block:
                self._block["title"] = text
            elif tag == "th":
                self._block["columns"].append(text[1:])
            elif tag == "code":
                self._block["codes"].append(text)
            elif tag == "pre":
                self._block["pres"].append(self._pre)
            elif tag == "p":
                self._block["paras"].append(" ".join(self._para.split()))
            elif tag == "td":
                if self._cell["value"] is not None:
                    self._block["rows"][-1][self._cell["label"]] = self._cell
                self._cell = None
            elif tag == "section":
                self._block = None
        self._in.pop()

    def handle_data(self, data):
        self._text += data
        if self._in and self._in[-1] == "code" and "pre" in self._in:
            self._pre += data
        if "p" in self._in:
            self._para += data


SAVED = re.compile(r"Or in GraphDB, open the saved query (.+) in the repository ")


def blocks(page):
    for block in page.blocks:
        paths = [code for code in block["codes"] if code.startswith("queries/")]
        if paths:
            block["path"] = paths[0]
            commands = [pre for pre in block["pres"] if pre.startswith("python -m cascade_pod ask")]
            block["command"] = commands[0] if commands else None
            saved = [m.group(1) for para in block["paras"] for m in [SAVED.match(para)] if m]
            block["saved"] = saved[0] if saved else None
            yield block


def page_of(iri):
    return hashlib.sha256(str(iri).encode("utf-8")).hexdigest() + ".html"


@lru_cache(maxsize=None)
def site_files(example):
    return site.Site(example).files()


@lru_cache(maxsize=None)
def site_pages(example):
    return {path: Page(octets.decode("utf-8")) for path, octets in sorted(site_files(example).items())
            if path.endswith(".html") and "/" not in path}


@pytest.fixture(scope="module", params=EXAMPLES, ids=lambda example: example.name)
def example(request):
    return request.param


@pytest.fixture(scope="module")
def built(example, tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    save(site_files(example), out)
    return out


@pytest.fixture(scope="module")
def pages(example):
    return site_pages(example)


def test_every_question_has_a_place_on_the_site(pages):
    shown = {block["path"] for page in pages.values() for block in blocks(page)}
    expected = {vocabulary.QUERIES.relative_to(ROOT).as_posix() + "/" + relative for relative in vocabulary.questions().values()}
    assert expected - shown == set()


def test_every_block_shows_its_querys_text_and_its_path(pages):
    found = [block for page in pages.values() for block in page.blocks]
    assert found and all("path" in block for page in pages.values() for block in blocks(page))
    assert len(found) == sum(1 for page in pages.values() for _ in blocks(page))
    for page in pages.values():
        for block in blocks(page):
            assert block["pres"][0] == (ROOT / block["path"]).read_text(encoding="utf-8"), block["path"]


def test_the_names_graphdb_saves_the_questions_under_are_the_names_the_site_prints(example, pages):
    server = GraphDB()
    try:
        graphdb.load(example, server.url)
    finally:
        server.server.shutdown()
    printed = {block["saved"] for page in pages.values() for block in blocks(page) if block["saved"]}
    assert printed == set(server.saved)


def entries_and_members(example, views=tuple(VIEW_FILES)):
    return sorted((entry, member) for view in views
                  for entry, member in pod_file(example, VIEW_FILES[view]).subject_objects(MERGED_FROM))


def asked(command):
    arguments = shlex.split(command)
    result = subprocess.run([sys.executable, *arguments[1:]], capture_output=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    return [dict(cell[1:].split("=", 1) for cell in line.split("\t"))
            for line in result.stdout.decode("utf-8").splitlines()]


def samples(example):
    [(entry, _), *_] = entries_and_members(example)
    return [("index.html", "What each folder holds", None), ("index.html", "How many of each kind", None),
            ("index.html", "What each import brought in", None), ("not-shown.html", "Why it is in no view", None),
            (page_of(entry), "Where it came from", entry)]


@pytest.mark.parametrize("example, page, title, thing", [(e, *s) for e in EXAMPLES for s in samples(e)],
                         ids=[f"{e.name}-{s[0]}-{s[1]}" for e in EXAMPLES for s in samples(e)])
def test_every_run_it_yourself_command_prints_the_rows_the_block_shows(example, page, title, thing):
    [block] = [b for b in blocks(site_pages(example)[page]) if b["title"] == title]
    printed = asked(block["command"])
    about = [code[1:] for code in block["codes"] if code.startswith("?")]
    if about:
        printed = [row for row in printed if row.get(about[0]) == f"<{thing}>"]
    shown = [{column: cell["value"] for column, cell in row.items()} for row in block["rows"]]
    assert shown == [{c: row[c] for c in block["columns"] if c in row} for row in printed]


def stored_documents(example, record, graph):
    """The copy of each stored document a revision of the record was derived from, and of the Turtle describing it."""
    documents = {d for revision in graph.subjects(REVISION_OF, record) for d in graph.objects(revision, DERIVED_FROM)}
    return {path for d in documents if (example.pod / "attachments" / "sha-256" / stem(str(d))).is_file()
            for path in (f"pod/attachments/sha-256/{stem(str(d))}", "pod/" + fanned("provenance/documents", str(d)))}


def test_an_entrys_page_reaches_each_members_source_file_and_its_turtle_by_links_alone(example, pages):
    graph = example.loaded("rdflib").graph()
    walked = entries_and_members(example)
    unreached = []
    for entry, member in walked:
        if page_of(member) not in pages[page_of(entry)].hrefs:
            unreached.append((str(entry), str(member)))
        elif not stored_documents(example, member, graph) <= set(pages[page_of(member)].hrefs):
            unreached.append((str(entry), str(member), "document"))
    assert walked and unreached == []
    assert any(stored_documents(example, member, graph) for _, member in walked)


def test_a_block_about_one_thing_says_its_command_prints_every_things_rows(example, pages):
    for record in {member for _, member in entries_and_members(example, set(VIEW_FILES) - {"patients"})}:
        [block] = [b for b in blocks(pages[page_of(record)]) if b["title"] == "Which judgments name it"]
        assert (f"It prints the rows for every record; this block keeps those whose ?record is {record}."
                in block["paras"])


def thing_pages(pages):
    return [name for name in pages if re.fullmatch(r"[0-9a-f]{64}\.html", name)]


def test_every_things_page_names_the_pod_file_that_states_it_and_links_to_its_turtle(example, pages, built):
    assert thing_pages(pages)
    for name in thing_pages(pages):
        [stated] = [b for b in blocks(pages[name]) if b["title"] == "Which file states each thing"]
        files = [row["file"]["hrefs"][0] for row in stated["rows"]]
        assert files and all(href.startswith(site.COPY) for href in files), name
        assert all((built / href).read_bytes() == (example.pod / href[len(site.COPY):]).read_bytes() for href in files), name


def test_every_internal_link_resolves(pages, built):
    broken = []
    for name, page in pages.items():
        for href in page.hrefs:
            link = urlparse(href)
            if link.scheme:
                continue
            target = link.path or name
            if not (built / target).is_file() or (link.fragment and link.fragment not in pages[target].ids):
                broken.append((name, href))
    assert broken == []


def test_a_second_build_gives_identical_bytes(example, built, tmp_path):
    save(site.Site(example).files(), tmp_path)
    first = {p.relative_to(built).as_posix(): p.read_bytes() for p in built.rglob("*") if p.is_file()}
    second = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert first == second


def test_the_site_copies_every_pod_file_and_the_stylesheet(example, built):
    assert (built / site.STYLESHEET).is_file()
    for path in example.files() + example.derived:
        assert (built / site.COPY / path).read_bytes() == (example.pod / path).read_bytes(), path


def markup(source):
    return [node.value for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and TAG.search(node.value)]


TAG = re.compile(r"<\s*/?\s*[A-Za-z!][^>]*>")


def test_the_markup_check_finds_a_tag_in_a_string():
    assert markup('ROW = "<tr><td>" + cell') == ["<tr><td>"]


def test_the_site_script_holds_no_markup_and_no_query():
    source = Path(site.__file__).read_text(encoding="utf-8")
    assert markup(source) == [] and queries_held(source) == []


def test_a_time_is_shown_in_utc_whatever_its_offset():
    assert site.shown(Literal("2027-01-01T09:00:00+05:00", datatype=XSD.dateTime)) == "2027-01-01 04:00 UTC"
    assert site.shown(Literal("2027-01-01T09:00:00", datatype=XSD.dateTime)) == "2027-01-01 09:00 UTC"


def test_a_literal_is_shown_as_a_time_only_when_it_is_an_xsd_date_time():
    assert site.shown(Literal("2027-01-01", datatype=XSD.date)) == "2027-01-01"
    assert site.shown(Literal("2027-01-01T09:00:00Z")) == "2027-01-01T09:00:00Z"


TINY = """
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#> .
@prefix pav: <http://purl.org/pav/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix : <urn:x:> .
:record a health:AllergyRecord .
"""


def tiny(tmp_path, turtle_text, thing="urn:x:record"):
    """The blocks on the thing's page, in the site of a pod built from the owner's profile and these statements."""
    folder = tmp_path / "tiny"
    files = {"profile/card.ttl": "<#me> <http://www.w3.org/ns/pim/space#storage> </> .\n", "data.ttl": TINY + turtle_text}
    for path, text in files.items():
        (folder / "pod" / path).parent.mkdir(parents=True, exist_ok=True)
        (folder / "pod" / path).write_text(text, encoding="utf-8")
    derived = [*VIEW_FILES.values(), LABEL_FILE, "index.ttl", "manifest.ttl"]
    story = {"address": "https://pod.example/", "derived": derived,
             "events": [{"event": "E1", "at": "2027-01-01T00:00:00Z", "adds": sorted(files)}]}
    (folder / "events.json").write_text(json.dumps(story), encoding="utf-8")
    (folder / "ro-crate-metadata.json").write_text(json.dumps({"@graph": [{"@id": "./", "name": "Tiny"}]}), encoding="utf-8")
    example = Example(folder)
    save(example.derived_turtle("oxigraph"), example.pod)
    built = site.Site(example).files()
    save(built, folder / "site")
    return {block["title"]: block for block in blocks(Page(built[page_of(thing)].decode("utf-8")))}


def column(block, name):
    return [row[name]["value"] if name in row else None for row in block["rows"]]


def test_judgments_are_listed_in_the_order_they_were_made_whatever_the_offsets(tmp_path):
    record = tiny(tmp_path, """
        :late a jdg:Judgment ; prov:hadMember :record ; prov:generatedAtTime "2027-01-01T06:00:00Z"^^xsd:dateTime .
        :early a jdg:Judgment ; prov:hadMember :record ; prov:generatedAtTime "2027-01-01T10:00:00+05:00"^^xsd:dateTime .
    """)
    assert column(record["Which judgments name it"], "judgment") == ["<urn:x:early>", "<urn:x:late>"]


def test_the_current_revision_is_the_one_that_arrived_last_whatever_the_offsets(tmp_path):
    record = tiny(tmp_path, """
        :late rec:revisionOf :record ; rec:version :v2 ; prov:generatedAtTime "2027-01-01T06:00:00Z"^^xsd:dateTime .
        :early rec:revisionOf :record ; rec:version :v1 ; prov:generatedAtTime "2027-01-01T10:00:00+05:00"^^xsd:dateTime .
    """)
    revisions = record["Its revisions, in the order they arrived"]
    assert list(zip(column(revisions, "revision"), column(revisions, "current"))) == [
        ("<urn:x:early>", turtle.term(Literal(False))), ("<urn:x:late>", turtle.term(Literal(True)))]


def test_values_that_differ_only_in_language_or_datatype_are_both_shown(tmp_path):
    record = tiny(tmp_path, """
        :revision rec:revisionOf :record ; rec:version :version ; prov:generatedAtTime "2027-01-01T09:00:00Z"^^xsd:dateTime .
        :version :name "Penicillin"@en , "Penicillin" .
    """)
    said = record["What each version says"]
    assert sorted(v for f, v in zip(column(said, "field"), column(said, "value")) if f == "<urn:x:name>") == [
        '"Penicillin"', '"Penicillin"@en']


def test_a_revision_derived_from_two_documents_shows_each_document_beside_its_own_hospital(tmp_path):
    record = tiny(tmp_path, """
        :revision rec:revisionOf :record ; rec:version :version ; prov:generatedAtTime "2027-01-03T09:00:00Z"^^xsd:dateTime ;
            prov:wasDerivedFrom :doc-a , :doc-b .
        :doc-a pav:retrievedOn "2027-01-01T09:00:00Z"^^xsd:dateTime ;
            prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Hospital A" ] ] .
        :doc-b pav:retrievedOn "2027-01-02T09:00:00Z"^^xsd:dateTime ;
            prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Hospital B" ] ] .
    """)
    revisions = record["Its revisions, in the order they arrived"]
    assert list(zip(column(revisions, "document"), column(revisions, "hospital"))) == [
        ("<urn:x:doc-a>", '"Hospital A"'), ("<urn:x:doc-b>", '"Hospital B"')]


def test_a_thing_only_ever_named_by_others_is_stated_by_the_files_that_name_it(tmp_path):
    profile = tiny(tmp_path, """
        :revision rec:revisionOf :record ; rec:version :version ; prov:generatedAtTime "2027-01-01T09:00:00Z"^^xsd:dateTime .
        :version rec:patient :profile .
    """, "urn:x:profile")
    stated = profile["Which file states each thing"]
    assert ("<https://pod.example/data.ttl>", '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>') in list(
        zip(column(stated, "file"), column(stated, "named")))


def test_the_folder_table_names_a_records_folders_untyped_versions_and_leaves_out_the_labels_file(pages):
    [folders] = [b for b in blocks(pages["index.html"]) if b["title"] == "What each folder holds"]
    rows = {(row["folder"]["value"], row["type"]["value"]) for row in folders["rows"]}
    assert ('"/records/allergies/"', '"no type stated"') in rows
    assert not {row for row in rows if row[0] == '"/clinical/"' and not row[1].startswith("<")}


def test_no_template_and_not_the_stylesheet_holds_an_iri():
    found = {path.name: re.findall(r"\w+://[^\s\"'<>]+", path.read_text(encoding="utf-8"))
             for path in [*(site.HERE / "templates").glob("*.html"), site.HERE / site.STYLESHEET]}
    assert {name: iris for name, iris in found.items() if iris} == {}


def test_no_things_page_shows_what_everything_is_called_and_the_pipeline_page_does(pages):
    titles = {name: {b["title"] for b in blocks(page)} for name, page in pages.items()}
    assert not [name for name in thing_pages(pages) if "What everything is called" in titles[name]]
    assert "What everything is called" in titles["pipeline.html"]


def test_text_from_the_pod_is_escaped_wherever_the_site_shows_it(tmp_path):
    label = '<script>alert(1)</script> " onmouseover="x'
    folder = tmp_path / "tiny"
    tiny(tmp_path, f"""
        :revision rec:revisionOf :record ; rec:version :version ; prov:generatedAtTime "2027-01-01T09:00:00Z"^^xsd:dateTime .
        :version :said "a \\"quoted\\" <b>bold</b> & x" .
        :record rdfs:label "{label.replace('"', '\\"')}" .
    """)
    text = (folder / "site" / page_of("urn:x:record")).read_text(encoding="utf-8")
    assert "<script>" not in text and "<b>" not in text and 'onmouseover="x' not in text
    assert "&lt;script&gt;" in text and "&lt;b&gt;bold&lt;/b&gt;" in text


def test_a_block_asked_under_the_other_lens_links_to_no_page_of_this_site(pages):
    other = [b for b in blocks(pages["pipeline.html"]) if b["command"] and "--lens" in b["command"]]
    assert other and not [href for b in other for row in b["rows"] for cell in row.values() for href in cell["hrefs"]
                          if href.endswith(".html")]
