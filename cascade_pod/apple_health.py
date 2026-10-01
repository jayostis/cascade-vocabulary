"""An Apple Health export: its clinical record files, what export.xml says of each, and the facts the Bridge states
from them."""

import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone

from rdflib import BNode, Literal, Namespace, URIRef
from rdflib.namespace import XSD

from . import turtle

BRIDGE, PAV, PROV, RDFS, REC = (Namespace(turtle.PREFIXES[p]) for p in ("bridge", "pav", "prov", "rdfs", "rec"))
ADAPTER = "<cascade-bridge-adapter-fhir-r4>"
VOCABULARIES = "<cascade-vocabulary at the adapter's pin>"
TRANSMITTER = "Apple Health"
IMPORT_LABEL = "Apple Health export"


def documents(export):
    """Each clinical record file of the export, with the attributes export.xml gives it, or None."""
    entries = clinical_records(export / "export.xml")
    for path in sorted(export.glob("clinical-records/*.json"), key=lambda path: f"/clinical-records/{path.name}"):
        yield path, entries.get(f"/clinical-records/{path.name}")


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
