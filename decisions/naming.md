# How everything in a pod is named

Status: draft, 2026-10-21, from the review on #130. Replaces N2's inputs, N4's single parent, N6's matcher constant
and A3; moves `pav:version` off the revision; makes servers and organisations (`prov:Organization`) kinds of record;
adds to judgments a Before verdict, a Same over servers, organisations and documents with a derivation each, an
assertion activity per matcher run and a release's migration; adds a review question and within-organisation matcher
rules; built by #193 then #191, one re-mint. Every recipe detail (constant, escaping, bit layout,
canonical form) lives in the rule terms and `runtime/naming.feature`, not here.

## Question

A pod holds records from several hospitals, versions of each, the pod's own revisions, stored documents, imports,
entries, a person's judgments and a machine's, findings, tables and views. The pod has no server of record, lives on
more than one device, and shows views the person may share. Each thing needs a name two runtimes give alike, that it
keeps, that nobody can forge, and that says nothing a shared view should not.

## What others do

- **FHIR** names a resource by its server plus a logical id and warns that neither is durable across systems; business
  identifiers are "the preferred basis to recognize the same content on different systems"; a `fullUrl` is unique
  within one bundle; a version is `meta.versionId`, one server's counter.
- **openEHR** names a versioned object `object_id::creating_system_id::version_tree_id`, the system visible in the
  name and branches in the tree; a `CONTRIBUTION` records each commit; a person resolves a merge.
- **SPHN** scopes every instance IRI by its data provider and keeps cross-provider sameness in a separate
  `hasSharedIdentifier`. **OMOP** keeps each source's own value beside the concept it maps to and names nothing across
  sources.
- **git** names blob, tree and commit by the hash of their content; a commit names its parents, one or several, and one
  tree, so one hash covers the whole state; a fork stays open until a person writes the merge.
- **Nanopublications** hash a self-referencing graph with the self-reference blanked (trusty URIs). **Web Annotation**
  gives each annotation exactly one IRI.
- **RFC 6920** gives a hash of bytes an IRI, `ni:///sha-256;…`. **RFC 9562** gives an application its own UUID layout
  (version 8) and recommends a random v4 or v7 as a namespace. **RFC 3986 §6** says which URL differences are not
  differences. **RDFC-1.0** canonicalises a graph so its hash is the same from any serialisation.

