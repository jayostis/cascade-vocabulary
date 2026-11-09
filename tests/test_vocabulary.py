import json
import re

import pytest
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SH, XSD

from contract import LAYOUT, QUERIES, ROOT

ONTOLOGIES = sorted(ROOT.glob("ontologies/**/*.ttl"))
SHAPES = [path for path in ONTOLOGIES if path.name.endswith(".shapes.ttl")]
SPEC = "https://github.com/the-cascade-protocol/spec/"
SOURCE_COMMIT = SPEC + "blob/d819bc2c045266f9f79ebf9398cbbb82a6156d27/"
CC_BY = URIRef("https://creativecommons.org/licenses/by/4.0/")
CASCADE = "https://ns.cascadeprotocol.org/"
CASCADE_NS = Namespace(CASCADE + "cascade#")
PROV = Namespace("http://www.w3.org/ns/prov#")
PAV = Namespace("http://purl.org/pav/")
SOLID = Namespace("http://www.w3.org/ns/solid/terms#")
OA = Namespace("http://www.w3.org/ns/oa#")
SEMAPV = Namespace("https://w3id.org/semapv/vocab/")
NOT_COPIED = (CASCADE, str(RDF), str(RDFS), str(OWL), str(XSD), str(SH))
BINDS_A_PREFIX = re.compile(r"(?:@prefix|PREFIX)[ \t]+([A-Za-z][\w-]*):[ \t]*<([^<>\s]*)>", re.IGNORECASE)
AN_IRI = re.compile(r"<[^<>\s]*>")
A_PREFIXED_NAME = re.compile(r"(?<![\w:#-])([A-Za-z][\w-]*):([A-Za-z]\w*)\b")
BOUND_IN_CASCADE = dict(
    Graph(bind_namespaces="none").parse(ROOT / "ontologies/cascade.ttl").namespaces())


def copied_terms_named_in(text):
    """The terms a pod file names from a vocabulary the pod copies rather than owns: those in a namespace that is not
    cascade's own, RDF, RDFS, OWL, XSD or SHACL, by a prefix the file binds (or cascade.ttl binds, for a file that
    binds none, as a feature or a guide) or by the namespace written out."""
    bound = {**{prefix: str(ns) for prefix, ns in BOUND_IN_CASCADE.items()},
             **{prefix: ns for prefix, ns in BINDS_A_PREFIX.findall(text)}}
    copied = {prefix: ns for prefix, ns in bound.items() if not ns.startswith(NOT_COPIED)}
    named = {URIRef(copied[prefix] + local) for prefix, local in A_PREFIXED_NAME.findall(AN_IRI.sub(" ", text))
             if prefix in copied}
    if copied:
        written_out = re.compile(
            "(" + "|".join(re.escape(ns) for ns in sorted(set(copied.values()), key=len, reverse=True))
            + r")([A-Za-z]\w*)")
        named |= {URIRef(ns + local) for ns, local in written_out.findall(text)}
    return named


FORMATS = {
    ".feature": "text/x-gherkin",
    ".json": "application/json",
    ".md": "text/markdown",
    ".rq": "application/sparql-query",
    ".ttl": "text/turtle",
    ".txt": "text/plain",
    ".xml": "application/xml",
}
DECLARES_A_PREDICATE = (
    RDF.Property,
    OWL.DatatypeProperty,
    OWL.ObjectProperty,
    OWL.AnnotationProperty,
)


def relative(path):
    return path.relative_to(ROOT).as_posix()


def union(paths):
    graph = Graph()
    for path in paths:
        graph.parse(path)
    return graph


def declared():
    vocabulary = union(ONTOLOGIES)
    return {
        s for kind in DECLARES_A_PREDICATE for s in vocabulary.subjects(RDF.type, kind)
    }


def members(graph, node):
    if isinstance(node, URIRef):
        return {node}
    return set(Collection(graph, graph.value(node, OWL.unionOf)))


