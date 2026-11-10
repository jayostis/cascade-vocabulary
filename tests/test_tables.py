import json
import re
from functools import cache

import pytest
from rdflib import Dataset, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH, XSD

from contract import QUERIES, CASCADE, ROOT, file_stem
from engines import parsed
from naming import content, table_row_name, table_version_name
from ontologies import row_messages, shapes, terms

PROV = Namespace("http://www.w3.org/ns/prov#")
VOID = Namespace("http://rdfs.org/ns/void#")
VERSIONS = ROOT / "tests" / "table-versions"
FOLDERS = sorted(index.parent for top in ("runtime", "conformance") for index in (ROOT / top).rglob("references.ttl"))
PREFIXES = """
@prefix dct: <http://purl.org/dc/terms/> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix semapv: <https://w3id.org/semapv/vocab/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sssom: <https://w3id.org/sssom/> .
@prefix cvx: <https://ns.cascadeprotocol.org/codes/cvx/> .
@prefix rxnorm: <https://ns.cascadeprotocol.org/codes/rxnorm/> .
@prefix icd: <https://ns.cascadeprotocol.org/codes/icd10cm/> .
@prefix cascade: <https://ns.cascadeprotocol.org/cascade#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""
VARIATION = "<https://identifiers.org/clinvar:90011>"
EXPRESSION = "<https://ns.cascadeprotocol.org/codes/hgvs/NM_000249.3%3Ac.2042C%3ET>"
CLASSIFIED = (f"{VARIATION} cascade:hgvsExpression {EXPRESSION} ; cascade:clinvarClassification cascade:Pathogenic , "
              'cascade:LikelyPathogenic ; cascade:clinvarReviewStatus cascade:ClinVarMultipleSubmittersNoConflicts ; '
              'cascade:lastEvaluated "2024-12-11"^^xsd:date ; cascade:contributingSubmitterCount 5')
ROW = "a owl:Axiom ; owl:annotatedSource cvx:141 ; owl:annotatedProperty obo:RO_0002350 ; owl:annotatedTarget cvx:88"
CURATED = "sssom:mapping_justification semapv:ManualMappingCuration"
CHAINED = "sssom:mapping_justification semapv:MappingChaining"
EARLIER = "a owl:Axiom ; owl:annotatedSource icd:C88.0 ; owl:annotatedProperty skos:exactMatch ; owl:annotatedTarget icd:C88.00"
CARDINALITY = 'sssom:mapping_cardinality "1:1"'
CONVERSION = EARLIER.replace("skos:exactMatch", "dct:isReplacedBy") + f" ; {CARDINALITY}"
DRUG = "a owl:Axiom ; owl:annotatedSource rxnorm:153010 ; owl:annotatedProperty skos:broadMatch ; owl:annotatedTarget rxnorm:5640"
INGREDIENT = DRUG.replace("skos:broadMatch", "obo:RO_0002248")
PANEL = ("a owl:Axiom ; owl:annotatedSource <http://loinc.org/rdf/24318-8> ; owl:annotatedProperty obo:RO_0002351 ; "
         "owl:annotatedTarget <http://loinc.org/rdf/30395-8> ; cascade:panelSequence 4")
CLASSIFIED_DRUG = ("a owl:Axiom ; owl:annotatedSource rxnorm:5640 ; owl:annotatedProperty cascade:establishedPharmacologicClass ; "
                   "owl:annotatedTarget <https://ns.cascadeprotocol.org/codes/medrt/N0000175722>")
MESH = "<http://id.nlm.nih.gov/mesh/M0006414>"
DIABETES = "<http://cts.nlm.nih.gov/fhir/ValueSet/2.16.840.1.113883.3.464.1003.103.12.1001>"
MEMBER = f"a owl:Axiom ; owl:annotatedSource <http://snomed.info/id/1481000119100> ; owl:annotatedProperty obo:RO_0002350 ; owl:annotatedTarget {DIABETES}"
SIXTEEN = {"CVX", "RxNorm", "NDC", "ICD10CM", "SNOMEDCT", "LOINC", "UNII", "CPT", "ICD9CM", "HGVS", "ClinVar", "MEDRT",
           "MeSH", "DataAbsentReason", "NullFlavor", "ObservationInterpretation"}
PAGES = {"ClinVar": ("90011", "https://www.ncbi.nlm.nih.gov/clinvar/variation/90011/"),
         "LOINC": ("2345-7", "https://loinc.org/2345-7"),
         "MeSH": ("M0006414", "https://id.nlm.nih.gov/mesh/M0006414.html")}
STEM = re.compile(r"https?://(?:snomed\.info|loinc\.org|id\.nlm\.nih\.gov|ns\.cascadeprotocol\.org/codes)/[A-Za-z0-9._/-]*/"
                  r"|https://identifiers\.org/[a-z]+:")
PUBLISHED_BEFORE_RO = ROOT / "runtime" / "scripted-input" / "hana" / "tables"
SHARED = ROOT / "runtime" / "rule-list"
CASES = json.loads((VERSIONS / "cases.json").read_text(encoding="utf-8"))


def held_messages(folder, kind, rows):
    """The messages of the kind's row shape that a table version in the folder is held to."""
    said = row_messages(kind, rows)
    if folder.parent == PUBLISHED_BEFORE_RO and kind in (CASCADE.ProductIngredients, CASCADE.VaccineGroups):
        return {m for m in said if not any(relation in m for relation in ("with obo:RO_0002350", "with obo:RO_0002248"))}
    return said


