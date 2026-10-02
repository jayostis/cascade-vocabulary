import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from cascade_pod import derive, derived_files, store, vocabulary
from cascade_pod.derived_files import VIEW_FILES
from cascade_pod.pod import NOT_RDF, Example

sys.path.insert(0, str(Path(__file__).absolute().parent))
import recomputed  # noqa: E402

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
ALEX = Example(EXAMPLE)
POD = ALEX.pod
EXPECTED = EXAMPLE / "expected"
POD_BASE = ALEX.address
HANDLE_NS = "urn:example:alex-rivera:handle:"

ENGINES = ("oxigraph", "rdflib")
LENSES = ("everyday", "export")

MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
IN_ENTRY = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#inEntry")
REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
NPX = Namespace("http://purl.org/nanopub/x/")
PROV = Namespace("http://www.w3.org/ns/prov#")
AUTHORS = {"Alex": URIRef(POD_BASE + "profile/card.ttl#me"),
           "matcher": URIRef("urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76")}

# J: event, time, author, verdict, members, justification, used, supersedes or retracts, a reason given
EVERY_JUDGMENT = {
    "J1": ("E2", "2026-09-01T10:00:30Z", "Alex", "About", ["H1-PAT"], None, [], [], False),
    "J2": ("E4", "2026-10-14T15:42:30Z", "Alex", "About", ["H2O-PAT"], None, [], [], False),
    "J3": ("E5", "2026-10-14T15:43:00Z", "matcher", "Same", ["H1-ALG-SULFA", "H2O-ALG-SULFA"], "SameCode",
           ["RS-RULES-2026.1", "H1-ALG-SULFA v1", "H2O-ALG-SULFA v1"], [], False),
    "J4": ("E5", "2026-10-14T15:43:00Z", "matcher", "Same", ["H1-ALG-PCN", "H2O-ALG-PCN"], "SameMappedCode",
           ["RS-RULES-2026.1", "RS-XWALK-2026-09", "H1-ALG-PCN v1", "H2O-ALG-PCN v1"], [], False),
    "J5": ("E5", "2026-10-14T15:43:00Z", "matcher", "Same", ["H1-CON-HTN", "H2O-CON-HTN"], "SameCode",
           ["RS-RULES-2026.1", "H1-CON-HTN v1", "H2O-CON-HTN v1"], [], False),
    "J6": ("E5", "2026-10-14T15:43:00Z", "matcher", "Same", ["H1-IMM-FLU25", "H2O-IMM-FLU25"], "SameCodeAndDate",
           ["RS-RULES-2026.1", "H1-IMM-FLU25 v1", "H2O-IMM-FLU25 v1"], [], False),
    "J7": ("E5", "2026-10-14T15:43:00Z", "matcher", "Same", ["H1-PROC-COLO", "H2O-PROC-COLO"], "SameCode",
           ["RS-RULES-2026.1", "H1-PROC-COLO v1", "H2O-PROC-COLO v1"], [], False),
    "J8": ("E8", "2026-12-02T19:00:00Z", "Alex", "Different", ["H1-PROC-COLO", "H2O-PROC-COLO"], None,
           ["H1-PROC-COLO v1", "H2O-PROC-COLO v1"], [], True),
    "J9": ("E8", "2026-12-02T19:00:00Z", "Alex", "Same", ["H1-ALG-SULFA", "H2O-ALG-SULFA"], None,
           ["H1-ALG-SULFA v2", "H2O-ALG-SULFA v1"], [("supersedes", "J3")], False),
    "J10": ("E8", "2026-12-02T19:00:00Z", "Alex", "Same", ["H1-CON-BRONCH", "H2O-CON-ASTHMA"], None,
            ["H1-CON-BRONCH v2", "H2O-CON-ASTHMA v1"], [], True),
    "J12": ("E12", "2027-03-18T12:00:30Z", "Alex", "About", ["H2F-PAT"], None, [], [], False),
    "J13": ("E13", "2027-03-18T12:01:00Z", "matcher", "Same", ["H1-ALG-SULFA", "H2O-ALG-SULFA", "H2F-ALG-SULFA"],
            "SameCode", ["RS-RULES-2026.1", "H1-ALG-SULFA v2", "H2O-ALG-SULFA v1", "H2F-ALG-SULFA v1"], [], False),
    "J14": ("E13", "2027-03-18T12:01:00Z", "matcher", "Same", ["H2O-ALG-PCN", "H2F-ALG-PCN"], "SameCode",
            ["RS-RULES-2026.1", "H2O-ALG-PCN v1", "H2F-ALG-PCN v1"], [], False),
    "J15": ("E13", "2027-03-18T12:01:00Z", "matcher", "Same", ["H1-CON-HTN", "H2O-CON-HTN", "H2F-CON-HTN"],
            "SameCode", ["RS-RULES-2026.1", "H1-CON-HTN v1", "H2O-CON-HTN v1", "H2F-CON-HTN v1"], [], False),
    "J16": ("E13", "2027-03-18T12:01:00Z", "matcher", "Same", ["H2O-CON-ASTHMA", "H2F-CON-ASTHMA"], "SameCode",
            ["RS-RULES-2026.1", "H2O-CON-ASTHMA v1", "H2F-CON-ASTHMA v1"], [], False),
    "J17": ("E13", "2027-03-18T12:01:00Z", "matcher", "Same", ["H1-IMM-FLU25", "H2O-IMM-FLU25", "H2F-IMM-FLU25"],
            "SameMappedCodeAndDate",
            ["RS-RULES-2026.1", "RS-CVXG-2026-08", "H1-IMM-FLU25 v1", "H2O-IMM-FLU25 v1", "H2F-IMM-FLU25 v1"],
            [], False),
    "J18": ("E13", "2027-03-18T12:01:00Z", "matcher", "Same", ["H1-PROC-COLO", "H2O-PROC-COLO", "H2F-PROC-COLO"],
            "SameCode", ["RS-RULES-2026.1", "H1-PROC-COLO v1", "H2O-PROC-COLO v1", "H2F-PROC-COLO v1"], [], False),
    "J19": ("E14", "2027-04-02T20:00:00Z", "Alex", "Different", ["H1-PROC-COLO", "H2F-PROC-COLO"], None,
            ["H1-PROC-COLO v1", "H2F-PROC-COLO v1"], [], False),
    "J20": ("E14", "2027-04-02T20:00:00Z", "Alex", None, [], None, [], [("retracts", "J10")], True),
    "J21": ("E14", "2027-04-02T20:00:00Z", "Alex", "Same", ["H1-ALG-PCN", "H2O-ALG-PCN", "H2F-ALG-PCN"], None,
            ["H1-ALG-PCN v1", "H2O-ALG-PCN v1", "H2F-ALG-PCN v1"], [], False),
    "J22": ("E10", "2027-02-10T17:21:30Z", "Alex", "About", ["H1P-PAT"], None, [], [], False),
    "J23": ("E14", "2027-04-02T20:00:00Z", "Alex", None, [], None, [], [("retracts", "J22")], True),
    "J24": ("E14", "2027-04-02T20:00:00Z", "Alex", "Erroneous", ["H1-PROC-ECHO"], None, ["H1-PROC-ECHO v1"], [], True),
}


