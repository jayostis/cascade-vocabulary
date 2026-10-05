"""Alex Rivera's kit: its story and inputs, and the name of each thing #4 gives a handle, worked out from the kit's
inputs alone, never from a pod."""

import json
from functools import cache
from typing import NamedTuple

from rdflib import Namespace, URIRef
from rdflib.namespace import RDF

import recomputed
from cascade_pod import store
from examples import ROOT

KIT = ROOT / "conformance" / "alex-rivera"
INPUT = KIT / "scripted-input"
STORY = json.loads((KIT / "story.json").read_text(encoding="utf-8"))
ADDRESS = STORY["address"]

REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
PROV = Namespace("http://www.w3.org/ns/prov#")
PAV = Namespace("http://purl.org/pav/")
BRIDGE = Namespace("https://ns.cascadeprotocol.org/bridge/v1-draft#")
MATCHER = "urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76"
WEBID = ADDRESS + "profile/card.ttl#me"


class Judgment(NamedTuple):
    step: str
    at: str
    author: str
    verdict: str | None
    members: list
    justification: str | None
    used: list
    supersedes_or_retracts: list
    reason_given: bool


EVERY_JUDGMENT = {handle: Judgment(*row) for handle, row in {
    "J1": ("J1", "2026-09-01T10:00:30Z", "Alex", "About", ["H1-PAT"], None, [], [], False),
    "J2": ("J2", "2026-10-14T15:42:30Z", "Alex", "About", ["H2O-PAT"], None, [], [], False),
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
    "J8": ("J8", "2026-12-02T19:00:00Z", "Alex", "Different", ["H1-PROC-COLO", "H2O-PROC-COLO"], None,
           ["H1-PROC-COLO v1", "H2O-PROC-COLO v1"], [], True),
    "J9": ("J9", "2026-12-02T19:00:00Z", "Alex", "Same", ["H1-ALG-SULFA", "H2O-ALG-SULFA"], None,
           ["H1-ALG-SULFA v2", "H2O-ALG-SULFA v1"], [("supersedes", "J3")], False),
    "J10": ("J10", "2026-12-02T19:00:00Z", "Alex", "Same", ["H1-CON-BRONCH", "H2O-CON-ASTHMA"], None,
            ["H1-CON-BRONCH v2", "H2O-CON-ASTHMA v1"], [], True),
    "J12": ("J12", "2027-03-18T12:00:30Z", "Alex", "About", ["H2F-PAT"], None, [], [], False),
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
    "J19": ("J19", "2027-04-02T20:00:00Z", "Alex", "Different", ["H1-PROC-COLO", "H2F-PROC-COLO"], None,
            ["H1-PROC-COLO v1", "H2F-PROC-COLO v1"], [], False),
    "J20": ("J20", "2027-04-02T20:00:00Z", "Alex", None, [], None, [], [("retracts", "J10")], True),
    "J21": ("J21", "2027-04-02T20:00:00Z", "Alex", "Same", ["H1-ALG-PCN", "H2O-ALG-PCN", "H2F-ALG-PCN"], None,
            ["H1-ALG-PCN v1", "H2O-ALG-PCN v1", "H2F-ALG-PCN v1"], [], False),
    "J22": ("J22", "2027-02-10T17:21:30Z", "Alex", "About", ["H1P-PAT"], None, [], [], False),
    "J23": ("J23", "2027-04-02T20:00:00Z", "Alex", None, [], None, [], [("retracts", "J22")], True),
    "J24": ("J24", "2027-04-02T20:00:00Z", "Alex", "Erroneous", ["H1-PROC-ECHO"], None, ["H1-PROC-ECHO v1"], [], True),
}.items()}


def step(name):
    return next(step for step in STORY["steps"] if step["name"] == name)


@cache
def sources():
    return json.loads((KIT / "expected" / "handles.json").read_text(encoding="utf-8"))


def document(relative):
    """The N5 name of a file of the kit's inputs."""
    return URIRef(recomputed.ni_name((KIT / relative).read_bytes()))


