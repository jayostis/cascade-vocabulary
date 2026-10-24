# How everything in a pod is named

Status: draft, 2026-10-22, from the review on #130. Replaces N1's owner, N2's inputs, N6's constant and its "used"
(the rule list's version leaves it, the maker becomes `jdg:CascadeMatcher`), N7's "nothing else" (six kinds of act
are random now), A2's single parent, and M5's and M9's "at the run's time" (an assertion carries no time); built by
#193 then #191, one re-mint. Which revision
is current is `currency.md`; how a moved, switched or re-issued source's records are joined is
`republishing-sources.md`; what a judgment is and borrows is `judgments.md`. The rubric below is the one the four
notes share. Recipe detail (constant, escaping, bit layout, canonical form) lives in the rule terms and
`runtime/naming.feature`.

## Question

A pod holds records from several hospitals, versions of each, the pod's own revisions, stored documents, acts, a
person's judgments and a machine's, findings, tables and views. It has no server of record, is written by more than one
writer, and shows views the person may share. Each thing needs a name two runtimes give alike, that it keeps, that
nobody can forge, and that says nothing a shared view should not.

## Rubric

Every rule in this note, in `currency.md`, in `republishing-sources.md` and in `judgments.md` is one input run through
four tests.

1. **A name is identity by definition, not by inference.** A thing is named by what its source says identifies it, and
   nothing past that: a server's record by that server's address, type and id; an entry by its document and position.
   Two things share a name only where the source itself gave them one definition.
2. **Everything past the definition is a judgment.** That two records are one fact, that two servers are one hospital,
   that a source's patient is this person: each is a belief, filed with its reason and its maker, so that it can be wrong and
   can be retracted without touching a name.
3. **One judgment per fact, where a fact exists.** Where one fact joins thousands of records, a moved server or a
   merged hospital, it is said once and the joins are derived. Where no such fact exists, a vendor switch that
   re-issues every id, judgments are per record, scoped as narrowly as the facts allow.
4. **The machine surfaces what it is less sure of.** Every judgment can be reviewed and overridden by a person, whose
   judgment outranks the machine's. The machine lists for the person the ones it made on weaker grounds, a code and a
   date rather than a shared identifier, or a pick between revisions no source time decided, so review goes where it
   is needed.

## What others do

- **FHIR** names a resource by its server plus a logical id, and says an id is stable only "on the same server" and a
  copy "might or might not keep the same logical id"; business identifiers are "the preferred basis to recognize the
  same content on different systems"; a `fullUrl` is unique within one bundle; `meta.versionId` is an opaque
  server-assigned version id.
- **CDA** gives every entry an `id` of the II datatype, whose root "guarantees the global uniqueness of the instance
  identifier": a promise of uniqueness, not persistence. HL7's C-CDA Companion Guide makes persistence a best practice,
  "C-CDA Content Creators SHOULD maintain act/observation IDs across documents", and the networks make it a SHALL: the
  Carequality and CommonWell joint content guide, "systems SHALL maintain consistent IDs", and the Sequoia Data
  Usability guide, "Organizations SHALL send the same ID for clinical data which has not changed".
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
CDA II datatype (https://hl7.org/cda/stds/core/StructureDefinition-II-definitions.html), C-CDA Companion Guide R4.1
§5.1.4 (HL7 members' copy; read from https://www.cal-med.com/fhir/HL7_CCDA_Companion_Guide.pdf), Joint Document Content
WG Concise Consolidated CDA v2.0 §2.2.2
(https://www.commonwellalliance.org/wp-content/uploads/2024/04/Resources-Improve-C-CDA-Joint-Content-WG-v2.0-FINAL-COPY-20220316.pdf),
Sequoia Data Usability IG v2.0 §3.4.2.1
(https://sequoiaproject.org/wp-content/uploads/2024/12/Data-Usability-Workgroup-Implementation-Guide-V2.0-Final.pdf);
openEHR `OBJECT_VERSION_ID` (https://specifications.openehr.org/releases/BASE/latest/base_types.html#_object_version_id_class)
and `CONTRIBUTION` (https://specifications.openehr.org/releases/RM/latest/common.html#_contribution_class); SPHN data
generation (https://sphn-semantic-framework.readthedocs.io/en/latest/user_guide/data_generation.html); OMOP CDM
(https://ohdsi.github.io/CommonDataModel/); git objects (https://git-scm.com/book/en/v2/Git-Internals-Git-Objects);
trusty URIs (https://trustyuri.net/); Web Annotation (https://www.w3.org/TR/annotation-model/); RFC 6920
(https://www.rfc-editor.org/rfc/rfc6920), RFC 9562 §5.8 and §6.6 (https://www.rfc-editor.org/rfc/rfc9562), RFC 3986
§6 (https://www.rfc-editor.org/rfc/rfc3986#section-6); RDFC-1.0 (https://www.w3.org/TR/rdf-canon/); Clarke et al., incremental multiset
hash functions, ASIACRYPT 2003 (https://doi.org/10.1007/978-3-540-40061-5_12); Bellare and Micciancio, incremental
hashing, EUROCRYPT 1997 (https://cseweb.ucsd.edu/~mihir/papers/inchash.pdf); Wagner, a generalized birthday problem,
CRYPTO 2002 (https://doi.org/10.1007/3-540-45708-9_19); Bitcoin Core's MuHash3072, its unit vectors and its Python
reference
(https://github.com/bitcoin/bitcoin/blob/a773e1e33b349dc819b5a0edc1c7a4839dc73b48/src/crypto/muhash.cpp,
https://github.com/bitcoin/bitcoin/blob/a773e1e33b349dc819b5a0edc1c7a4839dc73b48/src/test/crypto_tests.cpp,
https://github.com/bitcoin/bitcoin/blob/a773e1e33b349dc819b5a0edc1c7a4839dc73b48/test/functional/test_framework/crypto/muhash.py);
Maitin-Shepard et al., elliptic curve multiset hash (https://arxiv.org/abs/1601.06502); Lewi et al., LtHash
(https://eprint.iacr.org/2019/227). Research 1 to 5 on
#130: base-URL churn from archived endpoint lists
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6327416626), the server's self-asserted base
probed across seven vendors (https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328100407),
id-less and generator-minted ids in documents
(https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6328557801), C-CDA entry id stability across
documents (https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6334427968), and record identity
across every input kind (https://github.com/jayostis/cascade-vocabulary/issues/130#issuecomment-6334428443); the
evidence issue keeping the churn and self-URL counts and scripts
(https://github.com/jayostis/cascade-vocabulary/issues/201); and two downloads seven weeks apart from one EHR, in
cascade-cli #121 (https://github.com/the-cascade-protocol/cascade-cli/pull/121).

## Choice

Each row below is the rubric's first test applied to one kind of thing: what its source says identifies it, and so
what is hashed. Whatever failed that test, the server's self-asserted base, a generator's `urn:uuid`, a version id,
appears here only as evidence for a judgment.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| derived name | RFC 9562 §5.8, §6.6 | UUIDv8 over a random v4 namespace, the rule's IRI, then the inputs, escaped and joined; lists carry their count | borrowed; the rule IRI as first input is ours |
| rule | FHIR extensions named by URL | a term in the one unversioned Cascade namespace (#193); a changed recipe is a new IRI; local names are descriptive words in the ontology's own style, one per naming recipe: `RecordFromServer`, `RecordFromDocument`, `RecordFromCcda`, `ContainedRecord`, `Entry`, `Version`, `Revision`, `ViewEntry`, `Snapshot`, `Server`, `Organisation`, `Claim`, `Assertion`, `Retraction`, never a short tag like `fhir-resource` | borrowed |
| record from a server | FHIR server + id; SPHN provider-scoped IRI | hash of the normalised base URL the client used, the type and the id; `rec:sourceUrl` stated in the file | SPHN's scope, hashed so a shared view names no host; diverges from FHIR, which calls the pair not durable, and ignores the server's own `implementation.url` (see `republishing-sources.md`) |
| record from a document | FHIR documents | named by the document and a selector; an id the generator minted is the document's, never the hospital's; a `urn:uuid` fullUrl is never identity across documents | borrowed from FHIR's promise, uniqueness within one bundle only |
| record from C-CDA | CDA `id` roots; Sequoia Data Usability "same ID for unchanged data" | custodian and patient scopes, then the entry's CDA `id` root and extension, so the same statement in two documents from one system is one record; two entries of one document with one `id` and different content fall back to document-and-selector names and a finding says the source broke its own definition | borrowed from the networks' SHALL; diverges from the document row because CDA ids are measured stable where generator UUIDs are not |
| record from an entry | | hash of the session's IRI and the draft's position | ours |
| server, organisation | `prov:Organization`; FHIR `Organization`; CDA custodian | records: a server by the base URL the client used; an organisation by server plus `Organization/{id}` from a server, and from a document by its business identifier, a C-CDA `id` or a FHIR `Organization.identifier` as the paragraph below the table maps and picks it; what they report sits on versions | borrowed from PROV for the class; a versioned record typed as an Agent, which PROV allows |
| version | git blob; RFC 6920; RDFC-1.0 | `ni:` hash of RDFC-1.0 canonical N-Quads of exactly its triples (a sort, since no blank node is allowed), business identifiers nested and sorted | borrowed; diverges from FHIR's and openEHR's per-system version ids |
| source's own version | openEHR `creating_system_id`; FHIR `versionId` | a nested node on the revision, never in a name | diverges: not visible in a name |
| revision | git commit; trusty URIs | self-hashed over its own triples, carrying its act's id, `rec:asOf`, `prov:generatedAtTime`, and the record's heads it saw as `prov:wasRevisionOf` | borrowed; `ni:` form rather than trusty URI syntax; `prov:wasRevisionOf` used for the pod's own observation DAG |
| act | openEHR `CONTRIBUTION`; FHIR `urn:uuid` | six kinds, each a random v4 minted once: an import, an entry session, a connect (what a server reports), a release's migration (renames, retracts what a release declares wrong, rewrites what a release changes in form), a matcher run, a sync; every file an act writes is named by its snapshot, and a file a step that is no act writes (a new pod's files, a reference version's arrival, a person's judgment) is in the set hash but named by no snapshot; every act names the software and version that performed it; nothing else a runtime mints is random (the subject's `urn:uuid` and a person's judgment are minted once by their owners) | the act is the contribution; the kinds are ours |
| sync | git merge commit | an act the receiving writer writes only when a file arrived that this writer lacked, other than a sync act or a snapshot, naming the acts that arrived; the set excludes the files that change in place (the views under `clinical/`, `settings/`, `profile/card.ttl`, `manifest.ttl`), so it only grows; the order-free set hash of the snapshot row is what the snapshot carries, not what every check computes; a sync that brings nothing but another writer's sync acts and snapshots writes nothing | borrowed; written on arrival rather than by a merger, and never for a no-op |
| person's judgment | | keeps the IRI it arrived with, minted once by whoever made it | ours |
| machine judgment | nanopub assertion | the claim named once, by the naming rule `Claim`, then the maker, the matcher's rule, the justification, the member count, the members sorted and used sorted, where the members are the record and the least member of each entry it matched, a star that `same-pairs.rq` derives to its least member, and used is the version of each member and of each table the matcher's rule read, never the rule list's version (N6, M5) | borrowed from nanopubs' claim and assertion split |
| assertion, retraction by a release | | deterministic, with no time and no run: an assertion from the rule list version and the claim, so at most one per version per claim however many runs reach it, and none under a version whose row for the claim's rule carries the `rec:queryHash` of a version the claim is already asserted under, so a new version asserts only the claims of the rules it changed; the run that wrote it is known from its snapshot; a release's retraction from the release, the claim and the rule it declares wrong; two writers on one release write one file with one content (N6 and M9 for the assertion; the retraction is #215's) | ours |
| maker | PROV agents | the Cascade matcher is `jdg:CascadeMatcher`, one `prov:SoftwareAgent`, unversioned, for any runtime that follows `runtime/matcher.feature`; a matcher of another procedure is its own agent term in its own namespace; the runtime that ran is on the act, not the claim (M5) | borrowed; one agent for one procedure is ours |
| retraction | nanopub `npx:retracts` | a `prov:Activity` that `prov:invalidated`; replacement by `dcterms:replaces` | diverges: `npx:retracts` has domain `foaf:Agent`, making the retractor an agent and the retracted a nanopublication, where ours is an activity over any entity |
| document, finding | RFC 6920; Web Annotation | bytes hashed; content hashed | borrowed |
| view entry | | `<view>#` + hash of its least member, `prov:wasDerivedFrom` each judgment; named in the view that gives it members and rebuilt with it; another view in the same folder cites it by a relative reference, as the variant interpretations view cites a variant's entry `<variants.ttl#hex>`; carries every member's current state, with a lead per `currency.md` | ours |
| snapshot | git tree; git commit parents; Bitcoin Core's MuHash3072 | one node per act, in the act's file, a chain as git's commits are: its first parent, the writer's own previous snapshot, kept outside the pod as git keeps HEAD (a browser app beside the pod's name and key), none on a writer's first or when the head it was handed is no snapshot the pod holds; for a sync, each head that arrived as a merged parent, and on a writer's first, every head it holds; the files of the set this act wrote, never a file a step that is no act wrote; and an order-free hash of the set, every file N9 names in a folder the layout gives but the sync row's files that change in place and the act's own file: MuHash3072 exactly as Bitcoin Core computes it, over the path, a 0x00 byte and the SHA-256 of each file's bytes, so a changed byte changes it; the name binds the act's description, as a git commit binds its message outside its tree; two writers hold one set when the set hashes of what each holds agree, and one holds all the other holds when the other's head is an ancestor of its own; never a list of every file | borrowed from git's chain of commits and from Bitcoin Core's UTXO set hash, with its vectors; diverged from git's tree, which with this layout rewrites a leaf folder per act |
| pod identity | Solid WebID; DIDs | the subject's random `urn:uuid`; no name ever includes an address, a WebID or a DID; a judgment that leaves the pod carries it as the author, so a receiver can cite the person and reconcile their shares, and whether the author leaves at all is the share-time choice like every field; keying it hides nothing more, since it is random already, and a per-receiver id is open below | diverges from Solid, which names a pod by its URL |
| scheme | | declared per pod at creation: source URL as IRI, opaque hash (default), or keyed hash; what has no URL (C-CDA, entries, judgments) is hashed under all three; a test key for kits | ours |

An organization version's identifier is W3C ORG's `org:identifier`, a `skos:notation`, whose literal datatype names
the identifier system: `"1234567893"^^<http://hl7.org/fhir/sid/us-npi>`; an identifier with no system is a plain string.
A C-CDA `id` follows HL7's CDA-to-FHIR identifier mapping (https://hl7.org/fhir/us/ccda/en/mappingGuidance.html, "CDA id →
FHIR Identifier"): a root that is a known identifier system becomes its URI, and root and extension give the extension as
the value with that URI as datatype, else `urn:oid:<root>` (`urn:uuid:<root>` for a UUID root); a root alone gives
`urn:oid:<root>` (or `urn:uuid:<root>`) as the value with datatype `urn:ietf:rfc:3986`, and a known system's root alone is
no identifier. A FHIR system `urn:oid:<root>` of a known system is that URI too. The known systems are those of FHIR's
identifier registry (https://hl7.org/fhir/R4/identifier-registry.html) that an organization in a source here carries: the
NPI, `2.16.840.1.113883.4.6`, as `http://hl7.org/fhir/sid/us-npi`. So one NPI names one organization record in either
format. An organization a document names is named by the literal of one identifier its version carries, its datatype IRI
and lexical form, so its name and its version state one identifier byte for byte: of the identifiers that are an NPI or a
system rooted at an OID or a UUID, the NPI, else the least by code point of datatype IRI, then lexical form, whatever
order the document lists them in. A name is `foaf:name`; an address is
`cascade:organizationAddress`, one string per address. A document names its custodian and its author organization by
their records, in `cascade:CustodianRole` and `cascade:AuthorRole` (#212).

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
counts (unverified: the 2024 count was read from a search excerpt; that ids are re-issued is inferred); and the address
a client holds changing while the server stays, 2 to 3% of Epic's listed URLs a year, and 41% of them not listed
verbatim after Epic's Brands rewrite (verified, counted from the archived lists). Hashing the server's self-asserted
base instead lost: it survives a path edit and not a hosting move (verified, probed), MEDITECH never sends it, and
eClinicalWorks reports one base for every practice (both verified, probed), so two resources at two practices could fuse under one name, the one failure no judgment could undo. So the
client's address is hashed, and what the source says about itself is evidence for one judgment per source, in
`republishing-sources.md`. A record is one thing at one source, so a moved source is a new source, and the join is a
judgment because it is one.

**Why identifiers are evidence, not names.** An accession alone would merge a whole panel; sources disagree on
identifier systems; and a name input a source may correct later is a name that changes. So the identifier rides in
the version, sorted, and a judgment says when two records share one plus a code. A document's minted ids are the
document's for the same reason: two of three open converters mint a new id per run, a summary generator can be set to
mask server ids (both verified, in the generators' code), and nothing in a resource says whether a server or a generator assigned its id (research 3).

**Why content names a version, not a counter.** Many servers, version ids that reset or are opaque, and the same
state arriving by several paths (a pull, Apple's copy, a C-CDA). A content hash is the same from any path, which is
where idempotency comes from, and is recomputable by anyone with the file and the rule; the hash and the IRI form are
RFC 6920's, the selection of triples is ours. The source's version id rides in a nested node because the revision is
the pod's commit, not the server's.

**Why the revision is a commit with heads.** Two arrivals of one state are two events, so the act's id is hashed in;
a random name would check nothing, so the revision is self-hashed. Naming the record's heads it saw, as git's parents
do, lets two offline writers both import a correction and merge by union; naming every ancestor would grow without
bound. Which head is current is `currency.md`.

**Why six kinds of act, and a snapshot per act.** Every file an act writes is credited to it, which is what the
audit trail and the snapshot rest on. A connect writes what a server reports, a migration writes a release's
retractions, a run writes claims and assertions; folding them into an import would pretend a connect with no pull, or
a migration by a writer that never imports, happened inside one. So each is an act with a random id, a start, an
agent and a snapshot, and the snapshot exists because per-file integrity says nothing about the set being whole. The
snapshot is a chain, its previous snapshot and this act's additions with an order-free hash of the set, because
a list of every file per act grows with the square of the pod: 70 to 200 GB over ten years against a 1 GB pod, where
git's tree with this layout is 1 to 2 GB and the chain 60 to 115 MB (computed from a stated ten-year pod,
[#206](https://github.com/jayostis/cascade-vocabulary/issues/206)); the set only grows, so a chain loses nothing, and
"in sync" is one comparison of two hashes. A sync is an act because "when did this writer first see that import" is
history nothing else records, and the matcher run the union calls for needs a cause to name; it is written only when
a file arrived that the writer lacked, other than a sync act or a snapshot, because a background transport syncs many
times a day and moves nothing in nearly all of them, because the receiving writer is the one that knows what arrived,
and because an act that fired on every arrival would fire on its own arrival at the other writer. In a set that only
grows, that test says what "the merged set's hash differs" says at the cost of what arrived, and the files that change
in place are outside the set, or every view rebuild would change it. Union needs no merge step of its own: two
writers that imported one record wrote one version file by name, and two that ran one rule on one pair wrote one
claim, so the only things a union leaves are two heads of one record, which the ladder in `currency.md` ranks, and
pairs no matcher saw together, which the run the sync triggers takes, bound to the records the sync brought
(`republishing-sources.md`).

**Why MuHash3072 over each file's path and bytes, and the act outside the set.** The set hash is what a writer
compares with another's and what the kit checks a pod against, so it is a lasting wire format, and the members a
writer hashes are names an import derives from documents anyone can craft. A sum of hashes is broken for such
members: Wagner's generalized birthday attack finds chosen members with any target sum modulo 2^256 in about 2^32
work. MuHash3072 multiplies in a 3072-bit prime field, where finding a collision is a discrete logarithm problem of
about 128-bit strength; it is incremental, a file added being one multiplication; and Bitcoin Core has computed its
UTXO set hash with it since 2021, with unit vectors and a Python reference that this vocabulary's vectors are checked
against, so an implementer needs SHA-256, ChaCha20 and a big integer, all at hand in Python and a browser. A member
holds the file's bytes' SHA-256 as well as its path, because a path names a file and says nothing of what it holds,
and a removed file and a changed one should fail alike. The act's own file holds the snapshot, whose set hash cannot
cover itself, so the hash leaves that file out and the snapshot's name binds the act's description in its place, as a
git commit binds its message beside its tree; the next snapshot's set holds the file whole. Only an act's files are
credited to it: a file a step that is no act wrote, a new pod's, a reference version's, a person's judgment, is in
the set but credited to none, since crediting it to the next act would say that act wrote it.

**Why a claim, an assertion per rule list version, and one matcher agent.** A machine judgment is one claim with an
assertion per rule list version because the same inputs give the same name, so a later version that agrees could
otherwise write nothing, and a run that reaches an asserted claim writes nothing, so a daily run adds no files. A
claim counts while its maker is trusted, its used versions are current, and it has an assertion under a rule list
version whose row for the rule carries the same `rec:queryHash` as the version the app uses. M11 pins a rule's bytes,
so two versions with one hash reach the same claims, and a new version asserts only the claims of the rules it
changed; an assertion per claim per version would be 600k to 1.2M files over ten years, more than the rest of the pod
(computed, #206). A claim's members are the record and the least member of each entry it matched, a star, because
entries are a transitive closure and come out the same, where every earlier copy as a member makes a fact
re-downloaded in each monthly summary a claim of 1, 2 … g members, which `same-pairs.rq` expands to about 58M pairs
over ten years (computed from an assumed 100 persistent entries per summary, #206). The rule list's version is out of
the claim's name because with it in, every version renamed every claim, the duplication the split exists to stop; the
member and table versions stay in, because a claim about old content is a different claim, and a new table version
re-mints only the claims whose joining rows changed in it (M7), since rows are the content: re-minting every
table-reading claim per adopted table version is about 960k claims in ten years (assumed monthly adoption, #206), and
a used table version stays current for a claim while the current version's joining rows are the same. A rule list version that merely tightens a rule retracts nothing: the claims it no
longer reaches have no assertion under it and stop counting by derivation, and its first run files one finding naming
them, which the review page lists as one line with the three answers of `currency.md`'s rollback, a Same over the
finding deriving a person's Same per pair, an acknowledgement, or pairs one by one; a person's Same already filed on a
pair is untouched. A release retracts only what it declares wrong, so a known-bad join is never offered back. The
Cascade matcher is one unversioned agent because the matcher feature promises every runtime that follows it reaches
the same claims, so which runtime ran is forensics, and it sits on the run's act with every other act's performer: a
bug in a rule list version is found by the assertions under it, a bug in a runtime by the acts it performed, a bug in
an app by its own agent and version, and bad data from any of them is hidden by a person's Erroneous over the act.

**Why the rest.** Escaping closes a verified collision, `("a|b")` and `("a","b")` named one thing; a list carries its
count so two lists back to back are unambiguous; the rule IRI makes two rules of equal arity never collide and lets a
v8 name say which rule made it (`ni:` names take none, being content). Base URLs are normalised because `:443` and
none are one server, and userinfo is refused because a credential must never be a name input. The host is an ASCII
reg-name, or a bracketed IPv6 address or IPvFuture with no zone id, and the port is empty (no port) or ASCII digits read as an integer,
leading zeros dropped, above 65535 refused, then the scheme's default dropped, so `:0443` and none are one server too
and a URL two parsers read apart names nothing. A contained resource is scoped by its container's source version
because a renumbered one would otherwise become a revision of another
record. An entry hashes a session the app minted because the subject and a timestamp collide across writers in one
instant. Custodian and patient in a C-CDA name stop two patients' id-less statements from one clinic fusing. A
C-CDA entry is named by its CDA `id` across documents where a FHIR document's entry is not, because the two promises
differ and the measurements differ (research 4 on #130): FHIR says a document's ids are unique within that bundle
only, and converters mint them at random per run; CDA's networks say "organizations SHALL send the same ID for
clinical data which has not changed", HL7's companion guide makes it a SHOULD, and in the only public pairs from one
system every observation, medication and procedure kept its id (verified, counted: Greenway, 77 of 91 statements;
Allscripts, 26 of 26; Synthea a month on, 97%), as did every record with a source id in two downloads seven weeks
apart from one EHR (verified, cascade-cli #121). What failed was the wrappers, a concern act or a vitals organizer
re-minted per export, which the matcher joins like any duplicate, and an id reused for two different entries
(verified, counted: 2 in Synthea; 22 of 344 within one document in #121), which would fuse two facts under one name that no judgment could split; so the collision inside a
document falls back to the document's name with a finding, and the rare reuse across documents is accepted over the
per-document alternative's cost, thousands of records and a claim file per join on every re-download of a stable
sender. A person's judgment keeps its IRI because whoever made it minted it once, so another pod can cite it. A document and a
finding are named by content so the same one from two writers is one file, and Web Annotation wants exactly one IRI
per annotation. A view entry is a fragment of its view because the view is rebuilt from the set, so its entries are
too, and nothing outside the view may cite one. A retraction is an activity because PROV already says how an entity is invalidated. A fragment on a hashed parent (`#source-version`,
`#identifier-n`) is a stated convention because the node is inside the parent's hashed content; RFC 6920's grammar
has no fragment, and we say so. The opaque default hides a hospital from a casual reader of a shared view; the scheme
declaration says in plain words that only a key hides it from a determined one. The address stays out of every name
because a hostname in a name is a commitment nobody can undo. The vocabulary owns the rules because a pod reader has
only the vocabulary; vectors are cross-checked because an implementation that minted its own vectors proves nothing.

## Alternatives that lost

- **FHIR's pair as the visible IRI.** The strongest case: it is what every FHIR client already resolves, and it is
  honest about where a record came from. It names the hospital in every shared view. Kept as a scheme a pod may choose.
- **Business identifiers as name inputs for clinical records.** The strongest case: FHIR says they are the basis for
  sameness across systems, and they survive a server move. They are not unique across kinds, sources disagree on
  systems, and a corrected identifier would rename the record. An organisation is the exception: its NPI or OID is
  the one identifier a document carries for it, so it names the organisation record (`republishing-sources.md`).
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
- **An assertion per run.** The strongest case: a full record of every time the matcher agreed. A file per claim
  per day; the run's act and its snapshot already say which run wrote each assertion, and a run that finds nothing new writes nothing.
- **A migration retracting assertions on every rule change.** The strongest case: explicit, and PROV's own way to
  withdraw. A claim counts only under a version that keeps its rule's query hash, so the un-reached claims stop counting
  with no file written; a retraction is kept for what a release declares wrong, so the review page never offers a
  known-bad join back.
- **The matcher named per rule list version, or per runtime.** The strongest case: the agent would say which rules
  and which code. Per version, the maker changes every release, which is the duplicate problem again; per runtime,
  two correct runtimes would make two claims of one conclusion, which the matcher feature forbids. The version is on
  the assertion and the runtime on the act.
- **Connects and migrations folded into the next import.** The strongest case: two kinds of act, as today. A connect
  with no pull and a migration by a writer that never imports have nowhere to go.
- **Blank-node judgments and software agents.** The strongest case: nothing to mint. Apps link to judgments, and the
  same software on every run needs one name.
- **UUIDv5.** The strongest case: a standard name-based layout. SHA-1, and no room for a stated layout.
- **A hostname or a DID as the pod's identity.** The strongest case: resolvable and familiar. A hostname is a
  commitment nobody can undo, and a DID is what a person signs as, not what a pod is about.
- **C-CDA records named per document, like FHIR documents.** The strongest case: one rule for every document kind,
  and a name that can never fuse two facts, since a reused id becomes a derived join a Different can undo. The
  measured senders keep their ids, the networks require it, and a stable sender re-downloaded would write thousands of
  records and a claim file per join each time; the in-document collision is caught, and the cross-document reuse is
  rare enough to accept.
- **A claim's members as the record and everything it matched.** The strongest case: one file shows every record the
  rule found the record same as, and no derivation is needed to read it. A fact in every monthly summary gives claims
  of 1, 2 … g members, about 1.4M member and used triples, and `same-pairs.rq` expands each to all its pairs, about
  58M `currentlySame` triples in ten years, doubling every two and a half years after (computed from an assumed 100
  persistent entries per summary, #206); a member's new version voids every claim using its old one.
- **A snapshot naming the set of files the act left.** The strongest case: git's tree, one canonical node that says
  exactly what the writer held, compared without a walk. Summed over 5,000 acts it is 1.1 to 2.1 billion entries, 70
  to 200 GB against a 1 GB pod; git's own tree with this layout is 1 to 2 GB, the chain 60 to 115 MB (computed, #206).
- **AdHash, Clarke et al.'s MSet-Add-Hash: the sum modulo 2^256 of each path's SHA-256.** The strongest case: the
  simplest incremental set hash, 256 bits of state, a file added being one addition. Unkeyed, Wagner's generalized
  birthday attack finds paths with any chosen sum in about 2^32 work, and paths are names derived from documents an
  attacker can craft; keying it needs a secret every writer and every checker shares, which a pod has none of.
- **XOR of each path's hash.** The strongest case: simpler still. A file added twice cancels, and any target is reached
  by solving a linear system over 257 chosen members.
- **ECMH, the elliptic curve multiset hash.** The strongest case: 33 bytes of state where MuHash keeps 384, and it was
  proposed for Bitcoin's UTXO set beside MuHash. Looked at and lost: it needs a hash to a curve and point arithmetic, a
  library on each side; Bitcoin Core weighed both and shipped MuHash3072, so no deployment of the same weight
  publishes vectors for it.
- **LtHash, the lattice hash Facebook deploys.** The strongest case: vector addition is the fastest update of all.
  Looked at and lost: its state is 2 KB, its expansion is BLAKE2xb, which neither Python's standard library nor
  WebCrypto has, and its parameters are one deployment's; MuHash3072 needs SHA-256, a 20-line ChaCha20 and a big
  integer.
- **A member of the path alone.** The strongest case: a listing gives every member with no read. A changed file then
  keeps the set hash, and the hash says the set is whole when it is not.
- **An assertion under the rule list version the app uses, and a re-mint of every table-reading claim per table
  version (M7).** The strongest case: each version says for itself what it reaches, and each table version restates
  its claims, so nothing counts on a version that never ran. The first gives 600k to 1.2M assertions in ten years,
  more than the whole pod; the second, 120 adoptions of 8k table-reading claims, about 960k claims (computed and
  assumed, #206); versions with one query hash reach the same claims, and unchanged rows are unchanged content.
- **A sync written when the merged set's hash differs.** The strongest case: one comparison says exactly whether
  anything changed. Computed on every arrival check it sorts and hashes every name, about 24 MB and 0.3 to 1 s on
  Node plus a listing of about 1M files, 175k times in ten years, about two CPU-days, for 1,200 checks that write
  (assumed 48 checks a day, #206); and with views and settings in the set, the set is not grow-only.

## Still open

- Which nested element of a C-CDA entry carries the stable id: the networks' SHALL does not say, and the measured
  pairs show the inner statement stable and its wrapper re-minted.
- Whether a claim whose used versions are no longer current is re-reached by the next run over the new versions as a
  new claim, or whether the finding of what a version no longer reaches should list these too.
- The test by which a record is "from a server" or "from a document": bundle type, input format, Apple's optional
  `sourceURL`.
- The order "least IRI" compares in; the scheme shapes for server and organisation records under the keyed scheme;
  which kits re-author (Priya's C-CDA fixtures need a custodian and a patient id).
- Whether ids survive an Epic path edit on one server: inferred from one capability statement and one token endpoint
  under three path forms, not observed; one patient read under two paths with a registered test client settles it.
- A feature under consideration, not ruled: under the keyed scheme, a shared judgment's author derived from the key
  and the receiver, so the person is one stable id to each receiver and unlinkable across receivers. One field, so
  it works where pseudonymising every name did not; whether it earns its complexity is open, and nothing proves
  authorship without a signature either way.

## What would change our mind

A generator that guaranteed deterministic ids across documents would make trusting them right for that generator. A
C-CDA sender measured re-minting its inner statements' ids per export, or reusing ids across documents at any real
rate, would move C-CDA to per-document names.
Vendor switches rising well above the measured rate, or ids turning out not to survive a same-server URL change, would
make business identifiers a name input after all. Servers giving every record a long random id would make the keyed
scheme unnecessary; cross-pod reconciliation needing shared names would rule it out. A signed or hashed-graph
standard adopted across tools would replace the version and revision forms.
