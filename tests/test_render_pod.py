import hashlib
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import pytest
from rdflib import URIRef

sys.path.insert(0, str(Path(__file__).absolute().parent))
from alex_rivera_builds import POD, ROOT, events, load_pod_file, name, pod  # noqa: E402

sys.path.insert(0, str(ROOT / "example-pods"))
import render  # noqa: E402

REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
REVISION_OF = URIRef(REC + "revisionOf")
HAD_MEMBER = URIRef("http://www.w3.org/ns/prov#hadMember")
VIEWS = {"allergies": "clinical/allergies.ttl", "conditions": "clinical/conditions.ttl",
         "immunizations": "clinical/immunizations.ttl", "procedures": "clinical/procedures.ttl",
         "patients": "clinical/patient-profile.ttl"}
PENICILLIN = ("H1-ALG-PCN", "H2F-ALG-PCN", "H2O-ALG-PCN")
SAM = ("H1P-ALG-AMOX", "H1P-CON-OTITIS", "H1P-CON-ECZEMA")


class Page(HTMLParser):
    """Each table row of a page, as cells of (text, hrefs), and every href on it."""

    def __init__(self, text):
        super().__init__()
        self.rows, self.hrefs, self._cell = [], [], None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.rows.append([])
        elif tag == "td":
            self._cell = ["", []]
        elif tag == "a":
            href = dict(attrs)["href"]
            self.hrefs.append(href)
            if self._cell is not None:
                self._cell[1].append(href)

    def handle_endtag(self, tag):
        if tag == "td":
            self.rows[-1].append((self._cell[0].strip(), self._cell[1]))
            self._cell = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell[0] += data


def page_of(term):
    return hashlib.sha256(str(term).encode("utf-8")).hexdigest() + ".html"


def read(site, relative):
    return Page((site / relative).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    render.render(POD, out)
    return out


def final():
    return pod(events()[-1]["event"])


def committed_entries(view):
    return set(load_pod_file(VIEWS[view]).subjects(MERGED_FROM, None))


def test_every_internal_link_resolves(site):
    broken = []
    for path in sorted(site.glob("*.html")):
        for href in read(site, path.name).hrefs:
            if not urlparse(href).scheme and not (site / href).is_file():
                broken.append((path.name, href))
    assert broken == []


def test_every_view_entry_every_record_and_every_judgment_naming_a_record_has_a_page(site):
    graph = final()
    entries = {entry for view in VIEWS for entry in committed_entries(view)}
    records = set(graph.objects(None, REVISION_OF))
    judgments = {j for j, m in graph.subject_objects(HAD_MEMBER) if m in records}
    assert entries and records and judgments
    missing = sorted(str(thing) for thing in entries | records | judgments if not (site / page_of(thing)).is_file())
    assert missing == []


def test_the_entry_counts_on_the_index_equal_the_committed_views(site):
    shown = {cells[0][1][0]: int(cells[1][0]) for cells in read(site, "index.html").rows
             if cells and cells[0][1] and cells[0][1][0].startswith("view-")}
    assert shown == {f"view-{view}.html": len(committed_entries(view)) for view in VIEWS}


def test_penicillins_entry_page_names_its_three_member_records(site):
    members = {name(handle) for handle in PENICILLIN}
    [entry] = [e for e in committed_entries("allergies")
               if set(load_pod_file(VIEWS["allergies"]).objects(e, MERGED_FROM)) == members]
    records = set(final().objects(None, REVISION_OF))
    linked = {href for href in read(site, page_of(entry)).hrefs if href in {page_of(r) for r in records}}
    assert linked == {page_of(m) for m in members}


def test_sams_records_and_the_erroneous_record_are_on_not_shown_with_their_reasons(site):
    reasons = {(cells[0][1][0], cells[1][0]) for cells in read(site, "not-shown.html").rows if cells}
    expected = {(page_of(name(handle)), "its patient profile has no counting About") for handle in SAM}
    expected.add((page_of(name("H1-PROC-ECHO")), "judged erroneous"))
    assert expected <= reasons


def test_a_second_render_gives_identical_bytes(site, tmp_path):
    render.render(POD, tmp_path)
    first = {p.relative_to(site).as_posix(): p.read_bytes() for p in site.rglob("*") if p.is_file()}
    second = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert first == second


def test_a_documents_bytes_are_copied_beside_the_record_that_names_it(site):
    copied = sorted(p.name for p in (site / "attachments" / "sha-256").iterdir())
    assert copied == sorted(p.name for p in (POD / "attachments" / "sha-256").iterdir())
    assert all((site / "attachments" / "sha-256" / c).read_bytes() ==
               (POD / "attachments" / "sha-256" / c).read_bytes() for c in copied)
