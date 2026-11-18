import base64
import hashlib
import json
import shutil
import subprocess
import sys

import pytest

from contract import ROOT


def ni(octets):
    return base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode("ascii").rstrip("=")

LIST_A = "runtime/rule-list/5d0e7c34-6b1a-4e2f-9a58-2c4f0d8e1b73.ttl"
LIST_B = "runtime/rule-list/1cbf0000-0000-4000-8000-000000000000.ttl"
QUERY_A = "queries/matcher/same-code.rq"
QUERY_B = "queries/matcher/other.rq"
QUERY_A_BEFORE = b"SELECT ?record ?other WHERE { ?record ?p ?other }\n"
QUERY_A_AFTER = b"SELECT ?record ?other WHERE { ?record ?p ?other FILTER (?record != ?other) }\n"


def rule_list(query, query_bytes):
    return (f'<urn:row> cascade:queryPath "matcher/{query}" ;\n    cascade:queryHash <ni:///sha-256;{ni(query_bytes)}> .\n').encode()


def sha(octets):
    return hashlib.sha256(octets).hexdigest()


def run(*args, cwd):
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout


@pytest.fixture
def clone(tmp_path):
    """A scratch repository of two matcher queries, two rule lists naming one each, and the pins of all four, committed."""
    files = {
        QUERY_A: QUERY_A_BEFORE,
        QUERY_B: b"SELECT ?record ?other WHERE { ?other ?p ?record }\n",
        LIST_A: rule_list("same-code.rq", QUERY_A_BEFORE),
        LIST_B: rule_list("other.rq", b"SELECT ?record ?other WHERE { ?other ?p ?record }\n"),
    }
    for name, octets in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(octets)
    (tmp_path / "tests").mkdir(exist_ok=True)
    shutil.copy(ROOT / "tests" / "rehash_rule_lists.py", tmp_path / "tests")
    (tmp_path / "tests" / "published-bytes.json").write_text(
        json.dumps(dict(sorted((name, sha(octets)) for name, octets in files.items())), indent=2) + "\n", encoding="utf-8")
    for command in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "was"]):
        run("git", *command, cwd=tmp_path)
    return tmp_path


def rehash(clone):
    run(sys.executable, "-I", "tests/rehash_rule_lists.py", "--was", "HEAD", cwd=clone)
    return json.loads((clone / "tests" / "published-bytes.json").read_text(encoding="utf-8"))


class TestChecksOfTheReHashScript:
    """Checks of the re-hash script · tests/rehash_rule_lists.py

    The script writes the hash of an edited matcher query into every rule list row that named the query's old bytes, and
    writes the pins the test "keeps the bytes it was published with" compares only for what it re-hashed, so that every other
    edit of a published file is still named by that test. Each case runs it in a scratch clone with `--was HEAD`.
    """

    class TestGivenAQueryEditedAndItsRuleListRehashed:
        def test_pins_the_query_and_the_rule_list_at_their_new_bytes(self, clone):
            """pins the query and the rule list at their new bytes

            Only the query is edited; the rule list's row is written with the new hash, and the pins of both files are the
            hashes of the bytes now.
            """
            (clone / QUERY_A).write_bytes(QUERY_A_AFTER)
            pins = rehash(clone)
            assert (clone / LIST_A).read_bytes() == rule_list("same-code.rq", QUERY_A_AFTER)
            assert pins[QUERY_A] == sha(QUERY_A_AFTER)
            assert pins[LIST_A] == sha((clone / LIST_A).read_bytes())

    class TestGivenARuleListAlsoEditedByHand:
        def test_keeps_the_pin_of_the_rule_list(self, clone):
            """keeps the pin of the rule list

            The query is edited and a triple is added to the rule list that names it; the rule list's row is re-hashed, but
            its pin stays the hash of its bytes at `--was`, so the test "keeps the bytes it was published with" names it.
            """
            was = (clone / LIST_A).read_bytes()
            (clone / QUERY_A).write_bytes(QUERY_A_AFTER)
            (clone / LIST_A).write_bytes(was + b"<urn:row> cascade:note 'by hand' .\n")
            pins = rehash(clone)
            assert pins[LIST_A] == sha(was)
            assert pins[LIST_A] != sha((clone / LIST_A).read_bytes())

    class TestGivenAPublishedRuleListDeleted:
        def test_keeps_its_pin(self, clone):
            """keeps its pin

            A rule list is removed with `git rm`; its pin stays in `tests/published-bytes.json`, so a deleted published file is
            no more a pass of the test than an edited one.
            """
            was = (clone / LIST_B).read_bytes()
            run("git", "rm", "-q", LIST_B, cwd=clone)
            assert rehash(clone)[LIST_B] == sha(was)
