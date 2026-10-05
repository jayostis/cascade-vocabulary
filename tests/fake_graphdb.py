import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rdflib import Graph, URIRef

from cascade_pod import turtle

REPOSITORY_ID = URIRef(turtle.PREFIXES["config"] + "rep.id")


def repository_id(form):
    configuration = form.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n--", 1)[0]
    [found] = Graph().parse(data=configuration.decode("utf-8"), format="turtle").objects(None, REPOSITORY_ID)
    return str(found)


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
                    graphdb.repositories.add(repository_id(body))
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

