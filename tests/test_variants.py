"""The variant records and the ClinVar tables: the variant terms and their shapes, the HGVS and ClinVar code
systems, a variant classifications row in both of its forms, ClinVar's values parsed into concepts, and the two rules that
change what a query may do with a code (runtime/matcher.feature, rule M4)."""

import json
import re
from functools import cache

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, SH, SKOS, XSD

from contract import QUERIES, CASCADE, ROOT
from engines import ENGINES, parsed, prepared
from test_queries import every_query, nodes
from test_tables import kinds, messages, shapes

VOID = Namespace("http://rdfs.org/ns/void#")
VECTORS = ROOT / "tests" / "vectors" / "clinvar"
UNRESERVED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~")


def vector(name):
    return json.loads((VECTORS / name).read_text(encoding="utf-8"))


@cache
def genomics_shapes():
    return Graph().parse(ROOT / "ontologies" / "cascade.shapes.ttl")


def said(data):
    """The messages the genomics shapes give about the data."""
    prefixes = ("@prefix cascade: <https://ns.cascadeprotocol.org/cascade#> .\n"
                "@prefix prov: <http://www.w3.org/ns/prov#> .\n"
                "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
    _, report, _ = validate(Graph().parse(data=prefixes + data, format="turtle"), shacl_graph=genomics_shapes())
    return {str(message) for message in report.objects(None, SH.resultMessage)}


@pytest.mark.parametrize("data, message", [
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "NM_000249.4:c.2042C>T" .', None),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "NG_007110.2:c.100A>G" .', None),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "XM_011543.1:c.5del" .', None),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "NC_000003.12:c.1A>G" .', None),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "LRG_216t1:c.2042C>T" .', None),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "NM_000249.3(MLH1):c.2042C>T" .', "normal form"),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "NM_000249.4:p.Ala681Val" .', "normal form"),
    ('<urn:x:v> cascade:hgvsCodingDnaExpression "c.2042C>T" .', "normal form"),
    ('<urn:x:r> a cascade:GeneticVariantFinding . <urn:x:v> prov:specializationOf <urn:x:r> ; cascade:hgvsCodingDnaExpression "NM_000249.4:c.2042C>T", "NM_000249.3:c.2042C>T" .',
     "at most one HGVS"),
    ('<urn:x:e> cascade:mergedFrom <urn:x:a>, <urn:x:b> ; cascade:hgvsCodingDnaExpression "NM_000249.4:c.2042C>T", "NM_000249.3:c.2042C>T" ;'
     ' cascade:geneSymbol "MLH1", "EPCAM" ; cascade:clinvarVariationId "90011", "90012" .', None),
    ('<urn:x:v> cascade:clinvarVariationId "90011" .', None),
    ('<urn:x:v> cascade:clinvarVariationId "VCV000090011" .', "no leading zero"),
    ('<urn:x:v> cascade:clinvarVariationId "090011" .', "no leading zero"),
    ('<urn:x:r> a cascade:GeneticVariantFinding . <urn:x:v> prov:specializationOf <urn:x:r> ; cascade:clinvarVariationId "90011", "90012" .', "at most one ClinVar"),
    ('<urn:x:v> cascade:geneSymbol "MLH1" .', None),
    ('<urn:x:r> a cascade:GeneticVariantFinding . <urn:x:v> prov:specializationOf <urn:x:r> ; cascade:geneSymbol "MLH1", "EPCAM" .', "at most one gene symbol"),
    ('<urn:x:i> cascade:interpretedDate "2024-01-05"^^xsd:date .', None),
    ('<urn:x:i> cascade:interpretedDate "2024-01-05T10:00:00Z"^^xsd:dateTime .', "one xsd:date"),
    ('<urn:x:i> cascade:interpretedDate "2024-01-05" .', "one xsd:date"),
    ('<urn:x:i> cascade:acmgClassification cascade:LikelyPathogenic .', None),
    ('<urn:x:i> cascade:acmgClassification <urn:x:other> .', "at most one ACMG"),
    ('<urn:x:i> cascade:acmgClassification cascade:Benign, cascade:UncertainSignificance .', "at most one ACMG"),
    ('<urn:x:i> cascade:variantInterpreted <urn:uuid:5b1f2c3e-7a4d-4e8b-9c60-1d2e3f4a5b6c> .', None),
    ('<urn:x:i> cascade:variantInterpreted "a variant" .', "named by the variant record's IRI"),
    ('<urn:x:i> cascade:variantInterpreted <urn:x:a>, <urn:x:b> .', "named by the variant record's IRI"),
    ('<urn:x:i> cascade:acmgEvidenceCode "PVS1", "BP7" .', None),
    ('<urn:x:i> cascade:acmgEvidenceCode "PM7" .', "28 criteria"),
    ('<urn:x:i> cascade:statementObject "a condition" .', "at most one object"),
])
def test_the_genomics_shapes_accept_each_normal_form_and_refuse_each_break_with_its_message(data, message):
    found = said(data)
    assert (found == set()) if message is None else any(message in m for m in found), found


