import json
import re
from functools import cache

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
PARTIAL_DATE = {XSD.gYear, XSD.gYearMonth, XSD.date, XSD.dateTime}
HELD_AS_CODE_IRIS = {
    CASCADE_NS.testCodeInOtherSystem: {CASCADE_NS.testCode: (CASCADE_NS.LOINC, CASCADE_NS.SNOMEDCT)},
    CASCADE_NS.medicationCodeInOtherSystem: {CASCADE_NS.rxNormCode: (CASCADE_NS.RxNorm,),
                                             CASCADE_NS.ndcCode: (CASCADE_NS.NDC,)},
    CASCADE_NS.conditionCodeInOtherSystem: {CASCADE_NS.icd10Code: (CASCADE_NS.ICD10CM,),
                                            CASCADE_NS.snomedCode: (CASCADE_NS.SNOMEDCT,)},
    CASCADE_NS.procedureCodeInOtherSystem: {CASCADE_NS.cptCode: (CASCADE_NS.CPT,),
                                            CASCADE_NS.snomedCode: (CASCADE_NS.SNOMEDCT,)},
    CASCADE_NS.dosageRouteCodeInOtherSystem: {CASCADE_NS.dosageRouteCode: (CASCADE_NS.SNOMEDCT,)},
    CASCADE_NS.reportCodeInOtherSystem: {CASCADE_NS.reportCode: (CASCADE_NS.LOINC, CASCADE_NS.SNOMEDCT)},
    CASCADE_NS.noteOrDocumentTypeInOtherSystem: {CASCADE_NS.noteOrDocumentType: (CASCADE_NS.LOINC,)},
}


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


@cache
def vocabulary():
    return union(ONTOLOGIES)


@cache
def shape_graphs():
    return union(SHAPES)


@cache
def declared():
    return {s for kind in DECLARES_A_PREDICATE for s in vocabulary().subjects(RDF.type, kind)}


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


def shape_paths():
    """Each predicate a shape constrains, through any step of a path."""
    shapes = shape_graphs()
    return {p for path in shapes.objects(None, SH.path) for p in predicates(shapes, path)}


def held_wrongly():
    """Each predicate a shape holds to IRIs that is declared a datatype property, as (predicate, "IRI"), and each held to
    literals that is declared an object property, as (predicate, "literal")."""
    wrong = set()
    shapes = shape_graphs()
    for shape, predicate in shapes.subject_objects(SH.path):
        if not isinstance(predicate, URIRef):
            continue
        node = shapes.value(shape, SH.node)
        kind = shapes.value(shape, SH.nodeKind) or (node is not None and shapes.value(node, SH.nodeKind))
        if kind == SH.IRI and (predicate, RDF.type, OWL.DatatypeProperty) in vocabulary():
            wrong.add((str(predicate), "IRI"))
        if (kind == SH.Literal or shapes.value(shape, SH.datatype) is not None) and (
                predicate, RDF.type, OWL.ObjectProperty) in vocabulary():
            wrong.add((str(predicate), "literal"))
    return wrong


def listed_by_a_shape(path):
    """The members of the `sh:in` list of the one shape that constrains the path."""
    shapes = shape_graphs()
    (shape,) = shapes.subjects(SH.path, path)
    return set(Collection(shapes, shapes.value(shape, SH["in"])))


def classes_read_on(predicate):
    """The classes a property is stated of: those its domain names, else those a shape targets by subjects of it."""
    named = {c for domain in vocabulary().objects(predicate, RDFS.domain) for c in members(vocabulary(), domain)}
    shapes = shape_graphs()
    return named or {c for s in shapes.subjects(SH.targetSubjectsOf, predicate) for c in shapes.objects(s, SH.targetClass)}


def partial_date_properties():
    return {
        p
        for p, range_ in vocabulary().subject_objects(RDFS.range)
        if isinstance(range_, BNode) and vocabulary().value(range_, OWL.unionOf) is not None
        and set(Collection(vocabulary(), vocabulary().value(range_, OWL.unionOf))) == PARTIAL_DATE
    }


