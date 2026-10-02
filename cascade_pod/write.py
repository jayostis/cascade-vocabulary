"""Files an example's story into its pod/."""

import json
import re
import shutil
import sys
from collections import defaultdict

from rdflib import BNode, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from . import Failure, apple_health, names, store, turtle
from .pod import RECORD_FOLDERS, fanned, save, stem

BRIDGE, PAV, PROV, RDFS, REC = (Namespace(turtle.PREFIXES[p]) for p in ("bridge", "pav", "prov", "rdfs", "rec"))
DRAFT_OUTPUT = re.compile(r"^urn:cascade:output-(\d+)$")
OWNED_POD_FOLDERS = ["subject", "records", "provenance", "attachments"]


def closure(graph, subject):
    found = set()
    for triple in graph.triples((subject, None, None)):
        found.add(triple)
        if isinstance(triple[2], BNode):
            found |= closure(graph, triple[2])
    return found


# The pod as it grows

class Filing:
    def __init__(self, example):
        self.example = example
        self.files = {}
        self.records = {}
        self.stored = set()
        self.revisions = []
        self.first_records = {}
        self.activities = {}

    def add(self, event, path, content):
        if path in self.files and self.files[path][1] != content:
            raise Failure(f"{path} would be written twice with different content")
        if path not in self.files:
            self.files[path] = (event, content)

    def add_turtle(self, event, path, triples):
        self.add(event, path, turtle.write(triples, self.example.address + path))

    def revise(self, event, record, version, content, generated_at, generated_by, folder):
        history = self.records[record]["revisions"]
        this = URIRef(names.THIS_REVISION)
        triples = {(this, p, o) for p, o in content}
        triples |= {
            (this, RDF.type, REC.Revision),
            (this, REC.revisionOf, URIRef(record)),
            (this, REC.version, URIRef(version)),
            (this, PROV.generatedAtTime, Literal(generated_at, datatype=XSD.dateTime)),
            (this, PROV.wasGeneratedBy, URIRef(generated_by)),
        }
        if history:
            triples.add((this, PROV.wasRevisionOf, URIRef(history[-1]["name"])))
        name = names.content(triples)
        named = {(URIRef(name), p, o) for _, p, o in triples}
        source_version = next((str(o) for p, o in content if p == PAV.version), None)
        document = next((str(o) for p, o in content if p == PROV.wasDerivedFrom), None)
        selector = next((str(o) for p, o in content if p == BRIDGE.selector), None)
        history.append({"name": name, "version": version, "source_version": source_version})
        self.revisions.append({"record": record, "name": name, "version": version,
                               "document": document, "selector": selector})
        self.add_turtle(event, fanned(f"records/{folder}", name), named)


def file_subject(filing, event):
    subject = URIRef(event["subject"])
    filing.add_turtle(event["event"], fanned("subject", str(subject)), {(subject, RDF.type, REC.Subject)})


def file_entry(filing, event):
    graph = store.parsed(filing.example.folder / event["entry"])
    activities = list(graph.subjects(RDF.type, PROV.Activity))
    if len(activities) != 1:
        raise Failure(f"{event['entry']} holds {len(activities)} activities, not one")
    activity = activities[0]
    filing.activities[event["entry"]] = str(activity)
    filing.add_turtle(event["event"], fanned("provenance/activities", str(activity)), closure(graph, activity))
    drafts = {}
    for draft in set(graph.subjects(RDF.type, None)):
        position = DRAFT_OUTPUT.match(str(draft))
        if position:
            drafts[draft] = URIRef(names.record([str(activity), position.group(1)]))
    placeholder = URIRef(names.THIS_VERSION)
    for draft_version in sorted(set(graph.subjects(PROV.specializationOf, None)), key=str):
        draft_record = graph.value(draft_version, PROV.specializationOf)
        record, kind = drafts[draft_record], graph.value(draft_record, RDF.type)
        folder = RECORD_FOLDERS[str(kind)]
        content = {(placeholder, p, drafts.get(o, o)) for p, o in graph.predicate_objects(draft_version)}
        version = URIRef(names.content(content))
        filing.records.setdefault(str(record), {"folder": folder, "revisions": []})
        filing.first_records.setdefault(event["entry"], str(record))
        filing.add_turtle(event["event"], fanned(f"records/{folder}", str(record)), {(record, RDF.type, kind)})
        filing.add_turtle(event["event"], fanned(f"records/{folder}", str(version)),
                          {(version, p, o) for _, p, o in content})
        filing.revise(event["event"], str(record), str(version), set(),
                      str(graph.value(activity, PROV.startedAtTime)), str(activity), folder)