def predicates(graph, path):
    if isinstance(path, URIRef):
        return {path}
    inverse = graph.value(path, SH.inversePath)
    if inverse is not None:
        return predicates(graph, inverse)
    return {p for step in Collection(graph, path) for p in predicates(graph, step)}


@pytest.mark.parametrize("path", ONTOLOGIES, ids=relative)
def test_every_turtle_file_parses(path):
    assert len(Graph().parse(path)) > 0


@pytest.mark.parametrize("path", SHAPES, ids=relative)
def test_every_shapes_file_loads_as_shacl_that_shacl_accepts(path):
    result, _, report = validate(
        Graph(), shacl_graph=Graph().parse(path), meta_shacl=True
    )
    assert result, report


@pytest.mark.parametrize("path", ONTOLOGIES, ids=relative)
def test_every_term_copied_from_the_spec_names_the_commit_and_carries_its_licence(path):
    graph = Graph().parse(path)
    ontology = next(graph.subjects(RDF.type, OWL.Ontology), None)
    copied = {term for term, source in graph.subject_objects(DCTERMS.source)
              if str(source).startswith(SPEC) and term != ontology}
    assert copied
    assert sorted(term for term in copied if not all(str(source).startswith(SOURCE_COMMIT)
                                                    for source in graph.objects(term, DCTERMS.source))) == []
    assert sorted(term for term in copied if (term, DCTERMS.license, CC_BY) not in graph) == []


def test_every_predicate_a_shape_constrains_and_every_term_a_pod_file_names_from_a_vocabulary_cascade_does_not_own_is_declared():
    """A term in a namespace other than cascade's own, RDF, RDFS, OWL, XSD and SHACL, named by a prefix its file binds, by
    any step of a path, or by its IRI written out, is declared in ontologies/ with a type, a source and a licence."""
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    paths = {p for path in shapes.objects(None, SH.path) for p in predicates(shapes, path)}
    pod_files = sorted(QUERIES.rglob("*.rq")) + SHAPES + sorted(
        path for folder in ("runtime", "conformance") for path in (ROOT / folder).rglob("*") if path.is_file())
    named = set().union(*(copied_terms_named_in(path.read_text(encoding="utf-8")) for path in pod_files))
    assert {PROV.wasInformedBy, PAV.retrievedOn, OA.XPathSelector, SEMAPV.ManualMappingCuration, SOLID.forClass,
            URIRef("http://www.w3.org/ns/pim/space#storage"), URIRef("http://xmlns.com/foaf/0.1/name"),
            URIRef("http://www.w3.org/2004/02/skos/core#broadMatch")} <= named
    assert sorted(paths - declared()) == []
    assert sorted(term for term in named if not all(
        (term, predicate, None) in vocabulary for predicate in (RDF.type, DCTERMS.source, DCTERMS.license))) == []


@pytest.mark.parametrize("text, term", [
    ("PREFIX anno: <http://www.w3.org/ns/oa#>\nSELECT * { ?x anno:Bogus ?y }", OA.Bogus),
    ("@prefix anno: <http://www.w3.org/ns/oa#> .\n<a> anno:Bogus <b> .", OA.Bogus),
    ("PREFIX dcterms: <http://purl.org/dc/terms/>\nSELECT * { ?x dcterms:bogus ?y }", URIRef(str(DCTERMS) + "bogus")),
    ("PREFIX prov: <http://www.w3.org/ns/prov#>\nSELECT * { ?x prov:wasDerivedFrom/prov:bogus ?y }", PROV.bogus),
    ("PREFIX oa: <http://www.w3.org/ns/oa#>\nSELECT * { ?x a/oa:Bogus ?y }", OA.Bogus),
    ("PREFIX prov: <http://www.w3.org/ns/prov#>\nSELECT * { ?x prov:used|prov:bogus ?y }", PROV.bogus),
    ("PREFIX pim: <http://www.w3.org/ns/pim/space#>\nSELECT * { ?x pim:bogus ?y }", URIRef("http://www.w3.org/ns/pim/space#bogus")),
    ('{"term": "prov:bogus"}', PROV.bogus),
    ("<http://www.w3.org/ns/prov#bogus>", PROV.bogus),
])
def test_the_scan_for_copied_terms_reads_each_files_own_prefixes_and_every_step_of_a_path(text, term):
    assert term in copied_terms_named_in(text)


