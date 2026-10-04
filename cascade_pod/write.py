"""Files an example's story into its pod/."""

import json
import re
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property

from rdflib import BNode, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from . import Failure, apple_health, names, store, turtle
from .pod import RECORD_FOLDERS, fanned, save, stem

BRIDGE, PAV, PROV, REC = (Namespace(turtle.PREFIXES[p]) for p in ("bridge", "pav", "prov", "rec"))
DRAFT_OUTPUT = re.compile(r"^urn:cascade:output-(\d+)$")
OWNED_POD_FOLDERS = ["subject", "records", "provenance", "attachments"]


def closure(graph, subject):
    found = set()
    for triple in graph.triples((subject, None, None)):
        found.add(triple)
        if isinstance(triple[2], BNode):
            found |= closure(graph, triple[2])
    return found


def in_version(term, version):
    return term == version or str(term).startswith(str(version) + "#")


def records_folder(source, record, kind):
    if str(kind) not in RECORD_FOLDERS:
        raise Failure(f"{source}: {record} is of no type the pod files: {kind}")
    return f"records/{RECORD_FOLDERS[str(kind)]}"


# What a revision sets

@dataclass(frozen=True)
class Revision:
    record: URIRef
    folder: str
    record_triples: frozenset
    version: URIRef
    version_triples: frozenset
    statements: frozenset
    at: str
    by: str

    @property
    def source_version(self):
        return next((str(o) for p, o in self.statements if p == PAV.version), None)

    def triples(self, previous):
        this = URIRef(names.THIS_REVISION)
        return {(this, p, o) for p, o in self.statements} | {
            (this, RDF.type, REC.Revision),
            (this, REC.revisionOf, self.record),
            (this, REC.version, self.version),
            (this, PROV.generatedAtTime, Literal(self.at, datatype=XSD.dateTime, normalize=False)),
            (this, PROV.wasGeneratedBy, URIRef(self.by)),
        } | ({(this, PROV.wasRevisionOf, previous)} if previous else set())


# The pod as it grows

class Filing:
    def __init__(self, example):
        self.example = example
        self.files = {}
        self.stored = set()
        self.last_revision = {}
        self.last_version = {}
        self.source_versions = defaultdict(set)

    def add(self, event, path, content):
        if path in self.files and self.files[path][1] != content:
            raise Failure(f"{path} would be written twice with different content")
        if path not in self.files:
            self.files[path] = (event, content)

    def add_turtle(self, event, path, triples):
        self.add(event, path, turtle.write(triples, self.example.address + path))

    def revise(self, event, revision):
        self.add_turtle(event, fanned(revision.folder, str(revision.record)), revision.record_triples)
        self.add_turtle(event, fanned(revision.folder, str(revision.version)), revision.version_triples)
        triples = revision.triples(self.last_revision.get(revision.record))
        name = URIRef(names.content(triples))
        self.add_turtle(event, fanned(revision.folder, str(name)), {(name, p, o) for _, p, o in triples})
        self.last_revision[revision.record] = name
        self.last_version[revision.record] = revision.version
        self.source_versions[revision.record].add(revision.source_version)


# A subject and an entry

def file_subject(filing, event):
    subject = URIRef(event["subject"])
    filing.add_turtle(event["event"], fanned("subject", str(subject)), {(subject, RDF.type, REC.Subject)})


def file_entry(filing, event):
    graph = store.parsed(filing.example.folder / event["entry"])
    activities = list(graph.subjects(RDF.type, PROV.Activity))
    if len(activities) != 1:
        raise Failure(f"{event['entry']} holds {len(activities)} activities, not one")
    activity = activities[0]
    filing.add_turtle(event["event"], fanned("provenance/activities", str(activity)), closure(graph, activity))
    for revision in entry_revisions(graph, activity, event["entry"]):
        filing.revise(event["event"], revision)


