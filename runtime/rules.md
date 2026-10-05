# Runtime rules

What a runtime does when it fills a pod: how it names what it writes, which arrivals it writes, how the matcher judges,
and the order it writes in. Each rule names the vectors in [`vectors/manifest.ttl`](vectors/manifest.ttl) that show it,
and the planted cases of [the scenario](https://github.com/jayostis/cascade-vocabulary/issues/4) that exercise it.

## The test format

The vectors are a W3C test manifest, as an adapter's are
([`adapter/fixtures/manifest.md`](https://github.com/jayostis/cascade-bridge-spec/blob/main/adapter/fixtures/manifest.md)).
Relative IRIs resolve against the manifest's own location.

- **An entry** is a `rec:ReplayTest` with `mf:name`, an `rdfs:comment` saying what it shows, an `mf:action` and an
  `mf:result`. The test terms are declared in [`records.ttl`](../ontologies/records/v1-draft/records.ttl).
- **The action** gives `rec:story` (the story's file), `rec:step` (the name of the step to replay to), `rec:lens` (the
  lens's query file) and `qt:query` (a `.rq` file).
- **The result** is a SPARQL 1.1 Query Results JSON file (`.srj`), holding either the expected rows or, for an ASK, the
  expected boolean. Rows are compared as a multiset, with IRIs and literals exact. An entry uses rows where they can be
  written, and an ASK only where rows would be forced.
- **The query runs over the pod as it stood after that step.** Each file is a named graph, named by the pod's address
  plus its path. The lens's derived state is the graph `urn:cascade:derived:<lens>`, and the files built from that
  state, the views, the labels, the type index and `manifest.ttl`, are graphs too. The pod's layout,
  [`pod-layout.ttl`](pod-layout.ttl) read with the pod's address as its base, is the graph `urn:cascade:pod-layout`.
  The default graph is the union of all of these.
- **One more graph, `urn:cascade:steps`,** lists what each step wrote, up to and including the one replayed to:
  `<urn:cascade:step:<name>> prov:generated <file IRI>`. It lists only files that were new to the pod, `attachments/`
  included. It is not part of the default graph.
- **Expected rows name only things whose IRIs never depend on a run:** records, versions, documents, judgments and
  reference versions. A query reaches an import or an entry session through the files its step wrote, and a revision
  through its record and its position.
- **A runner reports in EARL** as
  [`engine/executing.md`](https://github.com/jayostis/cascade-bridge-spec/blob/main/engine/executing.md) describes, with
  the runtime as `earl:subject`. An entry of a type the runner does not know is `earl:inapplicable`.

**A story** is a `story.json` with a `scripted-input/` folder beside it. It holds the pod's `address`, the `subject`'s
ID, and its `steps`, in order. A step has a `name`, a `when`, and one of:

| Key | What happened |
|---|---|
| `creation` | The pod was created. |
| `import` | An Apple Health export was imported: `export` is its folder, and `converted` a folder holding the Bridge's saved output for each document that is converted, `<document's file stem>/graph.ttl` and `findings.ttl`. |
| `entry` | The person entered records: the entry's Turtle file. Its session is `urn:cascade:this-entry`, and its drafts `urn:cascade:output-N`, with their versions. |
| `judgment` | A person made a judgment: its Turtle file, holding one `jdg:Judgment`. |
| `reference` | A reference version arrived: its name, as `scripted-input/references/references.ttl` describes it. |
| `matcher` | The matcher ran: `takes` names the step whose import or entry session's records it takes, and a run with none is a recheck. |

The story holds nothing a tool writes: no file lists and no import IDs. The runner gives each import, and each entry
session, a new random UUID on every run; it gives the entry's session the step's time. A step that is refused writes
nothing, and the replay goes on.

**The matcher's reference tables** are `scripted-input/references/`, in Turtle:

- **`references.ttl`**, the index: each `rec:ReferenceSeries` with its `rdfs:label` and the version it `rec:shipsWith`,
  and each version, a `prov:Entity`, with its `prov:specializationOf` series, its `pav:version` and the version it
  `prov:wasRevisionOf`, if any. A version's description in the pod, and the file a `reference` step files, are what the
  index states about the series and the version, less `rec:shipsWith`.
- **One file per version, holding its rows,** named from the version's name by N9. An ingredient map's rows are
  `<SNOMED CT code> rec:sameIngredientAs <RxNorm code>`; a vaccine group table's are
  `[] rec:cvxCode "141" ; rec:vaccineGroup "INFLUENZA"`. A version with no rows is a file with no triples.
- **The rule list is a table like the others.** Each row is a `rec:MatcherRule` giving its justification
  (`rec:justifiedAs`), each kind of record it applies to as `rec:kind` words it (`rec:appliesTo`), its comparison query
  as a path under `queries/v1-draft/` (`rec:query`), N5's name for that file's bytes (`rec:queryHash`), and the series
  of the table the query reads, if any (`rec:table`). A matcher judgment uses the rule list's version, so the one row of
  that version whose `rec:justifiedAs` is the judgment's `jdg:justification` says which query ran, by its bytes.

The rows of a table's current version are loaded into the default graph the matcher's queries read, and those of no
other version; they are never written to the pod.

## Naming

### N1. A record from a document keeps the name the Bridge gave it

The rule is the Bridge's: [`fixtures/naming/`](https://github.com/jayostis/cascade-bridge-spec/tree/main/fixtures/naming).

Vectors: `record-keeps-the-bridges-name`. Planted cases: P10, P19.

### N2. A record from an entry is named by the record rule from the subject, the entry's start and the draft's position

The record rule is [`fixtures/naming/name.rq`](https://github.com/jayostis/cascade-bridge-spec/blob/main/fixtures/naming/name.rq),
and its three inputs, in this order, are the subject's IRI, the entry's start time as an `xsd:dateTime` in UTC, and the
draft's position N from `urn:cascade:output-N`. The time is written `YYYY-MM-DDThh:mm:ssZ`, with any fraction of a
second the entry gives kept and its trailing zeros dropped. The session's ID is not an input.

Vectors: `entry-record-name`, `two-drafts-of-one-entry-are-two-records`. Planted cases: P16.

### N3. A version is named from its content

The rule is the Bridge's: `VersioningTest` in
[`vocab/bridge.ttl`](https://github.com/jayostis/cascade-bridge-spec/blob/main/vocab/bridge.ttl) and
[`fixtures/versioning/`](https://github.com/jayostis/cascade-bridge-spec/tree/main/fixtures/versioning). An entry's
versions are named by the same rule, with a reference to a draft record replaced by that record's name.

Vectors: `entry-version-name`, `change-undone-reuses-its-version`. Planted cases: P2, P16, P18.

### N4. A revision is named the same way, from its own triples

Its placeholder is `urn:cascade:this-revision`, and its triples are: `rdf:type rec:Revision`, `rec:revisionOf`,
`rec:version`, `prov:generatedAtTime` (the import's or the session's start), `prov:wasGeneratedBy` (the import or the
session), `prov:wasRevisionOf` (the record's previous revision, if it has one), and every other statement on the arrival
except `bridge:arrivedAs` and `prov:wasGeneratedBy`. Its name depends on a run, through the import's or the session's
ID, so no expected row names it: the vectors pin the triples it is named from.

Vectors: `revision-holds-its-arrival`, `a-later-revision-keeps-the-earlier`. Planted cases: P2.

### N5. A document is named by its bytes

`ni:///sha-256;` followed by the unpadded base64url SHA-256 of its bytes.

Vectors: `document-name`. Planted cases: P9, P19.

### N6. A matcher judgment is named by the record rule

Its inputs, in this order: the matcher's IRI, the justification's IRI, the members' names sorted, then the sorted names
of everything it used.

Vectors: `judgment-name`, `a-judgment-cites-what-it-used`. Planted cases: P1, P12.

### N7. An import and an entry session each get a new random UUID

A `urn:uuid:`, version 4, new on every run. Nothing else does.

Vectors: `import-is-a-new-uuid`, `entry-session-is-a-new-uuid`. Planted cases: none; the example pod keeps fixed import
IDs until it is replayed from a story.

### N8. What a runtime gives the Bridge

- **The adapter:** `<repository>/tree/<commit>/`, from the adapter's entry in `cascade-runtime.json`.
- **The vocabulary:** the same form, for the vocabulary repository at the commit the adapter pins
  (`bridge:cascadeVocabularyPin`).
- **A document:** its N5 name, which is the name the Bridge itself gives it.
- **Its facts:** the document's IRI followed by `#facts`.

A checkout used as it is on disk is named by the commit it is at. Each IRI ends in a slash, so every file's path
resolves against it.

No vector shows this rule, because what the Bridge is given never reaches the pod. `engine/library.md` in
`cascade-bridge-spec` and the runtime's Bridge interface use it, and their own tests check it.

### N9. A file's name comes from the name of what it holds

For a `urn:uuid:` name, the UUID; for an `ni:///sha-256;` name, the hash in lowercase hex. An RDF file adds `.ttl`; a
stored document adds nothing. The folder and the fan-out are the layout's, [`pod-layout.ttl`](pod-layout.ttl).

Every vector shows this rule, because each graph is named by its file's path. Vectors: `files-named-from-what-they-hold`.
Planted cases: all.

## Arrivals

### A1. A document whose bytes the pod already keeps brings nothing new

It is not converted, and nothing is written. The vector's story saves no Bridge output for it, so a runtime that
converted it would have none.

Vectors: `same-bytes-again-writes-nothing`. Planted cases: P9, P25.

### A2. A record's first arrival writes the record, its version, and a revision with no `prov:wasRevisionOf`

Vectors: `first-arrival`. Planted cases: P2.

### A3. An arrival whose source version a revision of the record already carries writes no revision

The source version is the arrival's `pav:version`. No revision is written even if the content differs.

Vectors: `known-source-version-writes-no-revision`. Planted cases: P23.

### A4. An arrival whose version is the one the record is at writes no revision

Even under a new source version.

Vectors: `current-version-again-writes-no-revision`, `no-source-version-told-apart-by-content`. Planted cases: P17, P25.

### A5. Any other arrival writes a revision after the record's last one

Vectors: `new-content-writes-a-revision-after-the-last`. Planted cases: P2, P3.

### A6. Arrivals with no source version are told apart by their content alone

Vectors: `no-source-version-told-apart-by-content`. Planted cases: none.

### A7. A change that is undone at its source reuses the earlier version

The new revision points at it.

Vectors: `change-undone-reuses-its-version`. Planted cases: P18.

### A8. A record that is missing from a later export gets nothing written, and nothing of it goes

Vectors: `missing-from-a-later-export`. Planted cases: P5.

### A9. A revision holds exactly the triples listed in N4

Vectors: `revision-holds-its-arrival`. Planted cases: P2.

### A10. A document is kept when it wrote a revision or the Bridge raised findings on it

Kept is its bytes under `attachments/`, and its description. Otherwise nothing of it is written.

Vectors: `kept-for-its-findings`, `not-kept-without-revision-or-findings`. Planted cases: P19.

### A11. An import that kept any document writes its description once

That description is the label, the start and the association the Bridge gave, and `prov:used` for each kept document.
An import that kept nothing writes nothing, not even itself.

Vectors: `import-uses-each-kept-document`, `import-that-keeps-nothing-writes-nothing`. Planted cases: P9.

### A12. An entry writes its session's description

Each draft becomes a record (N2) with its version and a first revision, at the session's start, generated by the
session.

Vectors: `entry-files-each-draft`. Planted cases: P16.

### A13. The pod's creation writes the subject as a `rec:Subject`

With it, the owner's profile, saying only who the owner is, where the pod's root is and where the preferences file is,
and the preferences file, saying only that it is one and where the owner's type index is. The build writes the type
index, from the views in the layout.

Vectors: `creation-files-the-subject`. Planted cases: none.

### A14. Some steps are refused, and a refused step writes no revision and no import

Refused are: a graph holding a statement about no record, version, arrival, document or import; a record or draft of a
type the pod files nowhere; one import's documents disagreeing on the import's description; an entry holding other
than one activity; and an entry whose activity states a property by which [the layout](pod-layout.ttl) files an
activity elsewhere than an entry's.

Vectors: `refused-stray-statement`, `refused-type-filed-nowhere`, `refused-import-disagreement`,
`refused-entry-of-two-activities`, `refused-entry-session-filed-elsewhere`. Planted cases: none.

## The matcher's procedure

### M1. A step's records are those whose first revision came from that step's import or entry session

A step's records are those whose first revision, the one with no `prov:wasRevisionOf`, was generated by
(`prov:wasGeneratedBy`) the import or entry session that step made. The matcher is given that activity; it reads no file
name and no list of steps. A record of the subject's with no one first revision fails the run.

No vector can tell this from taking the records whose first revision's file the step wrote, since in a pod that follows
these rules the two always agree; `test_the_matcher_needs_no_file_names_or_event_list` in
[`tests/test_alex_rivera_matcher.py`](../tests/test_alex_rivera_matcher.py) shows the matcher reading triples alone.

Vectors: `takes-only-its-steps-records`. Planted cases: P1, P7.

### M2. The matcher takes only the subject's records

Those [`subjects.rq`](../queries/v1-draft/derivations/subjects.rq) gives the pod's `rec:Subject`, under the everyday
lens.

Vectors: `a-record-nobody-is-named-for-is-never-taken`, `a-retracted-about-stops-taking`. Planted cases: P8, P24.

### M3. It takes them in order of arrival, then by record name

Arrival is the first revision's `prov:generatedAtTime`, compared as a time. All of one step's records arrive at the
step's start (N4), so the record name decides among them. It compares each with the subject's other records, then adds
it to them for the next.

No vector can tell ordering by record name from ordering by file path, since a record's file is named from its name
(N9) in its kind's folder and no comparison joins two kinds; `taken-in-order-and-joining-the-compared` pins what the
order does.

Vectors: `taken-in-order-and-joining-the-compared`. Planted cases: P12.

### M4. Each row of the rule list runs its comparison query

For each row of the current rule list, the matcher runs the query the row names, over the pod, its derived state under
the everyday lens, and the rows of the current version of the table the row names. A row `(record, other)` of its
answer is a match when the record's kind is one the row applies to.

- R1, `jdg:SameCode`: [`matcher/same-code.rq`](../queries/v1-draft/matcher/same-code.rq).
- R2, `jdg:SameCodeAndDate`: [`matcher/same-code-and-date.rq`](../queries/v1-draft/matcher/same-code-and-date.rq).
- R3, `jdg:SameMappedCode`: [`matcher/same-mapped-code.rq`](../queries/v1-draft/matcher/same-mapped-code.rq), with the
  ingredient map.
- R4, `jdg:SameMappedCodeAndDate`:
  [`matcher/same-mapped-code-and-date.rq`](../queries/v1-draft/matcher/same-mapped-code-and-date.rq), with the vaccine
  group table.

Vectors: `same-code`, `same-code-ignores-a-procedures-date`, `same-cvx-code-needs-one-date`,
`mapped-code-under-the-current-table-only`, `vaccine-group-needs-two-codes-and-one-date`. Planted cases: P1, P7, P12.

### M5. It writes one judgment per record per rule that matched anything

The judgment's members are the record and everything it matched. It is `jdg:Same` with the rule's justification. It
uses the rule list's version, the table's version and each member's current version. It is attributed to the matcher,
at the run's time.

Vectors: `one-judgment-per-record-per-rule`, `a-judgment-cites-what-it-used`. Planted cases: P1, P15.

### M6. The matcher reads no person's Same or Different

Vectors: `reads-no-persons-judgment`. Planted cases: P11, P21.

### M7. A recheck re-runs the rule of each matcher Same that used a since-revised reference version

Unless the Same was retracted or superseded. It runs on the members that are still the subject's, under the current
tables, and writes a new judgment if at least two still match.

Vectors: `recheck-rederives-a-same-that-still-matches`, `recheck-skips-a-retracted-same`,
`recheck-skips-a-superseded-same`, `recheck-skips-a-record-whose-about-was-retracted`,
`recheck-writes-nothing-when-fewer-than-two-match`. Planted cases: P14.

### M8. A reference version's description is written only if the pod lacks it

Vectors: `reference-description-written-once`. Planted cases: P14.

### M9. If the pod already holds a judgment of that name, nothing is written

Not even the reference descriptions it would have written. So running again is always safe.

Vectors: `a-rerun-writes-nothing`, `a-rerun-keeps-the-judgments-first-time`. Planted cases: none.

### M10. A table's current version is the one the pod names, and otherwise the one its series ships with

`rec:shipsWith` in `references.ttl`.

Vectors: `shipped-version-until-the-pod-names-one`, `mapped-code-under-the-current-table-only`. Planted cases: P14.

### M11. A rule list whose row names a query that does not hash to the row's `rec:queryHash` refuses the run

It writes nothing. So does a rule list with a row naming a file outside `queries/v1-draft/matcher/`, a row without
exactly one `rec:justifiedAs`, `rec:query` and `rec:queryHash`, or two rows with one justification. A rule list's rows
are never edited: a changed query is a new version of the rule list, revising the old.

Vectors: `a-rule-list-naming-a-changed-query-is-refused`. Planted cases: none.

## Nothing is edited or deleted

### X1. No file, once written, changes or goes

A retraction, a later revision and an entered-in-error status each leave everything they follow in the pod.

Vectors: `a-retraction-deletes-nothing`, `a-later-revision-keeps-the-earlier`. Planted cases: P6, P13, P22, P24, P25.

## Write order

### W1. Content-addressed files are written first, and the revision and import files last

A step that stops partway then leaves nothing that passes for finished. The views, the type index and the manifest may
be stale after a crash, and are rebuilt.

No vector can show this rule, because a replay only sees finished steps. Each runtime tests it itself.
