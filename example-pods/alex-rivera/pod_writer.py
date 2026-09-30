"""Files Alex Rivera's story, E1 to E15, into pod/.

python3 example-pods/alex-rivera/pod_writer.py [--example <directory>]
"""

import argparse
import base64
import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import rdflib
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

rdflib.NORMALIZE_LITERALS = False
sys.path.insert(0, str(Path(__file__).absolute().parent))
from entry_facts import clinical_records, facts  # noqa: E402

POD_BASE = "https://pod.alex-rivera.example/"
RECORD_NAMESPACE = "90c60849-c5ef-4ca6-bfb8-8662bd07d2b5"
THIS_REVISION = "urn:cascade:this-revision"
DRAFT_OUTPUT = re.compile(r"^urn:cascade:output-(\d+)$")

PREFIXES = {
    "bridge": "https://ns.cascadeprotocol.org/bridge/v1-draft#",
    "clinical": "https://ns.cascadeprotocol.org/clinical/v1#",
    "health": "https://ns.cascadeprotocol.org/health/v1#",
    "jdg": "https://ns.cascadeprotocol.org/judgments/v1-draft#",
    "pav": "http://purl.org/pav/",
    "prov": "http://www.w3.org/ns/prov#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rec": "https://ns.cascadeprotocol.org/records/v1-draft#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
BRIDGE, PAV, PROV, RDFS, REC = (PREFIXES[p] for p in ("bridge", "pav", "prov", "rdfs", "rec"))
ARRIVED_AS = URIRef(BRIDGE + "arrivedAs")
SPECIALIZATION_OF = URIRef(PROV + "specializationOf")
GENERATED_BY = URIRef(PROV + "wasGeneratedBy")
DERIVED_FROM = URIRef(PROV + "wasDerivedFrom")
USED = URIRef(PROV + "used")
STARTED = URIRef(PROV + "startedAtTime")
ASSOCIATION = URIRef(PROV + "qualifiedAssociation")
LABEL = URIRef(RDFS + "label")
VERSION_OF_SOURCE = URIRef(PAV + "version")

FOLDERS = {
    PREFIXES["health"] + "AllergyRecord": "allergies",
    PREFIXES["health"] + "ConditionRecord": "conditions",
    PREFIXES["health"] + "ImmunizationRecord": "immunizations",
    PREFIXES["clinical"] + "Procedure": "procedures",
}
OWNED_POD_FOLDERS = ["subject", "records", "provenance", "attachments"]
ADAPTER = "<cascade-bridge-adapter-fhir-r4>"
VOCABULARIES = "<cascade-vocabulary at the adapter's pin>"
FORMATS = {".csv": "text/csv", ".json": "application/json", ".py": "text/x-python", ".rq": "application/sparql-query",
           ".ttl": "text/turtle", ".xml": "application/xml"}


class Failure(Exception):
    pass


# Names

def record_name(inputs):
    digest = bytearray(hashlib.sha256("|".join([RECORD_NAMESPACE, *inputs]).encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    text = digest.hex()
    return f"urn:uuid:{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def digest_name(octets):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode("ascii").rstrip("=")


def file_stem(name):
    if name.startswith("urn:uuid:"):
        return name[len("urn:uuid:"):]
    if name.startswith("ni:///sha-256;"):
        encoded = name[len("ni:///sha-256;"):]
        return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).hex()
    raise Failure(f"no file name for {name}")


def fanned(folder, name):
    stem = file_stem(name)
    return f"{folder}/{stem[:2]}/{stem}.ttl"


def _nquads_term(term):
    if isinstance(term, URIRef):
        return f"<{term}>"
    if isinstance(term, Literal):
        text = str(term).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
        if term.language:
            return f'"{text}"@{term.language}'
        if term.datatype is None or str(term.datatype) == str(XSD.string):
            return f'"{text}"'
        return f'"{text}"^^<{term.datatype}>'
    raise Failure(f"a revision holds a blank node: {term}")


def revision_name(triples):
    lines = {" ".join(_nquads_term(term) for term in triple) + " .\n" for triple in triples}
    return digest_name("".join(sorted(lines)).encode("utf-8"))


# Turtle, written by hand so that a rerun gives the same bytes

def _curie(iri, used):
    for prefix, namespace in PREFIXES.items():
        local = iri[len(namespace):]
        if iri.startswith(namespace) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", local):
            used.add(prefix)
            return f"{prefix}:{local}"
    return f"<{iri}>"


def _string(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    return f'"{escaped}"'


def _term(term, triples, used):
    if isinstance(term, URIRef):
        return "a" if term == RDF.type else _curie(str(term), used)
    if isinstance(term, Literal):
        if term.language:
            return f"{_string(str(term))}@{term.language}"
        if term.datatype is None or term.datatype == XSD.string:
            return _string(str(term))
        return f"{_string(str(term))}^^{_curie(str(term.datatype), used)}"
    statements = _statements(term, triples, used)
    return "[ " + " ; ".join(f"{p} {', '.join(objects)}" for p, objects in statements) + " ]"


def _statements(subject, triples, used):
    by_predicate = defaultdict(list)
    for s, p, o in triples:
        if s == subject:
            by_predicate[p].append(o)
    return [(_term(p, triples, used), sorted(_term(o, triples, used) for o in by_predicate[p]))
            for p in sorted(by_predicate, key=str)]


def turtle(triples):
    triples = set(triples)
    objects = [o for _, _, o in triples if isinstance(o, BNode)]
    if len(objects) != len(set(objects)):
        raise Failure("a blank node is the object of more than one triple")
    subjects = sorted({s for s, _, _ in triples if not isinstance(s, BNode)}, key=str)
    reached = set()

    def reach(node):
        for s, _, o in triples:
            if s == node and isinstance(o, BNode) and o not in reached:
                reached.add(o)
                reach(o)

    for subject in subjects:
        reach(subject)
    if {s for s, _, _ in triples if isinstance(s, BNode)} - reached:
        raise Failure("a blank node no named subject leads to")
    used, blocks = set(), []
    for subject in subjects:
        lines = [_term(subject, triples, used)]
        statements = _statements(subject, triples, used)
        for index, (predicate, values) in enumerate(statements):
            end = " ." if index == len(statements) - 1 else " ;"
            if len(values) == 1:
                lines.append(f"  {predicate} {values[0]}{end}")
            else:
                lines.append(f"  {predicate}")
                lines += [f"    {value}{end if i == len(values) - 1 else ' ,'}" for i, value in enumerate(values)]
        blocks.append("\n".join(lines))
    head = "".join(f"@prefix {prefix}: <{PREFIXES[prefix]}> .\n" for prefix in sorted(used))
    return (head + "\n" + "\n\n".join(blocks) + "\n").encode("utf-8")


def closure(graph, subject):
    found = set()
    for triple in graph.triples((subject, None, None)):
        found.add(triple)
        if isinstance(triple[2], BNode):
            found |= closure(graph, triple[2])
    return found


# The pod as it grows

class Pod:
    def __init__(self):
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

    def revise(self, event, record, version, content, generated_at, generated_by, folder):
        history = self.records[record]["revisions"]
        triples = {(URIRef(THIS_REVISION), p, o) for p, o in content}
        triples |= {
            (URIRef(THIS_REVISION), RDF.type, URIRef(REC + "Revision")),
            (URIRef(THIS_REVISION), URIRef(REC + "revisionOf"), URIRef(record)),
            (URIRef(THIS_REVISION), URIRef(REC + "version"), URIRef(version)),
            (URIRef(THIS_REVISION), URIRef(PROV + "generatedAtTime"), Literal(generated_at, datatype=XSD.dateTime)),
            (URIRef(THIS_REVISION), GENERATED_BY, URIRef(generated_by)),
        }
        if history:
            triples.add((URIRef(THIS_REVISION), URIRef(PROV + "wasRevisionOf"), URIRef(history[-1]["name"])))
        name = revision_name(triples)
        named = {(URIRef(name), p, o) for _, p, o in triples}
        source_version = next((str(o) for p, o in content if p == VERSION_OF_SOURCE), None)
        document = next((str(o) for p, o in content if p == DERIVED_FROM), None)
        selector = next((str(o) for p, o in content if p == URIRef(BRIDGE + "selector")), None)
        history.append({"name": name, "version": version, "source_version": source_version})
        self.revisions.append({"record": record, "name": name, "version": version,
                               "document": document, "selector": selector})
        self.add(event, fanned(f"records/{folder}", name), turtle(named))


def file_subject(pod, event):
    subject = URIRef(event["subject"])
    pod.add(event["event"], fanned("subject", str(subject)), turtle({(subject, RDF.type, URIRef(REC + "Subject"))}))


def file_entry(pod, event, example):
    graph = Graph().parse(example / event["entry"], format="turtle")
    activities = list(graph.subjects(RDF.type, URIRef(PROV + "Activity")))
    if len(activities) != 1:
        raise Failure(f"{event['entry']} holds {len(activities)} activities, not one")
    activity = activities[0]
    pod.activities[event["entry"]] = str(activity)
    pod.add(event["event"], fanned("provenance/activities", str(activity)), turtle(closure(graph, activity)))
    names = {}
    for draft in set(graph.subjects(RDF.type, None)):
        position = DRAFT_OUTPUT.match(str(draft))
        if position:
            names[draft] = URIRef(record_name([str(activity), position.group(1)]))
    placeholder = URIRef("urn:cascade:this-version")
    for draft_version in sorted(set(graph.subjects(SPECIALIZATION_OF, None)), key=str):
        draft_record = graph.value(draft_version, SPECIALIZATION_OF)
        record, kind = names[draft_record], graph.value(draft_record, RDF.type)
        folder = FOLDERS[str(kind)]
        content = {(placeholder, p, names.get(o, o)) for p, o in graph.predicate_objects(draft_version)}
        version = URIRef(digest_name(canonical(content).encode("utf-8")))
        pod.records.setdefault(str(record), {"folder": folder, "revisions": []})
        pod.first_records.setdefault(event["entry"], str(record))
        pod.add(event["event"], fanned(f"records/{folder}", str(record)), turtle({(record, RDF.type, kind)}))
        pod.add(event["event"], fanned(f"records/{folder}", str(version)), turtle({(version, p, o) for _, p, o in content}))
        pod.revise(event["event"], str(record), str(version), set(), str(graph.value(activity, STARTED)), str(activity), folder)


def canonical(triples):
    return "".join(sorted({" ".join(_nquads_term(term) for term in triple) + " .\n" for triple in triples}))


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


def file_export(pod, event, example, facts_files):
    export = example / event["export"]
    entries = clinical_records(export / "export.xml")
    documents = sorted(export.glob("clinical-records/*.json"), key=lambda path: f"/clinical-records/{path.name}")
    import_name = event.get("import")
    stored, import_descriptions, missing = [], {}, []
    for document in documents:
        octets = document.read_bytes()
        name = digest_name(octets)
        if name in pod.stored:
            continue
        conversion = example / "conversions" / event["event"].lower() / document.stem
        entry = entries.get(f"/clinical-records/{document.name}")
        facts_files[conversion / "facts.ttl"] = facts(entry, event["at"]).encode("utf-8")
        if not (conversion / "graph.ttl").exists():
            missing.append(convert_command(example.parent.parent, document, conversion))
            continue
        graph = Graph().parse(conversion / "graph.ttl", format="turtle")
        findings = Graph()
        if (conversion / "findings.ttl").exists():
            findings.parse(conversion / "findings.ttl", format="turtle")
        if (URIRef(name), RDF.type, URIRef(PROV + "Entity")) not in graph:
            raise Failure(f"{conversion / 'graph.ttl'} does not describe the document {name}")
        wrote = file_conversion(pod, event, graph, name, import_name, f"{export.parent.name}/{document.name}")
        if not wrote and not len(findings):
            continue
        if import_name is None:
            raise Failure(f"{event['event']} has no import, and {document.name} would be stored")
        stored.append(name)
        pod.stored.add(name)
        pod.add(event["event"], f"attachments/sha-256/{file_stem(name)}", octets)
        pod.add(event["event"], fanned("provenance/documents", name), turtle(closure(graph, URIRef(name))))
        activity = next(graph.subjects(USED, URIRef(name)))
        description = {(URIRef(import_name) if s == activity else s, p, o)
                       for s, p, o in closure(graph, activity) if p != USED}
        import_descriptions.setdefault(turtle(description), description)
    if missing or not stored:
        return missing
    if len(import_descriptions) != 1:
        raise Failure(f"{event['event']}'s runs disagree on the import's label, start or association")
    description = next(iter(import_descriptions.values()))
    description |= {(URIRef(import_name), USED, URIRef(name)) for name in stored}
    pod.add(event["event"], fanned("provenance/imports", import_name), turtle(description))
    return []


def _in_version(term, version):
    return term == version or str(term).startswith(str(version) + "#")


def file_conversion(pod, event, graph, document, import_name, source):
    arrivals = sorted(graph.subjects(ARRIVED_AS, None), key=lambda node: str(graph.value(node, ARRIVED_AS)))
    accounted = closure(graph, URIRef(document))
    for activity in graph.subjects(USED, URIRef(document)):
        accounted |= closure(graph, activity)
    for arrival in arrivals:
        accounted |= set(graph.triples((arrival, None, None)))
    for version in set(graph.subjects(SPECIALIZATION_OF, None)):
        accounted |= {t for t in graph if _in_version(t[0], version)}
        accounted |= set(graph.triples((graph.value(version, SPECIALIZATION_OF), None, None)))
    if set(graph) - accounted:
        raise Failure(f"{source}'s graph holds triples of no record, version, arrival, document or import")
    wrote = False
    for arrival in arrivals:
        version = graph.value(arrival, ARRIVED_AS)
        record = graph.value(version, SPECIALIZATION_OF)
        if record is None:
            raise Failure(f"{source}: {version} is the version of no record")
        kind = str(graph.value(record, RDF.type))
        if kind not in FOLDERS:
            raise Failure(f"{source}: {record} is of no type the pod files: {kind}")
        folder = FOLDERS[kind]
        pod.first_records.setdefault(source, str(record))
        history = pod.records.get(str(record), {"revisions": []})["revisions"]
        source_version = graph.value(arrival, VERSION_OF_SOURCE)
        if source_version is not None and any(r["source_version"] == str(source_version) for r in history):
            continue
        if history and history[-1]["version"] == str(version):
            continue
        if import_name is None:
            raise Failure(f"{event['event']} has no import, and {source} would write a revision")
        pod.records.setdefault(str(record), {"folder": folder, "revisions": []})
        pod.add(event["event"], fanned(f"records/{folder}", str(record)), turtle(graph.triples((record, None, None))))
        pod.add(event["event"], fanned(f"records/{folder}", str(version)),
                turtle({t for t in graph if _in_version(t[0], version)}))
        content = {(p, o) for p, o in graph.predicate_objects(arrival) if p not in (ARRIVED_AS, GENERATED_BY)}
        started = str(graph.value(graph.value(arrival, GENERATED_BY), STARTED))
        pod.revise(event["event"], str(record), str(version), content, started, import_name, folder)
        wrote = True
    return wrote


# The events manifest, the handle table and the crate

EVENT_KEYS = ["event", "at", "subject", "export", "import", "entry", "adds"]
COMPUTED_ROW = re.compile(r"^D-| [vr]\d+$")


def owned(path):
    return path.split("/", 1)[0] in OWNED_POD_FOLDERS


def write_json(path, value):
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def events_manifest(manifest, pod):
    events = []
    for event in manifest["events"]:
        adds = [path for path in event["adds"] if not owned(path)]
        adds += [path for path, (added_by, _) in pod.files.items() if added_by == event["event"]]
        event = {**event, "adds": sorted(adds)}
        events.append({key: event[key] for key in EVENT_KEYS + sorted(set(event) - set(EVENT_KEYS)) if key in event})
    rest = {key: manifest[key] for key in sorted(set(manifest) - {"events", "derived"})}
    return {"events": events, "derived": sorted(manifest.get("derived", [])), **rest}


def handle_table(handles, manifest, pod):
    table = {handle: dict(row) for handle, row in handles.items() if not COMPUTED_ROW.search(handle)}
    for handle, row in table.items():
        if "first" in row or "inputs" in row:
            row.pop("name", None)
        if row.get("inputs", [""])[0].startswith("ni:"):
            row.pop("inputs", None)
    names = {"S": next(e["subject"] for e in manifest["events"] if "subject" in e)}
    names.update({f"I-{e['event']}": e["import"] for e in manifest["events"] if "import" in e})
    names.update({"A1": activity for activity in pod.activities.values()})
    for handle, row in table.items():
        if "first" in row:
            if row["first"] not in pod.first_records:
                raise Failure(f"{handle}'s first arrival, {row['first']}, wrote no record")
            names[handle] = pod.first_records[row["first"]]
        elif "inputs" in row:
            names[handle] = record_name(row["inputs"])
    for handle, name in names.items():
        table.setdefault(handle, {})["name"] = name
    handle_of = {table[handle]["name"]: handle for handle in table if "first" in table[handle]}
    unnamed = set(pod.records) - set(handle_of)
    if unnamed:
        raise Failure(f"records with no handle: {sorted(unnamed)}")
    versions, counts = defaultdict(list), defaultdict(int)
    for revision in pod.revisions:
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

def run(example):
    manifest = json.loads((example / "events.json").read_text(encoding="utf-8"))
    handles = json.loads((example / "handles.json").read_text(encoding="utf-8"))
    pod, facts_files, missing = Pod(), {}, []
    for event in manifest["events"]:
        if "subject" in event:
            file_subject(pod, event)
        elif "entry" in event:
            file_entry(pod, event, example)
        elif "export" in event:
            missing = file_export(pod, event, example, facts_files)
            if missing:
                break
    for old in example.glob("conversions/*/*/facts.ttl"):
        old.unlink()
    for path, content in facts_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    if missing:
        print("\n\n".join(missing))
        print(f"{len(missing)} conversions to run from the repository root, then run this again", file=sys.stderr)
        return 1
    for folder in OWNED_POD_FOLDERS:
        shutil.rmtree(example / "pod" / folder, ignore_errors=True)
    for path, (_, content) in sorted(pod.files.items()):
        target = example / "pod" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    write_json(example / "events.json", events_manifest(manifest, pod))
    write_json(example / "handles.json", handle_table(handles, manifest, pod))
    crate = json.loads((example / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    write_json(example / "ro-crate-metadata.json", crate_with_files(crate, example))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--example", type=Path, default=Path(__file__).absolute().parent)
    example = parser.parse_args().example.absolute()
    try:
        return run(example)
    except Failure as failure:
        print(f"pod_writer.py: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