@pytest.mark.parametrize("text", [
    "see runtime/steps.md and queries/x.rq for <http://example.org/prov:bogus> and <file:///a/prov:bogus>",
    "PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>\nSELECT * { ?x cascade:bogus ?y . ?x rdf:type ?z }",
    "PREFIX sh: <http://www.w3.org/ns/shacl#>\n[] sh:bogus 1 .",
    "PREFIX ccda: <https://ns.cascadeprotocol.org/adapter/ccda/v1-draft#>\n[] ccda:bogus 1 .",
    "urn:uuid:5d0c8f3e and ni:///sha-256;abc",
])
def test_the_scan_for_copied_terms_does_not_read_iris_paths_or_terms_that_are_not_copied(text):
    assert copied_terms_named_in(text) == set()


def test_every_class_whose_records_a_placement_holds_is_a_prov_entity():
    vocabulary, layout = union(ONTOLOGIES), Graph().parse(LAYOUT)
    records = {layout.value(placement, SOLID.forClass)
               for placement in layout.subjects(CASCADE_NS.holdsRecords, Literal(True))}
    assert len(records) > 10
    assert sorted(c for c in records if PROV.Entity not in set(vocabulary.transitive_objects(c, RDFS.subClassOf))) == []


def test_every_term_outside_cascade_carries_its_source_and_its_licence():
    vocabulary = union(ONTOLOGIES)
    ontologies = set(vocabulary.subjects(RDF.type, OWL.Ontology))
    copied = {s for s in vocabulary.subjects() if isinstance(s, URIRef)
              and not str(s).startswith(str(CASCADE_NS)) and s not in ontologies}
    assert len(copied) > 50
    assert sorted(s for s in copied if not all((s, p, None) in vocabulary for p in (DCTERMS.source, DCTERMS.license))) == []


def test_a_judgment_and_a_reference_series_are_prov_entities_by_the_vocabularys_own_subclasses():
    vocabulary = union(ONTOLOGIES)
    for c in (CASCADE_NS.Judgment, CASCADE_NS.ReferenceSeries):
        assert PROV.Entity in set(vocabulary.transitive_objects(c, RDFS.subClassOf)), c


def reaches_every_domain(vocabulary, subject_class, predicate):
    """Whether a subject of the class may carry the predicate: through rdfs:subClassOf the class reaches a member of
    each of the predicate's domains."""
    reached = set(vocabulary.transitive_objects(subject_class, RDFS.subClassOf))
    domains = list(vocabulary.objects(predicate, RDFS.domain))
    return bool(domains) and all(reached & members(vocabulary, domain) for domain in domains)


@pytest.mark.parametrize("subject_class, predicate", [
    (PROV.Association, PROV.hadRole),
    (PROV.Association, PROV.agent),
    (CASCADE_NS.FindingForReview, PROV.wasDerivedFrom),
    (CASCADE_NS.View, PROV.wasDerivedFrom),
])
def test_a_class_a_pod_writes_a_property_on_reaches_every_domain_of_that_property(subject_class, predicate):
    assert reaches_every_domain(union(ONTOLOGIES), subject_class, predicate)


def test_a_role_on_an_attribution_reaches_no_domain_of_had_role_and_the_attribution_terms_are_not_declared():
    vocabulary = union(ONTOLOGIES)
    assert (PROV.Attribution, None, None) not in vocabulary
    assert (PROV.qualifiedAttribution, None, None) not in vocabulary
    vocabulary.add((PROV.Attribution, RDFS.subClassOf, PROV.AgentInfluence))
    assert not reaches_every_domain(vocabulary, PROV.Attribution, PROV.hadRole)


