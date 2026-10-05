"""The names a pod gives: a record's from its inputs, a document's, a version's or a revision's from its content, and an
import's or an entry session's at random."""

import base64
import hashlib
import uuid
from datetime import datetime, timezone

from rdflib import BNode

from . import Failure, turtle

RECORD_NAMESPACE = "90c60849-c5ef-4ca6-bfb8-8662bd07d2b5"
THIS_VERSION = "urn:cascade:this-version"
THIS_REVISION = "urn:cascade:this-revision"
THIS_ENTRY = "urn:cascade:this-entry"


def record(inputs):
    digest = bytearray(hashlib.sha256("|".join([RECORD_NAMESPACE, *inputs]).encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    text = digest.hex()
    return f"urn:uuid:{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def in_utc(date_time):
    """An xsd:dateTime's lexical form moved to UTC and ending in Z, any fraction of a second kept less its trailing
    zeros."""
    try:
        moment = datetime.fromisoformat(date_time)
    except ValueError:
        raise Failure(f"{date_time} is not an xsd:dateTime") from None
    if moment.tzinfo is None:
        raise Failure(f"{date_time} has no time zone")
    moment = moment.astimezone(timezone.utc)
    fraction = f".{moment.microsecond:06d}".rstrip("0") if moment.microsecond else ""
    return moment.strftime("%Y-%m-%dT%H:%M:%S") + fraction + "Z"


def document(octets):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode("ascii").rstrip("=")


def content(triples):
    """A version's name from its triples about THIS_VERSION, or a revision's from its triples about THIS_REVISION."""
    if any(isinstance(term, BNode) for triple in triples for term in triple):
        raise Failure("content to be named holds a blank node")
    return document(turtle.ntriples(triples).encode("utf-8"))


def new_id():
    return f"urn:uuid:{uuid.uuid4()}"
