# What a version's clinical content is

Status: accepted, 2026-10-29; amended 2026-10-30 by `medical-knowledge-in-the-model.md` (no care rules: row "what rules read" and the outputs row "care hypothesis" no longer apply to a rule, and the B12 rule's guideline closes). the owner accepted lean (a) as phase 0 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287)), on the research in
[#288](https://github.com/jayostis/cascade-vocabulary/issues/288). Answers the draft RFC's lean to make FHIR the
stored content of each version, with the `cascade:` clinical terms a rebuildable view (the maintainer's
`starter-shape/medplum/5-design-challenge.md`, section 3, kept outside any repository). No feature rule applies it yet: each row names #287, or the
issue that will write its rule. Depends on `naming.md` (a version is named by its content), `currency.md`,
`judgments.md`, `one-meaning-per-term.md`, `quantities.md`, `partial-dates-and-absent-reasons.md`,
`clinical-terms-follow-fhir.md` (how each borrow below is made) and `readings-and-care-hypotheses.md` (what the
outputs table shows over FHIR). Still open in phase 0: the decision note for the medication matching rules M15 and
M16, on which "long-term metformin" rests; the guideline the B12 rule's threshold and window cite; and
`readings-and-care-hypotheses.md`'s prior-art search.

## Question

A pod keeps every source's document byte for byte (`runtime/pod-layout.ttl:31`), and each record's version says
what that source said, in the `cascade:` clinical terms. The draft RFC proposes making a FHIR resource the version's
content instead, rebuilding the clinical terms as a view, putting a SMART-on-FHIR read interface and an MCP server in
front, adding a persisted indexed store, and allowing erasure that leaves a tombstone. This note settles only the
first of these, and keeps three choices apart, because the evidence answers them differently:

1. **What a version holds**: the content that is hashed into the version's name and that every view is built from.
2. **What rules and queries read**: where a care rule gets its facts. The care-gap epic is a patient-side assistant
   ("long-term metformin, no B12 result in any source held"; "type 2 diabetes, no urine albumin in 12 months"), whose
   rules must cite every fact and say where they looked.
3. **What apps see from outside**: the read interface, and how readings, care hypotheses and the person's responses
   are shown to FHIR clients.

What makes it hard: a pod has no server of record. It mirrors many sources in two formats (FHIR R4 and C-CDA) that
disagree, keeps every copy, joins copies by judgments the person can overrule, and must say where it looked before it
says something is missing.

## What others do

Read on 2026-10-29 by the research this note rests on (#288) unless marked.

- **FHIR R4 and US Core 9.0.0.** FHIR is the content model of every shipped consumer store. Provenance is a sidecar:
  `Meta.source` is "a uri that identifies the source system"; `Provenance.target` is 1..\*. `meta.versionId` has "no
  fixed order", and ids "might or might not" survive a copy between servers. `Linkage` (maturity 0) has `source`,
  `alternate` and `historical`, and nothing for "different", a reason or a retraction; `Linkage.author` may not be a
  Patient or a Device. US Core has **no MedicationStatement profile**: a self-reported medication is a
  `MedicationRequest` with `reported[x]`. `Observation.interpretation` is 0..\* and Must Support in the lab profile.
  US Core requires `DocumentReference` for its ten common note types and `DiagnosticReport` for Report and Note
  exchange.
- **FHIR R5** changes `MedicationStatement.status` to `recorded | entered-in-error | draft` and moves "not taking" to
  `adherence`. A rule over R4 and R5 sources needs a mapping from each status set to the same lifecycle.
- **C-CDA.** Making it FHIR takes a conversion (C-CDA on FHIR; Medplum's converter, Apache-2.0),
  and US Core "does not specify how to assign authorship" after a transformation.
- **Clinical reasoning.** CQL 1.5 over FHIR, with FHIRHelpers, value-set retrieve, `Interval` and `collapse`, and the
  CMS eCQM `CumulativeMedicationDuration` library for exposure. Da Vinci DEQM Gaps in Care (STU5) reports a gap as a
  `DetectedIssue` (code `CAREGAP`, a `gapStatus` modifier extension) whose evidence is a `MeasureReport` or a
  `GuidanceResponse`. `MeasureReport.evaluatedResource` names the data used, not the data looked for. CDS Hooks 2.0
  cards carry `summary`, `indicator` and `source`; feedback is `accepted | overridden`, and "CDS Hooks does not specify
  … the persistence of cards".
- **Outputs.** `Task` may have a Patient as `owner`, which makes it the nearest fit for a person's response.
  `DetectedIssue.mitigation.author` must be a Practitioner. The AI Transparency on FHIR IG (ballot) tags model-authored
  content `AIAST`. The `derivation-reference` extension points into text by offset and length.
- **Shipped stores.** Medplum, Metriport, Apple Health Records, Fasten and AWS HealthLake all store FHIR JSON as
  content. None keeps more than the latest copy per source. Metriport merges duplicates destructively and records
  provenance as a display string. HealthLake links duplicates with `Linkage` and does not merge them. None has a
  person-overridable Different, or currency across paths.
- **openEHR, OMOP.** openEHR keeps its own reference model and archetypes and exchanges FHIR at the edge. OMOP keeps
  its own tables and is loaded from FHIR by ETL. Both are the pattern this note chooses: one's own model inside, FHIR
  outside (memory, not re-read).
- **W3C Web Annotation** already supplies the vocabulary's selectors: main uses `oa:FragmentSelector` and
  `oa:XPathSelector` (`runtime/naming.feature:68`). `oa:TextQuoteSelector` and `refinedBy` are new, proposed by
  `readings-and-care-hypotheses.md`. A quote located by its text survives re-encoding, where FHIR's offset and length
  do not.

Sources: https://hl7.org/fhir/R4/resource.html, https://hl7.org/fhir/R4/provenance.html,
https://hl7.org/fhir/R4/linkage.html, https://hl7.org/fhir/R4/medicationstatement.html,
https://hl7.org/fhir/R5/medicationstatement.html,
https://hl7.org/fhir/us/core/StructureDefinition-us-core-medicationrequest.html,
https://hl7.org/fhir/us/core/StructureDefinition-us-core-observation-lab.html,
https://hl7.org/fhir/us/core/clinical-notes.html, https://hl7.org/fhir/us/core/profiles-and-extensions.html,
https://hl7.org/fhir/us/davinci-deqm/gaps-in-care-reporting.html, https://hl7.org/fhir/R4/detectedissue.html,
https://hl7.org/fhir/R4/guidanceresponse.html, https://hl7.org/fhir/R4/task.html, https://cds-hooks.hl7.org/2.0/,
https://hl7.org/fhir/uv/aitransparency/2026Jan/general_guidance.html,
https://docs.aws.amazon.com/healthlake/latest/devguide/resource-matching.html, https://www.w3.org/TR/annotation-model/.
The research is the evidence issue [#288](https://github.com/jayostis/cascade-vocabulary/issues/288): a comparison by
record kind; the cross-cutting concerns and prior art (with corrections for three claims made from a stale
checkout); and both care-gap rules written twice, as SPARQL over a pod and as CQL over FHIR, and run on 15 cases, with
the rule files inline. The runnable set (case generator, cases, runners) and the draft RFC are inputs the maintainer
keeps outside any repository; #288 inlines the two rules and the CQL library, and nothing else here depends on them.

## Choice

The first table is the three choices; the second is what to borrow from FHIR, ranked; the third is how the epic's
outputs are shown over FHIR; the fourth is the guardrails that keep the choice reversible.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| what a version holds | FHIR R4 resources in every shipped store; openEHR's and OMOP's own models | the `cascade:` clinical terms, as today, every one filled from one FHIR element (or C-CDA's mapping to it) and named as near to it as `naming.md` and descriptive naming allow, per `one-meaning-per-term.md` and `clinical-terms-follow-fhir.md`; the source's FHIR JSON or C-CDA XML stays as the kept document the version is derived from, reached by its revision's `oa:hasSelector` (`ontologies/cascade.ttl`) | diverged at the store, borrowed term by term: a FHIR store holds one server's latest resource, and a pod holds every source in two formats |
| per kind | the by-kind comparison (#288) | one model for every kind, with no kind stored as FHIR while the rest are not. Medications, labs, conditions, allergies, immunizations, procedures, variants and the person keep the `cascade:` terms and gain the borrowed terms below. The one new kind, reports and documents, takes its terms from `DiagnosticReport` and `DocumentReference`, and its content is the kept bytes (#150, written under #287) | as the row above |
| what rules read | CQL over FHIR; DEQM | three things, in this order. First, the lens's derived state: which records count, which copies are one entry, what a source or the person left out, and each source's `answeredAsOf`. Second, each member's own current version for codes, periods, statuses and values, never the entry's summary fields. Third, a small layer of derivations written for rules (exposure periods per member, value sets, classes) that defines exposure as `CumulativeMedicationDuration` does. The rules are SPARQL under `queries/`, and a rule's threshold, window and value set are data, each with its source (#287 writes the rules) | borrowed: the exposure definition from the eCQM library, value sets from VSAC; the record-keeping is ours |
| what apps see | SMART on FHIR; US Core; DEQM; `Task` | a read-only FHIR R4 facade. Each entry is a resource. For a FHIR source the member's own resource is reached as the source sent it; for C-CDA, as converted. A Same group is a plain `Linkage`. Each pull is a `Provenance`. Different and Erroneous have already been applied, so a FHIR client sees the counted record and never a verdict. The MCP server returns the rows of curated questions, each citing its record, version and selector. The facade itself is out of #287's scope; its mapping is a lean, whose home is #128 ("export a pod as FHIR RDF") | borrowed at the interface |
| exactness of absence | `List.emptyReason`; `MeasureReport.evaluatedResource`; none first-class | a "never checked" claim is only as true as what the pod holds, so a source's codings in every system, and its reports, panels and documents, all become records before any rule claims an absence. Each pull records what it asked for as well as when (#287, phase 1) | ours: neither FHIR nor the vocabulary scopes an absence |

What to borrow from FHIR, ranked by what the care-gap epic needs. Every borrow follows
`clinical-terms-follow-fhir.md`: a new term filled from a FHIR element points at the element's definition with
`rdfs:seeAlso` and has a row in #128's mapping table; it carries no `dct:source` or `dct:license`, which are for terms
copied from another vocabulary. The ranking is the one in #288 comment 1, re-ranked for the care-gap epic: what
causes a false "never checked" first (codings, then reports and documents), then the evidence of exposure; the three
items the first draft dropped (a `not-performed` absent reason, the `onset[x]` forms, `bodySite`) close the table. Adapter paths are in `cascade-bridge-adapter-fhir-r4` unless named.

| rank | borrow | FHIR element | the care-gap case that needs it |
|---|---|---|---|
| 1 | every coding a source gave, with its system, for every coded element: a code IRI where `code-iris.md` has a scheme, and otherwise the system, held on a `cascade:CodeSystem` by the existing `cascade:codingSystemUri` (`ontologies/cascade.ttl:1178`, FHIR `Coding.system`), with the code | `Coding.system` + `code` on `Observation.code`, `Medication.code`, `Procedure.code` | uACR or B12 coded only with a lab's local code keeps no `testCode` (`vocab/fhir-gaps.ttl:123`): a false "never checked" |
| 2 | a report or document kind, and a panel as a link between results rather than "no record", by the existing `obo:RO_0002351` "has member" (`ontologies/cascade.ttl:1589`, `rdfs:seeAlso` `Observation.hasMember`) before anything is minted | `DiagnosticReport` (code, `result`, `conclusion`, `conclusionCode`, `presentedForm`), `DocumentReference` (type by LOINC note code, date, attachment), `Observation.hasMember` | a B12 inside a panel or a PDF report makes no record today (`vocab/fhir-gaps.ttl:80`; `cascade-bridge-adapter-ccda/docs/format.md:88`), which gives a false gap; and a reading of "tingling in both feet" has no note record to target |
| 3 | intent and self-report read into `prescribedOrReported` | `MedicationRequest.intent`, `reported[x]` | metformin evidence says "prescribed at Northgate" for a US Core self-reported medication (`in/sparql/medication.rq:77`); a `proposal` or `plan` would count as exposure |
| 4 | the evidence that a medication was taken for a long time, and at what dose | `MedicationDispense` (`whenHandedOver`, `daysSupply`), `dispenseRequest` (`numberOfRepeatsAllowed`, `validityPeriod`), `courseOfTherapyType`, `Dosage` (`timing.repeat`, `doseAndRate.doseQuantity`, `route`) | "long-term" from a US Core source, whose `MedicationRequest` carries only `authoredOn`; dose as a B12 risk modifier |
| 5 | interpretation as coded values, repeatable, with their system, shown in the lab view with the typed value and the reference range | `Observation.interpretation` (v3 ObservationInterpretation) | "high MCV" cited as the lab's own flag rather than the pod's inference. Today the flag is one string with no system, only the first is kept, and the view leaves it out (`ontologies/cascade.ttl:272`; `queries/views/lab-results.rq`) |
| 6 | the person's sex, and that they have died | US Core Individual Sex extension (`Patient.gender` as fallback), `deceased[x]` | a death silences every hypothesis; sex gates most screening rules after the first two |
| 7 | why something was not done or was stopped | `statusReason` on MedicationRequest, MedicationStatement, Immunization, Procedure | "declined", "contraindicated" or "immune" suppresses or rewords a hypothesis |
| 8 | an order as a record | `ServiceRequest` (code, date, status) | "ordered, never resulted" is a different conversation from "never ordered" |
| 9 | where a dose sits in a series, and who reported it | `Immunization.protocolApplied`, `primarySource` | gaps in vaccine series (pneumococcal, hepatitis B in diabetes) |
| 10 | when a condition was recorded and asserted, and the `health-concern` category | `Condition.recordedDate`, `assertedDate`; US Core category | citing "known diabetic since"; a shape that lags US Core 9 (`ontologies/cascade.shapes.ttl:238`) |
| 11 | why a procedure was done, and its period | `Procedure.reasonReference`, `performed[x]` | "retinal exam done for diabetes" |
| 12 | more than one reference range, and the specimen | `referenceRange` with `appliesTo`, `age` and `type`; `Observation.specimen` | rarely needed: LOINC already names the specimen for both rules |
| 13 | a lab result a source marks `not-performed`, read as a statement | the `not-performed` data-absent-reason on `Observation` (`ontologies/cascade.ttl:927`) | "the test was not done, and the source says so" is a statement about the test, where an absent value is not |
| 14 | the other forms of when a condition began | `Condition.onset[x]` and `abatement[x]` as Age, Period, Range and string (US Core makes only the dateTime forms Must Support) | citing "known since" for a condition a source dates by age |
| 15 | where on the body | `Condition.bodySite`, `Procedure.bodySite` | low: no first rule reads it |

The borrows above are content. Two more borrows serve the rules and the outputs. **Value sets** come in as a table
kind holding VSAC and eCQM expansions, cited by the version used; today the B12, uACR and diabetes codes would be
written into the queries, and descendants of 44054006 missed. **Code lists** come in where they fit: IPS
absent-unknown for "no known X" (#152), `AIAST` for content a model wrote, and CDS Hooks' `indicator`.

How the epic's outputs are shown to a FHIR client. Each is stored in the pod in Cascade's terms, per
`readings-and-care-hypotheses.md`. This mapping is inferred from #288 section 7 (its "how each new claim would be
exposed over FHIR" table is marked inference throughout), not settled; its home is #128.

| claim | shown over FHIR as | lost on the way, and what carries it |
|---|---|---|
| care hypothesis | `DetectedIssue`. Its `code` is a Cascade code, never `CAREGAP`, which means a measure gap. `status` is `preliminary`, `detail` is the text, and `evidence.detail` lists the entries plus a `GuidanceResponse` for the rule's run (`module` the rule, `reasonReference` the evidence). Never a `Flag`, and never a `RiskAssessment` unless a model grades the risk | where the rule looked: an extension on the `GuidanceResponse` listing each source and its `answeredAsOf`; the kind of claim and the kind of maker: `author` is a `Device`, and the claim kind is an extension |
| reading of a note | not shown as clinical data. A client sees the note's `DocumentReference`, plus a `Provenance` with `entity.role` quotation, a model `Device` as agent, and `AIAST`. The reading becomes a `Condition` or `Observation` with `verificationStatus` unconfirmed only after the person confirms it | the quote's prefix and suffix, and the assertion status (asserted, negated, hypothetical), which stay in the pod |
| the person's response | `Task`, with `focus` the `DetectedIssue`, `for` and `owner` the Patient, `status` accepted, rejected or completed, and `businessStatus` "discussed with a clinician". Never `DetectedIssue.mitigation`, whose author must be a Practitioner | a retraction, shown as `Task.status` cancelled |

The guardrails that keep the choice reversible during the care-gap epic:

| guardrail | what it keeps open |
|---|---|
| G1. Every clinical term names the FHIR element it is filled from. A term with no FHIR element says, in its area's note, where it looked and why that failed (`clinical-terms-follow-fhir.md`) | the switch to FHIR content stays a mapping, not a redesign |
| G2 (a lean; its home is #128). A version can always be derived again from the kept document by the current adapter (a rule to write, #287) | storing FHIR later is one more re-derivation over bytes already held |
| G3. Rules read derived state, member versions and the rule-facing derivations, never an entry's summary fields and never an adapter's own terms | a change of content model rewrites the derivations, not the rules |
| G4. Hypotheses, readings and responses cite records, versions, documents and selectors, never a clinical term's value | the outputs survive any change to what a version holds |
| G5 (a lean; its home is #128). A "counted" FHIR Bundle (counted resources, plain `Linkage`, one `Provenance` per pull) is built from the pod and checked round-trip on the fixtures | the CQL route is one translation away, and the round-trip check measures how far the terms have drifted from FHIR |
| G6. One content model for every kind during the epic | no half-switched pod with two clinical models |

## Why

**Why the store stays Cascade's while its terms become FHIR's.** (rows "what a version holds", "per kind") The
research agrees that FHIR-as-content would change only the leaf, what one version says. It would leave the graph
around the leaf untouched: revisions, currency, judgments, acts, lenses and findings stay Cascade's whatever the
content is (verified against FHIR's own text: an unordered `versionId`, `Linkage` with no Different or retraction, and
Provenance as an optional sidecar). So the question is narrow: which leaf, FHIR's resource or the `cascade:` terms
filled from it, serves rules and views better.

The inputs did not agree. Two of the three leaned toward FHIR as content: the cross-cutting read (#288 comment 2) and the
experiment (#288 comment 3), whose verdict is that the content a rule reasons over "could just as well be FHIR". The
owner chose (a), the `cascade:` terms, on the arbiter's grounds. First, the exported Bundle is a projection of the
pod, and a projection needs no FHIR content in the pod. Second, every C-CDA source would be a conversion anyway. Third,
the CQL run covered `MedicationStatement` only, which US Core does not profile. The four reasons below are reasoning,
not measurement, and carry #288's **[I]** mark.

1. **C-CDA [I].** For a C-CDA source a FHIR leaf would be a conversion, and the promise that "the version is the
   source's statement" would hold only for FHIR sources.
2. **Versions disagree [I].** R4, R5 and C-CDA disagree inside a single kind: the medication status sets, and
   self-report carried as a resource type in R4 but as `reported[x]` on `MedicationRequest` in US Core. Some layer must
   map each to one lifecycle, and `cascade:MedicationLifecycle` is that layer, already built and tested.
3. **Computability [I].** A rule cannot compare a FHIR decimal stored as JSON, and FHIR RDF types it by inspection
   (`quantities.md`). FHIR content would still need the typed RDF projection for every query.
4. **Negation [I].** FHIR has "two accepted approaches" to it, so a FHIR leaf would import each source's choice, and
   the view would still have to normalise them.

The case for FHIR content is mostly coverage: what the adapters drop and the vocabulary has no term for (the by-kind
comparison's own reading). Coverage is fixed by borrowing terms, which deferring to a community scheme asks for
anyway. The value disciplines have already converged on FHIR: typed partial dates, the quantity node and absent
reasons are in the ontology (`ontologies/cascade.shapes.ttl:121`, `ontologies/cascade.ttl:780`,
`ontologies/cascade.ttl:924`), and the FHIR adapter types dates by precision
(`cascade-bridge-adapter-fhir-r4/in/sparql/allergy-intolerance.rq:12-13`). So the biggest "free" gain the RFC claims,
no loss of dates and precision at the adapter, is already in hand.

**Why rules read member versions under the lens.** (row "what rules read") In the experiment (#288), both care-gap
rules were run on 15 cases, as SPARQL on Oxigraph and rdflib (the two engines agreed on every case) and as CQL. Both
languages got every case right once each read every copy's own content (verified). The two wrong answers came from a
first SPARQL attempt that read the entry's summary dates. In case c3c, a copy that a second hospital first recorded
later shortened the exposure. In case c7b0, R5 joined a 2019 course with a 2026 course and the earlier course
disappeared. The record-keeping went the other way. In CQL it took two invented extensions, a workaround `Provenance`
for an empty pull, a silent merge of two Patient resources, and the filter `not … Judged Erroneous` repeated in every
retrieve. Even then it fell short of the lens: no supersession, no rule currency, and no join across two Linkages. In
SPARQL that was already done before the rule ran. So the lens decides what counts, member versions supply the facts,
and the clinical temporal logic that CQL gets for free (`collapse`, interval arithmetic, value-set retrieve) becomes a
few derivations, defined the way the community's exposure library defines exposure rather than invented anew.

**Why absence has to be made exact first.** (row "exactness of absence"; borrows 1 and 2) Every first rule of the
epic is a claim that something is missing. A test the pod failed to keep, because it was coded locally, sat in a
panel, or arrived only as a report or a PDF, turns a closed gap into a false hypothesis put to a person. That error is
worse than a missed gap, and it is the same whichever content model holds the version. That is why the two borrows
that close it rank above everything else, and why every raise states the sources and their `answeredAsOf`. The
experiment showed that SPARQL could state that scope from what the pod already holds. It also showed that it cannot
yet say what a pull asked for.

**Why FHIR at the edge.** (row "what apps see"; the outputs table) Every SMART app, every FHIR library and every
model trained on FHIR can read a FHIR facade, and none of them needs to learn Cascade's terms to do so. DEQM's use of
`DetectedIssue` and `GuidanceResponse` is HL7's own pattern for a care gap, and `Task` is the one resource a Patient
may own. Verdicts are applied before export because FHIR cannot carry a Different, and a client that is sent one can
only drop it.

**Why guardrails, not a trial now.** (the guardrails table) The epic will build rules, outputs and their tests. If
those rules read Cascade terms through a thin derivation layer and cite only records and selectors, then a later
switch of the leaf changes the adapters and the derivations, and nothing the epic built. The round-trip Bundle (G5)
turns "is FHIR content better?" from an argument into a number that the epic's fixtures produce as a side effect.

## Alternatives that lost

- **A FHIR resource as each version's content, with the `cascade:` terms rebuilt from it.** The strongest case: it
  defers to the community scheme wholesale. Every shipped PHR does it. An adapter could never drop what a source
  said. A view fix would need no re-import. CQL, value sets and `CumulativeMedicationDuration` would apply directly,
  and outsiders and models would already know the model. It lost on four grounds.
  - C-CDA sources would still be conversions.
  - The R4, R5 and C-CDA status sets would still need Cascade's lifecycle mapping.
  - A FHIR leaf would still need the typed RDF projection before any SPARQL rule could compare its values.
  - Its two strongest gains are available without it. A view fix without re-import comes from re-deriving versions
    from the kept bytes (G2). The CQL route comes from the counted Bundle (G5).

  The experiment's CQL ran only on `MedicationStatement`, which US Core does not profile. On US Core
  `MedicationRequest` sources, its easy exposure rule needs the very dispense and `dispenseRequest` evidence that
  borrow 4 brings in under either model.
- **Cascade's terms kept as they are, with FHIR borrowed only when a case forces it** (a narrow form of the chosen
  position). The strongest case: no churn, and every term is earned. It lost because absence rules are only as true
  as their coverage. Waiting until a case forces a borrow means waiting for a false hypothesis to be put to a person.
- **A different model per kind: FHIR content for procedures and immunizations, where FHIR is clearly better, and
  Cascade's terms elsewhere.** The strongest case: each kind gets its best model. It lost because every view, lens
  and rule would have to read two models, and the kinds where FHIR is better are better through elements that can be
  borrowed.
- **Rules in CQL over the counted Bundle from the start.** The strongest case: CQL is the better language for the
  clinical part, rule 2 is 13 lines in CQL against 33 in SPARQL, and eCQM libraries exist. It lost, for now, because
  the runtime would gain a second engine and a projection on its critical path before one rule ships. G5 keeps the
  route open, and the first trigger below says when to take it.

## Still open

- **The medication matching rules M15 and M16 need their decision note** (open on #286). "Long-term metformin" rests
  on which copies of a medication are one entry, so phase 1's matcher item on #287 is sequenced last until it lands.
- **The B12 rule's threshold and window cite a guideline.** ADA 2025 Section 9 says "long-term" with no number; the
  experiment used 2 years. The rule's parameters are data, and the guideline is chosen before the rule ships.
- **`readings-and-care-hypotheses.md`'s prior-art search,** which may change how the outputs table shows a care
  hypothesis and a reading.
- **The coding term.** Is it one general term for a coding (system and code) beside the per-system code IRI
  properties, or does the general term replace them? Lean: the code IRI wherever `code-iris.md` has a scheme, and the
  system-and-code pair only for the rest, the system by the existing `cascade:codingSystemUri`
  (`ontologies/cascade.ttl:1178`) before anything is minted. `cptCode` becomes one of the two, not a special case. The panel link is the
  existing `obo:RO_0002351` (`ontologies/cascade.ttl:1589`), likewise before anything is minted.
- **The names**, under the rule on descriptive names: the report or document kind, the rule-facing derivations, and
  the term on a pull for what it asked.
- **The derivation layer's interface.** Is it part of the vocabulary under `queries/derivations/`, or is it the
  rules' own `queries/questions/`? Lean: derivations, since more than one rule reads each.
- **The counted Bundle.** Is it built in the vocabulary as a CONSTRUCT, or in cascade-runtime-js? And what FHIR shape
  does it give a C-CDA member?
- **Erasure, the persisted store, the facade's sharing policy.** These are the RFC's other proposals, and each needs
  its own note. This note leans on none of them, except that erasure must say what it takes with it: readings quote
  the erased text.

## What would change our mind

- **The first five care rules,** written both ways through G5, where CQL over the counted Bundle is clearly shorter
  or more often right after the derivation layer exists. That reopens choice 2, not choice 1.
- **New rules need new terms.** More than two of the next five rules need a FHIR element the content lacks, after
  borrows 1 to 6. That would show the borrowed terms cannot keep pace with the rules, and it reopens choice 1.
- **The round-trip drifts.** G5's check fails on a term that has no FHIR element and no "looked here, failed because".
  That reopens choice 1 for that kind.
- **C-CDA turns out to be a small share of the sources,** because most arrive by patient-access FHIR APIs. The
  conversion argument goes.
- **A store computes over FHIR directly:** the persisted store indexes FHIR JSON with typed values, or FHIR RDF types
  its decimals and dates as `quantities.md` and `partial-dates-and-absent-reasons.md` do. The computability argument
  goes.
- **R6, or a US Core version, makes the medication statuses agree** across resources and versions. The lifecycle
  argument weakens.
- **An outside contributor's rule library or app** needs FHIR inside the pod and cannot be served by the facade.
