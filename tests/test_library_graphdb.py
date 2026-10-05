import re
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from rdflib import Graph

from cascade_pod import Failure, derive, vocabulary
from cascade_pod import graphdb as loader
from examples import ROOT
from fake_graphdb import GraphDB


@pytest.fixture
def graphdb():
    server = GraphDB()
    yield server
    server.server.shutdown()


def test_a_load_into_an_empty_graphdb_creates_the_repository_and_saves_every_question_under_its_path(graphdb, matching_pod):
    assert loader.load(matching_pod, graphdb.url) == 0
    assert graphdb.repositories == {matching_pod.name}
    assert graphdb.saved == {name: vocabulary.query(relative) for name, relative in vocabulary.questions().items()}


def test_a_load_fills_one_graph_for_each_graph_of_the_pods_store_and_the_derived_state_is_one_of_them(graphdb, matching_pod):
    assert loader.load(matching_pod, graphdb.url) == 0
    assert sorted(graphdb.graphs) == matching_pod.build("oxigraph", vocabulary.DEFAULT_LENS).store.graphs()
    derived = derive.derive(matching_pod.story_store("oxigraph"), vocabulary.DEFAULT_LENS).triples
    assert set(Graph().parse(data=graphdb.graphs[derive.DERIVED + vocabulary.DEFAULT_LENS], format="nt")) == derived


def test_a_load_refused_partway_removes_the_repository_it_created_so_a_rerun_loads(graphdb, matching_pod):
    graphdb.refuse_statements_after = 3
    with pytest.raises(Failure, match="refused"):
        loader.load(matching_pod, graphdb.url)
    assert graphdb.repositories == set()
    graphdb.refuse_statements_after = None
    assert loader.load(matching_pod, graphdb.url) == 0


def test_a_reload_after_the_repository_was_deleted_replaces_the_saved_queries(graphdb, matching_pod):
    assert loader.load(matching_pod, graphdb.url) == 0
    graphdb.repositories.clear()
    graphdb.saved = {name: "stale" for name in graphdb.saved}
    assert loader.load(matching_pod, graphdb.url) == 0
    assert "stale" not in graphdb.saved.values()


def test_a_graphdb_that_does_not_answer_is_reported_without_a_traceback(matching_pod):
    with socket.socket() as closed:
        closed.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{closed.getsockname()[1]}"
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "graphdb", str(matching_pod.folder), url],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr and result.stderr.startswith("cascade_pod graphdb: no answer"), result.stderr


def test_a_load_whose_cleanup_is_refused_still_reports_why_the_load_failed(graphdb, matching_pod):
    graphdb.refuse_statements_after, graphdb.refuse_delete = 3, True
    with pytest.raises(Failure, match="answered 500: refused"):
        loader.load(matching_pod, graphdb.url)


def test_the_graphdb_config_names_no_machine(matching_pod):
    configuration = loader.configuration(matching_pod).decode("utf-8")
    Graph().parse(data=configuration, format="turtle")
    machine = re.compile(r"file:|(?<![A-Za-z])[A-Za-z]:[\/]|localhost|127\.0\.0\.1|0\.0\.0\.0|/(?:home|Users|tmp)/|:\d{2,5}\b")
    for name, text in (("the configuration", configuration), ("graphdb.py", Path(loader.__file__).read_text(encoding="utf-8"))):
        assert machine.findall(text) == [], name
