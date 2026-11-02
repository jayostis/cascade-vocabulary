# Reports, notes and documents

Status: accepted, 2026-10-31: the owner accepted the departure in row "the text no entry holds". Written 2026-10-30
with the terms it rules under phase 1 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287), item 2,
[#291](https://github.com/jayostis/cascade-vocabulary/issues/291), and the narrative text of
[jayostis/cascade-bridge-adapter-ccda#50](https://github.com/jayostis/cascade-bridge-adapter-ccda/issues/50)). It is
the area note `clinical-terms-follow-fhir.md` asks for: what a report and a note borrow from FHIR, and the one place they
depart. Rows "report", "note or document", "a report's results", "a code", "an attachment" and "the text" only apply
accepted rule (b) of `clinical-terms-follow-fhir.md`; row "the text no entry holds" is a departure from FHIR, accepted by
the owner. It depends on `clinical-terms-follow-fhir.md`, `code-iris.md` (a coding in a system
with no property of its own is a literal typed by its system), `naming.md` (row "version": a node inside a version is a
fragment of it by role) and `partial-dates-and-absent-reasons.md` (how a source date is typed, padded and left absent).

## Question

A lab may send a vitamin B12 result only as a `DiagnosticReport` whose result is a PDF (`presentedForm`): no
Observation, so the pod holds no record of it, and "never checked" is false. A note says what a clinician concluded,
and the pod holds none, so a model reading the pod reports a finding the note holds as "not recorded". What records do a
report and a note make, from FHIR and from C-CDA, and what does each version hold?

What makes it hard: FHIR has two resources where C-CDA has three forms (a Result Organizer, a Note Activity, and a
section that is narrative only), and "document" already names the kept source file in this vocabulary
(`runtime/pod-layout.ttl`, `provenance/documents/`).

## What others do

Read on 2026-10-30.

- **FHIR R4 `DiagnosticReport`**: `status` 1..1 bound required to DiagnosticReportStatus (`registered | partial |
  preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown`); `category` 0..*, the
  discipline, department or service that created the report, bound by example; `code` 1..1, preferred LOINC;
  `effective[x]` `dateTime | Period`, the time or period the observed values relate to; `performer`; `result` 0..*,
  `Reference(Observation)`; `conclusion` string; `conclusionCode` 0..*, example SNOMED CT clinical findings;
  `presentedForm` 0..*, `Attachment`, the rich text of the full result.
- **FHIR R4 `DocumentReference`**: `status` 1..1 required DocumentReferenceStatus (`current | superseded |
  entered-in-error`); `docStatus` CompositionStatus; `type` 0..1, preferred LOINC document codes; `category`; `date`,
  when the document reference was created; `description`; `author`; `custodian`; `content` 1..*, each one `attachment`.
- **FHIR R4 `Attachment`**: `contentType`, `data`, `url`, `title`, `size`, `hash`, `creation`. **`DomainResource.text`**:
  a Narrative whose `div` holds the XHTML.
- **US Core** requires both resources for clinical notes, and profiles `DiagnosticReport` for labs and for reports.
- **C-CDA on FHIR 2.0.0, "C-CDA to FHIR Results"**: "Results in C-CDA are collected into `<organizer>` elements",
  "This corresponds to one FHIR DiagnosticReport for the `<organizer>`", each result observation a referenced
  Observation through `.result`; `effectiveTime` to `effectiveDateTime` or `effectivePeriod`.
- **C-CDA on FHIR 2.0.0, "C-CDA to FHIR Notes"**: a Note Activity (`2.16.840.1.113883.10.20.22.4.202`) becomes a
  `DocumentReference`. "The root code in C-CDA is always `34109-9: Note`. A more specific code may be sent in
  translation which should be sent as the DocumentReference.type"; `author/time` to `.date`. It maps no section to a
  record: a section is part of the document's `Composition`.
- **C-CDA 3.0 sections that are narrative**, each coded by a LOINC note code: Assessment
  (`2.16.840.1.113883.10.20.22.2.8`, 51848-0 Evaluation note), Plan of Treatment (`2.16.840.1.113883.10.20.22.2.10`,
  18776-5 Plan of care note), Assessment and Plan (`2.16.840.1.113883.10.20.22.2.9`, 51847-2 Evaluation + Plan note),
  History of Present Illness (`1.3.6.1.4.1.19376.1.5.3.1.3.4`, 10164-2), Hospital Course
  (`1.3.6.1.4.1.19376.1.5.3.1.3.5`, 8648-8 Hospital course note).

Sources: https://hl7.org/fhir/R4/diagnosticreport-definitions.html, https://hl7.org/fhir/R4/documentreference-definitions.html,
https://hl7.org/fhir/R4/datatypes-definitions.html#Attachment,
https://hl7.org/fhir/R4/domainresource-definitions.html#DomainResource.text,
https://hl7.org/fhir/R4/valueset-diagnostic-report-status.html, https://hl7.org/fhir/R4/valueset-document-reference-status.html,
https://hl7.org/fhir/us/ccda/en/CF-results.html, https://hl7.org/fhir/us/ccda/en/CF-notes.html,
https://hl7.org/cda/us/ccda/StructureDefinition-AssessmentSection.html,
https://hl7.org/cda/us/ccda/StructureDefinition-PlanOfTreatmentSection.html,
https://hl7.org/cda/us/ccda/StructureDefinition-AssessmentandPlanSection.html,
https://hl7.org/cda/us/ccda/StructureDefinition-HistoryofPresentIllnessSection.html,
https://hl7.org/cda/us/ccda/StructureDefinition-HospitalCourseSection.html; the LOINC names from NLM Clinical Tables
(https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search?terms=51848-0).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| report | FHIR `DiagnosticReport`; C-CDA on FHIR's Result Organizer | a record kind `cascade:DiagnosticReport`, word "Report": code, name, category, effective time, the time it was issued, conclusion, conclusion code, status, performer, attachments (`ontologies/cascade.ttl`, `queries/derivations/records.rq`) | borrowed |
| note or document | FHIR `DocumentReference`; C-CDA on FHIR's Note Activity | a record kind `cascade:ClinicalNoteOrDocument`, word "Note or document", not "Document", which is the kept source file: type, type name, title, date, status, the status of its content (`docStatus`, apart from the reference's own status), author, attachments (`ontologies/cascade.ttl`) | borrowed; the class name is ours |
| a report's results | `DiagnosticReport.result`; `Observation.hasMember` | each result record's IRI on the report's version, by RO's "has member" (`obo:RO_0002351`), as the panel members table already uses it, with no class constraint (`ontologies/cascade.shapes.ttl`) | borrowed from RO |
| a code | `code-iris.md` | a report's LOINC or SNOMED CT code and a note's LOINC type are code IRIs; any other system's is a literal typed by its system; a report's category is always such a literal, since no table joins a category (`ontologies/cascade.ttl`) | borrowed |
| an attachment | FHIR `Attachment` | a node of the version, `<version>#attachment-n`, with its media type, title and address; its bytes stay in the kept document (`ontologies/cascade.ttl`) | borrowed |
| the text | `DomainResource.text`; C-CDA `section/text` | one `cascade:narrativeText` per version of a record of any kind, the text its source wrote for it in document order with the markup removed: a note's or report's own text, and for any other kind the text its C-CDA statement's `text/reference` points at, the referenced element only (a table row's cells one to a line, a list item), as FHIR's `DomainResource.text` and C-CDA on FHIR build `.text` from the referenced element; a PDF is not read (`ontologies/cascade.ttl`) | borrowed, less the table header C-CDA on FHIR adds to each row; one string where FHIR keeps XHTML |
| the text no entry holds | C-CDA on FHIR maps section text into `Composition.section.text` | the blocks of a section's text that no entry references are one note record per section, for any section kind, its type the section's code, its date the document's `effectiveTime` (#291); a section none of whose entries references its text keeps all of it; an entry's `typeCode="DRIV"` is not read, since a download marks DRIV and still carries text no entry holds | diverged: a reading needs a record of note size, and `Composition` is exchange machinery |
| joining | the matcher's rules | kinds never join (`tests/fixtures/kinds-never-join`); two notes of one type, LOINC or, when neither has LOINC, another system's, join when, from one organization, the shorter text begins or ends the longer as whole lines, dated no earlier, and no two notes grew apart from it (R19), or, from any sources, the texts are equal once white space is one space (R20), either text of at least 200 characters; and two notes of one document master identifier join from any sources (R21) (`queries/matcher/same-note-type-and-text-grown-within-one-organization.rq`, `queries/matcher/same-note-type-and-text.rq`, `queries/matcher/same-note-or-document-master-identifier.rq`, rule M24) | ours |

