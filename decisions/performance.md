# What a pod costs as it grows

Status: ruled, 2026-10-22, from the read on [#206](https://github.com/jayostis/cascade-vocabulary/issues/206). Amends
`naming.md`, `currency.md`, `republishing-sources.md`, `judgments.md`, `variant-identity.md` and
`variant-classifications-table.md` with the nine rulings listed under #204's Performance section; rules nothing of its
own, and collects the argument the rulings carry. Sizes are marked computed (from the notes' rules and the stated pod)
or assumed (resting on one of #206's assumptions A1 to A8).

## Question

A pod lives ten years: three hospitals, 50,000 records, 200,000 revisions, 5,000 acts, 40 rule list versions, two
FHIR servers pulled daily, a background transport checking for arrivals 48 times a day. It runs on a Node server, and a
browser demos it from the same files. Nothing is a server of record, so every writer derives what it shows from the
set of files it holds. What grows with what: which costs track the pod's content, which track its acts, and which
would track the square of either?

## What others do

- **git** names each object by its content, so an unchanged file is stored once. A commit names its parents and one
  tree, and a tree names every entry of its folder, so a commit that changes one file rewrites the trees on its path.
  Packfiles store objects as deltas against similar ones. The index is a flat list of every tracked path with its stat
  data, so `git status` finds what changed without hashing what did not.
- **CRDTs** converge by union, every answer a function of the set; delta-state CRDTs ship only what a replica added
  since the last exchange, not the whole state.
- **openEHR** versions each composition under a versioned object, and a `CONTRIBUTION` lists only the versions one
  commit changed. AQL queries the latest version unless a query asks for every version (`all_versions`).
- **FHIR** keeps a resource's past in `_history`, and `_since` asks a server or a Bulk Data export for only what
  changed after an instant, so a client's cost follows change, not the size of the record.
- **Oxigraph**, the store this repository's tests and `cascade-bridge-rs` run on, keeps quads under several index orders on RocksDB on a server;
  its JavaScript build holds the store in memory (not re-checked here). #206 assumes about 0.5 to 1 GB for a 5M-triple
  store in WASM.

Sources: git objects and packfiles (https://git-scm.com/book/en/v2/Git-Internals-Git-Objects,
https://git-scm.com/book/en/v2/Git-Internals-Packfiles), git's index format
(https://git-scm.com/docs/index-format); Shapiro et al., CRDTs (https://hal.inria.fr/inria-00555588), Almeida et al.,
delta-state CRDTs (https://arxiv.org/abs/1603.01529); openEHR change control
(https://specifications.openehr.org/releases/RM/latest/common.html#_change_control_package) and AQL
(https://specifications.openehr.org/releases/QUERY/latest/AQL.html); FHIR R4 history
(https://hl7.org/fhir/R4/http.html#history) and Bulk Data (https://hl7.org/fhir/uv/bulkdata/); Oxigraph
(https://github.com/oxigraph/oxigraph). The read this note rests on, with its assumptions, per-ruling table and
fixes: [#206](https://github.com/jayostis/cascade-vocabulary/issues/206); the rulings:
[#204](https://github.com/jayostis/cascade-vocabulary/issues/204).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| content names and the held-state rule | git's content-named objects | a version is named by its content and an arrival the pod already holds writes nothing (`naming.md`, `currency.md`): an unchanged daily pull costs a hash and a lookup per resource, about 73M hashes in ten years, 0.5 to 2 CPU-hours, and writes 0 files (assumed, computed) (`runtime/arrivals.feature`, A1, A3 and A4) | borrowed |
| snapshot chain | git commit parents; delta-state CRDTs | each snapshot is the previous one's hash plus the act's additions, with an order-free hash of the set (`naming.md`): 60 to 115 MB in ten years (computed) (`runtime/naming.feature`, N14) | borrowed from git's chain; diverged from git's tree, 1 to 2 GB with this layout (assumed) |
| sync as union, with the no-hash test | CRDT union; git's index | a sync is a union of files, written only when the writer holds an act, other than a sync, whose snapshot is no ancestor of its last snapshot; files that change in place are outside the set (`naming.md`): a check costs a walk of the snapshots the writer holds, kept in memory, never a read of every file (`runtime/sync.feature`, S1) | borrowed from CRDTs; the test is ours |
| current per act, incrementally | openEHR `CONTRIBUTION`; FHIR `_since` | an act rebuilds only the records it wrote revisions for and those its judgments reach by derivation, equal to the full rebuild; a migration, a trusted-makers change and a rule list version change rebuild everything (`currency.md`; `runtime/currency.feature`, C8): the work is what the act touched and its groups; on Oxigraph JS 0.5.11 at 10k records a step's rebuild takes 0.8 to 1.8 s against 9 to 11 s whole, the writing of the views and labels about half of it (measured, on a machine shared with other work) | ours |
| the ladder as a maximum | CRDTs | current is a maximum over one record's revisions, about four, less its Befores and Erroneous, with no walk of history (`currency.md`; computed) (`runtime/currency.feature`, C2) | borrowed in spirit from CRDTs |
| claims named once, asserted per query hash | nanopub assertions | a claim counts under any rule list version whose row for its rule carries the same `rec:queryHash`, so a new version asserts only the claims of the rules it changed; only claims whose joining rows changed are re-minted (M7; `naming.md`, `judgments.md`, `variant-identity.md`): assertions track rule changes, not versions times claims | ours |
| the star | `prov:hadMember` | a claim's members are the record and the least member of each entry it matched; `same-pairs.rq` derives a star and entries are unchanged (`naming.md`, `judgments.md`): linear in members, where every earlier copy was 58M derived pairs (computed from A5) (`runtime/matcher.feature`, M5) | ours |
| entries by union-find | disjoint-set union (Tarjan) | a runtime may compute `queries/derivations/entries.rq`'s rows another way, such as a union-find over the `cascade:currentlySame` pairs, which `owl:SymmetricProperty` makes exact, so long as they equal the query's, which stays the oracle: on Oxigraph JS a 1,000-member entry takes 5.4 s by the query's closure and 0.04 s by union-find (measured, [#246](https://github.com/jayostis/cascade-vocabulary/issues/246)) | borrowed |
| runs bound to arrivals, scoped within an organisation | FHIR `_since` | a run binds `?record` to the records the import, entry or sync brought, and within-organisation rules stay within one (`republishing-sources.md`): about 100k comparisons a run against 1 to 5M rows unbound (assumed) (`runtime/matcher.feature`, M1 and M4) | ours |
| derivations of a source-level Same | FHIR `Linkage`, computed | a server Same's joins are a hash join on type and id over the records under both, kept with the derived state and redone when the judgment is filed or retracted, never per read (`republishing-sources.md`): on Oxigraph JS 0.5.11, 10,000 records under each of two servers judged one give about 10k pairs in 0.7 to 0.9 s, 1.0 to 2.5 s when every document names a custodian, and a pod with no server Same pays 2 to 5 ms (measured, on a machine shared with other work); until the runtime keeps them across steps ([cascade-runtime-js#518](https://github.com/jayostis/cascade-runtime-js/issues/518)), every derive recomputes them | ours |
| page-read tables, current versions only | openEHR AQL's latest version | tables are keyed row lookups, and R13 counts over current versions only, so an old version's rows may be dropped (`variant-identity.md`, `variant-classifications-table.md`): one version held, where every one was 72 GB of ClinVar (computed) (`runtime/matcher.feature`, M17) | borrowed from AQL's default |
| findings bounded | | one rollback finding per import that goes back, an acknowledged one still standing; no second clock finding while one stands on the new act's first-parent ancestry; one un-reached finding per rule list version, 40 in ten years (`currency.md`, `naming.md`; computed) (`runtime/arrivals.feature`, A18 and A19; `runtime/matcher.feature`, M18) | ours |
| the review page bounded | | a pick between two pulls of one source where one's snapshot is an ancestor of the other's is ordered by ancestry and not listed; only picks ancestry does not order are (`currency.md`): against about 8,000 lines by year ten (assumed) (`runtime/currency.feature`, C5) | ours |

## Why

**Storage follows change, not polling.** (row "content names and the held-state rule") Content names and the held-state rule mean a daily pull that finds nothing
new writes nothing, so the pod is about 443k files and 1 GB at year ten (assumed, A2) however often it is pulled; the
cost of a pull is CPU, about two hours over ten years.

**History is a chain, never a list per act.** (row "snapshot chain") Anything that names the whole set on every act is quadratic: 1.1 to 2.1
billion entries over 5,000 acts. A chain of additions sums to the set itself, 60 to 115 MB, and the order-free hash
keeps "in sync" one comparison. The pod only grows, so the chain loses nothing a list held.

**Work follows what arrived.** (rows "sync as union, with the no-hash test", "runs bound to arrivals, scoped within an organisation", "current per act, incrementally", "the ladder as a maximum") A sync check, a matcher run and a view rebuild each cost what the act brought and the
groups it touches: a sync check needs no hash of the set because in a grow-only set "a file arrived I lacked" says the
same; a run compares the arrived records with their code groups, since every older pair was compared when its later
record arrived; a rebuild touches the records whose current state could have changed, because the ladder is per
record and an entry a closure. The wholesale cases are named and rare: a rule list version's first run (40), a vendor
switch, an organisation Same, and the three rebuild triggers.

**Judgments grow with facts, not with versions or copies.** (rows "claims named once, asserted per query hash", "the star") A claim per conclusion, asserted again only when its
rule's bytes change, keeps assertions near the claim count rather than 600k to 1.2M; re-minting only claims whose
rows changed keeps M7 to what a table version changed rather than 8k claims an adoption; and a star keeps a fact seen in 120 summaries at 120 members
rather than 120³/3 derived pairs.

**Tables are today's.** (row "page-read tables, current versions only") A page and R13 ask what a table says now, so only current versions are read and kept, and a
browser holds one ClinVar version rather than a decade of them.

**What a person reads is bounded by events.** (rows "findings bounded", "the review page bounded") A finding is one per thing that happened, a restore or a skewed writer,
not one per act it touches; the review page lists only what the pod truly guessed, and what ancestry orders is not
a guess.

**Where it runs.** (row "derivations of a source-level Same") A browser can demo views read from materialised files and keyed table lookups. Full matcher runs,
a rule list version's first run and the derivations of source-level Sames belong on the Node server, since the whole
store is 0.5 to 1 GB in WASM (assumed).

## Alternatives that lost

Each is the wording a note had before 2026-10-22; the note named keeps it in full.

- **A claim's members as the record and everything it matched** (`naming.md`). The strongest case: one file shows the
  whole join. Cubic: about 58M `currentlySame` triples in ten years (computed from A5).
- **A snapshot naming every file the act left** (`naming.md`). The strongest case: git's tree, one canonical node per
  state. 70 to 200 GB over ten years against a 1 GB pod (computed).
- **A claim counting under the rule list version the app uses, and M7 re-minting every table-reading claim**
  (`naming.md`, `judgments.md`, `variant-identity.md`). The strongest case: each version says for itself what it
  reaches. 600k to 1.2M assertions (computed) and about 960k claims (assumed).
- **Matcher runs with `?record` unbound, and M1's triggers left open** (`republishing-sources.md`). The strongest
  case: a run needs no list of arrivals and misses nothing. 1 to 5M rows and 80M same-result comparisons per run
  (assumed).
- **A view rebuilt whole with every act** (`currency.md`). The strongest case: correct by construction. 10 to 60 s
  per act on Node, 14 to 80 hours in ten years, and no fit in a browser (assumed).
- **A sync written when the merged set's hash differs** (`naming.md`). The strongest case: one exact comparison. About
  two CPU-days over 175k checks, 1,200 of which write (assumed), and a set that is not grow-only while views are in it.
- **R13 counting over every held table version** (`variant-identity.md`, `variant-classifications-table.md`). The
  strongest case: an expression ever on two rows stays left alone. 72 GB of ClinVar in ten years (computed).
- **Every pick no source change time decided on the review page** (`currency.md`). The strongest case: every guess
  shown. About 8,000 lines by year ten from one source with no change time (assumed).
- **A rollback finding per earlier act contradicted, and a clock finding per act** (`currency.md`). The strongest
  case: each finding one contradiction. About 30 findings per 30-day restore and up to 365 a year per skewed writer
  (computed), and a daily refile once acknowledged.

## Still open

- A ten-year pod measured on the reference runtime: every size here is computed from the rules or assumed, none
  observed. A generated pod at #206's sizes, run through a year of acts on Node and its views opened in a browser,
  settles them.
- Incremental rebuild's correctness: that rebuilding the records an act reached equals the full rebuild is argued
  (the ladder is per record, entries are a closure), not proved; a property test over random act sequences, comparing
  the two, is the lean.
- Packfiles: whether a pod's files are stored packed or deltified, as git does, is the runtime's
  (jayostis/cascade-runtime-js#209).
- What the browser runs: which acts a browser may perform on its own, and whether a demo is read-only, is unruled.

## What would change our mind

A measured pod that grows faster than #206's assumptions (more than about 20k resources read a day, more than 150
entries a summary, table versions adopted weekly) would reopen the sizes, not the shape. A rebuild found to differ
from the full one on any act sequence would end incremental rebuild until the derivation is fixed. A browser store
that holds a 5M-triple pod comfortably would move matcher runs into the browser.
