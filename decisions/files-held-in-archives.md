# Where a host keeps a pod's files

Status: ruled, 2026-11-20, by Jay on [a pod that is fast at any size, cascade-runtime-js#819](https://github.com/the-cascade-protocol/cascade-runtime-js/issues/819#issuecomment-7049607696),
from the design pass in [the storage design](https://github.com/the-cascade-protocol/cascade-runtime-js/issues/819#issuecomment-7049288478).
Amends X1, N9, W1, S1 and the kit's check 5, which until now each said "No note rules this", and settles the
packfiles question `performance.md` left open as the runtime's. Depends on `naming.md` (what names a file) and
`performance.md` (the ten-year pod). Every figure says measured or estimate; laptop means Jay's Windows 11 machine
(i5-8257U, NTFS, Defender on), shared with other work, one sitting.

## Question

A pod is a folder of files, and its RDF files are its truth: a reader builds every view from them, two writers sync by
copying the files one lacks, and each act's snapshot hashes the set of them by path and bytes. Each record, version,
revision, judgment and act is a file of its own. A fresh import of a 16,833-record Synthea record writes 27,223 RDF
files; the ten-year pod of `performance.md` holds about 465,000. On the laptop, writing those 27,223 files takes 28.8 s
of an 85.7 s import (measured), and listing and reading them back takes 3.5 to 7.0 s (measured). The pod has no server
of record, so whatever stores the files cheaper must leave every name, graph name, snapshot and set hash as it is, and a
pod written one way must be read by every runtime and synced with every writer.

## What others do

- **FHIR, C-CDA, openEHR.** Nothing: each specifies resources, documents and compositions, and leaves how a server
  stores them to the server. FHIR Bulk Data exports a server's resources as NDJSON files: "Each file SHALL contain
  resources of only one type, but a server MAY create more than one file for each resource type", so a transfer is a
  few large files rather than one per resource.
- **Solid.** A pod is a tree of resources, each at its own URL; a server may store them however it likes behind that
  tree. The first example pod borrowed this tree as one file per resource on disk.
- **git.** An object is named by the hash of its content and is stored loose, one file each, or in a packfile with an
  index; a reader looks in both, and repacking changes no object's name. git began with loose objects only and added
  packs in its first months. A fetch keeps what it receives as a pack, not as loose objects, when it brings 100
  objects or more: "if the number of received objects equals or exceeds this limit then the received pack will be
  stored as a pack" (`fetch.unpackLimit`, defaulting to `transfer.unpackLimit`, "The default value is 100"). `git gc`
  packs loose objects and merges packs.
- **ZIP and ISO/IEC 21320-1.** ZIP is PKWARE's container: entries one after another and a central directory at the end
  that lists each entry's path and where it starts. ISO/IEC 21320-1 (Document Container File, Core) is written down
  from what EPUB, OOXML and ODF share: entries "may only be stored uncompressed or using the 'deflate' mechanism", and
  "the encryption features defined in APPNOTE.TXT are prohibited" (as the Library of Congress summarises it). It says
  UTF-8 only as a "should" and nothing of ZIP64: paths in UTF-8 only and no ZIP64 are this note's narrowings, not the
  profile's.
- **TriG and N-Quads.** W3C formats that hold many named graphs in one file, a graph's name beside its statements.
- **SQLite.** One file holding a whole database, which SQLite recommends as an application's file format; the
  runtime's SQL steps already keep a cache of the pod in one (`pod.db`, rebuilt from the files).

Sources: git's objects and packfiles (https://git-scm.com/book/en/v2/Git-Internals-Packfiles) and `fetch.unpackLimit`
and `transfer.unpackLimit` (https://git-scm.com/docs/git-config); ISO/IEC 21320-1 as the Library of Congress describes it
(https://www.loc.gov/preservation/digital/formats/fdd/fdd000361.shtml), ZIP
(https://www.loc.gov/preservation/digital/formats/fdd/fdd000354.shtml); the IANA registration of `application/zip`
(https://www.iana.org/assignments/media-types/application/zip); FHIR Bulk Data's export (https://hl7.org/fhir/uv/bulkdata/export.html);
TriG (https://www.w3.org/TR/trig/); SQLite as an application file format (https://www.sqlite.org/appfileformat.html).
The research this note rests on, with the prototype, its result files and every measurement:
[the storage design](https://github.com/the-cascade-protocol/cascade-runtime-js/issues/819#issuecomment-7049288478); the rulings:
[the decisions comment](https://github.com/the-cascade-protocol/cascade-runtime-js/issues/819#issuecomment-7049607696).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| a file | git: an object is the same object loose or packed | a file of the pod is its path and its bytes, wherever a host keeps it: at its own path, or as the entry at that path of an archive. The files stay the pod's truth, and "no file, once written, changes or goes" stays a promise about each file (`runtime/nothing-is-edited.feature`, X1) | borrowed from git |
| an archive | ISO/IEC 21320-1, as EPUB, OOXML and ODF use it | a ZIP in that profile, entries stored or deflated, paths in UTF-8 in byte order, one entry a path, every date 1980-01-01 00:00, no ZIP64, in the folder `runtime/pod-layout.ttl` gives `cascade:holdsFilesInArchivesOfMediaType`. It holds only files of the layout's folders, never a view nor a stored document, and is no file of the pod; a file held twice holds the same bytes in both (X1) | borrowed; diverged from git's own pack format, whose objects are named by their bytes' hash where a pod's file is named by its path |
| an archive's name | git names a pack by a hash | the SHA-256 of the archive's bytes in lowercase hex, adding `.zip`; an archive that does not match its name, or has no end record, is refused and nothing is read from it (`runtime/naming.feature`, N9) | borrowed |
| a step's archive | git's fetch keeps 100 objects or more as one pack (`transfer.unpackLimit`) | a host that keeps files in archives writes a step's new stored documents first at their paths, then every other new file an archive may hold, the act's among them, as one archive, flushed and renamed into place, then the files that change in place (`runtime/write-order.feature`, W1) | borrowed from git's fetch; ours in doing it for every step, a single judgment too |
| a sync | git's fetch | which files a writer lacks is decided by path; the receiver writes what arrived as W1 writes a step, or keeps whole archives it lacks as they are (`runtime/sync.feature`, S1) | borrowed |
| clean-up | `git gc` | a host may write the files of several archives, or loose files, into a new archive and then remove what they came from, each entry's bytes copied unchanged and the new archive in place first (X1) | borrowed from git |
| a loose folder | git reads loose and packed objects alike | a reader takes every file at its own path and every entry of every archive, so a hand-made, example, fixture or older pod stays a pod as it is (X1) | borrowed |
| the kit's check | | a file is where the layout says when its path is, at that path or in an archive (`runtime/the-kit.feature`, Check 5) | ours |
| the snapshot's set | | a file is in the set by its path wherever a host keeps it, and an archive is not in it, so no snapshot and no set hash changes (`ontologies/cascade.ttl`) | ours |

## Why

**One file each was never chosen against an alternative.** (row "a file") The first example pod, on 2026-09-30, was a
folder a Python script wrote into this repository, a Solid-style tree with one Turtle file per thing so that a reviewer
could read each in a pull request. On 2026-10-05 the layout moved into `runtime/pod-layout.ttl`
([#42](https://github.com/the-cascade-protocol/cascade-vocabulary/issues/42)), describing the folders that already existed. X1, N9
and W1 each said "No note rules this": they described what the runtime did. Packfiles were listed as a lesson from git
"not yet taken" on 2026-10-21 ([#198](https://github.com/the-cascade-protocol/cascade-vocabulary/issues/198)), and `performance.md`
left them open as the runtime's on 2026-10-22. No pod of size was measured until 2026-11-17. The cost stayed out of
sight because every pod was small and every measurement ran on Linux, where a small file costs about a tenth of what it
costs on the laptop.

**The cost is the number of files, not what is in them.** (rows "an archive", "a step's archive") Writing the large
pod's 27,224 files as today took 28.8 s on the laptop and 10.0 s in a Linux container on the same laptop; written as
one ZIP of the same files, the stored document beside it, flushed, it took 0.21 s (−99.3%, 137×) and 0.33 s (−96.7%,
30×) (measured, median of 3). Reading them all back went from 3.0 to 6.5 s to 0.07 s, and listing from 0.53 s to
0.02 s for the archive's directory (measured). The Linux container is not CI, and macOS was not measured; the
runtime's step 0 measures both. The saving phase of the laptop's import, 27.3 s of 85.7 s, is estimated to fall to
about 3 s.

**Every name stays, because no name depends on where a file is kept.** (rows "a file", "the snapshot's set") A record
is named from its source's identity, a version by its content, a revision by its own statements, an act by a random
UUID (`naming.md`); a graph is named by its file's path; the set hash is over each file's path and the SHA-256 of its
bytes. None reads where a host keeps the file. Two pods made separately from the same document share 1,151 of their
1,726 record and version paths byte for byte, in the 400 compared (measured). So an archive can be written, merged or
rewritten without changing a name, a graph name, a snapshot, a set hash or a judgment, which is the property git
relies on to repack.

**ZIP, because each entry is today's file.** (row "an archive") The central directory at the end is the index: one file
is one ranged read (0.27 ms, measured), and listing a pod is reading each archive's directory. An archive that was torn
has no end record and is refused. A ZIP opens in Explorer, Finder, 7-Zip and `unzip`, and each entry is the Turtle file
a person reads today. The rules keep the word "file" and stay true as written. The profile is the one three document
formats share, so no ZIP feature a reader might lack appears. Leaving out ZIP64 keeps every reader simple, at a limit
of 65,535 entries and 4 GiB an archive, past which a step writes more than one. A fixed date and path order make two
hosts that pack the same files the same way write the same bytes, so the same archive arriving twice is one file.

**One archive a step, because a step already knows its files.** (row "a step's archive") A step computes the files the
pod lacks before it writes any; that list is the archive. A repeat writes none: the same document again took 0.12 s
and wrote 0 files on the 647-record record, before archives and after (measured). The act's file lands with the
revisions it names, so the case W1 guards, a step stopped partway, shrinks to an archive that is whole or absent. A
step of 3 files took 5 ms loose and 7 ms as one flushed archive (measured), so one write path serves every step. One
flush a step is durability the pod never had: no write was flushed before.

**Stored documents stay at their own paths.** (row "an archive") Each is already one file, often large (38.1 MB for
the large record), and it is the first thing a removal would touch, if one is ever ruled. Whether they are kept
compressed is a later question.

**A loose folder stays a pod.** (row "a loose folder") Fixture and example pods in a repository stay readable in a
pull request, and a pod written before this note opens without conversion; the clean-up packs it when a host chooses.
The cost is two read paths, which git has carried since 2005.

**A host may keep files either way.** (rows "a step's archive", "a sync", "the kit's check") A browser host keeps a step
in one IndexedDB transaction and never had many operating-system files; it keeps doing so. The rules say how a host
that keeps archives writes them and how every reader reads them, and require no host to keep them.

## Alternatives that lost

- **Keep one file each and write faster.** The strongest case: nothing changes but the runtime's write path. Measured
  ceiling on the laptop, without the checks and the rename: 28.8 to 14.0 s (−51%, 2.1×), and the pod still holds
  27,223 files to list, read, back up, sync and remove, about 465,000 at year ten.
- **Loose first, packed at close, as git does every day.** The strongest case: it is what git does. It pays the whole
  loose cost and then packs and removes: 32.2 s against 28.8 s (measured). git itself skips it for a bulk fetch.
- **One TriG or N-Quads file a step.** The strongest case: a W3C format that loads into any SPARQL tool as it is. A
  stored document cannot go in it; the set hash needs each file's bytes, which a graph block does not give back; blank
  node labels are scoped to the document, not the graph; N-Quads repeats the pod's address on every line (+51%); and
  every rule that says "file" would be reworded to say "graph".
- **The database as the truth and the folder as an export.** The strongest case: one file, about as fast (1.9 s for the
  write, measured), and removal is a `DELETE`. It reverses the ruling of the SQL steps that the files are the truth and
  `pod.db` a cache rebuilt from them; a file rewritten in place on every change is copied whole by a backup or a
  file-sync tool, two devices cannot merge by copying files, and "nothing written changes" is no longer something a
  person can see on disk.
- **A container of our own, or git's pack format.** The strongest case: smallest (6.9 MB for the large pod with zstd,
  measured). No tool opens it and it is a format to specify; git's objects are named by their bytes' hash, and a pod's
  files by their paths.
- **tar.** The strongest case: as simple as a container gets. It has no index, so reading one file or listing a pod reads
  the whole archive.
- **"Statements never change", not files.** The strongest case: it is the promise a reader relies on. It is a larger
  change than the gain needs; the promise about each file holds once a file is its path and its bytes.

## Still open

- What removing anything means: nothing can be removed today (X1), the set hash only grows, and a sync would bring a
  removed file back. Archives make no answer harder: removing a file is writing its archive again without it. Not
  ruled here.
- One seal for each archive of an encrypted pod, instead of one for each file: a new encryption format version, and
  Jay's call. Until then an encrypted host seals each file as today and an archive holds the sealed files.
- Stored documents kept compressed, their name still the hash of their bytes uncompressed: Jay's call.
- Whether an act's file names its archive rather than listing every path it wrote, which the archive's directory now
  also lists (5.2 MB for the large import, measured).
- How many archives a pod holds before a clean-up merges them, and whether a merged index is kept beside the pod: set by
  measuring the ten-year pod's open, not guessed.
- A runtime from before this note, opening a pod whose files are in archives, sees a nearly empty folder; it must refuse
  rather than write into it. That is the runtime's to ensure, in the step that adds the reader.

## What would change our mind

A measured open of a ten-year pod in which reading the archives' directories costs more than listing loose files did
would reopen how archives are merged, not whether to keep them. A reader outside the runtime that must walk a pod's
folder, such as a Solid server serving it as it is, would need `unpack` or a second layout. A ruling that removal is
routine, per record, would weigh against putting many records in one archive.
