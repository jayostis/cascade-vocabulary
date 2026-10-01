"""The Cascade matcher: writes a Same wherever one of its four rules joins two records."""

import csv
import json
import re

from rdflib import URIRef
from rdflib.namespace import RDF

from . import Failure, names
from .pod import CLINICAL, HEALTH, NOT_RDF, RECORD_FOLDERS, fanned
from .store import Rdflib

MATCHER = "urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76"

PREFIXES = {
    "dct": "http://purl.org/dc/terms/",
    "jdg": "https://ns.cascadeprotocol.org/judgments/v1-draft#",
    "npx": "http://purl.org/nanopub/x/",
    "pav": "http://purl.org/pav/",
    "prov": "http://www.w3.org/ns/prov#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rec": "https://ns.cascadeprotocol.org/records/v1-draft#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
JDG, NPX, PROV, REC = (PREFIXES[p] for p in ("jdg", "npx", "prov", "rec"))
PAV_VERSION = URIRef(PREFIXES["pav"] + "version")
SPECIALIZATION_OF, WAS_REVISION_OF = URIRef(PROV + "specializationOf"), URIRef(PROV + "wasRevisionOf")
CODES = [URIRef(HEALTH + "allergenCode"), URIRef(HEALTH + "snomedCode"), URIRef(CLINICAL + "snomedCode")]
VACCINE_CODE, ADMINISTRATION_DATE = URIRef(HEALTH + "vaccineCode"), URIRef(HEALTH + "administrationDate")
SNOMED, RXNORM = "http://snomed.info/sct/", "http://www.nlm.nih.gov/research/umls/rxnorm/"


# Turtle in one fixed layout, shared by every judgment and reference file

JUDGMENT_ORDER = ["jdg:verdict", "jdg:subject", "jdg:basis", "prov:hadMember", "jdg:justification",
                  "npx:supersedes", "npx:retracts", "dct:description", "prov:used", "prov:wasAttributedTo",
                  "prov:qualifiedAttribution", "prov:generatedAtTime"]
REFERENCE_ORDER = ["rdfs:label", "prov:specializationOf", "pav:version", "prov:wasRevisionOf"]


def _iri(iri):
    for prefix, namespace in PREFIXES.items():
        if iri.startswith(namespace) and iri[len(namespace):].isalnum():
            return f"{prefix}:{iri[len(namespace):]}"
    return f"<{iri}>"


def _string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _block(subject, kind, statements, order):
    lines = [f"{_iri(subject)} a {kind} ;"]
    present = [p for p in order if statements.get(p)]
    for index, predicate in enumerate(present):
        end = " ." if index == len(present) - 1 else " ;"
        values = sorted(statements[predicate])
        indent = " " * (5 + len(predicate))
        lines.append(f"    {predicate} " + f" ,\n{indent}".join(values) + end)
    return "\n".join(lines)


def _file(blocks):
    text = "\n\n".join(blocks)
    bare = re.sub(r'<[^>]*>|"(?:[^"\\]|\\.)*"', " ", text)
    used = [p for p in PREFIXES if re.search(rf"(?<![\w-]){p}:", bare)]
    head = "".join(f"@prefix {p}: <{PREFIXES[p]}> ." + "\n" for p in used)
    return (head + "\n" + text + "\n").encode("utf-8")


def judgment_file(name, *, at, members, justification, used):
    statements = {
        "jdg:verdict": [_iri(JDG + "Same")],
        "prov:hadMember": [_iri(m) for m in members],
        "jdg:justification": [_iri(JDG + justification)],
        "prov:used": [_iri(u) for u in used],
        "prov:wasAttributedTo": [_iri(MATCHER)],
        "prov:generatedAtTime": [_string(at) + "^^xsd:dateTime"],
    }
    author_block = f'{_iri(MATCHER)} a prov:SoftwareAgent ;\n    rdfs:label "Cascade matcher" .'
    return _file([_block(name, "jdg:Judgment", statements, JUDGMENT_ORDER), author_block])


def series_file(series):
    return _file([_block(series["name"], "rec:ReferenceSeries", {"rdfs:label": [_string(series["label"])]},
                         REFERENCE_ORDER)])


def version_file(series, version):
    revises = [v["name"] for v in series["versions"] if v["version"] == version.get("revises")]
    return _file([_block(version["name"], "prov:Entity", {
        "prov:specializationOf": [_iri(series["name"])],
        "pav:version": [_string(version["version"])],
        "prov:wasRevisionOf": [_iri(r) for r in revises],
    }, REFERENCE_ORDER)])


# What the matcher knows: the example's references and their tables

class References:
    def __init__(self, folder):
        self.folder = folder
        self.series = json.loads((folder / "references.json").read_text(encoding="utf-8"))["series"]
        self.by_key = {s["key"]: s for s in self.series}
        self.versions = {v["name"]: (s, v) for s in self.series for v in s["versions"]}

    def table(self, version):
        with open(self.folder / version["table"], newline="", encoding="utf-8") as table:
            return list(csv.DictReader(table))

    def current(self, key, pod):
        series = self.by_key[key]
        held = [v for v in pod.graph.subjects(SPECIALIZATION_OF, URIRef(series["name"]))]
        if not held:
            shipped = next((v for v in series["versions"] if v["version"] == series["ships_with"]), None)
            if shipped is None:
                raise Failure(f"{series['label']} ships with {series['ships_with']}, a version it does not list")
            return shipped
        revised = {o for v in held for o in pod.graph.objects(v, WAS_REVISION_OF)}
        current = [v for v in held if v not in revised]
        if len(current) != 1 or str(current[0]) not in self.versions:
            raise Failure(f"the pod holds no one current version the matcher knows of {series['label']}")
        return self.versions[str(current[0])][1]


# The pod through one event

class Reading:
    def __init__(self, example, read_through):
        self.example = example
        events = example.through(read_through)
        self.subject = URIRef(next(e["subject"] for e in events if "subject" in e))
        self.added_by = {path: event["event"] for event in events for path in event["adds"]}
        store = Rdflib()
        example.load(store, read_through)
        self.graph, self.defined_in = store.graph(), {}
        for event in events:
            for path in (p for p in event["adds"] if not p.startswith(NOT_RDF)):
                for subject in store.graph(example.address + path).subjects(RDF.type, None):
                    self.defined_in.setdefault(subject, path)
        self.records = self._records()

    def _records(self):
        g, records = self.graph, {}
        for kind, folder in RECORD_FOLDERS.items():
            for record in g.subjects(RDF.type, URIRef(kind)):
                revisions = set(g.subjects(URIRef(REC + "revisionOf"), record))
                followed = {o for r in revisions for o in g.objects(r, WAS_REVISION_OF)}
                first = [r for r in revisions if g.value(r, WAS_REVISION_OF) is None]
                latest = list(revisions - followed)
                if len(first) != 1 or len(latest) != 1:
                    raise Failure(f"{record} has no one first and one latest revision")
                version = g.value(latest[0], URIRef(REC + "version"))
                records[record] = {
                    "name": str(record), "folder": folder, "path": self.defined_in[record],
                    "first": self.defined_in[first[0]], "arrived": str(g.value(first[0], URIRef(PROV + "generatedAtTime"))),
                    "version": str(version), "patient": g.value(version, URIRef(REC + "patient")),
                    "codes": {(p, o) for p in CODES for o in g.objects(version, p)},
                    "vaccine": g.value(version, VACCINE_CODE), "date": g.value(version, ADMINISTRATION_DATE),
                }
        return records

    def replaced(self, judgment):
        return any(True for p in (NPX + "supersedes", NPX + "retracts") for _ in self.graph.subjects(URIRef(p), judgment))

    def subjects_profiles(self):
        g, profiles = self.graph, {self.subject}
        for about in g.subjects(URIRef(JDG + "verdict"), URIRef(JDG + "About")):
            if g.value(about, URIRef(JDG + "subject")) == self.subject and not self.replaced(about):
                profiles |= set(g.objects(about, URIRef(PROV + "hadMember")))
        return profiles

    def subjects_records(self):
        profiles = self.subjects_profiles()
        return {name: r for name, r in self.records.items() if r["patient"] in profiles}

    def holds(self, name):
        return (URIRef(name), None, None) in self.graph


# The four rules

def same_code(a, b, _):
    return bool(a["codes"] & b["codes"])


def same_code_and_date(a, b, _):
    return a["vaccine"] is not None and a["vaccine"] == b["vaccine"] and a["date"] is not None and a["date"] == b["date"]


def mapped_code(a, b, table):
    pairs = {(row["snomed"], row["rxnorm"]) for row in table}
    codes = [{str(o) for p, o in r["codes"] if p == CODES[0]} for r in (a, b)]
    return any((s, x) in pairs or (x, s) in pairs
               for s in codes[0] for x in codes[1]
               if (s.startswith(SNOMED) and x.startswith(RXNORM)) or (s.startswith(RXNORM) and x.startswith(SNOMED)))


def vaccine_group_and_date(a, b, table):
    groups = {row["cvx"]: row["group"] for row in table}
    return (a["vaccine"] is not None and b["vaccine"] is not None and a["vaccine"] != b["vaccine"]
            and groups.get(str(a["vaccine"])) is not None
            and groups.get(str(a["vaccine"])) == groups.get(str(b["vaccine"]))
            and a["date"] is not None and a["date"] == b["date"])


MATCHES = {"R1": same_code, "R2": same_code_and_date, "R3": mapped_code, "R4": vaccine_group_and_date}


class Matcher:
    def __init__(self, pod, at):
        self.pod, self.at, self.references = pod, at, References(pod.example.folder / "references")
        self.rules_version = self.references.current("rules", pod)
        self.rules = self.references.table(self.rules_version)
        if sorted(r["rule"] for r in self.rules) != sorted(MATCHES):
            raise Failure(f"rule set {self.rules_version['version']} names rules this matcher does not apply")
        self.files = {}

    def table_version(self, rule):
        return self.references.current(rule["table"], self.pod) if rule["table"] else None

    def matches(self, rule, a, b):
        version = self.table_version(rule)
        table = self.references.table(version) if version else None
        return a["folder"] == b["folder"] and a["folder"] in rule["applies_to"].split() and MATCHES[rule["rule"]](a, b, table)

    def same(self, rule, members):
        applied = [self.rules_version] + ([self.table_version(rule)] if rule["table"] else [])
        used = sorted({v["name"] for v in applied} | {m["version"] for m in members})
        justification = JDG + rule["justification"]
        member_names = sorted(m["name"] for m in members)
        name = names.record([MATCHER, justification, *member_names, *used])
        self.files[fanned("judgments", name)] = judgment_file(
            name, at=self.at, members=member_names, justification=rule["justification"], used=used)
        for version in applied:
            series, _ = self.references.versions[version["name"]]
            for thing, content in ((series, series_file(series)), (version, version_file(series, version))):
                if not self.pod.holds(thing["name"]):
                    self.files[fanned("references", thing["name"])] = content

    def take(self, event):
        theirs = self.pod.subjects_records()
        taken = sorted((r for r in theirs.values() if self.pod.added_by[r["first"]] == event),
                       key=lambda r: (r["arrived"], r["path"]))
        compared = sorted((r for r in theirs.values() if r not in taken), key=lambda r: r["path"])
        for record in taken:
            for rule in self.rules:
                matched = [other for other in compared if self.matches(rule, record, other)]
                if matched:
                    self.same(rule, [record, *matched])
            compared.append(record)

    def recheck(self):
        g = self.pod.graph
        revised = {o for o in g.objects(None, WAS_REVISION_OF) if str(o) in self.references.versions}
        by_justification = {JDG + r["justification"]: r for r in self.rules}
        theirs = self.pod.subjects_records()
        for judgment in sorted(g.subjects(URIRef(PROV + "wasAttributedTo"), URIRef(MATCHER)), key=str):
            if g.value(judgment, URIRef(JDG + "verdict")) != URIRef(JDG + "Same") or self.pod.replaced(judgment):
                continue
            if not revised & set(g.objects(judgment, URIRef(PROV + "used"))):
                continue
            rule = by_justification[str(g.value(judgment, URIRef(JDG + "justification")))]
            members = [theirs[m] for m in sorted(g.objects(judgment, URIRef(PROV + "hadMember")), key=str) if m in theirs]
            still = [m for m in members if any(self.matches(rule, m, o) for o in members if o is not m)]
            if len(still) >= 2:
                self.same(rule, still)


def run(example, read_through, takes, at, out):
    matcher = Matcher(Reading(example, read_through), at)
    if takes:
        matcher.take(takes)
    else:
        matcher.recheck()
    for path, content in sorted(matcher.files.items()):
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return 0
