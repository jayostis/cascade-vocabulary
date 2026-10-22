"""The reference implementation of every naming rule of decisions/naming.md, one function per rule term; the vectors
under tests/vectors/naming/ are what every other implementation reproduces."""

import base64
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

import rdflib
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import XSD

CASCADE = "https://ns.cascadeprotocol.org/cascade#"
NAMESPACE = "90c60849-c5ef-4ca6-bfb8-8662bd07d2b5"
PROV = "http://www.w3.org/ns/prov#"

RULES = {local: CASCADE + local for local in (
    "RecordFromServerNamingRule", "RecordFromDocumentNamingRule", "RecordFromCcdaNamingRule",
    "ContainedRecordNamingRule", "EnteredRecordNamingRule", "VersionNamingRule", "RevisionNamingRule",
    "DocumentNamingRule", "FindingNamingRule", "TableRowNamingRule", "TableVersionNamingRule", "ViewEntryNamingRule",
    "SnapshotNamingRule", "ServerNamingRule", "OrganizationNamingRule", "ClaimNamingRule", "AssertionNamingRule",
    "RetractionNamingRule")}

THIS_VERSION = URIRef("urn:cascade:this-version")


def escaped(text):
    return text.replace("%", "%25").replace("|", "%7C")


def counted(items):
    """A list as name inputs: its count, then its distinct items in code point order."""
    distinct = sorted(set(items))
    return [str(len(distinct)), *distinct]


def v8_name(rule, inputs):
    """RFC 9562 §5.8: the first 128 bits of SHA-256 over the namespace, the rule's IRI and the inputs, each escaped and
    joined by |, with the version bits 1000 and the variant bits 10."""
    text = "|".join(escaped(part) for part in (NAMESPACE, RULES[rule], *inputs))
    octets = bytearray(hashlib.sha256(text.encode("utf-8")).digest()[:16])
    octets[6] = (octets[6] & 0x0F) | 0x80
    octets[8] = (octets[8] & 0x3F) | 0x80
    hexed = octets.hex()
    return f"urn:uuid:{hexed[:8]}-{hexed[8:12]}-{hexed[12:16]}-{hexed[16:20]}-{hexed[20:]}"


def ni_name(octets):
    """RFC 6920: SHA-256 of the octets in unpadded base64url."""
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode("ascii").rstrip("=")


UNRESERVED = re.compile(r"[A-Za-z0-9\-._~]")
DEFAULT_PORTS = {"http": "80", "https": "443"}


def _percent_normalised(text):
    def one(match):
        character = chr(int(match.group(1), 16))
        return character if UNRESERVED.fullmatch(character) else "%" + match.group(1).upper()

    return re.sub(r"%([0-9A-Fa-f]{2})", one, text)


def _without_dot_segments(path):
    """RFC 3986 §5.2.4."""
    output = []
    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith("./"):
            path = path[2:]
        elif path.startswith("/./"):
            path = path[2:]
        elif path == "/.":
            path = "/"
        elif path.startswith("/../"):
            path = path[3:]
            output = output[:-1]
        elif path == "/..":
            path = "/"
            output = output[:-1]
        elif path in (".", ".."):
            path = ""
        else:
            start = 1 if path.startswith("/") else 0
            end = path.find("/", start)
            end = len(path) if end == -1 else end
            output.append(path[:end])
            path = path[end:]
    return "".join(output)


def normalised_base_url(url):
    """RFC 3986 §6.2.2 and §6.2.3: scheme and host in lower case, percent-encodings in upper case and unreserved
    characters decoded, dot segments removed, the scheme's default port dropped; then every trailing / removed. A URL
    carrying userinfo is refused: a credential is never a name input."""
    parts = urlsplit(url)
    if "@" in parts.netloc:
        raise ValueError(f"a base URL carrying userinfo names nothing: {url}")
    scheme = parts.scheme.lower()
    host, port = re.fullmatch(r"(\[[^\]]*\]|[^:]*)(?::(\d*))?", parts.netloc).groups(default="")
    host = _percent_normalised(host).lower()
    netloc = host if port in ("", DEFAULT_PORTS.get(scheme)) else f"{host}:{port}"
    path = _without_dot_segments(_percent_normalised(parts.path)).rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, parts.fragment))


def encoded_for_uri(text):
    """SPARQL's ENCODE_FOR_URI: every character but A-Z a-z 0-9 - _ . ~ as % and two upper-case hex digits of its
    UTF-8."""
    return "".join(c if UNRESERVED.fullmatch(c) else "".join(f"%{b:02X}" for b in c.encode("utf-8")) for c in text)


def code_iri(stem, code):
    """A code joined to its system's stem, as decisions/code-iris.md rules."""
    return stem + encoded_for_uri(code)


def record_from_server_name(base_url, resource_type, resource_id):
    return v8_name("RecordFromServerNamingRule", [normalised_base_url(base_url), resource_type, resource_id])


def record_from_document_name(document, selector_value):
    return v8_name("RecordFromDocumentNamingRule", [document, selector_value])


def record_from_ccda_name(custodian, patient, entry):
    """Each of custodian, patient and entry is a CDA id's (root, extension), extension "" where the id has none."""
    return v8_name("RecordFromCcdaNamingRule", [*custodian, *patient, *entry])


def contained_record_name(container, container_source_version, contained_id):
    """container_source_version is the version id the source gives the container, "" where it gives none."""
    return v8_name("ContainedRecordNamingRule", [container, container_source_version, contained_id])


