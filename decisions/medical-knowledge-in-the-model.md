# Medical knowledge in the model, not the protocol: what a pod gives a model looking for care gaps

Status: draft, 2026-10-30. The owner's direction of 2026-10-30, for phases 2–5 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287)). Amends `readings-and-care-hypotheses.md`: its
rows "verdict", "reading of text" and "response to a care hypothesis" stand; its row "care hypothesis" keeps only the
model's, since no rule raises one, and its Still open items about a rule's hypothesis (how a derived one is named,
whether it needs a term) close. Amends `version-content.md`: its row "what rules read" and its outputs row "care
hypothesis" no longer apply to a rule, and the B12 rule's guideline, open in both notes, closes with no rule to cite
it. Depends on `clinical-terms-follow-fhir.md`.

## Question

The care-gap epic planned rules: a query per gap ("long-term metformin and no B12 test"), with thresholds, windows and
value sets as data citing a guideline, that raise a care hypothesis the same way every time. A model would find "the
rest". Should medical knowledge of that kind (if a condition, then a test, at an interval) be in the protocol at all?

What makes it hard for a pod:
- Guidelines change, and a coded rule goes stale without anyone noticing.
- The knowledge is broad. Many such associations exist; a protocol could ship only a few.
- The code lists that say who a rule applies to are often licensed (SNOMED CT, CPT) and cannot be published in the
  feed (jayostis/cascade-reference-tables#68).
- The protocol is a contract for records: what a record says, where it came from, how copies join. Medical knowledge
  is not part of that contract.

## What others do

- **HL7 CPG-on-FHIR and CQL** encode recommendations as computable knowledge artifacts over value sets, versioned under
  CRMI's lifecycle; **eCQMs** are released yearly. Both are kept out of the record resources: FHIR's own knowledge
  artifacts (PlanDefinition, Library, Measure, in its Clinical Reasoning module) are separate from the resources that
  hold a patient's record.
- **WHO SMART Guidelines** separate the data dictionary from the decision logic in each Digital Adaptation Kit.
- **The record resources of FHIR, C-CDA and OMOP** carry no care rules. openEHR keeps its decision logic in a separate
  language, GDL.
- **LLMs as the source of the knowledge.** ChronoEvo (arXiv 2610.30631, a 2026 preprint) gave 14 models 1,709
  guideline revisions with the new evidence in the prompt. The primary model (Qwen3-4B) recognised 90.8% of revisions
  but fully incorporated 58.5%; across models, full incorporation ran from 50.7% to 77.9%. When clinicians
  adjudicated 300 answers, the gap widened to about 40 points. (Inferred, not measured there: a model holds far more
  such associations than a rule set we could write.)
- **This project's own comparison** (2026-10-30,
  [posted on #287](https://github.com/jayostis/cascade-vocabulary/issues/287#issuecomment-6529455264)): the same model
  found the planted gaps as well, or better, from pasted records as from today's pod. The pod's errors had three causes:
  - what it does not hold (note and report text; a "historical result" label);
  - facts it holds one question deeper than the views a model asks first;
  - a few plain misreadings.

  Its false questions ran from 0 to 3 a run, against 0 to 1 for pasted records.

Sources: FHIR R4 Clinical Reasoning (https://hl7.org/fhir/R4/clinicalreasoning-module.html), CPG-on-FHIR
(https://hl7.org/fhir/uv/cpg/), CRMI (https://hl7.org/fhir/uv/crmi/), eCQI Resource Center (https://ecqi.healthit.gov/),
WHO SMART Guidelines (https://smart.who.int/), C-CDA (https://www.hl7.org/ccdasearch/), OMOP CDM 5.4
(https://ohdsi.github.io/CommonDataModel/cdm54.html), openEHR GDL2
(https://specifications.openehr.org/releases/CDS/latest/GDL2.html), ChronoEvo (https://arxiv.org/abs/2610.30631). The
comparison: https://github.com/jayostis/cascade-vocabulary/issues/287#issuecomment-6529455264.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| medical knowledge (condition → test, interval) | CPG-on-FHIR, CQL, eCQMs: artifacts kept out of the record resources | none in the vocabulary: no care-rule queries, no rule feed. The model brings the knowledge, and says it is its own (#287) | diverged from #287's first plan; agrees with the record resources, which carry no rules |
| what the pod gives a model | FHIR read APIs; MCP | read-only tools over the pod (`cascade-mcp`, over `cascade-runtime/tools`) whose first answers state each source's own values, with record citations and the scope of any absence (jayostis/cascade-runtime-js#548; #316) | borrowed MCP as the transport; the tools are ours |
| a care hypothesis | `readings-and-care-hypotheses.md` row "care hypothesis" | a model's only, minted once with its model version and the queries it ran; shown as unreviewed until the person accepts it (#287 lean g) | amends that row: no rule-derived kind |
| how it is judged | eCQM test decks; model evals | an eval harness (`packages/evals` in cascade-runtime-js): synthetic people with machine-readable answer keys, pasted records as the control arm, blind scoring, token budgets, run off CI (jayostis/cascade-runtime-js#549) | diverged from test decks: there is no rule's expected output to test, only answers to judge |

## Why

**Knowledge goes stale; records don't.** (row "medical knowledge") A record says what a source said on a date and stays
true of that. A rule says what a guideline said, and becomes wrong when the guideline changes. Keeping only records in
the protocol means a protocol release never has to track guideline editions.

**The model's breadth beats any rule set we could write.** (row "medical knowledge") A rule set covers only the gaps
someone coded. The model covers the long tail: a radiologist's follow-up nobody booked, a drug stopped at one hospital
and active at another. Its weaknesses are applying a change precisely and giving the same answer twice. Those are why
the pod checks facts, not why it should hold knowledge.

**The pod's job is facts a model can't get wrong by reading.** (row "what the pod gives a model") The comparison showed
this job is still undone. A model reading pasted records saw every source's state, the reactions, the flags and the
text. The views a model asks first showed one lead value per entry, and runs that asked one question deeper found the
rest. The pod earns its place when its first answers carry everything the records say, merged and dated, at a fraction
of the tokens, and that is measured, not assumed.

**A hypothesis is the model's, so it is stored as the model's.** (row "a care hypothesis") With no rule, nothing derives
a hypothesis again on each run. What the model raised can be found again, compared after a model update, and answered
by the person only if it is minted once, with what produced it, as `readings-and-care-hypotheses.md` already mints a
model's.

**An answer can only be judged, so it is judged against a key.** (row "how it is judged") A test deck checks a rule's
output against the output it must give. A model's answer varies from run to run and is right or wrong only against
what the records show. So the harness keeps a key written before any run, scores answers blind, repeats each arm, and
compares with the obvious alternative, pasted records.

## Alternatives that lost

- **Rules for the common cases, the model for the rest** (#287's first plan). The strongest case: the same answer
  every time for the cases that matter most, each citing a guideline. It lost because each rule goes stale silently,
  needs licensed code lists to say who it applies to, and covers a handful of gaps. Every records-arm run in the
  comparison found every planted gap without one.
- **Guideline statements as data, evaluated by one generic query.** The strongest case: dated, cited, versioned
  knowledge a model can propose changes to, in the shape CPG-on-FHIR gives a recommendation. It lost for the protocol,
  as it puts knowledge back into the contract. A model may still read such a table later, as a tool outside the
  vocabulary, if an eval shows it helps.

## Still open

- Whether a maintained table of guideline statements, outside the vocabulary, improves the model's answers enough to
  keep. An eval decides it.
- How the model's medical claims are labelled to the person, and which guideline they name when it can.
- The concept layer: whether entries resolve to open concepts (MONDO, RxNorm ingredients, LOINC groups) for the
  model's queries.

## What would change our mind

- An eval where a maintained rule beats the model on a gap the model keeps missing, at a cost worth paying.
- A regulatory reading under which a pod that answers a model's questions must itself hold the clinical logic.