@cache
def terms_copied_from_the_spec():
    """Each ontology file, as its path and its graph, with the terms whose `dct:source` is in the earlier Cascade
    specification, the ontology itself apart."""
    found = []
    for path in ONTOLOGIES:
        graph = Graph().parse(path)
        ontology = next(graph.subjects(RDF.type, OWL.Ontology), None)
        found.append((relative(path), graph, {term for term, source in graph.subject_objects(DCTERMS.source)
                                              if str(source).startswith(SPEC) and term != ontology}))
    return found


def reaches_every_domain(graph, subject_class, predicate):
    """Whether a subject of the class may carry the predicate: through rdfs:subClassOf the class reaches a member of
    each of the predicate's domains."""
    reached = set(graph.transitive_objects(subject_class, RDFS.subClassOf))
    domains = list(graph.objects(predicate, RDFS.domain))
    return bool(domains) and all(reached & members(graph, domain) for domain in domains)


def crate():
    return {entity["@id"]: entity for entity in json.loads((ROOT / "ro-crate-metadata.json").read_text(encoding="utf-8"))["@graph"]}


def parts(entities, dataset):
    """Each file a dataset has as a part, or as a part of a dataset that is one of its parts."""
    found = {}
    for part in entities[dataset]["hasPart"]:
        entity = entities[part["@id"]]
        found |= parts(entities, part["@id"]) if entity["@type"] == "Dataset" else {part["@id"]: entity["encodingFormat"]}
    return found


def references(value):
    if isinstance(value, dict):
        return {value["@id"]} if set(value) == {"@id"} else set().union(*map(references, value.values()))
    if isinstance(value, list):
        return set().union(*map(references, value))
    return set()


