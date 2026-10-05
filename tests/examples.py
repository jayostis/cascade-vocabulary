import ast
import subprocess
import sys
from functools import cache
from pathlib import Path

import pytest
from rdflib.plugins.sparql.parser import parseQuery

from cascade_pod import store
from cascade_pod.example import Example, Fixture

ROOT = Path(__file__).absolute().parent.parent
EXAMPLES = [Example(folder) for folder in sorted((ROOT / "example-pods").iterdir()) if folder.is_dir()]
FIXTURES = [Fixture(manifest) for manifest in sorted((ROOT / "tests" / "fixtures").glob("*/manifest.ttl"))]

every_example = pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.name)


def every_example_and(name, values):
    pairs = [(example, value) for example in EXAMPLES for value in values(example)]
    return pytest.mark.parametrize(f"example, {name}", pairs, ids=[f"{e.name}-{v}" for e, v in pairs])


def on_its_worker(fixture, *values, id):
    """A case about the fixture, run on the worker that builds it, so each fixture is built once a run."""
    return pytest.param(fixture, *values, id=id, marks=pytest.mark.xdist_group(fixture.name))


every_fixture = pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES])


@cache
def built(fixture, engine, lens):
    return fixture.build(engine, lens)


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
