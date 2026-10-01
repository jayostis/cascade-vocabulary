import re
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest
from rdflib import Graph, URIRef

from cascade_pod import derive, graphdb, store, vocabulary
from cascade_pod.build import LABEL_FILE, VIEW_FILES
from cascade_pod.pod import NOT_RDF, Example

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
ALEX = Example(EXAMPLE)

ENGINES = sorted(store.ENGINES)
REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
COMMITTED = sorted(set(VIEW_FILES.values()) | {LABEL_FILE, "index.ttl", "manifest.ttl"})


def canonical(term):
    return term if term[0] != "literal" else ("literal", term[1], term[2] or store.XSD_STRING, term[3])


def triples(found):
    return sorted(tuple(canonical(t) for t in triple) for triple in found)


def rows(found):
    return [sorted((name, canonical(term)) for name, term in row.items()) for row in found]


def final_graph():
    graph = Graph()
    for path in ALEX.files() + ALEX.derived:
        if not path.startswith(NOT_RDF):
            graph.parse(ALEX.pod / path, format="turtle", publicID=ALEX.address + path)
    return graph


EVENTS = [e["event"] for e in ALEX.events]
LENSES = ["everyday", "export"]


NEEDS_REVIEW = [relative for name, relative in vocabulary.questions().items() if name.endswith("/What needs review")]


def derived_state_views_and_reviews(engine, lens, through):
    held = ALEX.loaded(engine, through)
    derived = derive.derive(held, lens)
    views = {view: triples(held.construct(vocabulary.query(r))) for view, r in vocabulary.named("views").items()}
    reviews = {relative: rows(held.select(vocabulary.query(relative))) for relative in NEEDS_REVIEW}
    return triples(derived), views, reviews


@pytest.mark.parametrize("lens", LENSES)
@pytest.mark.parametrize("event", EVENTS)
def test_the_derived_state_each_view_and_what_needs_review_are_the_same_on_oxigraph_and_rdflib(event, lens):
    assert derived_state_views_and_reviews("oxigraph", lens, event) == derived_state_views_and_reviews("rdflib", lens, event)


@lru_cache(maxsize=None)
def answers(engine, lens, through=None):
    held = ALEX.store(engine, lens, through)
    return {name: rows(held.select(vocabulary.query(relative))) for name, relative in vocabulary.questions().items()}


@pytest.mark.parametrize("lens", LENSES)
def test_every_question_gives_the_same_rows_in_the_same_order_on_oxigraph_and_rdflib(lens):
    assert answers("oxigraph", lens) == answers("rdflib", lens)


def test_every_question_has_an_answer_at_some_event():
    unanswered = set(vocabulary.questions())
    for event in EVENTS:
        for lens in LENSES:
            unanswered -= {name for name, found in answers("oxigraph", lens, event).items() if found}
    assert unanswered == set()


@pytest.mark.parametrize("lens", LENSES)
@pytest.mark.parametrize("engine", ENGINES)
def test_the_derived_state_is_every_triple_the_derivations_add_and_none_of_the_pods_own(engine, lens):
    held = ALEX.loaded(engine)
    pod = held.triples()
    derived = derive.derive(held, lens)
    assert derived and derived.isdisjoint(pod)
    assert held.triples() == pod | derived


@pytest.mark.parametrize("engine", ENGINES)
def test_the_build_rewrites_every_committed_view_and_the_labels_byte_for_byte(engine, tmp_path):
    subprocess.run([sys.executable, "-m", "cascade_pod", "build", str(EXAMPLE), "--engine", engine, "--out", str(tmp_path)],
                   check=True, cwd=ROOT)
    written = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert written == COMMITTED
    for relative in COMMITTED:
        assert (tmp_path / relative).read_bytes() == (ALEX.pod / relative).read_bytes(), relative


def test_every_committed_view_is_marked_rebuildable_and_registered():
    held = ALEX.store("oxigraph", vocabulary.DEFAULT_LENS)
    current = {URIRef(row["version"][1]) for row in held.select(vocabulary.query(vocabulary.questions()["pod/Which reference versions are current"]))}
    for relative in sorted(set(VIEW_FILES.values()) | {LABEL_FILE}):
        address = URIRef(ALEX.address + relative)
        graph = Graph().parse(ALEX.pod / relative, format="turtle", publicID=str(address))
        assert (address, RDF_TYPE, URIRef(REC + "View")) in graph, relative
        assert set(graph.objects(address, URIRef("http://www.w3.org/ns/prov#used"))) == current, relative
    solid = "http://www.w3.org/ns/solid/terms#"
    index = Graph().parse(ALEX.pod / "settings/privateTypeIndex.ttl", publicID=ALEX.address + "settings/privateTypeIndex.ttl")
    registered = {(str(index.value(r, URIRef(solid + "forClass"))), str(index.value(r, URIRef(solid + "instance"))))
                  for r in index.subjects(RDF_TYPE, URIRef(solid + "TypeRegistration"))}
    classes = {"allergies": "https://ns.cascadeprotocol.org/health/v1#AllergyRecord",
               "conditions": "https://ns.cascadeprotocol.org/health/v1#ConditionRecord",
               "immunizations": "https://ns.cascadeprotocol.org/health/v1#ImmunizationRecord",
               "procedures": "https://ns.cascadeprotocol.org/clinical/v1#Procedure",
               "patients": "https://ns.cascadeprotocol.org/core/v1#PatientProfile"}
    for view, relative in VIEW_FILES.items():
        assert (classes[view], ALEX.address + relative) in registered
    containers = {(str(index.value(r, URIRef(solid + "forClass"))), str(index.value(r, URIRef(solid + "instanceContainer"))))
                  for r in index.subjects(RDF_TYPE, URIRef(solid + "TypeRegistration"))}
    assert (REC + "View", ALEX.address + "clinical/") in containers
    root = Graph().parse(ALEX.pod / "index.ttl", publicID=ALEX.address + "index.ttl")
    assert URIRef(ALEX.address + "clinical/") in set(root.objects(None, URIRef("http://www.w3.org/ns/ldp#contains")))
    assert set(COMMITTED) == set(ALEX.derived)
    assert set(ALEX.derived).isdisjoint(ALEX.files())


