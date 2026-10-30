# Readings, care hypotheses and verdicts: what a maker concludes that is not a verdict

Status: accepted, 2026-10-29; amended 2026-10-30 by `medical-knowledge-in-the-model.md` (no care rule raises a hypothesis: row "care hypothesis" keeps only the model's, and the Still open items about a rule's hypothesis and the B12 rule's guideline close). the owner accepted lean (c) as phase 0 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287)), on the research in
[#288](https://github.com/jayostis/cascade-vocabulary/issues/288), **to stand once the prior-art search below is
done**: a row that search overturns comes back to the owner, and the rest are built as written. Drafted 2026-10-28.
Amends `judgments.md` and asks how `naming.md`'s second test reads; depends on `judgments.md`, `naming.md`,
`currency.md`, and `version-content.md`, whose outputs table says how each kind here is shown over FHIR. No feature
rule applies it yet: phase 4 of #287 stores readings, hypotheses and responses. Still open in phase 0: this note's
prior-art search; the decision note for the medication matching rules M15 and M16; and the guideline the B12 rule's
threshold and window cite.

## Question

A pod's judgments today are verdicts: `cascade:Same`, `cascade:Different`, `cascade:Erroneous`, `cascade:Before`,
`cascade:About`, `cascade:Acknowledged` and `cascade:ClockDiscounted` say what records are, what a record is about, when a
clock is not to be trusted, or how the person answers a finding, and once a lens counts one, a view or the review page changes (`ontologies/cascade.ttl`, "Judgments"). The
care-gap assistant (#287) adds three more kinds of conclusion:

- **A reading of text:** a model quotes a visit note ("tingling in both feet") and says what concept it takes the
  quote to name.
- **A care hypothesis:** a rule or a model concludes, from entries and the absence of others, that a test or an option
  is worth raising with a clinician ("long-term metformin, no B12 result in any source held").
- **A response to a care hypothesis:** the person accepts it, dismisses it, or marks it discussed with a clinician.

Each must name its maker and reason, and be retractable without touching a name, as `naming.md`'s second test asks of
everything past the definition. But they do not behave as verdicts do. A reading must never become a diagnosis by
itself; a care hypothesis must never change a view; and accepted, dismissed and discussed are a lifecycle, not a
statement of what records are. Is each a `cascade:Judgment` with new verdicts, a kind of its own beside it, or a term
another vocabulary already defines?

Two constraints make it harder. The words are taken: "finding" already names a Bridge finding
(`cascade:BridgeFindingKinds`), a finding for review (`cascade:FindingForReview`, whose kinds include a source that
reported older states and a clock behind, `currency.md`'s rollback and clock findings) and
`cascade:GeneticVariantFinding`; "question" names a curated query under `queries/questions/`. And the assistant
must not claim to recommend: #287 draws the line FDA's "Policy for Device Software Functions and Mobile Medical
Applications" draws, whose Appendix A lists, among software functions that are not devices, those that "help guide
patients to ask appropriate questions to their physician relevant to their particular disease, condition, or concern"
(https://www.fda.gov/media/80958/download, issued September 28, 2022; read 2026-10-29). A term that says a pod
recommends would claim what that line excludes.

## What others do

The FHIR resources and CDS Hooks below were read at their source on 2026-10-29 for the research in #288 (verified).
**Every other entry has not been read for this note yet** (unverified, from memory); the search that follows must
read each and correct this section.

- **FHIR** has several resources near each kind (verified, #288). `DetectedIssue` R4 is "a specific instance of a
  potential issue for a particular patient", with `implicated`, `evidence`, `author` (Practitioner, PractitionerRole
  or Device), `mitigation` (whose `author` may only be a Practitioner or PractitionerRole) and `status`; it is near a
  care hypothesis. `GuidanceResponse` is "the result of invoking a decision support service", with `module[x]`,
  `performer` a Device, `reasonReference` and `dataRequirement`. `RiskAssessment` carries a predicted outcome with a
  probability. `Flag` is a warning "not used to convey information to a specific individual". `Task` may have a Patient
  as `owner` and `requester`, with `focus`, `status` and `businessStatus`; it is the one output resource a person may
  own. `ClinicalImpression` records a clinician's assessment (memory). None is near a reading: the `derivation-reference`
  extension points into text by offset and length only, and FHIR has no assertion status for an extracted concept.
- **Da Vinci DEQM Gaps in Care** (STU5, verified, #288) reports a care gap as a `DetectedIssue` with code `CAREGAP` and
  a `gapStatus` modifier extension, whose `evidence.detail` is a `MeasureReport` or a `GuidanceResponse`: HL7's own
  pattern, for a payer's measure verdict over a period.
- **CDS Hooks 2.0** cards carry `summary`, `indicator` (info, warning, critical), `source` and `suggestions`; feedback
  is `accepted | overridden`, and "CDS Hooks does not specify … the persistence of cards" (verified, #288).
- **The AI Transparency on FHIR IG** (ballot) tags model-authored content `AIAST`, with the model a `Device` named as a
  Provenance agent (verified, #288).
- **C-CDA** separates a Problem Concern Act (a concern being tracked, with a status) from the Problem Observation it
  holds; the concern's lifecycle is apart from the observation's content, as a response's is from a hypothesis's.
- **openEHR** splits archetypes into OBSERVATION, EVALUATION and INSTRUCTION; EVALUATION archetypes hold assessments,
  including, it is believed, health-risk and recommendation archetypes in the Clinical Knowledge Manager.
- **OMOP CDM** has `NOTE_NLP`, a row per term a language-processing system found in a note: the snippet, its offset,
  the system that found it, and whether the term is asserted, negated or hypothetical. It is the nearest health
  standard to a reading.
- **W3C Web Annotation**, which the vocabulary already imports (`oa:hasSelector`, `oa:hasSource`, `oa:hasBody`,
  `oa:hasTarget`, `oa:motivatedBy` and `oa:classifying`, in `ontologies/cascade.ttl`), has `oa:Annotation` with a body, a
  target, a motivation (`oa:describing`, `oa:identifying`, `oa:assessing`, `oa:questioning`, among others) and
  `oa:TextQuoteSelector` for an exact quote with its prefix and suffix. The vocabulary already makes one kind of
  conclusion an annotation: `cascade:FindingForReview` is a subclass of `oa:Annotation` whose body is its kind and
  whose motivation is `oa:classifying`.
- **PROV-O** gives what every kind shares: `prov:wasAttributedTo`, `prov:wasDerivedFrom`, `prov:used`, and retraction
  as an activity that `prov:invalidated` the entity, as `judgments.md` already uses and `queries/lenses/everyday.rq`
  tests.
- **Nanopublications** wrap any assertion with its provenance and publication info; `judgments.md` borrowed the split.
- **SSSOM** gives `confidence`, which `judgments.md` leaves open for a judgment (its row "confidence").
- **SEPIO** (Scientific Evidence and Provenance Information Ontology) models assertions, the evidence lines for and
  against them, and their confidence.
- **ECO** (Evidence and Conclusion Ontology) types how a conclusion was reached, separating manual from automatic
  assertion and curator inference from computational inference.
- **Biolink Model** marks each statement with a knowledge level (an assertion, a prediction, a statistical
  association, an observation) and an agent type (manual, automated, text mining, computational model). It is the
  nearest found to the distinction this note needs: what kind of claim, and what kind of maker.
- **Micropublications** distinguish claims, the statements supporting them and their evidence, for scientific
  argument.
- **SIO** (Semanticscience Integrated Ontology) has classes for hypothesis and for the roles of evidence.

**The search still to do.** Read each unverified entry above and say what it actually defines: first Biolink, ECO,
SEPIO, OMOP `NOTE_NLP` and the DEQM profiles beyond the Gaps in Care page. Then look further: openEHR's recommendation
and health-risk archetypes; SNOMED CT's situation-with-explicit-context concepts (licence permitting); HL7's clinical
reasoning module beyond `GuidanceResponse`; the ontologies for argument and hypothesis in science (SWAN, the Argument
Interchange Format, ORKG); vocabularies for natural-language-processing output (NIF, and the OMOP `NOTE_NLP`
conventions); and any ontology for AI-generated content and its provenance. For each, record whether it gives a
reading, a care hypothesis, a response, a claim kind or a maker kind, and whether the pod can borrow it as copied
terms are borrowed, with `dct:source` and `dct:license`.

Sources: FHIR R4 `DetectedIssue` (https://hl7.org/fhir/R4/detectedissue.html), `GuidanceResponse`
(https://hl7.org/fhir/R4/guidanceresponse.html), `RiskAssessment` (https://hl7.org/fhir/R4/riskassessment.html),
`ClinicalImpression` (https://hl7.org/fhir/R4/clinicalimpression.html), `Flag` (https://hl7.org/fhir/R4/flag.html),
`Task` (https://hl7.org/fhir/R4/task.html); Da Vinci DEQM Gaps in Care
(https://hl7.org/fhir/us/davinci-deqm/gaps-in-care-reporting.html); AI Transparency on FHIR
(https://hl7.org/fhir/uv/aitransparency/2026Jan/general_guidance.html); CDS Hooks (https://cds-hooks.hl7.org/2.0/);
openEHR Clinical Knowledge Manager (https://ckm.openehr.org/); OMOP CDM 5.4 `NOTE_NLP`
(https://ohdsi.github.io/CommonDataModel/cdm54.html#note_nlp); Web Annotation Vocabulary
(https://www.w3.org/TR/annotation-vocab/); PROV-O (https://www.w3.org/TR/prov-o/); nanopublication guidelines
(https://nanopub.net/guidelines/working_draft/); SSSOM (https://mapping-commons.github.io/sssom/spec-model/); SEPIO
(https://github.com/monarch-initiative/SEPIO-ontology); ECO (https://www.evidenceontology.org/); Biolink Model
(https://biolink.github.io/biolink-model/); Micropublications, Clark, Ciccarese and Goble, J Biomed Semantics 2014
(https://doi.org/10.1186/2041-1480-5-28); SIO (https://github.com/MaastrichtU-IDS/semanticscience). The research is
the evidence issue [#288](https://github.com/jayostis/cascade-vocabulary/issues/288): its cross-cutting concerns and
prior art, section 7, read the FHIR outputs, DEQM, CDS Hooks and the text-span options; the care-gap assistant's plan
is #287.

## Choice

Accepted as lean (c): every row stands unless the search overturns it. What goes beyond it (a shared superclass, the
kind of claim and maker, confidence, names) is under Still open, as leans.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| verdict | nanopub assertion; SSSOM row | `cascade:Judgment` as `judgments.md` has it, with its verdicts; unchanged (`ontologies/cascade.ttl`) | as `judgments.md` |
| reading of text | Web Annotation; OMOP `NOTE_NLP` | an `oa:Annotation`, as `cascade:FindingForReview` already is, whose target is the note's record with an `oa:TextQuoteSelector`, whose body is the concept the maker takes the quote to name, with an assertion status (asserted, negated, hypothetical) as `NOTE_NLP` keeps; it never enters a view as a record of its own, and counts only once the person confirms it (#287) | borrowed from Web Annotation, already imported; the status from `NOTE_NLP` |
| care hypothesis | FHIR `DetectedIssue`, `GuidanceResponse`; DEQM; CDS Hooks | a kind of its own, its members the entries it rests on, with its rule or its guidance, and the scope of any absence it claims (which sources, answered as of when). A rule's is derived when the rule raises it and never stored, as a view is; a model's is minted once, with the query it ran and its model version, as `judgments.md` mints a model's judgment. It never changes a view. Over FHIR it is a `DetectedIssue` with a `GuidanceResponse` for the run, as `version-content.md`'s outputs table says (#287) | borrowed fields; ours as a pod term unless the search finds one |
| response to a care hypothesis | FHIR `Task` owned by the Patient; `DetectedIssue.mitigation`; C-CDA concern status; CDS Hooks feedback | a `cascade:Judgment` by the person whose member is the hypothesis, with a verdict for accepted, dismissed or discussed with a clinician: the same move as `cascade:Acknowledged`, whose member is a finding (`judgments.md`, row "acknowledgement"). Over FHIR it is a `Task` with `for` and `owner` the Patient, never `DetectedIssue.mitigation`, whose author must be a Practitioner (#287) | ours, within `judgments.md`; borrowed at the interface |

## Why

**Why not more verdicts.** (rows "care hypothesis", "response to a care hypothesis") A verdict that counts changes a
view: a Same draws one entry on two records. A care hypothesis that counted the same way would let a model's guess,
or a rule's, reshape the person's record, where it should only ever be raised as something to ask. Accepted, dismissed
and discussed say where a hypothesis stands with the person, not what any record is; they are a lifecycle, and the one
part of it that is a belief, the person's response, is a judgment, as an acknowledgement of a finding already is,
which is why that row stays in `judgments.md`.

**Why a reading is an annotation.** (row "reading of text") A reading is a statement about a span of a document:
these words, at this place, name this concept. That is what Web Annotation is for, and the vocabulary already uses
its selectors for where a revision arrived and its `oa:Annotation` for a finding for review. A quote located by its
text survives re-encoding, where FHIR's offset and length do not (#288). Kept as an annotation, a model's reading of
"tingling in both feet" is evidence a hypothesis may cite and a person may confirm, and never a condition in the
conditions view.

## Alternatives that lost

- **Every kind a `cascade:Judgment`, with new verdicts.** The strongest case: one mechanism, one retraction, one lens,
  and `naming.md`'s second test read literally. It lost, as a lean, because a verdict that counts changes a view, and a
  reading or a hypothesis must not, so each lens and view would have to tell verdicts from the rest.
- **A model's output stored as a record, marked as made by a model.** The strongest case: it is what cascade-cli's
  `cascade_write` tool does today (`cascade:dataProvenance cascade:AIExtracted`, in cascade-cli's
  `src/lib/mcp/tools.ts`, a term this vocabulary does not define; #152 asks where a record came from beyond its import,
  including self-reported, device and AI-extracted origin), and every existing view and query works on it
  unchanged. It lost because the default is then inclusion: every query must remember to filter, and a model's guess
  reaches views, rules and an export to a clinician as if a hospital had written it.
- **Readings and hypotheses kept outside the pod, in the app.** The strongest case: the pod holds only what sources
  said and what people decided. It lost because a person's response must point at something that survives the app,
  and a model's conclusion that cannot be found again cannot be retracted or compared after a model update.
- **A care hypothesis stored as a FHIR `DetectedIssue`.** The strongest case: it is HL7's own care-gap pattern (DEQM).
  It lost because the scope of an absence has no element there, `CAREGAP` means a measure gap, and its mitigation
  cannot be the person's; `version-content.md` shows it as one at the edge instead.

## Still open

- **The prior-art search above,** done and written into What others do; a row it overturns comes back to the owner.
- **A shared superclass (lean).** Each kind is a `prov:Entity` with `prov:wasAttributedTo` its maker,
  `prov:wasDerivedFrom` what it rests on, and retraction as an activity that `prov:invalidated` it; a common
  superclass for an attributed, retractable conclusion, with `cascade:Judgment` beneath it, so `naming.md`'s second
  test reads "an attributed, retractable conclusion" and `cascade:Judgment` stays the verdicts. Borrowed from PROV;
  the superclass is ours if no search result names it. Why PROV and not `cascade:Judgment`: what `naming.md`'s second
  test protects, that a belief can be wrong and be retracted without touching a name, is attribution and retraction,
  which PROV already gives every entity, and widening the class to hold every kind would make each lens and view test
  which kind it is reading.
- **Kind of claim and kind of maker (lean).** Borrow the distinction (an assertion copied from a source, a
  deterministic derivation, a model's prediction, a reading) from Biolink's knowledge level and agent type, ECO or
  `AIAST` if their terms fit, rather than mint one. Each question is asked once: #152 already asks where a record came
  from beyond its import (self-reported, device and AI-extracted origin), so this waits on #152's answer before any
  term is added. It matters most for a model, whose output cannot be recomputed: a rule's hypothesis is true of the
  rows and rebuilt on every run, a model's is minted once and depends on its version.
- **Confidence (lean).** SSSOM `confidence`, the term `judgments.md` leaves open for a judgment, as a number for a
  model's reading or hypothesis; a rule's hypothesis has none, since it is true of the rows. FHIR `RiskAssessment`
  probability is the alternative.
- **How a derived hypothesis is named.** A rule's hypothesis is derived and never stored, so a response Judgment that
  points at it must still resolve after the rule stops raising it, and the hypothesis must be able to record that it
  closed and why. How it is named so that both hold is open.
- **The names,** for the shared superclass, the reading, the care hypothesis and its response verdicts. "Care
  hypothesis" is a working name: what the assistant raises is a reason to ask, not a proposed explanation, and the name
  should say which.
- Whether a rule's care hypothesis needs a term at all, or is only the rows of a curated query under
  `queries/questions/`, keyed as cascade-runtime-js's `find_changes` tool keys its findings, with only the person's
  response stored.
- Whether a reading's body is a code IRI only, or may be free text where no code fits.
- Whether the existing findings (Bridge findings, and `cascade:FindingForReview`, itself already an `oa:Annotation`)
  are kinds of the same superclass, and whether `cascade:GeneticVariantFinding`, a source's own statement, should keep
  the word.
- How a lens counts a model's reading or hypothesis: the trusted-makers list `judgments.md` describes, extended to
  these kinds, or a person's acceptance only. Accepted, lean (g) of #287: a person's acceptance only, with a model's
  shown as unreviewed until then.

## What would change our mind

- The search finds a vocabulary that already separates readings, hypotheses and verdicts with maker kinds and
  retraction; the pod borrows it and mints none of the rows above.
- A lens or view that must treat a reading or a hypothesis exactly as it treats a verdict, which would make the
  distinction cost more than it saves.
- A regulatory reading that makes any stored care hypothesis a recommendation, which would push hypotheses out of the
  pod and into the app.
