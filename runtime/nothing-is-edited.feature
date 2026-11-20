Feature: Nothing is edited or deleted

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Ada
  imports Apple Health exports of four allergies (peanut, latex, shellfish, mango) from one hospital, and later
  exports that change them.

  Rule: X1. No file, once written, changes or goes
    decisions/files-held-in-archives.md, rows "a file", "an archive", "clean-up", "a loose folder" and "what reading a pod requires".
    A retraction, a later revision and an entered-in-error status each leave everything they follow in the pod.

    A file is its path and its bytes, wherever a host keeps it: at its own path, or as the entry at that path of an
    archive in the folder pod-layout.ttl gives cascade:holdsFilesInArchivesOfMediaType. An archive is a ZIP in the
    ISO/IEC 21320-1 profile: each entry stored or deflated, its path in UTF-8 with forward slashes, one entry for a
    path; no ZIP64 field, so at most 65,535 entries and under 4 GiB. Two archives of the same files need not be the
    same bytes: the files are the same, the archives are not required to be.
    It holds only files named as N9 names a file, never one in the archives' folder or the requirements' folder (O4), a
    view nor a stored document, and it is no file of the pod: a host may write files it holds into a new archive and then remove the archives, or the
    copies at their own paths, they came from, so long as each file keeps its path and its bytes, and the new archive is
    at its name before anything it holds is removed. A reader takes every file at its own path and every entry of every
    archive at its name. A file held in two places, two archives or an archive and its own path, holds the same bytes in
    both; a reader that finds a path held with other bytes refuses the pod and names the path. A pod whose host keeps
    any file in an archive requires cascade:ReadingFilesHeldInArchives (O4), so a runtime that cannot read archives
    refuses it rather than read only the files at their own paths.

    No example shows where a host keeps a file, because a step's dataset names each file by its path.

    Example: a later revision leaves the earlier revision and version in the files the earlier step wrote
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "new-content" is imported on 2026-01-06 at 10:00
      When the query is:
        """
        SELECT ?step ?version ?at WHERE {
          GRAPH <urn:cascade:steps> { ?step prov:generated ?file }
          { GRAPH ?file { ?revision cascade:revisionOf <urn:uuid:beaefb13-def8-8f7f-882d-eff4a1ee11d9> ; cascade:version ?version ; prov:generatedAtTime ?at } }
          UNION
          { GRAPH ?file { ?version prov:specializationOf <urn:uuid:beaefb13-def8-8f7f-882d-eff4a1ee11d9> } }
        }
        """
      Then it answers:
        | step                            | version                       | at                                   |
        | <urn:cascade:step:first-export> | version 1 of allergy "Peanut" | "2026-01-02T10:00:00Z"^^xsd:dateTime |
        | <urn:cascade:step:first-export> | version 1 of allergy "Peanut" |                                      |
        | <urn:cascade:step:new-content>  | version 2 of allergy "Peanut" | "2026-01-06T10:00:00Z"^^xsd:dateTime |
        | <urn:cascade:step:new-content>  | version 2 of allergy "Peanut" |                                      |