Sources: FHIR R4 resource identity (https://hl7.org/fhir/R4/resource.html#id), bundle uniqueness
(https://hl7.org/fhir/R4/bundle.html#bundle-unique), `Identifier` (https://hl7.org/fhir/R4/datatypes.html#Identifier);
openEHR `OBJECT_VERSION_ID` (https://specifications.openehr.org/releases/BASE/latest/base_types.html#_object_version_id_class)
and `CONTRIBUTION` (https://specifications.openehr.org/releases/RM/latest/common.html#_contribution_class); SPHN data
generation (https://sphn-semantic-framework.readthedocs.io/en/latest/user_guide/data_generation.html); OMOP CDM
(https://ohdsi.github.io/CommonDataModel/); git objects (https://git-scm.com/book/en/v2/Git-Internals-Git-Objects);
trusty URIs (https://trustyuri.net/); Web Annotation (https://www.w3.org/TR/annotation-model/); RFC 6920
(https://www.rfc-editor.org/rfc/rfc6920), RFC 9562 §5.8 and §6.6 (https://www.rfc-editor.org/rfc/rfc9562), RFC 3986
§6 (https://www.rfc-editor.org/rfc/rfc3986#section-6); RDFC-1.0 (https://www.w3.org/TR/rdf-canon/). Base URL churn
measured from Epic's and Oracle's published endpoint lists, 2021 to 2026, with the standards' stability clauses quoted
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6327416626); the server's self-asserted base
probed across seven vendors, and across Epic's path edits and hosting moves
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407).

## Choice

Two tests decide every input: two things never share a name, and one thing never changes its name. What the source
says is the same is hashed; what we infer is the same is a judgment, never a name.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| derived name | RFC 9562 §5.8, §6.6 | UUIDv8 over a random v4 namespace, the rule's IRI, then the inputs, escaped and joined | borrowed; the rule IRI as first input is ours |
| rule | FHIR extensions named by URL | a term in an unversioned namespace; a changed recipe is a new IRI | borrowed from FHIR's URL-named rules |
| record from a server | FHIR server + id; SPHN provider-scoped IRI | hash of the normalised base URL the client used, type, id; `rec:sourceUrl` and the server's self-asserted base both stated in the file | SPHN's scope, hashed so a shared view names no host; diverges from FHIR, which calls this pair not durable |
| record from a document | FHIR documents; C-CDA | named by the document and a selector; an id the generator minted is the document's, never the hospital's, and a `urn:uuid` fullUrl is never identity across documents | borrowed from FHIR's own promise, uniqueness within one bundle only |
| server | FHIR `CapabilityStatement` | a record named by the base URL the client used; each connect yields a version of what the server reported (self-asserted base, login endpoint, software) | ours; the self-URL is evidence for a judgment, never a name input |
| organisation | `prov:Organization`; FHIR `Organization`; CDA custodian | a record, `prov:Organization`, named by server plus `Organization/{id}` or by the custodian's OID; name, address and identifiers on its versions; a document names its custodian and author by it | borrowed from PROV; named as any record |
| sameness of sources | git remotes; openEHR `creating_system_id` | a Same whose members are two servers, two organisations or two documents, each with its derivation: servers join every record of one type and id under both; document editions join entries whose content matches within the pair and scope the matcher to the pair; organisations give the matcher a within-organisation scope, where a shared identifier or a shared code and date joins | ours |
| record from C-CDA | CDA `id` roots | custodian and patient scopes, then the class's identifier ladder | ours; no standard names an id-less CDA statement |
| record from an entry | | hash of the session's IRI and the draft's position | ours |
| sameness across sources | FHIR business identifiers; SPHN `hasSharedIdentifier` | a judgment (`jdg:SameBusinessIdentifier`), never a name input | borrowed from SPHN; diverges from FHIR's "preferred basis" |
| version | git blob; RFC 6920; RDFC-1.0 | `ni:` hash of RDFC-1.0 canonical N-Quads of exactly its triples, identifiers nested and sorted | borrowed; diverges from FHIR's and openEHR's per-system counters |
| source's own version | openEHR `creating_system_id`; FHIR `versionId` | a nested node on the revision, never in a name | diverges: hashed or nested away, not visible |
| revision | git commit; trusty URIs | self-hashed over its own triples, carrying the import's id, `rec:asOf`, `prov:generatedAtTime` and every revision it saw | borrowed from both; `ni:` form rather than trusty URI syntax |
| current | git refs and manual merge | derived, never stored: less any revision an Erroneous names or a person's Before places before another candidate, the revisions at the latest source change time (or with none), then greatest `rec:asOf`, then least IRI, which is arbitrary and said so | diverges: the source's clock resolves by default; a person resolves by stating order, not by merging |
| order of states | git merge commit | a person's judgment, verdict Before, two revisions of one record in order; machines never make one; listed for review wherever the source's change time did not decide | ours; the merge commit's job, as a fact rather than a merge |
| import, session, person's judgment | openEHR `CONTRIBUTION`; FHIR `urn:uuid` | random v4, minted once; a person's judgment keeps the IRI it arrived with | the import is the contribution; borrowed |
| machine judgment | nanopub assertion | the claim named once, by rule IRI, justification, member count, members sorted, used sorted; each run that reaches it writes an assertion activity naming the release, the rule-list version and the time | borrowed from nanopubs' claim and assertion split |
| a release's migration | database migrations; git fix-forward | a rule-list version says which rules it changed; on first open under it, the runtime re-runs those rules' judgments and retracts, attributed to the release with the rule change as reason, each one the new rule no longer makes; a person's judgments are never touched; the review page lists what was withdrawn | ours |
| retraction | nanopub `npx:retracts` | a `prov:Activity` that `prov:invalidated`; replacement by `dcterms:replaces` | diverges: npx's domains make a judgment an agent |
| document, finding | RFC 6920; Web Annotation | bytes hashed; content hashed | borrowed |
| view entry | | `<view>#` + hash of its least member, `prov:wasDerivedFrom` each judgment; rebuilt with the view, cited by nothing outside it | ours |
| snapshot | git tree | one node per import or session naming the set of files it left on that device | borrowed; the merged set is open |
| pod identity | Solid WebID; DIDs | the subject's random `urn:uuid`; no name ever includes an address, a WebID or a DID | diverges from Solid, which names a pod by its URL |
| scheme | | declared per pod at creation: source URL as IRI, opaque hash (default), or keyed hash; C-CDA, entries and judgments hashed under all three; a test key for kits | ours |

The rules are the vocabulary's: each a term with `rdfs:seeAlso` to its standard, a `.rq` where SPARQL can state it,
vectors cross-checked against an independent library, a reference implementation, and a self-check shape (#191). One
unversioned namespace holds every term a pod file carries or a name hashes (#193), and it lands before the rules move,
so every name is re-minted once: a version hashes its predicates and a machine judgment its justification IRI, and
either change alone would re-mint them all.

## Why

**Why hash the server away when FHIR says the pair is not durable.** A patient's pod shows views the person shares, and
a URL there names every hospital they have used. SPHN already scopes by provider and carries sameness separately; we
keep that shape and hash the scope. The cost FHIR warns of is real, and measured (the churn research on #130,
2026-10-21): a hospital changes vendor, and so re-issues every id on a new base, at roughly 1 to 4.5% of US hospitals a
year; no naming scheme survives that, and the old and new records are joined by `jdg:SameBusinessIdentifier` or a
person's Same, exactly as a new hospital's would be. A record is one thing at one source, so a moved source is a new
source, and the join is a judgment because it is one. The second kind of change is the one to design for: the URL a
client holds changes while the server and its ids stay the same. Epic's own list moved 2 to 3% of its base URLs a
year to a new address for the same organisation, and its current Brands list rewrote about 40% of them at once with a
path segment; every old and new pair tested reports one server in `CapabilityStatement.implementation.url`. Oracle
Millennium moved none in four years. Hashing the URL the client used makes one resource two records there. Hashing the
server's self-asserted base instead was measured (research 2 on #130) and lost: it survives a path edit and not a
hosting move (19 of 19 old Epic hosts now report the new host as themselves), MEDITECH never sends it, and
eClinicalWorks reports one base for every practice, so two people at two practices could hash to one record, the one
failure no judgment could undo. So the client's URL is hashed, the self-URL is recorded, and one judgment joins the two
servers: a Same whose members are servers, from which every record with one type and id under both is the same by
derivation. One file, every join, retractable. The app can propose it at connect time, before a record is pulled,
from the self-URL, the login endpoint and the publisher's stable endpoint id; made later, it has the same effect,
because it was never baked into a name. Records pulled under the new address are still written, so a name never
depends on a judgment in one pod. A vendor switch re-issues ids, so a server Same joins nothing there; those records
join on their own evidence, a business identifier or a code and date, because that is the only evidence there is.

**Why a source is a record, and why sameness is one judgment per source.** Everything observed from a source is a record
with versions, revisions and a current state: a flu shot, the server it came from, the hospital that holds it. An
organisation is named by the server's id for it or the custodian's OID, which is one of the few identifiers that
survives across documents; its name and address sit on versions, so a merger's rename is history, not a new thing.
Mercy's FHIR `Organization` and Mercy's C-CDA custodian usually share an NPI or OID, so the shared-identifier rule
joins them as a machine judgment. The three re-publisher problems are then one problem at three levels, answered by
one mechanism: name by the source, join by one judgment per source-level fact, and let the matcher work per record
only inside the scope that judgment gives it. An address change is a server Same, and ids survive, so the derivation
joins by id. Two summaries from one hospital are a document Same, and the derivation joins unchanged entries by
content within the pair, which is nearly safe where content matching across the pod is not, and sends changed entries
to the matcher within the pair. A vendor switch is an organisation Same, and ids are gone, so nothing joins by id;
but within one organisation a shared identifier is certain and a shared code and date is nearly so, and those rules
join most of the history with what is left on the review page. A document's minted ids (research 3 on #130: two of
three open converters mint a random id per run; a summary generator masks server ids on purpose) are the document's,
so a record from a document is named per document and joined across documents like any re-published record; nothing
in a resource says whether a server or a generator assigned its id. The floor is a source that carries no identifier
at all, which falls back to labels and a person's judgment, as today.

**Why identifiers are evidence, not names.** An accession alone would merge a whole panel; sources disagree on
identifier systems; and a name input that a source may correct later is a name that changes. So the identifier rides in
the version, sorted, and a judgment says when two records share one plus a code.

**Why content names a version, not a counter.** Many servers, counters that reset, and the same state arriving by
several paths (a pull, Apple's copy, a C-CDA). A content hash is the same from any path, which is where idempotency
comes from, and is recomputable by anyone with the file and the rule. The counter rides in a nested node because the
revision is the pod's commit, not the server's.

**Why the revision is a commit with parents, and why forks resolve by clock.** Two arrivals of one state are two
events, so the import's id is hashed in; a random name would check nothing, so the revision is self-hashed. Naming
every revision it saw, as git's parents do, lets two offline devices both import a correction and merge by union.
git leaves the fork to a person; a pod is a mirror of sources it does not author, so the source's own change time is
the authority by default, and a stale copy can never un-correct or un-retract a record, which arrival order allowed.
The change time ranks states of the source; `rec:asOf` ranks observations of one state, a later look at a source
being better evidence of its current state, and a person's later session being their later edit. The version number
is kept in the nested source version and never ranks: counters reset and are strings. The device's write time ranks
nothing: it was a clock that happens to be right, which is a bias, not a reason, so the last step is the least IRI,
there only so two devices agree, and the note says it is arbitrary. A person outranks the clocks, as Different
outranks Same: a Before states which of two states came first, a fact the clocks were only inferring, and it
composes across three states where a verdict on one would not. Erroneous is for a state that is wrong, not one that
is stale; a stale copy was a true observation and stays in history. Because current is derived and never stored, the
pod cannot record that it guessed, so the review page lists every record whose current state the source's change
time did not decide, with the state shown, the state not shown, and the reason ("observed later", or "no basis"), and
the fix is one Before.

**Why the smaller rules.** Escaping closes a verified collision, `("a|b")` and `("a","b")` named one thing; a list
carries its count so two lists back to back are unambiguous; the rule IRI makes two rules of equal arity never collide
and lets a v8 name say which rule made it. Base URLs are normalised because `:443` and none are one server, and
userinfo is refused because a credential must never be a name input. A contained resource is scoped by its container's
source version because a renumbered one would otherwise become a revision of another record. An entry hashes a
session the app minted because the subject and a timestamp collide across devices in one instant. Custodian and
patient in a C-CDA name stop two patients' id-less statements from one clinic fusing. A machine judgment is one claim
with an assertion per run because the same inputs give the same name, so a second release that agrees could otherwise
write nothing, and a release that stops agreeing would leave the claim counting: silence is not retraction. The
release that changed a rule knows what it changed, so it carries the fix, re-running only that rule's judgments and
retracting what it no longer makes, named deterministically so two devices write one file; the review page is where
a release says what it took back. A retraction is an activity because PROV
already says how an entity is invalidated. A snapshot exists because per-file integrity says nothing about the set
being whole. A fragment on a hashed parent (`#source-version`, `#identifier-n`) is a stated convention because the
node is inside the parent's hashed content and needs no name of its own; RFC 6920's grammar has no fragment, and we
say so. The opaque default hides a hospital from a casual reader of a shared view; the scheme declaration says in plain
words that only a key hides it from a determined one. The address stays out of every name because a hostname in a name
is a commitment nobody can undo: moving host renames everything, and a shared view names the host. The vocabulary owns
the rules because a pod reader has only the vocabulary; vectors are cross-checked because an implementation that minted
its own vectors proves nothing.

## Alternatives that lost

- **FHIR's pair as the visible IRI.** The strongest case: it is what every FHIR client already resolves, and it is
  honest about where a record came from. It names the hospital in every shared view. Kept as a scheme a pod may choose.
- **The server's self-asserted base as the name input.** The strongest case: it survived every Epic path edit
  measured, which is the common churn. It does not survive a hosting move, is absent from MEDITECH, and is one value
  for every eClinicalWorks practice, which would merge two people into one name. As a judgment input it keeps the
  benefit and makes the failure retractable.
- **Pin to the first address the pod saw for a server.** The strongest case: it would survive a hosting move too.
  The name would then depend on one pod's memory, so no other holder could recompute it.
- **A `urn:uuid` fullUrl or a minted id trusted as identity across documents.** The strongest case: a deterministic
  converter repeats it, and a server's id is trusted the same way. Two of three converters mint a new one per run,
  the deterministic one gives one id to identical content in unrelated documents, and FHIR promises uniqueness within
  one bundle only.
- **Organisations as blank nodes with a label.** The strongest case: nothing pointed at one, and labels collide. A
  proposal, a view and a Same now point at one, and the source gives an OID or NPI to name it by.
- **Business identifiers as name inputs.** The strongest case: FHIR says they are the basis for sameness across
  systems, and they survive a server move. They are not unique across kinds, sources disagree on systems, and a
  corrected identifier would rename the record.
- **openEHR's visible system id and version tree.** The strongest case: twenty years of practice, and a reader sees the
  branch. The system id is the hospital, and a shared view would show it; the branch is kept, as parents on the revision.
- **git's open fork, merged by a person.** The strongest case: no clock is trusted and nothing is decided silently. The
  person did not author the sources and cannot judge every pair; the source's change time can, and where it cannot,
  the review page says so and a Before is the person's merge.
- **A device clock as a tiebreak, before the arbitrary step.** The strongest case: it is usually right. Usually right
  with no reason is a hidden guess; the arbitrary step is a visible one, and the review page shows it.
- **Erroneous as the override.** The strongest case: it exists. It means wrong and hides the revision from every view;
  a stale state is not wrong, and an ordering composes where a mark on one revision does not.
- **Current is the last arrival, and A3.** The strongest case: simplest to compute and today's rule. A stale export
  re-imported won, and a counter reset's correction was dropped.
- **A keyed hash as the default.** The strongest case: it is the only scheme that actually hides the source. The Bridge
  must hold the key to mint, losing it orphans every record, and two pods never share a name. Kept as a scheme.
- **No rule tag, or a bare word.** The strongest case: shorter inputs, and today's names survive. No tag needs a written
  invariant that no two rules share a first input's kind; a word is nothing a reader can look up.
- **A namespace hashed from the project URL.** The strongest case: derivable by anyone. It ties uniqueness to owning a
  domain, and RFC 9562 recommends a random one.
- **A versioned rule namespace.** The strongest case: it matches the other ontologies' IRIs. Whatever is hashed into a
  name must be as permanent as the constant.
- **Trusty URIs for revisions.** The strongest case: an existing convention for exactly this. `ni:` is an IETF standard
  with the same recomputation property, and one IRI form serves documents, versions and revisions alike.
- **`npx:retracts` and `npx:supersedes`.** The strongest case: nanopublication vocabulary built for retraction. Their
  domains make a judgment an agent or a nanopublication.
- **A machine judgment named once and owned by the first release.** The strongest case: simplest, and nothing
  duplicates. No record of which later releases agreed, and a migration cannot find what a changed rule made.
- **The release hashed into the judgment's name.** The strongest case: nothing is ever lost. A judgment per release
  for one pair, views that dedupe, and a retraction per copy.
- **Blank-node judgments and software agents.** The strongest case: nothing to mint. Apps link to judgments, and the
  same software on every run needs one name.
- **UUIDv5.** The strongest case: a standard name-based layout. SHA-1, and no room for a stated layout.
- **A hostname or a DID as the pod's identity.** The strongest case: resolvable and familiar. A hostname is a
  commitment nobody can undo, and a DID is what a person signs as, not what a pod is about.

## Still open

- The guard under which the matcher may make a server Same itself. Same self-URL and same login endpoint is the Epic
  path case; eClinicalWorks shows self-URL alone joins every practice. Until written, the judgment is a person's, on
  the app's proposal.
- Whether ids survive an Epic path edit on one server: every sign says yes (one capability statement and one token
  endpoint under three path forms), not yet observed; one patient read under two paths with a registered test client
  settles it.
- The view's latest member across a Same group is chosen by `rec:asOf`, so a re-publisher's stale copy pulled later
  shows over the origin's correction. Lean: the group's rule follows the record's ladder, the source's change time
  first; and a Before may order revisions of any two records a Same joins.
- An arrival with no source time whose version the record already holds: lean, write nothing, or a stale copy with no
  `meta` becomes current on `rec:asOf` alone.
- The guards under which the app proposes a document Same (same custodian, a later date, how much content matches)
  and the within-organisation matcher rules (which pairs of code and date are near-certain inside one organisation).
- Whether the NPI registry becomes a reference table kind, so a pod can show a hospital's name and address from its
  NPI; the organisation record does not wait on it.
- The shape of a rule-list version's change list (which rules changed, whether their judgments are re-evaluated) and
  the opening step that runs the migration (#59, ruled above as to the judgment's identity).
- A server rollback carrying old timestamps reads as stale and is not followed: lean, accept.
- An import that kept nothing writes nothing: lean, keep A11.
- Whether a judgment that leaves the pod carries the owner's `urn:uuid`: lean, yes.
- The snapshot rule's recipe, and what names a merged set after two devices sync.
- The rule IRIs' local names.

## What would change our mind

Sources stamping no change time often enough that currency falls to device clocks would reopen the open-fork
alternative. An exporter that re-mints `urn:uuid` fullUrls per export would end trusting them. Vendor switches rising
well above the measured 1 to 4.5% of hospitals a year, or ids turning out not to survive a same-server URL change,
would make business identifiers a name input after all. Servers giving every
record a long random id would make the keyed scheme unnecessary; cross-pod reconciliation needing shared names would
rule it out. A signed or hashed-graph standard adopted across tools would replace the version and revision forms.
