import os
import time
import traceback

import pytest

from alex_rivera import KIT
from cascade_pod import story
from cascade_pod.example import Example
from examples import ROOT

WAIT = 600


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Puts each case that names no xdist_group with the rest of its module, so what a module builds and caches is
    built on one worker, once."""
    for item in items:
        if item.get_closest_marker("xdist_group") is None:
            item.add_marker(pytest.mark.xdist_group(item.module.__name__))


def replayed_once(tmp_path_factory, kit):
    """The kit replayed once a run, with the files the build writes for its last step, in a folder every worker
    shares: the first to ask replays it, and the others wait for it."""
    shared = tmp_path_factory.getbasetemp()
    if os.environ.get("PYTEST_XDIST_WORKER"):
        shared = shared.parent
    folder, done, failed = shared / kit.name, shared / f"{kit.name}.done", shared / f"{kit.name}.failed"
    try:
        (shared / f"{kit.name}.replaying").mkdir()
    except FileExistsError:
        deadline = time.monotonic() + WAIT
        while not done.exists():
            if failed.exists():
                pytest.fail(f"the replay of {kit.name} failed on another worker:\n{failed.read_text(encoding='utf-8')}")
            if time.monotonic() > deadline:
                pytest.fail(f"the replay of {kit.name} did not finish in {WAIT} seconds")
            time.sleep(0.05)
        return Example(folder)
    try:
        story.replayed(kit, folder)
    except BaseException:
        failed.write_text(traceback.format_exc(), encoding="utf-8")
        raise
    done.touch()
    return Example(folder)


@pytest.fixture(scope="session")
def alex(tmp_path_factory):
    """The conformance kit's story replayed, with new import and session IDs."""
    return replayed_once(tmp_path_factory, KIT)


@pytest.fixture(scope="session")
def matching_pod(tmp_path_factory):
    """The matching vectors' story replayed: a small pod with an import, entries, judgments and matcher runs."""
    return replayed_once(tmp_path_factory, ROOT / "runtime" / "vectors" / "matching")
