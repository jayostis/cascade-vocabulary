"""Every table row conforms to its kind's shape and is named by N11, the shapes refuse broken rows, and a table version is
named by N12 (runtime/naming.feature)."""

import json
import re
from functools import cache

import pytest
from pyshacl import validate
from rdflib import Dataset, Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, SH, SKOS, XSD

from contract import QUERIES, CASCADE, ROOT, file_stem
from engines import parsed
from naming import content, table_row_name, table_version_name


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


@cache
def shapes():
    return Graph().parse(ROOT / "ontologies" / "cascade.shapes.ttl")


@cache
def kinds():
    return Graph().parse(ROOT / "ontologies" / "cascade.ttl")


def messages(kind, rows):
    """The messages the kind's row shape gives about the rows, every subject of them a focus node."""
    shape = kinds().value(kind, CASCADE.rowShape)
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
            kind = index.value(series, CASCADE.tableKind)
            if kind is not None:
                stem = file_stem(str(version))
                yield folder, stem, kind, parsed(folder / f"{stem}.ttl")


def test_a_story_folder_leaves_the_vocabularys_rule_list_to_it_and_every_version_it_lists_has_a_file_in_one_place():
    shared = ROOT / "runtime" / "rule-list"
    repeated, missing = [], []
    for folder in sorted(set(FOLDERS) - {shared}):
        index = parsed(folder / "references.ttl")
        for version, series in index.subject_objects(PROV.specializationOf):
            name = f"{file_stem(str(version))}.ttl"
            own = folder / name
            if own.is_file() and (shared / name).is_file() and own.read_bytes() == (shared / name).read_bytes():
                repeated.append(own.relative_to(ROOT).as_posix())
            open_names_it = folder.parent.name == "tables"
            if not own.is_file() and not (open_names_it and index.value(series, CASCADE.tableKind) is None and (shared / name).is_file()):
                missing.append(own.relative_to(ROOT).as_posix())
    assert repeated == [] and missing == []


def test_every_kind_names_one_row_shape_and_what_its_rows_are_found_by():
    declared = set(kinds().subjects(RDF.type, CASCADE.TableKind))
    series_kind = next(p for p in shapes().objects(CASCADE.ReferenceSeriesShape, SH.property)
                       if shapes().value(p, SH.path) == CASCADE.tableKind)
    assert declared and set(Collection(shapes(), shapes().value(series_kind, SH["in"]))) == declared
    assert {kind for kind in declared if len(set(kinds().objects(kind, CASCADE.rowShape))) != 1
            or not set(kinds().objects(kind, CASCADE.foundBy))} == set()


STEM = re.compile(r"https?://(?:snomed\.info|loinc\.org|id\.nlm\.nih\.gov|ns\.cascadeprotocol\.org/codes)/[A-Za-z0-9._/-]*/"
                  r"|https://identifiers\.org/[a-z]+:")


def test_every_iri_stem_a_query_or_an_ontology_writes_is_a_code_systems_uri_space():
    registered = {str(space) for space in kinds().objects(None, VOID.uriSpace)}
    system_uris = [f'"{uri}"' for uri in kinds().objects(None, CASCADE.codingSystemUri)]
    templates = [f'"{template}"' for template in kinds().objects(None, CASCADE.codePageUrlTemplate)]
    written = {}
    for path in [*sorted(QUERIES.parent.rglob("*.rq")), *sorted((ROOT / "ontologies").rglob("*.ttl"))]:
        text = path.read_text(encoding="utf-8").replace("\\\\.", ".")
        for uri in [*system_uris, *templates]:
            text = text.replace(uri, "")
        if stray := sorted(set(STEM.findall(text)) - registered):
            written[path.relative_to(ROOT).as_posix()] = stray
    assert written == {}


def test_every_code_system_has_one_iri_stem_ending_in_a_slash_or_a_colon_and_one_system_uri_ending_in_neither():
    systems = set(kinds().subjects(RDF.type, CASCADE.CodeSystem))
    assert {system.removeprefix(str(CASCADE)) for system in systems} == {
        "CVX", "RxNorm", "NDC", "ICD10CM", "SNOMEDCT", "LOINC", "UNII", "CPT", "ICD9CM", "HGVS", "ClinVar", "MEDRT", "MeSH",
        "DataAbsentReason", "NullFlavor", "ObservationInterpretation"}
    for system in systems:
        stems, uris = list(kinds().objects(system, VOID.uriSpace)), list(kinds().objects(system, CASCADE.codingSystemUri))
        assert len(stems) == 1 and str(stems[0]).endswith(("/", ":")), system
        assert len(uris) == 1 and uris[0].datatype == XSD.anyURI and not str(uris[0]).endswith(("/", ":")), system


