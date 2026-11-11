import pytest

from engines import parse_each_query_once
from page import page_properties

parse_each_query_once()


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Puts each case that names no xdist_group with the rest of its module, so what a module builds and caches is
    built on one worker, once, and gives each case what the tests page shows of it."""
    for item in items:
        if item.get_closest_marker("xdist_group") is None:
            item.add_marker(pytest.mark.xdist_group(item.module.__name__))
        item.user_properties.extend(page_properties(item))