def entry_revisions(graph, activity, source):
    records = {draft: URIRef(names.record([str(activity), position.group(1)]))
               for draft in set(graph.subjects(RDF.type, None))
               for position in [DRAFT_OUTPUT.match(str(draft))] if position}
    placeholder = URIRef(names.THIS_VERSION)
    for draft_version in sorted(set(graph.subjects(PROV.specializationOf, None)), key=str):
        draft_record = graph.value(draft_version, PROV.specializationOf)
        record, kind = records[draft_record], graph.value(draft_record, RDF.type)
        content = {(placeholder, p, records.get(o, o)) for p, o in graph.predicate_objects(draft_version)}
        version = URIRef(names.content(content))
        yield Revision(
            record=record, folder=records_folder(source, record, kind), record_triples=frozenset({(record, RDF.type, kind)}),
            version=version, version_triples=frozenset((version, p, o) for _, p, o in content),
            statements=frozenset(), at=str(graph.value(activity, PROV.startedAtTime)), by=str(activity))


# An export: each of its files, and what the Bridge made of it

class Conversion:
    def __init__(self, example, event, path, entry):
        self.path, self.entry, self.import_started_at = path, entry, event["at"]
        self.repository = example.folder.parent.parent
        self.octets = path.read_bytes()
        self.document = URIRef(names.document(self.octets))
        self.folder = example.folder / "conversions" / event["event"].lower() / path.stem
        self.source = f"{(example.folder / event['export']).parent.name}/{path.name}"

    @property
    def facts(self):
        return turtle.write(apple_health.facts(self.entry, self.import_started_at))

    @property
    def command(self):
        return apple_health.convert_command(self.repository, self.path, self.folder)

    @cached_property
    def graph(self):
        return store.parsed(self.folder / "graph.ttl")

    @cached_property
    def has_findings(self):
        return (self.folder / "findings.ttl").exists() and len(store.parsed(self.folder / "findings.ttl")) > 0

    def revisions(self, import_name):
        graph = self.graph
        for arrival in sorted(graph.subjects(BRIDGE.arrivedAs, None), key=lambda a: str(graph.value(a, BRIDGE.arrivedAs))):
            version = graph.value(arrival, BRIDGE.arrivedAs)
            record = graph.value(version, PROV.specializationOf)
            if record is None:
                raise Failure(f"{self.source}: {version} is the version of no record")
            yield Revision(
                record=record, folder=records_folder(self.source, record, graph.value(record, RDF.type)),
                record_triples=frozenset(graph.triples((record, None, None))),
                version=version, version_triples=frozenset(t for t in graph if in_version(t[0], version)),
                statements=frozenset((p, o) for p, o in graph.predicate_objects(arrival)
                                     if p not in (BRIDGE.arrivedAs, PROV.wasGeneratedBy)),
                at=str(graph.value(graph.value(arrival, PROV.wasGeneratedBy), PROV.startedAtTime)), by=import_name)

    def import_description(self, import_name):
        activity = next(self.graph.subjects(PROV.used, self.document))
        return {(URIRef(import_name) if s == activity else s, p, o)
                for s, p, o in closure(self.graph, activity) if p != PROV.used}


def file_export(filing, event, facts_files):
    to_convert, kept = [], {}
    for path, entry in apple_health.documents(filing.example.folder / event["export"]):
        conversion = Conversion(filing.example, event, path, entry)
        if brings_nothing_new(filing, conversion):
            continue
        facts_files[conversion.folder / "facts.ttl"] = conversion.facts
        if not is_converted(conversion):
            to_convert.append(conversion.command)
            continue
        refuse_unaccounted_statements(conversion)
        wrote = file_revisions(filing, event, conversion)
        if is_kept(conversion, wrote):
            kept[conversion.document] = keep(filing, event, conversion)
    if kept and not to_convert:
        file_import(filing, event, kept)
    return to_convert


def brings_nothing_new(filing, conversion):
    return conversion.document in filing.stored


def is_converted(conversion):
    return (conversion.folder / "graph.ttl").exists()


def refuse_unaccounted_statements(conversion):
    if (conversion.document, RDF.type, PROV.Entity) not in conversion.graph:
        raise Failure(f"{conversion.folder / 'graph.ttl'} does not describe the document {conversion.document}")
    if set(conversion.graph) - accounted_for(conversion.graph, conversion.document):
        raise Failure(f"{conversion.source}'s graph holds triples of no record, version, arrival, document or import")


