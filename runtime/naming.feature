Feature: Naming
  How a runtime names what it writes. Most names are hashes of what the thing holds, so an example of a naming rule
  writes the expected names out: a name checked by the code that made it would prove little. Each rule is a term of the
  vocabulary (cascade:RecordFromServerNamingRule and the rest), and a table's inputs column gives the rule first, then
  its inputs in order, a list in parentheses. tests/vectors/naming/ holds the vectors every implementation reproduces,
  and tests/naming.py computes them.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Ada
  imports Apple Health exports of four allergies (peanut, latex, shellfish, mango) from one hospital, and later
  exports that change them. Ben enters a peanut allergy and an asthma by hand. Cleo claims her hospital profile with
  an About, imports five allergies, enters ten more by hand, and judges some herself.

  Rule: N1. A record from a document keeps the name the Bridge gave it
    decisions/naming.md, rows "record from a server", "record from a document" and "record from C-CDA"; decisions/republishing-sources.md, row "record from a FHIR document"; decisions/variant-interpretation.md, row "its name"; decisions/variant-record.md, row "its name".
    The Bridge names
    each record by its rule, cascade:RecordFromServerNamingRule, cascade:RecordFromDocumentNamingRule,
    cascade:RecordFromCcdaNamingRule, cascade:RecordFromCcdaWithoutIdNamingRule or cascade:ContainedRecordNamingRule,
    as tests/vectors/naming/ shows.

    Example: each record an import writes has the name the Bridge gave it
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then these are named:
        | thing               | inputs                                                                                         | name                                          |
        | allergy "Peanut"    | cascade:RecordFromServerNamingRule, https://fhir.example.org/r4, AllergyIntolerance, peanut    | urn:uuid:beaefb13-def8-8f7f-882d-eff4a1ee11d9 |
        | allergy "Latex"     | cascade:RecordFromServerNamingRule, https://fhir.example.org/r4, AllergyIntolerance, latex     | urn:uuid:19bf6db0-83b8-8973-a79a-6b36138cb69b |
        | allergy "Shellfish" | cascade:RecordFromServerNamingRule, https://fhir.example.org/r4, AllergyIntolerance, shellfish | urn:uuid:fcdf6ee4-d11a-8ca6-8c7e-748d87af62e2 |
        | allergy "Mango"     | cascade:RecordFromServerNamingRule, https://fhir.example.org/r4, AllergyIntolerance, mango     | urn:uuid:df9490a2-ae95-87ef-a856-b899697aaf11 |

  Rule: N2. A record from an entry is named from its session and the draft's position
    decisions/naming.md, row "record from an entry". cascade:EnteredRecordNamingRule, over the entry session's IRI, which
    the entry gives (N7), and the draft's position N from urn:cascade:output-N, in decimal.

    Example: each draft of an entry is a record of its own, named from its session and its position
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      Then these are named:
        | thing              | inputs                                                                            | name                                          |
        | allergy "Peanut"   | cascade:EnteredRecordNamingRule, urn:uuid:ee6c4455-4446-4a5a-b28b-dedf744f4c01, 0 | urn:uuid:25a4876c-740b-8654-81ef-adf78e45f6d2 |
        | condition "Asthma" | cascade:EnteredRecordNamingRule, urn:uuid:ee6c4455-4446-4a5a-b28b-dedf744f4c01, 1 | urn:uuid:58858af9-286c-8630-9711-c04ea178bf2e |

  Rule: N3. A version is named from its content
    decisions/naming.md, row "version"; decisions/variant-interpretation.md, row "reclassification"; decisions/variant-record.md, row "content".
    cascade:VersionNamingRule, the Bridge's VersioningTest in
    https://github.com/the-cascade-protocol/cascade-bridge-spec/blob/main/vocab/bridge.ttl. An entry's versions are named by the
    same rule, with a reference to a draft record replaced by that record's name.

    Example: an entry's versions are named from their content, a draft's reference replaced by its record's name
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      Then these are named:
        | thing                           | name                                                      |
        | version 1 of allergy "Peanut"   | ni:///sha-256;mlP4M3MU6FDEoeHJF6GRr-LuhBzOMUoqUdvgpoWlI18 |
        | version 1 of condition "Asthma" | ni:///sha-256;yxMHROzm5nKt316d0UTtdz7zZREMPszlUlDd1guPhes |
      And these records have:
        | record             | field         | value            |
        | allergy "Peanut"   | influenced by |                  |
        | condition "Asthma" | influenced by | allergy "Peanut" |

  Rule: N4. A revision is named the same way, from its own triples
    decisions/naming.md, rows "revision" and "source's own version".
    cascade:RevisionNamingRule. Its placeholder is urn:cascade:this-revision, and
    its triples are: rdf:type cascade:Revision, cascade:revisionOf, cascade:version, prov:generatedAtTime (the start of
    the import, the session or the connect), cascade:observedAsOf (C1), prov:wasGeneratedBy (the import, the session or
    the connect),
    prov:wasRevisionOf (each of the record's heads, if it has any), and every other statement on the arrival except
    bridge:arrivedAs and prov:wasGeneratedBy, oa:hasSource the document among them, its selector written as the
    revision's oa:hasSelector: a node of the revision, <revision>#selector, an oa:FragmentSelector for a JSON document,
    its rdf:value the selector in RFC 6901 section 6's URI fragment form and its dcterms:conformsTo
    https://www.rfc-editor.org/rfc/rfc6901, or an oa:XPathSelector for an XML document, its rdf:value the selector. The
    vector revision-with-selector under tests/vectors/naming/ names one.

    No example names a revision: its name depends on a run, through the ID of the import, the session or the connect.
    A9's example pins the triples it is named from.

  Rule: N5. A document is named by its bytes
    decisions/naming.md, row "document, finding". cascade:DocumentNamingRule: ni:///sha-256; followed by the unpadded
    base64url SHA-256 of its bytes.

    Example: each kept document is named by the SHA-256 of its bytes
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then these are named:
        | thing                               | name                                                      |
        | the document of allergy "Peanut"    | ni:///sha-256;K96dQ7NMCx_qaokgjdYAocBi7_dSJVtKQmYSfWR4rRc |
        | the document of allergy "Latex"     | ni:///sha-256;BAt9YpIrH17dd8_pYoWl5kIAmfZI4pkKRTV1u7JSRnk |
        | the document of allergy "Shellfish" | ni:///sha-256;HgLQlJLSGhMq7xC5CYdLQEFVzvepvRrLiCGzeI65KI0 |
        | the document of allergy "Mango"     | ni:///sha-256;BMVJZrtTlT-XS2y6CvRWFW3r9Pi9GmNMlC-jzs1doZs |

  Rule: N6. A matcher judgment is named by the matcher judgment naming rule, and each assertion of it by the matcher judgment assertion naming rule
    decisions/naming.md, rows "matcher judgment" and "assertion, retraction by a release"; decisions/judgments.md, rows "matcher judgment and assertion" and "what a judgment, a finding or a view came from".
    The matcher judgment: cascade:MatcherJudgmentNamingRule, over, in this order: the maker, cascade:CascadeMatcher; the matcher rule term the rule list's row names (cascade:matcherRule); the
    justification; the members (M5), as a list; and everything it used, as a list, which never holds the rule list's
    version. It carries no time, so every run that reaches it reaches one name. Its assertion:
    cascade:MatcherJudgmentAssertionNamingRule, over the rule list version it is asserted under and the matcher judgment; it carries no time and
    names no run.

    Example: each judgment of a matcher run is named from the matcher, its justification, its members and what it used
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And Cleo enters "entry" on 2026-03-03 at 08:00
      When the matcher runs on the records of that entry on 2026-03-03 at 08:01
      Then that step wrote these matcher judgments:
        | justification    | members                                                                                                         | inputs                                                                                                                                                                                                                                                                                                                                                                                                                    | name                                          |
        | same code        | allergy RxNorm 10180 from sulfa, allergy RxNorm 10180 "Gantanol"                                                | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:13d721fb-b987-8c99-8a35-996a41bb164e, urn:uuid:fe55cfcc-c2b1-80c9-94c0-35bf68292cfc), (ni:///sha-256;VYaHdvjLZQv45sdWhrjmlj0hYlRrV6kZFvZVpDYrvkk, ni:///sha-256;VzP3MpLc8IL3Au_dpDT7vxTwsEPWA3jLJPOW2AEmEVY)                                                                                                           | urn:uuid:bea4ef01-8a02-8365-a977-c42c92ad8992 |
        | same code        | allergy RxNorm 1191 "Aspirin", allergy RxNorm 1191 "Bayer aspirin"                                              | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:1205148c-d231-891f-b2a4-872910f104dd, urn:uuid:21c34d40-b901-81fb-a3e9-9379ede7ea3c), (ni:///sha-256;GSSWGwj1ky6fqUutVt4hwbnAb0jIBXmqEsQVjtGIkz4, ni:///sha-256;w1VgtrE24VhRoi7O3HAE_un6tANfcbaqZF2B28MvXg4)                                                                                                           | urn:uuid:17b4cfce-9cf3-8021-b33b-30f7714362b7 |
        | same code        | allergy RxNorm 1191 "Bayer aspirin", allergy RxNorm 1191 "Ecotrin"                                              | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:1205148c-d231-891f-b2a4-872910f104dd, urn:uuid:47afd546-e89d-8efe-ad3a-0796ae353ec1), (ni:///sha-256;C1BRIvViJbv3nhp8HJSkMElRww1qBiikORfwiS4pRzs, ni:///sha-256;GSSWGwj1ky6fqUutVt4hwbnAb0jIBXmqEsQVjtGIkz4)                                                                                                           | urn:uuid:c75e060a-c162-8953-91dd-4cdcaf6d7e33 |
        | same code        | allergy RxNorm 7980 "Penicillin G", allergy RxNorm 7980 "Bicillin"                                              | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:bccb23ff-cf7f-83fb-928a-645915919943, urn:uuid:d5e8fd33-654f-8669-991f-9253dd59ef59), (ni:///sha-256;M3XXz5dSyS93vVaCuV5SagIfpDZbgz4vgXWJgjpagFE, ni:///sha-256;iJo6C8HlOaqrgICJIAagM_211uavgNETm5weOKAa2tQ)                                                                                                           | urn:uuid:2e5af0a0-7d87-8f4c-b548-8e3538d2bf90 |
        | same code        | allergy RxNorm 2670 from codeine-1, allergy RxNorm 2670 from codeine-2, allergy RxNorm 2670 "Codeine phosphate" | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:146e5e6c-b7c9-800a-9e8f-f2ec430aa76b, urn:uuid:d5b0f070-7cd3-8e4c-952a-a8d608135a1d, urn:uuid:de5fef39-300f-8fc0-aae0-89d9299ec849), (ni:///sha-256;-z3HCFGfpHKNuidlXA-KglWKJfvucAsvHKB5ZcVZ-zQ, ni:///sha-256;X1W8qUhshwHSpbzrUVJ2XUBSwDlSnRWYEigBXPB3ckI, ni:///sha-256;_N_ahMNI_ths69ePUqEvI6sQ_GwUR0d66fo38zTJ7ls) | urn:uuid:45368f8d-6ab8-8d65-8366-f67776a17b5a |

    Example: the judgments of the rules that also compare dates are named the same way
      Given a new pod for Dev on 2026-04-01 at 09:00
      And Dev enters "pairs" on 2026-04-02 at 09:00
      When the matcher runs on the records of that entry on 2026-04-02 at 09:05
      Then the matcher's judgments holding immunization CVX 150 "Fluzone", immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval" and immunization CVX 141 "Fluad" are:
        | justification             | members                                                         | inputs                                                                                                                                                                                                                                                                                                                                                                                               | name                                          |
        | same code and date        | immunization CVX 150 "Fluzone", immunization CVX 150 "Afluria"  | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeAndDateRule, cascade:SameCodeAndDate, (urn:uuid:19f3cb00-2efc-8253-b19c-ef1af699be90, urn:uuid:378463e0-fb61-8f8d-b507-4f414e8434ff), (ni:///sha-256;CSlRM5xyB9fPIdaoN0vM_uZxi03e1ipy2M1SajJtauQ, ni:///sha-256;qGd9AMZz72K_bxKokFSWgU13dZDxxsOFuISTgl2A_j0)                                                                        | urn:uuid:05d14a9f-a9c6-8174-b84d-c6078de762e2 |
        | same mapped code and date | immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval" | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameMappedCodeAndDateRule, cascade:SameMappedCodeAndDate, (urn:uuid:3dc7c789-629b-8c3d-bd56-1022c3b61370, urn:uuid:d9f834de-8400-8ea3-919d-9ee5c0dc81c0), (ni:///sha-256;74dShxmpQX8gLDSpc1-NCZc4pMfzOxUYrWX1iVPmNLY, ni:///sha-256;MVEOtUNQU1HYjJyOb0bkCIaR-wr8kaEPU_tDazvqXfo, ni:///sha-256;QB2fkudO_blj2MpVxMnWi-kAWCzxRbG1odWEGTSZL2I) | urn:uuid:14af565b-804d-84e3-b9a3-f3726e9d3535 |
        | same code and date        | immunization CVX 141 "Fluarix", immunization CVX 141 "Fluad"    | cascade:MatcherJudgmentNamingRule, cascade:CascadeMatcher, cascade:SameCodeAndDateRule, cascade:SameCodeAndDate, (urn:uuid:3dc7c789-629b-8c3d-bd56-1022c3b61370, urn:uuid:52a6821b-4f89-8890-9eb2-9ce535008383), (ni:///sha-256;74dShxmpQX8gLDSpc1-NCZc4pMfzOxUYrWX1iVPmNLY, ni:///sha-256;X79OAJXuXOeTdNyY-kDqKf5EAUhSTToICSZBinQYoCs)                                                                        | urn:uuid:6cdac3ea-1be7-8629-88f2-d2d43debe118 |

  Rule: N7. An import and a matcher run each get a new random UUID, an entry session keeps the IRI the app minted for it, and every act names the runtime that performed it
    decisions/naming.md, row "act". An import and a matcher run, a recheck's and an open's among them, are each a
    urn:uuid:, version 4, new on every run. An entry's session is minted once by the app that took the entry, and the
    entry carries it, so its records' names (N2) are the same on every run. Nothing else is random. Each act says
    prov:wasAssociatedWith the runtime that performed it, a prov:SoftwareAgent named as N8 names a checkout:
    https://github.com/the-cascade-protocol/cascade-runtime-js/tree/<commit>/ for the reference runtime, written
    https://github.com/the-cascade-protocol/cascade-runtime-js/tree/<commit>/#uncommitted for a build with uncommitted changes and
    https://github.com/the-cascade-protocol/cascade-runtime-js#unidentified for one whose commit it cannot read. A matcher run is a
    cascade:MatcherRun and a prov:Activity, prov:wasInformedBy the import or entry session whose records it takes, and is
    written only when it writes something else. A rule list version migration is a new random UUID too, a
    cascade:RuleListVersionMigration and a prov:Activity, written only when it writes a retraction (N15). The kit's
    check 4 holds each of a replay's acts to it.
    A connect (A16) is named as an import is: a urn:uuid:, version 4, new on every connect. A sync is a new random UUID
    too, a cascade:SyncFromAnotherWriter and a prov:Activity, whose examples are sync.feature's.

    Example: an import is named by a new random UUID, which no input gives
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then that step's import is named by a new random UUID

    Example: an entry's session is named by the IRI the entry gives it, and names the runtime that performed it
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      When the query is:
        """
        SELECT ?session ?runtime WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:entry> prov:generated ?file }
          GRAPH ?file { ?session a prov:Activity ; prov:startedAtTime [] ; prov:wasAssociatedWith ?runtime .
                        ?runtime a prov:SoftwareAgent }
        }
        """
      Then it answers:
        | session                                         | runtime     |
        | <urn:uuid:ee6c4455-4446-4a5a-b28b-dedf744f4c01> | the runtime |

    Example: a matcher run is named by a new random UUID, takes the entry session it was informed by, and names the runtime
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And Cleo enters "entry" on 2026-03-03 at 08:00
      When the matcher runs on the records of that entry on 2026-03-03 at 08:01
      When the query is:
        """
        SELECT ?random ?informedBy ?runtime WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:matcher> prov:generated ?file }
          GRAPH ?file { ?run a cascade:MatcherRun, prov:Activity ; prov:startedAtTime [] ; prov:wasInformedBy ?informedBy ;
                          prov:wasAssociatedWith ?runtime }
          BIND (REGEX(STR(?run), "^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$") AS ?random)
        }
        """
      Then it answers:
        | random | informedBy                                      | runtime     |
        | true   | <urn:uuid:4c555575-696f-4a0a-b4fa-228549fb872f> | the runtime |

  Rule: N8. What a runtime gives the Bridge
    No note rules this.
    - The adapter: <repository>/tree/<commit>/, at the commit the run reads, of the adapter the document is offered to.
      A document is offered, one adapter at a time, to the adapters cascade-runtime.json names whose
      bridge:sourceMediaType is the media type its importer gives it, in that order: each is asked whether it accepts
      the document, and the first whose answer is yes converts it. A no passes it to the next; a document failure
      refuses the step (A14).
    - The vocabulary: the same form, for the repository the adapter's bridge:cascadeVocabularyRepository
      names, at the commit the run reads.
    - A document: its N5 name, which is the name the Bridge itself gives it.
    - Its facts: the document's IRI followed by #facts.

    A checkout used as it is on disk is named by the commit it is at. Each IRI ends in a slash, so every file's path
    resolves against it.

    No example shows this rule, because what the Bridge is given never reaches the pod. engine/library.md in
    cascade-bridge-spec and the runtime's Bridge interface use it, and their own tests check it.

  Rule: N9. A file's name comes from the name of what it holds
    decisions/files-held-in-archives.md, row "an archive's name", rules its last paragraph; no note rules the rest.
    For a urn:uuid: name, the UUID; for an ni:///sha-256; name, the hash in lowercase hex. An RDF file adds .ttl; a stored
    document adds nothing. The folder and the fan-out are the layout's, pod-layout.ttl.

    An archive (X1) holds files and is named by none of them: its name is the SHA-256 of its own bytes in lowercase hex,
    adding .zip, in the folder pod-layout.ttl gives cascade:holdsFilesInArchivesOfMediaType, with no fan-out. A host
    checks that an archive's bytes hash to its name when it receives the archive (S1) and when a clean-up merges it, and
    refuses one that does not: the receive writes nothing. Reading an archive needs only its end of central directory
    record; an archive with none, which is a torn one, fails the open, naming the archive, and nothing is read from it.

    Every example shows this rule, because each graph is named by its file's path.

    Example: each file an import writes is named from the name of what it holds
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      When the query is:
        """
        SELECT ?thing ?fileName WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:first-export> prov:generated ?file }
          FILTER NOT EXISTS { GRAPH ?file { ?revision a cascade:Revision } }
          FILTER NOT EXISTS { GRAPH ?file { ?import prov:used ?document } }
          OPTIONAL { GRAPH ?file { ?thing a ?type FILTER (?type IN (cascade:AllergyOrIntolerance, cascade:Server, prov:Entity)) } }
          OPTIONAL { GRAPH ?file { ?thing prov:specializationOf ?record } }
          BIND(REPLACE(STR(?file), "^.*/", "") AS ?fileName)
        }
        """
      Then it answers:
        | thing                                                       | fileName                                                               |
        | <urn:uuid:beaefb13-def8-8f7f-882d-eff4a1ee11d9>             | "beaefb13-def8-8f7f-882d-eff4a1ee11d9.ttl"                             |
        | <urn:uuid:19bf6db0-83b8-8973-a79a-6b36138cb69b>             | "19bf6db0-83b8-8973-a79a-6b36138cb69b.ttl"                             |
        | <urn:uuid:fcdf6ee4-d11a-8ca6-8c7e-748d87af62e2>             | "fcdf6ee4-d11a-8ca6-8c7e-748d87af62e2.ttl"                             |
        | <urn:uuid:df9490a2-ae95-87ef-a856-b899697aaf11>             | "df9490a2-ae95-87ef-a856-b899697aaf11.ttl"                             |
        | <urn:uuid:c3c2e8d8-6bc9-80ac-a26d-dc02b72065bf>             | "c3c2e8d8-6bc9-80ac-a26d-dc02b72065bf.ttl"                             |
        | <ni:///sha-256;d_pMibc0ED454HtBEFnmnzYooyTeQoT6x0qyCzyjHgc> | "77fa4c89b734103e39e07b411059e69f3628a324de4284fac74ab20b3ca31e07.ttl" |
        | <ni:///sha-256;wcxukIkxmUPtdeHUvgKSrW9EBdKVvruBauDZvsMHg0A> | "c1cc6e9089319943ed75e1d4be0292ad6f4405d295bebb816ae0d9bec3078340.ttl" |
        | <ni:///sha-256;uSaNqwnnbOWt-cYNz9VaJQk-8Hko5AkNuw8epnb2pNk> | "b9268dab09e76ce5adf9c60dcfd55a25093ef07928e4090dbb0f1ea676f6a4d9.ttl" |
        | <ni:///sha-256;Sh2Nlw2DVkOXxZfd5-r4C3zQrhJyluXZnlw21EPLfig> | "4a1d8d970d83564397c597dde7eaf80b7cd0ae127296e5d99e5c36d443cb7e28.ttl" |
        | <ni:///sha-256;K96dQ7NMCx_qaokgjdYAocBi7_dSJVtKQmYSfWR4rRc> | "2bde9d43b34c0b1fea6a89208dd600a1c062eff752255b4a4266127d6478ad17.ttl" |
        | <ni:///sha-256;BAt9YpIrH17dd8_pYoWl5kIAmfZI4pkKRTV1u7JSRnk> | "040b7d62922b1f5edd77cfe96285a5e6420099f648e2990a453575bbb2524679.ttl" |
        | <ni:///sha-256;HgLQlJLSGhMq7xC5CYdLQEFVzvepvRrLiCGzeI65KI0> | "1e02d09492d21a132aef10b909874b404155cef7a9bd1acb8821b3788eb9288d.ttl" |
        | <ni:///sha-256;BMVJZrtTlT-XS2y6CvRWFW3r9Pi9GmNMlC-jzs1doZs> | "04c54966bb53953f974b6cba0af456156debf4f8bd1a634c942fa3cecd5da19b.ttl" |
        |                                                             | "2bde9d43b34c0b1fea6a89208dd600a1c062eff752255b4a4266127d6478ad17"     |
        |                                                             | "040b7d62922b1f5edd77cfe96285a5e6420099f648e2990a453575bbb2524679"     |
        |                                                             | "1e02d09492d21a132aef10b909874b404155cef7a9bd1acb8821b3788eb9288d"     |
        |                                                             | "04c54966bb53953f974b6cba0af456156debf4f8bd1a634c942fa3cecd5da19b"     |

  Rule: N10. A person's judgment, and a person's retraction, keeps the IRI its input gives it
    decisions/naming.md, rows "person's judgment" and "retraction"; decisions/judgments.md, rows "maker", "retraction" and "what a judgment, a finding or a view came from".
    A judgment a person makes arrives with its name: whoever made it minted that once, as the subject's ID was minted. A
    runtime files it under that IRI and gives it no other; it is neither a new random UUID nor named by a rule. So a
    judgment can name another person's judgment, and an answer can name it, on every run. A person's retraction, a
    prov:Activity that prov:invalidated a judgment (decisions/naming.md, row "retraction"), arrives with its name too and
    is filed under it, in the folder pod-layout.ttl gives what states prov:invalidated, even when it also states prov:used
    (cascade:Placement). A person's judgment names the part its author acted in, cascade:PatientRole, on a
    prov:qualifiedAssociation of the act that generated it, a blank node filed with the judgment; a retraction, an act
    itself, names it on its own association. A model that proposed either is named on another association of the same
    act (Y3).

    Example: a person's About and its retraction are each filed under the IRI they arrived with, in their own step's file
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-r" on 2026-03-04 at 07:00
      When Cleo files the judgment "retract-about-r" on 2026-03-04 at 12:00
      When the query is:
        """
        SELECT ?step ?filed ?kind ?verdict WHERE {
          GRAPH <urn:cascade:steps> { ?step prov:generated ?file }
          GRAPH ?file { ?filed a ?kind OPTIONAL { ?filed cascade:verdict ?verdict } }
          FILTER (?filed IN (<urn:uuid:b8d3f1a7-2c69-4e5b-9f14-3a7e6d2c8b91>, <urn:uuid:f2b6d9a4-7e3c-4815-b9d7-5a8e2c6f1d43>))
        }
        """
      Then it answers:
        | step                               | filed                                           | kind             | verdict       |
        | <urn:cascade:step:about-r>         | <urn:uuid:b8d3f1a7-2c69-4e5b-9f14-3a7e6d2c8b91> | cascade:Judgment | cascade:About |
        | <urn:cascade:step:retract-about-r> | <urn:uuid:f2b6d9a4-7e3c-4815-b9d7-5a8e2c6f1d43> | prov:Activity    |               |

  Rule: N11. A mapping row is named from its subject, its predicate and its object
    decisions/naming.md, row "derived name".
    cascade:TableRowNamingRule. Its IRI is its SSSOM record_id, and the rule's inputs, in this order, are the IRIs of
    its owl:annotatedSource, owl:annotatedProperty and owl:annotatedTarget. A row in two versions has one name in both.

    A panel member row (cascade:PanelMembers) has a fourth input, the canonical lexical form of its cascade:panelSequence (no
    sign, no leading zeros), because LOINC lists a member of a panel at two sequences, and the two places are two rows.

    No example shows this rule, because no step writes a row. The vocabulary's tests check every row of every kit and
    vector against it.

  Rule: N12. A table version is named from its series, the version it revises and its rows
    decisions/naming.md, row "version".
    cascade:TableVersionNamingRule: N3's rule over exactly these triples: <urn:cascade:this-version> prov:specializationOf its series,
    <urn:cascade:this-version> prov:wasRevisionOf the version it revises when there is one, and its rows. A row holds
    no blank node, so the canonical form is its triples' N-Triples lines in order. Two series with no rows have two
    names, and rows a version shares with an earlier one of its series still give it a name of its own. A story's
    versions are named so too.

    No example shows this rule, because no step names a version. The vocabulary's tests check it on
    tests/table-versions/.

  Rule: N13. A view entry is named relative to its view
    decisions/naming.md, row "view entry". cascade:ViewEntryNamingRule: the view's path as pod-layout.ttl places it, #,
    and the lower-case hexadecimal SHA-256 of the IRI of its least member in code point order. SPARQL cannot mint a
    relative IRI, so queries/derivations/entries.rq names each entry by a placeholder, urn:cascade:entry: and that hex,
    as urn:cascade:this-version stands for a version until it is named. When the runtime writes or shares a view, it
    writes each entry in the view file as <#hex>, the relative reference from the view's own path, never resolved
    against the pod's address, and no placeholder remains. An entry is named in the view that gives it members; another
    view in the same folder cites it by the relative reference from its own path, as the variant interpretations view
    cites a variant's entry as <variants.ttl#hex>. A member's current values in the view (cascade:memberCurrentValues)
    are a node named as the entry is, followed by -, and the lower-case hexadecimal SHA-256 of the member's IRI: <#hex-hex>.

    Nothing outside the view cites an entry. An app's statement about an entry names the records the person was shown in
    it, never the entry, and never changes after; it finds the entry again by the question record/Which entry shows it,
    read after every import or rebuild, and a read adds nothing to it. A runtime that removes an original carries a
    statement whose every record it removes to the records their entry then holds, signed as the runtime and listed for
    review; no runtime removes an original yet. A record is in at most one entry: it has a row in that question, or none and a row in record/Why it is in no view, or
    neither, which means the pod no longer holds it. A statement whose records are now in two entries is shown with each.

    No example shows this rule, because a query reads an entry's IRI resolved against the view's address, and the
    derived state, which examples query, holds the placeholder. The kit's
    check 6 holds every view a replay writes to it, and tests/vectors/naming/ names an entry.

  Rule: N14. Every act leaves one snapshot, chained to the writer's previous one
    decisions/naming.md, row "snapshot"; decisions/performance.md, row "snapshot chain".
    A node in the act's own file, a cascade:Snapshot, prov:wasGeneratedBy the act
    and named by cascade:SnapshotNamingRule. Its cascade:firstParentSnapshot is the writer's last snapshot, its
    previous one or the head it took as git fast-forwards (S4), which the writer keeps outside the pod as git keeps
    HEAD; a writer's first snapshot has none, and a writer that lost its last one is a new writer: a writer handed a
    head the pod does not hold as a snapshot is one too. Its cascade:mergedParentSnapshot values are the heads it
    merges: on a writer's first, every snapshot the pod holds that no snapshot names as a parent, and on a sync, every
    such snapshot but the first parent (S3). Its cascade:setHash is the set hash of the set the writer holds once the
    act's other files are written, its own file left out, and its name binds the act's description. Its
    cascade:fileAddedToSet values are the paths of the files of the set the act wrote, its own file among them, and of
    no other; a sync's names none, since its file is in the syncs' folder, outside the set, and the files that arrived
    are named by the snapshots of the acts that wrote them (S3). The set and the hash are cascade:Snapshot's and
    cascade:setHash's. A step that is no act, a new pod's creation, a reference
    version's arrival or a person's judgment, leaves no snapshot, and the files it writes are in the next snapshot's set
    but named by none. An act that writes nothing leaves no snapshot. tests/vectors/snapshot/ holds the vectors every
    implementation reproduces.

    No example computes a set hash or a snapshot's name: SPARQL cannot multiply 3072-bit numbers or canonicalise blank
    nodes, and an act's name is random. The kit's check 4 holds every snapshot of a replay to this rule.

    Example: a writer's first snapshot has no first parent, and each later act's names the one before it
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And Cleo enters "entry" on 2026-03-03 at 08:00
      When the matcher runs on the records of that entry on 2026-03-03 at 08:01
      When the query is:
        """
        SELECT ?step ?firstParentStep (COUNT(?merged) AS ?mergedParents) WHERE {
          GRAPH <urn:cascade:steps> { ?step prov:generated ?file }
          GRAPH ?file { ?snapshot a cascade:Snapshot ; prov:wasGeneratedBy ?act . ?act a prov:Activity }
          OPTIONAL {
            GRAPH ?file { ?snapshot cascade:firstParentSnapshot ?parent }
            GRAPH <urn:cascade:steps> { ?firstParentStep prov:generated ?parentFile }
            GRAPH ?parentFile { ?parent a cascade:Snapshot }
          }
          OPTIONAL { GRAPH ?file { ?snapshot cascade:mergedParentSnapshot ?merged } }
        }
        GROUP BY ?step ?firstParentStep
        """
      Then it answers:
        | step                            | firstParentStep                 | mergedParents |
        | <urn:cascade:step:first-export> |                                 | 0             |
        | <urn:cascade:step:entry>        | <urn:cascade:step:first-export> | 0             |
        | <urn:cascade:step:matcher>      | <urn:cascade:step:entry>        | 0             |

    Example: a snapshot names each file its act wrote, its act's own file among them
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And Cleo enters "entry" on 2026-03-03 at 08:00
      When the matcher runs on the records of that entry on 2026-03-03 at 08:01
      When the query is:
        """
        SELECT ?folder (COUNT(DISTINCT ?file) = COUNT(DISTINCT ?path) AS ?eachNamed) WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:matcher> prov:generated ?file }
          GRAPH <urn:cascade:steps> { <urn:cascade:step:matcher> prov:generated ?actFile }
          GRAPH ?actFile { ?snapshot a cascade:Snapshot }
          BIND (STRAFTER(STR(?file), "https://pod.example/") AS ?relative)
          OPTIONAL { GRAPH ?actFile { ?snapshot cascade:fileAddedToSet ?path } FILTER (?path = ?relative) }
          BIND (STRBEFORE(?relative, "/") AS ?folder)
        }
        GROUP BY ?folder
        """
      Then it answers:
        | folder        | eachNamed |
        | "judgments"   | true      |
        | "provenance"  | true      |
        | "references"  | true      |

  Rule: N15. A release's retraction is named from the release, the assertion and the rule it declares wrong
    decisions/naming.md, rows "act", "assertion, retraction by a release" and "retraction"; decisions/judgments.md, row "retraction".
    A rule list version, the release, declares a matcher rule wrong by cascade:matcherRuleDeclaredWrong in its description. Whenever the pod's current rule list
    version is the release or a version after it, a runtime performs the rule list version migration, an act (N7): at
    an open, before its matcher run (O1), with the version it adopts as the current one; at a sync's arrival; and before
    a matcher run. For each version on the line up to the current one that declares a rule wrong, oldest first, and each
    assertion of that rule's matcher judgment under a version it revises, directly or not, that no retraction invalidates, it
    writes a retraction: a prov:Activity that prov:invalidated the assertion and prov:used the release, named by
    cascade:ReleaseRetractionNamingRule over, in order, the release, the assertion and the rule. It carries no time and names no
    run, so two writers on one release write one file with one content, whatever order they met the versions in, and a
    pod that holds those retractions already, from another writer, writes nothing. A matcher judgment counts and lapses by the
    assertions no retraction invalidates: one whose every assertion a release retracted neither counts nor lapses, so
    "What needs review" never offers its pair back. An assertion under the release or a version after it is not
    declared wrong: a version that ships the rule fixed, or runs it again, asserts the matcher judgment again and it can join its
    pair again (M9). A person's retraction invalidates a person's judgment, never the matcher's (N16). Hana's pod and the apps' tables are opening.feature's.

    Example: adopting a release that declares R4 wrong retracts the assertions of R4's two matcher judgments before the open's matcher runs, and neither matcher judgment counts nor lapses
      Opened with "app-fewer-rules" instead, the two matcher judgments lapse and "What needs review" lists their pairs (O1).

      Given a new pod for Hana on 2026-07-01 at 09:00
      And the pod is opened with the tables "app" on 2026-07-01 at 09:01
      And Hana enters "flu-shots" on 2026-07-02 at 09:00
      And the matcher runs on the records of that entry on 2026-07-02 at 09:05
      When the pod is opened with the tables "app-wrong-rule" on 2026-07-03 at 09:00
      Then that step wrote these retractions:
        | justification             | members                                                                   | inputs                                                                                                                                                       | name                                          |
        | same mapped code and date | immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval"           | cascade:ReleaseRetractionNamingRule, urn:uuid:5b4d87d9-5a19-4bc9-8c26-22747b46e8d8, urn:uuid:594dc81f-d7bb-85e9-a1c1-6f49ede1b313, cascade:SameMappedCodeAndDateRule | urn:uuid:86de92fb-f9c0-85ae-9808-b7b7794735ae |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | cascade:ReleaseRetractionNamingRule, urn:uuid:5b4d87d9-5a19-4bc9-8c26-22747b46e8d8, urn:uuid:c01bb4af-045f-8594-8d6e-e93e0ae0dca4, cascade:SameMappedCodeAndDateRule | urn:uuid:a92a17c1-a553-8cf6-a17a-931697f6f5b9 |
      And that step wrote these matcher judgments:
        | justification | members | used |
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" does not count
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" has not lapsed
      And the matcher's same mapped code and date of immunization CVX 141 "Fluad" and immunization CVX 161 "Fluzone Quadrivalent" does not count
      And the matcher's same mapped code and date of immunization CVX 141 "Fluad" and immunization CVX 161 "Fluzone Quadrivalent" has not lapsed

    Example: a writer that received another writer's retractions adopts the release and writes no migration of its own
      Given a new pod for Hana on 2026-07-01 at 09:00
      And the pod is opened with the tables "app" on 2026-07-01 at 09:01
      And Hana enters "flu-shots" on 2026-07-02 at 09:00
      And the matcher runs on the records of that entry on 2026-07-02 at 09:05
      And a second writer of the pod
      And the pod is opened with the tables "app-wrong-rule" on 2026-07-03 at 09:00
      And the steps that follow are the second writer's
      And the second writer receives the files of the first writer on 2026-07-03 at 10:00
      When the pod is opened with the tables "app-wrong-rule" on 2026-07-03 at 11:00 (second-open)
      Then that step wrote these retractions:
        | justification | members | inputs | name |
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" does not count
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" has not lapsed
      When the query is:
        """
        SELECT (COUNT(?migration) AS ?migrations) WHERE { ?migration a cascade:RuleListVersionMigration }
        """
      Then it answers:
        | migrations |
        | 1          |

  Rule: N16. A person's judgment names records and the documents they were shown from, never a version, and never replaces or retracts a matcher's judgment
    decisions/naming.md, row "person's judgment" and its Why "Nothing kept cites anything derived"; decisions/judgments.md, row "what a judgment, a finding or a view came from".
    A person's judgment is kept, and versions, revisions, matcher judgments, findings and entries are derived, so it
    names none of them. When a person files a judgment whose members are records, the runtime adds, by
    prov:wasDerivedFrom, the document each member's current revision was derived from, which is what the person was
    shown, and never a version (cascade:PersonJudgmentDerivedFromNoVersionShape); a member entered by hand, whose
    revisions came from no document, adds none. A prov:wasDerivedFrom the input states is not filed. A runtime refuses a
    person's judgment that replaces (dct:replaces) a matcher's judgment, and a person's retraction of one, a matcher's
    judgment being any judgment that carries cascade:matcherRule, whatever its agent is typed
    (cascade:PersonJudgmentReplacesNoMatcherJudgmentShape, cascade:RetractionInvalidatesNoMatcherJudgmentShape): a
    person who agrees with the matcher files a Same over the records, and one who disagrees a Different over them. A
    judgment without cascade:matcherRule, such as a model's, is kept as it was minted, and a person may retract it.
    Only a writer that went around its runtime leaves such a file in the pod, and a receive of another writer's files
    that holds one refuses, naming the file's path, and writes nothing, not even the files that came with it (S3 would
    break on a part of the set). Every later receive from that writer meets the same file and refuses again, so the
    writer's file is removed on the writer's device, or a Same or a Different over the records is filed instead.

    Example: a person's Same over two imported records names the document each was shown from, and no version
      Given a new pod for Cleo on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When Cleo files the judgment "same-sulfa" on 2026-01-03 at 09:00
      And the query is:
        """
        SELECT ?from WHERE { <urn:uuid:c4e9a2d7-5b18-4f63-9a0e-7d2b8c6f1e54> prov:wasDerivedFrom ?from }
        """
      Then it answers:
        | from                                                        |
        | <ni:///sha-256;ia0W-ov4DzjbXqU9rRMLYEtbJpVewYVtL83fNzhesBE> |
        | <ni:///sha-256;vj5fTxByVxl2nnEtMHUs-LFJg_mzMb25VTMxz1cbTJQ> |

    Example: a person's Same whose input states the two versions is filed without them, naming the documents instead
      Given a new pod for Cleo on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When Cleo files the judgment "same-sulfa-naming-versions" on 2026-01-03 at 09:00
      And the query is:
        """
        SELECT ?from WHERE { <urn:uuid:7d3b1f90-2c64-4e8a-b5d1-9a0e6c4f2b87> prov:wasDerivedFrom ?from }
        """
      Then it answers:
        | from                                                        |
        | <ni:///sha-256;ia0W-ov4DzjbXqU9rRMLYEtbJpVewYVtL83fNzhesBE> |
        | <ni:///sha-256;vj5fTxByVxl2nnEtMHUs-LFJg_mzMb25VTMxz1cbTJQ> |

    Example: a person's Same that replaces the matcher's judgment is refused
      Given a new pod for Gus on 2026-09-01 at 09:00
      And the pod is opened with the tables "app-drugs" on 2026-09-01 at 09:01
      And Gus enters "earlier-sames" on 2026-09-02 at 09:00
      And the matcher runs on the records of that entry on 2026-09-02 at 09:05
      When Gus files the judgment "same-instead-of-the-lisinopril-matcher-judgment" on 2026-09-02 at 12:00
      Then that step is refused

    Example: a person's retraction of the matcher's judgment is refused
      Given a new pod for Gus on 2026-09-01 at 09:00
      And the pod is opened with the tables "app-drugs" on 2026-09-01 at 09:01
      And Gus enters "earlier-sames" on 2026-09-02 at 09:00
      And the matcher runs on the records of that entry on 2026-09-02 at 09:05
      When Gus files the judgment "retract-the-lisinopril-matcher-judgment" on 2026-09-02 at 12:00
      Then that step is refused

    Example: a receive that holds a person's retraction of the matcher's judgment is refused whole
      Given a new pod for Gus on 2026-09-01 at 09:00
      And a second writer of the pod
      And the pod is opened with the tables "app-drugs" on 2026-09-01 at 09:01
      And Gus enters "earlier-sames" on 2026-09-02 at 09:00
      And the matcher runs on the records of that entry on 2026-09-02 at 09:05
      When the second writer receives the files of the first writer and the file "retract-the-lisinopril-matcher-judgment" put in them on 2026-09-02 at 12:00
      Then that step is refused
      And "sync" wrote no file

    Example: a receive that holds a person's Same replacing the matcher's judgment is refused whole
      Given a new pod for Gus on 2026-09-01 at 09:00
      And a second writer of the pod
      And the pod is opened with the tables "app-drugs" on 2026-09-01 at 09:01
      And Gus enters "earlier-sames" on 2026-09-02 at 09:00
      And the matcher runs on the records of that entry on 2026-09-02 at 09:05
      When the second writer receives the files of the first writer and the file "same-instead-of-the-lisinopril-matcher-judgment" put in them on 2026-09-02 at 12:00
      Then that step is refused
      And "sync" wrote no file

    Example: a person's retraction of a model's judgment is kept, and "What needs review" does not list it
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "model-about-r" on 2026-03-04 at 07:00
      When Cleo files the judgment "retract-model-about-r" on 2026-03-04 at 12:00
      And the query "questions/judgment/What needs review.rq" is asked
      Then it answers nothing
