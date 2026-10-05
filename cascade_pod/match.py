"""The Cascade matcher: writes a Same wherever one of its rules joins two records."""

import csv
import json

from rdflib import Literal, URIRef
from rdflib.namespace import RDF, RDFS

from . import Failure, derive, names, turtle, vocabulary
from .pod import FOLDERS, NOT_RDF, fanned, save
from .store import date_time
from .turtle import CLINICAL, HEALTH, JDG, NPX, PAV, PROV, REC

MATCHER = URIRef("urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76")
CODES = [HEALTH.allergenCode, HEALTH.snomedCode, CLINICAL.snomedCode]
SNOMED, RXNORM = "http://snomed.info/sct/", "http://www.nlm.nih.gov/research/umls/rxnorm/"


def judgment(name, *, at, members, justification, used):
    same = URIRef(name)
    return {(same, RDF.type, JDG.Judgment), (same, JDG.verdict, JDG.Same), (same, JDG.justification, justification),
            *((same, PROV.hadMember, URIRef(m)) for m in members), *((same, PROV.used, URIRef(u)) for u in used),
            (same, PROV.wasAttributedTo, MATCHER), (same, PROV.generatedAtTime, date_time(at)),
            (MATCHER, RDF.type, PROV.SoftwareAgent), (MATCHER, RDFS.label, Literal("Cascade matcher"))}


def series_triples(series):
    return {(URIRef(series["name"]), RDF.type, REC.ReferenceSeries),
            (URIRef(series["name"]), RDFS.label, Literal(series["label"]))}


def version_triples(series, version):
    named = URIRef(version["name"])
    revises = [v["name"] for v in series["versions"] if v["version"] == version.get("revises")]
    return {(named, RDF.type, PROV.Entity), (named, PROV.specializationOf, URIRef(series["name"])),
            (named, PAV.version, Literal(version["version"])), *((named, PROV.wasRevisionOf, URIRef(r)) for r in revises)}


class References:
    def __init__(self, folder):
        self.folder = folder
        self.series = json.loads((folder / "references.json").read_text(encoding="utf-8"))["series"]
        self.by_key = {s["key"]: s for s in self.series}
        self.versions = {v["name"]: (s, v) for s in self.series for v in s["versions"]}

    def table(self, version):
        with open(self.folder / version["table"], newline="", encoding="utf-8") as table:
            return list(csv.DictReader(table))

    def current(self, key, reading):
        series = self.by_key[key]
        current = [str(v) for v in reading.graph.objects(URIRef(series["name"]), PAV.hasCurrentVersion)]
        if not current:
            shipped = next((v for v in series["versions"] if v["version"] == series["ships_with"]), None)
            if shipped is None:
                raise Failure(f"{series['label']} ships with {series['ships_with']}, a version it does not list")
            return shipped
        if len(current) != 1 or current[0] not in self.versions:
            raise Failure(f"the pod holds no one current version the matcher knows of {series['label']}")
        return self.versions[current[0]][1]


class Reading:
    def __init__(self, example, read_through):
        self.example = example
        events = example.through(read_through)
        self.subject = URIRef(next(e["subject"] for e in events if "subject" in e))
        self.added_by = example.added_by(read_through)
        store = example.pod_only("rdflib", read_through)
        derive.run(store, vocabulary.derivations_before_the_lens())
        self.graph, self.defined_in = store.graph(), {}
        for event in events:
            for path in (p for p in event["adds"] if not p.startswith(NOT_RDF)):
                for subject in store.graph(example.address + path).subjects(RDF.type, None):
                    self.defined_in.setdefault(subject, path)
        self.records = self._records()

    def _records(self):
        g, records = self.graph, {}
        for record in g.subjects(RDF.type, REC.Record):
            first = [r for r in g.subjects(REC.revisionOf, record) if g.value(r, PROV.wasRevisionOf) is None]
            version = g.value(record, PAV.hasCurrentVersion)
            if len(first) != 1 or version is None:
                raise Failure(f"{record} has no one first revision and current version")
            records[record] = {
                "name": str(record), "kind": str(g.value(record, REC.kind)), "path": self.defined_in[record],
                "first": self.defined_in[first[0]], "arrived": str(g.value(first[0], PROV.generatedAtTime)),
                "version": str(version), "patient": g.value(version, REC.patient),
                "codes": {(p, o) for p in CODES for o in g.objects(version, p)},
                "vaccine": g.value(version, HEALTH.vaccineCode), "date": g.value(version, REC.date),
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


def same_code(a, b, _):
    return bool(a["codes"] & b["codes"])


def same_code_and_date(a, b, _):
    return a["vaccine"] is not None and a["vaccine"] == b["vaccine"] and a["date"] is not None and a["date"] == b["date"]


def mapped_code(a, b, table):
    pairs = {(row["snomed"], row["rxnorm"]) for row in table}
    codes = [{str(o) for p, o in r["codes"] if p == HEALTH.allergenCode} for r in (a, b)]
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
    def __init__(self, reading, at):
        self.reading, self.at, self.references = reading, at, References(reading.example.folder / "references")
        self.rules_version = self.references.current("rules", reading)
        self.rules = self.references.table(self.rules_version)
        if sorted(r["rule"] for r in self.rules) != sorted(MATCHES):
            raise Failure(f"rule set {self.rules_version['version']} names rules this matcher does not apply")
        self.table_versions = {r["rule"]: self.references.current(r["table"], reading)
                               for r in self.rules if r["table"]}
        self.tables = {rule: self.references.table(version) for rule, version in self.table_versions.items()}
        self.files = {}

    def file(self, folder, name, triples):
        path = fanned(folder, name)
        self.files[path] = turtle.write(triples, self.reading.example.address + path)

    def matches(self, rule, a, b):
        return (a["kind"] == b["kind"] and a["kind"] in rule["applies_to"].split()
                and MATCHES[rule["rule"]](a, b, self.tables.get(rule["rule"])))

    def same(self, rule, members):
        applied = [self.rules_version] + ([self.table_versions[rule["rule"]]] if rule["table"] else [])
        used = sorted({v["name"] for v in applied} | {m["version"] for m in members})
        justification = JDG[rule["justification"]]
        member_names = sorted(m["name"] for m in members)
        name = names.record([str(MATCHER), str(justification), *member_names, *used])
        self.file(FOLDERS["judgments"], name,
                  judgment(name, at=self.at, members=member_names, justification=justification, used=used))
        for version in applied:
            series, _ = self.references.versions[version["name"]]
            for thing, triples in ((series, series_triples(series)), (version, version_triples(series, version))):
                if not self.reading.holds(thing["name"]):
                    self.file(FOLDERS["references"], thing["name"], triples)

    def take(self, event):
        theirs = self.reading.subjects_records()
        taken = sorted((r for r in theirs.values() if self.reading.added_by[r["first"]] == event),
                       key=lambda r: (r["arrived"], r["path"]))
        compared = sorted((r for r in theirs.values() if r not in taken), key=lambda r: r["path"])
        for record in taken:
            for rule in self.rules:
                matched = [other for other in compared if self.matches(rule, record, other)]
                if matched:
                    self.same(rule, [record, *matched])
            compared.append(record)

    def recheck(self):
        g = self.reading.graph
        revised = {o for o in g.objects(None, PROV.wasRevisionOf) if str(o) in self.references.versions}
        by_justification = {JDG[r["justification"]]: r for r in self.rules}
        theirs = self.reading.subjects_records()
        for judged in sorted(g.subjects(PROV.wasAttributedTo, MATCHER), key=str):
            if g.value(judged, JDG.verdict) != JDG.Same or self.reading.replaced(judged):
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
