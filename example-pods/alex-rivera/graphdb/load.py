"""Creates the alex-rivera repository in a GraphDB, loads the finished pod and its derived state, and saves every question.

python3 example-pods/alex-rivera/graphdb/load.py <GraphDB URL>
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import rdflib
from rdflib.namespace import OWL, RDF

rdflib.NORMALIZE_LITERALS = False

GRAPHDB = Path(__file__).absolute().parent
EXAMPLE = GRAPHDB.parent
ROOT = EXAMPLE.parent.parent
sys.path.insert(0, str(EXAMPLE / "queries"))
import build  # noqa: E402

REPOSITORY = "alex-rivera"
LENS = "everyday"
DERIVED = f"urn:cascade:derived:{LENS}"


def request(method, url, body=None, content_type=None, accept=None):
    headers = {key: value for key, value in (("Content-Type", content_type), ("Accept", accept)) if value}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method=method)) as response:
        return response.read()


def repositories(base):
    return {entry["id"] for entry in json.loads(request("GET", f"{base}/rest/repositories", accept="application/json"))}


def create(base):
    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="config"; filename="repository.ttl"\r\n'
            f"Content-Type: text/turtle\r\n\r\n").encode("utf-8")
    body += (GRAPHDB / "repository.ttl").read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    request("POST", f"{base}/rest/repositories", body, f"multipart/form-data; boundary={boundary}")


def graphs():
    """Each graph to load, by its name, as N-Triples: every RDF file of the finished pod at its address, each
    vocabulary, and the derived state."""
    manifest = build.events()
    for path in sorted(build.pod_files() + manifest["derived"]):
        if not path.startswith(build.NOT_RDF):
            address = build.POD_BASE + path
            graph = rdflib.Graph().parse(build.POD / path, format="turtle", publicID=address)
            yield address, graph.serialize(format="nt", encoding="utf-8")
    for path in sorted((ROOT / "ontologies").glob("*/*/*.ttl")):
        if not path.name.endswith(".shapes.ttl"):
            graph = rdflib.Graph().parse(path, format="turtle")
            yield str(next(graph.subjects(RDF.type, OWL.Ontology))), graph.serialize(format="nt", encoding="utf-8")
    derived = build.derive(build.loaded("oxigraph"), LENS)
    yield DERIVED, "".join(line + "\n" for line in build.ntriples(derived)).encode("utf-8")


def load(base, name, body):
    context = urllib.parse.quote(f"<{name}>", safe="")
    request("POST", f"{base}/repositories/{REPOSITORY}/statements?context={context}", body, "application/n-triples")


def save_questions(base):
    saved = {entry["name"] for entry in json.loads(request("GET", f"{base}/rest/sparql/saved-queries", accept="application/json"))}
    for name, relative in build.questions().items():
        query = {"name": name, "body": build.query_text(relative), "shared": True}
        body = json.dumps(query).encode("utf-8")
        if name in saved:
            replacing = urllib.parse.urlencode({"oldQueryName": name})
            request("PUT", f"{base}/rest/sparql/saved-queries?{replacing}", body, "application/json")
        else:
            request("POST", f"{base}/rest/sparql/saved-queries", body, "application/json")
        yield name


def fill(base):
    loaded = 0
    for name, body in graphs():
        load(base, name, body)
        loaded += 1
    saved = list(save_questions(base))
    size = request("GET", f"{base}/repositories/{REPOSITORY}/size").decode("utf-8").strip()
    return loaded, saved, size


def refusal(error):
    if isinstance(error, urllib.error.HTTPError):
        return f"{error.url} answered {error.code}: {error.read().decode('utf-8', 'replace')}"
    return f"no answer: {error.reason}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="the GraphDB's base URL")
    base = parser.parse_args().url.rstrip("/")
    try:
        if REPOSITORY in repositories(base):
            print(f"load.py: {base} already has a repository {REPOSITORY}; nothing changed", file=sys.stderr)
            return 1
        create(base)
        try:
            loaded, saved, size = fill(base)
        except BaseException:
            try:
                request("DELETE", f"{base}/rest/repositories/{REPOSITORY}")
            except urllib.error.URLError as cleanup:
                print(f"load.py: could not remove the repository {REPOSITORY} it had created: {refusal(cleanup)}",
                      file=sys.stderr)
            else:
                print(f"load.py: removed the repository {REPOSITORY} it had created", file=sys.stderr)
            raise
    except urllib.error.URLError as error:
        print(f"load.py: {refusal(error)}", file=sys.stderr)
        return 2
    print(f"{REPOSITORY}: {loaded} graphs, {size} statements, {len(saved)} saved queries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
