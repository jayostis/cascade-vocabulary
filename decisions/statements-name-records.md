# What an app's statement about an entry names

Status: accepted, 2026-11-16, the maintainer's ruling on the-cascade-protocol/planning#30, for
the-cascade-protocol/cascadeprotocol.org#64. Amends nothing: the view entry's name is `naming.md`'s row "view entry"
(N13) and is unchanged. Depends on `naming.md` (rows "record from a server", "record from C-CDA", "version", "view
entry") and `judgments.md`.

## Question

An app keeps things a person says about something a view shows: "still taking it, as of 12 November" about a
medicine, a note on a dose, a link from a lab result to a concern, a phone's cached list. Each needs a reference that
still finds the thing next month. A view entry is named from its least member (N13), so a source that joins with a
record whose IRI sorts lower renames the entry, and a statement stored against the entry's IRI then names nothing.
The pod has no server of record to mint an id once and remember it: every view is rebuilt from the originals, in any
order, by any writer, and a rebuild must give the same pod.

So: what does a statement about an entry name, how does a reader find the entry again, what does it show when what
was named is gone, and does it name the record, the version it saw, or both?

## What others do

Each quotation was read at its source on 2026-11-16 (verified).

- **FHIR R4 resource identity.** "Once assigned by the server, the id is never changed." But "when a resource is
  copied from one server to another server, the copy might or might not keep the same logical id", and "all copies
  of the resource refer to the same underlying concept". A reference names one resource on one server; the same
  thing on two servers has two ids, and FHIR mints nothing above them.
- **FHIR R4 `Linkage`.** "Identifies two or more records (resource instances) that refer to the same real-world
  'occurrence'", with `item.type` saying which item is the "source of truth" (if any) and which "are no longer
  considered to be current representations" (`source | alternate | historical`). The records keep their own ids; the
  linkage is a further resource beside them.
- **FHIR R4 `Patient.link`.** `replaced-by`: "The patient resource containing this link must no longer be used. The
  link points forward to another patient resource". A merge keeps the old id resolvable by a forward pointer that a
  server stores and maintains.
- **Wikidata merges.** After a merge "the obsolete item can then be redirected"; "Never reuse merged items for other
  things"; the item to keep is chosen by hand, "when in doubt ... the item with the lowest Q####". Undoing a wrong
  merge restores both items' histories by hand, in order, and a split is a separate manual procedure. An id minted
  once survives a merge only through a stored redirect, and a split has no rule.
- **PROV-O and the pod's judgments.** A judgment names records with `prov:hadMember` and the versions it was made from
  with `prov:wasDerivedFrom` (`judgments.md`); the `a-member-changed-since-the-judgment` fixture shows a reader telling
  a judgment made before a member changed from one made after.

Sources: FHIR R4 Resource (https://hl7.org/fhir/R4/resource.html), Linkage (https://hl7.org/fhir/R4/linkage.html),
link-type (https://hl7.org/fhir/R4/valueset-link-type.html), Wikidata Help:Merge
(https://www.wikidata.org/wiki/Help:Merge), PROV-O (https://www.w3.org/TR/prov-o/); the ask and its measurements,
the-cascade-protocol/planning#30.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| what a statement names | FHIR references a resource by its id; `Linkage` keeps each record's own id | a statement an app or a person makes about an entry names every record the entry held when it was made, by the record's IRI, never the entry's (`queries/questions/record/Which entry shows it.rq`) | borrowed from FHIR and `Linkage`: point at the records, whose ids hold still |
| versions | `prov:wasDerivedFrom`, as a judgment names the versions it was made from | a statement about what a record said (a dose, a status, a value) also names the versions it saw; one about the thing alone (a concern linked to a result) need not | borrowed from PROV-O and `judgments.md` |
| finding the entry | `Patient.link` `replaced-by`, Wikidata redirects: a stored forward pointer | read when shown: the entry of each named record, through `cascade:inEntry`, which "Which entry shows it" returns; nothing is stored (`queries/derivations/entries.rq`) | diverged: no pointer to maintain, because a rebuild gives the same entries |
| entry IRI | Wikidata's Q-id, minted once | unchanged: derived from the least member in each build (N13); it is not a stable reference, and an app never stores one | ours, `naming.md` row "view entry" |
| same thing across builds | Wikidata: a merge keeps one item, chosen by hand | two entries, in two builds, that share a record are the same thing; entries that share none are not | ours: a record is in at most one entry of its kind's view in a build |
| records all gone | none | a statement none of whose records the pod holds is kept, not dropped, and shown apart; "Which entry shows it" and "Why it is in no view" both give no row for such a record, and no question of its own is added (`queries/questions/record/Why it is in no view.rq`) | ours |
| records in two entries | Wikidata: a split is by hand | a statement whose records are now in two entries is shown with each of them | ours |

## Why

**Why a statement names records.** (rows "what a statement names", "finding the entry", "entry IRI") Any id
computed from an entry's members must change when its members do, and a source joining is a change of members. An id
minted once and stored would not change, but it is state no original holds, so a rebuild from the originals could
not give it back; `naming.md` (row "act") mints nothing at random but an act, the subject and a person's judgment,
and derives every other name from what the pod holds, so that two runtimes and two rebuilds agree. A record's IRI is already derived from its source's own
id (rows "record from a server" and "record from C-CDA"), or from the document that brought it (row "record from a
document"), so it holds still across rebuilds in any order and does not move when another source joins. A new
download of a FHIR document brings new records, which the matcher joins to the old; the old ones stay, since nothing
in a pod is deleted, and a statement naming them still finds the entry. The two-step MMR case of planning#30 shows it: the portal's record is in the entry
named from the portal's record before the download joins, and in the entry renamed from the download's record after,
which holds both (`TestGivenAnImmunizationASecondSourceJoins` in `tests/test_query_fixtures.py`). Judgments already
work this way: they name records, and so carry over a rebuild.

**Why every record the entry held.** (row "what a statement names") A statement that named one record would be lost
when that record's original is removed, though the thing still stands in the pod through its other sources, which is
the first failure planning#30 lists. Naming every member of the entry when the statement is made loses it only when
every one of them is gone.

**Why the versions too, when content matters.** (row "versions") Membership is on a record: `cascade:inEntry` and
`cascade:entryMember` join records, never versions. A version is named by its content alone (`naming.md` row
"version"), so one version can be two records', and it stops being current when its record is revised: it cannot find
an entry. But a record says nothing about which of its states the person saw, and "still taking 10 mg" means little
once the record says 20 mg. Naming both lets a reader find the entry by the records and tell, by the versions, that
what was confirmed has changed since, as a judgment's reader does. A statement about the thing and not its content
gains nothing from versions, so it is not asked to carry them.

**Why two entries that share a record are one thing.** (row "same thing across builds") A record is in at most one
entry of its kind's view in a build, so the record that an entry from last month and one from today both hold is a
single fact the two builds show under two names. A cache keyed by records can therefore tell "the same medicine,
renamed" (a record in common) from "one stopped and another started" (none in common), which an entry's IRI cannot.

**Why the empty lookup suffices.** (row "records all gone") Every record the pod holds is either in an entry or left
out of every view with a recorded reason, a check run over every fixture (`TestWhatIsTrueOfAnyPod`); so a record for
which "Which entry shows it" and "Why it is in no view" both give no row is one the pod no longer holds, and a record
hidden from every view is told apart by its reason. A question "statements whose records are gone" could not be asked
of the pod, because the statements an app keeps are in the app, and the rows it would return are those two
questions' empty answers: each question is asked once. The statement is kept because the person said it and the
original may come back; it is shown apart from the entries, with what the app saved of it, so the person can attach it
to a current entry by making it again.

**Why a statement in two entries is shown with each.** (row "records in two entries") A Different judgment or a
stricter matcher can split an entry. The statement was about all the records it names, and the pod does not say which
of the parts it meant, so it is shown with each until the person says otherwise; nothing is lost, which a single
stored entry id would have done.

## Alternatives that lost

- **An entry id minted once and carried forward.** The strongest case: one key per thing, which is what an app wants
  to store, and what planning#30 offered first. It lost because the id is state no original holds, so a rebuild
  from originals, in another order or by another runtime, gives it back only if it is itself stored and replayed; and
  it needs a rule for which side keeps the id when entries merge or split, which Wikidata leaves to a person and FHIR
  to a stored forward pointer.
- **An entry named from a member that does not move,** the first to arrive. The strongest case: a joining record
  would not rename it. It lost because arrival order is not the same across rebuilds, and the naming must not depend
  on order (planning#30 measured today's names the same in reverse order); and any name drawn from members moves when
  that member's original is removed.
- **The entry's IRI stored beside the records, as a fast path.** The strongest case: no lookup on the common read. It
  lost because two keys disagree as soon as a source joins, and the one that goes stale is the one the app reads
  first.

## Still open

- Where a statement a person makes lives: in the app, as today, or in the pod as a record or a judgment
  (jayostis/cascade-vocabulary#393, planning's notes, section 3.7). Lean: either way it names records as this note
  says, so nothing here changes.
- A summary exported to another app: whether the receiver can match its records by IRI. Lean: any runtime given the
  same originals names the same records alike (`naming.md`), so yes for records from the same originals; records from
  another download join by the matcher, not by name.

## What would change our mind

- Originals removed as a matter of course, as a pod that kept only the latest download of each source would: a
  statement would then lose its records at every pull, and would need the matcher's join to the new ones as well as
  the names.
- Entries that people split often: a statement shown with each part would then need a rule for which part it meant.