@cache
def table_versions():
    """Each table version of every kit and vector: its folder, its file stem, its kind and its rows."""
    found = []
    for folder in FOLDERS:
        index = parsed(folder / "references.ttl")
        for version, series in index.subject_objects(PROV.specializationOf):
            kind = index.value(series, CASCADE.tableKind)
            if kind is not None:
                stem = file_stem(str(version))
                found.append((folder, stem, kind, parsed(folder / f"{stem}.ttl")))
    return tuple(found)


def table_kinds():
    return set(terms().subjects(RDF.type, CASCADE.TableKind))


def name_inputs(rows, row):
    """N11's inputs for a row: its source, property and target, and a panel member's sequence."""
    inputs = [str(rows.value(row, p)) for p in (OWL.annotatedSource, OWL.annotatedProperty, OWL.annotatedTarget)]
    sequence = rows.value(row, CASCADE.panelSequence)
    return inputs if sequence is None else [*inputs, str(sequence)]


def listed_versions():
    """Each version that the `references.ttl` of a folder of tables lists, other than the rule list's own folder: the
    folder, the file it would be held in, the file of that name in the rule list, and its series' kind."""
    for folder in sorted(set(FOLDERS) - {SHARED}):
        index = parsed(folder / "references.ttl")
        for version, series in index.subject_objects(PROV.specializationOf):
            name = f"{file_stem(str(version))}.ttl"
            yield folder, folder / name, SHARED / name, index.value(series, CASCADE.tableKind)


def panel_member_names(rows):
    """Each panel and member a row states, with the names of the rows that state it."""
    named = {}
    for row in rows.subjects(RDF.type, OWL.Axiom):
        named.setdefault((rows.value(row, OWL.annotatedSource), rows.value(row, OWL.annotatedTarget)), set()).add(row)
    return named


def case_version_name(case):
    rows = content((VERSIONS / case["rows"]).read_text(encoding="utf-8"), "turtle") if case["rows"] else set()
    return table_version_name(case["series"], case["revises"] or None, rows)


