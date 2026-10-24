"""The reference implementation of every naming rule of decisions/naming.md, one function per rule term; the vectors
under tests/vectors/naming/ are what every other implementation reproduces."""

import base64
import hashlib
import ipaddress
import re
import struct

from pyoxigraph import BlankNode, CanonicalizationAlgorithm, Dataset, NamedNode, Quad, RdfFormat, Triple, parse

CASCADE = "https://ns.cascadeprotocol.org/cascade#"
NAMESPACE = "90c60849-c5ef-4ca6-bfb8-8662bd07d2b5"
PROV = "http://www.w3.org/ns/prov#"
XSD_STRING = "http://www.w3.org/2001/XMLSchema#string"

RULES = {local: CASCADE + local for local in (
    "RecordFromServerNamingRule", "RecordFromDocumentNamingRule", "RecordFromCcdaNamingRule",
    "RecordFromCcdaWithoutIdNamingRule", "ContainedRecordNamingRule", "EnteredRecordNamingRule", "VersionNamingRule", "RevisionNamingRule",
    "DocumentNamingRule", "FindingNamingRule", "TableRowNamingRule", "TableVersionNamingRule", "ViewEntryNamingRule",
    "SnapshotNamingRule", "ServerNamingRule", "OrganizationNamingRule", "ClaimNamingRule", "AssertionNamingRule",
    "RetractionNamingRule")}

THIS_VERSION = NamedNode("urn:cascade:this-version")


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


def _percent_normalised(text, lower=False):
    """Every percent-encoded unreserved character decoded and every other encoding's hex digits in upper case; with
    lower, every other character in lower case too, an encoding's hex digits kept upper (RFC 3986 §6.2.2.1)."""
    def one(piece):
        if not re.fullmatch(r"%[0-9A-Fa-f]{2}", piece):
            return piece.lower() if lower else piece
        character = chr(int(piece[1:], 16))
        if UNRESERVED.fullmatch(character):
            return character.lower() if lower else character
        return piece.upper()

    return "".join(one(piece) for piece in re.split(r"(%[0-9A-Fa-f]{2})", text))


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


HOST_NAME = re.compile(r"(?:[A-Za-z0-9\-._~!$&'()*+,;=]|%[0-9A-Fa-f]{2})+")
IP_FUTURE = re.compile(r"[vV][0-9A-Fa-f]+\.[A-Za-z0-9\-._~!$&'()*+,;=:]+")


def _host(text):
    """RFC 3986 §3.2.2: a reg-name of ASCII characters and percent-encodings, or an IP-literal in brackets holding an
    IPv6 address or an IPvFuture, with no zone id. Returns it normalised."""
    if not text.isascii():
        raise ValueError("a base URL whose host is not ASCII names nothing: a source sends an IDN punycoded")
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1]
        if IP_FUTURE.fullmatch(inner):
            return f"[{inner.lower()}]"
        if "%" not in inner:
            try:
                ipaddress.IPv6Address(inner)
            except ValueError:
                pass
            else:
                return f"[{inner.lower()}]"
        raise ValueError("a base URL whose bracketed host is not an IPv6 address or an IPvFuture names nothing")
    if "[" in text or "]" in text:
        raise ValueError("a base URL whose host has a bracket that is not an IP-literal's names nothing")
    if not HOST_NAME.fullmatch(text):
        raise ValueError("a base URL whose host is not a reg-name names nothing")
    return _percent_normalised(text, lower=True)