def evaluated(engine, system, literal):
    stem = str(kinds().value(CASCADE[system], VOID.uriSpace))
    query = f"SELECT (CONCAT({json.dumps(stem)}, ENCODE_FOR_URI({json.dumps(literal)})) AS ?iri) WHERE {{}}"
    return str(ENGINES[engine]().select(query)[0]["iri"])


@pytest.mark.parametrize("engine", sorted(ENGINES))
def test_each_code_gets_its_iri_by_encode_for_uri_on_each_engine(engine):
    rows = [row for row in vector("code-iris.json") if row["literal"] is not None]
    assert len(rows) == 7
    assert {row["iri"]: evaluated(engine, row["system"], row["literal"]) for row in rows} == {
        row["iri"]: row["iri"] for row in rows}


def test_a_written_variation_id_has_a_literal_of_digits_or_none_when_it_is_no_variation():
    for row in vector("code-iris.json"):
        if row["system"] == "ClinVar":
            match = re.fullmatch(r"(?:VCV0*)?([1-9][0-9]*)(?:\.[0-9]+)?", row["written"])
            assert (match.group(1) if match else None) == row["literal"], row


def row_from_json(row):
    found, subject = Graph(), URIRef(row["variation"])
    for key, predicate in (("hgvs", CASCADE.hgvsExpression), ("classification", CASCADE.clinvarClassification)):
        for value in row.get(key, []):
            found.add((subject, predicate, URIRef(value)))
    if "reviewStatus" in row:
        found.add((subject, CASCADE.clinvarReviewStatus, URIRef(row["reviewStatus"])))
    if "lastEvaluated" in row:
        found.add((subject, CASCADE.lastEvaluated, Literal(row["lastEvaluated"], datatype=XSD.date)))
    for key in ("contributingSubmitterCount", "submitterCount"):
        if key in row:
            found.add((subject, CASCADE[key], Literal(row[key], datatype=XSD.integer)))
    return found


