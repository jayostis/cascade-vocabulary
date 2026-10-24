"""Every snapshot vector under tests/vectors/snapshot/ is reproduced by tests/naming.py, and independently of hashlib by
Oxigraph's SHA256: each member's digest for a set hash, the rule's flattened inputs for a snapshot's name."""

import json

import pytest
from pyoxigraph import Literal, Store, Variable

import naming
from contract import ROOT
from test_naming_rules import flattened, sparql_sha256, v8_query

VECTORS = json.loads((ROOT / "tests" / "vectors" / "snapshot" / "vectors.json").read_text(encoding="utf-8"))
SET_HASHES = VECTORS["setHashes"]
SNAPSHOTS = [(chain["name"], at, snapshot) for chain in VECTORS["chains"]
             for at, snapshot in enumerate(chain["snapshots"])]


@pytest.mark.parametrize("vector", SET_HASHES, ids=[vector["name"] for vector in SET_HASHES])
def test_every_set_hash_is_what_the_reference_implementation_gives(vector):
    assert naming.set_hash(vector["members"]) == vector["setHash"]


@pytest.mark.parametrize("vector", SET_HASHES, ids=[vector["name"] for vector in SET_HASHES])
def test_every_set_hash_is_the_sum_of_oxigraphs_sha256_of_each_member(vector):
    total = sum(int(sparql_sha256(member), 16) for member in set(vector["members"]))
    assert f"{total % 2 ** 256:064x}" == vector["setHash"]


def test_a_set_hash_is_order_free_and_adds_what_a_set_lacked():
    by_name = {vector["name"]: vector for vector in SET_HASHES}
    assert by_name["two-members"]["setHash"] == by_name["two-members-reversed"]["setHash"]
    one, two = by_name["two-members"]["members"]
    assert naming.set_hash([two], before=naming.set_hash([one])) == by_name["two-members"]["setHash"]
    assert int(by_name["sum-wraps"]["setHash"], 16) < sum(
        int(naming.set_hash([member]), 16) for member in by_name["sum-wraps"]["members"])


@pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS, ids=[f"{chain}-{at}" for chain, at, _ in SNAPSHOTS])
def test_every_snapshot_chains_its_set_hash_and_is_named_by_its_rule(chain, at, snapshot):
    parent = snapshot["firstParent"]
    if parent is None:
        assert naming.set_hash(snapshot["set"]) == snapshot["setHash"]
    else:
        [before] = [s for c, _, s in SNAPSHOTS if c == chain and s["name"] == parent]
        assert naming.set_hash(snapshot["added"], before=before["setHash"]) == snapshot["setHash"]
    inputs = [snapshot["act"], tuple([] if parent is None else [parent]), tuple(snapshot["mergedParents"]),
              snapshot["setHash"]]
    assert naming.snapshot_name(snapshot["act"], parent, snapshot["mergedParents"], snapshot["setHash"]) == snapshot["name"]
    flat = flattened(inputs)
    [solution] = Store().query(v8_query("SnapshotNamingRule", len(flat)),
                               substitutions={Variable(f"input{n}"): Literal(v) for n, v in enumerate(flat, 1)})
    assert solution["name"].value == snapshot["name"]
