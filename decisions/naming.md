# How everything in a pod is named

Status: draft, 2026-10-21, from the review on #130. Replaces N2's inputs, N4's single parent, N6's matcher constant
and A3; moves `pav:version` off the revision; built by #191. Every recipe detail (constant, escaping, bit layout,
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
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6327416626).

## Choice

Two tests decide every input: two things never share a name, and one thing never changes its name. What the source
says is the same is hashed; what we infer is the same is a judgment, never a name.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| derived name | RFC 9562 §5.8, §6.6 | UUIDv8 over a random v4 namespace, the rule's IRI, then the inputs, escaped and joined | borrowed; the rule IRI as first input is ours |
| rule | FHIR extensions named by URL | a term in an unversioned namespace; a changed recipe is a new IRI | borrowed from FHIR's URL-named rules |
| record from a server | FHIR server + id; SPHN provider-scoped IRI | hash of normalised base URL, type, id; `rec:sourceUrl` stated in the file | SPHN's scope, hashed so a shared view names no host; diverges from FHIR, which calls this pair not durable |
| record from C-CDA | CDA `id` roots | custodian and patient scopes, then the class's identifier ladder | ours; no standard names an id-less CDA statement |
| record from an entry | | hash of the session's IRI and the draft's position | ours |
| sameness across sources | FHIR business identifiers; SPHN `hasSharedIdentifier` | a judgment (`jdg:SameBusinessIdentifier`), never a name input | borrowed from SPHN; diverges from FHIR's "preferred basis" |
| version | git blob; RFC 6920; RDFC-1.0 | `ni:` hash of RDFC-1.0 canonical N-Quads of exactly its triples, identifiers nested and sorted | borrowed; diverges from FHIR's and openEHR's per-system counters |
| source's own version | openEHR `creating_system_id`; FHIR `versionId` | a nested node on the revision, never in a name | diverges: hashed or nested away, not visible |
| revision | git commit; trusty URIs | self-hashed over its own triples, carrying the import's id, `rec:asOf`, `prov:generatedAtTime` and every revision it saw | borrowed from both; `ni:` form rather than trusty URI syntax |
| current | git refs and manual merge | derived: at the latest source change time (or none), greatest `rec:asOf`, then `prov:generatedAtTime`, then least IRI, less any an Erroneous names | diverges: resolved by the source's clock, never by a person |
| import, session, person's judgment | openEHR `CONTRIBUTION`; FHIR `urn:uuid` | random v4, minted once; a person's judgment keeps the IRI it arrived with | the import is the contribution; borrowed |
| machine judgment | nanopub assertion | hash of rule IRI, justification, member count, members sorted, used sorted; attributed to the runtime release and its run | borrowed in spirit |
| retraction | nanopub `npx:retracts` | a `prov:Activity` that `prov:invalidated`; replacement by `dcterms:replaces` | diverges: npx's domains make a judgment an agent |
| document, finding | RFC 6920; Web Annotation | bytes hashed; content hashed | borrowed |
| view entry | | `<view>#` + hash of its least member, `prov:wasDerivedFrom` each judgment; rebuilt with the view, cited by nothing outside it | ours |
| snapshot | git tree | one node per import or session naming the set of files it left on that device | borrowed; the merged set is open |
| pod identity | Solid WebID; DIDs | the subject's random `urn:uuid`; no name ever includes an address, a WebID or a DID | diverges from Solid, which names a pod by its URL |
| scheme | | declared per pod at creation: source URL as IRI, opaque hash (default), or keyed hash; C-CDA, entries and judgments hashed under all three; a test key for kits | ours |

The rules are the vocabulary's: each a term with `rdfs:seeAlso` to its standard, a `.rq` where SPARQL can state it,
vectors cross-checked against an independent library, a reference implementation, and a self-check shape (#191).

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
Millennium moved none in four years. Hashing the URL the client used would make one resource two records there, so
which base is hashed is still open below.

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
the authority, and a stale copy can never un-correct or un-retract a record, which arrival order allowed. Device clocks
decide only after the source's time and `rec:asOf` have tied.

**Why the smaller rules.** Escaping closes a verified collision, `("a|b")` and `("a","b")` named one thing; a list
carries its count so two lists back to back are unambiguous; the rule IRI makes two rules of equal arity never collide
and lets a v8 name say which rule made it. Base URLs are normalised because `:443` and none are one server, and
userinfo is refused because a credential must never be a name input. A contained resource is scoped by its container's
source version because a renumbered one would otherwise become a revision of another record. An entry hashes a
session the app minted because the subject and a timestamp collide across devices in one instant. Custodian and
patient in a C-CDA name stop two patients' id-less statements from one clinic fusing. A machine judgment is attributed
to a release because the same software on every run must have one name. A retraction is an activity because PROV
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
- **Business identifiers as name inputs.** The strongest case: FHIR says they are the basis for sameness across
  systems, and they survive a server move. They are not unique across kinds, sources disagree on systems, and a
  corrected identifier would rename the record.
- **openEHR's visible system id and version tree.** The strongest case: twenty years of practice, and a reader sees the
  branch. The system id is the hospital, and a shared view would show it; the branch is kept, as parents on the revision.
- **git's open fork, merged by a person.** The strongest case: no clock is trusted and nothing is decided silently. The
  person did not author the sources and cannot judge which hospital state is later; the source's change time can.
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
- **Blank-node judgments and software agents.** The strongest case: nothing to mint. Apps link to judgments, and the
  same software on every run needs one name.
- **UUIDv5.** The strongest case: a standard name-based layout. SHA-1, and no room for a stated layout.
- **A hostname or a DID as the pod's identity.** The strongest case: resolvable and familiar. A hostname is a
  commitment nobody can undo, and a DID is what a person signs as, not what a pod is about.

## Still open

- Which base URL a server record hashes: the one the client pulled from, or the one the server asserts in
  `CapabilityStatement.implementation.url`. Lean: the server's own, normalised, with the client's kept as
  `rec:sourceUrl`, so an alias or path change at one server does not split a record; it needs the research's
  inference that ids survive such a change confirmed by reading one `Patient/{id}` on both bases.
- Whether the pod lists, on the review page, records whose current revision was picked on weak evidence (no source
  change time, or a device-clock tiebreak), so a person can file an Erroneous. Lean: yes, as a derivation, not a filed
  judgment.
- One unversioned namespace (#193) is agreed in direction, not ruled. Versions and machine judgments hash `v1-draft`
  IRIs today, so the re-mint must follow the consolidation, or names change twice.
- An arrival with no source time whose version the record already holds: lean, write nothing, or a stale copy with no
  `meta` becomes current on `rec:asOf` alone.
- A `urn:uuid` `fullUrl` trusted as identity across bundles, beyond FHIR's within-one-bundle promise: lean, trust it as
  a server's id is trusted; a reused one is repaired by an Erroneous, and an exporter that re-mints per export makes
  duplicates the matcher joins.
- A matcher judgment's identity across procedure changes (#59): lean, the claim named once plus an assertion activity
  per run, decided now, because the judgment name already changes once under this note and must not change twice.
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
