"""Make every name that follows a version's content follow it, after the saved Bridge output or an entry is regenerated.

    python3 tests/rename_after_regeneration.py [--was <ref>] [--check]

A version is named from its content, so a regeneration or an edit of a content term renames it, and every name written beside
it follows: the matcher judgment names and the version names in the features, the versions a judgment file was derived from,
the file names naming.feature's N9 gives, and tests/matcher-judgment-versions.json. This script, in order:

1. names each version of the saved graphs under bridge/ and of the entries under entries/ at <ref> (default HEAD) and as they
   are now, by the saved graph's own version subject and by the content rule for an entry's draft, and pairs the old name
   with the new one by the file and the record it is in;
2. writes the new name over the old, as an ni: name and as the lower-case hex a file name is made of, in every runtime and
   conformance file but a downloaded one, and in tests/matcher-judgment-versions.json;
3. reads tests/matcher-judgment-versions.json again from the saved graphs, a record's versions in the order of the episodes
   that wrote them;
4. gives every name a feature writes beside its inputs, and every name a kit's matcher judgment table writes beside its
   members and what it used, the name its rule gives, until none changes: a matcher judgment's name holds its members' and
   its used versions' names, so one round renames the judgments and the next the assertions.

5. gives each file name naming.feature's N9 writes beside an ni: name the hex of that name's hash.

<ref> is the commit the saved output and the entries were last consistent with the names: a version renamed before it is not
found. It does not reach a name beside no inputs in a runtime feature, as a table of members and used under runtime/matcher.feature:
its labels, `allergy SNOMED 373270004` and `version 1 of ...`, name a draft of an entry the example enters, and no file says
which. Those are recomputed by hand from the entry's drafts, as naming.py names them.

With --check nothing is written and the exit status says whether anything would change.
"""

import argparse
import base64
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contract  # noqa: E402
import naming  # noqa: E402
import test_naming  # noqa: E402
from pyoxigraph import NamedNode, Triple  # noqa: E402

ROOT = contract.ROOT
PROV_SPECIALIZATION = NamedNode(naming.PROV + "specializationOf")
PROV_ACTIVITY = NamedNode(naming.PROV + "Activity")
RDF_TYPE = NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
SOURCE_URL = NamedNode(naming.CASCADE + "sourceUrl")
VERSIONS_FILE = ROOT / "tests" / "matcher-judgment-versions.json"
NI = "ni:///sha-256;"


def git(*args):
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    return done.stdout.decode("utf-8") if done.returncode == 0 else None


def tracked(*patterns):
    return [f for f in git("ls-files", *patterns).splitlines() if f and "/downloads/" not in f]


def graph_versions(text):
    """A saved graph's versions: for each record, by the record's source URL, its versions' names."""
    triples = naming.content(text, "turtle")
    urls = {t.subject: t.object.value for t in triples if t.predicate == SOURCE_URL}
    found = {}
    for t in sorted(triples, key=lambda t: str(t)):
        if t.predicate == PROV_SPECIALIZATION and t.subject.value.startswith(NI):
            found.setdefault(urls.get(t.object, t.object.value), []).append(t.subject.value)
    return found


def entry_versions(text):
    """An entry's drafts' versions, by position: the content rule over each draft's triples, a reference to another draft
    replaced by that record's name."""
    triples = naming.content(text, "turtle")
    session = next(t.subject.value for t in triples if t.predicate == RDF_TYPE and t.object == PROV_ACTIVITY)
    count = len({t.subject.value for t in triples if re.fullmatch(r"urn:cascade:output-\d+-version", t.subject.value)})
    records = {NamedNode(f"urn:cascade:output-{n}"): NamedNode(naming.entered_record_name(session, n)) for n in range(count)}
    found = {}
    for n in range(count):
        subject = NamedNode(f"urn:cascade:output-{n}-version")
        content = {Triple(naming.THIS_VERSION, t.predicate, records.get(t.object, t.object))
                   for t in triples if t.subject == subject}
        found[str(n)] = [naming.version_name(content)]
    return found


def versions_of(read, files):
    """Each file's versions as read() gives them, for the files read() can read."""
    out = {}
    for path in files:
        text = read(path)
        if text is not None:
            try:
                out[path] = (graph_versions if "/bridge/" in path else entry_versions)(text)
            except Exception:  # noqa: BLE001 - a file in neither shape has no versions to pair
                pass
    return out