class TestTermsTheShapesAndOntologyAgreeOn:
    """Terms the shapes and the ontology files agree on · ontologies/cascade.ttl, ontologies/cascade.shapes.ttl

    An ontology file declares a term: its type, and for a property its domain and its range. A shape then says what a
    pod may write with it. The two are written apart, so each thing a shape says of a term is held to what the term's
    declaration says.
    """

    class TestGivenAnyShapesFile:
        @pytest.mark.parametrize("path", SHAPES, ids=relative)
        def test_is_shacl_that_shacl_accepts(self, path):
            """is SHACL that SHACL's own shapes accept

            Validates the shapes file against SHACL's own shapes (its meta-shapes), as pyshacl runs them; a shapes file that
            uses SHACL in a way SHACL does not mean fails, though it still loads.
            """
            result, _, report = validate(Graph(), shacl_graph=Graph().parse(path), meta_shacl=True)
            assert result, report

    class TestGivenAnyPropertyAShapeConstrains:
        def test_is_declared_as_a_property(self):
            """is declared as a property

            Collects every predicate that a shape's `sh:path` names, through any step of a path; one that no ontology file
            declares as a property of any kind fails.
            """
            assert sorted(shape_paths() - declared()) == []

        def test_is_no_datatype_property_where_a_shape_holds_it_to_iris(self):
            """is no datatype property where a shape holds it to IRIs

            A property a shape holds to IRIs, by `sh:nodeKind sh:IRI`, must not be declared an `owl:DatatypeProperty`; each
            one that is fails.
            """
            assert sorted(wrong for wrong in held_wrongly() if wrong[1] == "IRI") == []

        def test_is_no_object_property_where_a_shape_holds_it_to_literals(self):
            """is no object property where a shape holds it to literals

            A property a shape holds to literals, by a datatype or `sh:nodeKind sh:Literal`, must not be declared an
            `owl:ObjectProperty`; each one that is fails.
            """
            assert sorted(wrong for wrong in held_wrongly() if wrong[1] == "literal") == []

        def test_has_in_its_range_every_datatype_a_shape_accepts(self):
            """has in its range every datatype a shape accepts for it

            For each shape on a property, each datatype it accepts, alone or in an `sh:or`, is compared with the property's
            range where that range is made of datatypes; one the range does not hold fails.
            """
            graph, shapes = vocabulary(), shape_graphs()
            outside = set()
            for shape, predicate in shapes.subject_objects(SH.path):
                ranges = [members(graph, r) for r in graph.objects(predicate, RDFS.range)]
                accepted = set(shapes.objects(shape, SH.datatype)) | {
                    datatype
                    for alternatives in shapes.objects(shape, SH["or"])
                    for alternative in Collection(shapes, alternatives)
                    for datatype in shapes.objects(alternative, SH.datatype)
                }
                datatype_ranges = [r for r in ranges if all(str(m).startswith(str(XSD)) for m in r)]
                outside |= {(predicate, d) for d in accepted for r in datatype_ranges if d not in r}
            assert outside == set()

    class TestGivenAnyTermAShapeTargets:
        def test_is_declared_with_a_type(self):
            """is declared with a type

            Collects each class and property that a shape targets with `sh:targetClass`, `sh:targetSubjectsOf` or
            `sh:targetObjectsOf`; one that no ontology file gives a type fails, as the shape would check nothing.
            """
            shapes = shape_graphs()
            targeted = {
                term
                for predicate in (SH.targetClass, SH.targetSubjectsOf, SH.targetObjectsOf)
                for term in shapes.objects(None, predicate)
            }
            assert targeted
            assert {t for t in targeted if (t, RDF.type, None) not in vocabulary()} == set()

    class TestGivenAnyClassATermNames:
        """given any class of the vocabulary that a term names as its domain, its range or its superclass"""

        def test_is_declared_with_a_type(self):
            """is declared with a type

            Collects each class under `cascade#` that any term of the ontology files names as its domain, its range or its
            superclass, a union member included; one with no type of its own fails.
            """
            graph = vocabulary()
            named = {
                member
                for predicate in (RDFS.domain, RDFS.range, RDFS.subClassOf)
                for node in graph.objects(None, predicate)
                for member in members(graph, node)
            }
            undeclared = {c for c in named if str(c).startswith(CASCADE) and (c, RDF.type, None) not in graph}
            assert undeclared == set()

    class TestGivenAnyPartialDateProperty:
        """given any property whose range is the four date types together

        The four are `xsd:gYear`, `xsd:gYearMonth`, `xsd:date` and `xsd:dateTime`, a date written to the year, the month,
        the day or the second.
        """

        def test_is_in_the_list_of_properties_whose_date_a_runtime_pads(self):
            """is in the list of properties whose date a runtime pads

            Each property whose range is the union of the four date types is compared with the `sh:in` list of
            `cascade:paddedDateTimeProperty`; one that the list leaves out fails.
            """
            dated = partial_date_properties()
            assert dated and sorted(dated - listed_by_a_shape(CASCADE_NS.paddedDateTimeProperty)) == []

        def test_is_in_the_list_of_properties_a_value_can_be_absent_for(self):
            """is in the list of properties a value can be absent for

            Each property whose range is the union of the four date types is compared with the `sh:in` list of
            `cascade:absentValueProperty`; one that the list leaves out fails.
            """
            dated = partial_date_properties()
            assert dated and sorted(dated - listed_by_a_shape(CASCADE_NS.absentValueProperty)) == []

    class TestGivenAnyPropertyAValueCanBeAbsentFor:
        def test_has_a_class_it_is_read_on(self):
            """has a class it is read on, by its domain or by a shape's target

            Each property in the `sh:in` list of `cascade:absentValueProperty` is given the classes its domain names or,
            with no domain, those a shape targets by the property's subjects; one given none fails.
            """
            unread = sorted(str(p) for p in listed_by_a_shape(CASCADE_NS.absentValueProperty) if not classes_read_on(p))
            assert unread == []

    class TestGivenValueAbsentForReason:
        """given `cascade:valueAbsentForReason`"""

        def test_has_for_its_domain_exactly_the_classes_of_those_properties(self):
            """has for its domain exactly the classes of those properties

            The classes that the properties a value can be absent for are read on are compared with the classes in the
            domain of `cascade:valueAbsentForReason`; a class on one side only fails.
            """
            graph = vocabulary()
            of_those = {c for p in listed_by_a_shape(CASCADE_NS.absentValueProperty) for c in classes_read_on(p)}
            stated = {c for domain in graph.objects(CASCADE_NS.valueAbsentForReason, RDFS.domain)
                      for c in members(graph, domain)}
            assert len(of_those) > 10 and stated == of_those

    class TestGivenAPropertyForACodeInAnotherSystem:
        @pytest.mark.parametrize("path", [
            pytest.param(CASCADE_NS.testCodeInOtherSystem, id="test"),
            pytest.param(CASCADE_NS.medicationCodeInOtherSystem, id="medication"),
            pytest.param(CASCADE_NS.conditionCodeInOtherSystem, id="condition"),
            pytest.param(CASCADE_NS.procedureCodeInOtherSystem, id="procedure"),
            pytest.param(CASCADE_NS.dosageRouteCodeInOtherSystem, id="dosage route"),
            pytest.param(CASCADE_NS.reportCodeInOtherSystem, id="report"),
            pytest.param(CASCADE_NS.noteOrDocumentTypeInOtherSystem, id="note or document type"),
        ])
        def test_refuses_exactly_the_system_uris_its_kind_holds(self, path):
            """refuses exactly the system URIs its kind already holds as code IRIs

            The case is a kind of record's property for a code in another system. The datatypes it refuses, the system URIs
            a shape rules out with `sh:not`, are compared with the system URIs of the code systems that kind's own code
            properties hold as code IRIs; a system refused that the kind holds, or held and not refused, fails.
            """
            shapes = shape_graphs()
            refused = {
                datatype
                for shape in shapes.subjects(SH.path, path)
                for negated in shapes.objects(shape, SH["not"]) if isinstance(negated, BNode)
                for alternatives in shapes.objects(negated, SH["or"])
                for alternative in Collection(shapes, alternatives)
                for datatype in shapes.objects(alternative, SH.datatype)
            }
            expected = {URIRef(vocabulary().value(system, CASCADE_NS.codingSystemUri))
                        for systems in HELD_AS_CODE_IRIS[path].values() for system in systems}
            assert refused == expected