def source_name(row):
    """The name a record or a profile's row in handles.json gives it: from its source's server, type and ID; from its
    document, when no clinical record entry gives a server; or from the subject, its entry's step's time and its
    position."""
    if "server" in row:
        return URIRef(recomputed.record_name([row["server"], row["type"], row["id"]]))
    if "download" in row:
        return URIRef(recomputed.record_name([str(document(row["download"])), ""]))
    [entering] = [s for s in STORY["steps"] if s.get("entry") == row["entry"]]
    return URIRef(recomputed.record_name([STORY["subject"], entering["when"], str(row["position"])]))


def saved_output():
    """Each graph the Bridge saved for an import step, in the story's order."""
    for imported in (s for s in STORY["steps"] if "import" in s):
        for graph in sorted((KIT / imported["import"]["converted"]).glob("*/graph.ttl")):
            yield store.parsed(graph)


def entry_versions(named):
    """The name of each version an entry gives, by N3, its drafts' references replaced by their records' names."""
    found = {}
    for handle, row in sources()["records"].items():
        if "entry" not in row:
            continue
        entry, draft = store.parsed(KIT / row["entry"]), URIRef(f"urn:cascade:output-{row['position']}")
        [version] = entry.subjects(PROV.specializationOf, draft)
        content = {(("iri", recomputed.PLACEHOLDER), ("iri", str(p)), term(named[handle] if o == draft else o))
                   for p, o in entry.predicate_objects(version)}
        found[handle] = URIRef(recomputed.ni_name(recomputed.canonical_nquads(content).encode("utf-8")))
    return found


def term(node):
    if isinstance(node, URIRef):
        return ("iri", str(node))
    return ("literal", str(node), str(node.datatype) if node.datatype else recomputed.XSD_STRING)


def matcher_judgment(handle, named):
    judgment = EVERY_JUDGMENT[handle]
    return URIRef(recomputed.record_name([MATCHER, str(JDG[judgment.justification]),
                                          *sorted(str(named[m]) for m in judgment.members),
                                          *sorted(str(named[u]) for u in judgment.used)]))


ROWS_OF = {"rules": (None, RDF.type, REC.MatcherRule), "ingredient-map": (None, REC.sameIngredientAs, None),
           "cvx-vaccine-groups": (None, REC.cvxCode, None)}


@cache
def handles():
    """Each handle #4 gives, by the name the kit's inputs give the thing it stands for."""
    named = {h: source_name(row) for kind in ("records", "profiles") for h, row in sources()[kind].items()}
    record_handle = {name: h for h, name in named.items()}
    versions = {}
    for graph in saved_output():
        for arrival in graph.subjects(BRIDGE.arrivedAs, None):
            version = graph.value(arrival, BRIDGE.arrivedAs)
            seen = versions.setdefault(record_handle[graph.value(version, PROV.specializationOf)], [])
            if version not in seen:
                seen.append(version)
    for h, version in entry_versions(named).items():
        versions[h] = [version]
    named |= {f"{h} v{n}": version for h, seen in versions.items() for n, version in enumerate(seen, 1)}
    references = store.parsed(INPUT / "references" / "references.ttl")
    for h, key in sources()["series"].items():
        [series] = [s for s in references.subjects(RDF.type, REC.ReferenceSeries)
                    if any(ROWS_OF[key] in store.parsed(INPUT / "references" / f"{str(v)[len('urn:uuid:'):]}.ttl")
                           for v in references.subjects(PROV.specializationOf, s))]
        named[h] = series
        named |= {f"{h}-{references.value(v, PAV.version)}": v for v in references.subjects(PROV.specializationOf, series)}
    named["S"] = URIRef(STORY["subject"])
    for path in sorted((INPUT / "judgments").glob("*.ttl")):
        [named[path.stem]] = store.parsed(path).subjects(RDF.type, JDG.Judgment)
    named |= {h: matcher_judgment(h, named) for h, row in EVERY_JUDGMENT.items() if row.author == "matcher"}
    return named


@cache
def handles_by_name():
    return {str(term): handle for handle, term in handles().items()}


def name(handle):
    return handles()[handle]


def handle(term):
    return handles_by_name()[str(term)]
