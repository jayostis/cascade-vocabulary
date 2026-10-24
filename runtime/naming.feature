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
    decisions/naming.md, rows "record from a server", "record from a document", "record from C-CDA". The Bridge names
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
    decisions/naming.md, row "version". cascade:VersionNamingRule, the Bridge's VersioningTest in
    https://github.com/jayostis/cascade-bridge-spec/blob/main/vocab/bridge.ttl. An entry's versions are named by the
    same rule, with a reference to a draft record replaced by that record's name.

    Example: an entry's versions are named from their content, a draft's reference replaced by its record's name
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      Then these are named:
        | thing                           | name                                                      |
        | version 1 of allergy "Peanut"   | ni:///sha-256;Madrh_NcaJSrkqMIk02amsTjh7YLsjtyit5b7GNjr_o |
        | version 1 of condition "Asthma" | ni:///sha-256;yxMHROzm5nKt316d0UTtdz7zZREMPszlUlDd1guPhes |
      And these records have:
        | record             | field         | value            |
        | allergy "Peanut"   | influenced by |                  |
        | condition "Asthma" | influenced by | allergy "Peanut" |

  Rule: N4. A revision is named the same way, from its own triples
    decisions/naming.md, row "revision". cascade:RevisionNamingRule. Its placeholder is urn:cascade:this-revision, and
    its triples are: rdf:type cascade:Revision, cascade:revisionOf, cascade:version, prov:generatedAtTime (the import's
    or the session's start), prov:wasGeneratedBy (the import or the session), prov:wasRevisionOf (each of the record's
    heads, if it has any), and every other statement on the arrival except bridge:arrivedAs and prov:wasGeneratedBy,
    oa:hasSource the document among them, its selector written as the revision's oa:hasSelector: a node of the
    revision, <revision>#selector, an oa:FragmentSelector for a JSON document, its rdf:value the selector in RFC 6901
    section 6's URI fragment form and its dcterms:conformsTo https://www.rfc-editor.org/rfc/rfc6901, or an
    oa:XPathSelector for an XML document, its rdf:value the selector. The vector revision-with-selector under
    tests/vectors/naming/ names one.

    No example names a revision: its name depends on a run, through the import's or the session's ID. A9's example pins
    the triples it is named from.

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

  Rule: N6. A matcher judgment is a claim named by the claim rule, and each assertion of it by the assertion rule
    decisions/naming.md, rows "machine judgment" and "assertion". The claim: cascade:ClaimNamingRule, over, in this
    order: the maker, cascade:CascadeMatcher; the matcher rule term the rule list's row names (cascade:matcherRule); the
    justification; the members (M5), as a list; and everything it used, as a list, which never holds the rule list's
    version. It carries no time, so every run that reaches it reaches one name. Its assertion:
    cascade:AssertionNamingRule, over the rule list version it is asserted under and the claim; it carries no time and
    names no run.

    Example: each judgment of a matcher run is named from the matcher, its justification, its members and what it used
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-p" on 2026-03-01 at 09:05
      And the export "first-export" is imported on 2026-03-02 at 10:00
      And Cleo enters "entry" on 2026-03-03 at 08:00
      When the matcher runs on the records of that entry on 2026-03-03 at 08:01
      Then that step wrote these matcher judgments:
        | justification    | members                                                                                                         | inputs                                                                                                                                                                                                                                                                                                                                                                                                                    | name                                          |
        | same code        | allergy RxNorm 10180 from sulfa, allergy RxNorm 10180 "Gantanol"                                                | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:13d721fb-b987-8c99-8a35-996a41bb164e, urn:uuid:fe55cfcc-c2b1-80c9-94c0-35bf68292cfc), (ni:///sha-256;_Vi1-d5kC4tt13fF-9xdRNzaaOQ7JmX_WVnWY0MfOSQ, ni:///sha-256;nj6IrY-r5Fd8i0onPzOBBKySle8swtflY42GAs5SxGA)                                                                                                           | urn:uuid:3e2987b0-dbf5-8fa3-be1d-09a8fcc46fea |
        | same code        | allergy RxNorm 1191 "Aspirin", allergy RxNorm 1191 "Bayer aspirin"                                              | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:1205148c-d231-891f-b2a4-872910f104dd, urn:uuid:21c34d40-b901-81fb-a3e9-9379ede7ea3c), (ni:///sha-256;Nh5MzYTciCL878ED1CzJv-UyJVKw4xokbTZ0EAo0A4o, ni:///sha-256;W1GQWoXsjYBNBNQvld70ods2yv5iMe9soEjqR6Z8H2c)                                                                                                           | urn:uuid:12e3211f-f84c-8295-a19f-580a5761b06a |
        | same code        | allergy RxNorm 1191 "Bayer aspirin", allergy RxNorm 1191 "Ecotrin"                                              | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:1205148c-d231-891f-b2a4-872910f104dd, urn:uuid:47afd546-e89d-8efe-ad3a-0796ae353ec1), (ni:///sha-256;W1GQWoXsjYBNBNQvld70ods2yv5iMe9soEjqR6Z8H2c, ni:///sha-256;jT5ATbQs3eEE8xLujs1BPj1L9aD9sZx3iPms7s-fxoM)                                                                                                           | urn:uuid:e6c490f5-0393-8347-89eb-730bfe547b1f |
        | same mapped code | allergy RxNorm 7980 "Penicillin G", allergy SNOMED 373270004                                                    | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameMappedCodeRule, cascade:SameMappedCode, (urn:uuid:5beb7e98-192f-87a2-9ab7-1233499be250, urn:uuid:bccb23ff-cf7f-83fb-928a-645915919943), (ni:///sha-256;0AhQXzxxseY6ypSxUOsY4mOBp3fJs7ALIEZwQTghduY, ni:///sha-256;0c8Dt6nnfMTzMgzo8MwZd7TAfmMuCy97Dl-D5prsklI, ni:///sha-256;BlFQPte-nrzoZ-yIqrd9zVoP2vxyfSfIO5gxxymsZdA)                                    | urn:uuid:69491f8f-812d-824a-ade4-abe6237ba5f2 |
        | same code        | allergy RxNorm 7980 "Penicillin G", allergy RxNorm 7980 "Bicillin"                                              | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:bccb23ff-cf7f-83fb-928a-645915919943, urn:uuid:d5e8fd33-654f-8669-991f-9253dd59ef59), (ni:///sha-256;0c8Dt6nnfMTzMgzo8MwZd7TAfmMuCy97Dl-D5prsklI, ni:///sha-256;wVWRNywF2xQL8cPELIt5gl-Yla7FCTn3_OyS-YDRa_s)                                                                                                           | urn:uuid:9ae0906a-d990-8734-b5d0-f9635e9e96f4 |
        | same mapped code | allergy RxNorm 7980 "Bicillin", allergy SNOMED 373270004                                                        | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameMappedCodeRule, cascade:SameMappedCode, (urn:uuid:5beb7e98-192f-87a2-9ab7-1233499be250, urn:uuid:d5e8fd33-654f-8669-991f-9253dd59ef59), (ni:///sha-256;0AhQXzxxseY6ypSxUOsY4mOBp3fJs7ALIEZwQTghduY, ni:///sha-256;BlFQPte-nrzoZ-yIqrd9zVoP2vxyfSfIO5gxxymsZdA, ni:///sha-256;wVWRNywF2xQL8cPELIt5gl-Yla7FCTn3_OyS-YDRa_s)                                    | urn:uuid:762824bb-afb0-81d9-b913-34abde19cfc5 |
        | same code        | allergy RxNorm 2670 from codeine-1, allergy RxNorm 2670 from codeine-2, allergy RxNorm 2670 "Codeine phosphate" | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeRule, cascade:SameCode, (urn:uuid:146e5e6c-b7c9-800a-9e8f-f2ec430aa76b, urn:uuid:d5b0f070-7cd3-8e4c-952a-a8d608135a1d, urn:uuid:de5fef39-300f-8fc0-aae0-89d9299ec849), (ni:///sha-256;0gwl5LYkrgMuHESokEb7ACMGMZOp4DKFzetkUx3PGFk, ni:///sha-256;YqZBurt1k6txrA2c3ZYai7VF3rhu7bDG92ua7o8v5Yw, ni:///sha-256;lGiZttUdyP_wps26Ax8DZP6M0NwRNH_Xupbm-KlHkkI) | urn:uuid:ea4b51aa-da1d-8352-94ee-cfba99a1314b |

    Example: the judgments of the rules that also compare dates are named the same way
      Given a new pod for Dev on 2026-04-01 at 09:00
      And Dev enters "pairs" on 2026-04-02 at 09:00
      When the matcher runs on the records of that entry on 2026-04-02 at 09:05
      Then the matcher's judgments holding immunization CVX 150 "Fluzone", immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval" and immunization CVX 141 "Fluad" are:
        | justification             | members                                                         | inputs                                                                                                                                                                                                                                                                                                                                                                                               | name                                          |
        | same code and date        | immunization CVX 150 "Fluzone", immunization CVX 150 "Afluria"  | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeAndDateRule, cascade:SameCodeAndDate, (urn:uuid:19f3cb00-2efc-8253-b19c-ef1af699be90, urn:uuid:378463e0-fb61-8f8d-b507-4f414e8434ff), (ni:///sha-256;CSlRM5xyB9fPIdaoN0vM_uZxi03e1ipy2M1SajJtauQ, ni:///sha-256;qGd9AMZz72K_bxKokFSWgU13dZDxxsOFuISTgl2A_j0)                                                                        | urn:uuid:482faaa6-b264-8622-ad81-c4b26f7d0dd1 |
        | same mapped code and date | immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval" | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameMappedCodeAndDateRule, cascade:SameMappedCodeAndDate, (urn:uuid:3dc7c789-629b-8c3d-bd56-1022c3b61370, urn:uuid:d9f834de-8400-8ea3-919d-9ee5c0dc81c0), (ni:///sha-256;74dShxmpQX8gLDSpc1-NCZc4pMfzOxUYrWX1iVPmNLY, ni:///sha-256;MVEOtUNQU1HYjJyOb0bkCIaR-wr8kaEPU_tDazvqXfo, ni:///sha-256;QB2fkudO_blj2MpVxMnWi-kAWCzxRbG1odWEGTSZL2I) | urn:uuid:f825e3a3-062e-8c97-9a3b-559d3aee9045 |
        | same code and date        | immunization CVX 141 "Fluarix", immunization CVX 141 "Fluad"    | cascade:ClaimNamingRule, cascade:CascadeMatcher, cascade:SameCodeAndDateRule, cascade:SameCodeAndDate, (urn:uuid:3dc7c789-629b-8c3d-bd56-1022c3b61370, urn:uuid:52a6821b-4f89-8890-9eb2-9ce535008383), (ni:///sha-256;74dShxmpQX8gLDSpc1-NCZc4pMfzOxUYrWX1iVPmNLY, ni:///sha-256;X79OAJXuXOeTdNyY-kDqKf5EAUhSTToICSZBinQYoCs)                                                                        | urn:uuid:838ce1ce-7f63-8e8b-a3b7-c8532dc02290 |

  Rule: N7. An import and a matcher run each get a new random UUID, an entry session keeps the IRI the app minted for it, and every act names the runtime that performed it
    decisions/naming.md, row "act". An import and a matcher run, a recheck's and an open's among them, are each a
    urn:uuid:, version 4, new on every run. An entry's session is minted once by the app that took the entry, and the
    entry carries it, so its records' names (N2) are the same on every run. Nothing else is random. Each act says
    prov:wasAssociatedWith the runtime that performed it, a prov:SoftwareAgent named as N8 names a checkout:
    https://github.com/jayostis/cascade-runtime-js/tree/<commit>/ for the reference runtime, written
    https://github.com/jayostis/cascade-runtime-js/tree/<commit>/#uncommitted for a build with uncommitted changes and
    https://github.com/jayostis/cascade-runtime-js#unidentified for one whose commit it cannot read. A matcher run is a
    cascade:MatcherRun and a prov:Activity, prov:wasInformedBy the import or entry session whose records it takes, and is
    written only when it writes something else. The kit's check 4 holds each of a replay's acts to it.
    A sync is a new random UUID too, a cascade:SyncFromAnotherWriter and a prov:Activity, whose examples are sync.feature's.

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
    For a urn:uuid: name, the UUID; for an ni:///sha-256; name, the hash in lowercase hex. An RDF file adds .ttl; a stored
    document adds nothing. The folder and the fan-out are the layout's, pod-layout.ttl.

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
          OPTIONAL { GRAPH ?file { ?thing a ?type FILTER (?type IN (cascade:AllergyOrIntolerance, prov:Entity)) } }
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
        | <ni:///sha-256;E64aGZVmGmEPgF7RM5roCn_8WdUdfQAgE1LC9RS2V4E> | "13ae1a1995661a610f805ed1339ae80a7ffc59d51d7d00201352c2f514b65781.ttl" |
        | <ni:///sha-256;8fNT3HoCWsm3G8msEdsnmRrSMiceLQPpXFV4a606pMo> | "f1f353dc7a025ac9b71bc9ac11db27991ad232271e2d03e95c55786bad3aa4ca.ttl" |
        | <ni:///sha-256;49M-53sf1aFpJGzpGpsKgRERjOpKg4VWYaHCBFi7Gqc> | "e3d33ee77b1fd5a169246ce91a9b0a8111118cea4a83855661a1c20458bb1aa7.ttl" |
        | <ni:///sha-256;vChKl5qj9w9FL5DDK5x8C0QAMfvHR_UKT51QqsupY4U> | "bc284a979aa3f70f452f90c32b9c7c0b440031fbc747f50a4f9d50aacba96385.ttl" |
        | <ni:///sha-256;K96dQ7NMCx_qaokgjdYAocBi7_dSJVtKQmYSfWR4rRc> | "2bde9d43b34c0b1fea6a89208dd600a1c062eff752255b4a4266127d6478ad17.ttl" |
        | <ni:///sha-256;BAt9YpIrH17dd8_pYoWl5kIAmfZI4pkKRTV1u7JSRnk> | "040b7d62922b1f5edd77cfe96285a5e6420099f648e2990a453575bbb2524679.ttl" |
        | <ni:///sha-256;HgLQlJLSGhMq7xC5CYdLQEFVzvepvRrLiCGzeI65KI0> | "1e02d09492d21a132aef10b909874b404155cef7a9bd1acb8821b3788eb9288d.ttl" |
        | <ni:///sha-256;BMVJZrtTlT-XS2y6CvRWFW3r9Pi9GmNMlC-jzs1doZs> | "04c54966bb53953f974b6cba0af456156debf4f8bd1a634c942fa3cecd5da19b.ttl" |
        |                                                             | "2bde9d43b34c0b1fea6a89208dd600a1c062eff752255b4a4266127d6478ad17"     |
        |                                                             | "040b7d62922b1f5edd77cfe96285a5e6420099f648e2990a453575bbb2524679"     |
        |                                                             | "1e02d09492d21a132aef10b909874b404155cef7a9bd1acb8821b3788eb9288d"     |
        |                                                             | "04c54966bb53953f974b6cba0af456156debf4f8bd1a634c942fa3cecd5da19b"     |

  Rule: N10. A person's judgment keeps the IRI its input gives it
    A judgment a person makes arrives with its name: whoever made it minted that once, as the subject's ID was minted. A
    runtime files it under that IRI and gives it no other; it is neither a new random UUID nor named by a rule. So a
    judgment can name another person's judgment, and an answer can name it, on every run.

    Example: a person's About and its retraction are each filed under the IRI they arrived with, in their own step's file
      Given a new pod for Cleo on 2026-03-01 at 09:00
      And Cleo files the judgment "about-r" on 2026-03-04 at 07:00
      When Cleo files the judgment "retract-about-r" on 2026-03-04 at 12:00
      When the query is:
        """
        SELECT ?step ?judgment ?verdict WHERE {
          GRAPH <urn:cascade:steps> { ?step prov:generated ?file }
          GRAPH ?file { ?judgment a cascade:Judgment OPTIONAL { ?judgment cascade:verdict ?verdict } }
          FILTER (?judgment IN (<urn:uuid:b8d3f1a7-2c69-4e5b-9f14-3a7e6d2c8b91>, <urn:uuid:f2b6d9a4-7e3c-4815-b9d7-5a8e2c6f1d43>))
        }
        """
      Then it answers:
        | step                               | judgment                                        | verdict       |
        | <urn:cascade:step:about-r>         | <urn:uuid:b8d3f1a7-2c69-4e5b-9f14-3a7e6d2c8b91> | cascade:About |
        | <urn:cascade:step:retract-about-r> | <urn:uuid:f2b6d9a4-7e3c-4815-b9d7-5a8e2c6f1d43> |               |

  Rule: N11. A mapping row is named from its subject, its predicate and its object
    cascade:TableRowNamingRule. Its IRI is its SSSOM record_id, and the rule's inputs, in this order, are the IRIs of
    its owl:annotatedSource, owl:annotatedProperty and owl:annotatedTarget. A row in two versions has one name in both.

    A panel member row (cascade:PanelMembers) has a fourth input, the canonical lexical form of its cascade:panelSequence (no
    sign, no leading zeros), because LOINC lists a member of a panel at two sequences, and the two places are two rows.

    No example shows this rule, because no step writes a row. The vocabulary's tests check every row of every kit and
    vector against it.

  Rule: N12. A table version is named from its series, the version it revises and its rows
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
    cites a variant's entry as <variants.ttl#hex>.

    No example shows this rule, because a query reads an entry's IRI resolved against the view's address, and the
    derived state, which examples query, holds the placeholder. The kit's
    check 6 holds every view a replay writes to it, and tests/vectors/naming/ names an entry.

  Rule: N14. Every act leaves one snapshot, chained to the writer's previous one
    decisions/naming.md, row "snapshot". A node in the act's own file, a cascade:Snapshot, prov:wasGeneratedBy the act
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