## Why

**Why a report is a record of its own.** (row "report") The false gap is the PDF-only report: a result sent only as
`presentedForm` has no Observation, so it makes no lab result, and a question that finds no result says it was never
checked. As a record, the report is found by its code and date though its value is in a file no query reads. A FHIR
panel Observation is not made a report: its members are already records, and a class named for FHIR's resource holds
only what FHIR or C-CDA on FHIR maps to it.

**Why the class is not called a document.** (row "note or document") Here a document is the file a pod keeps, the
`prov:Entity` every revision is derived from. A note sent as a C-CDA document is both, so the record is named for what
FHIR's resource holds, a clinical note or document, and its kind word for what a person reads it as.

**Why results are record IRIs and the link is RO's.** (row "a report's results") A report names results its source
also sent as records, as a variant interpretation names its variant; RO's "has member" already carries that meaning in
the panel members table, so no new term is minted. The Bridge validates each record's graph alone, so a class
constraint on the link would report every report whose results are in another record's graph.

**Why a category is a literal.** (row "a code") A code IRI exists so that two adapters' codes join a table or each
other. A category is read, not joined, and its common systems (HL7 v2 table 0074, LOINC parts) would need two
properties for one element; one literal typed by its system keeps every coding a source gave in one place.

**Why an attachment is a node.** (row "an attachment") A report may present several forms and a note several
contents; each has its own media type and title, so each is a node, named by its position as an identifier is.

