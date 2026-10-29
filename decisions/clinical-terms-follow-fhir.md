# A clinical term follows FHIR unless its area's note says why not

Status: accepted, 2026-10-29: the owner accepted lean (b) as phase 0 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287)), on the research in
[#288](https://github.com/jayostis/cascade-vocabulary/issues/288). Extends #128 (cite FHIR for each clinical term,
record where and why Cascade diverges) from a mapping into a rule for every new or changed clinical term. Depends on
`version-content.md`, which keeps the `cascade:` clinical terms as what a version holds; `one-meaning-per-term.md`,
whose renames this rule generalises; and `naming.md` for names. No runtime applies it: the terms in
`ontologies/cascade.ttl` do, and phase 1 of #287 is its first use. Still open in phase 0, and not ruled here: the
decision note for the medication matching rules M15 and M16; the guideline the B12 rule's threshold and window cite;
and `readings-and-care-hypotheses.md`'s prior-art search.

## Question

Every new or changed clinical term needs a starting point. Without a rule, each one is designed afresh and argued from
the prototype or from what the adapters already write, and the vocabulary drifts from what sources send one term at a
time. Phase 1 of #287 adds about a dozen kinds of clinical content at once (codings in every system, reports and
documents, intent and self-report, dispense and dosage, coded interpretation, sex and deceased). Which standard does a
clinical term start from, what is copied from it, where does that stop, and what does a departure cost?

What makes it hard: a pod reads FHIR R4, FHIR R5 and C-CDA sources that disagree, keeps every copy, and reconciles
them with judgments, which FHIR does not model. A rule must say which parts of the vocabulary FHIR is the starting
point for and which it is not, or every reconciliation term reopens the question.

## What others do

Read on 2026-10-29 by the research in #288 unless marked.

- **FHIR R4 and US Core 9.0.0** define the clinical content hospitals send through patient-access APIs: each element
  with its meaning, value set binding, cardinality and status axes (`clinicalStatus` apart from
  `verificationStatus`; `MedicationRequest.intent` apart from `status`). US Core is what certified US systems expose
  (memory, not re-read). The by-kind comparison in #288 found nothing in the vocabulary's clinical content that FHIR
  cannot hold, and found most of FHIR's advantages were terms the vocabulary lacks: coded interpretation, intent and
  self-report, dispense and dosage, reports and documents, deceased.
- **FHIR R5** changes some of what R4 says (`MedicationStatement.status` becomes `recorded | entered-in-error |
  draft`, with "not taking" moved to `adherence`). Sources send R4 and US Core today.
- **FHIR as wire format.** Bundles, references, extensions, `meta` and contained resources exist because FHIR
  exchanges documents between servers. **FHIR RDF** types values by inspection and puts `fhir:status` on every
  resource, whose values come from whichever list the resource binds (`one-meaning-per-term.md`, What others do).
