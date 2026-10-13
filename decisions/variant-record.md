# The variant record

Status: draft, 2026-10-13. Terms: `genomics:Variant`, `hgvsCDot`, `clinvarVariationId`, `geneSymbol`.

## Question

What does a person's pod hold when a report names a genetic variant, so that a page can show the variant, its gene and
what a table says of it?

## What others do

- **FHIR Genomics Reporting IG STU3 (v3.0.0).** A Variant is an Observation, LOINC 69548-6. Its components are the
  c.HGVS description (48004-6), the variation code in a variant database such as ClinVar (81252-9, example-bound) and the
  gene studied (48018-6), which is an HGNC ID coded under `http://www.genenames.org/geneId`; the symbol is the coding's
  display, when it has one.
- **GA4GH VRS.** The variant is a computed identifier, a digest of a canonical form of its allele on a reference
  sequence, so the same variant has the same identifier from any source.
- **openEHR.** CKM's `openEHR-EHR-CLUSTER.genomic_variant_result.v1`
  (https://ckm.openehr.org/ckm/archetypes/1013.1.3759) holds one sequencing-test variant, nested in the laboratory test
  result observation's "Test result" slot. It records the variant as an inline HGVS string and as a structured nested
  cluster, and is instantiated once per alternative allele. HGVS is identity there as here; the classification is not in
  this cluster (checked 2026-10 on the archetype's page and search results only).
- **OMOP.** The Genomic vocabulary (OHDSI symposium 2022, Gurley and Golozar) is built from cancer knowledge bases
  (CGI, CIViC, a ClinVar subset, JAX, NCIt, OncoKB) and holds a ClinVar subset only, because over 500,000 ClinVar
  variants would slow the relational model; its HGVS strings are matched against concept names and synonyms,
  case-insensitively. A forum post (https://forums.ohdsi.org/t/representing-germline-somatic-variants-in-omop-whos-actively-using-the-genomic-cdm-extension/25398)
  says it was born in oncology, with germline and copy-number gaps. The Genomic CDM extension's current status is unclear
  and no official specification was found.
- **SPHN.** Unverified: the Swiss omics notes list `VariantDescriptor` and `VariantNotation` in SPHN 2023.2 as potential
  concepts; the released schema was not checked.

## Choice

A variant is its own record, `genomics:Variant`, copied with its IRI from the retired spec (d819bc2). Its version holds at
most one HGVS coding expression (`hgvsCDot`, in the normal form, one of `NM_`, `NG_`, `XM_`, `NC_` and `LRG_`), at most
one ClinVar VariationID (`clinvarVariationId`, the digits without a leading zero) and at most one gene symbol
(`geneSymbol`, the HGNC approved symbol). The record is named by its HGVS expression and takes `clinical:status`.
An entry shows every member's codes. The gene symbol is the display of the gene-studied coding under the HGNC system
(`http://www.genenames.org/geneId` or `http://www.genenames.org`); the HGNC ID never goes in `geneSymbol`, and with no
display a source writes none and records a finding.

## Why

The terms are the ones a report states, and a page looks a variant up by exactly them. Content is on a version, so a
reclassified or corrected report is a new version. Copying keeps the IRI the adapters already used.

## Alternatives that lost

- **VRS identifiers as the key.** The strongest case: one identity from any source, no string matching. It needs the
  reference sequence to compute, which neither ClinVar's `variant_summary` nor a browser has, and no source in the story
  states one.
- **The gene as an HGNC ID.** It is what the IG codes, and it never changes when a symbol is renamed. The series' gene
  lists, ClinVar's `GeneSymbol` and a person reading a page all use symbols.
- **Several expressions on a version.** A report may state several transcripts. Two expressions on one version would let
  one record claim two variants; a second transcript is a second report, and the rules join them.

## What would change our mind

A source that states a reference sequence for every variant it reports, or a runtime that can compute VRS digests in the
browser, would make the digest the better key.
