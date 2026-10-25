# The variant record

Status: draft, 2026-10-13; revised 2026-10-22 against `README.md`, from the review on #202. Terms: `genomics:Variant`,
`hgvsCDot`, `clinvarVariationId`, `geneSymbol`. Replaces this note's own "the record is named by its HGVS expression",
which yields to `naming.md`: the rubric's first test names a thing by what its source says identifies it, and that an
expression is a variant is an inference across sources, since two transcripts' expressions are one variant only where a
table says so (`variant-identity.md`). No rule ever named a variant by its expression; the kit's are named by their
source (`conformance/martin-okafor/scripted-input/martin/bridge/E3/bundle/graph.ttl`). Names are `naming.md`; which
revision is current is `currency.md`; the lab behind a report is an organisation record in `republishing-sources.md`;
when two variant records are one is `variant-identity.md`. #193 renames the `genomics/v1#` namespace into the one
unversioned namespace, and #191 the rule terms.

## Question

What does a person's pod hold when a report names a genetic variant, so that a page can show the variant, its gene and
what a table says of it? Two labs report one variant on two transcript versions, years apart, one with a ClinVar ID and
one without; the pod has no server of record to say they are one, and a view the person shares must not need one.

## What others do

- **FHIR Genomics Reporting IG STU3 (v3.0.0, 2024-12-12),** "a product of the HL7 Clinical Genomics Work Group". A
  Variant is an Observation, code LOINC 69548-6. Its components are the c.HGVS description (48004-6), "A valid
  HGVS-formatted 'c.' string, e.g. NM_005228.5:c.2369C>T", bound required to HGVS; the variation code (81252-9), "ClinVar
  ID or similar", example-bound; and the gene studied (48018-6), where "The HGNC gene symbol is to be used as display
  text and the HGNC gene ID used as the code". Its coding appendix gives ClinVar the system
  `http://www.ncbi.nlm.nih.gov/clinvar`, "the variant ID as the code"; HGVS `http://varnomen.hgvs.org`; and HGNC
  `http://www.genenames.org`, "Gene IDs must be sent as codes and begin with 'HGNC:'".
- **HL7 Clinical Genomics Work Group** exists to enable "communication about clinical and personalized genomic data";
  the IG above is its FHIR product.
- **HGVS nomenclature,** administered by the HGVS Variant Nomenclature Committee under HUGO. A description is on a
  reference sequence with a "unique sequence identifier", and "variant descriptions lacking a version number are not
  valid": `NM_004006.3`, never `NM_004006`. So two transcript versions give two expressions of one variant.
- **HGNC** gives every gene "a unique symbol, HGNC ID (in the format HGNC:#)"; the ID "stays the same even if the
  nomenclature is updated", and the symbol may change.
