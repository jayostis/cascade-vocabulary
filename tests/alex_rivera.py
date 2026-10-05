import json
from functools import lru_cache
from typing import NamedTuple

import pytest
from rdflib import Namespace, URIRef
from rdflib.namespace import RDF

import recomputed
from cascade_pod import store
from cascade_pod.example import Example
from examples import ROOT

EXAMPLE = ROOT / "example-pods" / "alex-rivera"
ALEX = Example(EXAMPLE)

REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
PROV = Namespace("http://www.w3.org/ns/prov#")
PAV = Namespace("http://purl.org/pav/")
MATCHER = "urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76"


class Judgment(NamedTuple):
    event: str
    at: str
    author: str
    verdict: str | None
    members: list
    justification: str | None
    used: list
    supersedes_or_retracts: list
    reason_given: bool


EVERY_JUDGMENT = {handle: Judgment(*row) for handle, row in {
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
}.items()}


@lru_cache(maxsize=None)
def pod(event):
    return ALEX.story_store("rdflib", event).graph()


def final_pod():
    return pod(ALEX.events[-1]["event"])


@lru_cache(maxsize=None)
def sources():
    return json.loads((EXAMPLE / "expected" / "handles.json").read_text(encoding="utf-8"))


def source_name(row):
    if "server" in row:
        return URIRef(recomputed.record_name([row["server"], row["type"], row["id"]]))
    if "download" in row:
        return URIRef(recomputed.record_name([recomputed.ni_name((EXAMPLE / row["download"]).read_bytes()), ""]))
    entry = store.parsed(EXAMPLE / row["entry"])
    [activity] = entry.subjects(RDF.type, PROV.Activity)
    subject = next(event["subject"] for event in ALEX.events if "subject" in event)
    started = str(entry.value(activity, PROV.startedAtTime))
    assert started.endswith("Z"), started
    return URIRef(recomputed.record_name([subject, started, str(row["position"])]))


def arrivals(graph, record):
    return sorted(graph.subjects(REC.revisionOf, record), key=lambda r: str(graph.value(r, PROV.generatedAtTime)))


def _matcher_judgment(handle, named):
    judgment = EVERY_JUDGMENT[handle]
    return URIRef(recomputed.record_name([MATCHER, JDG[judgment.justification],
                                          *sorted(str(named[m]) for m in judgment.members),
                                          *sorted(str(named[u]) for u in judgment.used)]))


ROWS_OF = {"rules": (None, RDF.type, REC.MatcherRule), "ingredient-map": (None, REC.sameIngredientAs, None),
           "cvx-vaccine-groups": (None, REC.cvxCode, None)}


def holds_rows(references, series, key):
    """Whether a version of the series holds rows of the kind of table handles.json names by `key`."""
    return any(ROWS_OF[key] in store.parsed(EXAMPLE / "references" / f"{str(v)[len('urn:uuid:'):]}.ttl")
               for v in references.subjects(PROV.specializationOf, series))


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
    references = store.parsed(EXAMPLE / "references" / "references.ttl")
    for h, key in sources()["series"].items():
        [series] = [s for s in references.subjects(RDF.type, REC.ReferenceSeries) if holds_rows(references, s, key)]
        named[h] = series
        named |= {f"{h}-{references.value(v, PAV.version)}": v for v in references.subjects(PROV.specializationOf, series)}
    named |= {f"I-{e['event']}": URIRef(e["import"]) for e in ALEX.events if "import" in e}
    named |= {"S": URIRef(e["subject"]) for e in ALEX.events if "subject" in e}
    named |= {h: URIRef(n) for h, n in sources()["judgments"].items()}
    named |= {h: _matcher_judgment(h, named) for h, row in EVERY_JUDGMENT.items() if row.author == "matcher"}
    return named


@lru_cache(maxsize=None)
def handles_by_name():
    return {str(term): handle for handle, term in handles().items()}


def name(handle):
    term = handles().get(handle)
    if term is None:
        pytest.fail(f"handle {handle} names nothing in the pod")
    return term


def handle(term):
    found = handles_by_name().get(str(term))
    if found is None:
        pytest.fail(f"{term} has no handle")
    return found