class TestCopiedTerms:
    """Terms copied from another vocabulary · ontologies/*.ttl

    Where PROV, PAV or another published vocabulary has a term, the vocabulary uses it and copies its declaration, with
    where it was copied from and its licence. A file here may name such a term only once it is so declared.
    """

    class TestGivenAnyTermCopiedFromTheSpecification:
        """given any term copied from the earlier Cascade specification"""

        def test_names_the_commit_it_was_copied_at_as_its_source(self):
            """names the commit it was copied at as its source

            In each ontology file, each term whose `dct:source` is in the earlier specification must have only sources at
            the one commit the terms were copied at; a term with a source at another commit fails. A file with no such term
            fails too.
            """
            files = terms_copied_from_the_spec()
            assert all(copied for _, _, copied in files)
            offenders = sorted(f"{file}: {term}" for file, graph, copied in files for term in copied
                               if not all(str(source).startswith(SOURCE_COMMIT) for source in graph.objects(term, DCTERMS.source)))
            assert offenders == []

        def test_carries_the_cc_by_4_0_licence(self):
            """carries the CC BY 4.0 licence

            In each ontology file, each term whose `dct:source` is in the earlier specification must have
            `dct:license` the Creative Commons CC BY 4.0 licence; one without it fails. A file with no such term fails too.
            """
            files = terms_copied_from_the_spec()
            assert all(copied for _, _, copied in files)
            offenders = sorted(f"{file}: {term}" for file, graph, copied in files for term in copied
                               if (term, DCTERMS.license, CC_BY) not in graph)
            assert offenders == []

    class TestGivenAnyTermOutsideCascade:
        """given any term outside `cascade#` that an ontology file declares"""

        def test_carries_its_source_and_its_licence(self):
            """carries its source and its licence

            Collects each IRI the ontology files state something of, other than those in `cascade#` and the ontologies
            themselves (more than fifty); one with no `dct:source` or no `dct:license` fails.
            """
            graph = vocabulary()
            ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
            copied = {s for s in graph.subjects() if isinstance(s, URIRef)
                      and not str(s).startswith(str(CASCADE_NS)) and s not in ontologies}
            assert len(copied) > 50
            assert sorted(s for s in copied if not all((s, p, None) in graph for p in (DCTERMS.source, DCTERMS.license))) == []

    class TestGivenAnyTermAFileNames:
        """given any term a query, a shape, a feature or a kit names from a namespace the vocabulary copies"""

        def test_is_declared_with_a_type_a_source_and_a_licence(self):
            """is declared with a type, a source and a licence

            Scans every query, shapes file and file under `runtime/` and `conformance/` for terms of a copied namespace,
            named by a prefix the file binds, by any step of a path, or by its IRI written out. The scan must still find
            eight known terms, then each term found must have a type, a source and a licence in the ontology files.
            """
            graph = vocabulary()
            pod_files = sorted(QUERIES.rglob("*.rq")) + SHAPES + sorted(
                path for folder in ("runtime", "conformance") for path in (ROOT / folder).rglob("*") if path.is_file())
            named = set().union(*(copied_terms_named_in(path.read_text(encoding="utf-8")) for path in pod_files))
            assert {PROV.wasInformedBy, PAV.retrievedOn, OA.XPathSelector, SEMAPV.ManualMappingCuration, SOLID.forClass,
                    URIRef("http://www.w3.org/ns/pim/space#storage"), URIRef("http://xmlns.com/foaf/0.1/name"),
                    URIRef("http://www.w3.org/2004/02/skos/core#broadMatch")} <= named
            assert sorted(term for term in named if not all(
                (term, predicate, None) in graph for predicate in (RDF.type, DCTERMS.source, DCTERMS.license))) == []