def accounted_for(graph, document):
    found = closure(graph, document)
    for activity in graph.subjects(PROV.used, document):
        found |= closure(graph, activity)
    for arrival in graph.subjects(BRIDGE.arrivedAs, None):
        found |= set(graph.triples((arrival, None, None)))
    for version in set(graph.subjects(PROV.specializationOf, None)):
        found |= {t for t in graph if in_version(t[0], version)}
        found |= set(graph.triples((graph.value(version, PROV.specializationOf), None, None)))
    return found


def file_revisions(filing, event, conversion):
    wrote = False
    for revision in conversion.revisions(event.get("import")):
        if writes_a_revision(filing, revision):
            if revision.by is None:
                raise Failure(f"{event['event']} has no import, and {conversion.source} would write a revision")
            filing.revise(event["event"], revision)
            wrote = True
    return wrote


def writes_a_revision(filing, revision):
    return not repeats_a_source_version(filing, revision) and not sets_the_version_it_holds(filing, revision)


def repeats_a_source_version(filing, revision):
    return revision.source_version is not None and revision.source_version in filing.source_versions[revision.record]


def sets_the_version_it_holds(filing, revision):
    return filing.last_version.get(revision.record) == revision.version


def is_kept(conversion, wrote):
    return conversion.has_findings or wrote


def keep(filing, event, conversion):
    if event.get("import") is None:
        raise Failure(f"{event['event']} has no import, and {conversion.path.name} would be stored")
    filing.stored.add(conversion.document)
    filing.add(event["event"], f"attachments/sha-256/{stem(conversion.document)}", conversion.octets)
    filing.add_turtle(event["event"], fanned("provenance/documents", conversion.document),
                      closure(conversion.graph, conversion.document))
    return conversion.import_description(event["import"])


def file_import(filing, event, kept):
    descriptions = list(kept.values())
    if len({turtle.write(description) for description in descriptions}) != 1:
        raise Failure(f"{event['event']}'s runs disagree on the import's label, start or association")
    used = {(URIRef(event["import"]), PROV.used, document) for document in kept}
    filing.add_turtle(event["event"], fanned("provenance/imports", event["import"]), descriptions[0] | used)


# The events manifest

EVENT_KEYS = ["event", "at", "subject", "export", "import", "entry", "adds"]


def owned(path):
    return path.split("/", 1)[0] in OWNED_POD_FOLDERS


def write_json(path, value):
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def events_manifest(example, filing):
    events = []
    for event in example.events:
        adds = [path for path in event["adds"] if not owned(path)]
        adds += [path for path, (added_by, _) in filing.files.items() if added_by == event["event"]]
        event = {**event, "adds": sorted(adds)}
        events.append({key: event[key] for key in EVENT_KEYS + sorted(set(event) - set(EVENT_KEYS)) if key in event})
    return {"address": example.address, "events": events, "derived": sorted(example.derived)}


# One run

def run(example):
    filing, facts_files, to_convert = file_story(example)
    write_facts(example, facts_files)
    if to_convert:
        print("\n\n".join(to_convert))
        print(f"{len(to_convert)} conversions to run from the repository root, then run this again", file=sys.stderr)
        return 1
    write_pod(example, filing)
    return 0


def file_story(example):
    filing, facts_files = Filing(example), {}
    for event in example.events:
        if "subject" in event:
            file_subject(filing, event)
        elif "entry" in event:
            file_entry(filing, event)
        elif "export" in event:
            to_convert = file_export(filing, event, facts_files)
            if to_convert:
                return filing, facts_files, to_convert
    return filing, facts_files, []


def write_facts(example, facts_files):
    for old in example.folder.glob("conversions/*/*/facts.ttl"):
        old.unlink()
    for path, content in facts_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def write_pod(example, filing):
    for folder in OWNED_POD_FOLDERS:
        shutil.rmtree(example.pod / folder, ignore_errors=True)
    save({path: content for path, (_, content) in filing.files.items()}, example.pod)
    write_json(example.folder / "events.json", events_manifest(example, filing))
