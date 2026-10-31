# A person sets an allergy's status

Status: draft, 2026-10-31, for [#329](https://github.com/jayostis/cascade-vocabulary/issues/329), from the
maintainer's ruling there that a person can set an allergy's status, that the vocabulary tracks where each status came
from, and that a disagreement, or an item that may need revisiting, is easy to find. Replaces the scenario's "never an
allergy's status from Alex's own entry" (issue [#4](https://github.com/jayostis/cascade-vocabulary/issues/4), the view
rules under the events) and `cascade:statusOnlyFromDocuments`. Depends on `currency.md` for the lead and the Before,
`judgments.md` for what a verdict's member may be, `one-meaning-per-term.md` for the two status terms, and
`clinical-terms-follow-fhir.md` for where FHIR is the starting point. Leans only, until the maintainer's review.

## Question

Alex outgrew a peanut allergy. A hospital's record still says `active`. Today the only thing Alex can do is mark the
hospital's record Erroneous, which hides the whole allergy, reaction and criticality included, and says the record was
wrong when it was only out of date (`currency.md:53`). The entry takes its status only from a member derived from a
document: `queries/derivations/records.rq:15` sets `statusOnlyFromDocuments` true for an allergy alone, and
`queries/derivations/status-sources.rq:20,29,39` drops every member the person entered for such a kind.

How does a person state an allergy's status, which status does the entry show, how does the hospital's status stay
visible with its source, and how is a disagreement put in front of someone, including the case where a hospital
re-asserts `active` after the person said `resolved`? What makes it hard: the pod has no server of record to settle
it, a hospital will keep re-sending its list, nothing in the pod may be edited, and an allergy list is a safety list,
so the person's word must not silence a hospital's without a trace.

## What others do

- **FHIR R4 AllergyIntolerance** has two status axes. `clinicalStatus`, "The clinical status of the allergy or
  intolerance", from `allergyintolerance-clinical`: `active`, "The subject is currently experiencing, or is at risk of,
  a reaction to the identified substance"; `inactive`, "The subject is no longer at risk of a reaction to the
  identified substance"; `resolved`, "A reaction to the identified substance has been clinically reassessed by testing
  or re-exposure and is considered no longer to be present". `verificationStatus`, "Assertion about certainty associated with
  the propensity, or potential risk, of a reaction to the identified substance", from `allergyintolerance-verification`:
  `unconfirmed`, `confirmed`, `refuted`, "A propensity for a reaction to the identified substance has been disputed or
  disproven …", and `entered-in-error`. ait-1: "AllergyIntolerance.clinicalStatus SHALL be present if verificationStatus
  is not entered-in-error"; ait-2: it "SHALL NOT be present if verification Status is entered-in-error" (verified).
- **FHIR's authorship** of the statement: `recorder`, "Individual who recorded the record and takes responsibility for
  its content", and `asserter`, "The source of the information about the allergy that is recorded", each may reference
  a Patient (verified). A patient-stated allergy is a resource of its own with the Patient as asserter; FHIR has no
  element that ranks two resources' statuses, and no way to say one resource's status overrides another's.
- **FHIR on disagreement**: `DetectedIssue` and `Flag` are a clinical system's records about a patient, with a
  practitioner author (`judgments.md:48` read them for the acknowledgement); neither lists two sources' statuses side
  by side.
- **C-CDA** carries an allergy's status as a SNOMED CT code on the observation, which the C-CDA adapter crosswalks to
  FHIR's code (`one-meaning-per-term.md:88-89`, row 4); it has no patient-authored override either.
- **PROV-O** says who generated an entity and what it was derived from; the pod already uses its absence, a revision
  with no `prov:wasDerivedFrom`, as "the person entered this" (`queries/derivations/lead-member-candidates.rq:2-3`).
- **This vocabulary.** A person's own record leads any entry it is in, by rule (`currency.md:77-78`, way 3), and where
  members disagree on a field every value shows, the lead's first (`currency.md:46`). A Before across two members'
  current revisions says which leads (`currency.md:76`, way 2) and touches neither record's own currency
  (`queries/derivations/revision-judgments.rq:4-6`). Every member's `clinicalStatus` is already a member value of the
  allergies view (`queries/views/allergies.rq:20,36`), which `queries/questions/entry/What it shows.rq:1-7` lists with
  its From, and a record's label says "own entry" or its author and file (`queries/labels.rq:24-26`).

