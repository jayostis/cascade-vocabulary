# The IRI of every code

Status: draft, 2026-10-22. Replaces `hgvs-and-clinvar-codes.md` (2026-10-13, brought to the `README.md` standard on
2026-10-22 under #202), whose scope was HGVS and ClinVar: its rulings on encoding, the HGVS key's form and ClinVar's
normal form stand and are carried here; its ruling that a stem without an HL7 Terminology registration is the
`Coding.system` URI followed by a slash, "by the convention for CVX, RxNorm and ICD-10-CM", and that "the stems are not
Cascade IRIs and do not move", is reversed. Answers review item C1 (the unregistered stems) and applies C2 and C3 as
the settlement words them. Terms: `rec:CodeSystem` and its thirteen members (`records.ttl:469-570`), each adapter's
`vocab/*-code-systems.ttl`, `rec:HgvsCodeShape`, `rec:ClinVarCodeShape`; rule M4. Depends on `naming.md` (names hash
a version's content, codes included) and `variant-identity.md` (R12 and R13 join on the HGVS and ClinVar IRIs). The
new stems land in #193's one re-mint, with `cascade:codingSystemUri`; nothing in the ontology, the adapters or the
tables changes in this note's pull request. The research log is on that pull request.

## Question

What IRI does the vocabulary give a code, for each code system a pod carries? A code sits inside every version's
content, so its IRI is hashed into names (`naming.md`): it must be one IRI per code, computed byte for byte from the
code literal by any runtime, with no server, and it must never change. FHIR RDF gives a concept IRI only where HL7
Terminology (THO) registers an IRI stem, and otherwise "conceptIRI is undefined. Halt." THO registers one for two of
the thirteen systems here. For the rest, the vocabulary needs an IRI that someone other than Cascade would also
compute, or, failing that, one in Cascade's own space, and the old note chose neither: it wrote Cascade's choice into
URI space HL7, NLM, CDC, AMA, FDA, NCBI and HGVS own.

Where the stems stand today (verified, `records.ttl` and both adapters at main):

| system | `records.ttl` | stem today | THO stem |
|---|---|---|---|
| CVX | 481 | `http://hl7.org/fhir/sid/cvx/` | none |
| RxNorm | 487 | `http://www.nlm.nih.gov/research/umls/rxnorm/` | none |
| NDC | 493 | `https://ns.cascadeprotocol.org/codes/ndc11/` | none |
| ICD-10-CM | 500 | `http://hl7.org/fhir/sid/icd-10-cm/` | none |
| SNOMED CT | 506 | `http://snomed.info/id/` | none (the owner publishes it) |
| LOINC | 513 | `http://loinc.org/rdf/` | `http://loinc.org/rdf/` |
| MED-RT | 520 | `https://ns.cascadeprotocol.org/codes/medrt/` | none |
| MeSH | 527 | `http://id.nlm.nih.gov/mesh/` | `http://id.nlm.nih.gov/mesh/` |
| UNII | 535 | `http://fdasis.nlm.nih.gov/` | none |
| CPT | 542 | `http://www.ama-assn.org/go/cpt/` | none |
| ICD-9-CM | 549 | `http://hl7.org/fhir/sid/icd-9-cm/` | none |
| HGVS | 556 | `http://varnomen.hgvs.org/` | none |
| ClinVar | 563 | `http://www.ncbi.nlm.nih.gov/clinvar/` | none |

The FHIR adapter declares five of these (`fhir-code-systems.ttl`: SNOMED CT, RxNorm, NDC, ICD-10-CM, LOINC), the C-CDA
adapter nine (`ccda-code-systems.ttl`: those five and ICD-9-CM, CPT, CVX, UNII), each with the same stem as
`records.ttl` (verified). HGNC genes are held as approved symbols, literals (`records.ttl:433`, `genomics:geneSymbol`),
and units as UCUM strings (`quantities.md`, row "unit IRI"): neither is a code IRI today.

## Rubric

The owner's (Jay, 2026-10-22), applied to every code system the vocabulary or an adapter declares, and to any added
later:

1. Do not make something up where someone already made something pretty good that can be made to work: defer to the
   community. Prefer the owner's own IRI, then a community registry's, then Cascade's.
2. A candidate passes when it is (a) maintained by the code system's owner or a recognised community; (b) one IRI per
   code, computed deterministically from the code literal, with the rule stated (prefix and code, encoding, case, the
   form of the code); (c) under a stated commitment that the prefix and pattern persist, since names hash it; (d)
   permitted by its terms of use. Resolving is a bonus; perfection is not required.
3. Where nothing passes, the code goes under `https://ns.cascadeprotocol.org/codes/<system>/`, and this note says what
   was checked and why each candidate failed.
4. LOINC, SNOMED CT and MeSH keep their registered or published stems.

## What others do

- **FHIR RDF** (R5, Appendix 1): "If no IRI Stem is defined for s in the HL7 Terminology website, then conceptIRI is
  undefined. Halt."; otherwise the stem followed by "the IRI-safe version of c, as defined by the algorithm in section
  7.3 of R2RML", which keeps `iunreserved`, `ucschar` included. Its example table gives ICD-10 (WHO) the BioPortal stem
  `http://purl.bioontology.org/ontology/ICD10/`, SNOMED CT `http://snomed.info/id/`, MeSH
  `https://id.nlm.nih.gov/mesh/` and LOINC `https://loinc.org/rdf/` in R5, where THO registers `http://` for both and
  the current build writes `http://loinc.org/rdf/` (verified, both pages). A Coding carries `fhir:system` and
  `fhir:code`; the concept IRI is an optional `a` on it (verified). Neither SNOMED CT's nor ICD-10's stem is registered
  in THO (verified, below), so the algorithm as written halts for both.
- **HL7 Terminology.** Of the NamingSystems of the fifteen systems here (the thirteen, HGNC and UCUM), two carry a
  unique id of type `iri-stem`: LOINC `http://loinc.org/rdf/` and MeSH `http://id.nlm.nih.gov/mesh/`. The others
  register an OID and system URIs only: CVX `http://hl7.org/fhir/sid/cvx`, RxNorm
  `http://www.nlm.nih.gov/research/umls/rxnorm`, NDC `http://hl7.org/fhir/sid/ndc`, ICD-10-CM
  `http://hl7.org/fhir/sid/icd-10-cm`, ICD-9-CM diagnoses `http://hl7.org/fhir/sid/icd-9-cm`, CPT
  `http://www.ama-assn.org/go/cpt`, UNII `http://fdasis.nlm.nih.gov`, MED-RT `http://va.gov/terminology/medrt`, HGVS
  `http://varnomen.hgvs.org`, ClinVar `http://www.ncbi.nlm.nih.gov/clinvar`, HGNC `http://www.genenames.org`, UCUM
  `http://unitsofmeasure.org`, SNOMED CT `http://snomed.info/sct` (verified: the published NamingSystem JSON, and
  `grep -rl iri-stem` over UTG's `input/sourceOfTruth/external` at `05d22fc`, which finds those two files only).
- **The owners.** SNOMED International's URI Standard names a component `http://snomed.info/id/{sctid}` (verified).
  LOINC's users' guide has a section "Using a URI to identify LOINC concepts as resources in RDF" giving
  `http://loinc.org/rdf/`, and NLM serves MeSH as RDF under `http://id.nlm.nih.gov/mesh/` (verified; both redirect to
  `https://`, MeSH's answers 200 and LOINC's 403 to scripts). No other owner
  publishes an IRI per code: NLM's RxNav is a search page and a REST API, and `id.nlm.nih.gov/rxnorm/1191` is 404; CDC
  publishes CVX as tables and a PDF list; NCHS and CMS publish ICD-10-CM as files (inferred); AMA licenses CPT; FDA's UNII page is
  `precision.fda.gov/uniisearch/srs/unii/{UNII}`; NCBI's ClinVar page is `/clinvar/variation/{id}/`, and
  `/clinvar/{id}/` is 404; `varnomen.hgvs.org` no longer resolves (all verified 2026-10-22). VA's MED-RT is
  served by NCI EVS (inferred: EVS lists it among its terminologies), whose triple store names a concept `http://ncicb.nci.nih.gov/MEDRT.owl#N0000175562` in a graph
  named per release, `http://ncicb.nci.nih.gov/MEDRT_2026.07.06.owl` (verified, EVS SPARQL API); EVS states no
  commitment for that form (none found), and its predecessor NDF-RT's `http://evs.nci.nih.gov/ftp1/NDF-RT/NDF-RT.owl#`
  names went with NDF-RT's retirement (inferred).
- **identifiers.org** (EMBL-EBI): a compact identifier is "a Prefix …, a colon (':'), and an Accession", linked as
  `https://identifiers.org/[provider_code/]namespace:accession`; its FAQ: "Identifiers.org URIs are persistent since
  they shield the user from changes in the underlying, resource specific, URLs", "stable, perennial and globally
  unique"; its data are CC BY 4.0 and fall "under EBI's long term data preservation policy" (verified). Its earlier
  form was `http://identifiers.org/pubmed/23584831`; `http://identifiers.org/clinvar/90011` still redirects (verified).
  It registers `clinvar` ("ClinVar Variant", `^\d+$`, resolving to `/clinvar/variation/{id}`), `unii` (`^[A-Z0-9]+$`,
  official resource FDA), `ndc` (`^\d+\-\d+\-\d+$`, sample `0002-1975-61`, official resource hipaaspace.com), `hgnc`,
  `mesh` and `snomedct`, and nothing for CVX, RxNorm, ICD-10-CM, ICD-9-CM, CPT, MED-RT, HGVS or LOINC; its `icd` is WHO
  ICD-10, `^[A-Z]\d+(\.[-\d+])?$`, which rejects ICD-10-CM's `S72.001A` (verified, registry API).
- **Bioregistry** has a prefix for every system but MED-RT. Its `rdf_uri_format` is set for SNOMED CT, LOINC and MeSH
  only, to the owners' stems. Its `uri_format` elsewhere is a page: RxNav's search, `icd10data.com`, a search on
  `icd9cm.chrisendres.com`, `aapc.com`, `hipaaspace.com`, FDA's UNII page, ClinGen's allele query for HGVS, and for CVX
  `biopragmatics.github.io/providers/cvx/$1`. Its preferred ClinVar prefix is `clinvar.variation`, with `clinvar` and
  `clinvar.variant` as synonyms (verified, API). No statement that its own `https://bioregistry.io/{prefix}:{id}`
  resolver URLs persist was found.
- **BioPortal** (NCBO): "RRF and Protégé ontologies: terms in these ontologies do not have http URIs. We generate the
  URIs in the following form for these terms: `http://purl.bioontology.org/ontology/{Acronym}/{ID}`" (verified,
  archived wiki); a 2013 reply from NCBO: a URI 404s because it "refers to a terminology that is not in BioPortal any
  more" (verified). No persistence statement was found; its PURLs answered 403 to scripted requests on 2026-10-22, so
  resolution is unverified. Its UMLS-derived content is under the UMLS licence (inferred for each source).
- **Wikidata** has an identifier property for each system (CVX P10876, RxNorm P3345, ICD-10-CM P4229, ICD-9-CM P1692,
  NDC P3640, UNII P652, ClinVar P1929, HGVS P3331, HGNC P354 and P353); its "formatter URI for RDF resource" (P1921)
  is set for MeSH, LOINC and SNOMED CT only, to the owners' stems (verified, API). Its page formatters are third-party
  sites for CVX (findacode), ICD-10-CM, ICD-9-CM and NDC.
- **SPHN** uses `http://snomed.info/id/` for SNOMED CT; for a system whose owner publishes no RDF it mints its own
  space, as `https://biomedit.ch/rdf/sphn-resource/icd-10-gm/`, `…/chop/` and `…/emdn/`, or uses the owner's page, as
  ATC's `https://www.whocc.no/atc_ddd_index/?code=`; any other code is a `sphn:Code` with `sphn:hasIdentifier` and
  `sphn:hasCodingSystemAndVersion` literals (verified).
- **OMOP** holds a code as `concept_code` and `vocabulary_id` strings behind an integer `concept_id`, and no IRIs
  (verified, the CONCEPT table). **GA4GH**: a GKS `Coding` is `system` and `code`, with optional `iris` "if a dereferencable identifier is
  available" (verified, `gks-core-source.yaml` 1.0); VRS 2.0 holds an HGVS expression as an `Expression` with
  `syntax` `hgvs.c` and a string `value` (verified, `vrs-source.yaml` 2.0). **W3C HCLS**: Bio2RDF minted
  `http://bio2rdf.org/{prefix}:{id}`, as for NDC, and is unmaintained (unverified).
- **Web architecture**: "URI ownership gives the relevant social entity certain rights, including: … to associate a
  resource with an owned URI—URI allocation", and "It is important to avoid URI collision" (W3C, Architecture of the
  World Wide Web §2.2.2 and §2.2.2.1, verified).
- **Encoding.** SPARQL's `ENCODE_FOR_URI` escapes all but RFC 3986's unreserved `A-Z a-z 0-9 - . _ ~`, with upper-case
  hexadecimal; R2RML §7.3 also keeps `ucschar`; JavaScript's `encodeURIComponent` also keeps `! * ' ( )` (verified,
  as the old note recorded). HGVS 21.1 defines `NM_` as a coding transcript and `c.` as coding DNA, requires a
  version, and is moving to an EBNF grammar; ClinVar's Variation ID "can be used in lieu of the VCV accession number",
  and an Allele ID shares its numbering; ClinGen's Allele Registry assigns CA ids; VRS computes digests from the
  normalised object (verified, as the old note recorded, evidence on
  [#203](https://github.com/jayostis/cascade-vocabulary/issues/203)).

Sources: FHIR RDF R5 (https://hl7.org/fhir/R5/rdf.html) and current build (https://build.fhir.org/rdf.html); THO
NamingSystems (https://terminology.hl7.org/NamingSystem-v3-loinc.json, -MeSH, -v3-snomed-CT, -v3-rxNorm, -CVX,
-icd10CM, -icd9cm, -v3-ndc, -CPT, -UNII, -MEDRT, -v3-hgvs, -ClinVarV, -v3-hgnc, -v3-ucum) and UTG
(https://github.com/HL7/UTG/tree/05d22fc29bccb5ca5e60e249ec153da4ad07af58/input/sourceOfTruth/external); SNOMED CT URI
Standard §2 (https://docs.snomed.org/snomed-ct-specifications/snomed-ct-uri-standard/2-snomed-ct-uri-space); LOINC's
RDF guidance
(https://loinc.org/kb/users-guide/recommendations-for-best-practices-in-using-and-mapping-to-loinc/#using-a-uri-to-identify-loinc-concepts-as-resources-in-rdf);
CDC CVX (https://www2a.cdc.gov/vaccines/iis/iisstandards/vaccines.asp?rpt=cvx); NCI EVS REST
(https://api-evsrest.nci.nih.gov/api/v1/metadata/terminologies); identifiers.org identification scheme, FAQ, terms
and migration (https://docs.identifiers.org/pages/identification_scheme.html, …/faq.html, …/terms_of_use.html,
…/migration.html) and registry API
(https://registry.api.identifiers.org/restApi/namespaces/search/findByPrefix?prefix=clinvar, and `unii`, `ndc`,
`icd`); Bioregistry API (https://bioregistry.io/api/registry/rxnorm, and each prefix); NCBO, RDF in BioPortal
(https://web.archive.org/web/2025/https://www.bioontology.org/wiki/RDF_in_BioPortal) and the 2013 reply
(https://lists.w3.org/Archives/Public/public-semweb-lifesci/2013May/0082.html); Wikidata API
(https://www.wikidata.org/w/api.php?action=wbgetentities&ids=P3345); SPHN external terminologies
(https://sphn-semantic-framework.readthedocs.io/en/latest/external_terminologies/external_terminologies.html); OMOP CDM
5.4 (https://ohdsi.github.io/CommonDataModel/cdm54.html); GA4GH GKS core
(https://github.com/ga4gh/gks-core/blob/1.0/schema/gks-core/gks-core-source.yaml) and VRS
(https://github.com/ga4gh/vrs/blob/2.0/schema/vrs/vrs-source.yaml); W3C Web Architecture
(https://www.w3.org/TR/webarch/#uri-ownership); and the sources of `hgvs-and-clinvar-codes.md` for encoding, HGVS and
ClinVar, kept in its history and on #203. The commands and their answers are the research log on the pull request
that brought this note.

## Choice

Each row lands in #193's re-mint (settlements C1), which writes the stems into `records.ttl` and both adapters'
`vocab/*-code-systems.ttl` and states the form in M4; until then, M4 and `rec:CodeSystem` hold the old stems.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| LOINC | THO `iri-stem`; FHIR RDF | `http://loinc.org/rdf/` and the code with its check digit, `2823-3` | borrowed: THO's `http://` form, not R5's example `https://` |
| MeSH | THO `iri-stem`; NLM | `http://id.nlm.nih.gov/mesh/` and the unique ID, `D004095`, `M0006414` | borrowed: THO's form, as above |
| SNOMED CT | SNOMED URI Standard; FHIR RDF's table; SPHN, Bioregistry, Wikidata | `http://snomed.info/id/` and the SCTID | borrowed from the owner, where THO registers nothing |
| ClinVar | identifiers.org `clinvar`; ClinVar's Variation ID | `https://identifiers.org/clinvar:` and the Variation ID's digits, no leading zero, `https://identifiers.org/clinvar:90011` | borrowed from identifiers.org: the owner publishes no IRI, and the registry passes (a)-(d) |
| UNII | identifiers.org `unii` | `https://identifiers.org/unii:` and the UNII as FDA gives it, ten upper-case letters and digits, `https://identifiers.org/unii:3G6A5W338E` | borrowed from identifiers.org, as above |
| CVX | THO system URI only; Bioregistry `cvx` (a GitHub Pages provider); BioPortal | `https://ns.cascadeprotocol.org/codes/cvx/` and the code as CDC writes it, leading zero kept, `08` | ours: no candidate passes (c) |
| RxNorm | THO system URI only; RxNav pages; Bioregistry `rxnorm`; BioPortal | `https://ns.cascadeprotocol.org/codes/rxnorm/` and the RXCUI | ours: the owner publishes none; BioPortal fails (c) |
| NDC | THO system URI only; identifiers.org `ndc` | `https://ns.cascadeprotocol.org/codes/ndc11/` and the 11-digit 5-4-2 form, no hyphens; a 10-digit labelled code (4-4-2, 5-3-2, 5-4-1) is zero-padded in its short segment first | ours, unchanged: identifiers.org's `ndc` fails (b) |
| ICD-10-CM | THO system URI only; Bioregistry `icd10cm`; BioPortal; identifiers.org `icd` (WHO) | `https://ns.cascadeprotocol.org/codes/icd10cm/` and the code as FHIR and C-CDA write it, with its dot, `E11.65` | ours: BioPortal fails (c); `icd` is another system |
| ICD-9-CM | THO system URI only; Bioregistry `icd9cm`; BioPortal | `https://ns.cascadeprotocol.org/codes/icd9cm/` and the code with its dot | ours, as ICD-10-CM |
| CPT | THO system URI only; Bioregistry `cpt` (aapc.com); BioPortal | `https://ns.cascadeprotocol.org/codes/cpt/` and the five-character code | ours: no candidate passes (c), and AMA's licence covers the codes |
| MED-RT | THO system URI only; NCI EVS `MEDRT.owl#` | `https://ns.cascadeprotocol.org/codes/medrt/` and the NUI, `N0000175562` | ours, unchanged: EVS's form fails (c) |
| HGVS | THO system URI only; Bioregistry `hgvs` (a ClinGen query); VRS's string `Expression` | `https://ns.cascadeprotocol.org/codes/hgvs/` and the expression through `ENCODE_FOR_URI`, `…/codes/hgvs/NM_000249.4%3Ac.2042C%3ET` | ours: no registry has an identifier for an expression |
| a segment's name in our space | Bioregistry prefixes | the Bioregistry prefix (`cvx`, `rxnorm`, `icd10cm`, `icd9cm`, `cpt`, `hgvs`); `ndc11` and `medrt` keep theirs, since `ndc11` names the form and Bioregistry has no MED-RT | borrowed |
| HGNC | THO system URI; identifiers.org `hgnc` | no code IRI: a gene is its approved symbol, a literal | nothing to mint; Still open says which, if ever |
| UCUM | UCUM defines no IRIs (`quantities.md`) | no code IRI: `ucumUnit` is the source's string | borrowed, as `quantities.md` ruled |
| a code system's `Coding.system` | THO system URIs; GKS `Coding.system`; C2 | `cascade:codingSystemUri`, an `xsd:anyURI`, is THO's preferred system URI; a reader writing FHIR takes `Coding.system` from it and `Coding.code` from the IRI's tail after `void:uriSpace`, percent-decoded | borrowed; replaces `skos:exactMatch` (C2) |
| a stem registered later | none | THO registering a stem, or an owner publishing one, for a system here is recorded on the system beside its `void:uriSpace` and read as each code's `skos:exactMatch`; the code IRI is never renamed | ours: a renamed IRI renames every version that holds it |
| a literal joining as an IRI | `ENCODE_FOR_URI`; RFC 3986 §2.3 and §2.1; R2RML §7.3 | the stem, then the literal through `ENCODE_FOR_URI`: every character but `A-Z a-z 0-9 - _ . ~` as `%` and two upper-case hexadecimal digits of its UTF-8; M4 and `rec:CodeSystem` say so | borrowed from SPARQL; diverged from R2RML on `ucschar` (C3), which no code here holds |
| the pinned CVX comparisons | | `same-mapped-code-and-date.rq` and `same-vaccine-group-and-date.rq` join the unencoded literal; the re-mint writes the new CVX stem into them as new rule list versions | ours: a CVX code is digits, which the encoding leaves as they are |
| an HGVS key's form | HGVS: `NM_` a coding transcript, `c.`, a version required; ClinVar's `Type` | `rec:HgvsCodeShape`: a coding `NM_` expression by its form; the row's `Type` plays no part | HGVS's form borrowed; ClinVar's `Type` set aside, since 2,302 of 34,428 submitted `NM_` rows of Lynch's genes are typed "genomic" (verified, #203) |
| a variation's normal form | ClinVar's Variation ID and VCV accession | `rec:ClinVarCodeShape`: the digits without a leading zero; `VCV000090011` and `VCV000090011.7` give `90011`; an SCV or RCV accession is not a variation | borrowed |
| other allele identifiers | ClinGen CA ids; VRS digests | neither is a code system here | diverged: VRS needs the reference sequence, which a browser does not hold; no report in the story carries a CA id (`variant-record.md`) |

## Why

**The rubric.** The owner ruled that the vocabulary defers to what a community already made when it is pretty good and
workable, and mints its own only where nothing is, saying what was checked. Each candidate was tested on the four
conditions of the Rubric. A name hashes the IRI, so (b) and (c) carry the weight: an IRI no one else computes the same
way, or one whose pattern may change, costs every pod a re-mint.

**Why not the system URI and a slash.** The old note's only reason was that CVX, RxNorm and ICD-10-CM already did so:
consistency, not merit. It allocates URIs in space others own, a right web architecture gives the owner; FHIR RDF computes no such IRI, so no FHIR consumer recognises it; and if THO registered a different stem, two IRIs
in the owner's own space would name one code. `records.ttl:471` says the stem "is never the FHIR Coding.system URI",
and every one of these was that URI and a slash.

**Why identifiers.org for ClinVar and UNII.** It is the only candidate here that passes all four. (a) EMBL-EBI runs it
as a community registry, and NCBI's ClinVar and FDA's UNII are its namespaces' resources. (b) Each code is the prefix,
a colon and the code, under a pattern the registry states (`^\d+$`, `^[A-Z0-9]+$`), and both codes are unreserved
characters, so encoding changes nothing. (c) Its FAQ states the URIs persist; its earlier `http://…/clinvar/90011` form
still redirects, so a form change has kept the old names working. (d) CC BY 4.0. Of the eight others, neither the
owner nor identifiers.org has a scheme, or (NDC) identifiers.org has one that fails (b); ClinVar's and UNII's owners
have pages only, which carry no commitment.

**Why NDC stays ours.** identifiers.org's `ndc` requires hyphens and admits the 10-digit labelled forms and the 11-digit
form alike; its sample is 10-digit. One package therefore has two IRIs there, and the 10-digit form cannot be computed
from the 11-digit one RxNorm gives (the padded segment is not marked), so (b) fails. Its official resource is a
commercial billing site.

**Why BioPortal fails.** NCBO says it generates these URIs; no statement that it keeps them was found, and NCBO has said
a terminology that leaves BioPortal leaves 404s. It is the strongest candidate for CVX, RxNorm, ICD-10-CM, ICD-9-CM and
CPT, and FHIR RDF's own table uses it for WHO ICD-10, but a hashed name cannot rest on an unstated commitment.

**Why Bioregistry and Wikidata fail.** Bioregistry's resolver URLs carry no persistence statement, its page formats for
these systems are mostly third-party sites, and its preferred ClinVar prefix differs from identifiers.org's, with two
synonyms: the prefix is not fixed. Wikidata's items are lookups, not computable from the code, and its RDF formatter is
set for MeSH, LOINC and SNOMED CT only, which agrees with this note's row 4.

**Why our own space.** Cascade owns `ns.cascadeprotocol.org` and commits here that a `codes/<system>/` stem never
changes once a version holds it. Two of the thirteen were already there for the same reason (NDC, MED-RT); SPHN does
the same with `biomedit.ch/rdf/sphn-resource/<system>/`. Bioregistry's prefixes name the segments, so a reader can find
each system in a registry.

**Why `Coding.system` stays as data.** FHIR, GA4GH and SPHN all keep a code as a system and a code; an IRI is extra. The
system URI is therefore recorded on each system as `cascade:codingSystemUri` (C2), and a reader writing FHIR gets the
`Coding` from it and the IRI's tail; the IRI never has to be a FHIR concept IRI to be mapped back.

**Why a later stem aligns rather than renames.** A code IRI is inside every version's content, and the version's name
hashes it; renaming it renames the version and every claim and judgment on it. A second stem is a mapping: each code's
IRI under it is its `skos:exactMatch`, which SKOS allows between concepts, unlike C2's exactMatch on a code system.

## Alternatives that lost

- **Keep `Coding.system` and a slash for every unregistered system.** The strongest case: one rule computes every stem
  from the system URI with no table, and it is already applied. It lost: it mints in other owners' URI space, FHIR
  defines no such IRI, and a later THO stem would put two IRIs in the owner's space for one code.
- **Move every unregistered stem into Cascade's space** (the lean of review item C1). The strongest case: one rule, all
  in space Cascade controls, nothing depending on a registry. It lost to the rubric for ClinVar and UNII, where a
  community scheme passes every condition.
- **BioPortal PURLs for CVX, RxNorm, ICD-10-CM, ICD-9-CM and CPT.** The strongest case: one community scheme across the
  UMLS sources, the code appended as written, and FHIR RDF's own example uses it for WHO ICD-10. It lost on (c): no
  stated persistence, removal has broken them before, and they were unreachable to scripts on 2026-10-22.
- **identifiers.org for NDC, written 5-4-2 with hyphens.** The strongest case: the pattern admits it, so NDC would be
  borrowed. It lost on (b): the namespace gives no normal form, its sample is the 10-digit form, and another user of it
  writes a different IRI for the same package.
- **Bioregistry resolver URLs, `https://bioregistry.io/{prefix}:{id}`.** The strongest case: one registry covers twelve
  of the thirteen. It lost on (c), and on a preferred prefix that has changed for ClinVar.
- **The owners' page URLs** (RxNav, NCBI's ClinVar page, FDA's UNII page). The strongest case: the owner's own address,
  and it resolves. A page is not an identifier and carries no commitment; ClinVar's `/clinvar/{id}/`, the form
  `hgvs4variation`'s header gives, is 404. Each stays a `rec:pageTemplate`.
- **NCI EVS's `http://ncicb.nci.nih.gov/MEDRT.owl#` for MED-RT.** The strongest case: the distributor's own RDF names.
  It lost on (c): an internal name with no stated commitment, beside a release-named graph.
- **Bio2RDF's `http://bio2rdf.org/{prefix}:{id}`.** The strongest case: it covers NDC and others. It is unmaintained.
- **`encodeURIComponent`, or R2RML's IRI-safe form.** The strongest case: every runtime has the first, and FHIR RDF
  names the second. The first differs from `ENCODE_FOR_URI` on five characters, two of which (`(` and `*`) HGVS uses;
  the second differs on non-ASCII only, and SPARQL has no function for it.
- **A ClinGen CA id or a VRS digest as a variant's code.** The strongest case: one identity across transcripts and
  assemblies. A VRS digest needs the reference sequence, and no report in the story carries a CA id.

## Still open

- **For the owner: identifiers.org for ClinVar and UNII.** The rubric picks it; the cost is two systems whose stems end
  in a colon, outside both THO's and Cascade's space, and a test that every stem ends in a slash
  (`tests/test_tables.py:140`) that the re-mint rewrites. Lean: borrow, as ruled above.
- **For the owner: NDC.** The one close call. Lean: ours, as ruled.
- **Whether a code IRI under `codes/` should resolve**, by redirecting to the system's `rec:pageTemplate`. Lean: later;
  nothing in a pod dereferences a code.
- **HGNC, if a gene ever becomes an IRI:** identifiers.org's `hgnc` names an HGNC ID, not a symbol, and symbols are
  renamed. Lean: the HGNC ID under identifiers.org, the symbol kept as data.
- **ICD-9-CM's system URI**: THO's `icd9cm` NamingSystem registers `http://terminology.hl7.org/CodeSystem/icd9cm` under
  OID .6.2, and the diagnosis codes' `http://hl7.org/fhir/sid/icd-9-cm` under .6.103, which the C-CDA adapter reads
  (verified). `codingSystemUri` takes the latter; the re-mint checks the procedure codes.
- Whether `rec:HgvsCodeShape` should follow HGVS's EBNF grammar once it is complete.

## What would change our mind

THO registering a stem for a system here, or an owner publishing one (an alignment, never a rename); identifiers.org
deprecating `clinvar` or `unii` or changing its URI form without redirects; BioPortal or Bioregistry stating that its
IRIs persist (for a new system, not a re-mint); a source sending a code with non-ASCII characters (C3); a runtime that
can ask the Allele Registry or compute a VRS digest in the browser.
