"""Re-hash the rule lists after a matcher query is edited in place.

    python3 tests/rehash_rule_lists.py [--was <ref>] [--check]

A rule list row names its query by `cascade:queryPath` and the hash of the query's bytes, `cascade:queryHash`. Each row,
in every rule list version and in the copies of them under runtime/scripted-input/ and conformance/, whose hash is the
one the query had at <ref> (default origin/main) gets the hash of the query as it is now; a row with some other hash,
as the examples that give a run a hash its bytes do not have, is left as it is. The hex hash in tests/published-bytes.json, which
the test "keeps the bytes it was published with" compares, is written again only for a rule list this run wrote and for a matcher
query whose rows it re-hashed; a file new to the listed globs is added, and every other entry, those outside the globs too, is kept.
A published file edited for any other reason keeps its pin and fails that test, so the edit is a named change.
With --check nothing is written and the exit status says whether anything would change.
"""

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROW = re.compile(r'(cascade:queryPath "(matcher/[^"]+)" ;\s*cascade:queryHash )<ni:///sha-256;([A-Za-z0-9_-]+)>')
PUBLISHED_FILES = ("runtime/rule-list/[0-9a-f]*.ttl", "queries/matcher/*.rq")


def ni(octets):
    return base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode("ascii").rstrip("=")


def bytes_at(ref, relative):
    done = subprocess.run(["git", "show", f"{ref}:{relative}"], cwd=ROOT, capture_output=True)
    return done.stdout if done.returncode == 0 else None


def rehashed(text, ref, queries):
    def row(match):
        head, path, held = match.groups()
        now = (ROOT / "queries" / path).read_bytes()
        before = bytes_at(ref, f"queries/{path}")
        if before is None or ni(before) != held:
            return match.group(0)
        queries.add(f"queries/{path}")
        return f"{head}<ni:///sha-256;{ni(now)}>"

    return ROW.sub(row, text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--was", default="origin/main")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = []
    queries, written = set(), set()
    for folder in ("runtime", "conformance"):
        for path in sorted((ROOT / folder).rglob("*.ttl")):
            text = path.read_text(encoding="utf-8")
            new = rehashed(text, args.was, queries)
            if new != text:
                changed.append(path.relative_to(ROOT).as_posix())
                written.add(path.relative_to(ROOT).as_posix())
                if not args.check:
                    path.write_text(new, encoding="utf-8", newline="")
    listing = ROOT / "tests" / "published-bytes.json"
    published = json.loads(listing.read_text(encoding="utf-8"))
    for pattern in PUBLISHED_FILES:
        for p in ROOT.glob(pattern):
            name = p.relative_to(ROOT).as_posix()
            if name not in published or name in written or name in queries:
                published[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    published = {name: pin for name, pin in published.items() if (ROOT / name).exists()}
    text = json.dumps(dict(sorted(published.items())), indent=2) + "\n"
    if listing.read_text(encoding="utf-8") != text:
        changed.append("tests/published-bytes.json")
        if not args.check:
            listing.write_text(text, encoding="utf-8", newline="")
    print("\n".join(changed) or "nothing to change")
    return 1 if changed and args.check else 0


sys.exit(main())
