# The variant interpretation

Status: draft, 2026-10-13; revised 2026-10-22 against `README.md`, from the review on #202; the lab applied on
2026-10-24 (#219). Terms: `genomics:VariantInterpretation`, `acmgClassification`, `variantInterpreted`,
`interpretedDate`, `objectCondition`, `acmgEvidenceCode`, `prov:wasAttributedTo` on its version, and the concepts `Pathogenic`, `LikelyPathogenic`, `UncertainSignificance`, `LikelyBenign`,
`Benign`. Replaces this note's own "it is unnamed" and "the record may be outside the document it came from", which
yield to `naming.md`: the interpretation is named like any record, and `naming.md` never lets a `urn:uuid` be identity
across documents; how a variant held from another document is reached is open. Applied in `genomics.shapes.ttl:83`,
whose message this pull request (#200) changed to say the record is one in the same document. Names are `naming.md`;
which revision is current is `currency.md`; the lab is an organisation record in `republishing-sources.md`;
the variant is `variant-record.md`; that two labs' variants are one is `variant-identity.md`, by R12 and R13,
not a republishing join. #193 renames the `genomics/v1#` namespace into the one unversioned namespace, and #191
the rule terms.

## Question

Where does a report's classification of a variant live, and what is its shape, so that a page can show what each report
said beside what a table says today? Two labs may call one variant differently, years apart; neither call may overwrite
the other, the pod has no server of record to say which is right, and a view the person shares carries each.

## What others do

- **FHIR Genomics Reporting IG STU3 (v3.0.0),** from the HL7 Clinical Genomics Work Group. The classification is a
  component of a Diagnostic Implication, a separate Observation whose `derivedFrom` is the Variant, "Variant the
  implication is derived from". The clinical significance component (53037-8) is "The clinical impact of an implication
  on a person's health", its value example-bound to LOINC answer list LL4034-6, "Pathogenic | Likely pathogenic |
  Uncertain significance | Likely benign | Benign". A predicted phenotype component (81259-4) names the condition, and an
  evidence level component (93044-6) the evidence. Its `issued`, else `effective[x]`, is the date.
- **ACMG/AMP 2015** (Richards et al., *Genet Med*): "This report recommends the use of specific standard terminology:
  'pathogenic', 'likely pathogenic', 'uncertain significance', 'likely benign', and 'benign'".
- **ClinVar** says "The classification of a variant is provided only by the submitter": each submitted record (SCV) is a
  submitter's classification, an RCV aggregates per variant and condition, and a VCV per variant; germline terms "use five
  levels to describe pathogenicity". A 2018 submission for 90011 is flagged and excluded from the aggregate (unverified:
  read in #107's body, 2026-10-13).
- **GA4GH VA-spec.** A Statement is "A claim of purported truth as made by a particular agent, on a particular
  occasion", with a proposition ("A possible fact, the validity of which is assessed"), a direction, a strength, a
  classification, evidence lines and contributions, "Specific actions taken by an Agent"; its Variant Pathogenicity
  Statement profile follows ACMG 2015. It is built on **SEPIO**, which represents "assertions and their evidence and
  provenance of any kind".
- **openEHR.** The sequencing-test variant cluster (`genomic_variant_result.v1`, rev 1.1.1) holds the classification
  in its "ACMG classification" element, a `DV_CODED_TEXT` bound to the five LOINC answer codes (verified, #202).
- **OMOP.** The Genomic vocabulary holds variants and knowledge-base concepts; a classification is not a patient-level
  record there.
- **SPHN.** Its genomic concepts were not read (see `variant-record.md`).
- **PROV-O** gives `prov:wasAttributedTo`, "the ascribing of an entity to an agent", and `prov:Organization`.
- **SKOS** gives a `skos:ConceptScheme`, "an aggregation of one or more SKOS concepts", for a closed list of values.

Sources: FHIR Genomics Reporting IG STU3 (https://hl7.org/fhir/uv/genomics-reporting/STU3/, verified) and its Diagnostic
Implication profile (https://hl7.org/fhir/uv/genomics-reporting/STU3/StructureDefinition-diagnostic-implication.html,
verified; the LOINC answer codes LA6668-3 and the rest are not on that page and were not fetched from LOINC, unverified);
Richards et al., Genet Med 2015 (https://pmc.ncbi.nlm.nih.gov/articles/PMC4544753/, verified); ClinVar classifications
(https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/, verified) and identifiers
(https://www.ncbi.nlm.nih.gov/clinvar/docs/identifiers/, verified); GA4GH VA-spec (https://va-spec.ga4gh.org/en/latest/,
verified) and its Statement
(https://va-spec.ga4gh.org/en/latest/core-information-model/entities/information-entities/statement.html, verified);
SEPIO (https://sepio-framework.github.io/sepio-linkml/about/, verified); openEHR, OMOP and SPHN as cited in
`variant-record.md`; PROV-O (https://www.w3.org/TR/prov-o/, verified); SKOS (https://www.w3.org/TR/skos-reference/,
verified). Research: #107's body (https://github.com/jayostis/cascade-vocabulary/issues/107) and its Step 0 comment
(https://github.com/jayostis/cascade-vocabulary/issues/107#issuecomment-6139118340); the evidence issue
(https://github.com/jayostis/cascade-vocabulary/issues/203); the scenario #138 (https://github.com/jayostis/cascade-vocabulary/issues/138).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| the interpretation | FHIR Diagnostic Implication, an Observation; VA-spec Statement; SEPIO | its own record, `genomics:VariantInterpretation`, a `prov:Entity`, separate from the variant | borrowed from FHIR in being separate; diverged from FHIR's Observation and VA-spec's Statement in form; the reason is owed (Still open) |
| its name | `naming.md` | named as any record from its source is | borrowed from `naming.md` |
| link to its variant | FHIR `derivedFrom`; VA-spec proposition's subject | `variantInterpreted`, at most one, the variant record's IRI, as `rec:patient` points to its profile record; within one document that is a name; a `urn:uuid` never crosses documents, and how a variant held from another document is reached is open (Still open) | borrowed from FHIR's `derivedFrom` |
| classification | FHIR 53037-8, LOINC LL4034-6 (example); ACMG/AMP 2015; VA-spec classification | `acmgClassification`, at most one, one of the five concepts of `cascade:ClinVarClassifications` named above; a report whose answer is not one of the five states none | borrowed: the five ACMG terms as `skos:Concept`s of the ClinVar scheme, each `skos:exactMatch` its LOINC answer; a coded value is what the IG writes |
| date | FHIR `issued`, else `effective[x]` | `interpretedDate`, at most one `xsd:date` | borrowed |
| which revision is current | `currency.md` | `currency.md`'s ladder; `interpretedDate` is content, not a rung | borrowed from `currency.md` |
| condition | FHIR predicted phenotype 81259-4; VA-spec proposition's `objectCondition`; ClinVar RCV | `objectCondition`, at most one, the IRI of a `cascade:ProblemOrDiagnosis` record in the same document; none when the report states none | borrowed: VA-spec's name; the therapy objects wait (Why) |
| evidence | FHIR evidence level 93044-6; VA-spec ACMG 2015 profile evidence outcomes; SEPIO | `acmgEvidenceCode`, any number of strings, each written as VA-spec's ACMG 2015 profile writes an evidence outcome (`PM2`, `PS3_moderate`, `PS3_not_met`, `no_criteria_met`) | borrowed: VA-spec's string form, copied as a pattern |
| who called it | FHIR `Observation.performer`; VA-spec contributions; ClinVar SCV submitter; PROV-O `wasAttributedTo`; `republishing-sources.md` organisation | the version is `prov:wasAttributedTo` the lab's `cascade:Organization` record, at most one, named by `OrganizationNamingRule`; from FHIR, the one organisation record a Diagnostic Implication's `performer` names; none where it names none, or more than one, which the adapter reports | borrowed from PROV-O, the property judgments use; FHIR's performer as its source |
| status | FHIR `Observation.status` | `clinical:status` | borrowed |
| reclassification | ClinVar SCV versions | a new version, or a new report | ours |

## Why

**Why the report's call is its own record.** The report's classification is the record's content and a table's is the
table's; nothing overwrites the report (#107). A reclassification is a new version or a new report, and the pod keeps
what each lab said, as ClinVar keeps a classification per submitted record and the IG an implication per Observation.
Martin's two reports call one variant uncertain and likely pathogenic, and the page shows both beside ClinVar's row
(#138, case M2).

**Why it is named like any record.** The rubric's first test in `naming.md` names a thing by what its source says
identifies it, and an interpretation is as much a source's statement as its variant is; a view entry, a judgment and
a shared view each cite a record by its name. Its pointer to its variant is a name only where both came in one
document, since a `urn:uuid` is unique within one bundle only; in the story every interpretation points to a variant of
its own report (`conformance/martin-okafor/scripted-input/martin/bridge/E3/bundle/graph.ttl`).

**Why a condition, as VA-spec names it.** A pathogenicity statement's object is a condition in VA-spec, and a report may
state one, a panel's uncertain-significance call none (#107), so it is optional and at most one. We take its name
`objectCondition` and a range of `cascade:ProblemOrDiagnosis`. VA-spec's therapy objects (`objectTherapeutic`) and
`conditionQualifier` are left out: no source carries a therapy statement yet, and this is where to extend. VA-spec 1.1
renamed the property `object`; we keep the 1.0 name, which says what the object is.


**Why the version is attributed to the lab.** Which lab called a variant is what makes two calls of it two statements
rather than one changed value, and the lab is an organisation record (`republishing-sources.md`). PROV-O's
`wasAttributedTo` is the property a judgment names its author by, so "who said what" lists alike over a lab's call and a
person's belief. It is on the version, since a version is what the lab stated, and at most one, since a report that
names two labs does not say which made the call. The story (#138) shows no lab on the page, so no feature rule states
it; the shape case `record-variant-interpretation/two-labs` and the fixture of "What each report says of a variant"
test it (#219).

**Why evidence codes as strings.** A report's ACMG evidence is the criteria it applied, with a strength and whether met,
and VA-spec's ACMG 2015 profile writes each as one string; we copy its pattern so one string says all three. Its
evidence lines, with their own records, wait for a source that needs more than the code.

**Why a coded classification.** A coded concept is what the IG writes and what ACMG/AMP names; a string is what #132
found hard to compare (#107: "written as a code IRI, not a string").

## Alternatives that lost

- **The classification on the variant.** The strongest case: simpler, one record, and it is how a person speaks. It makes two
  labs' calls of one variant two values of one property, and the record would not say who called what.
- **A free string.** The strongest case: it holds any answer a lab writes, including ClinVar's combined and sub-tier
  terms. A coded concept is what the IG writes, and a string is what #132 found hard to compare.
- **ClinGen's ACMG Criterion Value Set (SEPIO:0000395) for the codes.** Looked here, failed because: its values are
  `sepio-clingen` IRIs of the 2018 ClinGen set, which has no strength or not-met values, and VA-spec 1.0 does not use it.
- **VA-spec itself.** Looked here, failed because: it publishes JSON Schema only, no RDF; we take its names and its
  evidence-code string form, not its classes.
- **A condition on every interpretation.** The strongest case: the IG's pair and VA-spec's proposition are variant and
  condition, and ClinVar aggregates per condition. No planted case reads a condition, and showing one beside a person's
  conditions would be the linkage the epic leaves out.
- **An unnamed interpretation, reachable only through its variant.** The strongest case: nothing else points at it, and
  no name has to be minted. `naming.md` names everything, and a judgment or a shared view cites the interpretation itself.
- **A `urn:uuid` reference across documents.** The strongest case: a report that cites a variant held from an earlier
  report would point at it directly. `naming.md` never lets a `urn:uuid` cross documents, and the join it stands for is a
  judgment with its own reason.

## Still open

- Ruled as a direction on 2026-10-22 (#202, the reopening): the interpretation stays a record, because it is the
  source's own signed content, which the rubric's first test keeps as stated, where a judgment is a belief past what a
  source defines; it takes VA-spec's Statement shape (about the variant record; an optional object, a condition or a
  therapy; the classification; optional ACMG evidence codes; a date), and its version is `prov:wasAttributedTo` the
  lab's organisation record, the property judgments use, so "who said what" lists alike over both. The five values are
  `skos:Concept`s of `cascade:ClinVarClassifications`, each `skos:exactMatch` its LOINC answer code; the class that typed
  them a second time is dropped, and the label clash ("Likely Pathogenic" against "Likely pathogenic") fixed, one IRI
  per class. Applied in #219.
- Cases neither the record nor a judgment frame handles, for that build: a somatic variant (AMP/ASCO/CAP tiers, not
  ACMG classes; a pharmacogenomic implication names a drug and a phenotype, not a pathogenicity); a VUS later resolved
  by a reissued report with a new id, which leaves both calls current unless the source declares the replacement.
- Which revision is current follows `currency.md`'s ladder, not `interpretedDate`. The view
  (`views/variant-interpretations.rq`) takes its classification, date and lab from `rec:latestMember`
  (`derivations/latest-members.rq`, by arrival) over `pav:hasCurrentVersion` (`derivations/current-revisions.rq`), the
  derivations `currency.md` replaces, and follows when the ladder and the lead are applied.
- Whom a ClinVar interpretation is attributed to, the SCV's submitter or ClinVar, is left out of #219: the ClinVar
  adapter attributes none. Lean: the submitter, as an organisation record named by its ClinVar organisation id.
  Whether the variant record names its lab too is `variant-record.md`'s.
- How a report reaches a variant it does not restate, held from another document: by a variant record in its own
  document that R12 or R13 joins, or by a term of its own. Lean: the first, since every case in the story points within
  its document.

## What would change our mind

A source that classifies a variant for a condition, with several conditions in one report, would need the condition
back; the follow-up that records what ClinVar said at each version (#135) may change how reclassification chains. A
page that needs the evidence behind a call would bring VA-spec's evidence lines.
