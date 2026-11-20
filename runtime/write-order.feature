Feature: Write order

  Rule: W1. Content-addressed files are written first, the revision files after them, and the act's file last
    decisions/files-held-in-archives.md, rows "a step's archive" and "what reading a pod requires", rule its second and third paragraphs; no note rules the rest.
    A step that stops partway then leaves nothing that passes for finished: the act's file holds its snapshot (N14), so
    no snapshot names a set the step did not finish writing. The views, the type index and the manifest may be stale
    after a crash, and are rebuilt: the manifest is written last of them, and a build is read back only where each file
    it wrote still holds the bytes it wrote (C8). A matcher run writes its judgments before the reference descriptions it writes, and
    an open writes the versions it adopts oldest first: an open that stops partway leaves the pod naming a version on
    the line no later than the adopted one, and the next open adopts from there, M9 skipping the judgments written and
    writing the descriptions still lacking.

    A host that keeps files in archives (X1) writes a step's new stored documents first, each at its own path, then
    every other new file of the step that an archive may hold, its act's file among them, as one archive, and the files
    that change in place after it; a step whose files would pass an archive's limits writes more than one, the act's
    file in the last, written last. An archive is written under another name, its bytes flushed to storage, and then
    renamed to its name (N9), so an archive at its name is whole and its files are in the pod together or not at all. A
    file in the archives' folder not named as N9 names an archive is a write that stopped, and is no part of the pod.

    A requirement's file (O4) is in the pod before any file that needs its requirement: a host writes it first, if the
    pod lacks it, under another name, its bytes flushed to storage, then renamed to its name, and only then writes what
    needs it. So a host that keeps files in archives writes the file of cascade:ReadingFilesHeldInArchives before the
    first archive it writes into a pod, whether in a step, a receive (S1) or a clean-up (X1), and a pod that holds an
    archive holds that file. It is never removed, even by a clean-up that leaves the pod no archive: a concurrent
    writer may have just written an archive that relies on it.

    No example can show this rule, because an example only sees finished steps. Each runtime tests it itself.