ROWS = [
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW} ; {CURATED} .", None, id="vaccine groups: a whole row"),
    pytest.param(CASCADE.VaccineGroups, f"[] {ROW} ; {CURATED} .", "A mapping row is an owl:Axiom named by an IRI",
     id="vaccine groups: a row named by a blank node"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW}, cvx:89 ; {CURATED} .", "A mapping row maps to one object code",
     id="vaccine groups: two targets"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW} ; {CURATED} ; skos:note \"x\" .", "A mapping row is an owl:Axiom named by an IRI",
     id="vaccine groups: a property a mapping row may not hold"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('obo:RO_0002350', 'skos:broadMatch')} ; {CURATED} .", "with obo:RO_0002350",
     id="vaccine groups: a broader-match property"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', 'rxnorm:7980')} ; {CURATED} .", "maps a CVX code",
     id="vaccine groups: an RxNorm source"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', '<https://ns.cascadeprotocol.org/codes/cvx/8>')} ; {CURATED} .",
     "maps a CVX code", id="vaccine groups: a CVX code of one digit"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', 'cvx:88')} ; {CURATED} .", None,
     id="vaccine groups: a group that is its own member"),
    pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW} ; sssom:mapping_justification semapv:LexicalMatching .", "justified as",
     id="vaccine groups: a lexical-match justification"),
    pytest.param(CASCADE.CodeNames, 'cvx:141 skos:prefLabel "Influenza" ; skos:altLabel "Flu" ; skos:notation "141" .', None,
     id="code names: a preferred and an alternative name"),
    pytest.param(CASCADE.CodeNames, 'cvx:141 skos:prefLabel "Influenza", "Flu" ; skos:notation "141" .', "one preferred name",
     id="code names: two preferred names"),
    pytest.param(CASCADE.CodeNames, 'cvx:99 skos:prefLabel "RESERVED" ; skos:altLabel "RESERVED" ; skos:notation "99" .',
     "none its preferred name", id="code names: an alternative name that is the preferred one"),
    pytest.param(CASCADE.CodeNames, 'cvx:141 skos:prefLabel "Influenza"@en ; skos:notation "141" .', "one preferred name",
     id="code names: a name with a language"),
    pytest.param(CASCADE.CodeNames, '<urn:x:141> skos:prefLabel "Influenza" ; skos:notation "141" .', "one of the code systems' forms",
     id="code names: a urn in place of a code IRI"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/cvx/8> skos:prefLabel "x" ; skos:notation "8" .', "one of the code systems' forms",
     id="code names: a CVX code of one digit"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/ndc11/00002143380> skos:prefLabel "x" ; skos:notation "0002-1433-80" .', None,
     id="code names: an eleven-digit NDC code"),
    pytest.param(CASCADE.CodeNames, '<http://hl7.org/fhir/sid/ndc/00002143380> skos:prefLabel "x" ; skos:notation "0002-1433-80" .',
     "one of the code systems' forms", id="code names: an NDC code in the FHIR system's form"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/ndc11/0002-1433-80> skos:prefLabel "x" ; skos:notation "0002-1433-80" .',
     "one of the code systems' forms", id="code names: an NDC code with hyphens"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/E11.9> skos:prefLabel "x" ; skos:notation "E11.9" .', None,
     id="code names: an ICD-10-CM code with a point"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/S72.001A> skos:prefLabel "x" ; skos:notation "S72.001A" .', None,
     id="code names: an ICD-10-CM code with a seventh character"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/QA0.0> skos:prefLabel "x" ; skos:notation "QA0.0" .', None,
     id="code names: an ICD-10-CM code that begins with two letters"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/E119> skos:prefLabel "x" ; skos:notation "E11.9" .',
     "one of the code systems' forms", id="code names: an ICD-10-CM code with no point"),
    pytest.param(CASCADE.CodeNames, 'rxnorm:RX7980 skos:prefLabel "x" ; skos:notation "7980" .', "one of the code systems' forms",
     id="code names: an RxNorm code with a prefix"),
    pytest.param(CASCADE.CodeNames, '<http://snomed.info/id/91936005> skos:prefLabel "x" ; skos:notation "91936005" .', None,
     id="code names: a SNOMED CT code"),
    pytest.param(CASCADE.CodeNames, '<http://snomed.info/sct/91936005> skos:prefLabel "x" ; skos:notation "91936005" .',
     "one of the code systems' forms", id="code names: a SNOMED CT code under sct"),
    pytest.param(CASCADE.CodeNames, '<http://snomed.info/id/x91936005> skos:prefLabel "x" ; skos:notation "91936005" .',
     "one of the code systems' forms", id="code names: a SNOMED CT code with a letter"),
    pytest.param(CASCADE.CodeNames, '<http://loinc.org/rdf/2823-3> skos:prefLabel "x" ; skos:notation "2823-3" .', None,
     id="code names: a LOINC code"),
    pytest.param(CASCADE.CodeNames, '<http://loinc.org/rdf/28233> skos:prefLabel "x" ; skos:notation "2823-3" .',
     "one of the code systems' forms", id="code names: a LOINC code with no hyphen"),
    pytest.param(CASCADE.ProductIngredients, f"<urn:x:r> {INGREDIENT} ; {CHAINED} .", None,
     id="product ingredients: a whole row"),
    pytest.param(CASCADE.ProductIngredients, f"<urn:x:r> {INGREDIENT.replace('rxnorm:153010', 'cvx:141')} ; {CHAINED} .",
     "A product ingredient row maps an RxNorm code", id="product ingredients: a CVX source"),
    pytest.param(CASCADE.ProductIngredients, f"<urn:x:r> {INGREDIENT.replace('obo:RO_0002248', 'cascade:hasPreciseIngredient')} ; {CHAINED} .", None,
     id="product ingredients: a precise-ingredient property"),
    pytest.param(CASCADE.ProductIngredients, f"<urn:x:r> {DRUG} ; {CHAINED} .", "with obo:RO_0002248",
     id="product ingredients: a broader-match property"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL} ; {CURATED} .", None, id="panel members: a whole row"),
    pytest.param(CASCADE.PanelMembers, f'<urn:x:r> {PANEL} ; {CURATED} ; cascade:observationRequiredInPanel "Rflx-a" .', None,
     id="panel members: a row with a requirement"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('; cascade:panelSequence 4', '')} ; {CURATED} .", "one sequence",
     id="panel members: no sequence"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('Sequence 4', 'Sequence \"4\"')} ; {CURATED} .", "one sequence",
     id="panel members: a sequence written as text"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL} ; {CURATED} ; cascade:observationRequiredInPanel \"R\", \"O\" .", "at most one requirement",
     id="panel members: two requirements"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('30395-8', 'XYZ')} ; {CURATED} .", "one member, a LOINC code",
     id="panel members: a member that is no LOINC code"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('24318-8', '24318')} ; {CURATED} .", "one panel, a LOINC code",
     id="panel members: a panel that is no LOINC code"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('RO_0002351', 'RO_0002350')} ; {CURATED} .", "with obo:RO_0002351",
     id="panel members: the property of a vaccine group"),
    pytest.param(CASCADE.PanelMembers, f"<urn:x:r> {PANEL} ; {CURATED} ; sssom:mapping_cardinality \"1:1\" .", "holding only its panel",
     id="panel members: a cardinality it may not hold"),
    pytest.param(CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG} ; {CURATED} .", None,
     id="drug classes: a whole row"),
    pytest.param(CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('establishedPharmacologicClass', 'chemicalStructureClass').replace('<https://ns.cascadeprotocol.org/codes/medrt/N0000175722>', MESH)} ; {CURATED} .", None,
     id="drug classes: a chemical structure class that is a MeSH code"),
    pytest.param(CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('<https://ns.cascadeprotocol.org/codes/medrt/N0000175722>', MESH)} ; {CURATED} .",
     "or, with cascade:chemicalStructureClass, to a MeSH code",
     id="drug classes: an established class that is a MeSH code"),
    pytest.param(CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('rxnorm:5640', 'cvx:141')} ; {CURATED} .", "maps an RxNorm code",
     id="drug classes: a CVX source"),
    pytest.param(CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('cascade:establishedPharmacologicClass', 'skos:broadMatch')} ; {CURATED} .",
     "with cascade:establishedPharmacologicClass, cascade:mechanismOfActionClass",
     id="drug classes: a broader-match property"),
    pytest.param(CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG} ; {CHAINED} .", "justified as the publisher's curated row",
     id="drug classes: a justification that is not curation"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER} ; {CURATED} .", None,
     id="value-set expansions: a whole row"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('<http://snomed.info/id/1481000119100>', '<urn:x:G0108>')} ; {CURATED} .",
     "maps a code, an IRI of one of the code systems' forms", id="value-set expansions: a member that is no code IRI"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('1001>', '1001#20220924>')} ; {CURATED} .", "named by its canonical URL",
     id="value-set expansions: a value set named with a version after a hash"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace(DIABETES, '<urn:oid:2.16.840.1.113883.3.464.1003.103.12.1001>')} ; {CURATED} .",
     "Cascade's rule, one value set one name", id="value-set expansions: a value set named by an OID"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('1001>', '1001|20220924>')} ; {CURATED} .", "named by its canonical URL",
     id="value-set expansions: a value set named with a version after a bar"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('obo:RO_0002350', 'skos:exactMatch')} ; {CURATED} .", "with obo:RO_0002350",
     id="value-set expansions: an exact-match property"),
    pytest.param(CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER} ; {CHAINED} .", "justified as a manually curated mapping",
     id="value-set expansions: a justification that is not manual curation"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/medrt/N0000175722> skos:prefLabel "Beta-Adrenergic Blocker [EPC]" ; skos:notation "N0000175722" .', None,
     id="code names: a MED-RT code"),
    pytest.param(CASCADE.CodeNames, f'{MESH} skos:prefLabel "Ibuprofen" ; skos:notation "M0006414" .', None,
     id="code names: a MeSH code beginning with M"),
    pytest.param(CASCADE.CodeNames, '<http://id.nlm.nih.gov/mesh/D004095> skos:prefLabel "x" ; skos:notation "D004095" .', None,
     id="code names: a MeSH code beginning with D"),
    pytest.param(CASCADE.CodeNames, '<http://id.nlm.nih.gov/mesh/X1> skos:prefLabel "x" ; skos:notation "X1" .', "one of the code systems' forms",
     id="code names: a MeSH code beginning with X"),
    pytest.param(CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/medrt/N000017572> skos:prefLabel "x" ; skos:notation "N000017572" .',
     "one of the code systems' forms", id="code names: a MED-RT code of nine digits"),
    pytest.param(CASCADE.BrandGenerics, f"<urn:x:r> {DRUG} ; {CURATED} .", None, id="brand generics: a whole row"),
    pytest.param(CASCADE.BrandGenerics, f"<urn:x:r> {DRUG.replace('rxnorm:5640', '<http://snomed.info/id/387207008>')} ; {CURATED} .",
     "A brand generic row maps to an RxNorm code", id="brand generics: a target that is no RxNorm code"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {CONVERSION} ; {CURATED} .", None,
     id="code conversions: a replacement with its cardinality"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {EARLIER} ; {CURATED} .", None,
     id="code conversions: an exact match"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {EARLIER} ; {CARDINALITY} ; {CURATED} .", "with dct:isReplacedBy",
     id="code conversions: an exact match that gives a cardinality"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {EARLIER.replace('exactMatch', 'narrowMatch')} ; {CURATED} .",
     "with dct:isReplacedBy", id="code conversions: a narrow match"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {EARLIER.replace('skos:exactMatch', 'dct:isReplacedBy')} ; {CURATED} .",
     "gives its cardinality", id="code conversions: a replacement with no cardinality"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {CONVERSION.replace('1:1', '1:2')} ; {CURATED} .",
     "one of 1:1, 1:n, n:1 or n:n", id="code conversions: a cardinality of 1:2"),
    pytest.param(CASCADE.VaccineGroups, f'<urn:x:r> {ROW} ; sssom:mapping_cardinality "n:1" ; {CURATED} .', None,
     id="vaccine groups: a row that gives its cardinality"),
    pytest.param(CASCADE.CodeConversions, f"<urn:x:r> {CONVERSION.replace('icd:C88.0 ', '<https://ns.cascadeprotocol.org/codes/icd10cm/C880> ')} ; {CURATED} .",
     "A code conversion row maps a code", id="code conversions: a source with no point"),
    pytest.param(CASCADE.RetiredCodes, "cvx:141 owl:deprecated true ; dct:isReplacedBy cvx:150 .", None,
     id="retired codes: a code replaced by another"),
    pytest.param(CASCADE.RetiredCodes, "cvx:141 owl:deprecated false .", "owl:deprecated true",
     id="retired codes: a code deprecated as false"),
    pytest.param(CASCADE.DrugProducts, 'rxnorm:197361 cascade:termType "SCD" .', None,
     id="drug products: a clinical drug"),
    pytest.param(CASCADE.DrugProducts, 'rxnorm:370573 cascade:termType "SCDF" .', "one of SCD, SBD, GPCK or BPCK",
     id="drug products: a term type that is not listed"),
    pytest.param(CASCADE.DrugProducts, 'cvx:141 cascade:termType "SCD" .', "holds only the code's term type",
     id="drug products: a CVX code"),
    pytest.param(CASCADE.DrugProducts, 'rxnorm:197361 cascade:termType "SCD" ; skos:prefLabel "x" .', "holds only the code's term type",
     id="drug products: a name beside the term type"),
    pytest.param(CASCADE.DrugProducts, 'rxnorm:197361 cascade:termType "SCD", "SBD" .', "one of SCD, SBD, GPCK or BPCK",
     id="drug products: two term types"),
    pytest.param(CASCADE.VariantClassifications, f"{CLASSIFIED} .", None, id="variant classifications: a whole row"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression {EXPRESSION} .", None,
     id="variant classifications: an expression and nothing else"),
    pytest.param(CASCADE.VariantClassifications, f'{CLASSIFIED.replace("contributingSubmitterCount 5", "submitterCount 6")} .', None,
     id="variant classifications: a submitter count in place of the contributing one"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression <https://ns.cascadeprotocol.org/codes/hgvs/NM_000249.3:c.2042C%3ET> .",
     "percent-encoded", id="variant classifications: an expression that is not percent-encoded"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression <https://ns.cascadeprotocol.org/codes/hgvs/NG_000249.3%3Ac.2042C%3ET> .",
     "coding NM_ expressions", id="variant classifications: an NG_ expression"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression {EXPRESSION} . "
     f"<https://identifiers.org/clinvar:90012> cascade:hgvsExpression {EXPRESSION} .", "finds one row",
     id="variant classifications: two variations of one expression"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:clinvarClassification <urn:x:made-up> .", "concept of cascade:ClinVarClassifications",
     id="variant classifications: a classification that is no concept"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:clinvarReviewStatus cascade:ClinVarExpertPanel , cascade:ClinVarSingleSubmitter .",
     "at most one review status", id="variant classifications: two review statuses"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:contributingSubmitterCount 5 ; cascade:submitterCount 6 .", "never both",
     id="variant classifications: both counts of submitters"),
    pytest.param(CASCADE.VariantClassifications, f"{VARIATION} cascade:contributingSubmitterCount -1 .", "non-negative",
     id="variant classifications: a negative count"),
    pytest.param(CASCADE.VariantClassifications, f'{VARIATION} cascade:lastEvaluated "soon" .', "one xsd:date",
     id="variant classifications: a date that is no date"),
    pytest.param(CASCADE.VariantClassifications, f'{VARIATION} cascade:lastEvaluated "2024-12-11T10:00:00Z"^^xsd:dateTime .', "one xsd:date",
     id="variant classifications: a date with a time"),
    pytest.param(CASCADE.VariantClassifications, f'{VARIATION} skos:note "x" .', "holds only its variation",
     id="variant classifications: a property a row may not hold"),
    pytest.param(CASCADE.VariantClassifications, '<https://identifiers.org/clinvar:090011> cascade:lastEvaluated "2024-12-11"^^xsd:date .',
     "holds only its variation", id="variant classifications: a ClinVar ID with a leading zero"),
]
assert len({row.id for row in ROWS}) == len(ROWS)
PASSING = [pytest.param(*row.values[:2], id=row.id) for row in ROWS if row.values[2] is None]
FAILING = [row for row in ROWS if row.values[2] is not None]
CONVERSION_BREAKS = [
    pytest.param(f"<urn:x:r> {CONVERSION} ; sssom:mapping_justification semapv:LexicalMatching .", "justified as",
     id="a justification not allowed"),
    pytest.param(f"<urn:x:r> {CONVERSION.replace('1:1', '1:2')} ; {CURATED} .", "one of 1:1, 1:n, n:1 or n:n",
     id="a cardinality not allowed"),
    pytest.param(f"<urn:x:r> {CONVERSION} ; {CURATED} ; skos:note \"x\" .", "A mapping row is an owl:Axiom named by an IRI",
     id="a property it may not hold"),
]


