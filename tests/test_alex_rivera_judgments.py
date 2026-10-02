import json
import subprocess
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, URIRef

ROOT = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import recomputed  # noqa: E402
from alex_rivera_builds import EVERY_JUDGMENT, handles  # noqa: E402
from cascade_pod import store  # noqa: E402

EXAMPLE = ROOT / "example-pods" / "alex-rivera"
POD = EXAMPLE / "pod"
POD_BASE = "https://pod.alex-rivera.example/"

JDG = "https://ns.cascadeprotocol.org/judgments/v1-draft#"
NPX = "http://purl.org/nanopub/x/"
PROV = "http://www.w3.org/ns/prov#"
REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
DESCRIPTION = URIRef("http://purl.org/dc/terms/description")
MATCHER = "urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76"
ALEX = "https://pod.alex-rivera.example/profile/card.ttl#me"

RUNS = [
    ("E2", "E2", "2026-09-01T10:00:04Z", None),
    ("E3", "E3", "2026-09-01T18:30:00Z", None),
    ("E4", "E4", "2026-10-14T15:43:00Z", "E5"),
    ("E6", "E6", "2026-11-20T09:00:04Z", None),
    ("E9", None, "2027-01-15T06:00:00Z", None),
    ("E10", "E10", "2027-02-10T17:21:00Z", None),
    ("E12", "E12", "2027-03-18T12:01:00Z", "E13"),
    ("E15", "E15", "2027-08-20T08:00:04Z", None),
]

EVERY_REFERENCE = {
    "RS-RULES": "E5", "RS-RULES-2026.1": "E5", "RS-XWALK": "E5", "RS-XWALK-2026-09": "E5",
    "RS-XWALK-2027-01": "E9", "RS-CVXG": "E13", "RS-CVXG-2026-08": "E13",
}


def manifest():
    return json.loads((EXAMPLE / "events.json").read_text(encoding="utf-8"))


def added_by():
    return {path: event["event"] for event in manifest()["events"] for path in event["adds"]}


def load(relative):
    return Graph().parse(POD / relative, format="turtle", publicID=POD_BASE + relative)


def listed(*folders):
    return sorted(p for p in added_by() if p.startswith(folders))


def path_of(folder, name):
    stem = name[len("urn:uuid:"):]
    return f"{folder}/{stem[:2]}/{stem}.ttl"


def judgments():
    found = {}
    for relative in listed("judgments/"):
        graph = load(relative)
        [judgment] = graph.subjects(RDF_TYPE, URIRef(JDG + "Judgment"))
        found[str(judgment)] = (relative, graph)
    return found


def through(event, *folders):
    events = [e["event"] for e in manifest()["events"]]
    graph = Graph()
    for e in manifest()["events"][: events.index(event) + 1]:
        for relative in e["adds"]:
            if relative.startswith(folders):
                graph += load(relative)
    return graph


def current_version(graph, record):
    revisions = set(graph.subjects(URIRef(REC + "revisionOf"), URIRef(record)))
    followed = {o for r in revisions for o in graph.objects(r, URIRef(PROV + "wasRevisionOf"))}
    [latest] = revisions - followed
    return str(graph.value(latest, URIRef(REC + "version")))


def test_every_judgment_and_reference_file_is_named_for_its_one_thing_and_listed_under_the_scenarios_event():
    names = {h: str(term) for h, term in handles().items()}
    expected = {path_of("judgments", names[j]): row[0] for j, row in EVERY_JUDGMENT.items()}
    expected |= {path_of("references", names[r]): event for r, event in EVERY_REFERENCE.items()}
    assert {p: e for p, e in added_by().items() if p.startswith(("judgments/", "references/"))} == expected
    on_disk = sorted(p.relative_to(POD).as_posix() for folder in ("judgments", "references")
                     for p in (POD / folder).rglob("*") if p.is_file())
    assert on_disk == sorted(expected)


