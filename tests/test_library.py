import ast
import hashlib
import re
import subprocess
import sys

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, URIRef
from rdflib.compare import to_isomorphic
from rdflib.namespace import XSD

from cascade_pod import Failure, ask, derive, site, store, turtle, vocabulary
from cascade_pod.pod import Example
from examples import ROOT, every_example

RECOMPUTED_SHA256 = "409b3dd5420a1a6f9707c802fa1bd7ed26e4d0c98119519968faa698344608f3"


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
def test_a_triple_stated_in_two_files_is_counted_once_by_a_query_over_the_default_graph(engine, tmp_path):
    held = store.ENGINES[engine]()
    for name in ("one", "two"):
        path = tmp_path / f"{name}.ttl"
        path.write_text("<urn:x:s> <urn:x:p> <urn:x:o> .\n", encoding="utf-8")
        held.load(path, f"urn:x:{name}")
    assert held.select("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }") == [{"n": Literal("1", datatype=XSD.integer)}]
    assert held.select("SELECT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g") == [
        {"g": URIRef("urn:x:one")}, {"g": URIRef("urn:x:two")}]


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
@every_example
def test_ask_prints_the_rows_the_builders_store_returns(example, engine):
    question = "record/Why it is in no view"
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "ask", str(example.folder), question, "--engine", engine],
                            capture_output=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    held = example.store(engine, vocabulary.DEFAULT_LENS)
    rows = held.select(vocabulary.query(vocabulary.questions()[question]))
    assert rows and result.stdout.decode("utf-8").splitlines() == [ask.line(row) for row in rows]


def turtle_text(source):
    return [node.value for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and TURTLE_TEXT.search(node.value)]


TURTLE_TEXT = re.compile(r"@prefix|\^\^| [.;,]$")


def test_the_turtle_text_check_finds_a_statement_built_in_a_string():
    assert turtle_text('LINE = f"<{s}> <{p}> <{o}> ."') == ["> ."]


@pytest.mark.parametrize("module", sorted(path.name for path in (ROOT / "cascade_pod").glob("*.py") if path.name != "turtle.py"))
def test_no_module_but_turtle_builds_turtle_text(module):
    assert turtle_text((ROOT / "cascade_pod" / module).read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("iri", ["https://pod.example/clinical/allergies.ttl", "https://pod.example/clinical/allergies.ttl#x",
                                 "https://pod.example/clinical/", "https://pod.example/clinical/other.ttl",
                                 "https://pod.example/clinical/#x", "https://pod.example/clinical//x",
                                 "https://pod.example/clinical/a:b", "https://pod.example/clinical/?q"])
def test_every_iri_the_writer_writes_reads_back_as_itself(iri):
    base = "https://pod.example/clinical/allergies.ttl"
    triple = (URIRef(iri), URIRef("urn:x:p"), URIRef(iri))
    assert set(store.parsed_text(turtle.write({triple}, base), base)) == {triple}


def test_a_folder_that_is_no_example_is_refused_in_one_line_without_a_traceback():
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "build", str(ROOT / "example-pods" / "no-such-example"),
                             "--engine", "oxigraph"], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 2
    assert result.stderr.startswith("cascade_pod build: ") and "Traceback" not in result.stderr, result.stderr


@every_example
def test_an_unknown_lens_is_refused_by_name_without_a_traceback(example):
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "ask", str(example.folder), "record/Why it is in no view",
                             "--lens", "nope"], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 2
    assert "invalid choice: 'nope'" in result.stderr and "Traceback" not in result.stderr, result.stderr


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
@every_example
def test_a_store_holding_the_pod_holds_nothing_of_the_vocabularys(example, engine):
    terms = {subject for path in vocabulary.ontologies().values() for subject in store.parsed(path).subjects()}
    held = example.store(engine, vocabulary.DEFAULT_LENS)
    assert {triple[0] for triple in held.triples()} & terms == set()
    assert not set(held.graphs()) & set(vocabulary.ontologies())


@every_example
def test_a_derived_file_events_json_lists_and_the_build_does_not_make_is_a_failure(example):
    extended = Example(example.folder)
    extended.derived = [*extended.derived, "clinical/extra.ttl"]
    with pytest.raises(Failure, match="clinical/extra.ttl"):
        extended.derived_turtle("oxigraph")


def test_recomputed_py_less_its_first_line_is_the_source_file_at_the_commit_it_names():
    lines = (ROOT / "tests" / "recomputed.py").read_bytes().split(b"\n", 1)
    assert lines[0].startswith(b"# https://github.com/jayostis/cascade-bridge-spec/blob/2249a3aec0aa9dfe6a8c5b8a5cabf8855c97c190/")
    assert hashlib.sha256(lines[1]).hexdigest() == RECOMPUTED_SHA256


@pytest.mark.parametrize("lens", sorted(vocabulary.named("lenses")))
@pytest.mark.parametrize("engine", sorted(store.ENGINES))
@every_example
def test_the_derived_state_is_every_triple_the_derivations_add_and_none_of_the_pods_own(example, engine, lens):
    held = example.loaded(engine)
    pod = held.triples()
    derived = derive.derive(held, lens)
    assert derived and derived.isdisjoint(pod)
    assert held.triples() == pod | derived


@every_example
def test_a_shacl_validation_in_the_same_process_changes_no_term_the_store_gives_and_no_byte_of_the_site(example):
    def made():
        return ({engine: to_isomorphic(graph_of(example.store(engine, vocabulary.DEFAULT_LENS).triples()))
                 for engine in sorted(store.ENGINES)},
                site.Site(example).files())

    before = made()
    validate(Graph(), shacl_graph=Graph())
    assert made() == before


def graph_of(triples):
    found = Graph()
    for triple in triples:
        found.add(triple)
    return found