@lru_cache(maxsize=None)
def sources():
    return json.loads((EXPECTED / "handles.json").read_text(encoding="utf-8"))


def source_name(row):
    if "server" in row:
        return URIRef(recomputed.record_name([row["server"], row["type"], row["id"]]))
    if "download" in row:
        return URIRef(recomputed.record_name([recomputed.ni_name((EXAMPLE / row["download"]).read_bytes()), ""]))
    [activity] = store.parsed(EXAMPLE / row["entry"]).subjects(RDF.type, PROV.Activity)
    return URIRef(recomputed.record_name([str(activity), str(row["position"])]))


def arrivals(graph, record):
    return sorted(graph.subjects(REC.revisionOf, record), key=lambda r: str(graph.value(r, PROV.generatedAtTime)))


def _judgment(graph, handle, named):
    _, at, author, verdict, members, _, _, replaces, _ = EVERY_JUDGMENT[handle]

    def is_it(judgment):
        return (str(graph.value(judgment, PROV.generatedAtTime)) == at
                and graph.value(judgment, PROV.wasAttributedTo) == AUTHORS[author]
                and graph.value(judgment, JDG.verdict) == (JDG[verdict] if verdict else None)
                and set(graph.objects(judgment, PROV.hadMember)) == {named[m] for m in members}
                and {(p, o) for p in (NPX.supersedes, NPX.retracts) for o in graph.objects(judgment, p)}
                == {(NPX[kind], named[target]) for kind, target in replaces})

    found = [j for j in graph.subjects(RDF.type, JDG.Judgment) if is_it(j)]
    if len(found) != 1:
        pytest.fail(f"{handle} is {len(found)} judgments of the pod, not one")
    return found[0]


@lru_cache(maxsize=None)
def handles():
    graph = final_pod()
    named = {h: source_name(row) for kind in ("records", "profiles") for h, row in sources()[kind].items()}
    for h in sources()["records"]:
        versions = []
        for n, revision in enumerate(arrivals(graph, named[h]), 1):
            named[f"{h} r{n}"] = revision
            if (revision, PROV.wasDerivedFrom, None) in graph:
                named[f"D-{h} r{n}"] = graph.value(revision, PROV.wasDerivedFrom)
            if graph.value(revision, REC.version) not in versions:
                versions.append(graph.value(revision, REC.version))
                named[f"{h} v{len(versions)}"] = versions[-1]
    references = json.loads((EXAMPLE / "references" / "references.json").read_text(encoding="utf-8"))["series"]
    for h, key in sources()["series"].items():
        [series] = [s for s in references if s["key"] == key]
        named[h] = URIRef(series["name"])
        named |= {f"{h}-{v['version']}": URIRef(v["name"]) for v in series["versions"]}
    named |= {f"I-{e['event']}": URIRef(e["import"]) for e in events() if "import" in e}
    named |= {"S": URIRef(e["subject"]) for e in events() if "subject" in e}
    for h in EVERY_JUDGMENT:
        named[h] = _judgment(graph, h, named)
    return named


