# Which revision of a record is current

Status: draft, 2026-10-21, from the review on #130. Replaces A3, A4's "the one the record is at", A5's "after the
record's last one", the single line of `prov:wasRevisionOf`, `derivations/current-revisions.rq`, and M1's and M3's
reliance on that line; adds `rec:asOf`, a Before verdict and a review question. Names are `naming.md`, whose rubric
this note applies: the source's change time is the definition (test 1), a Before is a judgment past it (test 2), and
the review page is test 4. What a judgment is, and the verdicts this note leaves open, are `judgments.md`.

## Question

A record's state arrives by several paths (a pull, Apple's copy, a C-CDA, a person's edit), by several writers, in
any order. Which of its revisions does the pod show, so that a stale copy never un-corrects or un-retracts a record,
two writers agree without talking, and a person can fix what the pod got wrong?

## What others do

- **FHIR** gives each version `meta.lastUpdated`, "when the resource last changed", and an opaque `meta.versionId`;
  a client that holds copies from several paths is on its own.
- **CDA** gives a document an `effectiveTime`, when it was created, and a `setId` and `versionNumber` for the
  successive documents that replace one another.
- **openEHR** keeps branches in a version tree under one versioned object; which branch is current is the system's.
- **git** keeps every head and leaves a fork to a person, who writes the merge commit; a ref says which is current.
- **CRDTs** make a replicated set converge by union, with every answer a function of the set.
- **Provenance (PROV)** records when an entity was generated and what it was derived from, and leaves "current" to the
  reader.

