import json
from functools import cache
from urllib.parse import quote

import pyoxigraph
import pytest
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH

from contract import KITS, CASCADE, ROOT
from manifests import MF, path
from pods import FIXTURES, every_fixture
from test_naming_rules import VECTORS, vectors

SHT = Namespace("http://www.w3.org/ns/shacl-test#")
CASES = ROOT / "tests" / "shape-cases"
TARGETS = (SH.targetClass, SH.targetSubjectsOf, SH.targetObjectsOf, SH.targetNode)
BROKEN_ELSEWHERE = {CASCADE.PlacementShape: "test_pod_layout.py breaks the layout's entries"}
UNDECLARED_ON_PURPOSE = {CASCADE.NoSuchRecord: "Finn's type-filed-nowhere export files a record of a type no folder holds"}


@cache
def parsed(file):
    return Graph().parse(file, format="turtle")


@cache
def shapes():
    graph = Graph()
    for file in sorted(ROOT.glob("ontologies/*.shapes.ttl")):
        graph += parsed(file)
    return graph


@cache
def ontology():
    graph = Graph()
    for file in sorted(ROOT.glob("ontologies/*.ttl")):
        if not file.name.endswith(".shapes.ttl"):
            graph += parsed(file)
    return graph


def path_of(graph, node):
    if node is None or isinstance(node, URIRef):
        return node
    inverse = graph.value(node, SH.inversePath)
    if inverse is not None:
        return ("^", path_of(graph, inverse))
    return tuple(path_of(graph, step) for step in Collection(graph, node))


@cache
def cases():
    """Each case's file, by its name, with the (node shape, path) of each result its manifest says it reports."""
    manifest = parsed(CASES / "manifest.ttl")
    found = {}
    for entry in manifest.subjects(RDF.type, SHT.Validate):
        result = manifest.value(entry, MF.result)
        found[str(entry).rpartition("#")[2]] = (
            path(manifest.value(manifest.value(entry, MF.action), SHT.dataGraph)),
            frozenset((shape, path_of(manifest, manifest.value(r, SH.resultPath)))
                      for r in manifest.objects(result, SH.result) for shape in manifest.objects(r, SH.sourceShape)))
    return found


@cache
def severity_pins():
    """The severities a manifest pins for a result, by case, then by (node shape, path); a result pinning none is any."""
    manifest = parsed(CASES / "manifest.ttl")
    return {str(entry).rpartition("#")[2]: {
                (shape, path_of(manifest, manifest.value(r, SH.resultPath))): set(manifest.objects(r, SH.resultSeverity))
                for r in manifest.objects(manifest.value(entry, MF.result), SH.result)
                for shape in manifest.objects(r, SH.sourceShape) if (r, SH.resultSeverity, None) in manifest}
            for entry in manifest.subjects(RDF.type, SHT.Validate)}


def node_shape(shape):
    return shape if (shape, RDF.type, SH.NodeShape) in shapes() else shapes().value(None, SH.property, shape)


@cache
def validated():
    """One validation of every case: each file's own nodes are its alone, as its IRIs are relative to it."""
    data, owner = Graph(), {}
    for name, (file, _) in cases().items():
        data += parsed(file)
        owner |= {node: name for node in parsed(file).subjects()}
    _, report, _ = validate(data, shacl_graph=shapes())
    found, severity = {name: set() for name in cases()}, {name: {} for name in cases()}
    for result in report.objects(None, SH.result):
        name = owner[report.value(result, SH.focusNode)]
        key = (node_shape(report.value(result, SH.sourceShape)), path_of(report, report.value(result, SH.resultPath)))
        found[name].add(key)
        severity[name].setdefault(key, set()).add(report.value(result, SH.resultSeverity))
    return found, severity


def reported():
    """What validating every case reports, by case: the (node shape, path) of each result."""
    return validated()[0]


def severities():
    """The severities each case's results carry, by case, then by (node shape, path)."""
    return validated()[1]