Sources: FHIR R4 AllergyIntolerance definitions (https://hl7.org/fhir/R4/allergyintolerance-definitions.html), its
clinical status codes (https://hl7.org/fhir/R4/codesystem-allergyintolerance-clinical.html) and verification codes
(https://hl7.org/fhir/R4/codesystem-allergyintolerance-verification.html), all read 2026-10-31; PROV-O
(https://www.w3.org/TR/prov-o/); the history of `statusOnlyFromDocuments`, below.

**Why `statusOnlyFromDocuments` was set.** No reason is recorded anywhere. The rule first appears in issue #9's table,
"taken only from a member translated from a document … never from Alex's own entry" (row "allergy | status"), written
into `allergy-status-sources.rq` by 6711a7b (2026-09-30) from the scenario's view rules, which say the same and give
no reason; the scenario's one entered allergy, APP-ALG-PEANUT, states no status at all (issue #4, P16 and the E3
table), so the rule changed no row of the scenario. cf61c5d (2026-10-04) merged the two status derivations and made
the rule every kind's; 1ba37a2 (2026-10-04) narrowed it back to allergies as a column of the `records.rq` table,
"as the scenario says". Nothing else depends on it: its only reader is `status-sources.rq:18,24,34`; it is written by
`records.rq:10,14-25`, declared at `ontologies/cascade.ttl:888`, and asked of by one fixture,
`tests/fixtures/records-of-every-kind`; cascade-runtime-js never reads it (it reads `cascade:statusFrom` only to name
it, `packages/runtime/src/phrases.ts:375`). No kit is affected: the only entered allergy in any kit is Alex's, which
states no status (`conformance/alex-rivera/scripted-input/alex/entries/a1.ttl`). The likely intent, inferred, is the
safety one in the Question: a person must not silence a hospital's allergy. The review line below answers that intent
without the rule.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| how the person states a status | FHIR: a patient-stated AllergyIntolerance with the Patient as asserter; a judgment (`judgments.md:45`) | through their own allergy record, stating `clinicalStatus` and, where they dispute it, `verificationStatus`, joined to the entry by a Same as any record is. A later change is a new revision of that record. No judgment kind (rule C6, amended; `ontologies/cascade.ttl`, no new clinical term) | borrowed from FHIR: a status is clinical content on a version |
| which status the entry shows | `currency.md` "The lead", way 3 | for an allergy, the status of a member the person entered, where one states a status; otherwise as today, the members that state one ranked by source change time, `cascade:observedAsOf`, then least IRI. `statusOnlyFromDocuments` is deleted and the `records.rq` column becomes `statusFromPersonEnteredRecordFirst`, true for an allergy alone (rule C6, amended; `queries/derivations/status-sources.rq`) | ours, applying `currency.md`'s lead to the status |
| what stays visible beside it | `currency.md:46`, every value shows, the lead's first | every member's `clinicalStatus` and `verificationStatus` stay member values with their From, and the entry also states the `verificationStatus` of the member its status came from (rule C6; `queries/views/allergies.rq`) | ours |
| the disagreement | FHIR `DetectedIssue`, `Flag` | `entry/What needs review` lists an allergy entry once per pair of a record the person entered and a member derived from a document that state different clinical statuses, or where the person's verification status is `refuted` and the document's is not. The row names the person's record and the document's, each labelled with its source, and two new columns give what each states, `?recordValue` and `?otherRecordValue`. It reads "a document disagrees with the person's status" when the document's current revision was observed before the person's, and "a document since the person's status disagrees" when after, which is the revisit (rule C9, new; `queries/questions/entry/What needs review.rq`) | ours: FHIR has no reconciliation, `clinical-terms-follow-fhir.md:70` |
| how a person answers it | `currency.md`, way 2 and row "Before"; `cascade:Acknowledged` | a person's Before across the two members' current revisions, the document's the earlier, takes the row off. A later state of the document is a new revision the Before does not name, so it is listed again, as the revisit. An app that lets the person set a status from the entry may file the Before in the same act (rule C9) | borrowed from `currency.md`; no new verdict |
| refuted, from the person | FHIR `verificationStatus` `refuted`, ait-1 | "I never had it" is `verificationStatus "refuted"` on the person's own record, with whatever `clinicalStatus` the app writes. `RefutedAtSource` leaves out a record whose current revision is derived from a document, as its label says, "refuted at its source" (`ontologies/cascade.ttl:1026-1027`); the person's own refuted record stays a member, leads, and the entry shows it. A person's `entered-in-error` still leaves their own record out (`queries/derivations/excluded-at-source.rq`) | borrowed from FHIR |
| asserter and recorder | FHIR `asserter`, `recorder` | not copied. That the person entered a record is PROV's fact, a current revision derived from no document, which `lead-member-candidates.rq:2-3` already reads. A hospital's record whose asserter is the Patient is the hospital's record of what it heard, and ranks as a document | diverged; see Why |

## Why

**Why the person's own record, not a judgment.** (row "how the person states a status") A status is clinical
content, and content is on a version (`CLAUDE.md`, "Content is on a version"); `clinical-terms-follow-fhir.md:67` makes
FHIR the starting point for it, and FHIR states a patient's own account as a resource of its own, with its own
`clinicalStatus`. A judgment is a belief about records past what any source defines, "that two records are one fact"
(`judgments.md:12-13`), with a verdict and members (`judgments.md:45,47`); "Alex no longer reacts to peanuts" is not a
belief about the hospital's record but a fact about Alex, with a date and an author, which a record holds and a
verdict would not. The record route needs nothing new: a person's own record already leads (`currency.md:77-78`), the
Same that joins it is the person's (`judgments.md:60`), its revisions carry the session's clock (`currency.md:40`), and a
second change of mind is a new revision, ranked as every revision is.

**Why the person's status leads for an allergy.** (row "which status the entry shows") `currency.md` already rules
that the person's own record leads any entry it is in "since it is the one statement the person authored"
(`currency.md:77-78`), and that where members disagree every value shows, the lead's first (`currency.md:46`). Taking
the status from the latest-observed member instead, as conditions do, would let any later revision of the hospital's
record take the status back: a hospital that adds a reaction text writes a new version (`currency.md:43`), observed
after Alex's entry, still saying `active`. Alex would re-enter "resolved" after every change the hospital makes. The
person's status leads, and the hospital's later revisions surface on the review page instead of silently winning.

**Why the column is renamed, not dropped.** (row "which status the entry shows") Medications and conditions are out
of #329's scope, and for them the rule stays the latest member that states one, as today: Priya's loratadine entry
takes its status from Fernhill's record though her own leads (`conformance/priya-natarajan/expected/medications.ttl:46-47`).
Which kinds put the person's status first is a fact about a kind, so it stays a column of `records.rq`'s table, as
1ba37a2 placed `statusOnlyFromDocuments`. The new term looked at FHIR, which has one resource per statement and no
element saying which of several statements a merged entry shows, and at PROV, which has derivation and no ranking;
neither holds it, so it is ours, a derived term like `cascade:statusFrom` (`ontologies/cascade.ttl:1053`).

**Why both statuses on the review line.** (rows "what stays visible beside it", "the disagreement") The ruling asks
for the disagreement to be easy to see. `entry/What it shows` already gives every member's status with its From, so
the view keeps the facts; but a reader of `What needs review` should not have to ask a second question to learn what
the disagreement is. One row per pair names the two records, whose labels say "own entry" and the document's author
and file (`queries/labels.rq:24-26`), and the two values. The columns are named for any field, not for status, so the
criticality line (`What needs review.rq:49-57`) can fill them later without another rename.

**Why the revisit is told by observation order.** (row "the disagreement") A document observed before the person's
status is one the person could have seen when they set it; one observed after is news. `cascade:observedAsOf` is the
pod's ranking of observations already (`currency.md:40`, `:88-91`), so the two readings cost one comparison. A re-pull
of the same hospital state writes nothing (`currency.md:43`), so a daily pull does not relist; only a new state does.

**Why a Before answers it, and nothing new.** (row "how a person answers it") A Before across two members' current
revisions already means "show this one first" (`currency.md:76`) and changes neither record's currency
(`revision-judgments.rq:4-6`). Filed with the document's revision as earlier, it says exactly "I have seen this
document's status, and mine stands". Because it orders revisions, not versions, a later state of the document is a
revision it does not name and shows again, which is `currency.md:113-116`'s reason for ordering revisions applied to
the revisit. `cascade:Acknowledged` was the other candidate; its one member is a finding (`judgments.md:48`), and a
disagreement here is derived from the records, not filed by an act, so there is no finding to acknowledge.

**Why refuted from the person is not left out.** (row "refuted, from the person") `excluded-at-source.rq:13` leaves
out any record whose current version says `refuted`, whoever wrote it, so today a person's "I never had it" removes
the person's own record and leaves the hospital's `active` alone in the entry: the opposite of what they said. The
reason's label already says "at its source" (`ontologies/cascade.ttl:1026-1027`); a refutation from a source is a
retraction of that source's record, and a refutation from the person is the person's statement, which leads and is
listed against the hospital's. Two fixtures model a refuted record with no `prov:wasDerivedFrom`
(`tests/fixtures/left-out-at-source/records.ttl:14-16`, `tests/fixtures/every-reason-a-record-is-in-no-view/records.ttl:51-54`),
so by the structural test they are entered records; they gain a document, and keep their meaning.

**Why asserter is not borrowed.** (row "asserter and recorder") FHIR's `asserter` says whom the recorder heard it from;
a hospital's record with the Patient as asserter is still the hospital's, written at a visit, perhaps years ago, and
re-sent with every pull. What the ruling needs is "the person said this in the pod", and the pod already knows that
from provenance, which `clinical-terms-follow-fhir.md:70` puts outside FHIR. No adapter writes an asserter today
(no such term in `ontologies/cascade.ttl`). The FHIR facade of `version-content.md:98` can write `asserter` Patient for
an own-entry record on the way out.

## Alternatives that lost

- **A judgment kind of its own, "the person sets this entry's status".** The strongest case: it targets the entry the
  person is looking at, with no record of its own to keep. A status is content, not a belief about records; the
  verdict would need a value, a date and a later change of mind, which a record's revisions already carry; and an
  entry's name lasts one build (issue #4, the view rules), so a verdict over an entry has nothing stable to name.
- **Erroneous over the hospital's record**, today's only tool. The strongest case: it exists and needs nothing.
  It hides the reaction and criticality with the status, and says "wrong" of a record that was only out of date
  (`currency.md:53`).
- **The latest-observed member's status, as for conditions.** The strongest case: one rule for every kind, and a
  hospital's re-assertion shows at once. Any new revision of the hospital's record, for any field, takes the status
  back, and the person re-enters theirs after every one; the review line shows the re-assertion without overruling
  the person.
- **Keep the person's status out, and only flag it.** The strongest case: a safety list errs toward `active`. It is
  the ruling's opposite, and the entry would show a status its own lead contradicts.
- **A finding filed per disagreement, acknowledged as findings are.** The strongest case: it reuses
  `cascade:Acknowledged` and the review page's finding lines. A finding is filed by an act; this disagreement is a
  function of the records, so a finding would be one more file per pair per change, recomputable from what is held.

## Still open

- **Conditions and medications.** Whether they also take the person's status first, so the column is deleted and
  `status-sources.rq` ranks as the lead does. Lean: yes for conditions, which share `clinicalStatus` and would share
  the review line; medications in an issue of their own, since L1's lifecycle reads `cascade:statusFrom`
  (`queries/derivations/medication-lifecycles.rq:113`) and a person's "active" over a prescriber's later "stopped"
  changes `My active medications`.
- **`My active allergies`** lists an entry whose status is `active` (`queries/questions/pod/My active allergies.rq:8`);
  an entry the person calls resolved and a hospital calls active is not listed. Lean: keep it out, as #327's ruling
  of 2026-10-31 keeps inactive and resolved out, and let the review line carry the disagreement; reopen if the
  comparison shows a model missing it. #327 words its `?status` "not stated" as "an allergy no document gives a
  status"; after this, "no member", whichever merges second.
- **A new revision whose status did not change** relists the row as a revisit. Lean: keep it; the hospital touched the
  record and still says `active`, which is the revisit, and the cost is one Before.
- **Two documents that disagree**, with no record of the person's. Not listed today; lean: out of this note.
- **The criticality line** filling `?recordValue` and `?otherRecordValue`. Lean: yes, when it is next touched.

## What would change our mind

- People filing a Before on most allergy rows, which would say the line is noise, not news.
- Hospitals writing new revisions of unchanged allergies often enough that revisits dominate the review page.
- A FHIR or US Core element for a patient's override of a recorded status, which would replace the lead rule here.

## Build plan

One pull request in cascade-vocabulary, sized for one builder. Each fixture is committed red before the query it
tests changes. No kit changes; no runtime pair is expected, since cascade-runtime-js runs these queries as written and
reads none of the terms by name but `cascade:statusFrom` (`phrases.ts:375`); the compatibility check confirms it.

Red first, one fixture per behaviour:

1. `tests/fixtures/status-from-the-latest-that-states-one/`: extend the expected rows. `allergyFromDocument` and
   `allergyEntered` take their status from `allergyEntered`, and `allergyEnteredAlone` from itself; the conditions'
   rows are unchanged. Reword the manifest's comments.
2. `tests/fixtures/records-of-every-kind/`: the query and rows ask for `statusFromPersonEnteredRecordFirst`, true for
   "Allergy" and false for every other kind.
3. `tests/fixtures/a-person-and-a-document-disagree-on-an-allergys-status/`, new: peanut, a document's `active`
   observed 2026-01-01 and the person's `resolved` entered 2026-02-01, joined by the person's Same; latex, the
   person's `resolved` entered 2026-01-01 and a document's `active` observed 2026-03-01; sulfa, both `active`. Asks
   `entry/What needs review` (peanut "a document disagrees with the person's status", latex "a document since the
   person's status disagrees", each with both values; sulfa not listed) and the allergies view's statuses (peanut
   `resolved` from the person's record, every member's status present).
4. `tests/fixtures/a-before-answers-an-allergy-status-disagreement/`, new: the peanut pair with a person's Before
   naming the document's revision as earlier, not listed; a second pair with the same Before and a second document
   revision observed after it, listed as "a document since the person's status disagrees".
5. `tests/fixtures/a-person-refutes-an-allergy/`, new: the person's own record with `verificationStatus "refuted"`
   and `clinicalStatus "inactive"`, joined to a document's `active`. `record/Why it is in no view` gives it no row;
   the entry shows `inactive` and `refuted` from the person's record; the review line lists the pair.
6. Fallout, staying green: give `:refuted`'s revision a `prov:wasDerivedFrom` in
   `tests/fixtures/left-out-at-source/records.ttl` and `tests/fixtures/every-reason-a-record-is-in-no-view/records.ttl`;
   add `?recordValue` and `?otherRecordValue` to the head of the ten `.srj` files that answer
   `entry/What needs review`.

Then the files:

- `queries/derivations/records.rq`: the column renamed, true for `cascade:AllergyOrIntolerance` alone; the header.
- `ontologies/cascade.ttl`: delete `cascade:statusOnlyFromDocuments` (`:888`); declare
  `cascade:statusFromPersonEnteredRecordFirst`, derived, boolean, domain `cascade:Record`.
- `queries/derivations/status-sources.rq`: for a kind whose column is true, where the entry holds a member the person
  entered that states a status, only such members compete; otherwise every member that states one, as today. A member
  states a status when it states `clinicalStatus`, `workflowStatus` or `verificationStatus`; a FHIR source never sends
  a verification status without a clinical one but entered-in-error (ait-1), which is left out already, so documents
  rank as before.
- `queries/derivations/excluded-at-source.rq`: the `refuted` row only for a record whose current revision is derived
  from a document; the header.
- `queries/views/allergies.rq`: the entry's `cascade:verificationStatus` from its `cascade:statusFrom` member, and each
  member's among its values. No shape change: `AllergyOrIntoleranceShape` already lists it
  (`ontologies/cascade.shapes.ttl:178`).
- `queries/questions/entry/What needs review.rq`: the new branch, the two columns, the header.
- `runtime/currency.feature`: C6 amended, an allergy entry's status from a record the person entered; C9, new, the
  disagreement line and the Before that answers it. Each first line names this note's rows; each points at the
  fixtures above for its examples, as C6 does.

Affected tests: `tests/test_query_fixtures.py -k "status or records-of-every-kind or allerg or left-out or
every-reason or review"`, then `tests/test_features.py` and `tests/test_vocabulary.py`.
