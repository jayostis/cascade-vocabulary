# Where a pull looked

Status: draft, 2026-10-29, for #296, from the care-gap epic's phase 1 (#287). Adds `cascade:answersForRecordClass` and
`cascade:refusedForRecordClass`. A document's clocks are `currency.md`'s (`cascade:answeredAsOf`, `pav:retrievedOn`); the
rules that read these terms are #287's phase 3.

## Question

A rule that asks "no B12 result in the last year?" must say where it looked: "Northgate, lab results, as of
2025-02-01". A pod holds documents, and a document today says when it was retrieved, not what was asked for. A pull
that fetched only medications looks like one that found no labs, and a search the hospital refused looks like one it
answered with nothing. With no server of record to ask afterwards, the document has to say, when it is saved, which
kinds of record its source answered for and which it refused, or "not found" cannot be told from "not asked".

## What others do

Each quotation was read at its source on 2026-10-29 (verified).

- **FHIR R4 search.** A search answer is a `searchset` Bundle. `Bundle.link` is "A series of links that provide
  context to this bundle", the `self` link the search as the server ran it; `Bundle.total` is "the total number of
  entries of type 'match' across all pages in the search". Both describe one search's answer; nothing states that a
  set of resources is all a server holds of a type for a patient, and nothing records a refused search.
- **FHIR R4 AuditEvent.** `AuditEvent.entity.query` is "The query parameters for a query-type entities", a
  `base64Binary` whose meaning "is specific to the AuditEvent.type, AuditEvent.subtype, AuditEvent.entity.type, and
  AuditEvent.entity.role". It records that a query ran, for an audit, not what the result covers.
- **FHIR Bulk Data (STU2) `$export`.** The completion manifest has `request`, "The full URL of the original Bulk Data
  kick-off request", and `output`, one item per file with its resource `type`; but "If no data are found for a
  resource, the server SHOULD NOT return an output item for that resource", so a type absent from `output` is either not
  asked or empty. Partial failures go in `error`, as OperationOutcome files, with no per-type structure.
- **C-CDA** (the review's correction 8; inferred, not quoted). A section is a summary the author chose, not a search:
  a CCD's Results section usually holds recent results, so its presence does not say the document holds every result.
  A section's `nullFlavor` says the section has no information, which is not the same as the source holding none.
- **PROV-O.** `prov:used` and `prov:qualifiedUsage` record what an activity used, not what a result covers.

Sources: FHIR R4 Bundle (https://hl7.org/fhir/R4/bundle-definitions.html#Bundle.link,
https://hl7.org/fhir/R4/bundle-definitions.html#Bundle.total), AuditEvent
(https://hl7.org/fhir/R4/auditevent-definitions.html#AuditEvent.entity.query), Bulk Data STU2 export
(https://hl7.org/fhir/uv/bulkdata/STU2/export.html), PROV-O (https://www.w3.org/TR/prov-o/); the care-gap epic's
review, correction 8 (on #287).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| answered | `Bundle.link` `self`, `Bundle.total`, `$export` `output`: one search's answer, no coverage | a document states `cascade:answersForRecordClass` for the class of record each search its source answered returns: the document holds every record that search returned as of its `cascade:answeredAsOf`, else its `pav:retrievedOn` (`ontologies/cascade.ttl`) | ours: nothing states coverage |
| refused | an HTTP 403 to the search; `$export` `error` | a document states `cascade:refusedForRecordClass` for the class of each search its source refused (`ontologies/cascade.ttl`) | ours |
| by class | `AuditEvent.entity.query`, `$export` `request`: the search itself | the value is a record class, `cascade:LaboratoryTestResult`, never the search string or the kind's word (`ontologies/cascade.shapes.ttl`) | diverged: a rule's scope is per kind |
| who writes them | | the FHIR pull, from the searches `pull.json` lists and the ones it was denied (`runtime/steps.md`) | ours |
| not stated | | a document stating neither term for a class is "scope not stated", and a rule says so rather than claim an absence; a C-CDA document always is, in phase 1 (#287) | ours |

## Why

**Why a statement on the document, not a search log.** (rows "answered", "refused") The question a rule asks of a
pod is "of this source, which kinds did it answer for, as of when": that is a fact about the document a pull saved,
beside its clocks. A search log (an `AuditEvent`, an `$export` manifest) answers "what ran", and a rule would have to
re-derive coverage from requests and status codes it cannot see. Every prior art above stops at the search; none
states coverage, so the terms are ours.

**Why a class, not the search.** (row "by class") A rule's scope sentence is per kind ("lab results"), and the
search-to-kind map already exists in the importer, so mapping once there costs nothing. One kind may need several
searches (a medication is a `MedicationRequest` or a `MedicationStatement`), and C-CDA has no search at all, so the
search string would make every rule carry the map. A search whose resources become no record (an `Encounter`, a
vital sign today) states nothing.

**Why both terms may hold for one class.** (rows "answered", "refused") Each term is per search: a hospital that
answers `MedicationRequest` and refuses `MedicationStatement` answered for medications and refused for them, and both
are true. Which wins for an absence is the rule's to say, and a rule that claims absence needs the class answered and
not refused.

**Why C-CDA states neither.** (row "not stated") A section is what an author chose to include, so "the document holds
every record of that class its source held" is false for a CCD's Results section; correction 8 of the epic's review
dropped the C-CDA half.

## Alternatives that lost

- **The search string on the document** (`"Observation?category=laboratory"`). The strongest case: it says exactly
  what ran, with nothing mapped. It lost because every rule would map searches to kinds, and C-CDA and Apple Health
  have no search to write.
- **Coverage from `$export`'s `output`.** The strongest case: it is a FHIR standard, and an export is a pull. It lost
  because a type absent from `output` is either not asked or empty, which is the ambiguity this note removes.
- **One term with a status** (answered, refused, not asked). The strongest case: one property to read. It lost
  because it needs a node per class to name and hash, where two object properties are one triple each.

## Still open

- How a rule phrases a refused or unstated scope, and whether a later pull of the same source widens an earlier
  one's: #287 phase 3. Lean: each document's scope stands alone; the rule reads the latest document of the source
  that answered for the class.
- Whether an Apple Health export states scope: its records are what the phone held, which is not a search. Lean: no.

## What would change our mind

- A FHIR or SMART artefact that states, per type, that a set is complete for a patient (an R6 or US Core addition):
  we would borrow it.
