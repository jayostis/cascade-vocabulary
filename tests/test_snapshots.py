"""Every snapshot vector under tests/vectors/snapshot/ is reproduced by tests/naming.py: its MuHash3072 by Bitcoin Core's
own vectors, each set hash, and each snapshot's description and name, the name again by the rule's flattened inputs on
Oxigraph."""

import hashlib
import json

import pytest
from pyoxigraph import Literal, NamedNode, Store, Variable

import naming
from contract import ROOT
from test_naming_rules import flattened, v8_query

VECTORS = json.loads((ROOT / "tests" / "vectors" / "snapshot" / "vectors.json").read_text(encoding="utf-8"))
SET_HASHES = VECTORS["setHashes"]
SNAPSHOTS = [(chain["name"], at, snapshot) for chain in VECTORS["chains"]
             for at, snapshot in enumerate(chain["snapshots"])]


def test_muhash3072_is_bitcoin_cores():
    for vector in VECTORS["muhash3072"]:
        members = [bytes.fromhex(member) for member in vector["members"]]
        assert hashlib.sha256(bytes.fromhex(vector["numerator"])).hexdigest() == vector["digest"]
        assert naming.muhash3072(members).hex() == vector["digest"]
    number = lambda first: naming._num3072(bytes([first]) + bytes(31))  # noqa: E731
    divided = number(0) * number(1) * pow(number(2), -1, naming.MUHASH_MODULUS) % naming.MUHASH_MODULUS
    assert hashlib.sha256(divided.to_bytes(384, "little")).digest()[::-1].hex() == (
        "10d312b100cbd32ada024a6646e40d3482fcff103668d2625f10002a607d5863")


@pytest.mark.parametrize("vector", SET_HASHES, ids=[vector["name"] for vector in SET_HASHES])
def test_every_set_hash_is_what_the_reference_implementation_gives(vector):
    files = [(f["path"], bytes.fromhex(f["sha256"])) for f in vector["files"]]
    assert naming.set_hash(files) == vector["setHash"]


@pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS, ids=[f"{chain}-{at}" for chain, at, _ in SNAPSHOTS])
def test_every_snapshot_is_named_by_its_rule_over_its_description_and_set(chain, at, snapshot):
    held = dict((f["path"], bytes.fromhex(f["sha256"])) for f in snapshot["set"])
    assert snapshot["path"] not in held
    assert naming.set_hash(held) == snapshot["setHash"]
    [earlier] = [s for c, n, s in SNAPSHOTS if c == chain and n == at - 1] or [None]
    if earlier is not None:
        assert held[earlier["path"]] == hashlib.sha256(earlier["file"].encode("utf-8")).digest()
    description = {t for t in naming.content(snapshot["file"]) if t.subject != NamedNode(snapshot["name"])}
    assert naming.act_description_name(description) == snapshot["description"]
    parent = snapshot["firstParent"]
    assert naming.snapshot_name(snapshot["act"], snapshot["description"], parent, snapshot["mergedParents"],
                                snapshot["setHash"]) == snapshot["name"]
    flat = flattened([snapshot["act"], snapshot["description"], tuple([] if parent is None else [parent]),
                      tuple(snapshot["mergedParents"]), snapshot["setHash"]])
    [solution] = Store().query(v8_query("SnapshotNamingRule", len(flat)),
                               substitutions={Variable(f"input{n}"): Literal(v) for n, v in enumerate(flat, 1)})
    assert solution["name"].value == snapshot["name"]
