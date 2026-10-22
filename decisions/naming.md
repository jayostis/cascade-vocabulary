# How everything in a pod is named

Status: draft, 2026-10-21, from the review on #130. Replaces N1's owner, N2's inputs, N6's constant, N7's "nothing
else" (five kinds of act are random now) and A2's single parent; built by #193 then #191, one re-mint. Which revision
is current is `currency.md`; how a moved, switched or re-issued source's records are joined is
`republishing-sources.md`; what a judgment is and borrows is `judgments.md`. The rubric below is the one the four
notes share. Recipe detail (constant, escaping, bit layout, canonical form) lives in the rule terms and
`runtime/naming.feature`.

## Question

A pod holds records from several hospitals, versions of each, the pod's own revisions, stored documents, acts, a
person's judgments and a machine's, findings, tables and views. It has no server of record, lives on more than one
device, and shows views the person may share. Each thing needs a name two runtimes give alike, that it keeps, that
nobody can forge, and that says nothing a shared view should not.

## Rubric

Every rule in this note, in `currency.md`, in `republishing-sources.md` and in `judgments.md` is one input run through
four tests.

1. **A name is identity by definition, not by inference.** A thing is named by what its source says identifies it, and
   nothing past that: a server's record by that server's address, type and id; an entry by its document and position.
   Two things share a name only where the source itself gave them one definition.
2. **Everything past the definition is a judgment.** That two records are one fact, that two servers are one hospital,
   that two documents are editions: each is a belief, filed with its reason and its maker, so that it can be wrong and
   can be retracted without touching a name.
3. **One judgment per fact.** Where one fact joins thousands of records, a moved server or a merged hospital, it is
   said once and the joins are derived; never a judgment per record.
4. **A machine's judgment is reviewable in proportion to its confidence.** A join from a shared business identifier
   goes through; a join from a code and a date, or a pick between revisions no source time decided, is listed for a
   person, whose own judgment outranks the machine's.

## What others do

- **FHIR** names a resource by its server plus a logical id, and says an id is stable only "on the same server" and a
  copy "might or might not keep the same logical id"; business identifiers are "the preferred basis to recognize the
  same content on different systems"; a `fullUrl` is unique within one bundle; `meta.versionId` is an opaque
  server-assigned version id.
- **openEHR** names a versioned object `object_id::creating_system_id::version_tree_id`, the system visible in the
  name; a `CONTRIBUTION` records each commit.
- **SPHN** scopes every instance IRI by its data provider and keeps cross-provider sameness in a separate
  `hasSharedIdentifier`. **OMOP** keeps each source's value beside the concept it maps to and names nothing across
  sources.
- **git** names blob, tree and commit by the hash of their content; a commit names its parent heads, one or several,
  and one tree, so one hash covers the whole state.
- **Nanopublications** hash a self-referencing graph with the self-reference blanked (trusty URIs). **Web Annotation**
  gives each annotation exactly one IRI.
- **RFC 6920** gives a hash of bytes an IRI, `ni:///sha-256;…`. **RFC 9562** gives an application its own UUID layout
  (version 8) and recommends a random v4 or v7 as a namespace. **RFC 3986 §6** says which URL differences are not
  differences. **RDFC-1.0** canonicalises a graph so its hash is the same from any serialisation.