def entered_record_name(session, position):
    return v8_name("EnteredRecordNamingRule", [session, str(int(position))])


def server_name(base_url):
    return v8_name("ServerNamingRule", [normalised_base_url(base_url)])


def organization_from_server_name(base_url, organization_id):
    return v8_name("OrganizationNamingRule", [normalised_base_url(base_url), "Organization", organization_id])


def organization_from_identifier_name(system, value):
    """A document's business identifier for the organization: a C-CDA id's root and extension, or a FHIR
    Organization.identifier's system and value."""
    return v8_name("OrganizationNamingRule", [system, value])


def claim_name(maker, matcher_rule, justification, members, used):
    return v8_name("ClaimNamingRule", [maker, matcher_rule, justification, *counted(members), *counted(used)])


def assertion_name(rule_list_version, claim):
    return v8_name("AssertionNamingRule", [rule_list_version, claim])


def retraction_name(release, claim, matcher_rule):
    return v8_name("RetractionNamingRule", [release, claim, matcher_rule])


def table_row_name(source, predicate, target, panel_sequence=None):
    extra = [] if panel_sequence is None else [str(int(panel_sequence))]
    return v8_name("TableRowNamingRule", [source, predicate, target, *extra])


def snapshot_name(first_parent, merged_parents, set_hash):
    """first_parent is None on a writer's first snapshot."""
    return v8_name("SnapshotNamingRule", [*counted([] if first_parent is None else [first_parent]),
                                          *counted(merged_parents), set_hash])


def view_entry_name(view, least_member):
    """view: the view's path as runtime/pod-layout.ttl places it, so the name is relative to the pod and holds no
    address."""
    return f"{view}#{hashlib.sha256(least_member.encode('utf-8')).hexdigest()}"


def named(rule, inputs):
    """A rule's name from its inputs as a vector's bridge:nameInputs lists them: strings in the rule's order, a list
    input as a list."""
    one_of = {
        "RecordFromServerNamingRule": lambda: record_from_server_name(*inputs),
        "RecordFromDocumentNamingRule": lambda: record_from_document_name(*inputs),
        "RecordFromCcdaNamingRule": lambda: record_from_ccda_name(inputs[0:2], inputs[2:4], inputs[4:6]),
        "ContainedRecordNamingRule": lambda: contained_record_name(*inputs),
        "EnteredRecordNamingRule": lambda: entered_record_name(*inputs),
        "ServerNamingRule": lambda: server_name(*inputs),
        "OrganizationNamingRule": lambda: (organization_from_server_name(inputs[0], inputs[2]) if len(inputs) == 3
                                           else organization_from_identifier_name(*inputs)),
        "ClaimNamingRule": lambda: claim_name(*inputs),
        "AssertionNamingRule": lambda: assertion_name(*inputs),
        "RetractionNamingRule": lambda: retraction_name(*inputs),
        "TableRowNamingRule": lambda: table_row_name(*inputs),
        "SnapshotNamingRule": lambda: snapshot_name(*(inputs[0] or [None]), inputs[1], inputs[2]),
        "ViewEntryNamingRule": lambda: view_entry_name(*inputs),
    }
    return one_of[rule]()


ECHAR = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def canonical(term):
    """A term as RDFC-1.0's canonical N-Quads write it, for a graph with no blank node."""
    if isinstance(term, BNode):
        raise ValueError("a content name is never taken over a blank node")
    if isinstance(term, URIRef):
        return f"<{term}>"
    text = "".join(ECHAR.get(c) or (f"\\u{ord(c):04X}" if c < " " or c == "\x7f" else c) for c in str(term))
    if term.language:
        return f'"{text}"@{term.language}'
    if term.datatype is not None and term.datatype != XSD.string:
        return f'"{text}"^^<{term.datatype}>'
    return f'"{text}"'


def content(text, format="nt"):
    """The triples of an RDF text with every literal's lexical form as written: rdflib would otherwise normalise
    "007"^^xsd:integer to "7" on parsing, and RDFC-1.0 hashes the form written."""
    kept = rdflib.NORMALIZE_LITERALS
    rdflib.NORMALIZE_LITERALS = False
    try:
        return set(Graph().parse(data=text, format=format))
    finally:
        rdflib.NORMALIZE_LITERALS = kept


def canonical_nquads(triples):
    """RDFC-1.0 of a graph with no blank node: its N-Quads lines, each once, in code point order."""
    return "".join(sorted({" ".join(map(canonical, triple)) + " .\n" for triple in triples}))


def content_name(triples):
    return ni_name(canonical_nquads(triples).encode("utf-8"))


def version_name(triples):
    """triples: the version's, its subject urn:cascade:this-version, prov:specializationOf its record among them."""
    return content_name(triples)


def revision_name(triples):
    """triples: the revision's, its subject urn:cascade:this-revision."""
    return content_name(triples)


def finding_name(triples):
    """triples: the finding's, its subject urn:cascade:this-finding."""
    return content_name(triples)


def document_name(octets):
    return ni_name(octets)


def table_version_name(series, revises, rows):
    triples = {(THIS_VERSION, URIRef(PROV + "specializationOf"), URIRef(series)), *rows}
    if revises is not None:
        triples.add((THIS_VERSION, URIRef(PROV + "wasRevisionOf"), URIRef(revises)))
    return content_name(triples)