def file_export(filing, event, facts_files):
    example = filing.example.folder
    export = example / event["export"]
    import_name = event.get("import")
    stored, import_descriptions, missing = [], {}, []
    for document, entry in apple_health.documents(export):
        octets = document.read_bytes()
        name = names.document(octets)
        if name in filing.stored:
            continue
        conversion = example / "conversions" / event["event"].lower() / document.stem
        facts_files[conversion / "facts.ttl"] = turtle.write(apple_health.facts(entry, event["at"]))
        if not (conversion / "graph.ttl").exists():
            missing.append(apple_health.convert_command(example.parent.parent, document, conversion))
            continue
        graph = store.parsed(conversion / "graph.ttl")
        found = (conversion / "findings.ttl").exists() and len(store.parsed(conversion / "findings.ttl"))
        if (URIRef(name), RDF.type, PROV.Entity) not in graph:
            raise Failure(f"{conversion / 'graph.ttl'} does not describe the document {name}")
        wrote = file_conversion(filing, event, graph, name, import_name, f"{export.parent.name}/{document.name}")
        if not wrote and not found:
            continue
        if import_name is None:
            raise Failure(f"{event['event']} has no import, and {document.name} would be stored")
        stored.append(name)
        filing.stored.add(name)
        filing.add(event["event"], f"attachments/sha-256/{stem(name)}", octets)
        filing.add_turtle(event["event"], fanned("provenance/documents", name), closure(graph, URIRef(name)))
        activity = next(graph.subjects(PROV.used, URIRef(name)))
        description = {(URIRef(import_name) if s == activity else s, p, o)
                       for s, p, o in closure(graph, activity) if p != PROV.used}
        import_descriptions.setdefault(turtle.write(description), description)
    if missing or not stored:
        return missing
    if len(import_descriptions) != 1:
        raise Failure(f"{event['event']}'s runs disagree on the import's label, start or association")
    description = next(iter(import_descriptions.values()))
    description |= {(URIRef(import_name), PROV.used, URIRef(name)) for name in stored}
    filing.add_turtle(event["event"], fanned("provenance/imports", import_name), description)
    return []


def _in_version(term, version):
    return term == version or str(term).startswith(str(version) + "#")


def file_conversion(filing, event, graph, document, import_name, source):
    arrivals = sorted(graph.subjects(BRIDGE.arrivedAs, None), key=lambda node: str(graph.value(node, BRIDGE.arrivedAs)))
    accounted = closure(graph, URIRef(document))
    for activity in graph.subjects(PROV.used, URIRef(document)):
        accounted |= closure(graph, activity)
    for arrival in arrivals:
        accounted |= set(graph.triples((arrival, None, None)))
    for version in set(graph.subjects(PROV.specializationOf, None)):
        accounted |= {t for t in graph if _in_version(t[0], version)}
        accounted |= set(graph.triples((graph.value(version, PROV.specializationOf), None, None)))
    if set(graph) - accounted:
        raise Failure(f"{source}'s graph holds triples of no record, version, arrival, document or import")
    wrote = False
    for arrival in arrivals:
        version = graph.value(arrival, BRIDGE.arrivedAs)
        record = graph.value(version, PROV.specializationOf)
        if record is None:
            raise Failure(f"{source}: {version} is the version of no record")
        kind = str(graph.value(record, RDF.type))
        if kind not in RECORD_FOLDERS:
            raise Failure(f"{source}: {record} is of no type the pod files: {kind}")
        folder = RECORD_FOLDERS[kind]
        filing.first_records.setdefault(source, str(record))
        history = filing.records.get(str(record), {"revisions": []})["revisions"]
        source_version = graph.value(arrival, PAV.version)
        if source_version is not None and any(r["source_version"] == str(source_version) for r in history):
            continue
        if history and history[-1]["version"] == str(version):
            continue
        if import_name is None:
            raise Failure(f"{event['event']} has no import, and {source} would write a revision")
        filing.records.setdefault(str(record), {"folder": folder, "revisions": []})
        filing.add_turtle(event["event"], fanned(f"records/{folder}", str(record)), graph.triples((record, None, None)))
        filing.add_turtle(event["event"], fanned(f"records/{folder}", str(version)),
                          {t for t in graph if _in_version(t[0], version)})
        content = {(p, o) for p, o in graph.predicate_objects(arrival)
                   if p not in (BRIDGE.arrivedAs, PROV.wasGeneratedBy)}
        started = str(graph.value(graph.value(arrival, PROV.wasGeneratedBy), PROV.startedAtTime))
        filing.revise(event["event"], str(record), str(version), content, started, import_name, folder)
        wrote = True
    return wrote