Sources: FHIR R4 resource identity and business identifiers (https://hl7.org/fhir/R4/resource.html#id,
https://hl7.org/fhir/R4/resource.html#identifiers), bundle uniqueness (https://hl7.org/fhir/R4/bundle.html#bundle-unique);
openEHR `OBJECT_VERSION_ID` (https://specifications.openehr.org/releases/BASE/latest/base_types.html#_object_version_id_class)
and `CONTRIBUTION` (https://specifications.openehr.org/releases/RM/latest/common.html#_contribution_class); SPHN data
generation (https://sphn-semantic-framework.readthedocs.io/en/latest/user_guide/data_generation.html); OMOP CDM
(https://ohdsi.github.io/CommonDataModel/); git objects (https://git-scm.com/book/en/v2/Git-Internals-Git-Objects);
trusty URIs (https://trustyuri.net/); Web Annotation (https://www.w3.org/TR/annotation-model/); RFC 6920
(https://www.rfc-editor.org/rfc/rfc6920), RFC 9562 §5.8 and §6.6 (https://www.rfc-editor.org/rfc/rfc9562), RFC 3986
§6 (https://www.rfc-editor.org/rfc/rfc3986#section-6); RDFC-1.0 (https://www.w3.org/TR/rdf-canon/). The three research
comments on #130: base-URL churn from archived endpoint lists, the server's self-asserted base probed across seven
vendors, and id-less and generator-minted ids in documents
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6327416626,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407,
https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328557801).

## Choice

Each row below is the rubric's first test applied to one kind of thing: what its source says identifies it, and so
what is hashed. Whatever failed that test, the server's self-asserted base, a generator's `urn:uuid`, a version id,
appears here only as evidence for a judgment.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| derived name | RFC 9562 §5.8, §6.6 | UUIDv8 over a random v4 namespace, the rule's IRI, then the inputs, escaped and joined; lists carry their count | borrowed; the rule IRI as first input is ours |
| rule | FHIR extensions named by URL | a term in an unversioned namespace; a changed recipe is a new IRI | borrowed |
| record from a server | FHIR server + id; SPHN provider-scoped IRI | hash of the normalised base URL the client used, the type and the id; `rec:sourceUrl` stated in the file | SPHN's scope, hashed so a shared view names no host; diverges from FHIR, which calls the pair not durable, and ignores the server's own `implementation.url` (see `republishing-sources.md`) |
| record from a document | FHIR documents | named by the document and a selector; an id the generator minted is the document's, never the hospital's; a `urn:uuid` fullUrl is never identity across documents | borrowed from FHIR's promise, uniqueness within one bundle only |
| record from C-CDA | CDA `id` roots | custodian and patient scopes, then the class's identifier ladder | ours; open against the document row below |
| record from an entry | | hash of the session's IRI and the draft's position | ours |
| server, organisation | `prov:Organization`; FHIR `Organization`; CDA custodian | records: a server by the base URL the client used; an organisation by server plus `Organization/{id}`, or by the custodian's `id` root and extension; what they report sits on versions | borrowed from PROV for the class; a versioned record typed as an Agent, which PROV allows |
| version | git blob; RFC 6920; RDFC-1.0 | `ni:` hash of RDFC-1.0 canonical N-Quads of exactly its triples (a sort, since no blank node is allowed), business identifiers nested and sorted | borrowed; diverges from FHIR's and openEHR's per-system version ids |
| source's own version | openEHR `creating_system_id`; FHIR `versionId` | a nested node on the revision, never in a name | diverges: not visible in a name |
| revision | git commit; trusty URIs | self-hashed over its own triples, carrying its act's id, `rec:asOf`, `prov:generatedAtTime`, and the record's heads it saw as `prov:wasRevisionOf` | borrowed; `ni:` form rather than trusty URI syntax; `prov:wasRevisionOf` used for the pod's own observation DAG |
| act | openEHR `CONTRIBUTION`; FHIR `urn:uuid` | five kinds, each a random v4 minted once: an import, an entry session, a connect (what a server reports), a release's migration, a matcher run; every file is generated by one; nothing else is random | the act is the contribution; the kinds are ours |
| person's judgment | | keeps the IRI it arrived with, minted once by whoever made it | ours |
| machine judgment | nanopub assertion | the claim named once, by rule IRI, justification, member count, members sorted, used sorted; each run that reaches it writes an assertion; what "used" holds is open | borrowed from nanopubs' claim and assertion split |
| retraction | nanopub `npx:retracts` | a `prov:Activity` that `prov:invalidated`; replacement by `dcterms:replaces` | diverges: npx's domains make a judgment an agent |
| document, finding | RFC 6920; Web Annotation | bytes hashed; content hashed | borrowed |
| view entry | | `<view>#` + hash of its least member, `prov:wasDerivedFrom` each judgment; rebuilt with the view, cited by nothing outside it | ours |
| snapshot | git tree | one node per act naming the set of files it left on that device | borrowed; the merged set is open |
| pod identity | Solid WebID; DIDs | the subject's random `urn:uuid`; no name ever includes an address, a WebID or a DID | diverges from Solid, which names a pod by its URL |
| scheme | | declared per pod at creation: source URL as IRI, opaque hash (default), or keyed hash; what has no URL (C-CDA, entries, judgments) is hashed under all three; a test key for kits | ours |

The rules are the vocabulary's: each a term with `rdfs:seeAlso` to its standard, a `.rq` where SPARQL can state it,
vectors cross-checked against an independent library, a reference implementation, and a self-check shape (#191). One
unversioned namespace holds every term a pod file carries or a name hashes (#193), and it lands before the rules move,
so every name is re-minted once: a version hashes its predicates and a machine judgment its justification IRI, and
either change alone would re-mint them all.

## Why

**Why hash the server away when FHIR says the pair is not durable.** A patient's pod shows views the person shares,
and a URL there names every hospital they have used. SPHN already scopes by provider and carries sameness separately;
we keep that shape and hash the scope. The cost FHIR warns of is real and was measured (research 1 and 2 on #130): a
vendor switch, which re-issues ids on a new base, at roughly 1 to 4.5% of US hospitals a year by KLAS's purchase
counts; and the address a client holds changing while the server stays, 2 to 3% of Epic's listed URLs a year, and 41%
of them not listed verbatim after Epic's Brands rewrite. Hashing the server's self-asserted base instead lost: it
survives a path edit and not a hosting move, MEDITECH never sends it, and eClinicalWorks reports one base for every
practice, so two resources at two practices could fuse under one name, the one failure no judgment could undo. So the
client's address is hashed, and what the source says about itself is evidence for one judgment per source, in
`republishing-sources.md`. A record is one thing at one source, so a moved source is a new source, and the join is a
judgment because it is one.

**Why identifiers are evidence, not names.** An accession alone would merge a whole panel; sources disagree on
identifier systems; and a name input a source may correct later is a name that changes. So the identifier rides in
the version, sorted, and a judgment says when two records share one plus a code. A document's minted ids are the
document's for the same reason: two of three open converters mint a new id per run, a summary generator can be set to
mask server ids, and nothing in a resource says whether a server or a generator assigned its id (research 3).

**Why content names a version, not a counter.** Many servers, version ids that reset or are opaque, and the same
state arriving by several paths (a pull, Apple's copy, a C-CDA). A content hash is the same from any path, which is
where idempotency comes from, and is recomputable by anyone with the file and the rule; the hash and the IRI form are
RFC 6920's, the selection of triples is ours. The source's version id rides in a nested node because the revision is
the pod's commit, not the server's.

**Why the revision is a commit with heads.** Two arrivals of one state are two events, so the act's id is hashed in;
a random name would check nothing, so the revision is self-hashed. Naming the record's heads it saw, as git's parents
do, lets two offline devices both import a correction and merge by union; naming every ancestor would grow without
bound. Which head is current is `currency.md`.

**Why five kinds of act, and a snapshot per act.** Every file in a pod is generated by an act, which is what the
audit trail and the snapshot rest on. A connect writes what a server reports, a migration writes a release's
retractions, a run writes claims and assertions; folding them into an import would pretend a connect with no pull, or
a migration on a device that never imports, happened inside one. So each is an act with a random id, a start, an
agent and a snapshot, and the snapshot exists because per-file integrity says nothing about the set being whole.

**Why the rest.** Escaping closes a verified collision, `("a|b")` and `("a","b")` named one thing; a list carries its
count so two lists back to back are unambiguous; the rule IRI makes two rules of equal arity never collide and lets a
v8 name say which rule made it (`ni:` names take none, being content). Base URLs are normalised because `:443` and
none are one server, and userinfo is refused because a credential must never be a name input. A contained resource is
scoped by its container's source version because a renumbered one would otherwise become a revision of another
record. An entry hashes a session the app minted because the subject and a timestamp collide across devices in one
instant. Custodian and patient in a C-CDA name stop two patients' id-less statements from one clinic fusing. A
person's judgment keeps its IRI because whoever made it minted it once, so another pod can cite it. A document and a
finding are named by content so the same one from two devices is one file, and Web Annotation wants exactly one IRI
per annotation. A view entry is a fragment of its view because the view is rebuilt from the set, so its entries are
too, and nothing outside the view may cite one. A machine judgment is one claim with an assertion per run because the
same inputs give the same name, so a second release that agrees could otherwise write nothing. A retraction is an
activity because PROV already says how an entity is invalidated. A fragment on a hashed parent (`#source-version`,
`#identifier-n`) is a stated convention because the node is inside the parent's hashed content; RFC 6920's grammar
has no fragment, and we say so. The opaque default hides a hospital from a casual reader of a shared view; the scheme
declaration says in plain words that only a key hides it from a determined one. The address stays out of every name
because a hostname in a name is a commitment nobody can undo. The vocabulary owns the rules because a pod reader has
only the vocabulary; vectors are cross-checked because an implementation that minted its own vectors proves nothing.

## Alternatives that lost

- **FHIR's pair as the visible IRI.** The strongest case: it is what every FHIR client already resolves, and it is
  honest about where a record came from. It names the hospital in every shared view. Kept as a scheme a pod may choose.
- **Business identifiers as name inputs.** The strongest case: FHIR says they are the basis for sameness across
  systems, and they survive a server move. They are not unique across kinds, sources disagree on systems, and a
  corrected identifier would rename the record.
- **A `urn:uuid` fullUrl or a minted id trusted across documents.** The strongest case: a deterministic converter
  repeats it, and a server's id is trusted the same way. Two of three converters mint a new one per run, the
  deterministic one gives one id to identical content in unrelated documents, and FHIR promises uniqueness within one
  bundle only.
- **openEHR's visible system id.** The strongest case: twenty years of practice, and a reader sees the system. The
  system id is the hospital, and a shared view would show it.
- **A keyed hash as the default.** The strongest case: it is the only scheme that actually hides the source. The Bridge
  must hold the key to mint, losing it orphans every record, and two pods never share a name. Kept as a scheme.
- **No rule tag, or a bare word.** The strongest case: shorter inputs, and today's names survive. No tag needs a written
  invariant that no two rules share a first input's kind; a word is nothing a reader can look up.
- **A namespace hashed from the project URL.** The strongest case: derivable by anyone. It ties uniqueness to owning a
  domain, and RFC 9562 recommends a random one.
- **A versioned rule namespace.** The strongest case: it matches the other ontologies' IRIs. Whatever is hashed into a
  name must be as permanent as the constant.
- **Every ancestor on a revision.** The strongest case: the whole history is in one file. It grows without bound, and
  git's parents are heads.
- **Trusty URIs for revisions.** The strongest case: an existing convention for exactly this. `ni:` is an IETF standard
  with the same recomputation property, and one IRI form serves documents, versions and revisions alike.
- **`npx:retracts` and `npx:supersedes`.** The strongest case: nanopublication vocabulary built for retraction. Their
  domains make a judgment an agent or a nanopublication.
- **A machine judgment named once and owned by the first release.** The strongest case: simplest, and nothing
  duplicates. No record of which later releases agreed, and a migration cannot find what a changed rule made.
- **The release hashed into the judgment's name.** The strongest case: nothing is ever lost. A judgment per release
  for one pair, views that dedupe, and a retraction per copy.
- **Connects and migrations folded into the next import.** The strongest case: two kinds of act, as today. A connect
  with no pull and a migration on a device that never imports have nowhere to go.
- **Blank-node judgments and software agents.** The strongest case: nothing to mint. Apps link to judgments, and the
  same software on every run needs one name.
- **UUIDv5.** The strongest case: a standard name-based layout. SHA-1, and no room for a stated layout.
- **A hostname or a DID as the pod's identity.** The strongest case: resolvable and familiar. A hostname is a
  commitment nobody can undo, and a DID is what a person signs as, not what a pod is about.

## Still open

- The C-CDA ladder names records across documents by CDA entry ids, which C-CDA on FHIR maps to business identifiers;
  nothing measured their stability across editions. Either C-CDA records are named per document too, or the note says
  why a CDA `id` is trusted where a generator's is not.
- What a machine claim's "used" holds: today it includes the rule-list version and each member's version, so every
  rule-list change renames every claim; lean, the rule-list version moves to the assertion, and a claim whose used
  versions are no longer current stops counting or is retracted.
- Whether a migration retracts the claim or a release's assertion; lean, the assertion, scoped to the release, so a
  later release that reverts a rule, or an older release on another device, is not silenced forever.
- Naming rows for an assertion and a migration's retraction: deterministic from the release, the claim and the rule
  change, with no time in the name.
- The test by which a record is "from a server" or "from a document": bundle type, input format, Apple's optional
  `sourceURL`.
- The order "least IRI" compares in; the scheme shapes for server and organisation records under the keyed scheme;
  which kits re-author (Priya's C-CDA fixtures need a custodian and a patient id).
- Whether ids survive an Epic path edit on one server: inferred from one capability statement and one token endpoint
  under three path forms, not observed; one patient read under two paths with a registered test client settles it.
- The rule IRIs' local names.

## What would change our mind

A generator that guaranteed deterministic ids across documents would make trusting them right for that generator.
Vendor switches rising well above the measured rate, or ids turning out not to survive a same-server URL change, would
make business identifiers a name input after all. Servers giving every record a long random id would make the keyed
scheme unnecessary; cross-pod reconciliation needing shared names would rule it out. A signed or hashed-graph
standard adopted across tools would replace the version and revision forms.