Sources: FHIR R4 `Meta` (https://hl7.org/fhir/R4/resource.html#Meta); CDA `ClinicalDocument` `effectiveTime`, `setId`
and `versionNumber` (https://hl7.org/cda/stds/core/StructureDefinition-ClinicalDocument.html); openEHR versioning
(https://specifications.openehr.org/releases/RM/latest/common.html#_change_control_package); git branching
(https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging); Shapiro et al., CRDTs
(https://hal.inria.fr/inria-00555588); PROV-O (https://www.w3.org/TR/prov-o/); the review on #130, where Before over
versions was arbitrated (https://github.com/jayostis/cascade-vocabulary/issues/130).

## Choice

Each row is one thing decided; the ladder and the lead the rows refer to follow the table.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| two clocks | FHIR `meta.lastUpdated`; CDA `effectiveTime`; PROV `prov:generatedAtTime` | a revision carries `prov:generatedAtTime`, when the pod wrote it, and `rec:asOf`, written `cascade:observedAsOf`, when the source was observed saying this state: the first of the document's `rec:answeredAsOf`, the document's `pav:retrievedOn`, the source's own change time, and the act's start; for an entry it is the session's start. The first two rungs are the exporter's clock, the third the source's, and the fourth the writer's: an unstamped record from a live pull, and every entry, carry the writer's clock as their observation time (`runtime/currency.feature`, C1) | borrowed from PROV for when the pod wrote it; `rec:asOf` and its rungs are ours |
| source's own version | FHIR `meta.versionId`, `meta.lastUpdated`; CDA `effectiveTime`, `versionNumber` | `meta.versionId`, `meta.lastUpdated`, or a C-CDA document's `effectiveTime` sits in a node nested in the revision, hashed with it, never on the revision itself | borrowed as the source states it; diverges in never ranking, since a version id is opaque and resets |
| heads | git parents; openEHR version tree | a revision names the record's heads it saw as `prov:wasRevisionOf`, one or several; a sync is a union of files (`runtime/arrivals.feature`, A5; `runtime/sync.feature`, S6) | borrowed from git |
| what an arrival writes | | a first arrival writes the record, its version and a revision. An arrival whose version is the current revision's writes nothing. An arrival whose (version, source version, source time) a revision already holds writes nothing, whether or not it would become current; so does an arrival with no source time whose version the record already holds, whatever stamp the held revision carries. Otherwise a revision, with its heads (`runtime/arrivals.feature`, A3 to A5) | ours |
| current | CRDTs; git ref; openEHR | derived, never stored, by the ladder below: a Before orders one pair, not the set, so it removes rather than sorts, and the pick is a maximum over what remains (`runtime/currency.feature`, C2) | borrowed in spirit from CRDTs, every answer a function of the set; the ladder is ours |
| view | | a view materialises the pick: current changes only when an act writes, and only for the records it wrote revisions for plus those its judgments reach by derivation, so an act rebuilds the entries of those records alone, and the rebuild equals the full one; a migration, a change to the trusted makers and a change of rule list version rebuild everything; the act's snapshot says whether a view is stale; a read is a lookup, and two writers at one snapshot rebuild one view; the incremental rebuild is the second part of [#220](https://github.com/jayostis/cascade-vocabulary/issues/220) | ours |
| entry on a Same group | | shows every member: each member's current state is picked by its own ladder, and the entry is the union of their fields, each field saying which member it came from; where members disagree on a field, every value shows, the lead's first, the lead decided by the person's pick of the three ways below. No merged record is stored; the entry is computed from the members. "Latest observed member" is gone (`runtime/currency.feature`, C6) | ours |
| Before | git merge commit | a person's judgment, verdict Before, two revisions in order, of one record or of two records a Same joins (the lead below), never two versions; machines never make one; a Before outranks every clock, as Different outranks Same; the verdict is `cascade:Before`, the earlier revision its `cascade:earlierMember` (`runtime/currency.feature`, C3 and C4) | ours; it stands where git has the person's merge commit |
| a source that goes backwards | | raises a finding: an import whose source reports a state older than that same source's own earlier report files one finding on the act, naming every earlier act it contradicts and each record that went back; it writes no revision where the older state is held, and writes one where it never was, which the ladder then ranks below the later state. A copy by another path (Apple's copy of a hospital record, a document exported last year) that is older than a direct pull files nothing: it is a stale copy, not a contradiction. The current pick is unchanged either way. One finding per import that goes back: a repeat pull of the rolled-back state files nothing new while that finding stands, and an acknowledged finding still stands. A finding is something kept, so A11 stands: an import that kept nothing writes nothing (`runtime/arrivals.feature`, A10 and A18) | ours |
| Before over a finding | | one judgment: its member is the finding, and the derivation places, for each named record, the revision the earlier act wrote before the revision holding the older state the source now reports, so the rollback wins, as a Same over two servers derives a join per record. Retracting it lifts every derived Before at once | ours |
| wrong writer clock | | caught after the fact and discounted by one judgment. Stamped records never use the writer's clock, so a skew touches only unstamped pulls and entries, at step 4. Two checks run on each act and file a finding, "this writer's clock was at least N days behind", and no second while one an act in the first-parent ancestry of the new act filed stands unanswered, neither acknowledged nor answered by a discount of the act that filed it, so a writer whose clock stays wrong files once more after each answer: a revision whose `rec:asOf` precedes a head it names, and a pull returning a record the source stamped after the pull's own time, which cannot tell a writer's slow clock from a source's fast one. The remedy is a person's judgment whose member is the act, saying its observation times are known wrong, usually by confirming the finding; the derivation treats every revision that act generated as carrying no `rec:asOf`, so its picks fall to step 5 and the review page. Nothing is rewritten, and the judgment is retractable. It is not Erroneous over the act: the content is sound, only its clocks are not. The verdict is `cascade:ClockDiscounted`, with no offset (`runtime/arrivals.feature`, A19; `runtime/currency.feature`, C7) | ours |
| findings before commit | | an act's findings are known before it is committed. An act is atomic, so an app may run an import to a staging area, show the person what it found, and let them commit it, commit it with a judgment filed in the same step, or decline it. A declined act never existed: no name, no snapshot, nothing for another writer to receive. The next pull will find the same thing and ask again; a declined act leaves no finding because no act generated one. The vocabulary permits staging and does not require it | ours |
| review page | | lists every record whose current state the source's change time did not decide, but a pick between two pulls of one source where one's snapshot is an ancestor of the other's, which ancestry orders; only picks ancestry does not order (two writers, two paths) are listed, each with the state shown, the state not shown, and the reason ("observed later", or "no basis"); the fix is one Before (`runtime/currency.feature`, C4 and C5). It lists each rollback finding as one line, "this source reports N records at states older than it reported on that date", expanding to the records, with three answers: a Before over the finding; an acknowledgement, so the later states stay and the finding clears; or a Before per record from the expanded list, N counting only the records no Before answers yet. It lists each clock finding with each revision it names, until the person acknowledges it or discounts the act's clock (`runtime/currency.feature`, C7) | ours |
| Erroneous | | for a state that is wrong, and hides it from every view; a stale state is not wrong and stays; an Erroneous over a revision removes it at the ladder's first step (`runtime/currency.feature`, C2) | ours |

**The ladder.** Current is the maximum over what remains:

1. Remove every revision a counting Erroneous names.
2. Remove every revision a counting Before places before another revision still present. Befores that form a cycle
   (two writers, "X before Y" and "Y before X") remove nothing and the pair is listed for review.
3. Of what remains, keep those at the latest source change time, together with those carrying none.
4. Of those, the greatest `rec:asOf`; between two live pulls of one source (a document retrieved on a date and answering as of no
   other instant, through one transmitter or none) where one's snapshot is an ancestor of the other's, the later in that
   ancestry.
5. Then the least IRI, which is arbitrary and said so.

A record with nothing left after step 1 has no current state and appears in no view, which is what its Erroneous
judgments said; it remains in the pod with its history. Example: A is stamped 1 January by the server, B 1 February,
C is Apple's copy of a third state with no stamp, observed before B arrived. The clocks pick B. The person files "B
before A"; step 2 removes B, step 3 keeps A and C, step 4 picks whichever the pod observed later. The ranked order is
"latest source time, then latest observation": a Before removes before the clocks rank, never after, or the clocks
would re-admit what the person ruled out.

**The lead.** The lead of an entry on a Same group is decided three ways, and the person picks which:

1. Say nothing: the lead is the member ranking first by the ladder above over the members' current states.
2. Say which leads: a Before across two members' current revisions, "show this one first".
3. Say what it is: the person enters the fact as their own record, a Same joins it to the group, and a person's own
   record leads any group it is in, by rule, since it is the one statement the person authored.

## Why

**Why the source's state decides, not the arrival.** The quantity that must decide is the source's state, not the
messenger's arrival: "latest to arrive" let a transmitter's late copy of an old state overrule a correction, and A3 let
a string the record had seen suppress new content, dropping a counter reset's correction. The source's change time
ranks states of the source: a copy of an older state never beats a newer one, whatever clock the transmitter stamped
on it.

**Why `rec:asOf` ranks observations.** `rec:asOf` ranks observations of one state, a later look at a source being
better evidence of its current state, and a person's later session being their later edit; it is a writer's clock for a
live pull or an entry, which is acceptable because a live pull has no other clock and an entry's order is
the person's own. Between two pulls of one source where one's snapshot is an ancestor of the other's, ancestry orders the two
acts whatever its clock says, so that pick is not a guess and is not listed; only picks ancestry does not order, two
writers or two paths, go to the review page. Listed, a source that sends no change time and changes a tenth of 8k
records a year gives about 800 lines a year and about 8,000 by year ten, each kept until someone files a Before
(assumed, [#206](https://github.com/jayostis/cascade-vocabulary/issues/206)).

**Why neither the version id nor the write time ranks.** The source's version id never ranks: it is opaque, it
resets, and it is a string. The writer's write time ranks nothing on its own: it was a clock that happens to be right,
which is a bias, not a reason, so the last step is the least IRI, there only so two writers agree, and the note says it
is arbitrary.

**Why a held state writes nothing.** The held state is skipped unconditionally because the only time it would become
current is when a judgment removed the revision that holds it, and writing it again would undo that judgment; an
unstamped copy of a held state is skipped because it is a copy by another path of a state the pod has seen, and
written it could win at step 4 on its observation time alone; an arrival with a new stamp is new evidence and is
written.

**Why a person's Before, not git's open fork.** A pod is a mirror of sources it does not author, so git's open fork is
wrong by default: the person cannot judge every pair, and the source's change time can. Where it cannot, a person
outranks the clocks with a Before, which states a fact the clocks were only inferring and composes across three states
where a verdict on one would not.

**Why a Before orders revisions, not versions.** Revisions, because a state recurs: a medication stopped and
restarted is the running version twice, and a Before over versions filed while the drug was stopped would hide the
real restart for good, with nothing on the review page because the clocks never got to decide it; over revisions the
restart is a new revision the Before does not name, so it shows, and the cost is a refile when a fresh stamp arrives,
which is new evidence. Also because a version is hashed from content alone and two records can share one, so a Before
over versions would need a record scope or leak; and because a rollback finding names an act and a record, which
picks out exactly one revision, so the derived Befores are recomputable from the finding and the file set after a
sync.

**Why the review page.** Because current is derived and never stored, the pod cannot record that it guessed, so the
review page is the confession.

**Why a rollback is one finding, and the later state stays.** A rollback is noticed by the same test that keeps a
stale copy quiet: a source contradicting its own earlier report is one fact, so it is one finding and, if the person
agrees with the source, one Before with the per-record orderings derived, where a copy that is merely behind is what
the ladder already expects. The pod keeps showing the later state because a hospital that restores a backup has
usually lost data it will re-enter. One finding per import that goes back, naming every earlier act, because a
finding per earlier act made a 30-day restore about 30 findings; an acknowledged finding still stands, or a daily
pull of the rolled-back state would file one again every day; and a skewed writer has one clock finding while one
stands, where one per act is up to 365 a year (computed, #206).

**Why a view rebuilds only what an act reached.** The ladder is per record and an entry is a closure over its
members' judgments, so an act changes current only for the records it wrote revisions for and those its judgments
reach by derivation, and rebuilding those gives what the full rebuild gives; two writers still agree, since the result
is a function of the set. A full rebuild per act is the ladder over 200k revisions, counting over 32k judgments, the
pairs, the entries and nine views, 10 to 60 s on Node and too much for a browser, 14 to 80 hours over 5,000 acts
(assumed, #206). What changes every record's inputs at once rebuilds everything: a migration, a change to the trusted
makers, a change of rule list version.

**Why heads rather than a line.** Heads rather than a line let two offline writers both import a correction and merge
by union; a maximum over the set needs no walk of the line.

## Alternatives that lost

- **Current is the last arrival, and A3.** The strongest case: simplest to compute and today's rule. A stale export
  re-imported won, and a counter reset's correction was dropped.
- **git's open fork, merged by a person.** The strongest case: no clock is trusted and nothing is decided silently. The
  person did not author the sources and cannot judge every pair; the source's change time can, and where it cannot,
  the review page says so and a Before is the person's merge.
- **The source's version id as the rank.** The strongest case: it is the server's own ordering. It is opaque by
  definition, resets on a restore, and is a string.
- **A writer's clock as a tiebreak, before the arbitrary step.** The strongest case: it is usually right. Usually right
  with no reason is a hidden guess; the arbitrary step is a visible one, and the review page shows it.
- **Erroneous as the override.** The strongest case: it exists. It means wrong and hides the revision from every view;
  a stale state is not wrong, and an ordering composes where a mark on one revision does not.
- **A "current" verdict on one revision.** The strongest case: one tap. Two people saying "current" need a rule; a
  Before composes and states a fact.
- **Currency as a filed machine judgment.** The strongest case: honest provenance of every pick. A file per record
  per import, for what is mostly not a judgment at all: the source's change time is what the source said.
- **Before over versions.** The strongest case: a rollback is a claim about states, and a stale copy of the
  superseded state re-arriving by another path would be covered without a refile. The re-arrival is already held and
  writes nothing, so the case never occurs; and the claim is timeless where states recur, so it hides a genuine
  restart silently. Arbitrated on #130 after the two sides tied.
- **A Same group shows its latest-observed member.** The strongest case: one rule, no judgment, and it was the rule.
  Which member was pulled last is an accident of the person's day, and it hid a field one member had and another
  lacked; showing every member hides nothing, and the lead is the person's to set.
- **Skipping a held state only when it would not become current.** The strongest case: a held state that would win
  is new information. It wins only because a judgment removed the revision holding it, so the write undoes the
  judgment; everything else that wins has a new stamp.
- **A view rebuilt whole with every act.** The strongest case: a view rebuilt with the act holds each entry's current
  revision by construction, with nothing to prove. It is 10 to 60 s on Node per act, 14 to 80 hours over ten years,
  and does not fit in a browser (assumed, #206).
- **Every pick the source's change time did not decide on the review page.** The strongest case: the review page is
  the confession, and every pick no source time made is shown. A source with no change time puts about 8,000 lines on
  it by year ten (assumed, #206), most of them pulls whose snapshots ancestry already orders.
- **A rollback finding per earlier act contradicted, and a clock finding per act.** The strongest case: each finding
  names one contradiction, and each act's own skew is on record. A 30-day restore gives about 30 findings, a skewed
  writer up to 365 a year, and without "an acknowledged finding still stands" the same rolled-back state files again
  every day (computed, #206).

## Still open

- A stamp-less copy of a state the pod never saw is written with no source time, stands beside the latest-stamped
  revision at step 3, and can win at step 4 on `rec:asOf`; the review page lists it as "observed later". Whether that
  listing is enough.
- A rollback that re-stamps its change times follows the server on its own and raises nothing; whether that is
  acceptable, since the person is not told.
- A source that no longer returns a record at all, as against returning an older state: nothing contradicts the
  record the pod holds, so no finding fires and the record stays current. Source deletion is a question of its own.

## What would change our mind

Sources stamping no change time often enough that currency falls to writers' clocks would reopen the open-fork
alternative. A source that re-stamps change times on every read would make the change time no better than the
arrival. A person filing Befores on most records would say the ladder picks wrong often enough to replace.
