import pytest

from engines import parse_each_query_once, use_parse_store
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


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Keeps the parses of the queries under this checkout's pytest cache, where a run finds those an earlier run made."""
    if getattr(config, "cache", None) is not None:
        use_parse_store(config.cache.mkdir("sparql_parses"))


def pytest_collection_finish(session):
    """Every worker collects every case, so each takes its share of the parses the test_queries cases read before any
    case runs, and the parsing is spread over the workers instead of done by the one that draws the first case."""
    if not session.config.option.collectonly and any(item.module.__name__ == "test_queries" for item in session.items):
        import test_queries

        test_queries.parse_every_query()