def test_the_row_in_turtle_conforms_to_its_shape_and_the_row_in_json_is_the_same_triples():
    turtle = parsed(VECTORS / "row.ttl")
    assert messages(CASCADE.VariantClassifications, turtle) == set()
    assert isomorphic(turtle, row_from_json(vector("row.json")))
    assert re.fullmatch(r"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        vector("row.json")["series"])


def members(scheme):
    """The concepts of a scheme with each label they go by, preferred or alternative."""
    return {concept: [str(label) for p in (SKOS.prefLabel, SKOS.altLabel) for label in kinds().objects(concept, p)]
            for concept in kinds().subjects(SKOS.inScheme, scheme)}


def parse_classification(written, scheme):
    """The parse rules for a classification value: the whole value `-`, else split on `; ` then `/`, never on `,`; each
    term matches a label exactly; a term matching none is a finding."""
    labelled = {label: concept for concept, labels in members(scheme).items() for label in labels}
    if written == "-":
        return {kinds().value(None, SKOS.notation, Literal("-"))}, []
    terms = [term for part in written.split("; ") for term in part.split("/")]
    return ({labelled[term] for term in terms if term in labelled},
            [term for term in terms if term not in labelled])


def test_each_classification_value_parses_to_its_concepts_and_each_review_status_to_its_concept():
    values = vector("values.json")
    classes, statuses = CASCADE.ClinVarClassifications, CASCADE.ClinVarReviewStatuses
    for row in values["classifications"]:
        concepts, findings = parse_classification(row["written"], classes)
        assert (concepts, findings) == ({URIRef(c) for c in row["concepts"]}, row["findings"]), row
        assert {URIRef(c) for c in row["concepts"]} <= set(members(classes))
    labelled = {label: concept for concept, labels in members(statuses).items() for label in labels}
    for row in values["reviewStatuses"]:
        assert labelled.get(row["written"]) == (URIRef(row["concept"]) if row["concept"] else None), row


ACMG_FIVE = {"Pathogenic", "LikelyPathogenic", "UncertainSignificance", "LikelyBenign", "Benign"}


def test_the_five_acmg_values_are_matched_by_the_labels_clinvar_spells_them_with():
    spelled = {str(concept).rpartition("#")[2]: str(kinds().value(concept, SKOS.prefLabel))
               for concept in members(CASCADE.ClinVarClassifications)
               if str(concept).rpartition("#")[2] in ACMG_FIVE}
    assert spelled == {"Pathogenic": "Pathogenic", "LikelyPathogenic": "Likely pathogenic",
                       "UncertainSignificance": "Uncertain significance", "LikelyBenign": "Likely benign", "Benign": "Benign"}


def test_a_value_is_in_a_scheme_a_row_may_hold_exactly_when_the_row_shape_lists_it():
    listed = {}
    for property_shape in shapes().objects(CASCADE.VariantClassificationRowShape, SH.property):
        path = shapes().value(property_shape, SH.path)
        if path in (CASCADE.clinvarClassification, CASCADE.clinvarReviewStatus):
            listed[path] = set(Collection(shapes(), shapes().value(property_shape, SH["in"])))
    assert listed == {CASCADE.clinvarClassification: set(members(CASCADE.ClinVarClassifications)),
                      CASCADE.clinvarReviewStatus: set(members(CASCADE.ClinVarReviewStatuses))}


def test_the_concepts_two_schemes_share_are_one_iri_each():
    assert set(members(CASCADE.ClinVarClassifications)) & set(members(CASCADE.ClinVarReviewStatuses)) == {
        CASCADE.ClinVarNoClassificationsFromUnflaggedRecords, CASCADE.ClinVarNoClassificationForTheSingleVariant}


def test_the_kinds_an_app_keeps_are_those_a_rule_list_names_and_those_marked_read_by_pages():
    declared = set(kinds().subjects(RDF.type, CASCADE.TableKind))
    marked = {kind for kind in declared if (kind, CASCADE.readByAppPages, Literal(True)) in kinds()}
    named = {kind for path in (ROOT / "runtime" / "rule-list").glob("*.ttl") if path.name != "references.ttl"
             for kind in parsed(path).objects(None, CASCADE.tableKind)}
    assert marked == {CASCADE.CodeNames, CASCADE.RetiredCodes, CASCADE.VariantClassifications, CASCADE.PanelMembers, CASCADE.DrugClasses}
    assert declared - named - marked == {CASCADE.SubstanceIngredients}


def joins_a_stem_to_a_literal_without_encoding(text, stems):
    """Whether a CONCAT of the query has a stem for an argument and an argument that is not ENCODE_FOR_URI."""
    for node in nodes(prepared(text).algebra):
        if node.name == "Builtin_CONCAT":
            arguments = list(node["arg"])
            if any(isinstance(a, Literal) and str(a) in stems for a in arguments):
                if any(not isinstance(a, Literal) and getattr(a, "name", None) != "Builtin_ENCODE_FOR_URI"
                       for a in arguments):
                    return True
    return False


def test_the_encoding_check_sees_a_stem_joined_to_a_literal_without_ENCODE_FOR_URI():
    stems = {"http://x/"}
    assert joins_a_stem_to_a_literal_without_encoding('SELECT * { BIND (CONCAT("http://x/", STR(?a)) AS ?b) }', stems)
    assert not joins_a_stem_to_a_literal_without_encoding(
        'SELECT * { BIND (CONCAT("http://x/", ENCODE_FOR_URI(STR(?a))) AS ?b) }', stems)
    assert not joins_a_stem_to_a_literal_without_encoding('SELECT * { BIND (CONCAT("a", STR(?a)) AS ?b) }', stems)


def test_every_query_that_joins_a_stem_to_a_literal_encodes_it():
    stems = {str(space) for space in kinds().objects(None, VOID.uriSpace)}
    assert {relative for relative in every_query()
            if joins_a_stem_to_a_literal_without_encoding((QUERIES / relative).read_text(encoding="utf-8"), stems)} == set()
