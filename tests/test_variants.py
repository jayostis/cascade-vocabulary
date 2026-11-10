import json
import re

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import SH, SKOS, XSD

from contract import CASCADE, ROOT
from engines import ENGINES, parsed
from ontologies import row_messages, shapes, terms

VOID = Namespace("http://rdfs.org/ns/void#")
VECTORS = ROOT / "tests" / "vectors" / "clinvar"
ACMG_FIVE = {"Pathogenic", "LikelyPathogenic", "UncertainSignificance", "LikelyBenign", "Benign"}


def vector(name):
    return json.loads((VECTORS / name).read_text(encoding="utf-8"))


def shape_messages(data):
    """The messages the genomics shapes give about the data."""
    prefixes = ("@prefix cascade: <https://ns.cascadeprotocol.org/cascade#> .\n"
                "@prefix prov: <http://www.w3.org/ns/prov#> .\n"
                "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
    _, report, _ = validate(Graph().parse(data=prefixes + data, format="turtle"), shacl_graph=shapes())
    return {str(message) for message in report.objects(None, SH.resultMessage)}


STATEMENTS = [
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "NM_000249.4:c.2042C>T" .', None,
                 id="a coding DNA expression on an NM_ transcript"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "NG_007110.2:c.100A>G" .', None,
                 id="a coding DNA expression on an NG_ sequence"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "XM_011543.1:c.5del" .', None,
                 id="a coding DNA expression on an XM_ transcript"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "NC_000003.12:c.1A>G" .', None,
                 id="a coding DNA expression on an NC_ sequence"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "LRG_216t1:c.2042C>T" .', None,
                 id="a coding DNA expression on an LRG transcript"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "NM_000249.3(MLH1):c.2042C>T" .', "normal form",
                 id="an expression with a gene in parentheses"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "NM_000249.4:p.Ala681Val" .', "normal form",
                 id="a protein expression"),
    pytest.param('<urn:x:v> cascade:hgvsCodingDnaExpression "c.2042C>T" .', "normal form",
                 id="an expression with no sequence"),
    pytest.param('<urn:x:r> a cascade:GeneticVariantFinding . <urn:x:v> prov:specializationOf <urn:x:r> ; cascade:hgvsCodingDnaExpression "NM_000249.4:c.2042C>T", "NM_000249.3:c.2042C>T" .',
     "at most one HGVS",
                 id="two expressions on one version"),
    pytest.param('<urn:x:e> cascade:mergedFrom <urn:x:a>, <urn:x:b> ; cascade:hgvsCodingDnaExpression "NM_000249.4:c.2042C>T", "NM_000249.3:c.2042C>T" ;'
     ' cascade:geneSymbol "MLH1", "EPCAM" ; cascade:clinvarVariationId "90011", "90012" .', None,
                 id="a merged entry with two of each"),
    pytest.param('<urn:x:v> cascade:clinvarVariationId "90011" .', None,
                 id="a ClinVar ID of digits"),
    pytest.param('<urn:x:v> cascade:clinvarVariationId "VCV000090011" .', "no leading zero",
                 id="a ClinVar ID written as VCV and a number"),
    pytest.param('<urn:x:v> cascade:clinvarVariationId "090011" .', "no leading zero",
                 id="a ClinVar ID with a leading zero"),
    pytest.param('<urn:x:r> a cascade:GeneticVariantFinding . <urn:x:v> prov:specializationOf <urn:x:r> ; cascade:clinvarVariationId "90011", "90012" .', "at most one ClinVar",
                 id="two ClinVar IDs on one version"),
    pytest.param('<urn:x:v> cascade:geneSymbol "MLH1" .', None,
                 id="a gene symbol"),
    pytest.param('<urn:x:r> a cascade:GeneticVariantFinding . <urn:x:v> prov:specializationOf <urn:x:r> ; cascade:geneSymbol "MLH1", "EPCAM" .', "at most one gene symbol",
                 id="two gene symbols on one version"),
    pytest.param('<urn:x:i> cascade:interpretedDate "2024-01-05"^^xsd:date .', None,
                 id="an interpreted date to the day"),
    pytest.param('<urn:x:i> cascade:interpretedDate "2024-01"^^xsd:gYearMonth .', None,
                 id="an interpreted date to the month"),
    pytest.param('<urn:x:i> cascade:interpretedDate "2024-01-05T10:00:00Z"^^xsd:dateTime .', "xsd:gYearMonth or xsd:date",
                 id="an interpreted date with a time"),
    pytest.param('<urn:x:i> cascade:interpretedDate "2024-01-05" .', "xsd:gYearMonth or xsd:date",
                 id="an interpreted date with no datatype"),
    pytest.param('<urn:x:i> cascade:acmgClassification cascade:LikelyPathogenic .', None,
                 id="an ACMG class"),
    pytest.param('<urn:x:i> cascade:acmgClassification <urn:x:other> .', "at most one ACMG",
                 id="an ACMG class that is no concept"),
    pytest.param('<urn:x:i> cascade:acmgClassification cascade:Benign, cascade:UncertainSignificance .', "at most one ACMG",
                 id="two ACMG classes"),
    pytest.param('<urn:x:i> cascade:variantInterpreted <urn:uuid:5b1f2c3e-7a4d-4e8b-9c60-1d2e3f4a5b6c> .', None,
                 id="a variant named by its IRI"),
    pytest.param('<urn:x:i> cascade:variantInterpreted "a variant" .', "named by the variant record's IRI",
                 id="a variant named in text"),
    pytest.param('<urn:x:i> cascade:variantInterpreted <urn:x:a>, <urn:x:b> .', "named by the variant record's IRI",
                 id="two variants"),
    pytest.param('<urn:x:i> cascade:acmgEvidenceCode "PM2_supporting", "PS3_not_met", "no_criteria_met" .', None,
                 id="three evidence codes with their outcomes"),
    pytest.param('<urn:x:i> cascade:acmgEvidenceCode "PM2_moderate" .', "evidence outcome",
                 id="an evidence outcome ACMG does not have"),
    pytest.param('<urn:x:i> cascade:objectCondition "a condition" .', "at most one object",
                 id="a condition named in text"),
    pytest.param('<urn:x:i> cascade:objectCondition <urn:x:a>, <urn:x:b> .', "at most one object",
                 id="two conditions"),
]
ACCEPTED = [pytest.param(row.values[0], id=row.id) for row in STATEMENTS if row.values[1] is None]
REFUSED = [row for row in STATEMENTS if row.values[1] is not None]