def normalised_base_url(url):
    """RFC 3986 §6.2.2 and §6.2.3: scheme and host in lower case, percent-encodings in upper case and unreserved
    characters decoded, dot segments removed, the scheme's default port dropped; then every trailing / removed. Refused
    with ValueError, never echoing the URL: userinfo, since a credential is never a name input; a control character or
    space, which a URL parser would otherwise drop; a query or a fragment, even an empty one, since a server's base has
    neither and a credential must never be a name input; no scheme or no host; a host that is not a reg-name of ASCII
    characters and percent-encodings or a bracketed IPv6 address or IPvFuture; a port that is not ASCII digits or is
    above 65535. A port is read as an integer, so its leading zeros are dropped."""
    if re.search(r"[\x00-\x20\x7f]", url):
        raise ValueError("a base URL holding a control character or space names nothing")
    if re.search(r"[?#]", url):
        raise ValueError("a base URL carrying a query or a fragment names nothing")
    parts = re.fullmatch(r"([A-Za-z][A-Za-z0-9+.\-]*):(?://([^/]*))?(.*)", url, re.DOTALL)
    if parts is None or parts[2] is None:
        raise ValueError("a base URL with no scheme or no host names nothing")
    scheme, authority, path = parts[1].lower(), parts[2], parts[3]
    if "@" in authority:
        raise ValueError("a base URL carrying userinfo names nothing")
    if authority.startswith("["):
        close = authority.find("]") + 1
        host, rest = (authority[:close], authority[close:]) if close else (authority, "")
        if rest and not rest.startswith(":"):
            raise ValueError("a base URL whose bracketed host is not followed by a port names nothing")
        port = rest[1:]
    else:
        host, _, port = authority.partition(":")
    if not host:
        raise ValueError("a base URL with no scheme or no host names nothing")
    if not re.fullmatch(r"[0-9]*", port):
        raise ValueError("a base URL whose port is not ASCII digits names nothing")
    if port:
        port = port.lstrip("0") or "0"
        if len(port) > 5 or int(port) > 65535:
            raise ValueError("a base URL whose port is above 65535 names nothing")
    host = _host(host)
    netloc = host if port in ("", DEFAULT_PORTS.get(scheme)) else f"{host}:{port}"
    return f"{scheme}://{netloc}{_without_dot_segments(_percent_normalised(path)).rstrip('/')}"


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


def record_from_ccda_without_id_name(custodian, patient, record_class, key, members):
    """An entry with no id, named inside its custodian and patient scopes: its record class's IRI, its key
    fingerprint, and its members fingerprint where it has no key; "" for each it lacks."""
    return v8_name("RecordFromCcdaWithoutIdNamingRule", [*custodian, *patient, record_class, key, members])


def contained_record_name(container, container_source_version, contained_id):
    """container_source_version is the version id the source gives the container (FHIR meta.versionId); where it
    gives none, the container's meta.lastUpdated as written; where it gives neither, ""."""
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


MUHASH_MODULUS = 2 ** 3072 - 1103717
CHACHA20_CONSTANTS = (0x61707865, 0x3320646E, 0x79622D32, 0x6B206574)


def _chacha20_block(key, counter):
    """RFC 8439 §2.3, its nonce zero: a block of the keystream Bitcoin Core's ChaCha20Aligned gives."""
    state = [*CHACHA20_CONSTANTS, *struct.unpack("<8I", key), counter, 0, 0, 0]
    x = state[:]

    def quarter(a, b, c, d):
        for p, q, r, shift in ((a, b, d, 16), (c, d, b, 12), (a, b, d, 8), (c, d, b, 7)):
            x[p] = (x[p] + x[q]) & 0xFFFFFFFF
            x[r] ^= x[p]
            x[r] = ((x[r] << shift) | (x[r] >> (32 - shift))) & 0xFFFFFFFF

    for _ in range(10):
        quarter(0, 4, 8, 12), quarter(1, 5, 9, 13), quarter(2, 6, 10, 14), quarter(3, 7, 11, 15)
        quarter(0, 5, 10, 15), quarter(1, 6, 11, 12), quarter(2, 7, 8, 13), quarter(3, 4, 9, 14)
    return struct.pack("<16I", *((a + b) & 0xFFFFFFFF for a, b in zip(x, state)))


def _num3072(member):
    """Bitcoin Core's MuHash3072::ToNum3072: the ChaCha20 keystream under the member's SHA-256, 384 bytes read
    little-endian."""
    key = hashlib.sha256(member).digest()
    return int.from_bytes(b"".join(_chacha20_block(key, counter) for counter in range(6)), "little")


def muhash3072(members):
    """Bitcoin Core's MuHash3072 over the byte strings, each inserted once: the SHA-256 of the product of their
    numbers modulo 2^3072 - 1103717, as 384 bytes little-endian. Bitcoin Core writes the digest byte-reversed."""
    product = 1
    for member in members:
        product = product * _num3072(member) % MUHASH_MODULUS
    return hashlib.sha256(product.to_bytes(384, "little")).digest()


def set_hash(files):
    """cascade:setHash: MuHash3072 over one member per file, its path relative to the pod in UTF-8, a 0x00 byte and
    the SHA-256 of its bytes, written as 64 lower-case hex digits. files: each path and the SHA-256 of its bytes."""
    return muhash3072(path.encode("utf-8") + b"\x00" + digest for path, digest in dict(files).items()).hex()