- **FHIR on reconciliation** is weak or silent: `meta.versionId` has "no fixed order", `Linkage` (maturity 0) has no
  Different, reason or retraction, and Provenance is an optional sidecar (#288, cross-cutting concerns 1 to 3).
- **The web standards the vocabulary already builds on** for that layer: PROV-O and PAV for versions, arrivals and
  provenance; W3C Web Annotation for selectors; nanopublications and SSSOM for judgments (`judgments.md`).
- **openEHR and OMOP** keep their own models inside and exchange FHIR at the edge (memory, not re-read); neither is
  what sources send.
- **Licences.** FHIR's specification is CC0 (memory, not re-read). Its code systems are not all free: LOINC,
  SNOMED CT and others keep their own terms, which the reference tables already handle.
- **This vocabulary.** #128 maps the 59 clinical terms to FHIR R4; `one-meaning-per-term.md` renamed the terms whose
  meaning differed from the FHIR element they are filled from, and ruled that the FHIR pointer is a row in #128's
  mapping table, never an `rdfs:seeAlso` on the term (its row 11). Concepts copied from a FHIR value set carry its
  page as their `dct:source` (`cascade:MedicationLifecycle`, `ontologies/cascade.ttl`).

Sources: https://hl7.org/fhir/R4/, https://hl7.org/fhir/us/core/profiles-and-extensions.html,
https://hl7.org/fhir/R5/medicationstatement.html, https://hl7.org/fhir/R4/rdf.html,
https://hl7.org/fhir/R4/linkage.html, https://hl7.org/fhir/R4/resource.html, https://hl7.org/fhir/R4/license.html,
https://www.w3.org/TR/prov-o/, https://pav-ontology.github.io/pav/, https://www.w3.org/TR/annotation-vocab/,
https://mapping-commons.github.io/sssom/spec-model/. The research is the evidence issue
[#288](https://github.com/jayostis/cascade-vocabulary/issues/288) (the by-record-kind comparison and the cross-cutting
concerns), and #128's mapping (https://github.com/jayostis/cascade-vocabulary/issues/128#issuecomment-6135264321).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| starting point | FHIR R4 + US Core 9; openEHR's and OMOP's own models | clinical content starts from FHIR R4 and US Core: medications, lab results, conditions, allergies, immunizations, procedures, reports and documents, and the person. A new or changed term takes the meaning, value set, cardinality and status axes of the FHIR element it corresponds to, and its name as near as `naming.md` and descriptive naming allow (`ontologies/cascade.ttl`; first applied by #287) | borrowed |
| R5 | FHIR R5 | where R5 differs and the difference matters, the term follows R4 and US Core, because that is what sources send, and the area's note records the R5 change (first applied by #287) | borrowed from what sources send |
| wire format | Bundles, references, extensions, `meta`, contained resources; FHIR RDF's per-resource `fhir:status` | not copied: meanings, not wire format. RDF and the pod already do those jobs (`runtime/pod-layout.ttl`) | diverged: those exist to move documents between servers |
| reconciliation layer | PROV-O, PAV, Web Annotation, nanopub, SSSOM; FHIR `Linkage`, `meta.versionId`, `Provenance` | does not start from FHIR. Versions and arrivals, provenance, judgments, lenses, scoped absence, readings, care hypotheses and the person's responses start from PROV-O, PAV, W3C Web Annotation, nanopub and SSSOM, as `currency.md` and `judgments.md` do; the boundary is settled once, here, and is not argued term by term (`ontologies/cascade.ttl`) | borrowed from the web standards; diverged from FHIR, which is weak or silent there |
| how a term says it follows | the copied-term rule; #128's mapping table | a term copied from a FHIR element carries that element's page as its `dct:source` and FHIR's licence as its `dct:license`, and #128's mapping table lists it as an exact or close match, naming the release. No `rdfs:seeAlso` on the term (`one-meaning-per-term.md`, row 11) and no note for it (#128) | borrowed |
| a departure | deferring to a community scheme; `one-meaning-per-term.md` | a term that departs from FHIR is explained in the decision note for its area, as "looked here, failed because", grouped by area (medications, labs, …), never one note per term. The model case is the medication lifecycle, kept because it is computed per copy across sources where FHIR's status codes describe one server's order (`queries/derivations/medication-lifecycles.rq`) | ours |
| the downstream cost | vocabulary first | the rewrite of adapters, the runtime, kits and tables is a cost, never a reason: they change to fit (#287) | ours |

## Why

**Why FHIR R4 and US Core are the starting point.** (rows "starting point", "R5") Hospitals send FHIR R4 and US
Core, so a term that matches them loses nothing on the way in and maps straight out through the FHIR facade
`version-content.md` settles. The by-kind comparison in #288 found that the vocabulary's gaps are terms it lacks, not
content FHIR cannot hold, so starting from FHIR fills them by copying rather than designing. Copied terms are cheap to
review: the argument is only "is this the right element", not "is this the right model". R5 is the next model, not
what arrives; following it now would make a term mean something no source says.

**Why meanings and not wire format.** (row "wire format") References, extensions, `meta` and contained resources
solve exchange between servers, which a pod does with RDF IRIs, named graphs and kept documents. FHIR RDF's own
shape, typed by inspection with one `fhir:status` across resources, is what `quantities.md` and
`one-meaning-per-term.md` already declined.

**Why the reconciliation layer starts elsewhere.** (row "reconciliation layer") The research in #288 found FHIR
unordered on versions, without a Different or a retraction on identity, and optional on provenance, which is the part
of a pod that has no counterpart in any FHIR store. PROV-O, PAV, Web Annotation, nanopub and SSSOM already carry it.
Settling the boundary once stops every reconciliation term from reopening "why not FHIR?".

**Why the pointer is a copy's `dct:source` and a mapping row.** (row "how a term says it follows") The copied-term
rule already says what a copied term carries, and `one-meaning-per-term.md` ruled the FHIR pointer into #128's table,
which names the release a bare link does not. A term that follows FHIR needs no note: the copy is the reason.

**Why a departure costs a note, grouped by area.** (rows "a departure", "the downstream cost") A divergence is where
the vocabulary costs every reader a translation, so it must be deliberate and findable, as `README.md`'s bar asks.
Grouping by area keeps related departures in one argument, as the medication lifecycle's reasons sit with the other
medication terms. A rewrite downstream is never the reason to depart, or the vocabulary would bend to whichever
consumer was written first.

## Alternatives that lost

- **Design each term afresh, from the prototype or the adapters.** The strongest case: each term fits the pod
  exactly, and nothing foreign is copied. It lost because the prototype's terms are what `one-meaning-per-term.md`
  had to rename, and because every fresh design re-argues a model FHIR already settled.
- **Use FHIR RDF's own terms (`fhir:`) as the clinical terms.** The strongest case: no copying, and a FHIR reader
  knows every term. It lost because FHIR RDF's terms are resource-shaped (`fhir:Procedure` is a resource, not a kind
  of record a pod holds), share `fhir:status` across resources, and type values by inspection; and because
  `version-content.md` keeps the `cascade:` terms as what a version holds.
- **Start from openEHR archetypes or OMOP's tables.** The strongest case: both are mature models built for analysis
  across sources. It lost because sources send FHIR and C-CDA, not either of these, so every term would be a
  translation of what arrives.
- **Start from FHIR for the reconciliation layer too.** The strongest case: one standard for everything. It lost on
  #288's cross-cutting read: `Linkage`, `meta.versionId` and `Provenance` cannot hold what the pod's judgments,
  currency and arrivals hold.
- **Follow R5 where it differs.** The strongest case: R5 fixes R4's mistakes, and sources will move to it. It lost
  because sources send R4 and US Core today; the area's note records the R5 change so the move is a known step.

## Still open

- **Where #128's mapping table lives.** It is an issue comment today. Lean: a file in this repository the moment a
  test reads it, so a new term without a row is caught.
- **When US Core moves to R5 or R6**, whether the starting point moves with it, release by release. Lean: with US
  Core, since that is what sources send.
- The phase 0 items #287 still has open (M15 and M16's note; the B12 threshold's guideline; the readings note's
  prior-art search) are not this note's, and change nothing here.

## What would change our mind

- **Departures in one area outnumber copies**, which would mean FHIR is the wrong starting point there.
- **`version-content.md` is reversed** and FHIR becomes what a version holds; this rule is then subsumed.
- **Sources stop sending US Core**, for a national standard of their own, which would move the starting point to it.