# The events manifest and the handle table

EVENT_KEYS = ["event", "at", "subject", "export", "import", "entry", "adds"]
COMPUTED_ROW = re.compile(r"^D-| [vr]\d+$")


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


def handle_table(handles, events, filing):
    table = {handle: dict(row) for handle, row in handles.items() if not COMPUTED_ROW.search(handle)}
    for handle, row in table.items():
        if "first" in row or "inputs" in row:
            row.pop("name", None)
        if row.get("inputs", [""])[0].startswith("ni:"):
            row.pop("inputs", None)
    named = {"S": next(e["subject"] for e in events if "subject" in e)}
    named.update({f"I-{e['event']}": e["import"] for e in events if "import" in e})
    named.update({f"A{n}": activity for n, activity in enumerate(filing.activities.values(), 1)})
    for handle, row in table.items():
        if "first" in row:
            if row["first"] not in filing.first_records:
                raise Failure(f"{handle}'s first arrival, {row['first']}, wrote no record")
            named[handle] = filing.first_records[row["first"]]
        elif "inputs" in row:
            named[handle] = names.record(row["inputs"])
    for handle, name in named.items():
        table.setdefault(handle, {})["name"] = name
    handle_of = {table[handle]["name"]: handle for handle in table if "first" in table[handle]}
    unnamed = set(filing.records) - set(handle_of)
    if unnamed:
        raise Failure(f"records with no handle: {sorted(unnamed)}")
    versions, counts = defaultdict(list), defaultdict(int)
    for revision in filing.revisions:
        handle = handle_of[revision["record"]]
        counts[handle] += 1
        if revision["version"] not in versions[handle]:
            versions[handle].append(revision["version"])
            table[f"{handle} v{len(versions[handle])}"] = {"name": revision["version"]}
        table[f"{handle} r{counts[handle]}"] = {"name": revision["name"]}
        if revision["document"]:
            table[f"D-{handle} r{counts[handle]}"] = {"name": revision["document"]}
            if counts[handle] == 1 and "inputs" not in table[handle]:
                table[handle]["inputs"] = [revision["document"], revision["selector"]]
    return {handle: {key: table[handle][key] for key in sorted(table[handle])} for handle in sorted(table)}


# One run

def run(example):
    handles = json.loads((example.folder / "handles.json").read_text(encoding="utf-8"))
    filing, facts_files, missing = Filing(example), {}, []
    for event in example.events:
        if "subject" in event:
            file_subject(filing, event)
        elif "entry" in event:
            file_entry(filing, event)
        elif "export" in event:
            missing = file_export(filing, event, facts_files)
            if missing:
                break
    for old in example.folder.glob("conversions/*/*/facts.ttl"):
        old.unlink()
    for path, content in facts_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    if missing:
        print("\n\n".join(missing))
        print(f"{len(missing)} conversions to run from the repository root, then run this again", file=sys.stderr)
        return 1
    for folder_name in OWNED_POD_FOLDERS:
        shutil.rmtree(example.pod / folder_name, ignore_errors=True)
    save({path: content for path, (_, content) in filing.files.items()}, example.pod)
    write_json(example.folder / "events.json", events_manifest(example, filing))
    write_json(example.folder / "handles.json", handle_table(handles, example.events, filing))
    return 0
