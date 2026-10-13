# The HGVS and ClinVar code systems, and encoding a code

Status: draft, 2026-10-13. Terms: `rec:HGVS`, `rec:ClinVar`, `rec:HgvsCodeShape`, `rec:ClinVarCodeShape`; rule M4.

## Question

What are the IRIs of an HGVS expression and a ClinVar variation, and what does it mean that a literal "joins as its IRI"
when the literal holds characters an IRI cannot?

## What others do

- **HL7 Terminology** registers a system URI for each and an IRI stem for neither: HGVS is `http://varnomen.hgvs.org`
  (NamingSystem v3-hgvs, OID 2.16.840.1.113883.6.282) and ClinVar is `http://www.ncbi.nlm.nih.gov/clinvar` (NamingSystem
  ClinVarV, OID 2.16.840.1.113883.6.319). FHIR R5's IRI-stem table names neither.
- **CVX, RxNorm, ICD-10-CM** are given the system URI followed by a slash where THO registers no stem (this vocabulary's
  convention).
- **JavaScript's `encodeURIComponent`** leaves `! ' ( ) *` unencoded, which `ENCODE_FOR_URI` encodes.

## Choice

- `rec:HGVS` has the stem `http://varnomen.hgvs.org/` and `rec:ClinVar` the stem `http://www.ncbi.nlm.nih.gov/clinvar/`;
  the system URI is the `skos:exactMatch`.
- A literal joins as the stem followed by the literal through SPARQL's `ENCODE_FOR_URI`: every character but
  `A-Z a-z 0-9 - _ . ~` as `%` and two upper-case hexadecimal digits of its UTF-8. `NM_000249.4:c.2042C>T` is
  `http://varnomen.hgvs.org/NM_000249.4%3Ac.2042C%3ET`. Rule M4 and `rec:CodeSystem` say so, the four question queries
  that built an IRI by concatenation encode, and a runtime's `codeIri` and a builder's follow.
- `same-mapped-code-and-date.rq` is not edited: every rule list version from 1 to 7 pins its bytes, it reads CVX rows
  only, and a CVX code is digits, which the encoding leaves as they are. A test checks that every query that joins a stem
  to a literal encodes it unless a rule list pins it and its kind's code shape allows unreserved characters only.
- `rec:HgvsCodeShape` is a coding `NM_` expression by its form, encoded; the row's Type column plays no part (2,302 of
  Lynch's 34,428 submitted `NM_` rows have Type "genomic"). `rec:ClinVarCodeShape` is the digits without a leading zero
  and joins `rec:CodeShape`, so a names series of variations can follow. A VariationID's normal form is the digits:
  `VCV000090011` and `VCV000090011.7` give `90011`, and an SCV or RCV accession is not a variation.

## Why

M4 said "the literal as written" while `rec:CodeSystem` said the code is percent-encoded; no code held a reserved
character, so they never differed. An HGVS expression holds `:` and `>`, and a runtime refuses a row holding a raw `>`.
Encoding is the one reading under which a row and a literal can meet.

## Alternatives that lost

- **A different stem scheme** such as the system URI followed by `#`. Every other stem ends in a slash, and a test says so.
- **`encodeURIComponent`.** The strongest case: every runtime has it. It differs from `ENCODE_FOR_URI` on five characters,
  two of which (`(` and `*`) HGVS uses, so a row and a literal would not meet.
- **Editing `same-mapped-code-and-date.rq` to encode.** Its hash is pinned by seven rule list versions; a changed query
  is a new version, for no change in what it joins.

## What would change our mind

HL7 Terminology registering a stem for either system, or a code system whose codes hold reserved characters and a pinned
query that reads them.
