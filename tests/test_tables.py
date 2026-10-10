"""Every table row conforms to its kind's shape and is named by N11, the shapes refuse broken rows, and a table version is
named by N12 (runtime/naming.feature)."""

import base64
import hashlib
import json
import re
from functools import cache

import pytest
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH, SKOS, XSD

from contract import QUERIES, REC, ROOT
from engines import parsed
from test_naming import record_name

PROV = Namespace("http://www.w3.org/ns/prov#")
VOID = Namespace("http://rdfs.org/ns/void#")
VERSIONS = ROOT / "tests" / "table-versions"
FOLDERS = sorted(index.parent for top in ("runtime", "conformance") for index in (ROOT / top).rglob("references.ttl"))
PREFIXES = """
@prefix dct: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix semapv: <https://w3id.org/semapv/vocab/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sssom: <https://w3id.org/sssom/> .
@prefix cvx: <http://hl7.org/fhir/sid/cvx/> .
@prefix rxnorm: <http://www.nlm.nih.gov/research/umls/rxnorm/> .
@prefix icd: <http://hl7.org/fhir/sid/icd-10-cm/> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
"""
ROW = "a owl:Axiom ; owl:annotatedSource cvx:141 ; owl:annotatedProperty skos:broadMatch ; owl:annotatedTarget cvx:88"
CURATED = "sssom:mapping_justification semapv:ManualMappingCuration"
CHAINED = "sssom:mapping_justification semapv:MappingChaining"
NDC = "<https://ns.cascadeprotocol.org/codes/ndc11/00069153066>"
EARLIER = "a owl:Axiom ; owl:annotatedSource icd:C88.0 ; owl:annotatedProperty skos:exactMatch ; owl:annotatedTarget icd:C88.00"
CARDINALITY = 'sssom:mapping_cardinality "1:1"'
CONVERSION = EARLIER.replace("skos:exactMatch", "dct:isReplacedBy") + f" ; {CARDINALITY}"
DRUG = "a owl:Axiom ; owl:annotatedSource rxnorm:153010 ; owl:annotatedProperty skos:broadMatch ; owl:annotatedTarget rxnorm:5640"


@cache
def shapes():
    return Graph().parse(ROOT / "ontologies" / "records" / "v1-draft" / "records.shapes.ttl")


@cache
def kinds():
    return Graph().parse(ROOT / "ontologies" / "records" / "v1-draft" / "records.ttl")


def messages(kind, rows):
    """The messages the kind's row shape gives about the rows, every subject of them a focus node."""
    shape = kinds().value(kind, REC.rowShape)
    targeted = Graph() + shapes()
    for subject in set(rows.subjects()):
        targeted.add((shape, SH.targetNode, subject))
    _, report, _ = validate(rows, shacl_graph=targeted)
    return {str(message) for message in report.objects(None, SH.resultMessage)}


def versions():
    """Each table version of every kit and vector: its folder, its file, its kind and its rows."""
    for folder in FOLDERS:
        index = parsed(folder / "references.ttl")
        for version, series in index.subject_objects(PROV.specializationOf):
            kind = index.value(series, REC.tableKind)
            if kind is not None:
                stem = str(version).removeprefix("urn:uuid:")
                yield folder, stem, kind, parsed(folder / f"{stem}.ttl")


def test_a_story_folder_leaves_the_vocabularys_rule_list_to_it_and_every_version_it_lists_has_a_file_in_one_place():
    shared = ROOT / "runtime" / "rule-list"
    repeated, missing = [], []
    for folder in sorted(set(FOLDERS) - {shared}):
        index = parsed(folder / "references.ttl")
        for version, series in index.subject_objects(PROV.specializationOf):
            name = f"{str(version).removeprefix('urn:uuid:')}.ttl"
            own = folder / name
            if own.is_file() and (shared / name).is_file() and own.read_bytes() == (shared / name).read_bytes():
                repeated.append(own.relative_to(ROOT).as_posix())
            open_names_it = folder.parent.name == "tables"
            if not own.is_file() and not (open_names_it and index.value(series, REC.tableKind) is None and (shared / name).is_file()):
                missing.append(own.relative_to(ROOT).as_posix())
    assert repeated == [] and missing == []


def test_every_kind_names_one_row_shape_and_what_its_rows_are_found_by():
    declared = set(kinds().subjects(RDF.type, REC.TableKind))
    series_kind = next(p for p in shapes().objects(REC.ReferenceSeriesShape, SH.property)
                       if shapes().value(p, SH.path) == REC.tableKind)
    assert declared and set(Collection(shapes(), shapes().value(series_kind, SH["in"]))) == declared
    assert {kind for kind in declared if len(set(kinds().objects(kind, REC.rowShape))) != 1
            or not set(kinds().objects(kind, REC.foundBy))} == set()


