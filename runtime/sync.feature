Feature: Syncs
  What a writer writes when files arrive from another writer of the same pod. Writers follow git: a writer has no id,
  its last snapshot is its own state outside the pod (N14), and a sync's snapshot is a merge.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Dev's pod
  gets a second writer before Dev enters anything; the first writer takes the entry "later", the second the entry
  "pairs", and each receives the other's files. Cleo's pod gets a second writer once she has claimed her hospital
  profile; both writers import her first export, the first writer also takes her entry, and the second receives the
  first's files. Ada's pod gets a second writer before anything arrives; both writers import her first export, the
  second receives the first's files, and then imports the export that changes her peanut allergy.

  Rule: S1. A sync is written whenever the writer holds an act, other than a sync, whose snapshot is no ancestor of its last snapshot
    decisions/naming.md, row "sync"; decisions/performance.md, row "sync as union, with the no-hash test".
    A writer receiving another writer's files writes each it lacks, in a folder the
    layout gives by solid:instanceContainer but the views', in W1's order: the stored documents first, then the other
    files of the set, then the act files, each after those holding its snapshot's parents, and its sync last. Whether
    it writes a sync, and which acts the sync names (S2), depends on what the writer holds, never on what this
    receiving wrote: it writes one whenever it holds an act, other than a sync, whose snapshot is no ancestor of its
    last snapshot, any act other than a sync on a writer's first. So a receiving that stops partway and is tried again
    writes the same sync, naming the same acts. The sync is a cascade:SyncFromAnotherWriter and a prov:Activity, a new
    random UUID (N7), with its prov:startedAtTime, in a file of the folder the layout gives
    cascade:SyncFromAnotherWriter. The files that arrived are the transport's, not the sync's: the step wrote only the
    sync's file.

    Example: a sync that brings an entry writes one file, its act's
      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      When the second writer receives the files of the first writer on 2026-04-05 at 09:00
      Then "sync" wrote 1 file

  Rule: S2. A sync names each act it is written for, and the runtime that performed it
    decisions/naming.md, row "sync".
    It is prov:wasInformedBy each act, other than a sync, whose snapshot is no ancestor of the writer's last snapshot:
    an act is held once its file, which holds its snapshot, is. It says prov:wasAssociatedWith the runtime, as every
    act does (N7). The matcher run it causes takes the records all of whose first revisions those acts generated (M1).

    Example: a sync is named by a new random UUID and names the entry session that arrived
      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      When the second writer receives the files of the first writer on 2026-04-05 at 09:00
      When the query is:
        """
        SELECT ?random ?informedBy ?runtime WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:sync> prov:generated ?file }
          GRAPH ?file { ?sync a cascade:SyncFromAnotherWriter, prov:Activity ; prov:startedAtTime [] ;
                          prov:wasInformedBy ?informedBy ; prov:wasAssociatedWith ?runtime }
          BIND (REGEX(STR(?sync), "^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$") AS ?random)
        }
        """
      Then it answers:
        | random | informedBy                                      | runtime     |
        | true   | <urn:uuid:92c5264b-3382-4bf8-aa8a-2458a549e98c> | the runtime |

    Example: after both writers imported one export, the sync's run takes only the entry the other writer made
      Each record of the export has two first revisions, one from each writer's import. The sync names the first
      writer's import and its entry session, but only the entry's records have no first revision from an act the sync
      does not name, so the run compares those alone, each with every record the second writer holds.

      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And a second writer of the pod
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And the steps that follow are the second writer's
      And the export "first-export" is imported on 2026-03-02 at 10:00 (second-import)
      And the steps that follow are the first writer's
      And Cleo enters "entry" on 2026-03-03 at 08:00
      And the second writer receives the files of the first writer on 2026-03-03 at 09:00
      When the matcher runs on the records of that step on 2026-03-03 at 09:05
      Then that step wrote these matcher judgments:
        | justification    | members                                                                                                         |
        | same code        | allergy RxNorm 10180 from sulfa, allergy RxNorm 10180 "Gantanol"                                                |
        | same code        | allergy RxNorm 1191 "Aspirin", allergy RxNorm 1191 "Bayer aspirin"                                              |
        | same code        | allergy RxNorm 1191 "Bayer aspirin", allergy RxNorm 1191 "Ecotrin"                                              |
        | same mapped code | allergy RxNorm 7980 "Penicillin G", allergy SNOMED 373270004                                                    |
        | same code        | allergy RxNorm 7980 "Penicillin G", allergy RxNorm 7980 "Bicillin"                                              |
        | same mapped code | allergy RxNorm 7980 "Bicillin", allergy SNOMED 373270004                                                        |
        | same code        | allergy RxNorm 2670 from codeine-1, allergy RxNorm 2670 from codeine-2, allergy RxNorm 2670 "Codeine phosphate" |

  Rule: S3. A sync's snapshot merges every head the writer holds
    decisions/naming.md, rows "snapshot" and "sync".
    Its cascade:firstParentSnapshot is the writer's last snapshot, and its
    cascade:mergedParentSnapshot values are every head the writer holds once the files that arrived are written, each
    snapshot it holds that no snapshot it holds names as a parent, but the first parent, as git merges; on a writer's
    first, it has no first parent and merges every head it holds (N14). Its cascade:setHash is N14's, over the set the
    writer holds once the files that arrived are written, and it names no cascade:fileAddedToSet: the sync wrote no
    file of the set, and the files that arrived are named by the snapshots of the acts that wrote them.

    Example: each writer's sync names its own last snapshot first and merges the other's head
      The second writer's sync merges the first writer's entry. The first writer's merges the second writer's sync,
      which names the second writer's entry as a parent, so that entry is no head.

      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      And the steps that follow are the second writer's
      And Dev enters "pairs" on 2026-04-04 at 10:00
      And the second writer receives the files of the first writer on 2026-04-05 at 09:00
      When the first writer receives the files of the second writer on 2026-04-05 at 10:00 (sync-back)
      When the query is:
        """
        SELECT ?step ?firstParentStep ?mergedParentStep (COUNT(?added) AS ?filesAdded) WHERE {
          GRAPH <urn:cascade:steps> { ?step prov:generated ?file }
          GRAPH ?file { ?snapshot a cascade:Snapshot ; prov:wasGeneratedBy ?sync . ?sync a cascade:SyncFromAnotherWriter }
          OPTIONAL {
            GRAPH ?file { ?snapshot cascade:firstParentSnapshot ?first }
            GRAPH <urn:cascade:steps> { ?firstParentStep prov:generated ?firstFile }
            GRAPH ?firstFile { ?first a cascade:Snapshot }
          }
          OPTIONAL {
            GRAPH ?file { ?snapshot cascade:mergedParentSnapshot ?merged }
            GRAPH <urn:cascade:steps> { ?mergedParentStep prov:generated ?mergedFile }
            GRAPH ?mergedFile { ?merged a cascade:Snapshot }
          }
          OPTIONAL { GRAPH ?file { ?snapshot cascade:fileAddedToSet ?added } }
        }
        GROUP BY ?step ?firstParentStep ?mergedParentStep
        """
      Then it answers:
        | step                         | firstParentStep            | mergedParentStep           | filesAdded |
        | <urn:cascade:step:sync>      | <urn:cascade:step:pairs>   | <urn:cascade:step:later>   | 0          |
        | <urn:cascade:step:sync-back> | <urn:cascade:step:later>   | <urn:cascade:step:sync>    | 0          |

  Rule: S4. A writer given only syncs writes nothing, and takes the one head it then holds as its last snapshot
    decisions/naming.md, row "sync".
    No sync names a sync, so syncs arriving alone give the writer no act to name: two writers that sync back and forth
    settle. The files that arrived are written all the same. When the writer then holds one head, and it is not the
    writer's last snapshot, that head descends from it and becomes its last snapshot, as git fast-forwards: the
    writer's next act's first parent is the sync that arrived, and no head is left behind.

    Example: the second writer, given the first writer's sync alone, writes nothing
      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      And the steps that follow are the second writer's
      And Dev enters "pairs" on 2026-04-04 at 10:00
      And the second writer receives the files of the first writer on 2026-04-05 at 09:00
      And the first writer receives the files of the second writer on 2026-04-05 at 10:00 (sync-back)
      When the second writer receives the files of the first writer on 2026-04-05 at 11:00 (settle)
      Then "settle" wrote no file

    Example: the second writer's next act follows the first writer's sync
      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      And the steps that follow are the second writer's
      And Dev enters "pairs" on 2026-04-04 at 10:00
      And the second writer receives the files of the first writer on 2026-04-05 at 09:00
      And the first writer receives the files of the second writer on 2026-04-05 at 10:00 (sync-back)
      And the second writer receives the files of the first writer on 2026-04-05 at 11:00 (settle)
      When the matcher runs on the records of "pairs" on 2026-04-05 at 12:00
      When the query is:
        """
        SELECT ?firstParentStep (COUNT(?merged) AS ?mergedParents) WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:matcher> prov:generated ?file }
          GRAPH ?file { ?snapshot a cascade:Snapshot ; cascade:firstParentSnapshot ?parent }
          GRAPH <urn:cascade:steps> { ?firstParentStep prov:generated ?parentFile }
          GRAPH ?parentFile { ?parent a cascade:Snapshot }
          OPTIONAL { GRAPH ?file { ?snapshot cascade:mergedParentSnapshot ?merged } }
        }
        GROUP BY ?firstParentStep
        """
      Then it answers:
        | firstParentStep              | mergedParents |
        | <urn:cascade:step:sync-back> | 0             |

  Rule: S5. Two writers hold one set when the set hashes of what each holds agree, whatever order the files arrived in
    decisions/naming.md, rows "snapshot" and "sync". The set hash is order-free, so two writers that each received the
    other's files carry one set hash on those syncs' snapshots, though neither received them in the order the other
    did.

    Example: the two writers' syncs carry one set hash
      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      And the steps that follow are the second writer's
      And Dev enters "pairs" on 2026-04-04 at 10:00
      And the second writer receives the files of the first writer on 2026-04-05 at 09:00
      And the first writer receives the files of the second writer on 2026-04-05 at 10:00 (sync-back)
      When the second writer receives the files of the first writer on 2026-04-05 at 11:00 (settle)
      When the query is:
        """
        SELECT (COUNT(DISTINCT ?snapshot) AS ?syncs) (COUNT(DISTINCT ?setHash) AS ?setHashes) WHERE {
          GRAPH ?file { ?snapshot a cascade:Snapshot ; prov:wasGeneratedBy ?sync ; cascade:setHash ?setHash .
                        ?sync a cascade:SyncFromAnotherWriter }
        }
        """
      Then it answers:
        | syncs | setHashes |
        | 2     | 1         |

  Rule: S6. An arrival after a sync revises each of the record's heads
    decisions/currency.md, row "heads".
    Two writers that each imported a record hold, once synced, two revisions of it that none revises: its heads. The
    next arrival that changes it writes one revision, prov:wasRevisionOf each head, as a git merge names each parent
    (A5), and one whose version is the record's current one writes none (A4).

    Example: an import after two writers imported one export writes one revision revising both
      Given a new pod for Ada on 2026-01-01 at 09:00
      And a second writer of the pod
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the steps that follow are the second writer's
      And the export "first-export" is imported on 2026-01-02 at 10:00 (second-import)
      And the second writer receives the files of the first writer on 2026-01-03 at 09:00
      When the export "new-content" is imported on 2026-01-06 at 10:00
      When the query is:
        """
        SELECT (COUNT(DISTINCT ?revision) AS ?revisions) (COUNT(DISTINCT ?head) AS ?revised) WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:new-content> prov:generated ?file }
          GRAPH ?file { ?revision a cascade:Revision ; prov:wasRevisionOf ?head }
        }
        """
      Then it answers:
        | revisions | revised |
        | 1         | 2       |