class TestProv:
    """PROV as a pod's records use it · ontologies/cascade.ttl, runtime/pod-layout.ttl

    A pod says who made a thing, and from what, in PROV's terms, and PROV gives each property a domain. A class a pod
    writes such a property on must reach that domain through its superclasses, or a reasoner reads the pod wrongly.
    """

    class TestGivenAnyClassWhoseRecordsAPlacementHolds:
        def test_is_a_prov_entity_through_its_superclasses(self):
            """is a `prov:Entity` through its superclasses

            Collects the class of each placement of the layout that holds records (more than ten); one from which
            `rdfs:subClassOf` does not lead to `prov:Entity` fails.
            """
            layout = Graph().parse(LAYOUT)
            records = {layout.value(placement, SOLID.forClass)
                       for placement in layout.subjects(CASCADE_NS.holdsRecords, Literal(True))}
            assert len(records) > 10
            assert sorted(c for c in records
                          if PROV.Entity not in set(vocabulary().transitive_objects(c, RDFS.subClassOf))) == []

    class TestGivenAClassTheVocabularyDeclares:
        @pytest.mark.parametrize("name", ["Judgment", "ReferenceSeries"])
        def test_is_a_prov_entity_through_its_own_subclass_statements(self, name):
            """is a `prov:Entity` through the vocabulary's own subclass statements

            From the class, `rdfs:subClassOf` statements in the ontology files alone lead to `prov:Entity`; this holds for a
            judgment and for a reference series, which a pod's records of them rely on.
            """
            assert PROV.Entity in set(vocabulary().transitive_objects(CASCADE_NS[name], RDFS.subClassOf))

    class TestGivenAClassAPodWritesAPropertyOn:
        @pytest.mark.parametrize("subject_class, predicate", [
            pytest.param(PROV.Association, PROV.hadRole, id="an association's role"),
            pytest.param(PROV.Association, PROV.agent, id="an association's agent"),
            pytest.param(CASCADE_NS.FindingForReview, PROV.wasDerivedFrom, id="what a finding for review is derived from"),
            pytest.param(CASCADE_NS.View, PROV.wasDerivedFrom, id="what a view is derived from"),
        ])
        def test_reaches_every_domain_of_that_property(self, subject_class, predicate):
            """reaches every domain of that property

            From the class, `rdfs:subClassOf` leads to a member of each domain that the ontology files give the property;
            a class that misses one would be read wrongly by a reasoner.
            """
            assert reaches_every_domain(vocabulary(), subject_class, predicate)

    class TestGivenProvsAttribution:
        """given PROV's attribution"""

        @pytest.mark.parametrize("term", [
            pytest.param(PROV.Attribution, id="prov:Attribution"),
            pytest.param(PROV.qualifiedAttribution, id="prov:qualifiedAttribution"),
        ])
        def test_is_declared_by_no_ontology_file(self, term):
            """is declared by no ontology file

            No statement in the ontology files has the term as its subject, so a pod has no declaration of it to rely on.
            """
            assert (term, None, None) not in vocabulary()

        def test_reaches_no_domain_of_had_role(self):
            """reaches no domain of `prov:hadRole`, so a role on one would be out of place

            On a copy of the ontology files, `prov:Attribution` is made a subclass of `prov:AgentInfluence`; it still does
            not reach every domain of `prov:hadRole`, so `prov:hadRole` is not written on an attribution.
            """
            graph = Graph() + vocabulary()
            graph.add((PROV.Attribution, RDFS.subClassOf, PROV.AgentInfluence))
            assert not reaches_every_domain(graph, PROV.Attribution, PROV.hadRole)