def test_every_judgment_and_reference_conforms_to_the_judgments_and_records_shapes():
    shapes = Graph()
    for vocabulary in ("judgments", "records"):
        shapes.parse(ROOT / "ontologies" / vocabulary / "v1-draft" / f"{vocabulary}.shapes.ttl", format="turtle")
    data = Graph()
    for relative in listed("judgments/", "references/"):
        data += load(relative)
    conforms, _, report = validate(data, shacl_graph=shapes, advanced=True)
    store.keep_literals_as_written()
    assert conforms, report
    assert len(set(data.subjects(RDF_TYPE, URIRef(JDG + "Judgment")))) == len(EVERY_JUDGMENT)
    assert len(set(data.subjects(RDF_TYPE, URIRef(REC + "ReferenceSeries")))) == 3


def test_the_judgments_are_the_scenarios_author_verdict_members_justification_used_and_time_by_handle():
    names = {h: str(term) for h, term in handles().items()}
    found = judgments()
    assert sorted(found) == sorted(names[j] for j in EVERY_JUDGMENT)
    for j, (event, at, author, verdict, members, justification, used, replaces, reason) in EVERY_JUDGMENT.items():
        relative, graph = found[names[j]]
        judgment = URIRef(names[j])

        def values(predicate):
            return sorted(str(o) for o in graph.objects(judgment, URIRef(predicate)))

        assert added_by()[relative] == event, j
        assert f'prov:generatedAtTime "{at}"^^xsd:dateTime' in (POD / relative).read_text(encoding="utf-8"), j
        assert len(values(PROV + "generatedAtTime")) == 1, j
        assert values(PROV + "wasAttributedTo") == [ALEX if author == "Alex" else MATCHER], j
        kind = "Person" if author == "Alex" else "SoftwareAgent"
        assert (URIRef(values(PROV + "wasAttributedTo")[0]), RDF_TYPE, URIRef(PROV + kind)) in graph, j
        assert values(JDG + "verdict") == ([JDG + verdict] if verdict else []), j
        assert values(PROV + "hadMember") == sorted(names[m] for m in members), j
        assert values(JDG + "justification") == ([JDG + justification] if justification else []), j
        assert values(PROV + "used") == sorted(names[u] for u in used), j
        for kind in ("supersedes", "retracts"):
            assert values(NPX + kind) == sorted(names[t] for k, t in replaces if k == kind), j
        assert (graph.value(judgment, DESCRIPTION) is not None) == reason, j
        if verdict == "About":
            assert values(JDG + "subject") == [names["S"]], j
            assert values(JDG + "basis") == [JDG + "OwnerStatement"], j


def test_each_matcher_judgment_names_the_rule_set_the_table_its_rule_applied_and_each_members_current_version():
    names = {h: str(term) for h, term in handles().items()}
    tables = {"SameCode": [], "SameCodeAndDate": [], "SameMappedCode": [names["RS-XWALK-2026-09"]],
              "SameMappedCodeAndDate": [names["RS-CVXG-2026-08"]]}
    for name, (relative, graph) in judgments().items():
        judgment = URIRef(name)
        if str(graph.value(judgment, URIRef(PROV + "wasAttributedTo"))) != MATCHER:
            continue
        records = through(added_by()[relative], "records/")
        justification = str(graph.value(judgment, URIRef(JDG + "justification")))[len(JDG):]
        members = sorted(str(m) for m in graph.objects(judgment, URIRef(PROV + "hadMember")))
        used = sorted(str(u) for u in graph.objects(judgment, URIRef(PROV + "used")))
        assert used == sorted([names["RS-RULES-2026.1"], *tables[justification],
                               *(current_version(records, m) for m in members)]), relative
        assert name == recomputed.record_name([MATCHER, JDG + justification, *members, *used]), relative


def test_the_matcher_reproduces_every_file_it_wrote_and_writes_nothing_on_its_other_runs(tmp_path):
    for read_through, takes, at, event in RUNS:
        out = tmp_path / read_through
        command = [sys.executable, "-m", "cascade_pod", "match", str(EXAMPLE),
                   "--read-through", read_through, "--at", at, "--out", str(out)]
        result = subprocess.run(command + (["--takes", takes] if takes else []), capture_output=True, text=True,
                                cwd=ROOT)
        assert result.returncode == 0, result.stderr
        written = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
        expected = [p for p, e in sorted(added_by().items()) if e == event]
        assert written == expected, read_through
        for relative in written:
            assert (out / relative).read_bytes() == (POD / relative).read_bytes(), relative