def targets(shape, data):
    found = {node for kind in shapes().objects(shape, SH.targetClass) for node in data.subjects(RDF.type, kind)}
    found |= {node for p in shapes().objects(shape, SH.targetSubjectsOf) for node in data.subjects(p, None)}
    found |= {node for p in shapes().objects(shape, SH.targetObjectsOf) for node in data.objects(None, p)}
    return found | set(shapes().objects(shape, SH.targetNode))


def targeting():
    return {shape for shape in shapes().subjects(RDF.type, SH.NodeShape)
            if any((shape, t, None) in shapes() for t in TARGETS)}


def namespaces():
    return tuple(str(n) for n in ontology().subjects(RDF.type, OWL.Ontology))


def constrained_by_one_shape():
    """Each property of this vocabulary that one targeting node shape alone constrains, with that shape. A property
    more than one class's content carries is no class's target."""
    shapes_of = {}
    for shape in targeting():
        for property_shape in shapes().objects(shape, SH.property):
            p = shapes().value(property_shape, SH.path)
            if isinstance(p, URIRef) and str(p).startswith(namespaces()):
                shapes_of.setdefault(p, set()).add(shape)
    return {p: shape for p, (shape, *more) in shapes_of.items() if not more}


def untargeted(data):
    """Each subject of a kind the shapes cover that no shape it needs takes as a focus node: an instance of a class of
    this vocabulary that no shape targets by that class, or a subject of a property one shape alone constrains that
    the shape does not target."""
    focus = {shape: targets(shape, data) for shape in targeting()}
    by_class = {(kind, node) for shape in targeting() for kind in shapes().objects(shape, SH.targetClass)
                for node in focus[shape]}
    found = {(str(node), str(kind)) for node, kind in data.subject_objects(RDF.type)
             if str(kind).startswith(namespaces()) and (kind, node) not in by_class}
    for p, shape in constrained_by_one_shape().items():
        found |= {(str(node), str(p)) for node in data.subjects(p, None) if node not in focus[shape]}
    return found


def fixture_pod(fixture):
    graph = Graph()
    for relative in fixture.files():
        graph += parsed(fixture.folder / relative)
    return graph


def pod_files_carried():
    yield from (fixture.folder / relative for fixture in FIXTURES for relative in fixture.files())
    yield from (file for file, expected in cases().values() if not expected)
    yield from (ROOT / "runtime" / "scripted-input").rglob("*.ttl")
    for kit in KITS:
        yield from (kit / "scripted-input").rglob("*.ttl")
        yield from (kit / "expected").glob("*.ttl")


def iris(file):
    quads = pyoxigraph.parse(path=file, format=pyoxigraph.RdfFormat.TURTLE, base_iri=file.as_uri())
    return {term.value for quad in quads for term in (quad.subject, quad.predicate, quad.object)
            if isinstance(term, pyoxigraph.NamedNode)}


def name_shape_select():
    [constraint] = shapes().objects(CASCADE.ServerRecordNameShape, SH.sparql)
    return str(shapes().value(constraint, SH.select))


def server_vectors():
    return [vector for vector in vectors() if vector.rule == "RecordFromServerNamingRule" and "%" not in vector.inputs[0]]


def records(pairs):
    graph = Graph()
    for name, vector in pairs:
        graph.add((URIRef(name), CASCADE.sourceUrl, URIRef("/".join(vector.inputs))))
    return graph


def servers(pairs):
    graph = Graph()
    for name, vector in pairs:
        graph.add((URIRef(name), RDF.type, CASCADE.Server))
        graph.add((URIRef(name), CASCADE.serverBaseUrl, Literal(vector.inputs[0])))
    return graph


def name_shape_only():
    graph = Graph()
    for triple in shapes().triples((CASCADE.ServerRecordNameShape, None, None)):
        graph.add(triple)
    for constraint in shapes().objects(CASCADE.ServerRecordNameShape, SH.sparql):
        for triple in shapes().triples((constraint, None, None)):
            graph.add(triple)
    return graph


