"""The Cascade matcher: writes a Same wherever one of rule set 2026.1's four rules joins two records.

python3 example-pods/alex-rivera/matcher/match.py --read-through <event> [--takes <event>] --at <time> --out <directory>
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import rdflib
from rdflib import Graph, URIRef
from rdflib.namespace import RDF

rdflib.NORMALIZE_LITERALS = False

MATCHER = "urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76"
POD_BASE = "https://pod.alex-rivera.example/"
RECORD_NAMESPACE = "90c60849-c5ef-4ca6-bfb8-8662bd07d2b5"
HERE = Path(__file__).absolute().parent

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
CLINICAL = "https://ns.cascadeprotocol.org/clinical/v1#"
HEALTH = "https://ns.cascadeprotocol.org/health/v1#"
JDG, NPX, PROV, REC = (PREFIXES[p] for p in ("jdg", "npx", "prov", "rec"))
PAV_VERSION = URIRef(PREFIXES["pav"] + "version")
SPECIALIZATION_OF, WAS_REVISION_OF = URIRef(PROV + "specializationOf"), URIRef(PROV + "wasRevisionOf")
FOLDERS = {
    HEALTH + "AllergyRecord": "allergies",
    HEALTH + "ConditionRecord": "conditions",
    HEALTH + "ImmunizationRecord": "immunizations",
    CLINICAL + "Procedure": "procedures",
}
CODES = [URIRef(HEALTH + "allergenCode"), URIRef(HEALTH + "snomedCode"), URIRef(CLINICAL + "snomedCode")]
VACCINE_CODE, ADMINISTRATION_DATE = URIRef(HEALTH + "vaccineCode"), URIRef(HEALTH + "administrationDate")
SNOMED, RXNORM = "http://snomed.info/sct/", "http://www.nlm.nih.gov/research/umls/rxnorm/"


class Failure(Exception):
    pass


def record_name(inputs):
    digest = bytearray(hashlib.sha256("|".join([RECORD_NAMESPACE, *inputs]).encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    text = digest.hex()
    return f"urn:uuid:{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def fanned(folder, name):
    stem = name[len("urn:uuid:"):]
    return f"{folder}/{stem[:2]}/{stem}.ttl"


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


def judgment_file(name, *, author, person, at, verdict=None, subject=None, basis=None, members=(),
                  justification=None, supersedes=(), retracts=(), description=None, used=()):
    statements = {
        "jdg:verdict": [_iri(JDG + verdict)] if verdict else [],
        "jdg:subject": [_iri(subject)] if subject else [],
        "jdg:basis": [_iri(JDG + basis)] if basis else [],
        "prov:hadMember": [_iri(m) for m in members],
        "jdg:justification": [_iri(JDG + justification)] if justification else [],
        "npx:supersedes": [_iri(j) for j in supersedes],
        "npx:retracts": [_iri(j) for j in retracts],
        "dct:description": [_string(description) + "@en"] if description else [],
        "prov:used": [_iri(u) for u in used],
        "prov:wasAttributedTo": [_iri(author)],
        "prov:generatedAtTime": [_string(at) + "^^xsd:dateTime"],
    }
    if person:
        statements["prov:qualifiedAttribution"] = [
            f"[ a prov:Attribution ;\n        prov:agent {_iri(author)} ;\n        prov:hadRole jdg:patient ]"]
        author_block = f"{_iri(author)} a prov:Person ."
    else:
        author_block = f'{_iri(author)} a prov:SoftwareAgent ;\n    rdfs:label "Cascade matcher" .'
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


# What the matcher knows: its references and their tables

def read_csv(relative):
    with open(HERE / relative, newline="", encoding="utf-8") as table:
        return list(csv.DictReader(table))


class References:
    def __init__(self):
        self.series = json.loads((HERE / "references.json").read_text(encoding="utf-8"))["series"]
        self.by_key = {s["key"]: s for s in self.series}
        self.versions = {v["name"]: (s, v) for s in self.series for v in s["versions"]}

    def current(self, key, pod):
        series = self.by_key[key]
        held = [v for v in pod.graph.subjects(SPECIALIZATION_OF, URIRef(series["name"]))]
        if not held:
            return next(v for v in series["versions"] if v["version"] == series["ships_with"])
        revised = {o for v in held for o in pod.graph.objects(v, WAS_REVISION_OF)}
        current = [v for v in held if v not in revised]
        if len(current) != 1 or str(current[0]) not in self.versions:
            raise Failure(f"the pod holds no one current version the matcher knows of {series['label']}")
        return self.versions[str(current[0])][1]


# The pod through one event

class Pod:
    def __init__(self, example, read_through):
        manifest = json.loads((example / "events.json").read_text(encoding="utf-8"))
        events = [e["event"] for e in manifest["events"]]
        if read_through not in events:
            raise Failure(f"no event {read_through}")
        self.subject = URIRef(next(e["subject"] for e in manifest["events"] if "subject" in e))
        self.added_by, self.graph, self.defined_in = {}, Graph(), {}
        for event in manifest["events"][: events.index(read_through) + 1]:
            for path in event["adds"]:
                self.added_by[path] = event["event"]
                if path.startswith(("records/", "judgments/", "references/")):
                    graph = Graph().parse(example / "pod" / path, format="turtle", publicID=POD_BASE + path)
                    for subject in graph.subjects(RDF.type, None):
                        self.defined_in.setdefault(subject, path)
                    self.graph += graph
        self.records = self._records()

    def _records(self):
        g, records = self.graph, {}
        for kind, folder in FOLDERS.items():
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
        self.pod, self.at, self.references = pod, at, References()
        self.rules_version = self.references.current("rules", pod)
        self.rules = read_csv(self.rules_version["table"])
        if sorted(r["rule"] for r in self.rules) != sorted(MATCHES):
            raise Failure(f"rule set {self.rules_version['version']} names rules this matcher does not apply")
        self.files = {}

    def table_version(self, rule):
        return self.references.current(rule["table"], self.pod) if rule["table"] else None

    def matches(self, rule, a, b):
        version = self.table_version(rule)
        table = read_csv(version["table"]) if version else None
        return a["folder"] == b["folder"] and a["folder"] in rule["applies_to"].split() and MATCHES[rule["rule"]](a, b, table)

    def same(self, rule, members):
        applied = [self.rules_version] + ([self.table_version(rule)] if rule["table"] else [])
        used = sorted({v["name"] for v in applied} | {m["version"] for m in members})
        justification = JDG + rule["justification"]
        names = sorted(m["name"] for m in members)
        name = record_name([MATCHER, justification, *names, *used])
        self.files[fanned("judgments", name)] = judgment_file(
            name, author=MATCHER, person=False, at=self.at, verdict="Same", members=names,
            justification=rule["justification"], used=used)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--read-through", required=True)
    parser.add_argument("--takes")
    parser.add_argument("--at", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--example", type=Path, default=HERE.parent)
    arguments = parser.parse_args()
    try:
        matcher = Matcher(Pod(arguments.example.absolute(), arguments.read_through), arguments.at)
        if arguments.takes:
            matcher.take(arguments.takes)
        else:
            matcher.recheck()
    except Failure as failure:
        print(f"match.py: {failure}", file=sys.stderr)
        return 2
    for path, content in sorted(matcher.files.items()):
        target = arguments.out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