@lru_cache(maxsize=None)
def _handles_by_name():
    return {str(term): handle for handle, term in handles().items()}


def name(handle):
    term = handles().get(handle)
    if term is None:
        pytest.fail(f"handle {handle} names nothing in the pod")
    return term


def handle(term):
    found = _handles_by_name().get(str(term))
    if found is None:
        pytest.fail(f"{term} has no handle")
    return found


def events():
    return ALEX.events


def adds(event):
    for row in events():
        if row["event"] == event:
            return row["adds"]
    pytest.fail(f"events.json lists no event {event}")


def files_through(event):
    return tuple(ALEX.files(event))


def is_rdf(relative):
    return not relative.startswith(NOT_RDF)


def load_pod_file(relative):
    return store.parsed(POD / relative, POD_BASE + relative)


def graph(triples):
    found = Graph()
    for triple in triples:
        found.add(triple)
    return found


@lru_cache(maxsize=None)
def pod(event):
    engine = store.Rdflib()
    ALEX.load(engine, event)
    return engine.graph()


def final_pod():
    return pod(events()[-1]["event"])


def _string_typed(term):
    if isinstance(term, Literal) and term.datatype is None and term.language is None:
        return Literal(str(term), datatype=XSD.string)
    return term


@dataclass(frozen=True)
class Build:
    state: Graph
    views: dict
    needs_review: dict


@lru_cache(maxsize=None)
def build(engine, lens, event):
    held = ALEX.loaded(engine, event)
    derive.derive(held, lens)
    state = graph(held.triples())
    files = derived_files.add(ALEX, held, event)
    needs_review = {kind: held.select(vocabulary.query(vocabulary.questions()[f"{kind}/What needs review"]))
                    for kind in ("entry", "judgment")}
    views = {view: graph(files[path]) for view, path in VIEW_FILES.items()}
    return Build(state, views, needs_review)


def comparable(term):
    if isinstance(term, BNode):
        pytest.fail(f"a view names a blank node, {term}, as an object")
    if isinstance(term, URIRef):
        found = _handles_by_name().get(str(term))
        return URIRef(HANDLE_NS + found) if found is not None else term
    return _string_typed(term)


def _member_handle(term):
    if str(term).startswith(HANDLE_NS):
        return str(term)[len(HANDLE_NS):]
    found = _handles_by_name().get(str(term))
    if found is None:
        pytest.fail(f"entry member {term} has no handle")
    return found


def entries(graph):
    found = {}
    for subject in set(graph.subjects(MERGED_FROM, None)):
        members = frozenset(_member_handle(m) for m in graph.objects(subject, MERGED_FROM))
        if members in found:
            pytest.fail(f"two entries have the members {sorted(members)}")
        found[members] = {(p, comparable(o)) for p, o in graph.predicate_objects(subject)}
    return found


def values(pairs, predicate):
    return {o for p, o in pairs if p == predicate}


def members_shown(build):
    return {member for graph in build.views.values() for key in entries(graph) for member in key}


def entry_holding(build, view, member):
    held = [key for key in entries(build.views[view]) if member in key]
    assert len(held) == 1, f"{member} is in {len(held)} entries of the {view} view"
    return held[0]


def entry_members(build, entry):
    members = set(build.state.subjects(IN_ENTRY, entry))
    for graph in build.views.values():
        members.update(graph.objects(entry, MERGED_FROM))
    return frozenset(_member_handle(m) for m in members)


def entries_needing(build, needs):
    return [row for row in build.needs_review["entry"] if str(row["needs"]) == needs]


def listed_entries(build, needs):
    return {entry_members(build, row["entry"]) for row in entries_needing(build, needs)}


def listed_judgments(build):
    return {handle(row["judgment"]) for row in build.needs_review["judgment"]}


def listed_pairs(build):
    pairs = set()
    for row in entries_needing(build, "judged different, still joined"):
        record, other = row["record"], row["otherRecord"]
        assert str(record) < str(other), f"?record {record} is not the smaller of the pair by STR"
        pairs.add((handle(record), handle(other), entry_members(build, row["entry"])))
    return pairs


def describe(key, expected, actual):
    lines = [f"entry {sorted(key)}:"]
    lines += [f"  missing {p.n3()} {o.n3()}" for p, o in sorted(expected - actual, key=str)]
    lines += [f"  should not have {p.n3()} {o.n3()}" for p, o in sorted(actual - expected, key=str)]
    return "\n".join(lines)


def view_differences(expected, actual):
    report = []
    for key in sorted(set(expected) | set(actual), key=sorted):
        if key not in actual:
            report.append(f"entry {sorted(key)} is missing")
        elif key not in expected:
            report.append(f"entry {sorted(key)} should not be there")
        elif expected[key] != actual[key]:
            report.append(describe(key, expected[key], actual[key]))
    return report