def selectable_codes(concepts):
    """Each code of the concepts and of theirs, at every depth, but one HL7 marks notSelectable (a heading, not a code a
    coding may carry), percent-encoded as XPath's fn:encode-for-uri does, every character but letters, digits and - _ . ~"""
    for concept in concepts:
        if not any(p["code"] == "notSelectable" and p.get("valueBoolean") for p in concept.get("property", [])):
            yield quote(concept["code"], safe="")
        yield from selectable_codes(concept.get("concept", []))


HL7_CODE_SYSTEM_ROWS = [
    (CASCADE.DataAbsentReasonCodeShape, CASCADE.DataAbsentReason, "CodeSystem-data-absent-reason.json"),
    (CASCADE.NullFlavorCodeShape, CASCADE.NullFlavor, "CodeSystem-v3-NullFlavor.json"),
    (CASCADE.ObservationInterpretationCodeShape, CASCADE.ObservationInterpretation,
     "CodeSystem-v3-ObservationInterpretation.json"),
]
HL7_IDS = ["DataAbsentReason", "NullFlavor", "ObservationInterpretation"]
HL7_CODE_SYSTEMS = pytest.mark.parametrize("shape, system, file", HL7_CODE_SYSTEM_ROWS, ids=HL7_IDS)
HL7_SYSTEM_FILES = pytest.mark.parametrize("system, file", [row[1:] for row in HL7_CODE_SYSTEM_ROWS], ids=HL7_IDS)


class TestShapesThatFindAWrongPod:
    """Shapes that find a wrong pod · ontologies/*.shapes.ttl, tests/shape-cases/

    The shapes say what a record, a judgment or a file of a pod must state. A shape case is a small file, valid or broken
    in one way, and the manifest beside the cases lists what validating each reports: which shape, and at which property.
    """

    class TestGivenAShapeCase:
        @pytest.mark.parametrize("name", sorted(cases()))
        def test_reports_exactly_the_results_the_manifest_lists_for_it(self, name):
            expected, found = cases()[name][1], reported()[name]
            assert found == expected, {"expected": sorted(map(str, expected)), "reported": sorted(map(str, found))}
            unpinned = {str(key): sorted(map(str, severity)) for key, severity in severity_pins()[name].items()
                        if severities()[name].get(key) != severity}
            assert unpinned == {}

    class TestGivenTheManifestOfTheShapeCases:
        def test_lists_every_file_under_shape_cases(self):
            """lists every file under `tests/shape-cases/`"""
            assert {file for file in CASES.rglob("*.ttl") if file.name != "manifest.ttl"} == {f for f, _ in cases().values()}

        def test_says_that_a_case_conforms_exactly_when_it_lists_no_result_for_it(self):
            manifest = parsed(CASES / "manifest.ttl")
            conforms = {str(entry).rpartition("#")[2]: manifest.value(manifest.value(entry, MF.result), SH.conforms)
                        for entry in manifest.subjects(RDF.type, SHT.Validate)}
            assert sorted(name for name, (_, expected) in cases().items() if conforms[name] != Literal(not expected)) == []

    class TestGivenAShapeThatTargetsAPodsData:
        """given a shape that targets a pod's data"""

        def test_has_a_valid_case_and_a_broken_one(self):
            """has a valid case and a broken one

            Every such shape has both, but `cascade:PlacementShape`, whose breaks are the layout's entries in
            `test_pod_layout.py`.
            """
            valid = {shape for name, (file, expected) in cases().items() if not expected
                     for shape in targeting() if targets(shape, parsed(file))}
            broken = {shape for _, expected in cases().values() for shape, _ in expected}
            assert sorted(targeting() - set(BROKEN_ELSEWHERE) - (valid & broken)) == []

    class TestGivenAnyFixture:
        @every_fixture
        def test_conforms_to_the_shapes(self, fixture):
            conforms, _, text = validate(fixture_pod(fixture), shacl_graph=shapes())
            assert conforms, text

    class TestGivenAnyFixtureOrValidCase:
        def test_takes_every_subject_of_a_kind_the_shapes_cover_as_a_focus_node_of_its_shape(self):
            pods = {fixture.name: fixture_pod(fixture) for fixture in FIXTURES}
            pods |= {name: parsed(file) for name, (file, expected) in cases().items() if not expected}
            assert {name: sorted(found) for name, data in pods.items() if (found := untargeted(data))} == {}


