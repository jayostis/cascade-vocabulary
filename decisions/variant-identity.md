# When two variant records are one variant

Status: draft, 2026-10-13; revised 2026-10-22 against `README.md`, from the review on #202. Rules: R12, justified
`jdg:SameVariation`, and R13, justified `jdg:SameVariationThroughTable`, in the rule list's version 8; rule M17 of
`runtime/matcher.feature`. Applies `naming.md`'s rubric: a variant record is named by its source (`variant-record.md`),
and that two are one variant is a judgment (test 2), made by `jdg:CascadeMatcher` as `judgments.md` rules. Claims,
assertions and used are `naming.md`; which revision is current is `currency.md`; the within-organisation rules these
rules are not are `republishing-sources.md`. #191 turns the short tags R12, R13 and M17 into descriptive rule terms, and
#193 moves `jdg:` and `genomics:` into the one unversioned namespace.

## Question

Two reports can name one variant on two transcript versions, one with a ClinVar ID and one without, from two labs that
share nothing: no server, no organisation, no identifier system. Which codes join them, which joins would be wrong, and
what does the pod read to decide, with no server of record to ask?

## What others do

- **FHIR Genomics Reporting IG STU3.** The Variant carries a variation code (81252-9, "ClinVar ID or similar") and a
  c.HGVS description (48004-6), and says nothing about when two Variants are one.
- **HGVS nomenclature.** "Variant descriptions lacking a version number are not valid", so one variant on
  `NM_000249.3` and on `NM_000249.4` is two expressions; nothing in the expressions says they are one. Its reference
  sequences page says "reference sequences must come from data sources that provide stable and permanent identifiers"
  (verified 2026-10-22).
