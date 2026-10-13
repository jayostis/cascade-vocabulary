# The variant interpretation

Status: draft, 2026-10-13. Terms: `genomics:VariantInterpretation`, `acmgClassification`, `variantInterpreted`,
`interpretedDate` and the class `AcmgClass` with `Pathogenic`, `LikelyPathogenic`, `VUS`, `LikelyBenign`, `Benign`.

## Question

Where does a report's classification of a variant live, and what is its shape, so that a page can show what each report
said beside what a table says today?

## What others do

- **FHIR Genomics Reporting IG STU3 (v3.0.0).** The classification is a component of a Diagnostic Implication
  (53037-8), a separate Observation that `derivedFrom` the Variant. Its value is a coded concept, a LOINC answer code
  (LA6668-3, LA26332-9, LA26333-7, LA26334-5, LA6675-8 for the five ACMG values). Its `issued`, else `effective[x]`, is
  the date.
- **GA4GH VA-spec.** A classification is a statement of its own: a proposition about a variant, a classification, and
  the evidence and the agent behind it.
- **openEHR.** The sequencing-test variant cluster (`genomic_variant_result.v1`) does not hold the classification
  (checked 2026-10 on the archetype's page only); it is not in the cluster.
- **OMOP.** The Genomic vocabulary holds variants and knowledge-base concepts; a classification is not a patient-level
  record there (the extension's status is unclear).
- **SPHN.** Unverified.

## Choice

A report's classification is its own record, `genomics:VariantInterpretation`, pointing to the variant record it is
about by that record's IRI, as `rec:patient` points to its profile record; the record may be outside the document it
came from. It states at most one ACMG value from the five copied individuals, at most one `xsd:date`
(`interpretedDate`, the Diagnostic Implication's `issued`, else the date of `effective[x]`), and takes
`clinical:status`. A report whose answer is not one of the five states no `acmgClassification`. It is unnamed. The
source's condition requirement is dropped: a panel's uncertain-significance call may name none.

## Why

The report's classification is the record's content and a table's is the table's; nothing overwrites the report. A
reclassification is a new version or a new report, and the pod keeps what each lab said.

## Alternatives that lost

- **The classification on the variant.** Simpler, and it is how a person speaks. It makes two labs' calls of one variant
  two values of one property, and the record would not say who called what.
- **A free string.** It would hold any answer. A coded concept is what the IG writes, and a string is what #132 found
  hard to compare.
- **A condition on every interpretation.** The IG's pair is variant and condition. No planted case reads a condition,
  and showing one beside a person's conditions would be the linkage the epic leaves out.

## What would change our mind

A source that classifies a variant for a condition, with several conditions in one report, would need the condition
back; the follow-up that records what ClinVar said at each version (jayostis/cascade-vocabulary#135) may change how
reclassification chains.