def test_every_page_template_is_one_address_with_the_code_as_its_only_expression():
    templated = {system: list(kinds().objects(system, CASCADE.codePageUrlTemplate)) for system in set(kinds().subjects(CASCADE.codePageUrlTemplate, None))}
    assert templated.keys() == {CASCADE.ClinVar, CASCADE.MeSH}
    for system, templates in templated.items():
        assert (system, RDF.type, CASCADE.CodeSystem) in kinds() and len(templates) == 1, system
        template = str(templates[0])
        assert template.startswith("https://") and template.count("{code}") == 1, system
        assert template.replace("{code}", "").count("{") == 0 and template.replace("{code}", "").count("}") == 0, system
    assert str(templated[CASCADE.ClinVar][0]).replace("{code}", "90011") == "https://www.ncbi.nlm.nih.gov/clinvar/variation/90011/"
    assert str(templated[CASCADE.MeSH][0]).replace("{code}", "M0006414") == "https://id.nlm.nih.gov/mesh/M0006414.html"


def name_inputs(rows, row):
    """N11's inputs for a row: its source, property and target, and a panel member's sequence."""
    inputs = [str(rows.value(row, p)) for p in (OWL.annotatedSource, OWL.annotatedProperty, OWL.annotatedTarget)]
    sequence = rows.value(row, CASCADE.panelSequence)
    return inputs if sequence is None else [*inputs, str(sequence)]


def test_a_panel_member_listed_at_two_sequences_is_two_rows_with_two_names_and_a_nested_panel_is_its_own_rows():
    rows = parsed(VERSIONS / "panel-members-1.ttl")
    assert messages(CASCADE.PanelMembers, rows) == set()
    named = {}
    for row in rows.subjects(RDF.type, OWL.Axiom):
        assert str(row) == table_row_name(*name_inputs(rows, row))
        named.setdefault((rows.value(row, OWL.annotatedSource), rows.value(row, OWL.annotatedTarget)), set()).add(row)
    twice = {pair: names for pair, names in named.items() if len(names) == 2}
    assert [pair[1] for pair in twice] == [URIRef("http://loinc.org/rdf/30395-8")]
    members = lambda panel: {m for p, m in named if p == URIRef(f"http://loinc.org/rdf/{panel}")}
    nested = URIRef("http://loinc.org/rdf/24320-4")
    assert nested in members("24318-8") and members("24320-4") == {URIRef("http://loinc.org/rdf/718-7")}


PUBLISHED_BEFORE_RO = ROOT / "runtime" / "scripted-input" / "hana" / "tables"


def test_every_row_of_every_kit_and_vector_conforms_to_its_kind_and_every_mapping_row_is_named_by_n11():
    found, broken, misnamed = 0, {}, set()
    for folder, stem, kind, rows in versions():
        found += 1
        held_as_published = folder.parent == PUBLISHED_BEFORE_RO and kind in (CASCADE.ProductIngredients, CASCADE.VaccineGroups)
        if (said := messages(kind, rows)) and not held_as_published:
            broken[f"{folder.relative_to(ROOT).as_posix()}/{stem}"] = said
        for row in rows.subjects(RDF.type, OWL.Axiom):
            if str(row) != table_row_name(*name_inputs(rows, row)):
                misnamed.add(str(row))
    assert found == 53
    assert broken == {}
    assert misnamed == set()