class TestRootCrate:
    """The root crate · ro-crate-metadata.json

    The root crate is the list of the vocabulary's files that a tool reads to find them, each with its format.
    """

    class TestGivenTheRootCrate:
        def test_lists_every_file_and_no_other(self):
            """lists every ontology, query, runtime, conformance and people file with its format, and no other

            The files the crate lists as parts, with their `encodingFormat`, are compared with the files on disk under
            `ontologies/`, `queries/`, `runtime/`, `conformance/` and `people/`, each with the format its suffix gives; a
            file on one side only, or in another format, fails.
            """
            files = (sorted(ROOT.glob("ontologies/**/*.ttl")) + sorted(QUERIES.rglob("*.rq"))
                     + sorted(path for folder in ("runtime", "conformance", "people") for path in (ROOT / folder).rglob("*")
                              if path.is_file()))
            assert parts(crate(), "./") == {path.relative_to(ROOT).as_posix(): FORMATS[path.suffix] for path in files}

        def test_describes_with_is_based_on_or_citation_only_files_that_exist(self):
            """describes with `isBasedOn` or `citation` only files that exist

            Each item of the crate that has `isBasedOn` or `citation` is named by the path of a file; one other than the
            crate's own root whose file is not there fails.
            """
            described = [path for path, entity in crate().items() if "isBasedOn" in entity or "citation" in entity]
            assert described and [path for path in described if path != "./" and not (ROOT / path).is_file()] == []

        def test_reaches_every_item_from_its_metadata_descriptor(self):
            """reaches every item from its metadata descriptor

            Following each `@id` reference from the descriptor `ro-crate-metadata.json`, every item of the crate is
            reached; an item nothing refers to fails.
            """
            entities, reached, todo = crate(), set(), ["ro-crate-metadata.json"]
            while todo:
                found = todo.pop()
                if found in entities and found not in reached:
                    reached.add(found)
                    todo.extend(references(entities[found]))
            assert sorted(set(entities) - reached) == []


