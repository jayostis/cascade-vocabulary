import ast
import re
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest
from rdflib import URIRef

from cascade_pod import ask, derive, match, store, turtle, vocabulary
from cascade_pod.pod import Example

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
XSD_INTEGER = "http://www.w3.org/2001/XMLSchema#integer"


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
def test_a_triple_stated_in_two_files_is_counted_once_by_a_query_over_the_default_graph(engine, tmp_path):
    held = store.ENGINES[engine]()
    for name in ("one", "two"):
        path = tmp_path / f"{name}.ttl"
        path.write_text("<urn:x:s> <urn:x:p> <urn:x:o> .\n", encoding="utf-8")
        held.load(path, f"urn:x:{name}")
    assert held.select("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }") == [{"n": store.literal("1", XSD_INTEGER)}]
    assert held.select("SELECT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g") == [
        {"g": store.iri("urn:x:one")}, {"g": store.iri("urn:x:two")}]


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
def test_ask_prints_the_rows_the_builders_store_returns(engine):
    question = "record/Why it is in no view"
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "ask", str(EXAMPLE), question, "--engine", engine],
                            capture_output=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    held = derive.build(Example(EXAMPLE), engine).store
    rows = held.select(vocabulary.query(vocabulary.questions()[question]))
    assert rows and result.stdout.decode("utf-8").splitlines() == [ask.line(row) for row in rows]


def alex():
    """What only Alex's example says: its address, its name and title, its subject and imports, and its hospitals."""
    example = Example(EXAMPLE)
    facts = {example.address, example.title, *example.name.split("-")}
    facts |= {event[key] for event in example.events for key in ("subject", "import") if key in event}
    for export in EXAMPLE.glob("downloads/*/apple_health_export/export.xml"):
        facts |= {entry.get("sourceName") for entry in ElementTree.parse(export).getroot().iter("ClinicalRecord")}
    return facts


def mentions(text, facts):
    return sorted(fact for fact in facts if fact.lower() in text.lower())


def test_the_alex_check_finds_her_address_in_a_line_of_code():
    assert mentions('POD = "https://pod.alex-rivera.example/"', alex()) != []


@pytest.mark.parametrize("module", sorted(path.name for path in (ROOT / "cascade_pod").glob("*.py")))
def test_nothing_in_cascade_pod_names_alex(module):
    assert mentions((ROOT / "cascade_pod" / module).read_text(encoding="utf-8"), alex()) == []


def turtle_text(source):
    return [node.value for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and TURTLE_TEXT.search(node.value)]


TURTLE_TEXT = re.compile(r"@prefix|\^\^| [.;,]$")


def test_the_turtle_text_check_finds_a_statement_built_in_a_string():
    assert turtle_text('LINE = f"<{s}> <{p}> <{o}> ."') == ["> ."]


@pytest.mark.parametrize("module", sorted(path.name for path in (ROOT / "cascade_pod").glob("*.py") if path.name != "turtle.py"))
def test_no_module_but_turtle_builds_turtle_text(module):
    assert turtle_text((ROOT / "cascade_pod" / module).read_text(encoding="utf-8")) == []


def written_by_a_tool(example):
    """Each Turtle file a tool writes, by its path, with the address it is written at."""
    found = {path: example.address + path for path in example.files() + example.derived
             if path.startswith(("subject/", "records/", "provenance/", "references/")) or path in example.derived}
    for path in example.files():
        if path.startswith("judgments/"):
            if (None, PROV_ATTRIBUTED_TO, match.MATCHER) in store.parsed(example.pod / path):
                found[path] = example.address + path
    return {example.pod / path: address for path, address in found.items()} | {
        path: None for path in example.folder.glob("conversions/*/*/facts.ttl")}


PROV_ATTRIBUTED_TO = URIRef("http://www.w3.org/ns/prov#wasAttributedTo")


def rewritten(path, address):
    return turtle.write(store.parsed(path, address), address)


def test_the_one_writer_check_finds_a_file_in_another_layout(tmp_path):
    view = Example(EXAMPLE).pod / "clinical" / "allergies.ttl"
    other = tmp_path / "allergies.nt"
    other.write_bytes(store.parsed(view, "https://pod.example/clinical/allergies.ttl").serialize(format="nt", encoding="utf-8"))
    assert rewritten(other, "https://pod.example/clinical/allergies.ttl") != other.read_bytes()


def test_every_turtle_file_a_tool_writes_comes_from_the_one_writer():
    files = written_by_a_tool(Example(EXAMPLE))
    assert len(files) > 100
    assert [path for path, address in files.items() if rewritten(path, address) != path.read_bytes()] == []
