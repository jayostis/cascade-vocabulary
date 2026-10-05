import ast
from functools import cache
from pathlib import Path

import pytest
from rdflib.plugins.sparql.parser import parseQuery

from cascade_pod import store
from cascade_pod.example import Fixture

ROOT = Path(__file__).absolute().parent.parent
FIXTURES = [Fixture(manifest) for manifest in sorted((ROOT / "tests" / "fixtures").glob("*/manifest.ttl"))]


def on_its_worker(fixture, *values, id, marks=()):
    """A case about the fixture, run on the worker that builds it, so each fixture is built once a run."""
    return pytest.param(fixture, *values, id=id, marks=[pytest.mark.xdist_group(fixture.name), *marks])


every_fixture = pytest.mark.parametrize("fixture", [on_its_worker(fixture, id=fixture.name) for fixture in FIXTURES])


@cache
def built(fixture, engine, lens):
    return fixture.build(engine, lens)


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