def test_a_value_absent_for_a_reason_has_for_domain_each_class_of_a_property_a_value_can_be_absent_for():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    (shape,) = shapes.subjects(SH.path, CASCADE_NS.absentValueProperty)
    can_be_absent = Collection(shapes, shapes.value(shape, SH["in"]))
    def subjects_of(p):
        named = {c for domain in vocabulary.objects(p, RDFS.domain) for c in members(vocabulary, domain)}
        return named or {c for s in shapes.subjects(SH.targetSubjectsOf, p) for c in shapes.objects(s, SH.targetClass)}

    unread = sorted(str(p) for p in can_be_absent if not subjects_of(p))
    assert unread == []
    of_those = {c for p in can_be_absent for c in subjects_of(p)}
    stated = {c for domain in vocabulary.objects(CASCADE_NS.valueAbsentForReason, RDFS.domain)
              for c in members(vocabulary, domain)}
    assert len(of_those) > 10 and stated == of_those


def test_every_term_a_shape_targets_is_declared_here():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    targeted = {
        term
        for predicate in (SH.targetClass, SH.targetSubjectsOf, SH.targetObjectsOf)
        for term in shapes.objects(None, predicate)
    }
    assert targeted
    assert {t for t in targeted if (t, RDF.type, None) not in vocabulary} == set()


def test_every_package_class_a_term_names_is_declared_here():
    vocabulary = union(ONTOLOGIES)
    named = {
        member
        for predicate in (RDFS.domain, RDFS.range, RDFS.subClassOf)
        for node in vocabulary.objects(None, predicate)
        for member in members(vocabulary, node)
    }
    undeclared = {
        c
        for c in named
        if str(c).startswith(CASCADE) and (c, RDF.type, None) not in vocabulary
    }
    assert undeclared == set()


def test_a_property_a_shape_holds_to_iris_is_an_object_property_and_one_held_to_literals_a_datatype_property():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    wrong = set()
    for shape, predicate in shapes.subject_objects(SH.path):
        if not isinstance(predicate, URIRef):
            continue
        node = shapes.value(shape, SH.node)
        kind = shapes.value(shape, SH.nodeKind) or (node is not None and shapes.value(node, SH.nodeKind))
        if kind == SH.IRI and (predicate, RDF.type, OWL.DatatypeProperty) in vocabulary:
            wrong.add((str(predicate), "IRI"))
        if (kind == SH.Literal or shapes.value(shape, SH.datatype) is not None) and (
                predicate, RDF.type, OWL.ObjectProperty) in vocabulary:
            wrong.add((str(predicate), "literal"))
    assert sorted(wrong) == []


def test_every_datatype_a_shape_accepts_is_in_its_predicates_range():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    outside = set()
    for shape, predicate in shapes.subject_objects(SH.path):
        ranges = [
            members(vocabulary, r) for r in vocabulary.objects(predicate, RDFS.range)
        ]
        accepted = set(shapes.objects(shape, SH.datatype)) | {
            datatype
            for alternatives in shapes.objects(shape, SH["or"])
            for alternative in Collection(shapes, alternatives)
            for datatype in shapes.objects(alternative, SH.datatype)
        }
        datatype_ranges = [
            r for r in ranges if all(str(m).startswith(str(XSD)) for m in r)
        ]
        outside |= {
            (predicate, d) for d in accepted for r in datatype_ranges if d not in r
        }
    assert outside == set()


def crate():
    return {entity["@id"]: entity for entity in json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]}


def parts(entities, dataset):
    """Each file a dataset has as a part, or as a part of a dataset that is one of its parts."""
    found = {}
    for part in entities[dataset]["hasPart"]:
        entity = entities[part["@id"]]
        found |= parts(entities, part["@id"]) if entity["@type"] == "Dataset" else {part["@id"]: entity["encodingFormat"]}
    return found


