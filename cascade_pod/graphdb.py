"""Creates an example's repository in a GraphDB, loads every graph of its pod's store into it, and saves every
question under its path."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

from rdflib import BNode, Literal, Namespace
from rdflib.namespace import RDF, RDFS

from . import derive, turtle, vocabulary

CONFIG, GRAPHDB = Namespace(turtle.PREFIXES["config"]), Namespace(turtle.PREFIXES["graphdb"])
LENS = "everyday"


def configuration(example):
    repository, implementation, sail = BNode(), BNode(), BNode()
    return turtle.write({
        (repository, RDF.type, CONFIG.Repository),
        (repository, CONFIG["rep.id"], Literal(example.name)),
        (repository, RDFS.label, Literal(example.title)),
        (repository, CONFIG["rep.impl"], implementation),
        (implementation, CONFIG["rep.type"], Literal("graphdb:SailRepository")),
        (implementation, CONFIG["sail.impl"], sail),
        (sail, CONFIG["sail.type"], Literal("graphdb:Sail")),
        (sail, GRAPHDB.ruleset, Literal("empty")),
        (sail, GRAPHDB["disable-sameAs"], Literal("true")),
    })


def request(method, url, body=None, content_type=None, accept=None):
    headers = {key: value for key, value in (("Content-Type", content_type), ("Accept", accept)) if value}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method=method)) as response:
        return response.read()


class GraphDB:
    def __init__(self, base, example):
        self.base, self.example = base, example
        self.repository = f"{base}/repositories/{example.name}"

    def holds_repository(self):
        listed = json.loads(request("GET", f"{self.base}/rest/repositories", accept="application/json"))
        return self.example.name in {entry["id"] for entry in listed}

    def create(self):
        boundary = uuid.uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="config"; filename="repository.ttl"\r\n'
                f"Content-Type: text/turtle\r\n\r\n").encode("utf-8")
        body += configuration(self.example) + f"\r\n--{boundary}--\r\n".encode("utf-8")
        request("POST", f"{self.base}/rest/repositories", body, f"multipart/form-data; boundary={boundary}")

    def delete(self):
        request("DELETE", f"{self.base}/rest/repositories/{self.example.name}")

    def fill(self):
        store = derive.build(self.example, "oxigraph", LENS).store
        graphs = store.graphs()
        for graph in graphs:
            context = urllib.parse.quote(f"<{graph}>", safe="")
            request("POST", f"{self.repository}/statements?context={context}", store.ntriples(graph),
                    "application/n-triples")
        saved = list(self.save_questions())
        size = request("GET", f"{self.repository}/size").decode("utf-8").strip()
        return len(graphs), saved, size

    def save_questions(self):
        listed = json.loads(request("GET", f"{self.base}/rest/sparql/saved-queries", accept="application/json"))
        held = {entry["name"] for entry in listed}
        for name, relative in vocabulary.questions().items():
            body = json.dumps({"name": name, "body": vocabulary.query(relative), "shared": True}).encode("utf-8")
            if name in held:
                replacing = urllib.parse.urlencode({"oldQueryName": name})
                request("PUT", f"{self.base}/rest/sparql/saved-queries?{replacing}", body, "application/json")
            else:
                request("POST", f"{self.base}/rest/sparql/saved-queries", body, "application/json")
            yield name


def refusal(error):
    if isinstance(error, urllib.error.HTTPError):
        return f"{error.url} answered {error.code}: {error.read().decode('utf-8', 'replace')}"
    return f"no answer: {error.reason}"


def load(example, base):
    graphdb = GraphDB(base.rstrip("/"), example)
    name = example.name
    try:
        if graphdb.holds_repository():
            print(f"cascade_pod graphdb: {base} already has a repository {name}; nothing changed", file=sys.stderr)
            return 1
        graphdb.create()
        try:
            loaded, saved, size = graphdb.fill()
        except BaseException:
            try:
                graphdb.delete()
            except urllib.error.URLError as cleanup:
                print(f"cascade_pod graphdb: could not remove the repository {name} it had created: "
                      f"{refusal(cleanup)}", file=sys.stderr)
            else:
                print(f"cascade_pod graphdb: removed the repository {name} it had created", file=sys.stderr)
            raise
    except urllib.error.URLError as error:
        print(f"cascade_pod graphdb: {refusal(error)}", file=sys.stderr)
        return 2
    print(f"{name}: {loaded} graphs, {size} statements, {len(saved)} saved queries")
    return 0
