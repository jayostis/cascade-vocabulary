# The variant classifications table

Status: draft, 2026-10-13. Terms: `rec:VariantClassifications`, its row properties, `rec:readByPages`, `rec:coversGene`,
the schemes `rec:ClinVarClassifications` and `rec:ClinVarReviewStatuses`.

## Question

How does a pod's app hold what ClinVar says of a variant today, in a form the matcher and the page both read, at a size a
browser keeps?

## What others do

- **ClinVar** publishes `variant_summary` (a line per variation and assembly, about 4.6 million variations) and
  `hgvs4variation` (the expressions of each variation, with `Submitted` and `UsedForNaming`). Its classification values are
  a grammar: ACMG terms joined with `/`, other terms with `;`, and a label renamed from "interpretations" to
  "classifications" between the 2024-01 and 2024-06 releases.
- **FHIR's IG** carries the classification as a coded concept.
- **OMOP's Genomic vocabulary** holds a ClinVar subset only, for size (see `variant-record.md`).
- **openEHR** has no table.

## Choice

- One table kind: a row per variation, found by its variation IRI (`rec:RowSubject`) and by each coding `NM_` expression
  a submitter used (`rec:hgvsExpression`). A row holds its classification concepts, review status, the day last
  evaluated, and `rec:contributingSubmitters` or `rec:submitters`, never both, so the row says which count it has.
  No conditions.
- Classification values are parsed into concepts by four rules (the whole value `-`; split on `; ` then `/`, never on
  `,`; exact match on a concept's label with case kept; an unmatched term is a finding, never a refused build). The
  five ACMG concepts are the copied `genomics:` individuals, labelled as ClinVar spells them in `records.ttl`, with the LOINC
  answer code as `skos:exactMatch`. `-` is `rec:ClinVarCombinationOnly`, whose preferred label is the sentence a page
  shows and whose notation is the hyphen. Two concepts, `rec:ClinVarNoClassificationForTheSingleVariant` and
  `rec:ClinVarNoClassificationsFromUnflaggedRecords`, are one IRI each in both schemes, because ClinVar writes each value
  in both columns.
- `rec:coversGene` is on the version, as an HGNC symbol, any number; a changed gene list is a new version. A version of
  the kind states at least one. A version without it covers no named gene.
- `rec:readByPages true` marks the kinds an app keeps and packs because its pages read them, though no rule does:
  `rec:CodeNames`, `rec:CodeStatus` and `rec:VariantClassifications`. It replaces the set a runtime hard-coded.
- A row whose classification parses to no known concept keeps its keys: the join is identity.

## Why

The row holds what a page shows and no more: keeping only the expressions a submitter used cuts the variation 90011 from
29 expressions to 2, and Lynch's variations from about 700,000 coding expressions to 34,428. A classification grammar
mapped to concepts survives a renamed label. The genes sit on the version so a page can tell "not covered" from "not found"
without reading the series, which carries no content.

## Alternatives that lost

- **A separate HGVS table.** The strongest case: each table is one thing. A report with only an expression then needs two
  lookups, and the two tables could disagree on the variation.
- **Mapping whole strings.** It is simplest to write. A value such as "Pathogenic/Likely pathogenic/Pathogenic, low
  penetrance" would need its own row for every combination ClinVar writes.
- **The genes on the series.** A series is described once, on first publish, and a runtime keeps only the series
  fields it lists; a changed gene list could not be a new version.
- **A hard-coded list of the kinds an app keeps.** It was the state before; every new kind a page reads would change a
  runtime.

## What would change our mind

A larger gene list than the one fitting a browser's heap (jayostis/cascade-runtime-js#231), a source whose rows need more
than identity and a classification, or a page that reads a kind no rule names and is not worth marking.
