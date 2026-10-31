# Medication matching: which copies are one medication

Status: accepted, 2026-10-31, by the maintainer's ruling on
[#293](https://github.com/jayostis/cascade-vocabulary/issues/293#issuecomment-6540369052) (decision d of the care-gap
epic, [#287](https://github.com/jayostis/cascade-vocabulary/issues/287)). It is the note `medications.md` says rules M15
and M16 still need. It depends on `medications.md` (rows "exposure start", "exposure end", "no end" and "no period": the
period it compares), `one-meaning-per-term.md` (row "1. clinical state and workflow state": M14's period test for
conditions, which this follows) and `naming.md` (row "document, finding": a version that tightens a rule retracts
nothing).

## Question

The matcher joins two medication records into one entry when they name one drug: one NDC (R5), one RxNorm product code
a drug products table lists (R11), or a brand and its generic by a brand generics table (R10). Up to the rule list's
version 17 it does so whatever their dates. A person who took metformin from 2019 to 2021 and started it again in 2026
then has one metformin entry, and a rule that reads the entry reads one course: in case c7b0 of the experiment on #288
([comment](https://github.com/jayostis/cascade-vocabulary/issues/288#issuecomment-6507076048)) the 2019 course
disappeared behind the 2026 one. When are two copies of one drug one medication?

What makes it hard: a pod has no server of record to say which copies are one course; sources date a medication
differently (a start of use, a prescription's written date, a supply), or not at all; and monthly fills of one
prescription leave gaps between them that a course does not have.

## What others do

Read on 2026-10-31.

- **The matcher's own rule for conditions, R8 (rule M14).** Two conditions of one code join when their periods overlap,
  both bounds counting; a condition with no onset joins nothing; one whose abatement is unknown runs on while its status
  keeps it going (`queries/matcher/same-code-and-period-read-as-ranges.rq`, `runtime/matcher.feature`, rule M14).
- **The CMS eCQM library `CumulativeMedicationDuration`** (4.1.000; `medications.md` cites it and its source) defines
  a medication's period, the one `queries/derivations/medication-exposure-periods.rq` derives as
  `cascade:medicationExposureStart` and `cascade:medicationExposureEnd`. It combines periods in a separate step:
  `CumulativeDuration` collapses them, and `RolloutIntervals` lays them end to end (`medications.md`, verified there).
- **CQL's `collapse`**: "adjacent intervals within a sorted list are merged if they either overlap or meet", and
  "meets" is true when "the first interval ends immediately before the second interval starts" (verified). Two courses
  a day apart are one under `collapse`.
- **FHIR R4** has no rule for which `MedicationStatement`s or `MedicationRequest`s are one course; `MedicationRequest`
  links a refill to the one before by `priorPrescription`, and a dispense to its prescription by
  `authorizingPrescription`. Neither is a period test.

Sources: https://cql.hl7.org/09-b-cqlreference.html (Collapse, Meets);
https://github.com/cqframework/ecqm-content-qicore-2024/blob/07c68e5e76d96d167627469f0face771c702023f/input/cql/CumulativeMedicationDuration.cql;
https://hl7.org/fhir/R4/medicationrequest-definitions.html; https://hl7.org/fhir/R4/medicationdispense-definitions.html.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| same course | R8's period test (M14) | two medication records join only when the drug test passes, unchanged (R5's NDC, R11's product code, R10's brand and generic), and their exposure periods share at least one day; from the rule list's version 18, rule M15 (`queries/matcher/same-ndc-code-and-overlapping-exposure-periods.rq`, `same-product-code-in-current-tables-and-overlapping-exposure-periods.rq`, `same-brand-generic-and-overlapping-exposure-periods.rq`) | borrowed from M14; diverged from CQL's `collapse`, which merges periods that only meet |
| a period | `CumulativeMedicationDuration` | from `cascade:medicationExposureStart` to `cascade:medicationExposureEnd`, both days included; with no end, on with no end while `cascade:medicationExposureOngoing` holds, and the start day alone otherwise (`medications.md`, rows "exposure start" to "no period") | borrowed; a course with no end that is not active is not known to have lasted past its start, as `medications.md` row "no end" reads it |
| an ongoing course | M14's active condition | runs on to today: compared as having no end, so it joins any later course of the drug | borrowed; "today" is read as no end so the comparison reads no clock, and a run, a recheck and a fixture agree whatever day they run; the two differ only for a course whose start is after the day the matcher runs |
| no dates | M14: no onset, no join | a record with no exposure start joins no other medication record | borrowed |
| a gap | CQL `collapse` merges intervals that meet | any break, even one day, keeps two records apart; no tolerance in days | diverged: a tolerance is a clinical judgment of how long a break still makes one course, which a pod should not make for the person |
| names | R5, R10, R11 under version 17 | the rules and their justifications keep their names (`cascade:SameMedicationCodeRule`, `cascade:SameProductCodeRule`, `cascade:SameBrandGenericRule`), each with a new query in version 18; each term's comment says what it means from version 18 | ours |
| what is kept apart | M16's "possibly the same medication" | a pair of one product or one NDC that the period test keeps apart is listed on "What needs review" as possibly the same medication (`queries/questions/entry/What needs review.rq`, rule M16), so a person can join a course with a gap | ours |

## Why

**Two courses are two medications.** A course is what a person took from a start to an end. Joining every copy of one
drug made the entry show one course, the latest arrival's, and the earlier course was lost to every reader of the view
(c7b0). Copies that describe one course overlap: a hospital's list and a clinic's prescription of the same metformin
share the days it was taken. So "same drug and a shared day" keeps copies of one course together and courses apart. We
treat this as the same course for now: a working rule, until a source that says which course a copy belongs to is held.

**The period is the one already derived.** Item 5 defined a medication's exposure as `CumulativeMedicationDuration`
does, conservatively: a partial start is its last day, a partial end its first, and a supply counts from the earliest
day it may. A second definition for matching would let a view and a rule disagree on when a drug was taken.

**No tolerance.** CQL merges intervals that meet, and a care measure may allow a gap of days before a course counts
as stopped. Both are judgments about clinical meaning, and the pod holds facts (`medical-knowledge-in-the-model.md`).
A break of one day is a break in what the sources said, and the pair goes to a person, not into one entry.

**Same rule names.** Version 18 tightens three rules; it does not add rules. M18 is built for this: the open that
first runs version 18 asserts again every claim its rules still reach, and files one finding naming the claims it no
longer reaches, the pairs now apart. New rule names would make that finding name every medication claim of version 17,
including the pairs the new rules join again, and file each again under a new claim. Which query a claim was judged
by is already on its assertion (rule list version and query hash, M4), as it was when versions 7, 12 and 14 changed the
queries of R5, R6 and R8.

**Measured.** Each comparison was timed in Oxigraph JS on a pod of 16,500 records with 3,000 medications, each with an
exposure start (a third ended, a third ongoing, a third with a start alone), in clusters of up to 20 copies of a drug,
three runs each. Bound to a step's records, the NDC rule took 2 to 5 ms (version 17: 2 to 3), the product code rule 72
to 265 ms (79 to 175), the brand generic rule 2 to 5 ms (4 to 8); run over the whole pod, 526 to 1,213 ms (382 to
787), 759 to 2,452 ms (570 to 1,207) and 195 to 583 ms (184 to 566).

## Alternatives that lost

- **A tolerance of N days between courses.** The strongest case: monthly fills of one prescription leave gaps of a few
  days, and a tolerance would join them into the course they belong to. It lost because no N is right for every drug,
  and a fill reaches its course by its prescription, not by its dates (#300, lean (b): a dispense linked by
  `authorizingPrescription`).
- **Merging periods that meet, as CQL's `collapse` does.** The strongest case: it is the community's interval
  arithmetic, and a course stopped one day and restarted the next is plausibly one. It lost to the ruling's "any break,
  no join": meeting is a tolerance of zero days, and the pair still reaches a person through "What needs review".
- **New rule and justification names (the issue's lean: `SameMedicationCodeAndPeriod` and the like).** The strongest
  case: a judgment's justification would say the period was compared, as R8's `SameCodeAndPeriod` does. It lost as
  "Same rule names" in Why says: version 18 tightens the rules, and M18 handles a tightening without re-filing every
  claim.
- **Joining an undated copy to any dated course.** The strongest case: a medication list often omits dates, and the
  copy surely belongs to some course. It lost because there is no telling which, and a wrong join hides a course; the
  pair is listed for review instead.

## Still open

- A brand and its generic kept apart by the period test share no code, so "What needs review" does not list them; a
  question reading the brand generics table could. Lean: wait until a pod shows such a pair.
- How a dispense reaches its course (#300, Q2). Lean (b): a `MedicationDispense` record linked to its prescription.
- "Today" for an ongoing course whose start is after the day the matcher runs. Lean: leave it as no end until a source
  is seen sending a future start of use.

## What would change our mind

- Pods whose medication entries split into many courses that a person rejoins on "What needs review": a tolerance, or
  the prescription link, would then be earning its place.
- A source that states which course a copy belongs to, or a chain of `priorPrescription` links held in the pod: a join
  by that would replace the period test for the copies that carry it.
