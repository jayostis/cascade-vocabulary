import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone

PREFIXES = {
    "bridge": "https://ns.cascadeprotocol.org/bridge/v1-draft#",
    "pav": "http://purl.org/pav/",
    "prov": "http://www.w3.org/ns/prov#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rec": "https://ns.cascadeprotocol.org/records/v1-draft#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
TRANSMITTER = "Apple Health"
IMPORT_LABEL = "Apple Health export"


def clinical_records(export_xml):
    root = ElementTree.parse(export_xml).getroot()
    return {entry.get("resourceFilePath"): dict(entry.attrib) for entry in root.iter("ClinicalRecord")}


def utc(apple_date):
    moment = datetime.strptime(apple_date, "%Y-%m-%d %H:%M:%S %z").astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _date_time(text):
    return f'{_string(text)}^^xsd:dateTime'


def _attribution(label, role):
    return f"[ prov:agent [ rdfs:label {_string(label)} ] ; prov:hadRole rec:{role} ]"


def _expand(curie):
    prefix, local = curie.split(":", 1)
    return PREFIXES[prefix] + local


def _block(subject, statements):
    lines = [subject]
    ordered = sorted(statements, key=lambda statement: _expand(statement[0]))
    for index, (predicate, objects) in enumerate(ordered):
        end = " ." if index == len(ordered) - 1 else " ;"
        objects = sorted(objects)
        if len(objects) == 1:
            lines.append(f"  {predicate} {objects[0]}{end}")
        else:
            lines.append(f"  {predicate}")
            for position, value in enumerate(objects):
                lines.append(f"    {value}{end if position == len(objects) - 1 else ' ,'}")
    return "\n".join(lines)


def facts(entry, import_started_at):
    document = [("prov:qualifiedAttribution", [_attribution(TRANSMITTER, "transmitter")])]
    if entry is not None:
        source_url = entry["sourceURL"]
        document[0][1].append(_attribution(entry["sourceName"], "author"))
        document += [
            ("bridge:serverBaseUrl", [_string(source_url.rsplit("/", 2)[0])]),
            ("pav:retrievedFrom", [f"<{source_url}>"]),
            ("pav:retrievedOn", [_date_time(utc(entry["receivedDate"]))]),
            ("bridge:sourceFormatVersion", [_string(entry["fhirVersion"])]),
        ]
    this_import = [
        ("rdfs:label", [_string(IMPORT_LABEL)]),
        ("prov:startedAtTime", [_date_time(import_started_at)]),
    ]
    body = _block("bridge:thisDocument", document) + "\n\n" + _block("bridge:thisImport", this_import) + "\n"
    used = sorted(prefix for prefix in PREFIXES if f"{prefix}:" in body)
    head = "".join(f"@prefix {prefix}: <{PREFIXES[prefix]}> .\n" for prefix in used)
    return head + "\n" + body
