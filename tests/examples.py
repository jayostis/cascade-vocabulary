import subprocess
import sys
from pathlib import Path

import pytest

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
