import json
import re
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest
import rdflib
from pyparsing import ParseResults
from rdflib import Graph, URIRef, Variable
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
QUERIES = EXAMPLE / "queries"
sys.path.insert(0, str(QUERIES))
import build  # noqa: E402

rdflib.NORMALIZE_LITERALS = False

ENGINES = sorted(build.ENGINES)
REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
IN_ENTRY = URIRef(REC + "inEntry")
COMMITTED = sorted(set(build.VIEW_FILES.values()) | {build.LABEL_FILE, "index.ttl", "manifest.ttl"})


def every_query():
    return sorted(p.relative_to(QUERIES).as_posix() for p in QUERIES.rglob("*.rq"))


def listed():
    listing = build.listing()
    paths = [listing["labels"], *listing["people"]]
    for lens in listing["lenses"].values():
        paths += lens["derivations"] + list(lens["views"].values()) + list(lens["reviews"].values())
    return paths


def nodes(tree):
    if isinstance(tree, CompValue):
        yield tree
        for value in tree.values():
            yield from nodes(value)
    elif isinstance(tree, (list, tuple, ParseResults)):
        for value in tree:
            yield from nodes(value)


def is_subquery(part):
    return part.name == "GroupOrUnionGraphPattern" and [g.name for g in part["graph"]] == ["SubSelect"]


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


@pytest.mark.parametrize("relative", every_query())
def test_every_query_parses_on_rdflib_and_on_pyoxigraph(relative):
    text = build.query_text(relative)
    prepareQuery(text)
    build.Oxigraph().store.query(text)


def test_the_listing_names_every_query_and_every_query_exists():
    counts = Counter(listed())
    everyday, export = (build.listing()["lenses"][lens] for lens in ("everyday", "export"))
    assert sorted(counts) == every_query()
    assert [p for p, n in counts.items() if n > 1 and not p.startswith(("derivations/", "views/", "review/"))] == []
    assert {k: v for k, v in everyday.items() if k != "derivations"} == {k: v for k, v in export.items() if k != "derivations"}
    assert [(a, b) for a, b in zip(everyday["derivations"], export["derivations"]) if a != b] == [
        ("derivations/counting-judgments-everyday.rq", "derivations/counting-judgments-export.rq")]
    assert build.listing()["people"] == sorted(p for p in every_query() if p.startswith("people/"))


@pytest.mark.parametrize("relative", every_query())
def test_every_subquery_comes_first_in_its_group(relative):
    for group in nodes(parseQuery(build.query_text(relative))):
        if group.name == "GroupGraphPatternSub":
            parts = list(group.get("part") or [])
            first_other = next((i for i, part in enumerate(parts) if not is_subquery(part)), len(parts))
            assert not any(is_subquery(part) for part in parts[first_other:]), relative


@pytest.mark.parametrize("relative", every_query())
def test_every_query_reading_in_entry_names_its_type(relative):
    algebra = prepareQuery(build.query_text(relative)).algebra
    patterns = [t for node in nodes(algebra["p"]) if node.name == "BGP" for t in node["triples"]]
    bound_by_values = {v for node in nodes(algebra["p"]) if node.name == "values" for row in node["res"] for v in row}
    typed = {s for s, p, o in patterns if p == RDF_TYPE and (isinstance(o, URIRef) or o in bound_by_values)}
    readers = {s for s, p, o in patterns if p == IN_ENTRY}
    assert readers <= typed, relative


def derived_state_views_and_reviews(engine, lens, through):
    store = build.loaded(engine, through)
    derived = []
    for relative in build.listing()["lenses"][lens]["derivations"]:
        found = store.construct(build.query_text(relative))
        derived.append((relative, triples(found)))
        store.add(found)
    queries = build.listing()["lenses"][lens]
    views = {v: triples(store.construct(build.query_text(r))) for v, r in queries["views"].items()}
    reviews = {v: rows(store.select(build.query_text(r))) for v, r in queries["reviews"].items()}
    return derived, views, reviews


@pytest.mark.parametrize("lens", ["everyday", "export"])
@pytest.mark.parametrize("event", [e["event"] for e in build.events()["events"]])
def test_each_derivation_view_and_review_is_the_same_on_oxigraph_and_rdflib(event, lens):
    assert derived_state_views_and_reviews("oxigraph", lens, event) == derived_state_views_and_reviews("rdflib", lens, event)


@pytest.mark.parametrize("engine", ENGINES)
def test_the_build_rewrites_every_committed_view_and_the_labels_byte_for_byte(engine, tmp_path):
    subprocess.run([sys.executable, str(QUERIES / "build.py"), "--engine", engine, "--out", str(tmp_path)], check=True)
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
    found = graph.query(build.PREFIXES + """
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


@pytest.mark.parametrize("relative", build.listing()["people"])
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
