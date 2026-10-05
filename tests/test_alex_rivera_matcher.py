from rdflib import Graph
from rdflib.namespace import RDF

from alex_rivera import EVERY_JUDGMENT, INPUT, JDG, PROV, name, step
from cascade_pod import match, store


def test_the_matcher_needs_no_file_names_or_step_list(alex):
    pod = alex.story_store("oxigraph", "J2").triples()
    matcher = match.Matcher(pod, match.References(INPUT / "references"), step("E5")["when"], alex.address, "oxigraph")
    written = Graph()
    for path, octets in matcher.take(alex.event("E4")["import"]).items():
        written += store.parsed_text(octets, alex.address + path)
    expected = {j: row for j, row in EVERY_JUDGMENT.items() if row.step == "E5"}
    assert sorted(expected) == ["J3", "J4", "J5", "J6", "J7"]
    assert set(written.subjects(RDF.type, JDG.Judgment)) == {name(j) for j in expected}
    for j, row in expected.items():
        assert set(written.objects(name(j), PROV.hadMember)) == {name(m) for m in row.members}, j
        assert written.value(name(j), JDG.justification) == JDG[row.justification], j
