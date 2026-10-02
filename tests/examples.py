from pathlib import Path

import pytest

from cascade_pod.pod import Example

ROOT = Path(__file__).absolute().parent.parent
EXAMPLES = [Example(folder) for folder in sorted((ROOT / "example-pods").iterdir()) if folder.is_dir()]

every_example = pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.name)


def every_example_and(name, values):
    pairs = [(example, value) for example in EXAMPLES for value in values(example)]
    return pytest.mark.parametrize(f"example, {name}", pairs, ids=[f"{e.name}-{v}" for e, v in pairs])
