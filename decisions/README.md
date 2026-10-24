# Decision notes

A note is the one place that records why a term, a rule or a shape is as it is, so that the next person does not
re-decide it, and so that a divergence from a standard is deliberate and can be found. There is one note per question,
not one per file: a question that touches the ontology, a query and a feature file is one note.

## The sections

A note has these, in this order, under these headings.

- **Status:** a line, not a heading: draft or accepted, the date, what it replaces or amends, and which other notes it
  depends on.
- **Question:** the problem, with the constraints of a pod that make it hard: no server of record, more than one
  writer, views the person may share.
- **What others do:** the prior art, each named, with what it actually says, quoted where the words matter. The health
  standards come first: FHIR, C-CDA and CDA, openEHR, and whichever others bear, SPHN, OMOP, DICOM, HL7 v2. Then the web
  standards the vocabulary builds on: PROV-O, SKOS, RDF and Turtle conventions, the RFCs. "Nothing" is an answer. It
  ends with a Sources list, each with its URL, and the research the note rests on.
- **Choice:** a table, `thing | prior art | what we do | borrowed or diverged`, one row per thing decided. The last cell
  says which, and where it diverged, why in a few words.
- **Why:** the reasons, one paragraph per idea, with numbers where there are numbers.
- **Alternatives that lost:** each one stated fairly, "The strongest case:" first, then why it lost.
- **Still open:** every question the note does not rule, with a lean where there is one. A lean is not a ruling in
  disguise.
- **What would change our mind:** the observations that would reopen the choice.

A note that states tests other notes apply has a **Rubric** after its Question, as `naming.md` does.

## The bar

Adopt the standard wherever it fits, and say which. Where the vocabulary diverges, the table says so, Why says why, and
the reason is research, not opinion. A note that diverges from a standard with no reason in Why is not done.

Research is cited with its numbers and lives where a reader can reach it: an issue comment, as research 1 to 5 on
[#130](https://github.com/jayostis/cascade-vocabulary/issues/130); or an evidence issue that keeps the counts and the
scripts, as [#201](https://github.com/jayostis/cascade-vocabulary/issues/201). A folder on one machine is not
reachable. A claim that rests on measurement says whether it was verified, inferred or unverified: "ids survive
(inferred, not observed)".

## The review

A note gets a critical read by someone who did not write it before it is accepted. The read's findings, and what became
of each, are recorded on the pull request. Rulings are the owner's: a note presents an open question as open, and a
reviewer's lean as a lean.

## A note and the rest of the repository

A ruling in a note is applied in the ontology, the queries, the feature files and the kits, in the same pull request or
in one the note names. A note never contradicts them silently. A change to a term, a shape or a query says why in its
commit message, never in the file, and the note is where the longer why lives.

A note that replaces an older rule names it, as `naming.md` names N1, N2, N6, N7, A2, M5 and M9, and `currency.md` names A3 to
A5, M1 and M3. Notes cite one another by file name.

A note and a feature rule point at each other. A Choice row states the rule in one sentence and names the rule in
`runtime/` that applies it (`N3`, `M17`); that rule's first line names the note and the row that ruled it. Neither
leans on the other to be read: the note says what and why, the feature says exactly how, with the examples. An
example belongs in the feature, never in the note; a reason belongs in the note, never in the feature. A ruling with
no feature rule yet names the issue that will write it.

## The notes

Written to this standard, from the review on #130; the five genomics notes after them, written before it settled, were
brought to it on 2026-10-22 under #202:

- [`naming.md`](naming.md): how everything in a pod is named, so that two runtimes give alike a name nobody can forge
  and a shared view says nothing it should not.
- [`currency.md`](currency.md): which revision of a record is current, when its states arrive by several paths, by
  several writers, in any order.
- [`republishing-sources.md`](republishing-sources.md): how a moved, switched or re-issued source's records join the
  ones the pod holds, with one judgment where one will do.
- [`judgments.md`](judgments.md): what a judgment is, who makes one, and what it borrows from the vocabularies for
  beliefs about things.
- [`variant-record.md`](variant-record.md): what a pod holds when a report names a genetic variant.
- [`variant-identity.md`](variant-identity.md): when two variant records are one variant, and which codes join them.
- [`variant-interpretation.md`](variant-interpretation.md): where a report's classification of a variant lives, and
  its shape.
- [`variant-classifications-table.md`](variant-classifications-table.md): how an app holds what ClinVar says of a
  variant today, at a size a browser keeps.
- [`code-iris.md`](code-iris.md): the IRI of every code, by code system, deferring to the owner or a community scheme
  where one passes, and how a literal holding reserved characters joins as an IRI.
- [`performance.md`](performance.md): what a ten-year pod costs as it grows, and which rulings keep every cost
  tracking what changed rather than the square of the pod.
- [`one-meaning-per-term.md`](one-meaning-per-term.md): which list a clinical status is from, and the clinical terms
  renamed so that none means something other than the FHIR element it is filled from.
