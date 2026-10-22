# Which revision of a record is current

Status: draft, 2026-10-21, from the review on #130. Replaces A3, A4's "the one the record is at", A5's "after the
record's last one", the single line of `prov:wasRevisionOf`, `derivations/current-revisions.rq`, and M1's and M3's
reliance on that line; adds `rec:asOf`, a Before verdict and a review question. Names are `naming.md`, whose rubric
this note applies: the source's change time is the definition (test 1), a Before is a judgment past it (test 2), and
the review page is test 4.

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
  source's own change time, and the act's start. For an entry it is the session's start. The first two rungs are the
  exporter's clock, the third the source's, and the fourth the device's: an unstamped record from a live pull, and
  every entry, carry the device's clock as their observation time.
- **The source's own version** (`meta.versionId`, `meta.lastUpdated`, or a C-CDA document's `effectiveTime`) sits in a
  node nested in the revision, hashed with it, never on the revision itself.
- **A revision names the record's heads it saw** as `prov:wasRevisionOf`, one or several; a sync is a union of files.
- **What an arrival writes.** A first arrival writes the record, its version and a revision. An arrival whose version
  is the current revision's writes nothing. An arrival whose (version, source version, source time) a revision already
  holds writes nothing, whether or not it would become current. Otherwise a revision, with its heads. The held
  state is skipped unconditionally because the only time it would become current is when a judgment removed the
  revision that holds it, and writing it again would undo that judgment; a copy by another path that re-arrives with
  no stamp, or with the stamp it had, is held already, and an arrival with a new stamp is new evidence and is written.
- **Current is derived, never stored.** A Before orders one pair, not the set, so it removes rather than sorts, and
  the pick is a maximum over what remains:
  1. Remove every revision a counting Erroneous names.
  2. Remove every revision a counting Before places before another revision still present. Befores that form a cycle
     (two devices, "X before Y" and "Y before X") remove nothing and the pair is listed for review.
  3. Of what remains, keep those at the latest source change time, together with those carrying none.
  4. Of those, the greatest `rec:asOf`.
  5. Then the least IRI, which is arbitrary and said so.

  A record with nothing left after step 1 has no current state and appears in no view, which is what its Erroneous
  judgments said; it remains in the pod with its history. Example: A is stamped 1 January by the server, B 1 February,
  C is Apple's copy with no stamp. The clocks pick B. The person files "B before A"; step 2 removes B, step 3 keeps A
  and C, step 4 picks whichever the pod observed later. The ranked order is "latest source time, then latest
  observation": a Before removes before the clocks rank, never after, or the clocks would re-admit what the person
  ruled out.
- **A view materialises the pick.** Current changes only when an act writes, so a view rebuilt with the act holds each
  entry's current revision, and the act's snapshot says whether a view is stale; a read is a lookup, and two devices at
  one snapshot rebuild one view.
- **An entry on a Same group shows every member.** Each member's current state is picked by its own ladder, and the
  entry is the union of their fields, each field saying which member it came from; where members disagree on a field,
  every value shows, the lead's first. The lead is decided three ways, and the person picks which:
  1. Say nothing: the lead is the member ranking first by this ladder over the members' current states.
  2. Say which leads: a Before across two members' current revisions, "show this one first".
  3. Say what it is: the person enters the fact as their own record, a Same joins it to the group, and a person's own
     record leads any group it is in, by rule, since it is the one statement the person authored.
  No merged record is stored; the entry is computed from the members. "Latest observed member" is gone.
- **Before** is a person's judgment, verdict Before, two revisions of one record in order, never two versions; machines
  never make one; a Before outranks every clock, as Different outranks Same. Revisions, because a state recurs: a
  medication stopped and restarted is the running version twice, and a Before over versions filed while the drug was
  stopped would hide the real restart for good, with nothing on the review page because the clocks never got to decide
  it; over revisions the restart is a new revision the Before does not name, so it shows, and the cost is a refile
  when a fresh stamp arrives, which is new evidence. Also because a version is hashed from content alone and two
  records can share one, so a Before over versions would need a record scope or leak; and because the finding below
  names an act and a record, which picks out exactly one revision, so the derived Befores are recomputable from the
  finding and the file set after a sync.
