"""Files an example's story into its pod/."""

import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ElementTree
from collections import defaultdict
from datetime import datetime, timezone

from rdflib import BNode, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from . import Failure, names, store, turtle
from .pod import RECORD_FOLDERS, Example, fanned, stem

BRIDGE, PAV, PROV, RDFS, REC = (Namespace(turtle.PREFIXES[p]) for p in ("bridge", "pav", "prov", "rdfs", "rec"))
DRAFT_OUTPUT = re.compile(r"^urn:cascade:output-(\d+)$")
OWNED_POD_FOLDERS = ["subject", "records", "provenance", "attachments"]
ADAPTER = "<cascade-bridge-adapter-fhir-r4>"
VOCABULARIES = "<cascade-vocabulary at the adapter's pin>"
TRANSMITTER = "Apple Health"
IMPORT_LABEL = "Apple Health export"
FORMATS = {".csv": "text/csv", ".json": "application/json", ".py": "text/x-python",
           ".ttl": "text/turtle", ".xml": "application/xml"}


def closure(graph, subject):
    found = set()
    for triple in graph.triples((subject, None, None)):
        found.add(triple)
        if isinstance(triple[2], BNode):
            found |= closure(graph, triple[2])
    return found


# An Apple Health export

def clinical_records(export_xml):
    root = ElementTree.parse(export_xml).getroot()
    return {entry.get("resourceFilePath"): dict(entry.attrib) for entry in root.iter("ClinicalRecord")}


def utc(apple_date):
    moment = datetime.strptime(apple_date, "%Y-%m-%d %H:%M:%S %z").astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _attribution(document, label, role):
    attribution, agent = BNode(), BNode()
    return {(document, PROV.qualifiedAttribution, attribution), (attribution, PROV.agent, agent),
            (agent, RDFS.label, Literal(label)), (attribution, PROV.hadRole, role)}


def facts(entry, import_started_at):
    """What the export says of one document and of its import, for the Bridge to state."""
    document, this_import = BRIDGE.thisDocument, BRIDGE.thisImport
    triples = {(this_import, RDFS.label, Literal(IMPORT_LABEL)),
               (this_import, PROV.startedAtTime, Literal(import_started_at, datatype=XSD.dateTime)),
               *_attribution(document, TRANSMITTER, REC.transmitter)}
    if entry is not None:
        source_url = entry["sourceURL"]
        triples |= {*_attribution(document, entry["sourceName"], REC.author),
                    (document, BRIDGE.serverBaseUrl, Literal(source_url.rsplit("/", 2)[0])),
                    (document, PAV.retrievedFrom, URIRef(source_url)),
                    (document, PAV.retrievedOn, Literal(utc(entry["receivedDate"]), datatype=XSD.dateTime)),
                    (document, BRIDGE.sourceFormatVersion, Literal(entry["fhirVersion"]))}
    return triples


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


def convert_command(repository, document, conversion):
    def relative(path):
        return path.relative_to(repository).as_posix()

    return " \\\n  ".join([
        f"cascade-bridge convert {ADAPTER}",
        relative(document),
        "--envelope '#envelope-resource'",
        f"--facts {relative(conversion / 'facts.ttl')}",
        f"--vocabularies {VOCABULARIES}",
        f"--out {relative(conversion / 'graph.ttl')}",
        f"--findings {relative(conversion / 'findings.ttl')}",
    ])


def file_export(filing, event, facts_files):
    example = filing.example.folder
    export = example / event["export"]
    entries = clinical_records(export / "export.xml")
    documents = sorted(export.glob("clinical-records/*.json"), key=lambda path: f"/clinical-records/{path.name}")
    import_name = event.get("import")
    stored, import_descriptions, missing = [], {}, []
    for document in documents:
        octets = document.read_bytes()
        name = names.document(octets)
        if name in filing.stored:
            continue
        conversion = example / "conversions" / event["event"].lower() / document.stem
        entry = entries.get(f"/clinical-records/{document.name}")
        facts_files[conversion / "facts.ttl"] = turtle.write(facts(entry, event["at"]))
        if not (conversion / "graph.ttl").exists():
            missing.append(convert_command(example.parent.parent, document, conversion))
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


# The events manifest, the handle table and the crate

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


def encoding_format(relative, path):
    if relative == "pod/.well-known/solid":
        return "application/ld+json"
    if relative == "pod/settings/preferences":
        return "text/turtle"
    if relative.startswith("pod/attachments/sha-256/") or (relative.startswith("downloads/") and path.suffix == ".json"):
        return "application/fhir+json"
    return FORMATS.get(path.suffix, "application/octet-stream")


def _is_file(entity):
    kinds = entity.get("@type")
    return "File" in (kinds if isinstance(kinds, list) else [kinds])


def crate_with_files(crate, example):
    found = {entity["@id"]: entity for entity in crate["@graph"] if _is_file(entity)}
    descriptor = next(e for e in crate["@graph"] if e["@id"] == "ro-crate-metadata.json")
    root = next(e for e in crate["@graph"] if e["@id"] == "./")
    others = [e for e in crate["@graph"] if not _is_file(e) and e["@id"] not in ("ro-crate-metadata.json", "./")]
    files = []
    for path in sorted(example.rglob("*"), key=lambda p: p.relative_to(example).as_posix()):
        relative = path.relative_to(example).as_posix()
        if not path.is_file() or relative == "ro-crate-metadata.json" or "__pycache__" in path.parts:
            continue
        octets = path.read_bytes()
        entity = {"@id": relative, "@type": "File", "encodingFormat": encoding_format(relative, path),
                  "contentSize": str(len(octets)), "sha256": hashlib.sha256(octets).hexdigest()}
        kept = found.get(relative, {})
        entity.update({key: kept[key] for key in kept if key not in entity or key == "@type"})
        files.append(entity)
    root = {**root, "hasPart": [{"@id": entity["@id"]} for entity in files]}
    return {**crate, "@graph": [descriptor, root, *files, *others]}


# One run

def run(folder):
    example = Example(folder)
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
    for path, (_, content) in sorted(filing.files.items()):
        target = example.pod / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    write_json(example.folder / "events.json", events_manifest(example, filing))
    write_json(example.folder / "handles.json", handle_table(handles, example.events, filing))
    crate = json.loads((example.folder / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    write_json(example.folder / "ro-crate-metadata.json", crate_with_files(crate, example.folder))
    return 0
