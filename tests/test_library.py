import subprocess
import sys
from pathlib import Path

import pytest

from cascade_pod import ask, derive, store, vocabulary
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