class TestCodeSystems:
    """Code systems and the IRI a code gets · ontologies/cascade.ttl

    The vocabulary declares each code system with a stem, the beginning of the IRI every code of that system gets, and
    with the system URI that FHIR and C-CDA name it by. A code's IRI is its system's stem and the code, so two sources
    that state one code state one IRI.
    """

    class TestGivenAnyCodeSystem:
        def test_has_one_stem(self):
            """has one stem, which ends in a slash or a colon

            Each code system the vocabulary declares is read for its `void:uriSpace`. A system that has none or two, or
            whose one ends in any other character, fails.
            """
            offenders = {}
            for system in terms().subjects(RDF.type, CASCADE.CodeSystem):
                stems = list(terms().objects(system, VOID.uriSpace))
                if not (len(stems) == 1 and str(stems[0]).endswith(("/", ":"))):
                    offenders[str(system)] = [str(stem) for stem in stems]
            assert offenders == {}

        def test_has_one_system_uri(self):
            """has one system URI, an `xsd:anyURI` that ends in neither

            Each code system is read for its `cascade:codingSystemUri`. A system that has none or two, whose one is not an
            `xsd:anyURI`, or whose one ends in a slash or a colon fails.
            """
            offenders = {}
            for system in terms().subjects(RDF.type, CASCADE.CodeSystem):
                uris = list(terms().objects(system, CASCADE.codingSystemUri))
                if not (len(uris) == 1 and uris[0].datatype == XSD.anyURI and not str(uris[0]).endswith(("/", ":"))):
                    offenders[str(system)] = [str(uri) for uri in uris]
            assert offenders == {}

    class TestGivenTheCodeSystemsTogether:
        def test_holds_each_of_the_sixteen(self):
            """holds each of the sixteen that records and tables are written with

            The code systems the vocabulary declares include CVX, RxNorm, NDC, ICD-10-CM, SNOMED CT, LOINC, UNII, CPT,
            ICD-9-CM, HGVS, ClinVar, MED-RT, MeSH, Data Absent Reason, Null Flavor and Observation Interpretation. A system
            added beside them passes; one of the sixteen missing fails.
            """
            declared = {system.removeprefix(str(CASCADE)) for system in terms().subjects(RDF.type, CASCADE.CodeSystem)}
            assert SIXTEEN <= declared

        def test_gives_a_page_template_to_three_and_no_other(self):
            """gives a page template to ClinVar, LOINC and MeSH and to no other

            The code systems that have a `cascade:codePageUrlTemplate` are compared with ClinVar, LOINC and MeSH; they must
            be those three and no more.
            """
            assert set(terms().subjects(CASCADE.codePageUrlTemplate, None)) == {CASCADE[name] for name in PAGES}

    class TestGivenACodeSystemWithAPageTemplate:
        @pytest.mark.parametrize("system", list(PAGES))
        def test_has_one_template(self, system):
            """has one template, an https address with `{code}` as its only expression

            The system is a declared code system with exactly one page template, which begins `https://`, holds `{code}`
            once and holds no other brace, so an app can fill it with a code and nothing else.
            """
            templates = list(terms().objects(CASCADE[system], CASCADE.codePageUrlTemplate))
            assert (CASCADE[system], RDF.type, CASCADE.CodeSystem) in terms() and len(templates) == 1
            template = str(templates[0])
            assert template.startswith("https://") and template.count("{code}") == 1
            assert template.replace("{code}", "").count("{") == 0 and template.replace("{code}", "").count("}") == 0

        @pytest.mark.parametrize("system", list(PAGES))
        def test_gives_a_code_its_page(self, system):
            """gives a code its page

            Putting a code in place of `{code}` in the system's template gives the address of that code's page at its
            publisher: variation 90011 for ClinVar, 2345-7 for LOINC and M0006414 for MeSH.
            """
            code, page = PAGES[system]
            assert str(terms().value(CASCADE[system], CASCADE.codePageUrlTemplate)).replace("{code}", code) == page

    class TestGivenAnyQueryOrOntologyFile:
        def test_writes_no_stem_that_no_code_system_registers(self):
            """writes no stem that no code system registers

            Every IRI stem written in a query or an ontology file, once the system URIs and page templates are taken out of
            its text, is compared with the stems the code systems declare. A file that writes a stem none declares fails.
            """
            registered = {str(space) for space in terms().objects(None, VOID.uriSpace)}
            system_uris = [f'"{uri}"' for uri in terms().objects(None, CASCADE.codingSystemUri)]
            templates = [f'"{template}"' for template in terms().objects(None, CASCADE.codePageUrlTemplate)]
            written = {}
            for path in [*sorted(QUERIES.parent.rglob("*.rq")), *sorted((ROOT / "ontologies").rglob("*.ttl"))]:
                text = path.read_text(encoding="utf-8").replace("\\\\.", ".")
                for uri in [*system_uris, *templates]:
                    text = text.replace(uri, "")
                if stray := sorted(set(STEM.findall(text)) - registered):
                    written[path.relative_to(ROOT).as_posix()] = stray
            assert written == {}


