import pytest

from cascade_pod import store

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