STEM = re.compile(r"https?://(?:snomed\.info|loinc\.org|www\.nlm\.nih\.gov|hl7\.org/fhir/sid|fdasis\.nlm\.nih\.gov"
                  r"|www\.ama-assn\.org/go|ns\.cascadeprotocol\.org/codes)/[A-Za-z0-9._/-]*/")


def test_every_iri_stem_a_query_or_an_ontology_writes_is_a_code_systems_uri_space():
    registered = {str(space) for space in kinds().objects(None, VOID.uriSpace)}
    system_uris = [f"<{uri}>" for uri in kinds().objects(None, SKOS.exactMatch)]
    written = {}
    for path in [*sorted(QUERIES.parent.rglob("*.rq")), *sorted((ROOT / "ontologies").rglob("*.ttl"))]:
        text = path.read_text(encoding="utf-8").replace("\\\\.", ".")
        for uri in system_uris:
            text = text.replace(uri, "")
        if stray := sorted(set(STEM.findall(text)) - registered):
            written[path.relative_to(ROOT).as_posix()] = stray
    assert written == {}


def test_every_code_system_has_one_iri_stem_ending_in_a_slash_and_one_system_uri_without():
    systems = set(kinds().subjects(RDF.type, REC.CodeSystem))
    assert {system.removeprefix(str(REC)) for system in systems} == {
        "CVX", "RxNorm", "NDC", "ICD10CM", "SNOMEDCT", "LOINC", "UNII", "CPT", "ICD9CM"}
    for system in systems:
        stems, uris = list(kinds().objects(system, VOID.uriSpace)), list(kinds().objects(system, SKOS.exactMatch))
        assert len(stems) == 1 and str(stems[0]).endswith("/"), system
        assert len(uris) == 1 and isinstance(uris[0], URIRef) and not str(uris[0]).endswith("/"), system


def test_every_row_of_every_kit_and_vector_conforms_to_its_kind_and_every_mapping_row_is_named_by_n11():
    found, broken, misnamed = 0, {}, set()
    for folder, stem, kind, rows in versions():
        found += 1
        if said := messages(kind, rows):
            broken[f"{folder.relative_to(ROOT).as_posix()}/{stem}"] = said
        for row in rows.subjects(RDF.type, OWL.Axiom):
            inputs = [str(rows.value(row, p)) for p in (OWL.annotatedSource, OWL.annotatedProperty, OWL.annotatedTarget)]
            if str(row) != record_name(inputs):
                misnamed.add(str(row))
    assert found == 35
    assert broken == {}
    assert misnamed == set()


