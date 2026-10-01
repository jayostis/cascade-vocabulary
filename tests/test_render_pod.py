import hashlib
import re
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


XSD = "http://www.w3.org/2001/XMLSchema#"
PREFIXES = """
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
@prefix jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix pav: <http://purl.org/pav/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix : <https://pod.example/> .
"""


def site_over(tmp_path, turtle):
    build = render.example_build(POD)
    store = build.Oxigraph()
    path = tmp_path / "pod.ttl"
    path.write_text(PREFIXES + turtle, encoding="utf-8")
    store.load(path, "https://pod.example/")
    pod = object.__new__(render.Pod)
    pod.folder, pod.build, pod.store, pod.labels, pod.views = tmp_path, build, store, {}, {}
    return render.Site(pod)


def facts_of(html_text):
    return re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", html_text)


def test_a_literal_is_shown_as_a_time_only_when_it_is_an_xsd_date_time(tmp_path):
    site = site_over(tmp_path, "")
    assert site.label(("literal", "Pneumonia Type B, unspecified", XSD + "string", None)) == \
        "Pneumonia Type B, unspecified"
    assert site.label(("literal", "2027-01-01T09:00:00Z", XSD + "dateTime", None)) == "2027-01-01 09:00 UTC"


def test_a_time_keeps_its_offset(tmp_path):
    assert render.when("2027-01-01T09:00:00+05:00") == "2027-01-01 09:00 +05:00"


def test_the_current_revision_is_the_one_that_arrived_last_whatever_the_offsets(tmp_path):
    site = site_over(tmp_path, """
        :early rec:revisionOf :record ; rec:version :v1 ; prov:generatedAtTime "2027-01-01T10:00:00+05:00"^^xsd:dateTime .
        :late rec:revisionOf :record ; rec:version :v2 ; prov:generatedAtTime "2027-01-01T06:00:00Z"^^xsd:dateTime .
    """)
    assert site.current["https://pod.example/record"]["revision"] == ("iri", "https://pod.example/late")


def test_values_that_differ_only_in_language_or_datatype_render(tmp_path):
    site = site_over(tmp_path, """
        :revision rec:revisionOf :record ; rec:version :version ; prov:generatedAtTime "2027-01-01T09:00:00Z"^^xsd:dateTime .
        :version :name "Penicillin"@en , "Penicillin" .
    """)
    names = [v for f, v in facts_of(site.record("https://pod.example/record", set()).decode("utf-8"))
             if f == "Its content"]
    assert names and names[0].count("Penicillin") == 2


def test_a_revision_derived_from_two_documents_arrives_once_with_each_document_beside_its_own_hospital(tmp_path):
    site = site_over(tmp_path, """
        :revision rec:revisionOf :record ; rec:version :version ; prov:generatedAtTime "2027-01-03T09:00:00Z"^^xsd:dateTime ;
            prov:wasDerivedFrom :doc-a , :doc-b .
        :doc-a pav:retrievedOn "2027-01-01T09:00:00Z"^^xsd:dateTime ;
            prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Hospital A" ] ] .
        :doc-b pav:retrievedOn "2027-01-02T09:00:00Z"^^xsd:dateTime ;
            prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Hospital B" ] ] .
    """)
    text = site.record("https://pod.example/record", set()).decode("utf-8")
    assert text.count("<h3>Arrived") == 1
    assert [f for f in facts_of(text) if f[0] in ("Document", "Hospital", "Retrieved")] == [
        ("Document", "doc-a"), ("Hospital", "Hospital A"), ("Retrieved", "2027-01-01 09:00 UTC"),
        ("Document", "doc-b"), ("Hospital", "Hospital B"), ("Retrieved", "2027-01-02 09:00 UTC")]


def test_a_profile_whose_records_come_from_two_hospitals_is_listed_once(tmp_path):
    site = site_over(tmp_path, """
        :about a jdg:Judgment ; rec:counts true ; jdg:verdict jdg:About ; prov:hadMember :profile ; jdg:subject :alex .
        :ra rec:version :va ; prov:wasDerivedFrom [ prov:qualifiedAttribution
            [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Hospital A" ] ] ] .
        :rb rec:version :vb ; prov:wasDerivedFrom [ prov:qualifiedAttribution
            [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Hospital B" ] ] ] .
        :va rec:patient :profile .
        :vb rec:patient :profile .
    """)
    rows = [cells for cells in Page(site.index().decode("utf-8")).rows
            if cells and cells[0][1] == [page_of("https://pod.example/profile")]]
    assert [cells[1][0] for cells in rows] == ["Hospital A, Hospital B"]