def act_description_name(triples):
    """The act's description, every triple of its file but the snapshot's, named as cascade:VersionNamingRule names a
    version but with its blank nodes labelled by RDFC-1.0."""
    dataset = Dataset(Quad(t.subject, t.predicate, t.object) for t in triples)
    dataset.canonicalize(CanonicalizationAlgorithm.RDFC_1_0)
    term = lambda t: f"_:{t.value}" if isinstance(t, BlankNode) else canonical(t)  # noqa: E731
    return ni_name("".join(sorted({f"{term(q.subject)} {term(q.predicate)} {term(q.object)} .\n"
                                   for q in dataset})).encode("utf-8"))


def snapshot_name(act, description, first_parent, merged_parents, set_hash):
    """The snapshot of one act; description is act_description_name's; first_parent is None on a writer's first."""
    return v8_name("SnapshotNamingRule", [act, description, *counted([] if first_parent is None else [first_parent]),
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
        "RecordFromCcdaWithoutIdNamingRule": lambda: record_from_ccda_without_id_name(inputs[0:2], inputs[2:4],
                                                                                      *inputs[4:]),
        "ContainedRecordNamingRule": lambda: contained_record_name(*inputs),
        "EnteredRecordNamingRule": lambda: entered_record_name(*inputs),
        "ServerNamingRule": lambda: server_name(*inputs),
        "OrganizationNamingRule": lambda: (organization_from_server_name(inputs[0], inputs[2]) if len(inputs) == 3
                                           else organization_from_identifier_name(*inputs)),
        "ClaimNamingRule": lambda: claim_name(*inputs),
        "AssertionNamingRule": lambda: assertion_name(*inputs),
        "RetractionNamingRule": lambda: retraction_name(*inputs),
        "TableRowNamingRule": lambda: table_row_name(*inputs),
        "SnapshotNamingRule": lambda: snapshot_name(inputs[0], inputs[1], *(inputs[2] or [None]), inputs[3], inputs[4]),
        "ViewEntryNamingRule": lambda: view_entry_name(*inputs),
    }
    return one_of[rule]()


ECHAR = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def canonical(term):
    """A pyoxigraph term as RDFC-1.0's canonical N-Quads write it, for a graph with no blank node; Oxigraph holds a language tag
    in lower case, since BCP 47 tags are case-insensitive."""
    if isinstance(term, BlankNode):
        raise ValueError("a content name is never taken over a blank node")
    if isinstance(term, NamedNode):
        return f"<{term.value}>"
    text = "".join(ECHAR.get(c) or (f"\\u{ord(c):04X}" if c < " " or c == "\x7f" else c) for c in term.value)
    if term.language:
        return f'"{text}"@{term.language}'
    if term.datatype.value != XSD_STRING:
        return f'"{text}"^^<{term.datatype.value}>'
    return f'"{text}"'


FORMATS = {"nt": RdfFormat.N_TRIPLES, "turtle": RdfFormat.TURTLE}


def content(text, format="nt"):
    """The triples of an N-Triples or Turtle text as Oxigraph parses them, every literal's lexical form as written:
    rdflib rewrites Turtle's 007, +5, .5 and -0 even with its literal normalisation off, and RDFC-1.0 hashes the form
    written."""
    return {Triple(quad.subject, quad.predicate, quad.object)
            for quad in parse(text.encode("utf-8"), format=FORMATS[format])}


def canonical_nquads(triples):
    """RDFC-1.0 of a graph with no blank node: its N-Quads lines, each once, in code point order."""
    return "".join(sorted({f"{canonical(t.subject)} {canonical(t.predicate)} {canonical(t.object)} .\n"
                           for t in triples}))


def content_name(triples):
    return ni_name(canonical_nquads(triples).encode("utf-8"))


def version_name(triples):
    """triples: the version's, its subject urn:cascade:this-version, prov:specializationOf its record among them."""
    return content_name(triples)


def document_name(octets):
    return ni_name(octets)


def table_version_name(series, revises, rows):
    """rows: the version's row triples as content() gives them."""
    triples = {Triple(THIS_VERSION, NamedNode(PROV + "specializationOf"), NamedNode(series)), *rows}
    if revises is not None:
        triples.add(Triple(THIS_VERSION, NamedNode(PROV + "wasRevisionOf"), NamedNode(revises)))
    return content_name(triples)
