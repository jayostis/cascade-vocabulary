# Which revision of a record is current

Status: draft, 2026-10-21, from the review on #130. Replaces A3, A4's "the one the record is at", A5's "after the
record's last one", the single line of `prov:wasRevisionOf`, `derivations/current-revisions.rq`, and M1's and M3's
reliance on that line; adds `rec:asOf`, a Before verdict and a review question. Names are `naming.md`.

## Question

A record's state arrives by several paths (a pull, Apple's copy, a C-CDA, a person's edit), on several devices, in
any order. Which of its revisions does the pod show, so that a stale copy never un-corrects or un-retracts a record,
two devices agree without talking, and a person can fix what the pod got wrong?

## What others do

- **FHIR** gives each version `meta.lastUpdated`, "when the resource last changed", and an opaque `meta.versionId`;
  a client that holds copies from several paths is on its own.
- **openEHR** keeps branches in a version tree under one versioned object; which branch is current is the system's.
- **git** keeps every head and leaves a fork to a person, who writes the merge commit; a ref says which is current.
- **CRDTs** make a replicated set converge by union, with every answer a function of the set.
- **Provenance (PROV)** records when an entity was generated and what it was derived from, and leaves "current" to the
  reader.

Sources: FHIR R4 `Meta` (https://hl7.org/fhir/R4/resource.html#Meta); openEHR versioning
(https://specifications.openehr.org/releases/RM/latest/common.html#_change_control_package); git branching
(https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging); Shapiro et al., CRDTs
(https://hal.inria.fr/inria-00555588); PROV-O (https://www.w3.org/TR/prov-o/).

## Choice

- **A revision carries two clocks.** `prov:generatedAtTime`, when the pod wrote it, and `rec:asOf`, when the source was
  observed saying this state: the first of the document's `rec:answeredAsOf`, the document's `pav:retrievedOn`, the
  source's own change time, and the act's start. For an entry it is the session's start. The second, third and fourth
  rungs are device clocks for a live pull or an entry; the first two are the exporter's.
- **The source's own version** (`meta.versionId`, `meta.lastUpdated`, or a C-CDA document's `effectiveTime`) sits in a
  node nested in the revision, hashed with it, never on the revision itself.
- **A revision names the record's heads it saw** as `prov:wasRevisionOf`, one or several; a sync is a union of files.
- **What an arrival writes.** A first arrival writes the record, its version and a revision. An arrival whose version
  is the current revision's writes nothing. An arrival whose (version, source version, source time) a revision already
  holds, and which would not become current, writes nothing. Otherwise a revision, with its heads.
- **Current is derived, never stored:** first drop any revision an Erroneous names and any a counting Before places
  before another candidate; of the rest, take those at the latest source change time, together with those carrying
  none; of those, the greatest `rec:asOf`; then the least IRI, which is arbitrary and said so.
- **Before** is a person's judgment, verdict Before, two revisions of one record in order; machines never make one;
  a Before outranks every clock, as Different outranks Same.
- **The review page** lists every record whose current state the source's change time did not decide, with the state
  shown, the state not shown, and the reason ("observed later", or "no basis"); the fix is one Before.
- **Erroneous** is for a state that is wrong, and hides it from every view; a stale state is not wrong and stays.

## Why

The quantity that must decide is the source's state, not the messenger's arrival: "latest to arrive" let a
transmitter's late copy of an old state overrule a correction, and A3 let a string the record had seen suppress new
content, dropping a counter reset's correction. The source's change time ranks states of the source: a copy of an
older state never beats a newer one, whatever clock the transmitter stamped on it. `rec:asOf` ranks observations of
one state, a later look at a source being better evidence of its current state, and a person's later session being
their later edit; it is a device clock for a live pull or an entry, which is acceptable because a pull from one device
has no other clock and an entry's order is the person's own. The source's version id never ranks: it is opaque, it
resets, and it is a string. The device's write time ranks nothing on its own: it was a clock that happens to be right,
which is a bias, not a reason, so the last step is the least IRI, there only so two devices agree, and the note says it
is arbitrary. A pod is a mirror of sources it does not author, so git's open fork is wrong by default: the person
cannot judge every pair, and the source's change time can. Where it cannot, a person outranks the clocks with a
Before, which states a fact the clocks were only inferring and composes across three states where a verdict on one
would not. Because current is derived and never stored, the pod cannot record that it guessed, so the review page is
the confession. Heads rather than a line let two offline devices both import a correction and merge by union; a
maximum over the set needs no walk of the line.

## Alternatives that lost

- **Current is the last arrival, and A3.** The strongest case: simplest to compute and today's rule. A stale export
  re-imported won, and a counter reset's correction was dropped.
- **git's open fork, merged by a person.** The strongest case: no clock is trusted and nothing is decided silently. The
  person did not author the sources and cannot judge every pair; the source's change time can, and where it cannot,
  the review page says so and a Before is the person's merge.
- **The source's version id as the rank.** The strongest case: it is the server's own ordering. It is opaque by
  definition, resets on a restore, and is a string.
- **A device clock as a tiebreak, before the arbitrary step.** The strongest case: it is usually right. Usually right
  with no reason is a hidden guess; the arbitrary step is a visible one, and the review page shows it.
- **Erroneous as the override.** The strongest case: it exists. It means wrong and hides the revision from every view;
  a stale state is not wrong, and an ordering composes where a mark on one revision does not.
- **A "current" verdict on one revision.** The strongest case: one tap. Two people saying "current" need a rule; a
  Before composes and states a fact.
- **Currency as a filed machine judgment.** The strongest case: honest provenance of every pick. A file per record
  per import, for what is mostly not a judgment at all: the source's change time is what the source said.

## Still open

- Order of the steps: whether the latest source time is taken before or after Before and Erroneous remove revisions
  (the ladder above removes first); what a Before cycle from two devices yields, and what an empty candidate set
  yields.
- Whether Before orders versions or revisions: a revision may repeat an earlier version, so the two differ.
- The stamp-less copy: revisions with no source time are candidates beside those at the latest time, so a stale copy
  with its `meta` stripped can become current on `rec:asOf` alone. Lean: an arrival with no source time whose version
  the record already holds writes nothing; a stale copy of a state the pod never saw is still open.
- A server rollback keeping old timestamps: its content and source version are already held, so nothing is written
  and nothing is shown; a rollback that re-stamps follows the server on its own. Whether the silent case raises a
  finding, so the review page can list it. Lean: yes.
- An import that kept nothing writes nothing (A11). Stands if a rollback's finding counts as keeping something.
- The latest member of a Same group is chosen by `rec:asOf`, so a re-publisher's stale copy pulled later shows over
  the origin's correction. Lean: the group's rule follows this ladder, and a Before may order revisions of any two
  records a Same joins.
- The term: `rec:asOf` beside the existing `rec:answeredAsOf` on documents, and whether one name serves both.

## What would change our mind

Sources stamping no change time often enough that currency falls to device clocks would reopen the open-fork
alternative. A source that re-stamps change times on every read would make the change time no better than the
arrival. A person filing Befores on most records would say the ladder picks wrong often enough to replace.
