Feature: Naming
  How a runtime names what it writes. Most names are hashes of what the thing holds, so an example of a naming rule
  writes the expected names out: a name checked by the code that made it would prove little.

  Rule: N1. A record from a document keeps the name the Bridge gave it
    The rule is the Bridge's: https://github.com/jayostis/cascade-bridge-spec/tree/main/fixtures/naming

    Example: each record an import writes has the name the Bridge gave it
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then these are named:
        | thing               | name                                          |
        | allergy "Peanut"    | urn:uuid:ce5ac62c-8a4a-8ee4-b7ac-c9f3172d9f82 |
        | allergy "Latex"     | urn:uuid:de5509dd-2eb5-86f2-925c-bf35bd4a0fc5 |
        | allergy "Shellfish" | urn:uuid:eae9b463-3109-8ca4-ba91-6d18290855ea |
        | allergy "Mango"     | urn:uuid:172278aa-1e87-8578-b178-b513816ede91 |

  Rule: N2. A record from an entry is named by the record rule from the subject, the entry's start and the draft's position
    The record rule is https://github.com/jayostis/cascade-bridge-spec/blob/main/fixtures/naming/name.rq, and its three
    inputs, in this order, are the subject's IRI, the entry's start time as an xsd:dateTime in UTC, and the draft's
    position N from urn:cascade:output-N. The time is written YYYY-MM-DDThh:mm:ssZ, with any fraction of a second the
    entry gives kept and its trailing zeros dropped. The session's ID is not an input.

    Example: each draft of an entry is a record of its own, named from the subject, the entry's start and its position
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      Then these are named:
        | thing              | name                                          |
        | allergy "Peanut"   | urn:uuid:f30549b0-911c-8277-b028-7b56d28e0316 |
        | condition "Asthma" | urn:uuid:ed7e8009-d8fb-8306-a0ba-e289a353a096 |

  Rule: N3. A version is named from its content
    The rule is the Bridge's: VersioningTest in https://github.com/jayostis/cascade-bridge-spec/blob/main/vocab/bridge.ttl
    and https://github.com/jayostis/cascade-bridge-spec/tree/main/fixtures/versioning. An entry's versions are named by
    the same rule, with a reference to a draft record replaced by that record's name.

    Example: an entry's versions are named from their content, a draft's reference replaced by its record's name
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      Then these are named:
        | thing                           | name                                                      |
        | version 1 of allergy "Peanut"   | ni:///sha-256;Q2zb2hq5EC43OWgfnQ-uPPQDVO6_EFXtdyhjpb_8PnQ |
        | version 1 of condition "Asthma" | ni:///sha-256;eplyjFwBziuuDGwAXYG-OsnSc_l9nZRWlgn28AA-riY |
      And these records have:
        | record             | field         | value            |
        | allergy "Peanut"   | influenced by |                  |
        | condition "Asthma" | influenced by | allergy "Peanut" |

  Rule: N4. A revision is named the same way, from its own triples
    Its placeholder is urn:cascade:this-revision, and its triples are: rdf:type rec:Revision, rec:revisionOf,
    rec:version, prov:generatedAtTime (the import's or the session's start), prov:wasGeneratedBy (the import or the
    session), prov:wasRevisionOf (the record's previous revision, if it has one), and every other statement on the arrival
    except bridge:arrivedAs and prov:wasGeneratedBy.

    No example names a revision: its name depends on a run, through the import's or the session's ID. A9's example pins
    the triples it is named from.

  Rule: N5. A document is named by its bytes
    ni:///sha-256; followed by the unpadded base64url SHA-256 of its bytes.

    Example: each kept document is named by the SHA-256 of its bytes
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then these are named:
        | thing                               | name                                                      |
        | the document of allergy "Peanut"    | ni:///sha-256;K96dQ7NMCx_qaokgjdYAocBi7_dSJVtKQmYSfWR4rRc |
        | the document of allergy "Latex"     | ni:///sha-256;BAt9YpIrH17dd8_pYoWl5kIAmfZI4pkKRTV1u7JSRnk |
        | the document of allergy "Shellfish" | ni:///sha-256;HgLQlJLSGhMq7xC5CYdLQEFVzvepvRrLiCGzeI65KI0 |
        | the document of allergy "Mango"     | ni:///sha-256;BMVJZrtTlT-XS2y6CvRWFW3r9Pi9GmNMlC-jzs1doZs |

  Rule: N6. A matcher judgment is named by the record rule
    Its inputs, in this order: the matcher's IRI, the justification's IRI, the members' names sorted, then the sorted
    names of everything it used.

    Example: each judgment of a matcher run is named from the matcher, its justification, its members and what it used
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And Cleo enters "entry" on 2026-03-03 at 08:00
      When the matcher runs on the records of that entry on 2026-03-03 at 08:01
      Then that step wrote these matcher judgments:
        | justification    | members                                                                                                  | name                                          |
        | same code        | allergy RxNorm 10180 from sulfa, allergy RxNorm 10180 from draft 0                                       | urn:uuid:37e0a66c-c8dc-8a12-a6e3-8b15a912b0c9 |
        | same code        | allergy RxNorm 1191 from draft 1, allergy RxNorm 1191 from draft 3                                       | urn:uuid:e5652955-f87b-8271-93a2-a5cb3caffc5a |
        | same code        | allergy RxNorm 1191 from draft 1, allergy RxNorm 1191 from draft 2, allergy RxNorm 1191 from draft 3     | urn:uuid:62c11127-f5ef-85eb-8063-8a859cd57845 |
        | same mapped code | allergy RxNorm 7980 from draft 4, allergy SNOMED 373270004                                               | urn:uuid:5299e444-b87a-8bcd-8375-476624f6b583 |
        | same code        | allergy RxNorm 7980 from draft 4, allergy RxNorm 7980 from draft 5                                       | urn:uuid:629b672d-233f-8f3c-8515-a707e3301e54 |
        | same mapped code | allergy RxNorm 7980 from draft 5, allergy SNOMED 373270004                                               | urn:uuid:f2f75a46-7805-831d-b5d3-0a897e9ef2a6 |
        | same code        | allergy RxNorm 2670 from codeine-1, allergy RxNorm 2670 from codeine-2, allergy RxNorm 2670 from draft 8 | urn:uuid:8c6b6827-041d-8a8a-b9d8-11c075bf4e16 |

  Rule: N7. An import and an entry session each get a new random UUID
    A urn:uuid:, version 4, new on every run. Nothing else does. The kit's check 4 holds each of a replay's imports and
    sessions to it.

    Example: an import is named by a new random UUID, which no input gives
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then that step's import is named by a new random UUID

    Example: an entry's session, scripted as urn:cascade:this-entry, is named by a new random UUID
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      Then that step's entry session is named by a new random UUID

  Rule: N8. What a runtime gives the Bridge
    - The adapter: <repository>/tree/<commit>/, from the adapter's entry in cascade-runtime.json.
    - The vocabulary: the same form, for the vocabulary repository at the commit the adapter pins
      (bridge:cascadeVocabularyPin).
    - A document: its N5 name, which is the name the Bridge itself gives it.
    - Its facts: the document's IRI followed by #facts.

    A checkout used as it is on disk is named by the commit it is at. Each IRI ends in a slash, so every file's path
    resolves against it.

    No example shows this rule, because what the Bridge is given never reaches the pod. engine/library.md in
    cascade-bridge-spec and the runtime's Bridge interface use it, and their own tests check it.

  Rule: N9. A file's name comes from the name of what it holds
    For a urn:uuid: name, the UUID; for an ni:///sha-256; name, the hash in lowercase hex. An RDF file adds .ttl; a stored
    document adds nothing. The folder and the fan-out are the layout's, pod-layout.ttl.

    Every example shows this rule, because each graph is named by its file's path.

    Example: each file an import writes is named from the name of what it holds
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then the query "queries/files-named-from-what-they-hold.rq" answers:
        | thing                                                     | fileName                                                             |
        | <urn:uuid:ce5ac62c-8a4a-8ee4-b7ac-c9f3172d9f82>           | "ce5ac62c-8a4a-8ee4-b7ac-c9f3172d9f82.ttl"                           |
        | <urn:uuid:de5509dd-2eb5-86f2-925c-bf35bd4a0fc5>           | "de5509dd-2eb5-86f2-925c-bf35bd4a0fc5.ttl"                           |
        | <urn:uuid:eae9b463-3109-8ca4-ba91-6d18290855ea>           | "eae9b463-3109-8ca4-ba91-6d18290855ea.ttl"                           |
        | <urn:uuid:172278aa-1e87-8578-b178-b513816ede91>           | "172278aa-1e87-8578-b178-b513816ede91.ttl"                           |
        | <ni:///sha-256;Rx15Nd4sUNwYcdZW94THU_g2iVOlOmZ0kGyYl74dDAk> | "471d7935de2c50dc1871d656f784c753f8368953a53a6674906c9897be1d0c09.ttl" |
        | <ni:///sha-256;PBXZez-Aw-W0iOMLH8K8rkj7eI7ouZ8FgJMGRQpolEM> | "3c15d97b3f80c3e5b488e30b1fc2bcae48fb788ee8b99f05809306450a689443.ttl" |
        | <ni:///sha-256;GvG1PpZ655CyegCrKsAGYRpvN7UOHUFBDy4Au7IaRdc> | "1af1b53e967ae790b27a00ab2ac006611a6f37b50e1d41410f2e00bbb21a45d7.ttl" |
        | <ni:///sha-256;o4VM6lH4p3bOmm768biggeF_LnP5xAEVKFFU5QXV7N0> | "a3854cea51f8a776ce9a6efaf1b8a081e17f2e73f9c40115285154e505d5ecdd.ttl" |
        | <ni:///sha-256;K96dQ7NMCx_qaokgjdYAocBi7_dSJVtKQmYSfWR4rRc> | "2bde9d43b34c0b1fea6a89208dd600a1c062eff752255b4a4266127d6478ad17.ttl" |
        | <ni:///sha-256;BAt9YpIrH17dd8_pYoWl5kIAmfZI4pkKRTV1u7JSRnk> | "040b7d62922b1f5edd77cfe96285a5e6420099f648e2990a453575bbb2524679.ttl" |
        | <ni:///sha-256;HgLQlJLSGhMq7xC5CYdLQEFVzvepvRrLiCGzeI65KI0> | "1e02d09492d21a132aef10b909874b404155cef7a9bd1acb8821b3788eb9288d.ttl" |
        | <ni:///sha-256;BMVJZrtTlT-XS2y6CvRWFW3r9Pi9GmNMlC-jzs1doZs> | "04c54966bb53953f974b6cba0af456156debf4f8bd1a634c942fa3cecd5da19b.ttl" |
        |                                                           | "2bde9d43b34c0b1fea6a89208dd600a1c062eff752255b4a4266127d6478ad17"     |
        |                                                           | "040b7d62922b1f5edd77cfe96285a5e6420099f648e2990a453575bbb2524679"     |
        |                                                           | "1e02d09492d21a132aef10b909874b404155cef7a9bd1acb8821b3788eb9288d"     |
        |                                                           | "04c54966bb53953f974b6cba0af456156debf4f8bd1a634c942fa3cecd5da19b"     |

  Rule: N10. A person's judgment keeps the IRI its input gives it
    A judgment a person makes arrives with its name: whoever made it minted that once, as the subject's ID was minted. A
    runtime files it under that IRI and gives it no other; it is neither a new random UUID nor named by a rule. So a
    judgment can name another person's judgment, and an answer can name it, on every run.

    Example: a person's About and its retraction are each filed under the IRI they arrived with, in their own step's file
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-r" on 2026-03-04 at 07:00
      When Cleo files the judgment "retract-about-r" on 2026-03-04 at 12:00
      Then the query "queries/a-retraction-deletes-nothing.rq" answers:
        | step                                   | judgment                                        | verdict   |
        | <urn:cascade:step:about-r>             | <urn:uuid:b8d3f1a7-2c69-4e5b-9f14-3a7e6d2c8b91> | jdg:About |
        | <urn:cascade:step:retract-about-r>     | <urn:uuid:f2b6d9a4-7e3c-4815-b9d7-5a8e2c6f1d43> |           |