class TestReferenceTables:
    """Reference tables whose rows the shapes hold · ontologies/cascade.shapes.ttl, tests/table-versions/, **/references.ttl

    Reference tables reach a pod as versions of a series, each of one table kind, and every kind has a row shape: what one
    row of it must state. A row that breaks its shape is refused with a message that says how, and a row and a table
    version are each named from what they hold.
    `hana`'s apps hold rule-list versions 1 to 8, whose pinned R3 and R4 queries read only skos:broadMatch rows, so their
    product ingredient and vaccine group tables stay as published before version 9 and are held to every part of their
    row shape but the relation.

    @rule naming N11
    @rule naming N12
    """

    class TestGivenAnyTableKind:
        def test_is_one_a_series_may_name(self):
            """is one that `cascade:ReferenceSeriesShape` lets a series name, as no other is

            The kinds in the `sh:in` list of the series shape's `cascade:tableKind` property are compared with the kinds the
            vocabulary declares; the two lists are the same.
            """
            declared = table_kinds()
            series_kind = next(p for p in shapes().objects(CASCADE.ReferenceSeriesShape, SH.property)
                               if shapes().value(p, SH.path) == CASCADE.tableKind)
            assert declared and set(Collection(shapes(), shapes().value(series_kind, SH["in"]))) == declared

        def test_names_one_row_shape(self):
            """names one row shape

            Each declared kind is read for its `cascade:rowShape`. A kind with none or with two fails.
            """
            assert table_kinds()
            assert {kind for kind in table_kinds() if len(set(terms().objects(kind, CASCADE.rowShape))) != 1} == set()

        def test_says_what_its_rows_are_found_by(self):
            """says what its rows are found by

            Each declared kind is read for its `cascade:foundBy`, the properties that find a row of it. A kind that has
            none fails.
            """
            assert table_kinds()
            assert {kind for kind in table_kinds() if not set(terms().objects(kind, CASCADE.foundBy))} == set()

    class TestGivenTheTableKindsTogether:
        def test_marks_exactly_five_as_read_by_an_apps_pages(self):
            """marks exactly five as read by an app's pages

            The kinds marked `cascade:readByAppPages` are compared with code names, retired codes, variant classifications,
            panel members and drug classes; they must be those five and no more.
            """
            marked = {kind for kind in table_kinds() if (kind, CASCADE.readByAppPages, Literal(True)) in terms()}
            assert marked == {CASCADE.CodeNames, CASCADE.RetiredCodes, CASCADE.VariantClassifications, CASCADE.PanelMembers,
                              CASCADE.DrugClasses}

        def test_leaves_two_that_no_rule_list_names_and_no_page_reads(self):
            """leaves two, substance ingredients and value-set expansions, that no rule list names and no page reads

            Of the declared kinds, those that no file under `runtime/rule-list/` names and that are not marked as read by an
            app's pages are compared with substance ingredients and value-set expansions; they must be those two.
            """
            marked = {kind for kind in table_kinds() if (kind, CASCADE.readByAppPages, Literal(True)) in terms()}
            named = {kind for path in SHARED.glob("*.ttl") if path.name != "references.ttl"
                     for kind in parsed(path).objects(None, CASCADE.tableKind)}
            assert table_kinds() - named - marked == {CASCADE.SubstanceIngredients, CASCADE.ValueSetExpansions}

    class TestGivenARowOfAKind:
        @pytest.mark.parametrize("kind, rows", PASSING)
        def test_passes_its_kinds_row_shape(self, kind, rows):
            """passes its kind's row shape

            The row, written as Turtle, is checked against the row shape its kind names. The shape gives no message about
            it, so a runtime may hold it.
            """
            said = row_messages(kind, Graph().parse(data=PREFIXES + rows, format="turtle"))
            assert said == set()

        @pytest.mark.parametrize("kind, rows, message", FAILING)
        def test_fails_its_kinds_row_shape(self, kind, rows, message):
            """fails its kind's row shape with a message that says how

            The row is one break of its kind's row shape. The messages the shape gives about it are collected, and the words
            written for this break are in one of them: the row is refused, and for the reason the case names.
            """
            said = row_messages(kind, Graph().parse(data=PREFIXES + rows, format="turtle"))
            assert any(message in m for m in said), said

    class TestGivenACodeConversionRowBrokenInAnotherWay:
        @pytest.mark.parametrize("rows, message", CONVERSION_BREAKS)
        def test_reports_its_own_break(self, rows, message):
            """reports its own break and not the one about its form

            A code conversion row that is a replacement and has one other fault is given the message for that fault. It is
            not also told to be written with `dct:isReplacedBy`, as a row of another form would be.
            """
            said = row_messages(CASCADE.CodeConversions, Graph().parse(data=PREFIXES + rows, format="turtle"))
            assert any(message in m for m in said), said
            assert not any("with dct:isReplacedBy" in m for m in said), said

    class TestGivenATableHeldAsPublished:
        @pytest.mark.parametrize("kind, rows", [
            pytest.param(CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('obo:RO_0002350', 'skos:broadMatch')} ; {CURATED} .",
                         id="vaccine groups"),
            pytest.param(CASCADE.ProductIngredients, f"<urn:x:r> {DRUG} ; {CHAINED} .", id="product ingredients"),
        ])
        def test_is_not_told_to_use_the_relation(self, kind, rows):
            """is not told to use the relation

            A vaccine group row or a product ingredient row that states a `skos:broadMatch` and nothing else wrong gets no
            message, in a table of `hana`'s.
            """
            folder = PUBLISHED_BEFORE_RO / "app"
            assert held_messages(folder, kind, Graph().parse(data=PREFIXES + rows, format="turtle")) == set()

        @pytest.mark.parametrize("kind, rows, message", [
            pytest.param(CASCADE.VaccineGroups,
                         f"<urn:x:r> {ROW.replace('obo:RO_0002350', 'skos:broadMatch').replace('cvx:141', 'rxnorm:7980')} ; {CURATED} .",
                         "maps a CVX code", id="vaccine groups"),
            pytest.param(CASCADE.ProductIngredients, f"<urn:x:r> {DRUG.replace('rxnorm:153010', 'cvx:141')} ; {CHAINED} .",
                         "A product ingredient row maps an RxNorm code", id="product ingredients"),
        ])
        def test_reports_a_break_other_than_the_relation(self, kind, rows, message):
            """reports a break other than the relation

            A vaccine group row or a product ingredient row that states a `skos:broadMatch` and is broken another way is
            given the message for that break, in a table of `hana`'s.
            """
            said = held_messages(PUBLISHED_BEFORE_RO / "app", kind, Graph().parse(data=PREFIXES + rows, format="turtle"))
            assert any(message in m for m in said), said

    class TestGivenAnyTableVersionOfAKitOrOfScriptedInput:
        def test_conforms_to_its_kinds_row_shape(self):
            """conforms to its kind's row shape, but for the relation of two kinds of `hana`'s tables

            The rows of every table version a kit or the scripted input holds are checked against its kind's row shape.
            The product ingredients and vaccine groups under `runtime/scripted-input/hana/tables` are not checked for
            the relation their rows state.
            """
            assert table_versions()
            broken = {}
            for folder, stem, kind, rows in table_versions():
                if said := held_messages(folder, kind, rows):
                    broken[f"{folder.relative_to(ROOT).as_posix()}/{stem}"] = said
            assert broken == {}

        def test_names_every_mapping_row_by_n11(self):
            """names every mapping row by N11

            Each row of every table version that is an `owl:Axiom` is named by the naming rule over its source, property
            and target, and its sequence for a panel member. A row named otherwise fails.
            """
            assert table_versions()
            misnamed = {str(row) for _, _, _, rows in table_versions() for row in rows.subjects(RDF.type, OWL.Axiom)
                        if str(row) != table_row_name(*name_inputs(rows, row))}
            assert misnamed == set()

    class TestGivenAnyFolderOfTablesBesideAReferencesTtl:
        """given any folder of tables beside a `references.ttl`"""

        def test_repeats_no_file_of_the_rule_list(self):
            """repeats no file of `runtime/rule-list/` byte for byte

            A folder of tables beside a `references.ttl`, other than the rule list's own, leaves the vocabulary's rule list
            to it. A version file of the folder that is the rule list's file of that name, byte for byte, fails.
            """
            repeated = [own.relative_to(ROOT).as_posix() for _, own, shared, _ in listed_versions()
                        if own.is_file() and shared.is_file() and own.read_bytes() == shared.read_bytes()]
            assert repeated == []

        def test_holds_a_file_for_every_version_it_lists(self):
            """holds a file for every version it lists, or leaves a rule list to `runtime/rule-list/`

            Each version the folder's `references.ttl` lists has a file in the folder. The one exception is a rule list,
            a version of no table kind, listed by a scripted input's `tables` folder and held in `runtime/rule-list/`.
            """
            missing = [own.relative_to(ROOT).as_posix() for folder, own, shared, kind in listed_versions()
                       if not own.is_file()
                       and not (folder.parent.name == "tables" and kind is None and shared.is_file())]
            assert missing == []

    class TestGivenThePanelMembersVector:
        def test_conforms_to_its_kinds_row_shape(self):
            """conforms to its kind's row shape

            The rows of `tests/table-versions/panel-members-1.ttl` are checked against the panel members row shape, which
            gives no message about them.
            """
            assert row_messages(CASCADE.PanelMembers, parsed(VERSIONS / "panel-members-1.ttl")) == set()

        def test_names_every_row_by_n11(self):
            """names every row by N11 over its source, property, target and sequence

            Each row of the vector is named by the naming rule over its panel, its member, the property that links them and
            the member's sequence in the panel.
            """
            rows = parsed(VERSIONS / "panel-members-1.ttl")
            misnamed = [str(row) for row in rows.subjects(RDF.type, OWL.Axiom)
                        if str(row) != table_row_name(*name_inputs(rows, row))]
            assert misnamed == []

        def test_holds_a_member_listed_at_two_sequences_as_two_rows(self):
            """holds a member listed at two sequences as two rows

            A member that the vector lists twice in one panel, at two sequences, is two rows with two names. The only such
            member is the LOINC code 30395-8.
            """
            twice = {pair: names for pair, names in panel_member_names(parsed(VERSIONS / "panel-members-1.ttl")).items()
                     if len(names) == 2}
            assert [pair[1] for pair in twice] == [URIRef("http://loinc.org/rdf/30395-8")]

        def test_holds_a_nested_panels_members_as_rows_of_that_panel(self):
            """holds a nested panel's members as rows of that panel

            Panel 24320-4 is listed as a member of panel 24318-8, and the members listed for 24320-4 itself are 718-7 and no
            other.
            """
            named = panel_member_names(parsed(VERSIONS / "panel-members-1.ttl"))
            members = lambda panel: {m for p, m in named if p == URIRef(f"http://loinc.org/rdf/{panel}")}
            nested = URIRef("http://loinc.org/rdf/24320-4")
            assert nested in members("24318-8") and members("24320-4") == {URIRef("http://loinc.org/rdf/718-7")}

    class TestGivenAnyTableVersionCase:
        """given any table-version case"""

        def test_conforms_in_its_rows_to_its_kinds_row_shape(self):
            """conforms, in its rows, to its kind's row shape

            Each case in `tests/table-versions/cases.json` that has a file of rows is checked against the row shape of its
            kind, and the shape gives no message about any.
            """
            offenders = [case["rows"] for case in CASES
                         if case["rows"] and row_messages(CASCADE[case["kind"]], parsed(VERSIONS / case["rows"]))]
            assert offenders == []

        def test_is_named_by_n12(self):
            """is named by N12 over its series, the version it revises and its rows

            The naming rule N12 is given each case's series, the version it revises (none for a first version) and the
            statements of its rows. The name it gives must be the name the case lists.
            """
            assert [case_version_name(case) for case in CASES] == [case["name"] for case in CASES]

        def test_has_a_name_no_other_case_has(self):
            """has a name no other case has

            The names N12 gives the cases are all different, so two versions are never named alike.
            """
            assert len({case_version_name(case) for case in CASES}) == len(CASES)

    class TestGivenAnyValueSetExpansionOfAFixture:
        """given any value-set expansion of a fixture"""

        def test_names_one_value_set(self):
            """names one value set, which every row of it has as its target

            A fixture that holds the rows of a value-set expansion in `rows.trig` names, on its version, one value set. Every
            row of that version's graph has that value set as its `owl:annotatedTarget`.
            """
            checked, offenders = 0, []
            for index_file in sorted((ROOT / "tests" / "fixtures").glob("*/references.ttl")):
                if not (index_file.parent / "rows.trig").is_file():
                    continue
                index = parsed(index_file)
                rows = Dataset()
                rows.parse(data=(index_file.parent / "rows.trig").read_text(encoding="utf-8"), format="trig")
                for version, series in index.subject_objects(PROV.specializationOf):
                    if index.value(series, CASCADE.tableKind) != CASCADE.ValueSetExpansions:
                        continue
                    named = set(index.objects(version, CASCADE.expandedValueSet))
                    targets = set(rows.graph(version).objects(None, OWL.annotatedTarget))
                    if not (len(named) == 1 and targets <= named):
                        offenders.append((index_file.parent.name, str(version)))
                    checked += 1
            assert checked
            assert offenders == []