class TestTermsDeclared:
    """Terms declared for everything a pod writes · ontologies/*.ttl

    A term in one of the vocabulary's namespaces means something only once an ontology file declares it. Every pod file
    the vocabulary carries (fixtures, valid shape cases, scripted input, the kits' expected files) is held to that.
    """

    class TestGivenEveryPodFileTheVocabularyCarries:
        """given every pod file the vocabulary carries

        The files of the fixtures, the valid shape cases, the examples' scripted input and the kits' scripted input and
        expected files: each is a file a pod could hold, and each is read for the terms it writes.
        """

        def test_writes_no_term_of_the_vocabularys_namespaces_that_no_ontology_file_declares(self):
            """writes no term of the vocabulary's namespaces that no ontology file declares

            One term is allowed to go undeclared, on purpose: `cascade:NoSuchRecord`, the type that a hand-made failure
            fixture (`runtime/scripted-input/finn/bridge/type-filed-nowhere/`) gives its record, to show a record of a type
            the pod files nowhere. Any other undeclared term fails, naming it and its file.
            """
            declared = {str(term) for term in ontology().subjects(RDF.type, None)} | set(map(str, UNDECLARED_ON_PURPOSE))
            ours = namespaces()
            undeclared = {(term, file.relative_to(ROOT).as_posix()) for file in pod_files_carried() for term in iris(file)
                          if term.startswith(ours) and term not in declared}
            assert sorted(undeclared) == []


class TestNameShapes:
    """Shapes that check a name against the address it comes from · cascade:ServerRecordNameShape, cascade:ServerNameShape

    A record pulled from a server, and the server itself, are named from an address by a naming rule, which is a SPARQL
    query. Each shape embeds its rule's query, so validating a pod finds a name that the rule does not give.
    """

    class TestGivenARecordWithASourceAddress:
        """given a record with a source address

        A record pulled from a server keeps the address it was fetched from, as `cascade:sourceUrl`, and its name is the
        one `RecordFromServerNamingRule` gives for that address.
        """

        def test_embeds_the_query_of_its_naming_rule_after_binding_its_inputs(self):
            """embeds the query of `RecordFromServerNamingRule` after binding its inputs"""
            rule = (VECTORS / "RecordFromServerNamingRule.rq").read_text(encoding="utf-8")
            body = rule.split(" WHERE {\n", 1)[1].rsplit("\n}", 1)[0]
            select = name_shape_select()
            assert body in select
            assert select.index("AS ?input3") < select.index(body)

        def test_accepts_each_server_vectors_name_for_its_address_and_no_other_name(self):
            """accepts each server vector's name for its address, and no other vector's name for it

            A record at each vector's address, named as the vector says, passes the shape; the same records with the names
            rotated one place along all fail it.
            """
            found = server_vectors()
            assert len(found) >= 2
            conforms, _, _ = validate(records((vector.expected, vector) for vector in found), shacl_graph=shapes())
            assert conforms
            swapped = records(zip([vector.expected for vector in found[1:] + found[:1]], found))
            _, report, _ = validate(swapped, shacl_graph=shapes())
            assert {str(node) for node in report.objects(None, SH.focusNode)} == {vector.expected for vector in found}

        def test_leaves_alone_an_address_that_holds_a_delete_character(self):
            pod = Graph()
            pod.add((URIRef("urn:uuid:11111111-1111-8111-8111-111111111106"), CASCADE.sourceUrl,
                     URIRef("https://fhir.example/r4\x7f/Observation/obs-9")))
            conforms, _, _ = validate(pod, shacl_graph=shapes())
            assert conforms

    class TestGivenAServer:
        def test_embeds_the_query_of_its_naming_rule(self):
            """embeds the query of `ServerNamingRule`"""
            [constraint] = shapes().objects(CASCADE.ServerNameShape, SH.sparql)
            body = (VECTORS / "ServerNamingRule.rq").read_text(encoding="utf-8").split(" WHERE {\n", 1)[1].rsplit("\n}", 1)[0]
            assert body in str(shapes().value(constraint, SH.select))

        def test_accepts_each_server_vectors_name_for_its_base_address_and_no_other_name(self):
            """accepts each server vector's name for its base address, and no other vector's name for it

            A server at each vector's base address, named as the vector says, passes the shape; the same servers with the
            names rotated one place along all fail it.
            """
            found = [vector for vector in vectors() if vector.rule == "ServerNamingRule"]
            assert len(found) >= 2
            conforms, _, _ = validate(servers((vector.expected, vector) for vector in found), shacl_graph=shapes())
            assert conforms
            _, report, _ = validate(servers(zip([vector.expected for vector in found[1:] + found[:1]], found)),
                                    shacl_graph=shapes())
            assert {str(node) for node in report.objects(None, SH.focusNode)} == {vector.expected for vector in found}

    class TestGivenAKitsFiles:
        """given a kit's scripted input and expected files"""

        @pytest.mark.parametrize("kit", KITS, ids=lambda kit: kit.name)
        def test_reports_no_record_named_otherwise_than_its_source_address_gives(self, kit):
            pod = Graph()
            for folder in ("scripted-input", "expected"):
                for file in sorted((kit / folder).rglob("*.ttl")):
                    pod += parsed(file)
            _, report, _ = validate(pod, shacl_graph=name_shape_only())
            named_wrong = {str(report.value(result, SH.focusNode)) for result in report.objects(None, SH.result)
                           if report.value(result, SH.sourceShape) == CASCADE.ServerRecordNameShape}
            assert named_wrong == set()