@pytest.mark.parametrize("kind, rows, message", [
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW} ; {CURATED} .", None),
    (CASCADE.VaccineGroups, f"[] {ROW} ; {CURATED} .", "A mapping row is an owl:Axiom named by an IRI"),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW}, cvx:89 ; {CURATED} .", "A mapping row maps to one object code"),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW} ; {CURATED} ; skos:note \"x\" .", "A mapping row is an owl:Axiom named by an IRI"),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('obo:RO_0002350', 'skos:broadMatch')} ; {CURATED} .", "with obo:RO_0002350"),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', 'rxnorm:7980')} ; {CURATED} .", "maps a CVX code"),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', '<https://ns.cascadeprotocol.org/codes/cvx/8>')} ; {CURATED} .",
     "maps a CVX code"),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW.replace('cvx:141', 'cvx:88')} ; {CURATED} .", None),
    (CASCADE.VaccineGroups, f"<urn:x:r> {ROW} ; sssom:mapping_justification semapv:LexicalMatching .", "justified as"),
    (CASCADE.CodeNames, 'cvx:141 skos:prefLabel "Influenza" ; skos:altLabel "Flu" ; skos:notation "141" .', None),
    (CASCADE.CodeNames, 'cvx:141 skos:prefLabel "Influenza", "Flu" ; skos:notation "141" .', "one preferred name"),
    (CASCADE.CodeNames, 'cvx:99 skos:prefLabel "RESERVED" ; skos:altLabel "RESERVED" ; skos:notation "99" .',
     "none its preferred name"),
    (CASCADE.CodeNames, 'cvx:141 skos:prefLabel "Influenza"@en ; skos:notation "141" .', "one preferred name"),
    (CASCADE.CodeNames, '<urn:x:141> skos:prefLabel "Influenza" ; skos:notation "141" .', "one of the code systems' forms"),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/cvx/8> skos:prefLabel "x" ; skos:notation "8" .', "one of the code systems' forms"),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/ndc11/00002143380> skos:prefLabel "x" ; skos:notation "0002-1433-80" .', None),
    (CASCADE.CodeNames, '<http://hl7.org/fhir/sid/ndc/00002143380> skos:prefLabel "x" ; skos:notation "0002-1433-80" .',
     "one of the code systems' forms"),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/ndc11/0002-1433-80> skos:prefLabel "x" ; skos:notation "0002-1433-80" .',
     "one of the code systems' forms"),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/E11.9> skos:prefLabel "x" ; skos:notation "E11.9" .', None),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/S72.001A> skos:prefLabel "x" ; skos:notation "S72.001A" .', None),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/QA0.0> skos:prefLabel "x" ; skos:notation "QA0.0" .', None),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/icd10cm/E119> skos:prefLabel "x" ; skos:notation "E11.9" .',
     "one of the code systems' forms"),
    (CASCADE.CodeNames, 'rxnorm:RX7980 skos:prefLabel "x" ; skos:notation "7980" .', "one of the code systems' forms"),
    (CASCADE.CodeNames, '<http://snomed.info/id/91936005> skos:prefLabel "x" ; skos:notation "91936005" .', None),
    (CASCADE.CodeNames, '<http://snomed.info/sct/91936005> skos:prefLabel "x" ; skos:notation "91936005" .',
     "one of the code systems' forms"),
    (CASCADE.CodeNames, '<http://snomed.info/id/x91936005> skos:prefLabel "x" ; skos:notation "91936005" .',
     "one of the code systems' forms"),
    (CASCADE.CodeNames, '<http://loinc.org/rdf/2823-3> skos:prefLabel "x" ; skos:notation "2823-3" .', None),
    (CASCADE.CodeNames, '<http://loinc.org/rdf/28233> skos:prefLabel "x" ; skos:notation "2823-3" .',
     "one of the code systems' forms"),
    (CASCADE.ProductIngredients, f"<urn:x:r> {INGREDIENT} ; {CHAINED} .", None),
    (CASCADE.ProductIngredients, f"<urn:x:r> {INGREDIENT.replace('rxnorm:153010', 'cvx:141')} ; {CHAINED} .",
     "A product ingredient row maps an RxNorm code"),
    (CASCADE.ProductIngredients, f"<urn:x:r> {INGREDIENT.replace('obo:RO_0002248', 'cascade:hasPreciseIngredient')} ; {CHAINED} .", None),
    (CASCADE.ProductIngredients, f"<urn:x:r> {DRUG} ; {CHAINED} .", "with obo:RO_0002248"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL} ; {CURATED} .", None),
    (CASCADE.PanelMembers, f'<urn:x:r> {PANEL} ; {CURATED} ; cascade:observationRequiredInPanel "Rflx-a" .', None),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('; cascade:panelSequence 4', '')} ; {CURATED} .", "one sequence"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('Sequence 4', 'Sequence \"4\"')} ; {CURATED} .", "one sequence"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL} ; {CURATED} ; cascade:observationRequiredInPanel \"R\", \"O\" .", "at most one requirement"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('30395-8', 'XYZ')} ; {CURATED} .", "one member, a LOINC code"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('24318-8', '24318')} ; {CURATED} .", "one panel, a LOINC code"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL.replace('RO_0002351', 'RO_0002350')} ; {CURATED} .", "with obo:RO_0002351"),
    (CASCADE.PanelMembers, f"<urn:x:r> {PANEL} ; {CURATED} ; sssom:mapping_cardinality \"1:1\" .", "holding only its panel"),
    (CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG} ; {CURATED} .", None),
    (CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('establishedPharmacologicClass', 'chemicalStructureClass').replace('<https://ns.cascadeprotocol.org/codes/medrt/N0000175722>', MESH)} ; {CURATED} .", None),
    (CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('<https://ns.cascadeprotocol.org/codes/medrt/N0000175722>', MESH)} ; {CURATED} .",
     "or, with cascade:chemicalStructureClass, to a MeSH code"),
    (CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('rxnorm:5640', 'cvx:141')} ; {CURATED} .", "maps an RxNorm code"),
    (CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG.replace('cascade:establishedPharmacologicClass', 'skos:broadMatch')} ; {CURATED} .",
     "with cascade:establishedPharmacologicClass, cascade:mechanismOfActionClass"),
    (CASCADE.DrugClasses, f"<urn:x:r> {CLASSIFIED_DRUG} ; {CHAINED} .", "justified as the publisher's curated row"),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER} ; {CURATED} .", None),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('<http://snomed.info/id/1481000119100>', '<urn:x:G0108>')} ; {CURATED} .",
     "maps a code, an IRI of one of the code systems' forms"),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('1001>', '1001#20220924>')} ; {CURATED} .", "named by its canonical URL"),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace(DIABETES, '<urn:oid:2.16.840.1.113883.3.464.1003.103.12.1001>')} ; {CURATED} .",
     "Cascade's rule, one value set one name"),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('1001>', '1001|20220924>')} ; {CURATED} .", "named by its canonical URL"),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER.replace('obo:RO_0002350', 'skos:exactMatch')} ; {CURATED} .", "with obo:RO_0002350"),
    (CASCADE.ValueSetExpansions, f"<urn:x:r> {MEMBER} ; {CHAINED} .", "justified as a manually curated mapping"),
    (CASCADE.CodeNames, f'<https://ns.cascadeprotocol.org/codes/medrt/N0000175722> skos:prefLabel "Beta-Adrenergic Blocker [EPC]" ; skos:notation "N0000175722" .', None),
    (CASCADE.CodeNames, f'{MESH} skos:prefLabel "Ibuprofen" ; skos:notation "M0006414" .', None),
    (CASCADE.CodeNames, '<http://id.nlm.nih.gov/mesh/D004095> skos:prefLabel "x" ; skos:notation "D004095" .', None),
    (CASCADE.CodeNames, '<http://id.nlm.nih.gov/mesh/X1> skos:prefLabel "x" ; skos:notation "X1" .', "one of the code systems' forms"),
    (CASCADE.CodeNames, '<https://ns.cascadeprotocol.org/codes/medrt/N000017572> skos:prefLabel "x" ; skos:notation "N000017572" .',
     "one of the code systems' forms"),
    (CASCADE.BrandGenerics, f"<urn:x:r> {DRUG} ; {CURATED} .", None),
    (CASCADE.BrandGenerics, f"<urn:x:r> {DRUG.replace('rxnorm:5640', '<http://snomed.info/id/387207008>')} ; {CURATED} .",
     "A brand generic row maps to an RxNorm code"),
    (CASCADE.CodeConversions, f"<urn:x:r> {CONVERSION} ; {CURATED} .", None),
    (CASCADE.CodeConversions, f"<urn:x:r> {EARLIER} ; {CURATED} .", None),
    (CASCADE.CodeConversions, f"<urn:x:r> {EARLIER} ; {CARDINALITY} ; {CURATED} .", "with dct:isReplacedBy"),
    (CASCADE.CodeConversions, f"<urn:x:r> {EARLIER.replace('exactMatch', 'narrowMatch')} ; {CURATED} .",
     "with dct:isReplacedBy"),
    (CASCADE.CodeConversions, f"<urn:x:r> {EARLIER.replace('skos:exactMatch', 'dct:isReplacedBy')} ; {CURATED} .",
     "gives its cardinality"),
    (CASCADE.CodeConversions, f"<urn:x:r> {CONVERSION.replace('1:1', '1:2')} ; {CURATED} .",
     "one of 1:1, 1:n, n:1 or n:n"),
    (CASCADE.VaccineGroups, f'<urn:x:r> {ROW} ; sssom:mapping_cardinality "n:1" ; {CURATED} .', None),
    (CASCADE.CodeConversions, f"<urn:x:r> {CONVERSION.replace('icd:C88.0 ', '<https://ns.cascadeprotocol.org/codes/icd10cm/C880> ')} ; {CURATED} .",
     "A code conversion row maps a code"),
    (CASCADE.RetiredCodes, "cvx:141 owl:deprecated true ; dct:isReplacedBy cvx:150 .", None),
    (CASCADE.RetiredCodes, "cvx:141 owl:deprecated false .", "owl:deprecated true"),
    (CASCADE.DrugProducts, 'rxnorm:197361 cascade:termType "SCD" .', None),
    (CASCADE.DrugProducts, 'rxnorm:370573 cascade:termType "SCDF" .', "one of SCD, SBD, GPCK or BPCK"),
    (CASCADE.DrugProducts, 'cvx:141 cascade:termType "SCD" .', "holds only the code's term type"),
    (CASCADE.DrugProducts, 'rxnorm:197361 cascade:termType "SCD" ; skos:prefLabel "x" .', "holds only the code's term type"),
    (CASCADE.DrugProducts, 'rxnorm:197361 cascade:termType "SCD", "SBD" .', "one of SCD, SBD, GPCK or BPCK"),
    (CASCADE.VariantClassifications, f"{CLASSIFIED} .", None),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression {EXPRESSION} .", None),
    (CASCADE.VariantClassifications, f'{CLASSIFIED.replace("contributingSubmitters 5", "submitters 6")} .', None),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression <https://ns.cascadeprotocol.org/codes/hgvs/NM_000249.3:c.2042C%3ET> .",
     "percent-encoded"),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression <https://ns.cascadeprotocol.org/codes/hgvs/NG_000249.3%3Ac.2042C%3ET> .",
     "coding NM_ expressions"),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:hgvsExpression {EXPRESSION} . "
     f"<https://identifiers.org/clinvar:90012> cascade:hgvsExpression {EXPRESSION} .", "finds one row"),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:clinvarClassification <urn:x:made-up> .", "concept of cascade:ClinVarClassifications"),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:clinvarReviewStatus cascade:ClinVarExpertPanel , cascade:ClinVarSingleSubmitter .",
     "at most one review status"),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:contributingSubmitterCount 5 ; cascade:submitterCount 6 .", "never both"),
    (CASCADE.VariantClassifications, f"{VARIATION} cascade:contributingSubmitterCount -1 .", "non-negative"),
    (CASCADE.VariantClassifications, f'{VARIATION} cascade:lastEvaluated "soon" .', "one xsd:date"),
    (CASCADE.VariantClassifications, f'{VARIATION} cascade:lastEvaluated "2024-12-11T10:00:00Z"^^xsd:dateTime .', "one xsd:date"),
    (CASCADE.VariantClassifications, f'{VARIATION} skos:note "x" .', "holds only its variation"),
    (CASCADE.VariantClassifications, '<https://identifiers.org/clinvar:090011> cascade:lastEvaluated "2024-12-11"^^xsd:date .',
     "holds only its variation"),
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
    said = messages(CASCADE.CodeConversions, Graph().parse(data=PREFIXES + rows, format="turtle"))
    assert any(message in m for m in said), said
    assert not any("with dct:isReplacedBy" in m for m in said), said


def test_each_table_version_is_named_by_n12_from_its_series_the_version_it_revises_and_its_rows():
    cases = json.loads((VERSIONS / "cases.json").read_text(encoding="utf-8"))
    named = []
    for case in cases:
        rows = set()
        if case["rows"]:
            assert messages(CASCADE[case["kind"]], parsed(VERSIONS / case["rows"])) == set(), case["rows"]
            rows = content((VERSIONS / case["rows"]).read_text(encoding="utf-8"), "turtle")
        named.append(table_version_name(case["series"], case["revises"] or None, rows))
    assert named == [case["name"] for case in cases]
    assert len(set(named)) == len(cases)


def test_every_row_of_a_value_set_expansion_has_the_value_set_its_version_names_as_its_target():
    checked = 0
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
            assert len(named) == 1 and targets <= named, (index_file.parent.name, version)
            checked += 1
    assert checked
