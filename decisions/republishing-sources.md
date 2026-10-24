# When a source moves, switches vendor or issues a new edition

Status: draft, 2026-10-21, from the review on #130. Adds server and organisation records, a connect act, a Same over
servers and over organisations with a derivation each, and within-organisation matcher rules; changes M2
(organisations are not the subject's records) and M1's triggers, and leaves `jdg:currentlySame`'s amendment open. Names are
`naming.md`, whose rubric this note applies: a re-published record is a new definition (test 1), its join is a
judgment (test 2), one per server or organisation pair (test 3); which revision is current is
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
https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7); research 1 to 5 on #130
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6327416626,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328557801,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6334427968,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6334428443); the evidence issue keeping the
churn and self-URL counts and scripts (https://github.com/jayostis/cascade-vocabulary/issues/201).

## Choice

Everything observed from a source is a record with versions, revisions and a current state, and sameness of sources
is one judgment per source-level fact, from which the per-record joins are derived.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| server | FHIR `CapabilityStatement` | a record named by the base URL the client used; a connect is an act, and each writes a version of what the server reported: self-asserted base, login endpoint, software, and the client id it was reported to, since a pod holds connects from several apps; an address known only from a document or an export (Apple's copy carries the URL, not what the server said) has a server record with no version (A16, A17) | ours; the self-URL is evidence, never a name input, diverging from FHIR's own statement of where a server lives |
| organisation | `prov:Organization`; FHIR `Organization`; CDA custodian | a record, `prov:Organization`, named by server plus `Organization/{id}` from a server, and by a business identifier from a document, as `naming.md` maps it (a C-CDA `id` through HL7's CDA-to-FHIR identifier mapping, a FHIR `Organization.identifier`, a registered OID as its URI in both, so one NPI is one record in either format); name, address and identifiers on versions; a document names its custodian and author by it, in `cascade:CustodianRole` and `cascade:AuthorRole`; never the subject's record, so never taken by the matcher (M2) | borrowed from PROV; FHIR's `Organization` resource treated as any record |
| two servers are one | git remotes | a Same whose members are two servers, by a person on the app's proposal, or by the machine when two connects made with one client id report the same self-URL, the same login endpoint and the same host (the Epic path edit: 57 of 57 kept the self-URL, 19 of 19 hosting moves changed it; verified, probed, [research 2](https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407)); with no like-for-like connect, the app proposes and the person decides; derivation: every record of one type and id under both, within one organisation, is one record | ours; the derivation is `Linkage` computed rather than asserted |
| two organisations are one | `Patient.link`; SPHN | a Same whose members are two organisations, usually the machine's from a shared NPI or OID, where one was read from a server or a document named them by different identifiers; derivation: the matcher's within-organisation rules run over both | ours |
| two documents from one organisation | CDA `setId`, `versionNumber`, `relatedDocument` `RPLC`; FHIR `relatesTo` | no judgment: a document names its custodian and author organisations by an identifier they carry (a C-CDA `id`; a FHIR document's `Organization` by an NPI or an identifier whose system is rooted at an OID or a UUID, never by its id in the bundle), as `naming.md` picks one, so two documents from one organisation point at one organisation record by name; where a document declares that it replaces another, the adapter reads it onto the document's version, once #254 rules what a replaced document is named by, since a pod names a document by its bytes; the overlap between the two is joined by name for C-CDA entries and by the within-organisation rules for a FHIR document's | borrowed: a declared replacement is the standards' fact, stored as stated; "edition" as a judgment of ours is dropped |
| within-organisation rules | | inside one organisation a shared business identifier joins, and a shared code and date joins; which pairs, and what belongs to an organisation when one server serves many, is open | ours |
| what a run compares | | a matcher run binds `?record` to the records the import, entry or sync that triggered it brought, never the whole pod; a sync is a trigger, named as the run's cause (M1); the matcher queries change to bind it | ours |
| record from a FHIR document | FHIR documents | named per document; joined across documents like any re-published record; a C-CDA's entries are named across documents by CDA id, per `naming.md` | borrowed from FHIR's within-one-bundle promise |
| what leaves the pod | | a shared view carries records, by their opaque names, and their current states; never a server or organisation record, an act, or a Same over them, so a name outside the pod is stable and citable and says nothing of where the record came from; the keyed scheme is for a pod that must hide it even from one who knows the address, and the URL scheme for one that need hide nothing | ours |
| what joins mean | `jdg:currentlySame` | a derived join counts as a counting Same; a record-level Different still wins; the amended definition is open | ours |

## Why

**Why one mechanism.** The three problems are one problem at three levels, answered by one mechanism: name by the
source, join by one judgment per source-level fact, and let the matcher work per record only inside the scope that
judgment gives it. Everything here is derived, so timing does not matter and retraction undoes every join at once.

**Why the client's address, and the self-URL only as evidence.** Hashing the server's self-asserted base instead of
the client's address was measured and lost (research 2): it survives a path edit and not a hosting move (verified,
probed: 19 of 19 old Epic hosts now report the new host as themselves), MEDITECH never sends it, eClinicalWorks
reports one base for every practice (both verified, probed), and Epic documents that it can differ per client id; as
a judgment input it keeps the benefit and makes the failure retractable.

**Why the machine's server Same needs two connects under one client id.** An address change is a server Same, and ids
survive (inferred, not observed), so the derivation joins by id; the machine makes it only from two of the pod's own
connects under one client id, because Epic documents that the self-URL can differ by the client id asking and a pod
holds connects from several apps, so a mismatch across apps proves nothing and is left to the person, the safe
direction; the app may propose it before a record is pulled, and a judgment made later has the same effect because it
was never baked into a name. Records pulled under the new address are still written, so a name never depends on a
judgment in one pod.

**Why Apple's copy usually needs no join.** The common case needs no join at all: Apple's copy of a Mercy record
carries the address Apple used, and where that is the address the app used the names already agree and the copy is
one more revision; where Apple's address is the older one, the pod never spoke to it, so the join is the person's, or
the app connects to the old address itself and earns like-for-like evidence while it still answers.

**Why a server Same joins only within one organisation.** The derivation is confined to one organisation because a
multi-tenant server is one server, so the Same is true, and `Patient/1` under two of its practices are two people.

**Why a vendor switch is joined by the within-organisation rules.** A vendor switch re-issues ids, so a server Same
joins nothing; but within one organisation a shared identifier is certain and a shared code and date is strong, and
those rules join most of the history, with what is left on the review page. The floor is a source that carries no
identifier at all, which falls back to labels and a person's judgment, as today.

**Why a run is bound to what arrived.** A pair neither of whose records arrived was compared when the later of them
did, so a run compares the arrived records with their code groups and nothing else; a sync is a trigger because a union leaves
pairs no matcher saw together. With `?record` unbound, every run enumerates every ordered pair of every code group,
about 1 to 5M rows, and same-result within one code is about 80M comparisons, where bound it is about 100k
(assumed ten-year pod, [#206](https://github.com/jayostis/cascade-vocabulary/issues/206)).

**Why two documents from one organisation need no judgment.** Two summaries from one hospital need no judgment of
their own: each names its custodian by the identifier it carries, so both point at one organisation record by name, a
C-CDA's entries are named across documents by their CDA ids under that custodian, and a FHIR document's entries fall
to the within-organisation rules like a vendor switch's; "edition" as a judgment would have been a story told about
two documents that are only sometimes editions, and where one is, the document says so and the adapter stores what it
said.

**Why an organisation is a record.** An organisation is a record because a proposal, a view and a Same now point at
one, and the source gives an OID or NPI to name it by; its name and address sit on versions so a merger's rename is
history.

**Why privacy is drawn at the boundary.** The server and organisation records are in the clear inside the pod because
the person owns the pod; the opaque name earns its keep at the boundary, where a receiver gets a name it can cite and
reconcile by, and nothing that says where the record came from, because what leaves the pod is the person's choice,
record by record, and the source is one more thing they may not want known.

## Alternatives that lost

- **The server's self-asserted base as the name input.** The strongest case: it survived every Epic path edit
  measured, which is the common churn. It does not survive a hosting move, is absent from MEDITECH, and is one value
  for every eClinicalWorks practice.
- **Pin to the first address the pod saw for a server.** The strongest case: it would survive a hosting move too.
  The name would then depend on one pod's memory, so no other holder could recompute it.
- **The guard on self-URL alone, whoever asked.** The strongest case: it would fire on Apple's addresses and on
  another app's connects too. Apple's export carries no capability statement, so there is nothing to compare, and a
  self-URL reported to another client id can differ for the same server, so the comparison would miss joins it
  should make and could not be told from a real move.
- **An edition judgment between two documents, with a derivation.** The strongest case: CDA and FHIR both name the
  relation, and one judgment would join a whole summary's entries at once. Two summaries from one organisation are
  only sometimes editions; where they are, the document says so and that is a fact, not a judgment; and the entry
  joins already come from names (C-CDA) or the within-organisation rules (FHIR), so the derivation had nothing left
  to do.
- **A judgment per record.** The strongest case: it is what the matcher does today and needs nothing new. A moved
  server is one fact and thousands of records; one judgment says it once and is retracted once.
- **Organisations as blank nodes with a label.** The strongest case: nothing pointed at one, and labels collide. A
  proposal, a view and a Same now point at one, and the source gives an OID or NPI to name it by.
- **Name by the visible pair and pseudonymise at share time.** The strongest case: FHIR already has every part
  (`Provenance`, identifiers, `Linkage`, `relatesTo`), privacy belongs at the one boundary where it matters, and the
  pod stores source URLs, organisation names and OIDs in plain text anyway. A pseudonym per share is a new name per
  share, so a receiver cannot tell that two shares hold one record, or cite one back, and a hospital importing over the protocol
  needs the pod's names stable for the same reconciliation the pod does; the opaque name is stable and says nothing,
  and the line is drawn at what a share carries instead.
- **A run over the whole pod, filtered to its records afterwards.** The strongest case: the matcher queries as written
  leave `?record` unbound, so a run needs no list of what arrived and misses nothing. Every run then enumerates every
  pair of every code group, 1 to 5M rows and 80M same-result comparisons, a thousand times in ten years (assumed,
  #206).

## Still open

- The full list of what a shared view may carry, beyond "records and their current states, no source records, acts
  or the Sames over them, and a person's judgment only as the share-time choice says": a views decision, resting on the tenet that anything in the pod may be what the person does not want
  shared, so the person chooses what leaves and nothing leaves by default.
- Which code-and-date pairs are near-certain inside one organisation; and how a record is assigned to an
  organisation on a server that serves many (81 brands on one Epic server, verified, [research 2](https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407); every eClinicalWorks practice on one base),
  which the within-organisation derivation now depends on.
- The amended `jdg:currentlySame`.
- A matcher rule for organisations: `jdg:SameBusinessIdentifier` needs a shared code, which an organisation lacks,
  and M2 takes only the subject's records.
- Whether the NPI registry becomes a reference table kind; the organisation record does not wait on it.

## What would change our mind

Vendors publishing an old-to-new address mapping, or a stable server identity the client can read, would make the
server Same a derivation with no judgment. Servers keeping ids across a vendor switch would let the server Same cover
it. Generators guaranteeing deterministic entry ids in FHIR documents would let those join by name as C-CDA entries do.
