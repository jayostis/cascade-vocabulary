# How everything in a pod is named

Status: decided 2026-10-21 (#130), not yet built (#191, #193). Rules: N1 to N12, A1 to A15 where they name, M-rules
where they read a name. Review: two independent designs, a red team on each, one arbiter, every citation checked; the
record is on #130.

## Question

A pod holds records from hospitals, versions of each, the pod's own revisions, stored documents, imports, entries, a
person's judgments and a machine's, findings, tables and views. Each needs a name that two runtimes give the same thing,
that one thing keeps, that nobody can forge, and that says nothing a shared view should not say.

## What others do

- **FHIR** names a resource by its server plus a logical id, and says a `fullUrl` is unique within a bundle; identifiers
  are "the preferred basis to recognize the same content on different systems"; a version is `meta.versionId`, a
  server's counter.
- **openEHR** names a versioned object by `object_id::creating_system_id::version_tree_id`, one string holding what
  Cascade splits into record, source and revision; a contribution groups the versions one act committed.
- **git** names a blob, a tree and a commit by the SHA of their content; a commit names its parents, one or several,
  and its one tree, so one hash covers the whole state.
- **RFC 6920** gives a content hash an IRI, `ni:///sha-256;…`, that any holder of the bytes recomputes with no other
  knowledge. **RFC 9562** gives an application its own UUID layout (version 8) and recommends a random v4 as a
  namespace. **RDFC-1.0** canonicalises a graph so its hash is the same from any serialisation.
- **SPHN** and **OMOP** keep source-assigned identifiers and say nothing about naming across sources.
- **Nanopublications** name an assertion by its hash (trusty URIs); **Web Annotation** gives each annotation exactly one
  IRI.

Sources: FHIR R4 resource identity (https://hl7.org/fhir/R4/resource.html#id), bundle uniqueness
(https://hl7.org/fhir/R4/bundle.html#bundle-unique), `Identifier` (https://hl7.org/fhir/R4/datatypes.html#Identifier);
openEHR `OBJECT_VERSION_ID` (https://specifications.openehr.org/releases/BASE/latest/base_types.html#_object_version_id_class)
and `CONTRIBUTION` (https://specifications.openehr.org/releases/RM/latest/common.html#_contribution_class); git objects
(https://git-scm.com/book/en/v2/Git-Internals-Git-Objects); RFC 6920 (https://www.rfc-editor.org/rfc/rfc6920), RFC 9562
§5.8 and §6.6 (https://www.rfc-editor.org/rfc/rfc9562), RFC 3986 §6 (https://www.rfc-editor.org/rfc/rfc3986#section-6);
RDFC-1.0 (https://www.w3.org/TR/rdf-canon/); Web Annotation (https://www.w3.org/TR/annotation-model/).

## Choice

**Two tests decide every input:** two things never share a name, and one thing never changes its name. What the source
says is the same is hashed; what we infer is the same is a judgment, never a name.

- **A derived name is a UUIDv8:** SHA-256 over the namespace UUID `90c60849-c5ef-4ca6-bfb8-8662bd07d2b5`, then the rule's
  IRI, then the rule's inputs in order, joined with `|` after `%` becomes `%25` and `|` becomes `%7C`; the first 128
  bits with the version and variant bits set. Lists carry their count. The constant is a random v4 minted once
  (cascade-bridge-spec b406c3a) and never changes.
- **The first input is the rule's IRI,** in an unversioned namespace. A rule is immutable: a changed recipe is a new rule
  with a new IRI, and the old IRI keeps naming what it named.
- **A record from a server** hashes the base URL (normalised per RFC 3986; userinfo, query and fragment refused), the
  resource type and the logical id. A `urn:uuid:` `fullUrl` is trusted as an id. A contained resource is scoped by its
  container's source version. A record with no server hashes the document and a selector. **A C-CDA record** hashes
  the custodian and the patient as well, and id-less twins are told apart by their members' fingerprint, then ordinal.
  **A record from an entry** hashes the session's IRI and the draft's position. The record states its `rec:sourceUrl`
  in its own file, so any holder recomputes the name.
- **A version is its content:** canonical sorted N-Triples of exactly its triples, `prov:specializationOf` the record
  and `rec:patient` included, business identifiers nested and sorted, hashed to `ni:///sha-256;…`. No rule IRI: the
  content is the name, and RFC 6920 holders recompute it knowing nothing of Cascade. A document is its bytes, the same
  way. A finding is its content.
- **A revision is the pod's commit:** self-hashed over its own triples with `urn:cascade:this-revision` as placeholder,
  carrying the import's random id, so two arrivals are two revisions. It names every revision of the record it saw when
  written (`prov:wasRevisionOf`, one or several, as git's parents), never only "the one before". It carries two
  clocks: `rec:asOf`, when the source said it was so, and `prov:generatedAtTime`, when the pod wrote it. The source's
  own version sits in a nested `rec:SourceVersion` node, never on the revision.
- **Current is derived, not arrival order:** among a record's revisions carrying the source's latest change time, the
  greatest by (`rec:asOf`, `prov:generatedAtTime`), least IRI as the last tiebreak. An arrival whose content is the
  current version writes nothing; a held (content, source version, time) that would not become current writes nothing.
- **An import, a session and a person's judgment** are random v4 `urn:uuid`s minted once; the pod files a person's
  judgment under the IRI it arrived with. **A machine judgment** hashes the rule IRI, the justification, the member
  count, the members sorted and what it used sorted, and is attributed to the runtime's release and its run. A
  retraction is a `prov:Activity` that `prov:invalidated` the judgment; a replacement says `dcterms:replaces`.
- **A view entry** is `<view>#` plus the hex SHA-256 of its least member. Only PROV qualification nodes, organisation
  agents and the Bridge's transient arrival are blank. A fragment on a hashed parent is a stated convention.
- **A snapshot** per import and session: one node naming the root of the pod's files after it, over the sorted (path,
  name) pairs, so one hash says the set is whole.
- **No name ever includes the pod's address, a WebID or a DID.** The subject is the pod's random `urn:uuid`, the owner
  named on a person's judgments; the address is a mount point and is written in no file.
- **A pod declares its record-naming scheme** at creation, fixed for its life: the normalised source URL as the IRI,
  the opaque hash above (the default, the only one the kits cover at first), or the same hash over a pod key. A switch
  is a new pod re-importing the stored documents.
- **The vocabulary owns the rules.** Each is a term with its IRI, `rdfs:comment`, ordered inputs and `rdfs:seeAlso` to
  the standard; beside it a plain `.rq` where SPARQL can state it, vectors every implementation reproduces, cross-checked
  against an independent library, a reference implementation under `tests/`, and a shape that recomputes a record's
  name from its file. The version rule has no `.rq` and no shape: canonicalising a graph is not SPARQL.

## Why

A name is recomputed by whoever holds the file, so every input is in the file or in the standard. The rule's IRI in
the hash means two rules of equal arity never collide and a name says which rule made it; a bare word said neither.
Escaping closes a verified collision: `("a|b")` and `("a","b")` named one thing. Content names make the same version
from any path, which is where idempotency comes from, and make a sync a union of files: every file is immutable and
either content-named or randomly minted, and every answer is a function of the set, never of write order. Currency
from the source's clocks stops a stale copy un-correcting or un-retracting a record, which arrival order allowed, and a
revision naming every revision it saw lets two offline devices both import a correction and merge. Custodian and
patient in a C-CDA name stop two patients' id-less statements from one clinic fusing into one record. The address out
of every name keeps a pod movable and a shared view from naming its host; the opaque hash hides a hospital from a
casual reader of a shared view, and the scheme declaration says plainly that only a key hides it from a determined one.

## Alternatives that lost

- **The namespace as a hash of the project URL.** Ties uniqueness to owning a domain and invites re-derivation when it
  moves; RFC 9562 recommends a random one.
- **No tag, or a word.** No tag needs a written invariant that no two rules share a first input's kind; a word is
  arbitrary and nothing looks it up. The IRI is a term.
- **The source URL as every record's IRI.** It names the hospital in every shared view. Kept as a scheme a pod may
  choose.
- **A keyed hash as the default.** The Bridge must hold the key to mint; losing it orphans every record; two pods never
  share a name. Kept as a scheme a pod may choose.
- **Current = the last arrival, and A3 (a seen source version suppresses content).** A stale export re-imported won;
  a counter reset's correction was dropped.
- **One `prov:wasRevisionOf` line.** Two offline imports fork, and the union was refused.
- **UUIDv5.** SHA-1, and no room for a stated layout.
- **A versioned rule namespace.** Whatever is hashed into a name must be as permanent as the constant.
- **`npx:retracts` and `npx:supersedes`.** Their domains make a judgment an agent or a nanopublication.
- **Blank-node judgments and software agents.** The same software on every run must have one name.
- **A hostname or DID as the pod's identity.** An irreversible commitment; the prototype rejected it and so do we.

## Still open

The rule IRIs' local names. A matcher judgment's identity across procedure changes (#59; lean: the claim named once
plus an assertion activity per run). A server rollback carrying old timestamps reads as stale (lean: accept). An import
that kept nothing is not recorded (lean: keep A11). Whether a judgment that leaves the pod carries the owner's
`urn:uuid` (lean: yes). The snapshot rule's exact recipe.

## What would change our mind

A standard content-addressing scheme for RDF graphs adopted across tools would replace the version rule's own canonical
form. Servers giving every record a long random id would make the keyed scheme unnecessary. Cross-pod reconciliation
that needs shared record names would rule out the keyed scheme.
