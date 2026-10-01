import json
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from rdflib import Graph

from cascade_pod import derive, store, vocabulary
from cascade_pod.pod import Example

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
ALEX = Example(EXAMPLE)


class GraphDB:
    """Answers the loader as a GraphDB does: a repository by its id, statements into it by graph, and workbench-global
    saved queries whose names POST refuses twice and PUT replaces by the oldQueryName it is given."""

    def __init__(self):
        self.repositories, self.saved, self.refuse_statements_after, self.refuse_delete = set(), {}, None, False
        self.statements, self.graphs = 0, {}
        graphdb = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def answer(self, code, body=b"", content_type="text/plain"):
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def body(self):
                return self.rfile.read(int(self.headers.get("Content-Length", 0)))

            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/rest/repositories":
                    self.answer(200, json.dumps([{"id": r} for r in sorted(graphdb.repositories)]).encode(), "application/json")
                elif path == "/rest/sparql/saved-queries":
                    self.answer(200, json.dumps([{"name": n, "body": b} for n, b in graphdb.saved.items()]).encode(),
                                "application/json")
                elif path.endswith("/size") and path.split("/")[2] in graphdb.repositories:
                    self.answer(200, str(graphdb.statements).encode())
                else:
                    self.answer(404)

            def do_POST(self):
                path, body = urlparse(self.path).path, self.body()
                if path == "/rest/repositories":
                    graphdb.repositories.add("alex-rivera")
                    self.answer(201)
                elif path.endswith("/statements") and path.split("/")[2] in graphdb.repositories:
                    if graphdb.refuse_statements_after is not None and graphdb.statements >= graphdb.refuse_statements_after:
                        self.answer(500, b"refused")
                    else:
                        graphdb.statements += 1
                        [context] = parse_qs(urlparse(self.path).query)["context"]
                        graphdb.graphs[context.strip("<>")] = body.decode("utf-8")
                        self.answer(204)
                elif path == "/rest/sparql/saved-queries":
                    query = json.loads(body)
                    if query["name"] in graphdb.saved:
                        self.answer(400, f"Query '{query['name']}' already exists".encode())
                    else:
                        graphdb.saved[query["name"]] = query["body"]
                        self.answer(201)
                else:
                    self.answer(404)

            def do_PUT(self):
                url, query = urlparse(self.path), json.loads(self.body())
                [old] = parse_qs(url.query).get("oldQueryName", [None])
                if old is None:
                    self.answer(500, b"Required request parameter 'oldQueryName' is not present")
                elif url.path == "/rest/sparql/saved-queries" and old in graphdb.saved:
                    del graphdb.saved[old]
                    graphdb.saved[query["name"]] = query["body"]
                    self.answer(200)
                else:
                    self.answer(404)

            def do_DELETE(self):
                path = urlparse(self.path).path
                repository = path.rsplit("/", 1)[-1]
                if graphdb.refuse_delete:
                    self.answer(500, b"cannot delete")
                elif path.startswith("/rest/repositories/") and repository in graphdb.repositories:
                    graphdb.repositories.discard(repository)
                    graphdb.statements = 0
                    self.answer(200)
                else:
                    self.answer(404)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


@pytest.fixture
def graphdb():
    server = GraphDB()
    yield server
    server.server.shutdown()


def load(url):
    return subprocess.run([sys.executable, "-m", "cascade_pod", "graphdb", str(EXAMPLE), url],
                          capture_output=True, text=True, cwd=ROOT)


def test_a_load_into_an_empty_graphdb_creates_the_repository_and_saves_the_queries(graphdb):
    result = load(graphdb.url)
    assert result.returncode == 0, result.stderr
    assert graphdb.repositories == {"alex-rivera"} and graphdb.saved


def test_a_load_adds_the_derived_state_under_the_everyday_lens_as_a_graph_of_its_own(graphdb):
    assert load(graphdb.url).returncode == 0
    derived = derive.derive(derive.loaded(ALEX, "oxigraph"), "everyday")
    posted = Graph().parse(data=graphdb.graphs["urn:cascade:derived:everyday"], format="nt")
    assert {tuple(store.from_rdflib(t) for t in triple) for triple in posted} == derived


def test_a_load_fills_one_graph_for_each_graph_of_the_pod_in_the_builders_store(graphdb):
    assert load(graphdb.url).returncode == 0
    assert sorted(graphdb.graphs) == derive.build(ALEX, "oxigraph").store.graphs()


def test_a_load_saves_every_question_under_its_path_in_questions(graphdb):
    assert load(graphdb.url).returncode == 0
    assert graphdb.saved == {name: vocabulary.query(relative) for name, relative in vocabulary.questions().items()}


def test_a_load_refused_partway_removes_the_repository_it_created_so_a_rerun_loads(graphdb):
    graphdb.refuse_statements_after = 3
    result = load(graphdb.url)
    assert result.returncode == 2 and "refused" in result.stderr
    assert graphdb.repositories == set()
    graphdb.refuse_statements_after = None
    result = load(graphdb.url)
    assert result.returncode == 0, result.stderr


def test_a_reload_after_the_repository_was_deleted_replaces_the_saved_queries(graphdb):
    assert load(graphdb.url).returncode == 0
    graphdb.repositories.clear()
    graphdb.saved = {name: "stale" for name in graphdb.saved}
    result = load(graphdb.url)
    assert result.returncode == 0, result.stderr
    assert "stale" not in graphdb.saved.values()


def test_a_graphdb_that_does_not_answer_is_reported_without_a_traceback():
    with socket.socket() as closed:
        closed.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{closed.getsockname()[1]}"
    result = load(url)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr and result.stderr.startswith("cascade_pod graphdb: ")


def test_a_load_whose_cleanup_is_refused_still_reports_why_the_load_failed(graphdb):
    graphdb.refuse_statements_after, graphdb.refuse_delete = 3, True
    result = load(graphdb.url)
    assert result.returncode == 2 and "answered 500: refused" in result.stderr, result.stderr
