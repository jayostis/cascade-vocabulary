import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from rdflib.plugins.sparql.parser import parseQuery

from cascade_pod import store
from cascade_pod.example import Example

ROOT = Path(__file__).absolute().parent.parent
EXAMPLES = [Example(folder) for folder in sorted((ROOT / "example-pods").iterdir()) if folder.is_dir()]

every_example = pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.name)


def every_example_and(name, values):
    pairs = [(example, value) for example in EXAMPLES for value in values(example)]
    return pytest.mark.parametrize(f"example, {name}", pairs, ids=[f"{e.name}-{v}" for e, v in pairs])


def run_matcher(folder, read_through, at, out, takes=None):
    options = ["--read-through", read_through, "--at", at, "--out", str(out)] + (["--takes", takes] if takes else [])
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "match", str(folder), *options],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    return {p.relative_to(out).as_posix(): p for p in Path(out).rglob("*") if p.is_file()}


def pod_file(example, relative):
    return store.parsed(example.pod / relative, example.address + relative)


def queries_held(source):
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                parseQuery(node.value)
            except Exception:
                continue
            found.append(node.value)
    return found


def moved(example, moves, folder, added=None):
    """A copy of the example in `folder`, with each file `moves` names moved to the path it gives, and each file `added`
    names added to the last event with the text it gives."""
    copy = Path(folder) / example.name
    shutil.copytree(example.pod, copy / "pod")
    shutil.copy(example.folder / "ro-crate-metadata.json", copy)
    story = json.loads((example.folder / "events.json").read_text(encoding="utf-8"))
    for event in story["events"]:
        event["adds"] = [moves.get(path, path) for path in event["adds"]]
    for path, target in moves.items():
        (copy / "pod" / target).parent.mkdir(parents=True, exist_ok=True)
        (copy / "pod" / path).rename(copy / "pod" / target)
    for path, text in (added or {}).items():
        (copy / "pod" / path).parent.mkdir(parents=True, exist_ok=True)
        (copy / "pod" / path).write_text(text, encoding="utf-8")
        story["events"][-1]["adds"].append(path)
    (copy / "events.json").write_text(json.dumps(story), encoding="utf-8")
    return Example(copy)
