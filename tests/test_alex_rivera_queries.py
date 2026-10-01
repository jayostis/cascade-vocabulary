import re
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest
import rdflib
from rdflib import Graph, URIRef

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
sys.path.insert(0, str(EXAMPLE / "queries"))
import build  # noqa: E402

rdflib.NORMALIZE_LITERALS = False

ENGINES = sorted(build.ENGINES)
REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
COMMITTED = sorted(set(build.VIEW_FILES.values()) | {build.LABEL_FILE, "index.ttl", "manifest.ttl"})


def canonical(term):
    return term if term[0] != "literal" else ("literal", term[1], term[2] or build.XSD_STRING, term[3])


def triples(found):
    return sorted(tuple(canonical(t) for t in triple) for triple in found)


def rows(found):
    return sorted(sorted((name, canonical(term)) for name, term in row.items()) for row in found)


@lru_cache(maxsize=None)
def final_pod(engine):
    store = build.ENGINES[engine]()
    for path in build.pod_files() + build.events()["derived"]:
        if not path.startswith(build.NOT_RDF):
            store.load(build.POD / path, build.POD_BASE + path)
    return store


def final_graph():
    graph = Graph()
    for path in build.pod_files() + build.events()["derived"]:
        if not path.startswith(build.NOT_RDF):
            graph.parse(build.POD / path, format="turtle", publicID=build.POD_BASE + path)
    return graph



def derived_state_views_and_reviews(engine, lens, through):
    store = build.loaded(engine, through)
    derived = []
    for relative in build.derivations(lens):
        found = store.construct(build.query_text(relative))
        derived.append((relative, triples(found)))
        store.add(found)
    views = {v: triples(store.construct(build.query_text(r))) for v, r in build.named("views").items()}
    reviews = {v: rows(store.select(build.query_text(r))) for v, r in build.named("review").items()}
    return derived, views, reviews


@pytest.mark.parametrize("lens", ["everyday", "export"])
@pytest.mark.parametrize("event", [e["event"] for e in build.events()["events"]])
def test_each_derivation_view_and_review_is_the_same_on_oxigraph_and_rdflib(event, lens):
    assert derived_state_views_and_reviews("oxigraph", lens, event) == derived_state_views_and_reviews("rdflib", lens, event)


@pytest.mark.parametrize("engine", ENGINES)
def test_the_build_rewrites_every_committed_view_and_the_labels_byte_for_byte(engine, tmp_path):
    subprocess.run([sys.executable, str(EXAMPLE / "queries" / "build.py"), "--engine", engine, "--out", str(tmp_path)], check=True)
    written = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert written == COMMITTED
    for relative in COMMITTED:
        assert (tmp_path / relative).read_bytes() == (build.POD / relative).read_bytes(), relative


def test_every_committed_view_is_marked_rebuildable_and_registered():
    store = build.derive(build.loaded("oxigraph"), "everyday")
    current = {URIRef(row["v"][1]) for row in store.select(build.CURRENT_REFERENCE_VERSIONS)}
    for relative in sorted(set(build.VIEW_FILES.values()) | {build.LABEL_FILE}):
        address = URIRef(build.POD_BASE + relative)
        graph = Graph().parse(build.POD / relative, format="turtle", publicID=str(address))
        assert (address, RDF_TYPE, URIRef(REC + "View")) in graph, relative
        assert set(graph.objects(address, URIRef("http://www.w3.org/ns/prov#used"))) == current, relative
    solid = "http://www.w3.org/ns/solid/terms#"
    index = Graph().parse(build.POD / "settings/privateTypeIndex.ttl", publicID=build.POD_BASE + "settings/privateTypeIndex.ttl")
    registered = {(str(index.value(r, URIRef(solid + "forClass"))), str(index.value(r, URIRef(solid + "instance"))))
                  for r in index.subjects(RDF_TYPE, URIRef(solid + "TypeRegistration"))}
    classes = {"allergies": "https://ns.cascadeprotocol.org/health/v1#AllergyRecord",
               "conditions": "https://ns.cascadeprotocol.org/health/v1#ConditionRecord",
               "immunizations": "https://ns.cascadeprotocol.org/health/v1#ImmunizationRecord",
               "procedures": "https://ns.cascadeprotocol.org/clinical/v1#Procedure",
               "patients": "https://ns.cascadeprotocol.org/core/v1#PatientProfile"}
    for view, relative in build.VIEW_FILES.items():
        assert (classes[view], build.POD_BASE + relative) in registered
    containers = {(str(index.value(r, URIRef(solid + "forClass"))), str(index.value(r, URIRef(solid + "instanceContainer"))))
                  for r in index.subjects(RDF_TYPE, URIRef(solid + "TypeRegistration"))}
    assert (REC + "View", build.POD_BASE + "clinical/") in containers
    root = Graph().parse(build.POD / "index.ttl", publicID=build.POD_BASE + "index.ttl")
    assert URIRef(build.POD_BASE + "clinical/") in set(root.objects(None, URIRef("http://www.w3.org/ns/ldp#contains")))
    derived = build.events()["derived"]
    assert set(COMMITTED) == set(derived)
    assert set(derived).isdisjoint(build.pod_files())


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
    address = build.POD_BASE + build.LABEL_FILE
    own = Graph().parse(build.POD / build.LABEL_FILE, publicID=address)
    predicates = {(str(s) == address, str(p)) for s, p, _ in own}
    assert predicates == {(False, RDFS_LABEL), (True, str(RDF_TYPE)), (True, "http://www.w3.org/ns/prov#used")}


def test_no_two_labelled_things_share_a_label():
    graph = Graph().parse(build.POD / build.LABEL_FILE, publicID=build.POD_BASE + build.LABEL_FILE)
    things = Counter(str(label) for label in graph.objects(None, URIRef(RDFS_LABEL)))
    assert {label: n for label, n in things.items() if n > 1} == {}


@pytest.mark.parametrize("relative", build.named("people").values())
def test_every_query_for_people_runs_on_the_final_pod_and_both_engines_agree(relative):
    text = build.query_text(relative)
    found = {engine: rows(final_pod(engine).select(text)) for engine in ENGINES}
    assert found["oxigraph"] != []
    assert found["oxigraph"] == found["rdflib"]


def test_the_graphdb_config_names_no_machine():
    Graph().parse(EXAMPLE / "graphdb" / "repository.ttl", format="turtle")
    machine = re.compile(r"file:|(?<![A-Za-z])[A-Za-z]:[\\/]|localhost|127\.0\.0\.1|0\.0\.0\.0|/(?:home|Users|tmp)/|:\d{2,5}\b")
    for name in ("repository.ttl", "load.py"):
        assert machine.findall((EXAMPLE / "graphdb" / name).read_text(encoding="utf-8")) == [], name
