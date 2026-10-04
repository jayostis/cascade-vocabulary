"""The Cascade matcher: writes a Same wherever one of its four rules joins two records."""

import csv
import json

from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from . import Failure, names, turtle
from .pod import NOT_RDF, RECORD_FOLDERS, fanned, save
from .store import Rdflib

CLINICAL, HEALTH, JDG, NPX, PAV, PROV, RDFS, REC = (
    Namespace(turtle.PREFIXES[p]) for p in ("clinical", "health", "jdg", "npx", "pav", "prov", "rdfs", "rec"))
MATCHER = URIRef("urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76")
CODES = [HEALTH.allergenCode, HEALTH.snomedCode, CLINICAL.snomedCode]
SNOMED, RXNORM = "http://snomed.info/sct/", "http://www.nlm.nih.gov/research/umls/rxnorm/"


def judgment(name, *, at, members, justification, used):
    same = URIRef(name)
    return {(same, RDF.type, JDG.Judgment), (same, JDG.verdict, JDG.Same), (same, JDG.justification, justification),
            *((same, PROV.hadMember, URIRef(m)) for m in members), *((same, PROV.used, URIRef(u)) for u in used),
            (same, PROV.wasAttributedTo, MATCHER), (same, PROV.generatedAtTime, Literal(at, datatype=XSD.dateTime, normalize=False)),
            (MATCHER, RDF.type, PROV.SoftwareAgent), (MATCHER, RDFS.label, Literal("Cascade matcher"))}


def series_triples(series):
    return {(URIRef(series["name"]), RDF.type, REC.ReferenceSeries),
            (URIRef(series["name"]), RDFS.label, Literal(series["label"]))}


def version_triples(series, version):
    named = URIRef(version["name"])
    revises = [v["name"] for v in series["versions"] if v["version"] == version.get("revises")]
    return {(named, RDF.type, PROV.Entity), (named, PROV.specializationOf, URIRef(series["name"])),
            (named, PAV.version, Literal(version["version"])), *((named, PROV.wasRevisionOf, URIRef(r)) for r in revises)}


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
        held = [v for v in pod.graph.subjects(PROV.specializationOf, URIRef(series["name"]))]
        if not held:
            shipped = next((v for v in series["versions"] if v["version"] == series["ships_with"]), None)
            if shipped is None:
                raise Failure(f"{series['label']} ships with {series['ships_with']}, a version it does not list")
            return shipped
        revised = {o for v in held for o in pod.graph.objects(v, PROV.wasRevisionOf)}
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
        self.added_by = example.added_by(read_through)
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
                revisions = set(g.subjects(REC.revisionOf, record))
                followed = {o for r in revisions for o in g.objects(r, PROV.wasRevisionOf)}
                first = [r for r in revisions if g.value(r, PROV.wasRevisionOf) is None]
                latest = list(revisions - followed)
                if len(first) != 1 or len(latest) != 1:
                    raise Failure(f"{record} has no one first and one latest revision")
                version = g.value(latest[0], REC.version)
                records[record] = {
                    "name": str(record), "folder": folder, "path": self.defined_in[record],
                    "first": self.defined_in[first[0]], "arrived": str(g.value(first[0], PROV.generatedAtTime)),
                    "version": str(version), "patient": g.value(version, REC.patient),
                    "codes": {(p, o) for p in CODES for o in g.objects(version, p)},
                    "vaccine": g.value(version, HEALTH.vaccineCode), "date": g.value(version, HEALTH.administrationDate),
                }
        return records

    def replaced(self, judgment):
        return any(True for p in (NPX.supersedes, NPX.retracts) for _ in self.graph.subjects(p, judgment))

    def subjects_profiles(self):
        g, profiles = self.graph, {self.subject}
        for about in g.subjects(JDG.verdict, JDG.About):
            if g.value(about, JDG.subject) == self.subject and not self.replaced(about):
                profiles |= set(g.objects(about, PROV.hadMember))
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

    def file(self, folder, name, triples):
        path = fanned(folder, name)
        self.files[path] = turtle.write(triples, self.pod.example.address + path)

    def table_version(self, rule):
        return self.references.current(rule["table"], self.pod) if rule["table"] else None

    def matches(self, rule, a, b):
        version = self.table_version(rule)
        table = self.references.table(version) if version else None
        return a["folder"] == b["folder"] and a["folder"] in rule["applies_to"].split() and MATCHES[rule["rule"]](a, b, table)

    def same(self, rule, members):
        applied = [self.rules_version] + ([self.table_version(rule)] if rule["table"] else [])
        used = sorted({v["name"] for v in applied} | {m["version"] for m in members})
        justification = JDG[rule["justification"]]
        member_names = sorted(m["name"] for m in members)
        name = names.record([str(MATCHER), str(justification), *member_names, *used])
        self.file("judgments", name, judgment(name, at=self.at, members=member_names, justification=justification,
                                              used=used))
        for version in applied:
            series, _ = self.references.versions[version["name"]]
            for thing, triples in ((series, series_triples(series)), (version, version_triples(series, version))):
                if not self.pod.holds(thing["name"]):
                    self.file("references", thing["name"], triples)

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
        revised = {o for o in g.objects(None, PROV.wasRevisionOf) if str(o) in self.references.versions}
        by_justification = {JDG[r["justification"]]: r for r in self.rules}
        theirs = self.pod.subjects_records()
        for judged in sorted(g.subjects(PROV.wasAttributedTo, MATCHER), key=str):
            if g.value(judged, JDG.verdict) != JDG.Same or self.pod.replaced(judged):
                continue
            if not revised & set(g.objects(judged, PROV.used)):
                continue
            rule = by_justification[g.value(judged, JDG.justification)]
            members = [theirs[m] for m in sorted(g.objects(judged, PROV.hadMember), key=str) if m in theirs]
            still = [m for m in members if any(self.matches(rule, m, o) for o in members if o is not m)]
            if len(still) >= 2:
                self.same(rule, still)


def run(example, read_through, takes, at, out):
    matcher = Matcher(Reading(example, read_through), at)
    if takes:
        matcher.take(takes)
    else:
        matcher.recheck()
    save(matcher.files, out)
    return 0
