import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Puts each case that names no xdist_group with the rest of its module, so what a module builds and caches is
    built on one worker, once."""
    for item in items:
        if item.get_closest_marker("xdist_group") is None:
            item.add_marker(pytest.mark.xdist_group(item.module.__name__))