def evaluated(engine, system, literal):
    stem = str(terms().value(CASCADE[system], VOID.uriSpace))
    query = f"SELECT (CONCAT({json.dumps(stem)}, ENCODE_FOR_URI({json.dumps(literal)})) AS ?iri) WHERE {{}}"
    return str(ENGINES[engine]().select(query)[0]["iri"])


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


def members(scheme):
    """The concepts of a scheme with each label they go by, preferred or alternative."""
    return {concept: [str(label) for p in (SKOS.prefLabel, SKOS.altLabel) for label in terms().objects(concept, p)]
            for concept in terms().subjects(SKOS.inScheme, scheme)}


def parse_classification(written, scheme):
    """The parse rules for a classification value: the whole value `-`, else split on `; ` then `/`, never on `,`; each
    term matches a label exactly; a term matching none is a finding."""
    labelled = {label: concept for concept, labels in members(scheme).items() for label in labels}
    if written == "-":
        return {terms().value(None, SKOS.notation, Literal("-"))}, []
    words = [word for part in written.split("; ") for word in part.split("/")]
    return ({labelled[word] for word in words if word in labelled},
            [word for word in words if word not in labelled])


class TestVariantRecords:
    """Variant records and ClinVar's classifications · ontologies/cascade.ttl, ontologies/cascade.shapes.ttl, tests/vectors/clinvar/

    A genetic test reports a variant by its HGVS expression, the standard way to write a change in a gene, and ClinVar
    says how laboratories classify it. The shapes say what a variant record and its interpretation may state, and the
    vectors show how ClinVar's own values and IDs become the vocabulary's concepts and code IRIs.
    """

    class TestGivenAStatementAboutAVariant:
        """given a statement about a variant or its interpretation"""

        @pytest.mark.parametrize("data", ACCEPTED)
        def test_passes_the_shapes(self, data):
            """passes the shapes

            The case is a statement written as the shapes allow, in Turtle; validated against the shapes, it draws no
            message.
            """
            assert shape_messages(data) == set()

        @pytest.mark.parametrize("data, message", REFUSED)
        def test_fails_the_shapes_with_a_message_that_says_how(self, data, message):
            """fails the shapes with a message that says how

            The case is a statement with one break; validated against the shapes, at least one message contains the words
            the case expects, so the break is refused for the reason it is meant to be.
            """
            found = shape_messages(data)
            assert any(message in m for m in found), found

    class TestGivenTheCodeVectors:
        @pytest.mark.parametrize("engine", sorted(ENGINES))
        def test_is_each_the_iri_that_its_stem_and_encode_for_uri_give(self, engine):
            """is, each, the IRI that its system's stem and `ENCODE_FOR_URI` of its literal give

            For each code vector that has a literal, the engine computes the stem of the vector's code system joined to the
            literal through `ENCODE_FOR_URI`; the result is compared with the IRI the vector states, on Oxigraph and on
            rdflib alike.
            """
            rows = [row for row in vector("code-iris.json") if row["literal"] is not None]
            assert rows
            assert {row["iri"]: evaluated(engine, row["system"], row["literal"]) for row in rows} == {
                row["iri"]: row["iri"] for row in rows}

        def test_has_for_a_clinvar_id_the_digits_of_what_was_written(self):
            """has for a ClinVar ID the digits of what was written, or nothing when that is no variation

            Each vector of the ClinVar system gives a written ID, such as `VCV000090011.3` or `90011`, and its literal.
            The literal is compared with the digits a pattern finds in the written ID, with no leading zero and no version,
            or with nothing when the written text is no variation ID.
            """
            offenders = []
            for row in vector("code-iris.json"):
                if row["system"] == "ClinVar":
                    match = re.fullmatch(r"(?:VCV0*)?([1-9][0-9]*)(?:\.[0-9]+)?", row["written"])
                    if (match.group(1) if match else None) != row["literal"]:
                        offenders.append(row["written"])
            assert offenders == []

    class TestGivenTheRowVector:
        def test_conforms_in_turtle_to_the_row_shape_of_variant_classifications(self):
            """conforms, in Turtle, to the row shape of variant classifications

            The vector's row in Turtle is validated against the row shape of the variant classifications kind; it draws no
            message.
            """
            assert row_messages(CASCADE.VariantClassifications, parsed(VECTORS / "row.ttl")) == set()

        def test_states_in_json_what_it_states_in_turtle(self):
            """states in JSON what it states in Turtle

            The vector's row in JSON is turned into statements, and they are compared with the statements of its row in
            Turtle; the two must be the same graph.
            """
            assert isomorphic(parsed(VECTORS / "row.ttl"), row_from_json(vector("row.json")))

        def test_names_its_series_by_a_urn_uuid(self):
            """names its series by a `urn:uuid:`

            The series the vector's JSON row names is compared with the form `urn:uuid:` and a UUID in lower-case
            hexadecimal.
            """
            assert re.fullmatch(r"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                                vector("row.json")["series"])

    class TestGivenClinvarsValuesAsWritten:
        """given ClinVar's values as written"""

        def test_parses_to_the_concepts_and_the_unmatched_words_its_vector_lists(self):
            """parses, split on `; ` and then `/`, to the concepts and the unmatched words its vector lists

            Each classification value as ClinVar writes it is split on `; ` and then on `/`, never on a comma, and each
            word is matched to a concept of `cascade:ClinVarClassifications` by its name. The concepts and the words that
            match none are compared with those the vector lists for the value.
            """
            classes = CASCADE.ClinVarClassifications
            offenders = [row["written"] for row in vector("values.json")["classifications"]
                         if parse_classification(row["written"], classes) != ({URIRef(c) for c in row["concepts"]},
                                                                               row["findings"])]
            assert offenders == []

        def test_names_only_concepts_of_the_classification_scheme(self):
            """names only concepts of `cascade:ClinVarClassifications`

            Each concept the vector lists for a classification value is compared with the concepts the vocabulary puts in
            `cascade:ClinVarClassifications`; one outside it fails.
            """
            members_of = set(members(CASCADE.ClinVarClassifications))
            offenders = [row["written"] for row in vector("values.json")["classifications"]
                         if not {URIRef(c) for c in row["concepts"]} <= members_of]
            assert offenders == []

        def test_is_for_a_review_status_the_one_concept_labelled_so(self):
            """is, for a review status, the one concept labelled so, or none

            Each review status as ClinVar writes it is matched to a concept of `cascade:ClinVarReviewStatuses` by its name;
            the concept found, or none when no name matches, is compared with the concept the vector lists.
            """
            labelled = {label: concept for concept, labels in members(CASCADE.ClinVarReviewStatuses).items()
                        for label in labels}
            offenders = [row["written"] for row in vector("values.json")["reviewStatuses"]
                         if labelled.get(row["written"]) != (URIRef(row["concept"]) if row["concept"] else None)]
            assert offenders == []

    class TestGivenTheFiveAcmgClasses:
        """given the five ACMG classes"""

        def test_is_a_concept_of_the_classification_scheme_each_of_the_five(self):
            """is a concept of `cascade:ClinVarClassifications`, each of the five

            The five classes of the ACMG, Pathogenic, Likely pathogenic, Uncertain significance, Likely benign and
            Benign, are compared with those of the five that the vocabulary puts in `cascade:ClinVarClassifications`; all
            five must be there.
            """
            assert {name for name in ACMG_FIVE
                    if (CASCADE[name], SKOS.inScheme, CASCADE.ClinVarClassifications) in terms()} == ACMG_FIVE

        def test_has_the_preferred_name_clinvar_spells_it_with(self):
            """has the preferred name ClinVar spells it with

            The `skos:prefLabel` of each of the five classes is compared with the words ClinVar writes it with, such as
            `Likely pathogenic`, which is what a ClinVar value is matched by.
            """
            spelled = {name: str(terms().value(CASCADE[name], SKOS.prefLabel)) for name in ACMG_FIVE}
            assert spelled == {"Pathogenic": "Pathogenic", "LikelyPathogenic": "Likely pathogenic",
                               "UncertainSignificance": "Uncertain significance", "LikelyBenign": "Likely benign",
                               "Benign": "Benign"}

    class TestGivenTheTwoClinvarSchemes:
        """given the two ClinVar schemes"""

        def test_holds_exactly_the_concepts_the_row_shape_lists_for_its_property(self):
            """holds exactly the concepts the row shape lists for its property

            For `cascade:clinvarClassification` and `cascade:clinvarReviewStatus`, the concepts that the row shape of
            variant classifications lists in its `sh:in` are compared with the concepts of the property's scheme; a concept
            the shape refuses, or lets through without a declaration, fails.
            """
            listed = {}
            for property_shape in shapes().objects(CASCADE.VariantClassificationRowShape, SH.property):
                path = shapes().value(property_shape, SH.path)
                if path in (CASCADE.clinvarClassification, CASCADE.clinvarReviewStatus):
                    listed[path] = set(Collection(shapes(), shapes().value(property_shape, SH["in"])))
            assert listed == {CASCADE.clinvarClassification: set(members(CASCADE.ClinVarClassifications)),
                              CASCADE.clinvarReviewStatus: set(members(CASCADE.ClinVarReviewStatuses))}

        def test_shares_two_concepts_with_the_other_each_one_iri_in_both(self):
            """shares two concepts with the other, each one IRI in both

            The concepts of the classification scheme that are also concepts of the review status scheme are compared with
            the two that stand for "no classification": each has one IRI, which both schemes use.
            """
            assert set(members(CASCADE.ClinVarClassifications)) & set(members(CASCADE.ClinVarReviewStatuses)) == {
                CASCADE.ClinVarNoClassificationsFromUnflaggedRecords, CASCADE.ClinVarNoClassificationForTheSingleVariant}