- **A source that goes backwards raises one finding.** An import whose source reports a state older than that same
  source's own earlier report writes no revision and files one finding on the act, naming the earlier act and each
  record that went back. A copy by another path (Apple's copy of a hospital record, a document exported last year)
  that is older than a direct pull files nothing: it is a stale copy, not a contradiction. The current pick is
  unchanged either way. One finding per source per earlier act it contradicts: a repeat pull of the rolled-back state
  files nothing new while that finding stands. A finding is something kept, so A11 stands: an import that kept nothing
  writes nothing.
- **A Before over a finding** is one judgment: its member is the finding, and the derivation places each named record's
  rolled-back revision before the ones it superseded, as a Same over two servers derives a join per record. Retracting
  it lifts every derived Before at once.
- **The review page** lists every record whose current state the source's change time did not decide, with the state
  shown, the state not shown, and the reason ("observed later", or "no basis"); the fix is one Before. It lists each
  rollback finding as one line, "this source reports N records at states older than it reported on that date",
  expanding to the records, with three answers: a Before over the finding; an acknowledgement, so the later states stay
  and the finding clears; or a Before per record from the expanded list.
- **A wrong device clock is caught after the fact and discounted by one judgment.** Stamped records never use the
  device's clock, so a skew touches only unstamped pulls and entries, at step 4. Two checks run on each act and file
  a finding, "this device's clock was at least N days behind": a revision whose `rec:asOf` precedes a head it names,
  and a pull returning a record the source stamped after the pull's own time. The remedy is a person's judgment whose
  member is the act, saying its observation times are known wrong, usually by confirming the finding; the derivation
  treats every revision that act generated as carrying no `rec:asOf`, so its picks fall to step 5 and the review
  page. Nothing is rewritten, and the judgment is retractable. It is not Erroneous over the act: the content is
  sound, only its clocks are not. The verdict's name is open in `judgments.md`.
- **An act's findings are known before it is committed.** An act is atomic, so an app may run an import to a staging
  area, show the person what it found, and let them commit it, commit it with a judgment filed in the same step, or
  decline it. A declined act never existed: no name, no snapshot, nothing for another device to receive. The next
  pull will find the same thing and ask again; a declined act leaves no finding because no act generated one. The
  vocabulary permits staging and does not require it.
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
the confession. A rollback is noticed by the same test that keeps a stale copy quiet: a source contradicting its own
earlier report is one fact, so it is one finding and, if the person agrees with the source, one Before with the
per-record orderings derived, where a copy that is merely behind is what the ladder already expects. The pod keeps
showing the later state because a hospital that restores a backup has usually lost data it will re-enter. Heads rather than a line let two offline devices both import a correction and merge by union; a
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

## Still open

- A stamp-less copy of a state the pod never saw is written with no source time, stands beside the latest-stamped
  revision at step 3, and can win at step 4 on `rec:asOf`; the review page lists it as "observed later". Whether that
  listing is enough.
- A rollback that re-stamps its change times follows the server on its own and raises nothing; whether that is
  acceptable, since the person is not told.
- A source that no longer returns a record at all, as against returning an older state: nothing contradicts the
  record the pod holds, so no finding fires and the record stays current. Source deletion is a question of its own.
- The acknowledgement that clears a finding has no verdict today; it is open in `judgments.md`.
- The term: `rec:asOf` beside the existing `rec:answeredAsOf` on documents, and whether one name serves both.

## What would change our mind

Sources stamping no change time often enough that currency falls to device clocks would reopen the open-fork
alternative. A source that re-stamps change times on every read would make the change time no better than the
arrival. A person filing Befores on most records would say the ladder picks wrong often enough to replace.