class TestChecksOfTheScanForCopiedTerms:
    """Checks of the scan for copied terms · tests/test_vocabulary.py

    The leaf above that names every term the files use from a copied vocabulary stands on a scan of their text. These
    cases give the scan a text that names a term and a text that names none, so a scan that misses a term, or finds one
    that is not there, is known.
    """

    class TestCopiedTermsNamedIn:
        """`copied_terms_named_in()`"""

        @pytest.mark.parametrize("text, term", [
            pytest.param("PREFIX anno: <http://www.w3.org/ns/oa#>\nSELECT * { ?x anno:Bogus ?y }", OA.Bogus,
                         id="by a prefix a query binds"),
            pytest.param("@prefix anno: <http://www.w3.org/ns/oa#> .\n<a> anno:Bogus <b> .", OA.Bogus,
                         id="by a prefix a Turtle file binds"),
            pytest.param("PREFIX dcterms: <http://purl.org/dc/terms/>\nSELECT * { ?x dcterms:bogus ?y }",
                         URIRef(str(DCTERMS) + "bogus"), id="by `dcterms:`"),
            pytest.param("PREFIX prov: <http://www.w3.org/ns/prov#>\nSELECT * { ?x prov:wasDerivedFrom/prov:bogus ?y }",
                         PROV.bogus, id="at the second place of a path"),
            pytest.param("PREFIX oa: <http://www.w3.org/ns/oa#>\nSELECT * { ?x a/oa:Bogus ?y }", OA.Bogus,
                         id="after `a/` in a path"),
            pytest.param("PREFIX prov: <http://www.w3.org/ns/prov#>\nSELECT * { ?x prov:used|prov:bogus ?y }", PROV.bogus,
                         id="in an alternative of a path"),
            pytest.param("PREFIX pim: <http://www.w3.org/ns/pim/space#>\nSELECT * { ?x pim:bogus ?y }",
                         URIRef("http://www.w3.org/ns/pim/space#bogus"), id="by `pim:`"),
            pytest.param('{"term": "prov:bogus"}', PROV.bogus, id="in JSON, by a prefix `cascade.ttl` binds"),
            pytest.param("<http://www.w3.org/ns/prov#bogus>", PROV.bogus, id="by its IRI written out"),
        ])
        def test_finds_a_term_named(self, text, term):
            """finds a term named

            Given a text that names an invented term of a copied vocabulary in the way the case says, the scan returns a set
            that holds that term's IRI.
            """
            assert term in copied_terms_named_in(text)

        @pytest.mark.parametrize("text", [
            pytest.param("see runtime/steps.md and queries/x.rq for <http://example.org/prov:bogus> and <file:///a/prov:bogus>",
                         id="a prefixed name inside an IRI or a path"),
            pytest.param("PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>\nSELECT * { ?x cascade:bogus ?y . ?x rdf:type ?z }",
                         id="cascade's own terms and RDF's"),
            pytest.param("PREFIX sh: <http://www.w3.org/ns/shacl#>\n[] sh:bogus 1 .", id="SHACL's terms"),
            pytest.param("PREFIX ccda: <https://ns.cascadeprotocol.org/adapter/ccda/v1-draft#>\n[] ccda:bogus 1 .",
                         id="an adapter's namespace under cascade's"),
            pytest.param("urn:uuid:5d0c8f3e and ni:///sha-256;abc", id="a urn and an ni name"),
        ])
        def test_returns_nothing_for(self, text):
            """returns nothing for

            Given a text where a prefixed name sits inside an IRI or a path, or whose terms are cascade's, RDF's, SHACL's or
            an adapter's, or a urn or an ni name, the scan returns an empty set.
            """
            assert copied_terms_named_in(text) == set()
