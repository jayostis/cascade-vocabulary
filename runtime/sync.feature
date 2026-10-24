Feature: Syncs
  What a writer writes when files arrive from another writer of the same pod. Writers follow git: a writer has no id,
  its last snapshot is its own state outside the pod (N14), and a sync's snapshot is a merge.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Dev's pod
  gets a second writer before Dev enters anything; the first writer takes the entry "later", the second the entry
  "pairs", and each receives the other's files.

  Rule: S1. A sync is written only when a file arrived that the writer lacked, other than a sync's act file
    decisions/naming.md, row "sync". A writer receiving another writer's files writes each it lacks, in a folder the
    layout gives by solid:instanceContainer but the views', and then, if any of them is not a sync's act file, a sync: a
    cascade:SyncFromAnotherWriter and a prov:Activity, a new random UUID (N7), with its prov:startedAtTime, in a file of
    the act folder, written last (W1). The files that arrived are the transport's, not the sync's: the step wrote only
    the sync's file.

    Example: a sync that brings an entry writes one file, its act's
      Given a new pod for Dev on 2026-04-01 at 09:00
      And a second writer of the pod
      And Dev enters "later" on 2026-04-04 at 09:00
      When the second writer receives the files of the first writer on 2026-04-05 at 09:00
      Then "sync" wrote 1 file

  Rule: S2. A sync names each act whose file arrived, and the runtime that performed it
    It is prov:wasInformedBy each act whose act file arrived with it, a sync's among them: an act has arrived once its
    file, which holds its snapshot, is present. It says prov:wasAssociatedWith the runtime, as every act does (N7).

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

  Rule: S3. A sync's snapshot is a merge of the heads that arrived
    decisions/naming.md, row "snapshot". Its cascade:firstParentSnapshot is the writer's previous snapshot, and its
    cascade:mergedParentSnapshot values each snapshot that arrived which no snapshot the writer holds names as a parent;
    on a writer's first, it has no first parent and merges every head it holds (N14). Its cascade:setHash is N14's, over
    the set the writer holds once the files that arrived are written, and it names no cascade:fileAddedToSet: the sync
    wrote no file of the set, and the files that arrived are named by the snapshots of the acts that wrote them.

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

  Rule: S4. A sync that brings only syncs writes nothing, so two writers that sync back and forth settle
    A sync's act file is outside the set, so its arrival brings the receiving writer nothing it lacked: no act fires on
    its own arrival at the other writer. The file that arrived is written all the same.

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

  Rule: S5. Two writers hold one set when the set hashes of what each holds agree, whatever order the files arrived in
    decisions/naming.md, rows "snapshot" and "sync". The set hash is order-free, so two writers that each received the
    other's files carry one set hash on those syncs' snapshots, though neither received them in the order the other
    did. One holds all the other holds when the other's head is an ancestor of its own.

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