**Why one string of text.** (row "the text") A model and a reading quote text, not markup. The XHTML or the C-CDA
narrative block stays in the kept document, which the revision's selector reaches.

**Why the text no entry holds is a note, for any section.** (row "the text no entry holds") C-CDA documents carry the
assessment, the plan and the hospital course as sections with no entries. FHIR would hold them as `Composition.section`,
which exists to assemble a document for exchange; the pod keeps the document itself, and a reading needs something of
note size to target and cite. Looked at FHIR's `Composition` and C-CDA on FHIR's notes page: failed because neither gives
a section an identity of its own apart from its document.

The first rule kept a section only when its template was one of five and it held no entries, on the premise that an
entry-bearing section's text is the human-readable copy of its entries. Real downloads break it, and every scored loss
of the care-gap evaluation's first round traces to it
([#287, the owner's ruling](https://github.com/jayostis/cascade-vocabulary/issues/287#issuecomment-6582465877)): a
Results section carries a CT report with a lung nodule beside the lab table its entries reference; every Encounters
section has no entry; a Plan of Treatment section that gains two order entries loses its discharge text; a pharmacy's
fill-history table is pointed at by no entry. So any section's text that no entry references is kept, and a section
whose entries reference none of it keeps all of it, the safe default. A block is a `paragraph`, `list item`, table row
or a run of text directly in `text`; a table or list that holds a referenced block is walked into, one that holds none is
kept whole; a table's header (`thead`, `tfoot`, `caption`) is kept only beside a kept row, so a fully said lab table
leaves no header line. `typeCode="DRIV"` is not read: a download marks it and still carries text no entry holds.
Measured on Priya's downloads the notes grow by 2.1 KB, at scale by 20 KB.

**Why an entry's text is on its version.** (row "the text") C-CDA on FHIR builds a resource's `.text` from the element
its `text/reference` points at, with the table's header rows; we keep the referenced element only, because the header
costs bytes on every lab row and the version already has the test's name. It is on the statement's own version, for
every kind, because the colonoscopy's finding ("normal; repeat in 10 years"), a result's label ("historical result") and
a medication's stop reason are what the source wrote for that row and nothing else holds them. A concern act's reference
is not read: it is no record, and no download carries one. A Result Organizer's text is the report's. Text the row
references only for a name, the other cells of a referenced row, are named in the adapter's `ccda:narrative` as a known
loss. The matcher's trimmed lines stay a note's and a report's: the note rules read nothing else.

**Why kinds never join, and how two notes do.** (row "joining") No rule yet says when a report sent as a
`DiagnosticReport` and the same report sent as a `DocumentReference` are one; joining them by code and date would join
two notes of one day. A section's kept text has no id, so it is named by its code and its text, and the departure
in row "the text no entry holds" holds only if its repeats join. Counted on the comparison person `priya_l` (19
downloads, converted with the C-CDA adapter's note sections; the counts, lines and timings are posted at
https://github.com/jayostis/cascade-vocabulary/issues/321#issuecomment-6533857683): 10 note sections made 9 records, identical re-sends
already one record; Fernhill's 5 cumulative plans of treatment, each keeping every visit's paragraph and adding the
latest, made 4 records and 4 entries. A grown note's earlier text begins (or, newest first, ends) its later one, so R19
joins them, within one organization, since another organization's note that holds a note whole is quoting it; the
later must be dated no earlier, by instant when both are times, or a note cut down to its latest paragraph would lead
and hide the rest. Growth is a chain: a plan of four generic lines passes the 200-character guard, and two visits'
plans written from it each hold it; joining both to it would put the two visits in one entry behind one lead, so a
note two notes grew apart from joins neither, and the entries R19 makes are chains whose lead holds every line. With R19
Fernhill's 4 records are 1 entry and `priya_l`'s 9 note records are 6 entries; every other note there is distinct.
R20 joins one note two sources sent (a hospital course in the hospital's and the clinic's summaries), compared with
white space read as one space because two adapters break lines differently. The 200-character guard comes from the
same inputs: every generic plan line there, the kind that recurs in unrelated notes, is under 45 characters ("Follow-up in 2 months."),
the longest generic line, an emergency department's warning to come back, is 106, and the shortest note that grew is
271. A note's text stays in its name: keyed on its code alone, each visit's history of present illness would
supersede the last. One document can reach the pod twice, as an unstructured C-CDA document's note and as a FHIR
`DocumentReference` to it, which holds no text when its attachment is the C-CDA document; FHIR R4 maps
`DocumentReference.masterIdentifier` to CDA's `ClinicalDocument/id`
(https://hl7.org/fhir/R4/documentreference-mappings.html), so R21 joins them by that identifier, a term of its own,
`cascade:noteOrDocumentMasterIdentifier`, since `dct:identifier` holds a record's business identifiers, which
`DocumentReference.identifier` is. A section or a Note Activity is part of a document and never carries it.

## Alternatives that lost

- **A FHIR panel Observation as a report.** The strongest case: C-CDA on FHIR maps the organizer, the panel's C-CDA
  form, to a report, so both groupings would be one kind. It lost because it closes no false gap (every member is a
  record already) and puts in a class named for `DiagnosticReport` what FHIR itself holds as an Observation.
- **One class for both.** The strongest case: a report and a note are both text a clinician signed. It lost because
  FHIR keeps two resources with different fields (results and a conclusion; a type and an author) and statuses.

## Still open

- A note's category is not carried; lean: add it when a question reads it. `docStatus` and a report's `issued` time
  waited for the same and are carried: `pod/My reports, notes and documents` reads them, so a preliminary note and a
  report with no effective time are told apart.
- Whether a `DocumentReference` whose attachment is a C-CDA document makes a note: the FHIR adapter's step for #291
  settles it.
- A rule joining one report sent both ways.
- An edited note: a source that sends a section again with a line reworded or a typo fixed names a new record, and
  no rule joins it, so the pod holds two current notes. A C-CDA document that says it replaces another, by one
  `setId` and a higher `versionNumber` (with a `relatedDocument` of type `RPLC`), lets the C-CDA adapter make its
  sections new versions of the replaced document's records, each section matched by its code: that covers an
  amendment the source sends as a new version of the same document. It does not cover the common portal case, where
  each download is a new document with a new `setId` that replaces nothing, a section edited between two such
  summaries; nor a document holding two sections of one code. For those no safe rule was found: a typo in a
  one-paragraph section changes its only line, so line overlap cannot see it, and a word-level likeness cannot be
  computed in the plain SPARQL a matcher runs; the visits it must not join look alike (Kestrel's three plans in
  `priya_l`, each "Most recent visit, <date> (Susan Park, MD): …" and an "Annual physical due …" line, share no line).
  The kit inputs hold no edited section (0 pairs of one source and type that share a line without one holding the
  other), so no threshold could be measured. Lean: a likeness rule once a source is measured sending edits, filed as
  likely for review.
- R20 compares no date: one templated text of 200 characters or more that two organizations wrote at two visits is
  taken for one note with two copies. A date guard would break the case R20 exists for, a hospital course whose two
  copies carry the hospital's and the clinic's document dates. Lean: none until a source is measured sending such a
  template.
- An undated note cut down from a dated one, or the other way round, passes R19's date guard, so an undated copy can
  lead the entry; the lead rule, not R19, would have to say what an undated revision weighs.
- R21 waits on the adapters writing `cascade:noteOrDocumentMasterIdentifier` (the FHIR adapter from
  `DocumentReference.masterIdentifier`, the C-CDA adapter on an unstructured document's note); until then it joins
  nothing they convert, and rule M24 has no example of it.

## What would change our mind

A source measured sending its notes as `Composition` resources would make sections records by FHIR's own route. A
question that needs a category joined across sources would make it a code IRI.
