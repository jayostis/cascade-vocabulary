# The HGVS and ClinVar code systems, and encoding a code

Status: draft, 2026-10-13, brought to the `README.md` standard on 2026-10-22 under #202. Terms: `rec:HGVS`,
`rec:ClinVar`, `rec:HgvsCodeShape`, `rec:ClinVarCodeShape`; rule M4. Depends on `naming.md` (how everything in a
pod is named) and `judgments.md` (the identity rules R12 and R13 that join on these IRIs, per
`variant-identity.md`); the counts are the evidence issue
[#203](https://github.com/jayostis/cascade-vocabulary/issues/203). #193 will move the `rec:` terms into the one
unversioned Cascade namespace; the stems are not Cascade IRIs and do not move.

## Question

What are the IRIs of an HGVS expression and a ClinVar variation, and what does it mean that a literal "joins as its
IRI" when the literal holds characters an IRI cannot? A pod has no server to normalise a code: the builder that writes
a table's rows and every runtime that reads a report's codes must each turn one literal into one IRI, byte for byte,
or a row and a record never meet.

## What others do

- **The HGVS Nomenclature** (version 21.1, at hgvs-nomenclature.org) writes an expression as a reference sequence, a
  prefix and the change: `NM_` is a "coding transcript", "coding DNA reference sequences are indicated using a `c.`
  prefix", and "variant descriptions lacking a version number are **not** valid". Its 2024 paper says the nomenclature
  "is transitioning to the use of Extended Backus-Naur Form (EBNF)", recommends MANE Select transcripts "where
  possible", and that "Previous names — Mutnomen, VarNomen, and HGVS Recommendations — are discouraged". The host
  `varnomen.hgvs.org` no longer resolves (verified 2026-10-22: no DNS answer).
- **HL7 Terminology** registers a system URI for each and an IRI stem for neither: HGVS is `http://varnomen.hgvs.org`
  (NamingSystem v3-hgvs, OID 2.16.840.1.113883.6.282) and ClinVar is `http://www.ncbi.nlm.nih.gov/clinvar`
  (NamingSystem ClinVarV, "ClinVar Variant ID", OID 2.16.840.1.113883.6.319). Where it registers a stem, it is a
  unique id of type `iri-stem`, as LOINC's `http://loinc.org/rdf/` (all verified, from the NamingSystem JSON).
- **FHIR RDF** builds a concept IRI from a stem and says "If no IRI Stem is defined for s in the HL7 Terminology
  website, then conceptIRI is undefined. Halt." Its example table names ICD-10, SNOMED CT, MeSH and LOINC, and
  neither HGVS nor ClinVar (verified, R5 and the current build).
- **FHIR Genomics Reporting IG STU3 (3.0.0).** The Variant's c.HGVS component, 48004-6, takes "A valid HGVS-formatted
  'c.' string", bound (required) to a value set including the system `http://varnomen.hgvs.org`; its variation code,
  81252-9, is an "Accession number in a variant database such as ClinVar", example-bound. Its examples write
  `NM_002528.7:c.728G>A` under `http://varnomen.hgvs.org` and the ClinVar variation as digits, `962538`, under
  `http://www.ncbi.nlm.nih.gov/clinvar` (verified).
- **ClinVar** gives "a unique integer identifier to each _set_ of variants", the Variation ID. A VCV accession is it
  with "VCV and a number of zeros to equal nine digits", so "the Variation ID can be used in lieu of the VCV accession
  number"; a VCV's version rises when its record's content changes. An RCV aggregates a variant and a condition, an
  SCV is one submitted record, and an Allele ID shares the Variation ID's numbering, "so it is important to note the
  context of any integer identifier" (verified). `hgvs4variation`'s header says the Variation ID is "used to build the
  URL, namely https://ncbi.nlm.nih.gov/clinvar/VariantID" (verified, #203); the page that answers is
  `https://www.ncbi.nlm.nih.gov/clinvar/variation/90011/`, and `…/clinvar/90011/` returns 404 (verified 2026-10-22).
- **ClinGen's Allele Registry** runs "a canonicalization service, which groups variant identifiers denoting the same
  nucleotide variant and assigns unique and dereferenceable CAids", across assemblies and transcripts; a CA id is
  looked up through the registry's site or its API (verified, Pawliczek 2018).
- **GA4GH VRS** computes an identifier from the variant itself, `ga4gh:VA.` and a truncated SHA-512 of the normalised
  object, whose location names its reference sequence by digest (verified).
- **SPARQL 1.1's `ENCODE_FOR_URI`** "corresponds to the XPath fn:encode-for-uri function", under which "All characters
  are escaped except those identified as 'unreserved' by [RFC 3986]", with hexadecimal "using the upper-case letters
  A-F" (verified). **RFC 3986 §2.3** defines `unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~"`, and §2.1 says
  producers "should use uppercase hexadecimal digits for all percent-encodings" (verified).
- **JavaScript's `encodeURIComponent`** escapes all characters except "A–Z a–z 0–9 - _ . ! ~ * ' ( )" (verified, MDN),
  so it leaves five that `ENCODE_FOR_URI` encodes.
- **This vocabulary** gives CVX, RxNorm and ICD-10-CM the system URI followed by a slash where HL7 Terminology registers
  no stem.

Sources: HGVS Nomenclature (https://hgvs-nomenclature.org/stable/), its reference sequences
(https://hgvs-nomenclature.org/stable/background/refseq/), and Hart et al., "HGVS Nomenclature 2024", *Genome
Medicine* 16 (2024) (https://pmc.ncbi.nlm.nih.gov/articles/PMC11660784/); HL7 Terminology NamingSystems v3-hgvs
(https://terminology.hl7.org/NamingSystem-v3-hgvs.json), ClinVarV
(https://terminology.hl7.org/NamingSystem-ClinVarV.json) and v3-loinc
(https://terminology.hl7.org/NamingSystem-v3-loinc.json); FHIR RDF, Appendix 1 (https://hl7.org/fhir/R5/rdf.html,
https://build.fhir.org/rdf.html); Genomics Reporting IG STU3 Variant
(https://hl7.org/fhir/uv/genomics-reporting/STU3/StructureDefinition-variant.html), its HGVS value set
(https://hl7.org/fhir/uv/genomics-reporting/STU3/ValueSet-hgvs-vs.json) and an example
(https://hl7.org/fhir/uv/genomics-reporting/STU3/Observation-NTHL1-snv-var.json); ClinVar identifiers
(https://www.ncbi.nlm.nih.gov/clinvar/docs/identifiers/); Pawliczek et al., "ClinGen Allele Registry links information
about genetic variants", *Human Mutation* 39 (2018) (https://pmc.ncbi.nlm.nih.gov/articles/PMC6519371/); VRS computed
identifiers (https://vrs.ga4gh.org/en/stable/conventions/computed_identifiers.html); SPARQL 1.1 §17.4.3.11
(https://www.w3.org/TR/sparql11-query/#func-encode) and XPath and XQuery Functions 3.1 §6.2
(https://www.w3.org/TR/xpath-functions-31/#func-encode-for-uri); RFC 3986 §2.1 and §2.3
(https://www.rfc-editor.org/rfc/rfc3986#section-2.3); `encodeURIComponent`
(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent). The counts are
in the evidence issue (https://github.com/jayostis/cascade-vocabulary/issues/203).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| HGVS code system | HL7 Terminology v3-hgvs; FHIR RDF's stem rule | `rec:HGVS`, stem `http://varnomen.hgvs.org/`, `skos:exactMatch <http://varnomen.hgvs.org>` | system URI borrowed; the stem is ours, where FHIR RDF leaves the IRI undefined, by the convention for CVX, RxNorm and ICD-10-CM |
| ClinVar code system | HL7 Terminology ClinVarV; the IG's digits | `rec:ClinVar`, stem `http://www.ncbi.nlm.nih.gov/clinvar/`, `skos:exactMatch <http://www.ncbi.nlm.nih.gov/clinvar>`, then the digits | system URI and digits borrowed; the stem is ours, as above, and is not ClinVar's page URL (`/clinvar/variation/{id}/`) |
| a literal joining as an IRI | `ENCODE_FOR_URI`; RFC 3986 §2.3 and §2.1 | the stem, then the literal through `ENCODE_FOR_URI`: every character but `A-Z a-z 0-9 - _ . ~` as `%` and two upper-case hexadecimal digits of its UTF-8; `NM_000249.4:c.2042C>T` is `http://varnomen.hgvs.org/NM_000249.4%3Ac.2042C%3ET`; M4 and `rec:CodeSystem` say so, and the question queries and R13 encode, as a runtime's `codeIri` and a builder's do | borrowed |
| the pinned CVX comparisons | | `same-mapped-code-and-date.rq`, whose bytes every rule list version from 1 to 8 pins, and its successor `same-vaccine-group-and-date.rq`, whose bytes version 9 pins, join the unencoded literal; a test checks that every query joining a stem to a literal encodes it unless a rule list pins it and its kind's code shape allows unreserved characters only | ours: a pinned query's bytes are its version's, and a CVX code is digits, which the encoding leaves as they are |
| an HGVS key's form | HGVS: `NM_` a coding transcript, `c.`, a version required; ClinVar's `Type` column | `rec:HgvsCodeShape`: a coding `NM_` expression by its form, encoded; the row's `Type` plays no part | HGVS's form borrowed; ClinVar's `Type` set aside, since 2,302 of 34,428 submitted `NM_` rows of Lynch's genes are typed "genomic" (verified, [#203](https://github.com/jayostis/cascade-vocabulary/issues/203)) |
| a variation's normal form | ClinVar's Variation ID and VCV accession; the IG's digits | `rec:ClinVarCodeShape`: the digits without a leading zero, in `rec:CodeShape` so a names series can follow; `VCV000090011` and `VCV000090011.7` give `90011`; an SCV or RCV accession is not a variation | borrowed |
| other allele identifiers | ClinGen CA ids; VRS digests | neither is a code system here | diverged: VRS needs the reference sequence, which neither ClinVar's files nor a browser hold (#107, `variant-record.md`); for CA ids the reason is owed (Still open) |

## Why

**Why encode.** M4 said "the literal as written" while `rec:CodeSystem` said the code is percent-encoded; no code held a
reserved character, so they never differed. An HGVS expression holds `:` and `>`, and a runtime refuses a row holding a
raw `>`. Encoding is the one reading under which a row and a literal can meet.

**Why `ENCODE_FOR_URI`.** It is the encoding SPARQL has, so a query, a builder and a runtime can each do the same thing,
and it is defined by RFC 3986's unreserved set, so it has one answer: the vectors give one IRI per code on rdflib and on
Oxigraph (`tests/test_variants.py`).

**Why a slash after the system URI.** FHIR RDF leaves a concept IRI undefined where HL7 Terminology registers no stem,
so the vocabulary has to choose one, and it chooses as it did for CVX, RxNorm and ICD-10-CM. Every stem ends in a
slash, and a test says so.

**Why the pinned queries are not edited.** A rule list version pins its queries' bytes, so an edited query is a new
version, for no change in what it joins: those queries read CVX rows only, and a CVX code is digits by
`rec:CvxCodeShape`.

**Why the form and not the `Type` column.** ClinVar's `Type` does not follow the expression's form: 2,302 of the 34,428
submitted `NM_` rows of Lynch's five genes are typed "genomic" (verified, counted by the file's gene column; on the
builder's VariationID basis, of 34,405 rows, not recounted: unverified;
[#203](https://github.com/jayostis/cascade-vocabulary/issues/203)). HGVS defines `NM_` and `c.` by the expression itself.

**Why the digits.** ClinVar says the Variation ID "can be used in lieu of the VCV accession number", and the IG writes
the digits; so a report's `90011`, `VCV000090011` and `VCV000090011.7` are one code.

## Alternatives that lost

- **A different stem scheme, such as the system URI followed by `#`.** The strongest case: the system URI stays whole as
  the IRI's base. Every other stem ends in a slash, and a test says so.
- **ClinVar's page URL, `https://www.ncbi.nlm.nih.gov/clinvar/variation/`, as the stem.** The strongest case: it is the
  one form that resolves. It is not the system URI HL7 Terminology registers, and where no stem is registered the
  vocabulary takes the system URI followed by a slash.
- **`encodeURIComponent`.** The strongest case: every runtime has it. It differs from `ENCODE_FOR_URI` on five
  characters, two of which (`(` and `*`) HGVS uses, so a row and a literal would not meet.
- **Editing the pinned comparisons to encode.** The strongest case: one rule for every query, and no exemption for a
  test to carry. Their bytes are pinned by rule list versions 1 to 9; a changed query is a new version, for no change
  in what it joins.
- **A ClinGen CA id or a VRS digest as the code.** The strongest case: one identity for a variant across transcripts and
  assemblies, where two HGVS expressions of one variant are two codes. A VRS digest needs the reference sequence to
  compute (`variant-record.md`). Why a CA id lost is not written anywhere; it is owed below.

## Still open

- Why a ClinGen CA id is not a code system here. #202 names the Allele Registry as prior art the notes skipped, and
  neither #107 nor #139 weighs it; the divergence stands, and its reason is owed.
- Whether a code IRI should resolve. Neither stem does (verified 2026-10-22); ClinVar's page is under
  `/clinvar/variation/`, and HGVS has moved to hgvs-nomenclature.org. Nothing in the pod dereferences a code today.
- Whether `rec:HgvsCodeShape`'s pattern should follow the EBNF grammar HGVS 21 is moving to, once it is complete.

## What would change our mind

HL7 Terminology registering a stem for either system, or a new system URI for HGVS; a code system whose codes hold
reserved characters and a pinned query that reads them; a runtime that can ask the Allele Registry or compute a VRS
digest in the browser.
