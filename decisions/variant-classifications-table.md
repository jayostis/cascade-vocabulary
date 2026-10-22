# The variant classifications table

Status: draft, 2026-10-13, brought to the `README.md` standard on 2026-10-22 under #202. Terms:
`rec:VariantClassifications`, its row properties, `rec:readByPages`, `rec:coversGene`, the schemes
`rec:ClinVarClassifications` and `rec:ClinVarReviewStatuses`. Depends on `naming.md` (how a table version is named,
and what a judgment's used holds), `variant-identity.md` (R13, the identity rule that reads the rows),
`hgvs-and-clinvar-codes.md` (the IRIs a row is found by), and the evidence issue
[#203](https://github.com/jayostis/cascade-vocabulary/issues/203). #193 will move the `rec:` and `genomics:` terms into
the one unversioned Cascade namespace.

## Question

How does a pod's app hold what ClinVar says of a variant today, in a form the matcher and the page both read, at a size a
browser keeps? The app has no server to ask: it keeps whole versions of the table on the device, ClinVar publishes a new
one monthly, the matcher joins two reports through a row while a page shows the same row, and a report may name its
variant by an expression, by a ClinVar ID, or both.

## What others do

- **ClinVar** publishes `variant_summary`, where "The data for the variant are reported for each assembly", generated
  weekly and archived monthly; its `ClinicalSignificance` is a "semicolon-separated list of aggregate values of germline
  classification" (verified, README). The 2026-10 release holds 4,646,126 variations (verified,
  [#203](https://github.com/jayostis/cascade-vocabulary/issues/203)). It publishes `hgvs4variation`, "HGVS expressions
  ClinVar reports per VariationID and AlleleID", updated weekly and not archived (verified, README), whose `Submitted`
  column says an expression "was used by a submitter", `Current` or `Previous`, and takes `No` as well (verified, #203).
- **ClinVar's value set.** Its germline terms are the five ACMG/AMP terms with sub-tiers VUS-high, VUS-mid and VUS-low,
  ClinGen's low-penetrance and risk-allele terms, and drug response, association, protective, Affects, other and not
  provided. Terms that do not conflict are joined with "/", others appended with ";", and disagreement is "Conflicting
  classifications of pathogenicity" (verified, clinsig page). The 2026-10 release writes 107 distinct values (verified,
  #203). The label changed from "interpretations" to "classifications" between the 2024-01 and 2024-06 releases
  (verified for variation 90011 across eight archived releases; for every value inferred, #203); ClinVar dates a split of
  the field to "the January 29, 2024 release" (verified, clinsig page).
- **ClinVar's review statuses** are graded zero to four stars, from "no assertion criteria provided" to "practice
  guideline" (verified). The page writes "no classification for the individual variant" and lists no "no
  classifications from unflagged records"; the file writes "no classification for the single variant" and both values,
  in both `ClinicalSignificance` and `ReviewStatus`, with equal counts per gene list (verified, page and #203).
- **ACMG/AMP (Richards et al. 2015)** recommends "'pathogenic', 'likely pathogenic', 'uncertain significance', 'likely
  benign', and 'benign'" (verified).
- **FHIR.** R4's `Observation.interpretation` is "A categorical assessment of an observation value. For example, high,
  low, normal" (verified); the Genomics Reporting IG STU3 does not put a classification there but on a Diagnostic
  Implication, component 53037-8, example-bound to LOINC answer list LL4034-6, "Pathogenic | Likely pathogenic |
  Uncertain significance | Likely benign | Benign" (verified). The answer codes are in `variant-interpretation.md`
  (unverified here: loinc.org refused the fetch).
- **ClinGen's Evidence Repository** is an "FDA-recognized human genetic variant database" of "expert-curated
  assertions regarding variants' pathogenicity" (verified); ClinVar archives "the results of interpretation by
  recognized expert panels" (verified, HL7 Terminology's ClinVarV), which it shows as "reviewed by expert panel".
- **OMOP's Genomic vocabulary** holds a ClinVar subset only, for size (see `variant-record.md`). **openEHR** has no table
  (not re-checked).
- **SKOS.** A concept scheme is "an aggregation of one or more SKOS concepts", and "there are no conditions preventing
  a SKOS concept from taking part in zero, one, or more than one concept scheme"; a notation "is used to uniquely
  identify a concept within the scope of a given concept scheme" (verified).
- **Gene coverage and a page-read marker.** None of the above says which genes a release of a table covers, or marks a
  kind an app keeps though no rule reads it. Nothing found.

Sources: ClinVar's tab-delimited files and README (https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/README,
https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/), its classification terms
(https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/) and review statuses
(https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/); Richards et al., "Standards and guidelines for the
interpretation of sequence variants", *Genetics in Medicine* 17 (2015) (https://pmc.ncbi.nlm.nih.gov/articles/PMC4544753/);
FHIR R4 `Observation.interpretation` (https://hl7.org/fhir/R4/observation-definitions.html#Observation.interpretation);
Genomics Reporting IG STU3 Diagnostic Implication
(https://hl7.org/fhir/uv/genomics-reporting/STU3/StructureDefinition-diagnostic-implication.html); LOINC LL4034-6
(https://loinc.org/LL4034-6/, unverified); HL7 Terminology ClinVarV (https://terminology.hl7.org/NamingSystem-ClinVarV.json);
ClinGen Evidence Repository (https://erepo.clinicalgenome.org/evrepo/); SKOS Reference §4 and §6
(https://www.w3.org/TR/skos-reference/); GA4GH VRS (https://vrs.ga4gh.org/en/stable/) for the identifier set aside; OMOP
as cited in `variant-record.md`. The counts, the scripts and the archived classification values are the evidence issue
(https://github.com/jayostis/cascade-vocabulary/issues/203), from #107's epic and its Step 0
(https://github.com/jayostis/cascade-vocabulary/issues/107#issuecomment-6139118340).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| the table kind | ClinVar's two files: `variant_summary`, a line per variation and assembly; `hgvs4variation`, a line per expression | one kind, `rec:VariantClassifications`: a row per variation, found by its variation IRI (`rec:RowSubject`) and by each coding `NM_` expression a submitter used (`rec:hgvsExpression`) | diverged: one row from both files, so a report with only an expression finds its classification in one lookup; a row per variation, since the classification is per variation (#107) |
| which expressions | `hgvs4variation`'s `Submitted` column | those with `Submitted` `Current` or `Previous` | the column borrowed; diverged from carrying every expression, for size (Why) |
| what a row holds | `variant_summary`'s `ClinicalSignificance`, `ReviewStatus`, `LastEvaluated`, `NumberSubmitters`, `SCVsForAggregateGermlineClassification` | its classification concepts, review status, the day last evaluated, and `rec:contributingSubmitters` or `rec:submitters`, never both, so the row says which count it has | borrowed |
| conditions | ClinVar's RCV, a variant and a condition; the IG's Diagnostic Implication | none | diverged: no planted case reads them, they are the row's longest field, and beside a person's conditions they would be the linkage #107 leaves out |
| the classification values | ClinVar's grammar; the ACMG/AMP terms; LOINC LL4034-6 | parsed into concepts by four rules: the whole value `-`; split on `; ` then `/`, never on `,`; exact match on a concept's label with case kept; an unmatched term is a finding, never a refused build. The five ACMG concepts are the copied `genomics:` individuals, labelled as ClinVar spells them in `records.ttl`, with the LOINC answer code as `skos:exactMatch` | the terms and the grammar borrowed; diverged from the IG's one coded value per observation, since a ClinVar value may hold several terms |
| the schemes | SKOS concept schemes | `rec:ClinVarClassifications` and `rec:ClinVarReviewStatuses`, each concept a `skos:Concept` with its label as ClinVar writes it and `skos:altLabel` for a renamed one; `-` is `rec:ClinVarCombinationOnly`, whose preferred label is the sentence a page shows and whose notation is the hyphen | borrowed |
| a value in both columns | SKOS: a concept in more than one scheme | `rec:ClinVarNoClassificationForTheSingleVariant` and `rec:ClinVarNoClassificationsFromUnflaggedRecords` are one IRI each, in both schemes | borrowed; ClinVar writes each in both columns |
| gene coverage | nothing found | `rec:coversGene` on the version, an HGNC symbol, any number including none; a changed gene list is a new version; a version without it covers no named gene | ours |
| kinds an app keeps for its pages | nothing found | `rec:readByPages true` marks the kinds an app keeps and packs because its pages read them, though no rule does: `rec:CodeNames`, `rec:CodeStatus`, `rec:VariantClassifications`, `rec:PanelMembers` and `rec:DrugClasses` (`records.ttl`); it replaces the set a runtime hard-coded | ours |
| a row whose classification parses to no concept | | keeps its keys | ours: the join through a row is identity and reads no classification |
| versions an app keeps | ClinVar archives `variant_summary` monthly | R13 counts over current versions only (`variant-identity.md`), so an old version's rows may be dropped; a new version re-mints only the claims whose joining rows changed in it (M7) | ours |

## Why

**Why one row per variation, found two ways.** A report may carry only an expression, only an ID, or both. With a row
found by either, each finds its classification in one lookup, and two tables cannot disagree on the variation. The row
is per variation because ClinVar's classification is: `variant_summary` repeats it on each assembly's line, and some
variations have no GRCh38 line (#107). Variation 90011's GRCh37 and GRCh38 lines are identical in eight archived
releases (verified for 90011; for every variation inferred,
[#203](https://github.com/jayostis/cascade-vocabulary/issues/203)).

**Why only the expressions a submitter used.** A report cites what a lab wrote (#107), and the rest is size. Keeping
the submitted expressions cuts variation 90011 from 29 expressions to 2, and Lynch's variations from 692,290 coding
expressions to 34,405 (both verified, #203). Every expression would break the keep bounds even for Lynch: 2.24 GB at
the first check, against 0.60 GB for the submitted ones (verified, Step 0, one laptop, N = 3; #203).

**Why a grammar mapped to concepts.** ClinVar writes 107 distinct values in one release (verified, #203), built from
a short list of terms, and renamed a label in 2024. Mapping each term to a concept survives the rename through an
alternative label, and a combination ClinVar has not written yet still parses.

**Why one concept in both schemes.** ClinVar writes "no classification for the single variant" and "no
classifications from unflagged records" in both `ClinicalSignificance` and `ReviewStatus`, with equal counts in every
gene list (verified, #203), so each is one statement, not two.

**Why no conditions.** They are the row's longest field, no planted case reads them, and showing them beside a person's
conditions would be the linkage #107 leaves out.

**Why the genes sit on the version.** A page can then tell "not covered" from "not found" without reading the series,
which carries no content. A series is described once, on first publish, and a runtime keeps only the series fields it
lists (#139), so a changed gene list can only be a new version.

**Why current versions only.** A page and R13 both ask what ClinVar says today. Held for the count, a monthly 0.60 GB
version is 72 GB in ten years (computed, [#206](https://github.com/jayostis/cascade-vocabulary/issues/206)), against
a browser's keep bounds.

**Why a marker, not a list.** A runtime that hard-codes the kinds its pages read changes for every new kind a page
reads; a marker in the vocabulary changes none.

## Alternatives that lost

- **A separate HGVS table.** The strongest case: each table is one thing. A report with only an expression then needs two
  lookups, and the two tables could disagree on the variation.
- **Every coding expression as a key.** The strongest case: a report on any transcript finds its row; by HGVS it finds
  32,085 of Lynch's variations against 24,621 (verified, Step 0, #203). It is 3.8 times the lines and breaks the keep
  bounds even for Lynch.
- **Mapping whole strings.** The strongest case: it is the simplest to write and needs no parser. A value such as
  "Pathogenic/Likely pathogenic/Pathogenic, low penetrance" would need its own row for every combination ClinVar writes,
  and a new combination would be unmapped.
- **Conditions in the row.** The strongest case: the IG pairs variant and condition, and ClinVar aggregates per
  condition in an RCV. No planted case reads them, and they would be the linkage #107 leaves out.
- **The genes on the series.** The strongest case: a series' gene list is one fact, said once. A series is described
  once, on first publish, and a runtime keeps only the series fields it lists; a changed gene list could not be a new
  version.
- **A hard-coded list of the kinds an app keeps.** The strongest case: no vocabulary term, and the runtime already knows
  what its pages read. It was the state before; every new kind a page reads would change a runtime.
- **Every held version counted by R13.** The strongest case: an expression ClinVar ever put on two rows stays left
  alone. Every version is then kept, 72 GB of ClinVar in ten years (computed, #206).
- **Every table-reading claim re-minted per adopted version (M7).** The strongest case: each claim names the version it
  was last read under. About 960k claims in ten years for rows that did not change (assumed monthly adoption, #206).

## Still open

- `rec:coversGene` is defined, shaped and written on each version a host publishes, but no query reads it, so "not
  covered" against "not found" is never exercised: kit M4 checks only that the code joins nothing. #202 asks for a
  query and a kit expectation, or for the ruling to move here.
- The table version is named by `urn:uuid` in the kit, where `naming.md` says nothing else a runtime mints is random.
  #191 changes it.
- Which revision of a variant record is current when R13 and the table queries read its codes: they read the
  derivation `currency.md` replaces.
- The row's keys. #139 settled them as the submitted expressions plus the one in the variation's own ClinVar name, which
  raises Lynch's variations found by HGVS from 74.7% to 97.0% (verified, Step 0, #203); this note and `records.ttl`'s
  comment on `rec:VariantClassifications` say submitted only. Which is ruled is owed.
- The two-VariationIDs guard. 195 of 3,304,067 submitted coding expressions name two variations across the whole file
  (verified, #203), but the guard as settled counts every `NM_` row and every variation's name expression, which nobody
  has counted (unverified, #203).
- ClinVar's review-status page and its file spell one value two ways ("individual", "single"); whether the scheme takes
  the page's as an alternative label.

## What would change our mind

A larger gene list than the one fitting a browser's heap (jayostis/cascade-runtime-js#231), a source whose rows need more
than identity and a classification, a planted case that reads a condition, or a page that reads a kind no rule names
and is not worth marking.
