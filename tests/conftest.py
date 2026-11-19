import pytest

from engines import parse_each_query_once
from page import page_properties

pytest_plugins = ["group_budget"]

parse_each_query_once()


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Puts each case that names no xdist_group with the rest of its module, so what a module builds and caches is
    built on one worker, once, and gives each case what the tests page shows of it."""
    for item in items:
        if item.get_closest_marker("xdist_group") is None:
            item.add_marker(pytest.mark.xdist_group(item.module.__name__))
        item.user_properties.extend(page_properties(item))


def pytest_collection_finish(session):
    """Every worker that holds a test_queries case, before any case runs, takes its share of the parses the module's
    cases read, so the parsing is spread over the workers instead of done by the one that draws the first case."""
    if any(item.module.__name__ == "test_queries" for item in session.items):
        import test_queries

        test_queries.parse_every_query()
