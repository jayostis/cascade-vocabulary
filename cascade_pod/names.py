"""The names a pod gives: a record's from its inputs, and a document's, a version's or a revision's from its content."""

import base64
import hashlib

from rdflib import BNode

from . import Failure, turtle

RECORD_NAMESPACE = "90c60849-c5ef-4ca6-bfb8-8662bd07d2b5"
THIS_VERSION = "urn:cascade:this-version"
THIS_REVISION = "urn:cascade:this-revision"


def record(inputs):
    digest = bytearray(hashlib.sha256("|".join([RECORD_NAMESPACE, *inputs]).encode("utf-8")).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    text = digest.hex()
    return f"urn:uuid:{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def document(octets):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode("ascii").rstrip("=")


def content(triples):
    """A version's name from its triples about THIS_VERSION, or a revision's from its triples about THIS_REVISION."""
    if any(isinstance(term, BNode) for triple in triples for term in triple):
        raise Failure("content to be named holds a blank node")
    return document(turtle.ntriples(triples).encode("utf-8"))
