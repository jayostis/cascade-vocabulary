import hashlib
import json

import pytest
from pyoxigraph import Literal, NamedNode, Store, Variable

import naming
from contract import ROOT
from naming_vectors import flattened, v8_query

SNAPSHOT_VECTORS = json.loads((ROOT / "tests" / "vectors" / "snapshot" / "vectors.json").read_text(encoding="utf-8"))
SET_HASHES = SNAPSHOT_VECTORS["setHashes"]
CHAINS = {chain["name"]: chain["snapshots"] for chain in SNAPSHOT_VECTORS["chains"]}
SNAPSHOTS = [pytest.param(chain["name"], at, snapshot, id=f"{chain['name']}-{at}")
             for chain in SNAPSHOT_VECTORS["chains"] for at, snapshot in enumerate(chain["snapshots"])]


def held(snapshot):
    """The files a snapshot holds: each path with the SHA-256 of the file."""
    return dict((f["path"], bytes.fromhex(f["sha256"])) for f in snapshot["set"])


def flat_inputs(snapshot):
    """The inputs of the snapshot naming rule with each list flattened to its count and its sorted members."""
    parent = snapshot["firstParent"]
    return flattened([snapshot["act"], snapshot["description"], tuple([] if parent is None else [parent]),
                      tuple(snapshot["mergedParents"]), snapshot["setHash"]])


class TestSnapshotVectors:
    """Snapshot vectors a runtime reproduces · tests/vectors/snapshot/vectors.json, tests/naming.py

    Every act leaves a snapshot, named from the act, its description, the snapshots before it and a set hash: one hash
    of the files the pod then holds, which can be kept up as files come and go. The set hash is MuHash3072, as Bitcoin
    Core computes it; these vectors are runs of snapshots, each after the one before, worked out by the reference
    implementation.

    @rule naming N14
    """

    class TestGivenBitcoinCoresMuhashVectors:
        """given Bitcoin Core's MuHash3072 vectors"""

        def test_is_hashed_to_its_digest_by_muhash3072(self):
            """is hashed to its digest by `naming.muhash3072()`

            For each of Bitcoin Core's vectors the SHA-256 of its numerator is compared with its digest, and the digest
            `naming.muhash3072()` gives its members is compared with it too; a vector where either differs fails.
            """
            wrong = [vector["name"] for vector in SNAPSHOT_VECTORS["muhash3072"]
                     if hashlib.sha256(bytes.fromhex(vector["numerator"])).hexdigest() != vector["digest"]
                     or naming.muhash3072([bytes.fromhex(member) for member in vector["members"]]).hex()
                     != vector["digest"]]
            assert SNAPSHOT_VECTORS["muhash3072"] and wrong == []

        def test_holds_a_division_that_gives_bitcoin_cores_digest(self):
            """holds a division that gives Bitcoin Core's digest

            Three numbers made from the bytes 0, 1 and 2 are multiplied and divided as MuHash3072 removes a member: the
            first times the second over the third, kept below its prime. The result is written as 384 bytes, the least significant first,
            hashed with SHA-256 and written backwards in hex, as Bitcoin Core writes a digest, and is compared with the
            digest Bitcoin Core publishes for that division.
            """
            number = lambda first: naming._num3072(bytes([first]) + bytes(31))  # noqa: E731
            divided = number(0) * number(1) * pow(number(2), -1, naming.MUHASH_MODULUS) % naming.MUHASH_MODULUS
            assert hashlib.sha256(divided.to_bytes(384, "little")).digest()[::-1].hex() == (
                "10d312b100cbd32ada024a6646e40d3482fcff103668d2625f10002a607d5863")

    class TestGivenASetHashVector:
        """given a set-hash vector"""

        @pytest.mark.parametrize("vector", SET_HASHES, ids=[vector["name"] for vector in SET_HASHES])
        def test_is_the_set_hash_the_reference_implementation_gives_its_files(self, vector):
            """is the set hash `naming.set_hash()` gives its files

            The files of the vector, each a path and the SHA-256 of its bytes, are given to `naming.set_hash()`, and
            the hash it gives is compared with the one the vector holds.
            """
            files = [(f["path"], bytes.fromhex(f["sha256"])) for f in vector["files"]]
            assert naming.set_hash(files) == vector["setHash"]

    class TestGivenASnapshotOfAChain:
        """given a snapshot in a run of snapshots"""

        @pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS)
        def test_holds_no_line_for_its_own_file(self, chain, at, snapshot):
            """holds no line for its own file

            The path of the snapshot's own file is compared with the paths of the files the snapshot holds: a snapshot
            cannot hold the file that describes it, as the file would then have to hold its own hash.
            """
            assert snapshot["path"] not in held(snapshot)

        @pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS)
        def test_has_the_set_hash_of_the_files_it_holds(self, chain, at, snapshot):
            """has the set hash of the files it holds

            `naming.set_hash()` is given the files the snapshot holds, and the hash it gives is compared with the set
            hash the snapshot names.
            """
            assert naming.set_hash(held(snapshot)) == snapshot["setHash"]

        @pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS)
        def test_holds_the_snapshot_before_it_by_the_sha_256_of_that_file(self, chain, at, snapshot):
            """holds the snapshot before it by the SHA-256 of that file

            The first snapshot of a run has no first parent. A later one holds the file of the snapshot before it, and
            the SHA-256 it holds for that file is compared with the SHA-256 of the earlier snapshot's own text.
            """
            earlier = CHAINS[chain][at - 1] if at else None
            if earlier is None:
                assert snapshot["firstParent"] is None
            else:
                assert held(snapshot)[earlier["path"]] == hashlib.sha256(earlier["file"].encode("utf-8")).digest()

        @pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS)
        def test_has_the_description_name_of_its_files_statements_about_anything_but_itself(self, chain, at, snapshot):
            """has the description name of its file's statements about anything but itself

            The statements of the snapshot's file whose subject is not the snapshot are given to
            `naming.act_description_name()`, and the name it gives is compared with the description the snapshot names.
            """
            description = {t for t in naming.content(snapshot["file"]) if t.subject != NamedNode(snapshot["name"])}
            assert naming.act_description_name(description) == snapshot["description"]

        @pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS)
        def test_is_named_by_the_snapshot_naming_rule_over_its_act_description_parents_and_set_hash(
                self, chain, at, snapshot):
            """is named by the snapshot naming rule over its act, description, parents and set hash

            `naming.snapshot_name()` is given the snapshot's act, description, first parent, merged parents and set hash,
            and the name it gives is compared with the snapshot's name.
            """
            assert naming.snapshot_name(snapshot["act"], snapshot["description"], snapshot["firstParent"],
                                        snapshot["mergedParents"], snapshot["setHash"]) == snapshot["name"]

        @pytest.mark.parametrize("chain, at, snapshot", SNAPSHOTS)
        def test_is_named_alike_by_one_query_over_its_flattened_inputs_on_oxigraph(self, chain, at, snapshot):
            """is named alike by one query over its flattened inputs on Oxigraph

            The inputs of the snapshot naming rule are flattened, each list to its count and its sorted members, and one
            query computes the name from them on Oxigraph, apart from the reference implementation; the name it gives is
            compared with the snapshot's name.
            """
            flat = flat_inputs(snapshot)
            [solution] = Store().query(v8_query("SnapshotNamingRule", len(flat)),
                                       substitutions={Variable(f"input{n}"): Literal(v) for n, v in enumerate(flat, 1)})
            assert solution["name"].value == snapshot["name"]