def renames(was):
    files = tracked("runtime/**/bridge/**/graph.ttl", "conformance/**/bridge/**/graph.ttl", "runtime/**/entries/*.ttl",
                    "conformance/**/entries/*.ttl")
    before = versions_of(lambda p: git("show", f"{was}:{p}"), files)
    after = versions_of(lambda p: (ROOT / p).read_text(encoding="utf-8") if (ROOT / p).exists() else None, files)
    renamed = {}
    for path, now in after.items():
        for key, new in now.items():
            old = before.get(path, {}).get(key)
            if old and len(old) == len(new):
                renamed.update({o: n for o, n in zip(old, new) if o != n})
    return renamed


def hex_of(name):
    digest = name.removeprefix(NI)
    return base64.urlsafe_b64decode(digest + "=" * (-len(digest) % 4)).hex()


def rewrite(change, check, written):
    """Apply change(text) to every runtime and conformance file and the versions file."""
    for path in [*tracked("runtime", "conformance"), VERSIONS_FILE.relative_to(ROOT).as_posix()]:
        p = ROOT / path
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = change(text)
        if new != text:
            written.add(path)
            if not check:
                p.write_text(new, encoding="utf-8", newline="")


def versions_from_saved_graphs():
    """Per kit and handle, the versions of the record the handle names, from the saved graphs under the kit's bridge/ folders
    in episode order; a handle a kit's matcher judgments use."""
    old = json.loads(VERSIONS_FILE.read_text(encoding="utf-8"))
    out = {}
    for kit in old:
        handles = json.loads((ROOT / "conformance" / kit / "expected" / "handles.json").read_text(encoding="utf-8"))["records"]
        episodes = sorted((ROOT / "conformance" / kit).glob("scripted-input/*/bridge/E*/*/graph.ttl"),
                          key=lambda p: (int(re.search(r"/E(\d+)/", p.as_posix())[1]), p.as_posix()))
        by_url = {}
        for path in episodes:
            for url, names in graph_versions(path.read_text(encoding="utf-8")).items():
                for name in names:
                    if name not in by_url.setdefault(url, []):
                        by_url[url].append(name)
        out[kit] = {}
        for handle in old[kit]:
            given = handles[handle]
            out[kit][handle] = by_url[f"{given['server']}/{given['type']}/{given['id']}"]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--was", default="HEAD")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    written = set()

    renamed = renames(args.was)
    held = json.loads(VERSIONS_FILE.read_text(encoding="utf-8"))
    fresh = versions_from_saved_graphs()
    for kit, handles in fresh.items():
        for handle, names in handles.items():
            if len(names) == len(held[kit][handle]):
                renamed.update({o: n for o, n in zip(held[kit][handle], names) if o != n})
    if renamed:
        by_text = {**renamed, **{hex_of(old): hex_of(new) for old, new in renamed.items()}}
        pattern = re.compile("|".join(sorted(map(re.escape, by_text), key=len, reverse=True)))
        rewrite(lambda text: pattern.sub(lambda m: by_text[m[0]], text), args.check, written)

    text = json.dumps(fresh, indent=2) + "\n"
    if VERSIONS_FILE.read_text(encoding="utf-8") != text:
        written.add(VERSIONS_FILE.relative_to(ROOT).as_posix())
        if not args.check:
            VERSIONS_FILE.write_text(text, encoding="utf-8", newline="")

    for _ in range(6):
        for module in (contract, test_naming):
            importlib.reload(module)
        wrong = {}
        for inputs, name in sorted(set(test_naming.names_beside_inputs())):
            right = naming.named(*test_naming.inputs_of(inputs))
            if right != name:
                wrong[name] = right
        wrong.update({name: computed for _, _, _, name, computed in test_naming.kit_judgment_names(
            test_naming.matcher_judgments_written_with_what_they_used()) if computed != name})
        if not wrong:
            break
        if args.check:
            written.add("a name beside its inputs")
            break
        rewrite(lambda text: re.sub("|".join(map(re.escape, wrong)), lambda m: wrong[m[0]], text), False, written)
    stems = re.compile(r'(<(ni:///sha-256;[A-Za-z0-9_-]+)>\s*\|\s*")[0-9a-f]{64}(\.ttl")')
    rewrite(lambda text: stems.sub(lambda m: m[1] + contract.file_stem(m[2]) + m[3], text), args.check, written)
    print("\n".join(sorted(written)) or "nothing to change")
    return 1 if written and args.check else 0


sys.exit(main())