- **ClinVar** gives "a unique integer identifier to each set of variants" (the VariationID; a VCV aggregates every
  submitted record for it), an AlleleID to each single variant, an RCV per variant and condition, and an SCV to each
  submitted record. Its `hgvs4variation` file reports "HGVS expressions ClinVar reports per VariationID and AlleleID",
  with columns marking which a submitter gave. VariationID 90011 has 29 expressions, two of them submitted coding
  expressions and 22 on other transcripts (verified, [#203](https://github.com/jayostis/cascade-vocabulary/issues/203)); of 46,242,796 rows, 5,384,668 are `Submitted` Current and
  1,225 Previous (verified, counted in #107's Step 0 comment).
- **GA4GH VRS** names a variation by a digest of its serialisation: "All valid implementations of the VRS Computed
  Identifier will generate the same identifier when the objects are identical." An allele is located on a sequence
  reference, so the digest needs the reference sequence. **VRSATILE**, "a set of proposed extensions for VRS" for
  "common descriptive data alongside variation concepts", carries labels and HGVS expressions beside the digest; it says
  it is "in a draft state" and "not a GA4GH standard". **Cat-VRS** represents "categorical variant concepts in genomics
  knowledgebases", a class of variants rather than one.
- **ClinGen Allele Registry** gives each canonical allele a CA id with a resolvable URI: "All contextual alleles
  corresponding to a same variant are associated with the same canonical allele", whatever transcript or assembly they
  are written on (Pawliczek et al., 2018).
- **openEHR.** CKM's `openEHR-EHR-CLUSTER.genomic_variant_result.v1` holds one sequencing-test variant, nested in the
  laboratory test result observation's "Test result" slot, as an inline HGVS string and as a structured nested cluster,
  instantiated once per alternative allele. HGVS is identity there; the classification is not in this cluster.
- **SPHN.** A Swiss omics planning page lists `VariantDescriptor` and `VariantNotation` under SPHN 2023.2 as potential
  concepts, and SPHN's 2025.1 release announces "new concepts for the representation of genomic variants"; the released
  schema was not read.
- **OMOP.** The Genomic vocabulary is built from cancer knowledge bases and holds a ClinVar subset, its HGVS strings
  matched against concept names and synonyms; its maintainer writes that it "was born in oncology", with gaps for
  germline and copy number.
- **PROV-O.** A variant record is a `prov:Entity`, as every record here is.

Sources: FHIR Genomics Reporting IG STU3 (https://hl7.org/fhir/uv/genomics-reporting/STU3/, verified), its Variant
profile (https://hl7.org/fhir/uv/genomics-reporting/STU3/StructureDefinition-variant.html, verified) and coding appendix
(https://hl7.org/fhir/uv/genomics-reporting/STU3/codings.html, verified); HL7 Clinical Genomics Work Group
(https://wiki.hl7.org/CG, unverified: read from a search excerpt); HGVS nomenclature
(https://hgvs-nomenclature.org/stable/, verified) and its reference sequences
(https://hgvs-nomenclature.org/stable/background/refseq/, verified); HGNC (https://www.genenames.org/about/, verified;
https://www.genenames.org/about/guidelines/, verified); ClinVar identifiers
(https://www.ncbi.nlm.nih.gov/clinvar/docs/identifiers/, verified) and its tab-delimited files' README
(https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/README, verified); GA4GH VRS (https://vrs.ga4gh.org/en/stable/,
verified) and its computed identifiers
(https://vrs.ga4gh.org/en/stable/conventions/computed_identifiers.html, verified); VRSATILE
(https://vrsatile.readthedocs.io/en/latest/, verified); Cat-VRS (https://cat-vrs.ga4gh.org/en/latest/, verified);
ClinGen Allele Registry (https://reg.clinicalgenome.org/, unverified: the page did not render) and Pawliczek et al.,
Hum Mutat 2018 (https://pmc.ncbi.nlm.nih.gov/articles/PMC6519371/, verified); openEHR
`genomic_variant_result.v1` (https://ckm.openehr.org/ckm/archetypes/1013.1.3759, unverified: the page renders by script,
read from search excerpts); SPHN omics concepts (https://docs.switzerlandomics.ch/pages/data_concepts.html, unverified:
search excerpt) and SPHN 2025.1
(https://sphn.ch/2025/01/17/sphn-releases-the-newest-version-of-the-sphn-semantic-interoperability-framework/,
unverified: search excerpt); OMOP genomic forum thread
(https://forums.ohdsi.org/t/representing-germline-somatic-variants-in-omop-whos-actively-using-the-genomic-cdm-extension/25398,
verified); PROV-O (https://www.w3.org/TR/prov-o/, verified). Research: #107's body
(https://github.com/jayostis/cascade-vocabulary/issues/107) and its Step 0 comment
(https://github.com/jayostis/cascade-vocabulary/issues/107#issuecomment-6139118340); the evidence issue
(https://github.com/jayostis/cascade-vocabulary/issues/203); the scenario #138 (https://github.com/jayostis/cascade-vocabulary/issues/138).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| the variant | FHIR IG Variant, an Observation coded 69548-6; openEHR `genomic_variant_result`; SPHN `VariantDescriptor` | its own record, `genomics:Variant`, a `prov:Entity`, copied with its IRI from the retired spec (d819bc2) (`ontologies/cascade.ttl`) | diverged from FHIR's Observation; the reason is owed (Still open) |
| its name | `naming.md` | named as any record from its source is: a server's by server, type and id; a document's by document and selector; a C-CDA entry's by custodian, patient and id. Never by its HGVS expression (`runtime/naming.feature`, N1) | borrowed from `naming.md` |
| HGVS expression | FHIR c.HGVS component 48004-6; HGVS nomenclature | `hgvsCDot`, at most one per version, in the normal form: a reference sequence with its version (`NM_`, `NG_`, `XM_`, `NC_`, `LRG_`), a colon, `c.` and the change. It is the record's display name and a join key for the identity rules (`ontologies/cascade.shapes.ttl`) | borrowed; one per version is ours |
| ClinVar variation | FHIR variation code 81252-9, ClinVar's variant ID as code; ClinVar VariationID | `clinvarVariationId`, at most one per version, the digits with no leading zero (`ontologies/cascade.shapes.ttl`) | borrowed |
| gene | FHIR gene studied 48018-6: HGNC ID as code, symbol as display; HGNC | `geneSymbol`, at most one per version, the display of the gene-studied coding under HGNC (`http://www.genenames.org/geneId` or `http://www.genenames.org`); never the HGNC ID; with no display a source writes none and records a finding (`ontologies/cascade.shapes.ttl`) | diverged from FHIR's code: the symbol is what a table's gene list states (Why) |
| content | FHIR versions; `naming.md` | on a version; a reclassified or corrected report is a new version (`runtime/naming.feature`, N3) | borrowed from the vocabulary's rule |
| which revision is current | `currency.md` | `currency.md`'s ladder, like any record (`runtime/currency.feature`, C2) | borrowed from `currency.md` |
| status | FHIR `Observation.status` | `clinical:status` (`ontologies/cascade.shapes.ttl`) | borrowed |
| computed identity | GA4GH VRS digest; ClinGen CA id | none (`runtime/matcher.feature`, M17) | diverged: no source states a reference sequence or a CA id (Why) |
| an entry | | shows every member's codes (`queries/views/variants.rq`) | ours |

## Why

**Why a name from the source and not the expression.** (row "its name") The rubric's first test in `naming.md` names a thing by what its
source says identifies it. A report says which record it holds by its server and id, or its document and position; it
does not say its expression identifies a variant, and HGVS itself makes two transcript versions two expressions. That two
expressions are one variant is a judgment, filed by a rule that reads a table (`variant-identity.md`), so it can be wrong
and be retracted without touching a name. An expression is not even unique to one variation: 195 of 3,304,067 submitted
coding expressions map to two VariationIDs across the 2026-10 file, and 3 within Lynch's five genes (both verified,
[#203](https://github.com/jayostis/cascade-vocabulary/issues/203)).

**Why these three codes.** (rows "HGVS expression", "ClinVar variation", "gene") They are what a report states and what a page looks a variant up by. The ClinVar VariationID
is the code the IG puts in its variation component and the key of ClinVar's rows; the HGVS expression is the IG's
required c.HGVS component; both are copied as #107 asked ("Copy only what the story uses"). The normal form keeps the
reference sequence's version, which HGVS requires, and drops the gene in parentheses, which is not part of the
expression.

**Why the gene is a symbol.** (row "gene") A variant classifications table states the genes it covers by symbol (`rec:coversGene`,
`records.ttl:431`; `rec:coversGene "MLH1"` in `runtime/scripted-input/ivo/tables/app-variants/references.ttl:57`), and the page tells "not covered" from "not found" by comparing them (#107, "`geneSymbol`,
which the page needs to tell 'not covered'"; #138, case M4). ClinVar's files carry the symbol too. `hgncId` waits, with
`zygosity`, `genomeAssembly` and `transcriptRef`, for a planted case that reads it (#107).

**Why no computed identity.** (row "computed identity") A VRS digest needs the reference sequence, which neither ClinVar's `variant_summary` nor a
browser has (#107), and no report in the story states one; nor does any carry a CA id (#138's inputs carry an HGVS
expression, a ClinVar ID where they have one, and a gene). So the join keys are the ClinVar VariationID and the HGVS
expression as written, exact.

## Alternatives that lost

- **The record named by its HGVS expression.** The strongest case: two reports of one expression would be one record
  with no judgment, and the expression is what a person reads. It names by inference: an expression is a variant only
  where a table says so, 195 expressions name two variations, and a name that a table decides cannot be retracted.
- **VRS identifiers as the key.** The strongest case: one identity from any source, no string matching, and a GA4GH
  standard. It needs the reference sequence to compute, which neither ClinVar's `variant_summary` nor a browser has, and no
  source in the story states one.
- **ClinGen CA ids as the key.** The strongest case: the registry canonicalises every transcript and assembly to one id,
  which is exactly what two transcripts' expressions need. No report in the story carries one, and the table built from
  ClinVar already lists the expressions submitters used under one VariationID.
- **The gene as an HGNC ID.** The strongest case: it is what the IG codes, and it never changes when a symbol is renamed.
  The table's gene list, ClinVar's `GeneSymbol` and a person reading a page all use symbols, and no planted case reads the
  ID.
- **Several expressions on a version.** The strongest case: a report may state several transcripts, and the IG's
  component repeats. Two expressions on one version would let one record claim two variants; a second transcript is a
  second report, and the rules join them.

## Still open

- Ruled as a direction on 2026-10-22 (#202, the reopening): the variant stays its own class, and gains what every
  standard's finding has and this record lacks: a performer (the lab's organisation record), an effective date, the
  specimen where given, the reference build, zygosity (the kit's reports send it on every variant and the pod keeps
  none of it), and whether it is germline or somatic. Not a FHIR Observation subclass: it would share one code with
  every variant, the lab-result rules would have to exclude it, and a germline fact would sit on a time axis. Applied
  in the genomics build.
- Cases for that build: a somatic variant, which R12 and R13 would merge with a germline finding of the same ClinVar
  id, and whose allele fraction over time is an observation the model lacks; two findings of one variant from one lab
  on two dates, right to join when germline and wrong when somatic.
- Which revision of a variant is current follows `currency.md`'s ladder: the queries that read a variant
  (`views/variants.rq`, `matcher/same-variation.rq`, `matcher/same-variation-through-table.rq`) read
  `pav:hasCurrentVersion`, which `derivations/current-revisions.rq` derives by it (`runtime/currency.feature`, C2).
- The lab that reported a variant is an organisation record (`republishing-sources.md`); the variant does not say which
  lab reported it, and whether it should, or only its interpretation should (`variant-interpretation.md`), is open.
- "With no display a source writes none and records a finding": no finding term here says so. It may be the adapter's,
  as a gap in its own report, rather than the vocabulary's.

## What would change our mind

A source that states a reference sequence or a CA id for every variant it reports, or a runtime that can compute VRS
digests in the browser, would make that the better join key. A table that states its genes by HGNC ID would bring the ID
back.