class TestHl7CodeShapes:
    """Shapes that list the codes of an HL7 code system · cascade:DataAbsentReasonCodeShape, cascade:NullFlavorCodeShape,
    cascade:ObservationInterpretationCodeShape

    Three shapes list the codes a coding may carry from a code system that HL7 publishes. The list is HL7's own, read from
    the copy under `tests/terminology/hl7-terminology/`.
    """

    class TestGivenOneOfTheThreeCodeSystems:
        @HL7_SYSTEM_FILES
        def test_is_declared_with_the_url_that_hl7_publishes_it_under(self, system, file):
            """is declared with the URL that HL7 publishes it under"""
            published = json.loads((ROOT / "tests" / "terminology" / "hl7-terminology" / file).read_text(encoding="utf-8"))
            assert published["url"] == str(ontology().value(system, CASCADE.codingSystemUri))

        @HL7_CODE_SYSTEMS
        def test_lists_exactly_the_codes_hl7_lets_a_coding_carry(self, shape, system, file):
            """lists exactly the codes HL7 lets a coding carry, percent-encoded, in HL7's order

            The shape's `sh:in` list, prefix included, equals HL7's codes with that prefix, in order: every code at every
            depth but one HL7 marks `notSelectable` (a heading, not a code a coding may carry), each percent-encoded as
            XPath's fn:encode-for-uri does, every character but letters, digits and - _ . ~
            """
            published = json.loads((ROOT / "tests" / "terminology" / "hl7-terminology" / file).read_text(encoding="utf-8"))
            stem = str(ontology().value(system, URIRef("http://rdfs.org/ns/void#uriSpace")))
            listed = [str(code) for code in Collection(shapes(), shapes().value(shape, SH["in"]))]
            assert listed == [stem + code for code in selectable_codes(published["concept"])]


class TestChecksOfTheShapeCaseTools:
    """Checks of the shape cases' own tools · tests/test_shapes.py

    The shape cases are validated together by code in this module. This case shows that code what it must catch.
    """

    class TestValidated:
        """`validated()`"""

        def test_credits_each_result_to_one_case(self):
            """credits each result to one case, as no two case files share an absolute subject IRI

            `validated()` merges every case into one graph and credits each node to one file, so a name two files share
            would credit one file with the other's results.
            """
            owners = {}
            for name, (file, _) in cases().items():
                for node in {s for s in parsed(file).subjects() if isinstance(s, URIRef) and ":" in s}:
                    owners.setdefault(node, set()).add(name)
            assert {str(node): sorted(names) for node, names in owners.items() if len(names) > 1} == {}