def test_everything_labelled_has_exactly_one_label():
    graph = final_graph()
    labels = Counter(str(s) for s in graph.subjects(URIRef(RDFS_LABEL), None))
    kinds = "VALUES ?type { health:AllergyRecord health:ConditionRecord health:ImmunizationRecord clinical:Procedure }"
    found = graph.query("""
        PREFIX cascade: <https://ns.cascadeprotocol.org/core/v1#>
        PREFIX clinical: <https://ns.cascadeprotocol.org/clinical/v1#>
        PREFIX health: <https://ns.cascadeprotocol.org/health/v1#>
        PREFIX jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX rec: <https://ns.cascadeprotocol.org/records/v1-draft#>
        SELECT DISTINCT ?thing WHERE {
          { %s ?thing a ?type ; ^rec:revisionOf [] }
          UNION { %s ?record a ?type ; ^rec:revisionOf [] . ?thing prov:specializationOf ?record }
          UNION { ?thing a rec:Revision }
          UNION { [] a rec:Revision ; prov:wasDerivedFrom ?thing }
          UNION { ?thing a jdg:Judgment }
          UNION { ?thing prov:specializationOf/a rec:ReferenceSeries }
          UNION { ?thing cascade:mergedFrom [] }
          UNION { [] a jdg:Judgment ; jdg:verdict jdg:About ; prov:hadMember ?thing }
          UNION { ?thing a rec:Subject }
        }""" % (kinds, kinds))
    everything = {str(row[0]) for row in found}
    assert everything
    assert {thing: labels[thing] for thing in everything if labels[thing] != 1} == {}
    address = ALEX.address + LABEL_FILE
    own = Graph().parse(ALEX.pod / LABEL_FILE, publicID=address)
    predicates = {(str(s) == address, str(p)) for s, p, _ in own}
    assert predicates == {(False, RDFS_LABEL), (True, str(RDF_TYPE)), (True, "http://www.w3.org/ns/prov#used")}


def test_no_two_labelled_things_share_a_label():
    graph = Graph().parse(ALEX.pod / LABEL_FILE, publicID=ALEX.address + LABEL_FILE)
    things = Counter(str(label) for label in graph.objects(None, URIRef(RDFS_LABEL)))
    assert {label: n for label, n in things.items() if n > 1} == {}


def test_the_graphdb_config_names_no_machine():
    configuration = graphdb.configuration(ALEX).decode("utf-8")
    Graph().parse(data=configuration, format="turtle")
    machine = re.compile(r"file:|(?<![A-Za-z])[A-Za-z]:[\\/]|localhost|127\.0\.0\.1|0\.0\.0\.0|/(?:home|Users|tmp)/|:\d{2,5}\b")
    for name, text in (("the configuration", configuration), ("graphdb.py", Path(graphdb.__file__).read_text(encoding="utf-8"))):
        assert machine.findall(text) == [], name


UNIT_PREFIXES = """
@prefix jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
@prefix : <urn:x:> .
"""


def answer(engine, question, turtle, tmp_path):
    path = tmp_path / f"{engine}.ttl"
    path.write_text(UNIT_PREFIXES + turtle, encoding="utf-8")
    held = store.ENGINES[engine]()
    held.load(path, "urn:x:")
    return [{name: term[1] for name, term in row.items()}
            for row in held.select(vocabulary.query(vocabulary.questions()[question]))]


@pytest.mark.parametrize("engine", ENGINES)
def test_a_profile_named_by_two_hospitals_records_gives_each_hospitals_row_the_total_of_its_records(engine, tmp_path):
    found = answer(engine, "profile/Whose it is counted as", """
        :about a jdg:Judgment ; rec:counts true ; jdg:verdict jdg:About ; prov:hadMember :p ; jdg:subject :s .
        :v1 rec:patient :p ; prov:specializationOf :r1 . :rev1 rec:version :v1 ; prov:wasDerivedFrom :d1 .
        :v2 rec:patient :p ; prov:specializationOf :r2 . :rev2 rec:version :v2 ; prov:wasDerivedFrom :d2 .
        :v3 rec:patient :p ; prov:specializationOf :r3 . :rev3 rec:version :v3 ; prov:wasDerivedFrom :d2 .
        :d1 prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Meridian" ] ] .
        :d2 prov:qualifiedAttribution [ prov:hadRole rec:author ; prov:agent [ rdfs:label "Larkspur" ] ] .
    """, tmp_path)
    assert sorted((row["hospital"], row["records"]) for row in found) == [("Larkspur", "3"), ("Meridian", "3")]


@pytest.mark.parametrize("engine", ENGINES)
def test_an_entry_lists_a_pair_still_joined_by_what_the_derivations_judged_currently_different(engine, tmp_path):
    found = answer(engine, "entry/What needs review", """
        @prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
        :a a health:AllergyRecord ; rec:inEntry :entry ; jdg:currentlyDifferent :b .
        :b a health:AllergyRecord ; rec:inEntry :entry ; jdg:currentlyDifferent :a .
    """, tmp_path)
    assert [(row["entry"], row["record"], row["otherRecord"]) for row in found] == [("urn:x:entry", "urn:x:a", "urn:x:b")]