def test_the_crate_lists_every_ontology_query_runtime_conformance_and_people_file_and_nothing_else():
    files = (sorted(ROOT.glob("ontologies/**/*.ttl")) + sorted(QUERIES.rglob("*.rq"))
             + sorted(path for folder in ("runtime", "conformance", "people") for path in (ROOT / folder).rglob("*") if path.is_file()))
    assert parts(crate(), "./") == {path.relative_to(ROOT).as_posix(): FORMATS[path.suffix] for path in files}


def references(value):
    if isinstance(value, dict):
        return {value["@id"]} if set(value) == {"@id"} else set().union(*map(references, value.values()))
    if isinstance(value, list):
        return set().union(*map(references, value))
    return set()


def test_every_is_based_on_and_citation_in_the_crate_is_on_a_file_that_exists():
    described = [path for path, entity in crate().items() if "isBasedOn" in entity or "citation" in entity]
    assert described and [path for path in described if path != "./" and not (ROOT / path).is_file()] == []


def test_every_entity_in_the_crate_is_reached_from_its_metadata_descriptor():
    entities, reached, todo = crate(), set(), ["ro-crate-metadata.json"]
    while todo:
        found = todo.pop()
        if found in entities and found not in reached:
            reached.add(found)
            todo.extend(references(entities[found]))
    assert sorted(set(entities) - reached) == []


def test_every_property_ranging_over_the_partial_date_union_is_in_the_padded_and_the_absent_property_lists():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    partial_date = {XSD.gYear, XSD.gYearMonth, XSD.date, XSD.dateTime}

    def listed(path):
        (shape,) = shapes.subjects(SH.path, path)
        return set(Collection(shapes, shapes.value(shape, SH["in"])))

    padded = listed(URIRef(CASCADE + "cascade#paddedDateTimeProperty"))
    absent = listed(URIRef(CASCADE + "cascade#absentValueProperty"))
    dated = {
        p
        for p, range_ in vocabulary.subject_objects(RDFS.range)
        if isinstance(range_, BNode) and vocabulary.value(range_, OWL.unionOf) is not None
        and set(Collection(vocabulary, vocabulary.value(range_, OWL.unionOf))) == partial_date
    }
    assert dated and sorted(dated - padded) == [] and sorted(dated - absent) == []


def test_each_kind_refuses_as_a_code_in_another_system_exactly_the_systems_it_holds_as_code_iris():
    vocabulary, shapes = union(ONTOLOGIES), union(SHAPES)
    cascade = Namespace(CASCADE + "cascade#")
    held = {
        cascade.testCodeInOtherSystem: {cascade.testCode: (cascade.LOINC, cascade.SNOMEDCT)},
        cascade.medicationCodeInOtherSystem: {cascade.rxNormCode: (cascade.RxNorm,), cascade.ndcCode: (cascade.NDC,)},
        cascade.conditionCodeInOtherSystem: {cascade.icd10Code: (cascade.ICD10CM,), cascade.snomedCode: (cascade.SNOMEDCT,)},
        cascade.procedureCodeInOtherSystem: {cascade.cptCode: (cascade.CPT,), cascade.snomedCode: (cascade.SNOMEDCT,)},
        cascade.dosageRouteCodeInOtherSystem: {cascade.dosageRouteCode: (cascade.SNOMEDCT,)},
        cascade.reportCodeInOtherSystem: {cascade.reportCode: (cascade.LOINC, cascade.SNOMEDCT)},
        cascade.noteOrDocumentTypeInOtherSystem: {cascade.noteOrDocumentType: (cascade.LOINC,)},
    }

    def refused(path):
        return {
            datatype
            for shape in shapes.subjects(SH.path, path)
            for negated in shapes.objects(shape, SH["not"]) if isinstance(negated, BNode)
            for alternatives in shapes.objects(negated, SH["or"])
            for alternative in Collection(shapes, alternatives)
            for datatype in shapes.objects(alternative, SH.datatype)
        }

    expected = {
        path: {URIRef(vocabulary.value(system, cascade.codingSystemUri)) for systems in by_property.values() for system in systems}
        for path, by_property in held.items()
    }
    assert {path: refused(path) for path in held} == expected