- **ClinVar** keys a variation by its VariationID, "a unique integer identifier to each set of variants", and
  `hgvs4variation` lists the expressions that map to each, marking which a submitter gave. 90011's two submitted
  expressions are `NM_000249.3:c.2042C>T` and `NM_000249.4:c.2042C>T` (verified, #203). An
  expression is not unique across variations: 195 of 3,304,067 submitted coding expressions map to two VariationIDs in the
  2026-10 snapshot, 3 within Lynch's five genes and 21 within the 26-gene panel (all verified,
  [#203](https://github.com/jayostis/cascade-vocabulary/issues/203)).
- **ClinGen Allele Registry** does the join this note needs as a service: "All contextual alleles corresponding to a
  same variant are associated with the same canonical allele", across transcripts and assemblies, under one CA id.
- **GA4GH VRS** gives one variant one digest from any source, set aside in `variant-record.md`. **Cat-VRS** names a
  category of variants, which is not sameness of two reports.
- **openEHR** keeps the HGVS string as identity. **OMOP** matches HGVS strings against concept names and synonyms.
- **SEMAPV** names the kind of a mapping's justification: lexical matching, "based on a lexical comparison between one or
  more syntactic features of the subject with one or more syntactic features of the object", and background
  knowledge-based matching, which "exploits background knowledge from external resources". **SKOS** `skos:broadMatch`
  states "a hierarchical mapping link between two concepts".
- **SPARQL** `ENCODE_FOR_URI` returns "a simple literal with the lexical form obtained from the lexical form of its
  input", reserved characters percent-encoded, which is how an expression becomes a row's key (`hgvs-and-clinvar-codes.md`).

Sources: FHIR Genomics Reporting IG STU3, Variant profile
(https://hl7.org/fhir/uv/genomics-reporting/STU3/StructureDefinition-variant.html, verified); HGVS reference sequences
(https://hgvs-nomenclature.org/stable/background/refseq/, verified 2026-10-22, the source of "stable and permanent
identifiers"); ClinVar identifiers
(https://www.ncbi.nlm.nih.gov/clinvar/docs/identifiers/, verified) and the tab-delimited README
(https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/README, verified); Pawliczek et al., ClinGen Allele Registry,
Hum Mutat 2018 (https://pmc.ncbi.nlm.nih.gov/articles/PMC6519371/, verified); GA4GH VRS (https://vrs.ga4gh.org/en/stable/,
verified); Cat-VRS (https://cat-vrs.ga4gh.org/en/latest/, verified); openEHR and OMOP as cited in `variant-record.md`;
SEMAPV (https://mapping-commons.github.io/semantic-mapping-vocabulary/, verified); SKOS
(https://www.w3.org/TR/skos-reference/#mapping, verified); SPARQL 1.1 `ENCODE_FOR_URI`
(https://www.w3.org/TR/sparql11-query/#func-encode, verified). Research: #107's body
(https://github.com/jayostis/cascade-vocabulary/issues/107) and its Step 0 comment
(https://github.com/jayostis/cascade-vocabulary/issues/107#issuecomment-6139118340); the evidence issue
(https://github.com/jayostis/cascade-vocabulary/issues/203); the scenario #138 (https://github.com/jayostis/cascade-vocabulary/issues/138).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| join by ID (R12) | ClinVar VariationID; FHIR variation code | joins two variants whose current versions carry one ClinVar VariationID | borrowed: the ID as ClinVar defines it; the rule is ours |
| join through the table (R13) | ClinVar `hgvs4variation`; ClinGen's canonical allele | joins two variants whose current versions find one row of one version of a variant classifications table; the classification plays no part | ours: ClinGen's canonical allele does this join as a service (prior art), set aside under Alternatives |
| how a version finds its row | | a version with a VariationID finds that variation's row and only that row, its expression unread; one with none finds the row holding its expression, percent-encoded as `ENCODE_FOR_URI` does | ours; the encoding is SPARQL's |
| left alone | | a pair that shares an ID (R12's, so no pair has two justifications); a pair whose versions carry different IDs, whatever expressions they hold; a version whose expression is on more than one row, rows counted as distinct row subjects over every held version of every series of the kind; a version whose ID is on no row | ours |
| a page's lookup | | through the ClinVar IDs of the variant's entry when it carries any, through its HGVS expressions only when it carries none, never both (`tables/agreement.rq`) | ours |
| justification kinds | SEMAPV | `jdg:SameVariation` `skos:broadMatch` `semapv:LexicalMatching` (`judgments.ttl:93`); `jdg:SameVariationThroughTable` `skos:broadMatch` `semapv:BackgroundKnowledgeBasedMatching` (`judgments.ttl:98`) | borrowed from SEMAPV at the kind level, as `judgments.md` rules |
| maker | PROV agents; `judgments.md` | `jdg:CascadeMatcher`, one unversioned `prov:SoftwareAgent`; not yet in `judgments.ttl` | borrowed from `judgments.md` |
| used | `naming.md`: each member's version and each table version the rule read | each member's version and `?origin`, the table version whose row joined them | diverged from `naming.md` for R13, which reads every held version to count rows; open |
| scope | `republishing-sources.md`: within-organisation rules | across organisations: both are identity rules on global codes | ours: `republishing-sources.md` adds rules within one organisation, and these two are not among them (Why) |
| rule IRI | `naming.md`: descriptive terms in the one unversioned namespace | short tags in a versioned namespace today | yields to `naming.md` under #191 and #193 |
| computed identity | VRS digest; CA id | none | diverged; `variant-record.md` says why |

## Why

**Why only a table joins two expressions.** An HGVS expression names a transcript version, so two expressions are two
strings and nothing in the pod says they are one variant; only a table does, by listing both under one VariationID, as
ClinVar's `hgvs4variation` does for 90011. Sameness is a claim the pod makes from a table that says so, which is the
rubric's second test, and the table version is in the claim's used, so a later table that says otherwise makes a
different claim.

**Why an ID is read before an expression.** An ID is a stronger claim than an expression, so a version that carries one
is read by it alone: otherwise a report carrying ID 12345 and an expression of another variation would join that
variation's records (`runtime/matcher.feature`, M17, "a variant whose ID is on no row finds nothing"). A page reads the
same way, or a variant with ID 12345, on no row, and an expression on row 90011 would be shown 90011's classification.

**Why an expression on two rows joins nothing.** 195 submitted expressions name two variations in ClinVar's file, 3
within Lynch's genes (unverified and verified as above); one of them on a version would join two variations, and entries
would then join through it. Counting distinct row subjects, as `same-product-code.rq` counts, keeps two series that both
hold a variation from leaving every pair alone.

**Why these rules cross organisations.** `republishing-sources.md` confines its rules to one organisation, inside which
a shared business identifier is certain and a shared code and date is strong. A ClinVar VariationID is
not an organisation's: NCBI issues it, one per set of variants, for every submitter alike. An HGVS expression is not an
organisation's either: it is written on a reference sequence that must have "stable and permanent identifiers". Two
labs that share nothing still mean one variant by one VariationID, so R12 and R13 are cross-organisation identity rules,
and that is right for a variant.

**Why the SEMAPV kinds.** R12 compares one code string on two records, which is SEMAPV's lexical matching; R13 joins two
records through a table neither states, which is its background knowledge-based matching. Declaring the kind lets a view
treat both by kind without knowing the rule (`judgments.md`).

## Alternatives that lost

- **Join any two records that share an expression.** The strongest case: it needs no table, and two reports of one
  expression on one transcript are almost always one variant. An expression is not unique across variations (195 in the
  2026-10 file), and sameness is a claim the pod should make from a table that says so.
- **Read both the ID and the expression.** The strongest case: it would join more pairs, including a report whose ID is
  on no row of the held version. A pair of different IDs would join through one's expression, against what the IDs say.
- **A string distance between expressions.** The strongest case: it would join `NM_000249.3:c.2042C>T` and
  `NM_000249.4:c.2042C>T` with no table at all. #107 rules it out: "No rule infers sameness from similar strings", and
  weaker overlaps go to a person.
- **Ask the ClinGen Allele Registry.** The strongest case: it canonicalises every transcript and assembly to one CA id,
  the join R13 approximates. No report in the story carries a CA id, and the ClinVar table
  already lists the submitted expressions under one VariationID.
- **Confine the rules to one organisation.** The strongest case: one scope for every matcher rule, as
  `republishing-sources.md` draws it. Two labs are two organisations, so the two reports of Martin's story (#138)
  would never join, though ClinVar says they are one variation.

## Still open

- R13 reads every held version of every variant classifications series to count an expression's rows (`?anyOrigin` in
  `same-variation-through-table.rq`), but cites only `?origin` as used, where `naming.md` says used holds each table
  version the rule read. Whether used lists every version the count read, or the count is confined to `?origin`, is
  open.
- R12 and R13 are cross-organisation identity rules because a ClinVar ID or an HGVS expression is a global identity, not
  an organisation's. Whether every matcher rule on a global code (an RxNorm code, a LOINC code with a date) holds across
  organisations the same way, or only identity codes do, is open.
- The maker is `jdg:CascadeMatcher`, which `judgments.md` adds and `judgments.ttl` does not yet hold.
- The kit and M17 put "Matcher rules version 8" in a claim's used, where `naming.md` moves the rule list version to the
  assertion, and the kit names its table version by a `urn:uuid`; both change under #191, not here.

## What would change our mind

A table that lists IDs for expressions it does not hold as rows, or a source that states an expression and its ID
inconsistently often enough to matter. Sources carrying CA ids or VRS digests would make a computed join the better rule.
