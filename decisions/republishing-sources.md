# When a source moves, switches vendor or issues a new edition

Status: draft, 2026-10-21, from the review on #130. Adds server and organisation records, a connect act, a Same over
servers, organisations and documents with a derivation each, and within-organisation matcher rules; changes M2
(organisations are not the subject's records) and M1's triggers, and amends `jdg:currentlySame`. Names are
`naming.md`, whose rubric this note applies: a re-published record is a new definition (test 1), its join is a
judgment (test 2), one per server, organisation or document pair (test 3); which revision is current is
`currency.md`; what a judgment is and borrows is `judgments.md`.

## Question

A record is named by its server and id, and the research on #130 measured that pair moving: the address a client
holds changes while the server stays (2 to 3% of Epic's listed URLs a year, 41% not listed verbatim after one list
rewrite); a hospital switches vendor and re-issues every id (1 to 4.5% of US hospitals a year); a hospital hands the
person a second summary whose entry ids the generator minted. How are a re-published source's records joined to the
ones the pod holds, without a judgment per record where one judgment will do?

## What others do

- **FHIR** has `Provenance` for where a resource came from, `Linkage` for "these resources are one thing",
  `Patient.link` for merged patients, and `DocumentReference.relatesTo` (replaces, transforms, appends) for editions;
  `CapabilityStatement.implementation.url` is where a server states its own base.
- **CDA** gives a document `setId` and `versionNumber`, and `relatedDocument` with `RPLC` for the edition it replaces.
- **openEHR** puts the creating system in the version id, so a moved record is visibly from another system.
- **SPHN** keeps cross-provider sameness in `hasSharedIdentifier`; **git** names remotes and lets a user say two are
  one.

Sources: FHIR `Provenance` (https://hl7.org/fhir/R4/provenance.html), `Linkage` (https://hl7.org/fhir/R4/linkage.html),
`Patient.link` (https://hl7.org/fhir/R4/patient.html#links), `DocumentReference.relatesTo`
(https://hl7.org/fhir/R4/documentreference.html), `CapabilityStatement.implementation`
(https://hl7.org/fhir/R4/capabilitystatement.html); CDA `relatedDocument` (HL7 CDA R2, §4.2.3.3,
https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7); research 1 to 3 on #130
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6327416626,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328557801).

## Choice

Everything observed from a source is a record with versions, revisions and a current state, and sameness of sources
is one judgment per source-level fact, from which the per-record joins are derived.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| server | FHIR `CapabilityStatement` | a record named by the base URL the client used; a connect is an act, and each writes a version of what the server reported: self-asserted base, login endpoint, software | ours; the self-URL is evidence, never a name input, diverging from FHIR's own statement of where a server lives |
| organisation | `prov:Organization`; FHIR `Organization`; CDA custodian | a record, `prov:Organization`, named by server plus `Organization/{id}` or the custodian's `id` root and extension; name, address and identifiers on versions; a document names its custodian and author by it | borrowed from PROV; FHIR's `Organization` resource treated as any record |
| two servers are one | git remotes | a Same whose members are two servers, by a person on the app's proposal or by the machine under a guard; derivation: every record of one type and id under both is one record | ours; the derivation is `Linkage` computed rather than asserted |
| two organisations are one | `Patient.link`; SPHN | a Same whose members are two organisations, usually the machine's from a shared NPI or OID; derivation: the matcher's within-organisation rules run over both | ours |
| two documents are editions | CDA `RPLC`; `relatesTo` | a judgment between two documents from one custodian, the later edition named; derivation: entries whose content matches within the pair are one record, changed entries go to the matcher within the pair, the rest are new or dropped; the verdict is open | borrowed in substance from CDA and FHIR, which the adapters read where present |
| within-organisation rules | | inside one organisation a shared business identifier joins, and a shared code and date joins; which pairs, and what belongs to an organisation when one server serves many, is open | ours |
| record from a document | FHIR documents | named per document; joined across documents like any re-published record | borrowed from FHIR's within-one-bundle promise |
| what joins mean | `jdg:currentlySame` | a derived join counts as a counting Same; a record-level Different still wins; the amended definition is open | ours |

## Why

The three problems are one problem at three levels, answered by one mechanism: name by the source, join by one
judgment per source-level fact, and let the matcher work per record only inside the scope that judgment gives it.
Hashing the server's self-asserted base instead of the client's address was measured and lost (research 2): it
survives a path edit and not a hosting move (19 of 19 old Epic hosts now report the new host as themselves), MEDITECH
never sends it, eClinicalWorks reports one base for every practice, and Epic documents that it can differ per client
id; as a judgment input it keeps the benefit and makes the failure retractable. An address change is a server Same,
and ids survive (inferred, not observed), so the derivation joins by id; the app can propose it at connect time from
the self-URL and the login endpoint, before a record is pulled, and made later it has the same effect because it was
never baked into a name. Records pulled under the new address are still written, so a name never depends on a
judgment in one pod. A vendor switch re-issues ids, so a server Same joins nothing; but within one organisation a
shared identifier is certain and a shared code and date is strong, and those rules join most of the history, with
what is left on the review page. Two summaries from one hospital are editions: their custodian is one organisation
record by its OID, which survives across documents where entry ids do not, so the app can propose the edition, and
content matching within the pair is nearly safe where content matching across the pod is not. An organisation is a
record because a proposal, a view and a Same now point at one, and the source gives an OID or NPI to name it by; its
name and address sit on versions so a merger's rename is history. Everything here is derived, so timing does not
matter and retraction undoes every join at once. The floor is a source that carries no identifier at all, which falls
back to labels and a person's judgment, as today.

## Alternatives that lost

- **The server's self-asserted base as the name input.** The strongest case: it survived every Epic path edit
  measured, which is the common churn. It does not survive a hosting move, is absent from MEDITECH, and is one value
  for every eClinicalWorks practice.
- **Pin to the first address the pod saw for a server.** The strongest case: it would survive a hosting move too.
  The name would then depend on one pod's memory, so no other holder could recompute it.
- **A judgment per record.** The strongest case: it is what the matcher does today and needs nothing new. A moved
  server is one fact and thousands of records; one judgment says it once and is retracted once.
- **Organisations as blank nodes with a label.** The strongest case: nothing pointed at one, and labels collide. A
  proposal, a view and a Same now point at one, and the source gives an OID or NPI to name it by.
- **Name by the visible pair and pseudonymise at share time.** The strongest case: FHIR already has every part
  (`Provenance`, identifiers, `Linkage`, `relatesTo`), privacy belongs at the one boundary where it matters, and the
  pod stores source URLs, organisation names and OIDs in plain text anyway. Not yet answered; it is open below.

## Still open

- What a shared view may carry: never server or organisation records or their Sames, or the opaque scheme hides
  nothing once source records are shared. The alternative above stands or falls on this.
- The verdict for editions: `jdg:Same` means "one thing", and two editions are two documents; an edition relation of
  its own, citing CDA `RPLC` and `relatesTo`, or a Same with the documents' dates giving order.
- "Content matches" within a pair: entries that reference another record of their own document hash differently, so
  references must not count.
- The guard under which the machine makes a server Same (same self-URL and same login endpoint is the Epic path
  case; the self-URL read with which client id), and under which the app proposes an edition.
- What belongs to an organisation when one server serves many (81 brands on one Epic server; every eClinicalWorks
  practice on one base), and which code-and-date pairs are near-certain inside one organisation.
- The amended `jdg:currentlySame`, and M1's triggers for the scoped runs; a sync act is one trigger, since a union
  leaves pairs no matcher saw together, and the run names the sync as its cause.
- A matcher rule for organisations: `jdg:SameBusinessIdentifier` needs a shared code, which an organisation lacks,
  and M2 takes only the subject's records.
- Whether the NPI registry becomes a reference table kind; the organisation record does not wait on it.

## What would change our mind

Vendors publishing an old-to-new address mapping, or a stable server identity the client can read, would make the
server Same a derivation with no judgment. Servers keeping ids across a vendor switch would let the server Same cover
it. Generators guaranteeing deterministic entry ids would make editions join by id.
