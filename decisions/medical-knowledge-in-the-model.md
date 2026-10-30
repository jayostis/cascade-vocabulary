# Medical knowledge in the model, not the protocol: what a pod gives a model looking for care gaps

Status: draft, 2026-10-30. The owner's direction of 2026-10-30, for phases 2–5 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287)). Amends `readings-and-care-hypotheses.md`: its
rows "reading of text" and "response to a care hypothesis" stand; its row "care hypothesis" keeps only the model's
hypothesis, since no rule raises one. Depends on `version-content.md` and `clinical-terms-follow-fhir.md`.

## Question

The care-gap epic planned rules: a query per gap ("long-term metformin and no B12 test"), with thresholds, windows and
value sets as data citing a guideline, that raise a care hypothesis the same way every time. A model would find "the
rest". Should medical knowledge of that kind (if a condition, then a test, at an interval) be in the protocol at all?

What makes it hard for a pod:
- Guidelines change, and a coded rule goes stale without anyone noticing.
- The knowledge is broad. Thousands of such associations exist; a protocol could ship only a few.
- The code lists that say who a rule applies to are often licensed (SNOMED CT, CPT) and cannot be published in the
  feed (reference-tables#68).
- The protocol is a contract for records: what a record says, where it came from, how copies join. Medical knowledge
  is not part of that contract.

## What others do

- **HL7 CPG-on-FHIR, CQL and eCQMs** encode recommendations as computable knowledge artifacts over value sets, kept
  apart from the record and versioned yearly. They are published by guideline and measure bodies, not by record
  formats.
- **WHO SMART Guidelines** separate the data dictionary from the decision logic in each Digital Adaptation Kit.
- **Record formats (FHIR, C-CDA, openEHR, OMOP)** carry no care rules. openEHR keeps its decision logic in a separate
  language, GDL.
- **LLMs as the source of the knowledge.** ChronoEvo (arXiv 2610.30631, 2026) found models recognise 91% of guideline
  revisions but fully apply 52–78%. Even so, a model knows far more associations than any rule set holds.
- **This project's own comparison** (2026-10-30, posted on [#287](https://github.com/jayostis/cascade-vocabulary/issues/287)): the
  same model found the planted gaps as well, or better, from pasted records as from today's pod. The pod's errors came
  from text it does not hold, and from facts it holds one question deeper than the views a model asks.

Sources: CPG-on-FHIR (https://hl7.org/fhir/uv/cpg/), WHO SMART Guidelines (https://smart.who.int/), openEHR GDL
(https://specifications.openehr.org/releases/CDS/latest/GDL2.html), ChronoEvo (https://arxiv.org/abs/2610.30631). The
comparison and the prior-art research behind it are summarised on #287.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| medical knowledge (condition → test, interval) | CPG-on-FHIR, CQL, eCQMs: artifacts kept apart from the record | none in the vocabulary: no care-rule queries, no rule feed. The model brings the knowledge, and says it is its own (#287) | diverged from #287's plan; agrees with record formats, which carry no rules |
| what the pod gives a model | FHIR read APIs; MCP | read-only tools over the pod (`cascade-mcp`, over `cascade-runtime/tools`) whose answers state each source's own values, with record citations and the scope of any absence (#287) | ours |
| a care hypothesis | `readings-and-care-hypotheses.md` row "care hypothesis" | a model's only, minted once with its model version and the queries it ran; shown as unreviewed until the person accepts it (#287 lean g) | amends that row: no rule-derived kind |
| how it is judged | eCQM test decks; model evals | an eval harness (`packages/evals` in cascade-runtime-js): synthetic people with machine-readable answer keys, pasted records as the control arm, blind scoring, token budgets, run off CI (#287) | ours |

## Why

**Knowledge goes stale; records don't.** A record says what a source said on a date and stays true of that. A rule
says what a guideline said, and becomes wrong when the guideline changes. Keeping only records in the protocol means a
protocol release never has to track guideline editions.

**The model's breadth beats any rule set we could write.** A rule set covers only the gaps someone coded. The model
covers the long tail: a radiologist's follow-up nobody booked, a drug stopped at one hospital and active at another. Its
weaknesses are applying a change precisely and repeating itself. Those are why the pod checks facts, not why it should
hold knowledge.

**The pod's job is facts a model can't get wrong by reading.** The comparison showed this is the job still undone. A
model reading pasted records saw every source's state, the reactions, the flags and the text. A model reading the pod
saw one lead value per entry. The pod earns its place when its answers carry everything the records say, merged and
dated, at a fraction of the tokens, and that is measured, not assumed.

## Alternatives that lost

- **Rules for the common cases, the model for the rest** (#287's original plan). The strongest case: the same answer
  every time for the cases that matter most, each citing a guideline. It lost because each rule goes stale silently,
  needs licensed code lists to say who it applies to, and covers a handful of gaps. The model already finds those
  gaps: every run found them in the comparison.
- **Guideline statements as data, evaluated by one generic query** (the prior-art research on #287).
  The strongest case: dated, cited, versioned knowledge a model can propose changes to. It lost for the protocol, as
  it puts knowledge back into the contract. A model may still read such a table later, as a tool outside the
  vocabulary, if an eval shows it helps.

## Still open

- Whether a maintained table of guideline statements, outside the vocabulary, improves the model's answers enough to
  keep. An eval decides it.
- How the model's medical claims are labelled to the person, and which guideline they name when it can.
- The concept layer: whether entries resolve to open concepts (MONDO, RxNorm ingredients, LOINC groups) for the
  model's queries (the prior-art research on #287).

## What would change our mind

- An eval where a maintained rule beats the model on a gap the model keeps missing, at a cost worth paying.
- A regulatory reading under which a pod that answers a model's questions must itself hold the clinical logic.
