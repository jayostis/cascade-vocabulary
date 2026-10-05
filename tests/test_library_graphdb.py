import re
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from rdflib import Graph

from cascade_pod import derive, vocabulary
from cascade_pod import graphdb as loader
from examples import EXAMPLES, ROOT, GraphDB, every_example


@pytest.fixture
def graphdb():
    server = GraphDB()
    yield server
    server.server.shutdown()


def load(example, url):
    return subprocess.run([sys.executable, "-m", "cascade_pod", "graphdb", str(example.folder), url],
                          capture_output=True, text=True, cwd=ROOT)


@every_example
def test_a_load_into_an_empty_graphdb_creates_the_repository_and_saves_the_queries(graphdb, example):
    result = load(example, graphdb.url)
    assert result.returncode == 0, result.stderr
    assert graphdb.repositories == {example.name} and graphdb.saved


@every_example
def test_a_load_adds_the_derived_state_under_the_everyday_lens_as_a_graph_of_its_own(graphdb, example):
    assert load(example, graphdb.url).returncode == 0
    derived = derive.derive(example.story_store("oxigraph"), vocabulary.DEFAULT_LENS).triples
    posted = Graph().parse(data=graphdb.graphs["urn:cascade:derived:everyday"], format="nt")
    assert set(posted) == derived


@every_example
def test_a_load_fills_one_graph_for_each_graph_of_the_pod_in_the_builders_store(graphdb, example):
    assert load(example, graphdb.url).returncode == 0
    assert sorted(graphdb.graphs) == example.build("oxigraph", vocabulary.DEFAULT_LENS).store.graphs()


@every_example
def test_a_load_saves_every_question_under_its_path_in_questions(graphdb, example):
    assert load(example, graphdb.url).returncode == 0
    assert graphdb.saved == {name: vocabulary.query(relative) for name, relative in vocabulary.questions().items()}


@every_example
def test_a_load_refused_partway_removes_the_repository_it_created_so_a_rerun_loads(graphdb, example):
    graphdb.refuse_statements_after = 3
    result = load(example, graphdb.url)
    assert result.returncode == 2 and "refused" in result.stderr
    assert graphdb.repositories == set()
    graphdb.refuse_statements_after = None
    result = load(example, graphdb.url)
    assert result.returncode == 0, result.stderr


@every_example
def test_a_reload_after_the_repository_was_deleted_replaces_the_saved_queries(graphdb, example):
    assert load(example, graphdb.url).returncode == 0
    graphdb.repositories.clear()
    graphdb.saved = {name: "stale" for name in graphdb.saved}
    result = load(example, graphdb.url)
    assert result.returncode == 0, result.stderr
    assert "stale" not in graphdb.saved.values()


def test_a_graphdb_that_does_not_answer_is_reported_without_a_traceback():
    with socket.socket() as closed:
        closed.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{closed.getsockname()[1]}"
    result = load(EXAMPLES[0], url)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr and result.stderr.startswith("cascade_pod graphdb: ")


@every_example
def test_a_load_whose_cleanup_is_refused_still_reports_why_the_load_failed(graphdb, example):
    graphdb.refuse_statements_after, graphdb.refuse_delete = 3, True
    result = load(example, graphdb.url)
    assert result.returncode == 2 and "answered 500: refused" in result.stderr, result.stderr


@every_example
def test_the_graphdb_config_names_no_machine(example):
    configuration = loader.configuration(example).decode("utf-8")
    Graph().parse(data=configuration, format="turtle")
    machine = re.compile(r"file:|(?<![A-Za-z])[A-Za-z]:[\/]|localhost|127\.0\.0\.1|0\.0\.0\.0|/(?:home|Users|tmp)/|:\d{2,5}\b")
    for name, text in (("the configuration", configuration), ("graphdb.py", Path(loader.__file__).read_text(encoding="utf-8"))):
        assert machine.findall(text) == [], name