@pytest.mark.parametrize("kind, rows, message", [
    (REC.VaccineGroups, f"<urn:x:r> {ROW} ; {CURATED} .", None),
    (REC.VaccineGroups, f"[] {ROW} ; {CURATED} .", "A mapping row is an owl:Axiom named by an IRI"),
    (REC.VaccineGroups, f"<urn:x:r> {ROW}, cvx:89 ; {CURATED} .", "A mapping row maps to one object code"),
    (REC.VaccineGroups, f"<urn:x:r> {ROW} ; {CURATED} ; skos:note \"x\" .", "A mapping row is an owl:Axiom named by an IRI"),
    (REC.VaccineGroups, f"<urn:x:r> {ROW.replace('broadMatch', 'exactMatch')} ; {CURATED} .", "with skos:broadMatch"),
    (REC.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', 'rxnorm:7980')} ; {CURATED} .", "maps a CVX code"),
    (REC.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', '<http://hl7.org/fhir/sid/cvx/8>')} ; {CURATED} .",
     "maps a CVX code"),
    (REC.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', 'cvx:88')} ; {CURATED} .", None),
    (REC.VaccineGroups, f"<urn:x:r> {ROW} ; sssom:mapping_justification semapv:LexicalMatching .", "justified as"),
    (REC.CodeNames, 'cvx:141 skos:prefLabel "Influenza" ; skos:altLabel "Flu" ; skos:notation "141" .', None),
    (REC.CodeNames, 'cvx:141 skos:prefLabel "Influenza", "Flu" ; skos:notation "141" .', "one preferred name"),
    (REC.CodeNames, 'cvx:99 skos:prefLabel "RESERVED" ; skos:altLabel "RESERVED" ; skos:notation "99" .',
     "none its preferred name"),
    (REC.CodeNames, 'cvx:141 skos:prefLabel "Influenza"@en ; skos:notation "141" .', "one preferred name"),
    (REC.CodeNames, '<urn:x:141> skos:prefLabel "Influenza" ; skos:notation "141" .', "one of the code systems' forms"),
    (REC.CodeNames, '<http://hl7.org/fhir/sid/cvx/8> skos:prefLabel "x" ; skos:notation "8" .', "one of the code systems' forms"),
    (REC.CodeNames, '<https://ns.cascadeprotocol.org/codes/ndc11/00002143380> skos:prefLabel "x" ; skos:notation "0002-1433-80" .', None),
    (REC.CodeNames, '<http://hl7.org/fhir/sid/ndc/00002143380> skos:prefLabel "x" ; skos:notation "0002-1433-80" .',
     "one of the code systems' forms"),
    (REC.CodeNames, '<https://ns.cascadeprotocol.org/codes/ndc11/0002-1433-80> skos:prefLabel "x" ; skos:notation "0002-1433-80" .',
     "one of the code systems' forms"),
    (REC.CodeNames, '<http://hl7.org/fhir/sid/icd-10-cm/E11.9> skos:prefLabel "x" ; skos:notation "E11.9" .', None),
    (REC.CodeNames, '<http://hl7.org/fhir/sid/icd-10-cm/S72.001A> skos:prefLabel "x" ; skos:notation "S72.001A" .', None),
    (REC.CodeNames, '<http://hl7.org/fhir/sid/icd-10-cm/QA0.0> skos:prefLabel "x" ; skos:notation "QA0.0" .', None),
    (REC.CodeNames, '<http://hl7.org/fhir/sid/icd-10-cm/E119> skos:prefLabel "x" ; skos:notation "E11.9" .',
     "one of the code systems' forms"),
    (REC.CodeNames, 'rxnorm:RX7980 skos:prefLabel "x" ; skos:notation "7980" .', "one of the code systems' forms"),
    (REC.CodeNames, '<http://snomed.info/id/91936005> skos:prefLabel "x" ; skos:notation "91936005" .', None),
    (REC.CodeNames, '<http://snomed.info/sct/91936005> skos:prefLabel "x" ; skos:notation "91936005" .',
     "one of the code systems' forms"),
    (REC.CodeNames, '<http://snomed.info/id/x91936005> skos:prefLabel "x" ; skos:notation "91936005" .',
     "one of the code systems' forms"),
    (REC.CodeNames, '<http://loinc.org/rdf/2823-3> skos:prefLabel "x" ; skos:notation "2823-3" .', None),
    (REC.CodeNames, '<http://loinc.org/rdf/28233> skos:prefLabel "x" ; skos:notation "2823-3" .',
     "one of the code systems' forms"),
    (REC.ProductIngredients, f"<urn:x:r> {DRUG} ; {CHAINED} .", None),
    (REC.ProductIngredients, f"<urn:x:r> {DRUG.replace('rxnorm:153010', 'cvx:141')} ; {CHAINED} .",
     "A product ingredient row maps an RxNorm code"),
    (REC.ProductIngredients, f"<urn:x:r> {DRUG.replace('broadMatch', 'exactMatch')} ; {CHAINED} .",
     "with skos:broadMatch"),
    (REC.BrandGenerics, f"<urn:x:r> {DRUG} ; {CURATED} .", None),
    (REC.BrandGenerics, f"<urn:x:r> {DRUG.replace('rxnorm:5640', '<http://snomed.info/id/387207008>')} ; {CURATED} .",
     "A brand generic row maps to an RxNorm code"),
    (REC.NdcDrugs, f"<urn:x:r> {DRUG.replace('rxnorm:153010', NDC)} ; {CURATED} .", None),
    (REC.NdcDrugs, f"<urn:x:r> {DRUG.replace('rxnorm:153010', NDC.replace('/000', '/00'))} ; {CURATED} .",
     "An NDC drug row maps an NDC of 11 digits"),
    (REC.NdcDrugs, f"<urn:x:r> {DRUG.replace('rxnorm:153010', NDC).replace('broadMatch', 'closeMatch')} ; {CURATED} .",
     "with skos:broadMatch"),
    (REC.CodeConversions, f"<urn:x:r> {CONVERSION} ; {CURATED} .", None),
    (REC.CodeConversions, f"<urn:x:r> {EARLIER} ; {CURATED} .", None),
    (REC.CodeConversions, f"<urn:x:r> {EARLIER} ; {CARDINALITY} ; {CURATED} .", "with dct:isReplacedBy"),
    (REC.CodeConversions, f"<urn:x:r> {EARLIER.replace('exactMatch', 'narrowMatch')} ; {CURATED} .",
     "with dct:isReplacedBy"),
    (REC.CodeConversions, f"<urn:x:r> {EARLIER.replace('skos:exactMatch', 'dct:isReplacedBy')} ; {CURATED} .",
     "gives its cardinality"),
    (REC.CodeConversions, f"<urn:x:r> {CONVERSION.replace('1:1', '1:2')} ; {CURATED} .",
     "one of 1:1, 1:n, n:1 or n:n"),
    (REC.VaccineGroups, f'<urn:x:r> {ROW} ; sssom:mapping_cardinality "n:1" ; {CURATED} .', None),
    (REC.CodeConversions, f"<urn:x:r> {CONVERSION.replace('icd:C88.0 ', '<http://hl7.org/fhir/sid/icd-10-cm/C880> ')} ; {CURATED} .",
     "A code conversion row maps a code"),
    (REC.CodeStatus, "cvx:141 owl:deprecated true ; dct:isReplacedBy cvx:150 .", None),
    (REC.CodeStatus, "cvx:141 owl:deprecated false .", "owl:deprecated true"),
    (REC.DrugProducts, 'rxnorm:197361 rec:termType "SCD" .', None),
    (REC.DrugProducts, 'rxnorm:370573 rec:termType "SCDF" .', "one of SCD, SBD, GPCK or BPCK"),
    (REC.DrugProducts, 'cvx:141 rec:termType "SCD" .', "holds only the code's term type"),
    (REC.DrugProducts, 'rxnorm:197361 rec:termType "SCD" ; skos:prefLabel "x" .', "holds only the code's term type"),
    (REC.DrugProducts, 'rxnorm:197361 rec:termType "SCD", "SBD" .', "one of SCD, SBD, GPCK or BPCK"),
])
def test_the_row_shapes_accept_a_row_of_each_kind_and_refuse_each_break_with_its_message(kind, rows, message):
    said = messages(kind, Graph().parse(data=PREFIXES + rows, format="turtle"))
    assert (said == set()) if message is None else any(message in m for m in said), said


@pytest.mark.parametrize("rows, message", [
    (f"<urn:x:r> {CONVERSION} ; sssom:mapping_justification semapv:LexicalMatching .", "justified as"),
    (f"<urn:x:r> {CONVERSION.replace('1:1', '1:2')} ; {CURATED} .", "one of 1:1, 1:n, n:1 or n:n"),
    (f"<urn:x:r> {CONVERSION} ; {CURATED} ; skos:note \"x\" .", "A mapping row is an owl:Axiom named by an IRI"),
])
def test_a_conversion_row_broken_otherwise_does_not_also_say_its_form_is_wrong(rows, message):
    said = messages(REC.CodeConversions, Graph().parse(data=PREFIXES + rows, format="turtle"))
    assert any(message in m for m in said), said
    assert not any("with dct:isReplacedBy" in m for m in said), said


ESCAPES = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def canonical(term):
    """A term in canonical N-Triples, as RDFC-1.0 writes it for a graph with no blank node."""
    if isinstance(term, BNode):
        raise ValueError("N12 names no version whose rows hold a blank node")
    if isinstance(term, URIRef):
        return f"<{term}>"
    escaped = "".join(ESCAPES.get(c) or (f"\\u{ord(c):04X}" if c < " " or c == "\x7f" else c) for c in str(term))
    if term.language:
        return f'"{escaped}"@{term.language}'
    if term.datatype is not None and term.datatype != XSD.string:
        return f'"{escaped}"^^<{term.datatype}>'
    return f'"{escaped}"'


def test_canonical_escapes_a_literal_as_rdfc_writes_it_and_refuses_a_blank_node():
    assert canonical(Literal('a"\\\b\t\n\f\r\x01\x7fé')) == r'"a\"\\\b\t\n\f\r\u0001\u007Fé"'
    with pytest.raises(ValueError, match="blank node"):
        canonical(BNode())


def version_name(triples):
    lines = sorted(" ".join(map(canonical, triple)) + " .\n" for triple in triples)
    digest = hashlib.sha256("".join(lines).encode()).digest()
    return "ni:///sha-256;" + base64.urlsafe_b64encode(digest).decode().rstrip("=")


def test_each_table_version_is_named_by_n12_from_its_series_the_version_it_revises_and_its_rows():
    this = URIRef("urn:cascade:this-version")
    cases = json.loads((VERSIONS / "cases.json").read_text(encoding="utf-8"))
    named = []
    for case in cases:
        triples = {(this, PROV.specializationOf, URIRef(case["series"]))}
        if case["revises"]:
            triples.add((this, PROV.wasRevisionOf, URIRef(case["revises"])))
        if case["rows"]:
            rows = parsed(VERSIONS / case["rows"])
            assert messages(REC[case["kind"]], rows) == set(), case["rows"]
            triples |= set(rows)
        named.append(version_name(triples))
    assert named == [case["name"] for case in cases]
    assert len(set(named)) == len(cases)
