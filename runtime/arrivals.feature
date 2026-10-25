Feature: Arrivals
  Which arrivals a runtime writes, and what each writes: when an import brings a document, an entry brings drafts, an
  app connects to a server, or the pod is created; and which views the build writes.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Ada
  imports Apple Health exports of four allergies (peanut, latex, shellfish, mango) from one hospital, and later
  exports that change them. Ben enters a peanut allergy and an asthma by hand. Finn brings exports, downloads and
  entries a runtime must refuse, two allergies of one code, a C-CDA download of one allergy, and a pull from his
  hospital, whose FHIR server his app connects to; then pulls of his allergies before and after the hospital restored
  a backup, and pulls on a clock that ran behind.

  Rule: A1. A document whose bytes the pod already keeps brings nothing new
    decisions/naming.md, row "document, finding", and decisions/performance.md, row "content names and the held-state rule".
    It is not converted, and nothing is written. The example saves no Bridge output for it, so a runtime that converted
    it would have none.

    Example: an export bringing a document the pod already keeps writes nothing
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "same-bytes" is imported on 2026-01-03 at 10:00
      Then that step wrote no file

  Rule: A2. A record's first arrival writes the record, its version, and a revision with no prov:wasRevisionOf
    decisions/currency.md, row "what an arrival writes".

    Example: each record's first arrival is its first version and a revision that follows none
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then the records have these revisions:
        | record              | arrived             | version | after |
        | allergy "Peanut"    | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Latex"     | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Shellfish" | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Mango"     | 2026-01-02 at 10:00 | 1       |       |

  Rule: A3. An arrival whose version, source version and source change time a revision of the record holds writes no revision
    decisions/currency.md, rows "what an arrival writes" and "source's own version"; decisions/performance.md, row "content names and the held-state rule".
    The source version is the arrival's pav:version and its change
    time its pav:lastUpdateOn. So does an arrival that carries no source change time and whose version the record
    holds, whatever stamp the revision holding it carries. Either holds whether or not the arrival would be current: it
    would be only if a judgment removed the revision that holds its state, and writing it again would undo the
    judgment. A source version alone tells nothing apart.

    Example: an older state the record holds arrives again after a newer one, and writes nothing
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      When the export "first-export" is imported on 2026-01-09 at 10:00 (second-import)
      Then allergy "Peanut" has these revisions:
        | arrived             | version | clinical status | after               |
        | 2026-01-02 at 10:00 | 1       | active          |                     |
        | 2026-01-06 at 10:00 | 2       | inactive        | 2026-01-02 at 10:00 |

    Example: the latex allergy arrives under a source version it already has, with other content, and is a revision
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "known-source-version" is imported on 2026-01-04 at 10:00
      Then allergy "Latex" has these revisions:
        | arrived             | version | after               |
        | 2026-01-02 at 10:00 | 1       |                     |
        | 2026-01-04 at 10:00 | 2       | 2026-01-02 at 10:00 |

  Rule: A4. An arrival whose version is the record's current version writes no revision
    decisions/currency.md, row "what an arrival writes"; decisions/performance.md, row "content names and the held-state rule".
    Even under a new source version or a new source change time.
    The record's current version is its current revision's, as the ladder picks it before the step (C2).

    Example: the peanut allergy arrives again unchanged under a new source version
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "current-version-again" is imported on 2026-01-05 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | after |
        | 2026-01-02 at 10:00 | 1       |       |

  Rule: A5. Any other arrival writes a revision after each of the record's heads
    decisions/currency.md, rows "what an arrival writes" and "heads".
    Its prov:wasRevisionOf names each head, as a git merge names each parent: one, unless two writers revised the
    record apart (S6).

    Example: new content under a new source version is a revision after the last
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "new-content" is imported on 2026-01-06 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | clinical status | after               |
        | 2026-01-02 at 10:00 | 1       | active          |                     |
        | 2026-01-06 at 10:00 | 2       | inactive        | 2026-01-02 at 10:00 |

  Rule: A6. Arrivals with no source version are told apart by their content alone
    decisions/currency.md, row "what an arrival writes".
    So, by A4, one with the content the record is at now writes no revision.

    Example: with no source version, new content is a revision and the content the record is at is none
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "no-source-version" is imported on 2026-01-07 at 10:00
      When the export "no-source-version-again" is imported on 2026-01-07 at 12:00
      Then allergy "Shellfish" has these revisions:
        | arrived             | version | clinical status | after               |
        | 2026-01-02 at 10:00 | 1       | active          |                     |
        | 2026-01-07 at 10:00 | 2       | inactive        | 2026-01-02 at 10:00 |

  Rule: A7. A change that is undone at its source reuses the earlier version
    decisions/naming.md, row "version".
    The new revision points at it.

    Example: the peanut allergy changes and changes back, and its third revision sets its first version again
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      When the export "change-undone" is imported on 2026-01-08 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | clinical status | after               |
        | 2026-01-02 at 10:00 | 1       | active          |                     |
        | 2026-01-06 at 10:00 | 2       | inactive        | 2026-01-02 at 10:00 |
        | 2026-01-08 at 10:00 | 1       | active          | 2026-01-06 at 10:00 |

  Rule: A8. A record that is missing from a later export gets nothing written, and nothing of it goes
    No note rules this.

    Example: three allergies missing from a later export keep what they had
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "same-bytes" is imported on 2026-01-03 at 10:00
      Then the records have these revisions:
        | record              | arrived             | version | after |
        | allergy "Peanut"    | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Latex"     | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Shellfish" | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Mango"     | 2026-01-02 at 10:00 | 1       |       |

  Rule: A9. A revision holds exactly the triples listed in N4
    decisions/naming.md, row "revision".

    Example: a revision holds its own six statements and its arrival's, the import that made it shown as its step
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      When the query is:
        """
        SELECT ?predicate ?value WHERE {
          { SELECT DISTINCT ?import WHERE {
            GRAPH <urn:cascade:steps> { <urn:cascade:step:first-export> prov:generated ?importFile }
            GRAPH ?importFile { ?import prov:used ?document }
          } }
          GRAPH <urn:cascade:steps> { <urn:cascade:step:first-export> prov:generated ?file }
          GRAPH ?file { ?revision cascade:revisionOf <urn:uuid:beaefb13-def8-8f7f-882d-eff4a1ee11d9> ; ?predicate ?object }
          BIND(IF(sameTerm(?object, ?import), <urn:cascade:step:first-export>,
                  IF(STRSTARTS(STR(?object), CONCAT(STR(?revision), "#")), STRAFTER(STR(?object), STR(?revision)), ?object)) AS ?value)
        }
        """
      Then it answers:
        | predicate            | value                                |
        | rdf:type             | cascade:Revision                     |
        | cascade:revisionOf   | allergy "Peanut"                     |
        | cascade:version      | version 1 of allergy "Peanut"        |
        | prov:generatedAtTime | "2026-01-02T10:00:00Z"^^xsd:dateTime |
        | cascade:observedAsOf | "2026-01-02T10:00:00Z"^^xsd:dateTime |
        | prov:wasGeneratedBy  | <urn:cascade:step:first-export>      |
        | pav:version          | "1"                                  |
        | pav:lastUpdateOn     | "2025-12-01T00:00:00Z"^^xsd:dateTime |
        | oa:hasSelector       | "#selector"                          |
        | oa:hasSource         | the document of allergy "Peanut"     |
        | prov:wasDerivedFrom  | the document of allergy "Peanut"     |

  Rule: A10. A document is kept when it wrote a revision, the Bridge raised findings on it, or it reported an older state
    decisions/currency.md, row "a source that goes backwards".
    Kept is its bytes under attachments/, and its description. Otherwise nothing of it is written. A document with an
    arrival that a finding that its source reported older states names (A18) is kept, though it wrote no revision: a
    finding is something kept.

    Example: a document that wrote no revision is kept for the findings the Bridge raised on it
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "current-version-again" is imported on 2026-01-05 at 10:00
      When the query is:
        """
        SELECT ?document (COUNT(DISTINCT ?attachment) AS ?storedFiles) ?usedByTheImport WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:current-version-again> prov:generated ?description }
          GRAPH ?description { ?document a prov:Entity }
          OPTIONAL {
            GRAPH <urn:cascade:steps> { <urn:cascade:step:current-version-again> prov:generated ?attachment }
            FILTER NOT EXISTS { GRAPH ?attachment { ?s ?p ?o } }
          }
          BIND(EXISTS {
            GRAPH <urn:cascade:steps> { <urn:cascade:step:current-version-again> prov:generated ?importFile }
            GRAPH ?importFile { ?import a prov:Activity ; prov:used ?document }
          } AS ?usedByTheImport)
        }
        GROUP BY ?document ?usedByTheImport
        """
      Then it answers:
        | document                                                                                                 | storedFiles | usedByTheImport |
        | the document "current-version-again/apple_health_export/clinical-records/AllergyIntolerance-peanut.json" | 1           | true            |

    Example: a document that wrote no revision and raised no findings is not kept
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "no-source-version" is imported on 2026-01-07 at 10:00
      When the export "no-source-version-again" is imported on 2026-01-07 at 12:00
      Then that step wrote no file
      And the pod neither names nor stores the document "no-source-version-again/apple_health_export/clinical-records/AllergyIntolerance-shellfish.json"

  Rule: A11. An import that kept any document writes its description once
    decisions/naming.md, row "act".
    That description is the label, the start and the association the Bridge gave, the runtime that performed the import
    (N7), and prov:used for each kept document. The import's snapshot (N14) is in its file.
    An import that kept nothing writes nothing, not even itself.

    Example: an import writes its label, its start, its association and each document it kept
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      When the query is:
        """
        SELECT ?predicate ?value WHERE {
          { SELECT DISTINCT ?import ?file WHERE {
            GRAPH <urn:cascade:steps> { <urn:cascade:step:first-export> prov:generated ?file }
            GRAPH ?file { ?import prov:used ?document }
          } }
          GRAPH ?file {
            { ?import ?predicate ?value FILTER (!isBlank(?value)) }
            UNION
            { ?import prov:qualifiedAssociation/prov:hadPlan/rdfs:label ?value BIND(prov:qualifiedAssociation AS ?predicate) }
          }
        }
        """
      Then it answers:
        | predicate                 | value                                |
        | rdf:type                  | prov:Activity                        |
        | rdfs:label                | "Apple Health export"                |
        | prov:startedAtTime        | "2026-01-02T10:00:00Z"^^xsd:dateTime |
        | prov:qualifiedAssociation | "fhir-r4"                            |
        | prov:wasAssociatedWith    | the runtime                          |
        | prov:used                 | the document of allergy "Peanut"     |
        | prov:used                 | the document of allergy "Latex"      |
        | prov:used                 | the document of allergy "Shellfish"  |
        | prov:used                 | the document of allergy "Mango"      |

    Example: an import that kept no document writes nothing, not even itself
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "no-source-version" is imported on 2026-01-07 at 10:00
      When the export "no-source-version-again" is imported on 2026-01-07 at 12:00
      Then that step wrote no file

    Example: a download's import writes its label, its start, its association and the document it kept
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the download "allergy-summary.xml" is imported on 2026-06-07 at 09:00
      When the query is:
        """
        SELECT ?predicate ?value WHERE {
          { SELECT DISTINCT ?import ?file WHERE {
            GRAPH <urn:cascade:steps> { <urn:cascade:step:allergy-summary.xml> prov:generated ?file }
            GRAPH ?file { ?import prov:used ?document }
          } }
          GRAPH ?file {
            { ?import ?predicate ?value FILTER (!isBlank(?value)) }
            UNION
            { ?import prov:qualifiedAssociation/prov:hadPlan/rdfs:label ?value BIND(prov:qualifiedAssociation AS ?predicate) }
          }
        }
        """
      Then it answers:
        | predicate                 | value                                |
        | rdf:type                  | prov:Activity                        |
        | rdfs:label                | "C-CDA download"                     |
        | prov:startedAtTime        | "2026-06-07T09:00:00Z"^^xsd:dateTime |
        | prov:qualifiedAssociation | "ccda"                               |
        | prov:wasAssociatedWith    | the runtime                          |
        | prov:used                 | the document "allergy-summary.xml"   |

    Example: a pull's import uses its bundle.json as its one document, and its pull.json as none
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the pull "allergy-pull" is imported on 2026-06-08 at 09:00
      When the query is:
        """
        SELECT ?predicate ?value WHERE {
          { SELECT DISTINCT ?import ?file WHERE {
            GRAPH <urn:cascade:steps> { <urn:cascade:step:allergy-pull> prov:generated ?file }
            GRAPH ?file { ?import prov:used ?document }
          } }
          GRAPH ?file {
            { ?import ?predicate ?value FILTER (!isBlank(?value)) }
            UNION
            { ?import prov:qualifiedAssociation/prov:hadPlan/rdfs:label ?value BIND(prov:qualifiedAssociation AS ?predicate) }
          }
        }
        """
      Then it answers:
        | predicate                 | value                                   |
        | rdf:type                  | prov:Activity                           |
        | rdfs:label                | "FHIR pull"                             |
        | prov:startedAtTime        | "2026-06-08T09:00:00Z"^^xsd:dateTime    |
        | prov:qualifiedAssociation | "fhir-r4"                               |
        | prov:wasAssociatedWith    | the runtime                             |
        | prov:used                 | the document "allergy-pull/bundle.json" |
      And the pod neither names nor stores the document "allergy-pull/pull.json"

  Rule: A12. An entry writes its session's description
    decisions/naming.md, rows "record from an entry" and "act".
    Each draft becomes a record (N2) with its version and a first revision, at the session's start, generated by the
    session.

    Example: an entry writes its session and, for each draft, a record with its version and a first revision
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      When the query is:
        """
        SELECT ?record ?version ?at ?sessionStarted ?sessionLabel ?previous WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:entry> prov:generated ?sessionFile }
          GRAPH <urn:cascade:steps> { <urn:cascade:step:entry> prov:generated ?revisionFile }
          GRAPH ?sessionFile { ?session a prov:Activity ; prov:startedAtTime ?sessionStarted ; rdfs:label ?sessionLabel }
          GRAPH ?revisionFile {
            ?revision a cascade:Revision ; cascade:revisionOf ?record ; cascade:version ?version ; prov:generatedAtTime ?at ;
              prov:wasGeneratedBy ?session .
          }
          OPTIONAL { ?revision prov:wasRevisionOf ?previous }
        }
        """
      Then it answers:
        | record             | version                         | at                                   | sessionStarted                       | sessionLabel                 | previous |
        | allergy "Peanut"   | version 1 of allergy "Peanut"   | "2026-02-01T08:30:00Z"^^xsd:dateTime | "2026-02-01T08:30:00Z"^^xsd:dateTime | "entered in the Cascade app" |          |
        | condition "Asthma" | version 1 of condition "Asthma" | "2026-02-01T08:30:00Z"^^xsd:dateTime | "2026-02-01T08:30:00Z"^^xsd:dateTime | "entered in the Cascade app" |          |

  Rule: A13. The pod's creation writes the subject as a cascade:Subject
    decisions/naming.md, row "pod identity".
    With it, the owner's profile, saying only who the owner is, where the pod's root is and where the preferences file
    is, and the preferences file, saying only that it is one and where the owner's type index is. The build writes the
    type index, from the views it writes (A15).

    Example: the pod's creation files its subject
      Given a new pod for Ben on 2026-02-01 at 08:00
      When the query is:
        """
        SELECT ?subject WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:pod> prov:generated ?file }
          GRAPH ?file { ?subject a cascade:Subject }
        }
        """
      Then it answers:
        | subject |
        | Ben     |

  Rule: A14. Some steps are refused, and a refused step writes no revision and no import
    No note rules this.
    Refused are: an export, a download or a pull no importer recognises, or one its importer cannot read, as an Apple
    Health export whose export.xml it cannot read, a downloaded file that is not well-formed or a pull whose pull.json
    names no FHIR base; a connect whose connect.json names no FHIR base that can be normalised or no client id, whose
    capability.json is no CapabilityStatement, or whose smart-configuration.json is no JSON object; a document no
    adapter of its media type accepts, as a CDA that is not a C-CDA, or one the Bridge fails on (a
    bridge:documentFailure); a graph holding a statement about no record, version, arrival, document or import; a
    record or draft of a type the pod files nowhere; one import's documents disagreeing on the import's description; an
    entry holding other than one activity; and an entry whose activity states a property by which the layout files an
    activity elsewhere than an entry's.

    Example: a Bridge graph holding a statement about nothing the pod files
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the export "stray-statement" is imported on 2026-06-02 at 09:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: a record of a type the pod files nowhere
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the export "type-filed-nowhere" is imported on 2026-06-03 at 09:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: one import's documents disagreeing on the import's description, so not even the agreeing one is written
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the export "import-disagreement" is imported on 2026-06-04 at 09:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: a downloaded file that is not well-formed
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the download "not-well-formed.xml" is imported on 2026-06-04 at 10:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: a downloaded CDA that is not a C-CDA, which no adapter accepts
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the download "not-a-ccda.xml" is imported on 2026-06-04 at 11:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: a pull whose pull.json names no FHIR base
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the pull "pull-without-base" is imported on 2026-06-08 at 10:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: a connect whose connect.json names no client id
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the connect "connect-without-client-id" is made on 2026-06-08 at 08:55
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: an entry holding two activities
      Given a new pod for Finn on 2026-06-01 at 09:00
      When Finn enters "entry-of-two-activities" on 2026-06-05 at 09:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

    Example: an entry whose session states prov:used, by which the layout files an import
      Given a new pod for Finn on 2026-06-01 at 09:00
      When Finn enters "entry-session-filed-elsewhere" on 2026-06-06 at 09:00
      Then that step is refused
      And that step wrote no file
      And the pod holds no revision

  Rule: A15. The build writes a view once the pod holds a record of its kind, and at every build after
    No note rules this.
    Records are never removed, so nothing a build wrote goes stale. The labels file, and each view pod-layout.ttl marks
    cascade:writtenAlways, as the patient-profile view, are written at every build: a pod always has a subject. The type
    index registers only the views written. So a kind the layout adds changes no pod that holds none of it.

    Example: a pod of an allergy and a condition holds those two views, the patient-profile view and the labels, and no other
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      And the query is:
        """
        SELECT ?view WHERE {
          GRAPH ?view { ?view a cascade:View }
        }
        """
      Then it answers:
        | view                                               |
        | <https://pod.example/clinical/allergies.ttl>       |
        | <https://pod.example/clinical/conditions.ttl>      |
        | <https://pod.example/clinical/labels.ttl>          |
        | <https://pod.example/clinical/patient-profile.ttl> |

  Rule: A16. A connect writes its act and a version of its server's record holding what the server reported
    decisions/republishing-sources.md, row "server"; decisions/naming.md, row "server, organisation".
    A connect is a cascade:ConnectToServer and a prov:Activity, named
    as N7 says, started at the step's time. It writes its server's record, named by cascade:ServerNamingRule from
    connect.json's fhirBase and stating that base, normalised, as its cascade:serverBaseUrl, unless the pod holds it;
    and a version of it, with a revision as A2 to A5 say, generated by the connect. The version holds what
    capability.json, the server's CapabilityStatement, says, as the server wrote it: implementation.url as
    cascade:selfAssertedBaseUrl; software.name and software.version as cascade:serverSoftwareName and
    cascade:serverSoftwareVersion; and as cascade:authorizationEndpoint, the authorization_endpoint of
    smart-configuration.json, the server's SMART App Launch 2 discovery document, or, where the connect saved none or it
    names none, the authorize valueUri of the oauth-uris extension on the security of capability.json's first rest
    whose mode is server; each only where it is a string that is not empty. It holds connect.json's clientId as
    cascade:connectClientId. A connect whose version is the one the server's record is
    at writes nothing, not even itself, as an import that kept nothing; a connect with no pull is complete.

    Example: a connect's version holds what the server reported and the client id it was reported to
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the connect "hospital" is made on 2026-06-08 at 08:55
      When the query is:
        """
        SELECT ?predicate ?value WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital> prov:generated ?file }
          GRAPH ?file { ?version prov:specializationOf ?server ; ?predicate ?value }
        }
        """
      Then it answers:
        | predicate                     | value                                                     |
        | prov:specializationOf         | <urn:uuid:4461f3ef-4caf-8a24-93f1-da07a8455cc5>           |
        | cascade:selfAssertedBaseUrl   | "https://fhir.example-hospital.example/api/FHIR/R4/"      |
        | cascade:authorizationEndpoint | "https://login.example-hospital.example/oauth2/authorize" |
        | cascade:serverSoftwareName    | "Example EHR"                                             |
        | cascade:serverSoftwareVersion | "2026.2"                                                  |
        | cascade:connectClientId       | "cascade-app"                                             |

    Example: a connect is an act that generated its server's revision, and names the runtime that performed it
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the connect "hospital" is made on 2026-06-08 at 08:55
      When the query is:
        """
        SELECT ?predicate ?value WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital> prov:generated ?revisionFile, ?actFile }
          GRAPH ?revisionFile { [] cascade:revisionOf ?server ; prov:wasGeneratedBy ?connect }
          GRAPH ?actFile { ?connect ?predicate ?value }
        }
        """
      Then it answers:
        | predicate              | value                                |
        | rdf:type               | prov:Activity                        |
        | rdf:type               | cascade:ConnectToServer              |
        | prov:startedAtTime     | "2026-06-08T08:55:00Z"^^xsd:dateTime |
        | prov:wasAssociatedWith | the runtime                          |

    Example: a server serving no SMART configuration names its authorization endpoint in its CapabilityStatement
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the connect "hospital-without-smart-configuration" is made on 2026-06-08 at 08:55
      When the query is:
        """
        SELECT ?endpoint WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-without-smart-configuration> prov:generated ?file }
          GRAPH ?file { [] prov:specializationOf ?server ; cascade:authorizationEndpoint ?endpoint }
        }
        """
      Then it answers:
        | endpoint                                                 |
        | "https://fhir.example-hospital.example/oauth2/authorize" |

    Example: a connect reporting what its server's record already says writes nothing
      Given a new pod for Finn on 2026-06-01 at 09:00
      And the connect "hospital" is made on 2026-06-08 at 08:55
      When the connect "hospital" is made on 2026-06-09 at 08:55 (hospital-again)
      Then that step wrote no file

    Example: a connect reporting other than its server's record says writes a revision after the record's last
      Given a new pod for Finn on 2026-06-01 at 09:00
      And the connect "hospital" is made on 2026-06-08 at 08:55
      When the connect "hospital-without-smart-configuration" is made on 2026-06-09 at 08:55
      When the query is:
        """
        SELECT ?server WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital> prov:generated ?first }
          GRAPH ?first { ?previous a cascade:Revision ; cascade:revisionOf ?server }
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-without-smart-configuration> prov:generated ?second }
          GRAPH ?second { [] a cascade:Revision ; cascade:revisionOf ?server ; prov:wasRevisionOf ?previous }
        }
        """
      Then it answers:
        | server                                          |
        | <urn:uuid:4461f3ef-4caf-8a24-93f1-da07a8455cc5> |

    Example: a connect after a pull from its server writes a version and a revision, and not the record again
      Given a new pod for Finn on 2026-06-01 at 09:00
      And the pull "allergy-pull" is imported on 2026-06-08 at 09:00
      When the connect "hospital" is made on 2026-06-08 at 09:30
      When the query is:
        """
        SELECT ?written WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital> prov:generated ?file }
          {
            GRAPH ?file { [] prov:specializationOf <urn:uuid:4461f3ef-4caf-8a24-93f1-da07a8455cc5> }
            BIND ("version" AS ?written)
          } UNION {
            GRAPH ?file { [] a cascade:Revision }
            BIND ("revision" AS ?written)
          } UNION {
            GRAPH ?file { [] a cascade:Server }
            BIND ("record" AS ?written)
          }
        }
        """
      Then it answers:
        | written    |
        | "version"  |
        | "revision" |

  Rule: A17. An import writes the record of each server its kept documents name, with no version, when the pod has none
    decisions/republishing-sources.md, row "server"; decisions/naming.md, row "server, organisation".
    Each document an import keeps (A10) that states a
    cascade:serverBaseUrl, as a pull's and an Apple Health export's do, names a server: the import writes that server's
    record, named and stating its base as A16 says, with no version, unless the pod holds it. So a server a connect
    wrote is not written again, and a server known only from a document has a record with no version. A base URL that
    cannot be normalised names no server, so the import writes no server record for it and is not refused.

    Example: a pull writes the record of the server it came from, with no version
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the pull "allergy-pull" is imported on 2026-06-08 at 09:00
      When the query is:
        """
        SELECT ?server ?base WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:allergy-pull> prov:generated ?file }
          GRAPH ?file { ?server a cascade:Server ; cascade:serverBaseUrl ?base }
          FILTER NOT EXISTS { ?version prov:specializationOf ?server }
        }
        """
      Then it answers:
        | server                                          | base                                       |
        | <urn:uuid:4461f3ef-4caf-8a24-93f1-da07a8455cc5> | "https://fhir.example-hospital.example/r4" |

    Example: a pull after a connect to its server writes no server record
      Given a new pod for Finn on 2026-06-01 at 09:00
      And the connect "hospital" is made on 2026-06-08 at 08:55
      When the pull "allergy-pull" is imported on 2026-06-08 at 09:00
      When the query is:
        """
        SELECT ?server WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:allergy-pull> prov:generated ?file }
          GRAPH ?file { ?server a cascade:Server }
        }
        """
      Then it answers nothing

  Rule: A18. An import whose source reports states older than it reported before files one finding naming each record that went back
    decisions/currency.md, row "a source that goes backwards"; decisions/performance.md, row "findings bounded".
    A live pull is a document retrieved on a date
    (pav:retrievedOn) that answers as of no other instant (cascade:answeredAsOf); two are of one source when both name
    one transmitter, the same agent, or neither names one, as the ladder reads them (C2). An arrival from a live pull
    that carries a source change time, of a record holding revisions from live pulls of the same source stamped later,
    contradicts each of those. After its revisions and before its act (W1), the import files one
    cascade:FindingForReview whose oa:hasBody is cascade:SourceReportedOlderStates, whose oa:motivatedBy is
    oa:classifying, whose oa:hasTarget is, for each such arrival, the revision holding its state, the one A3 found or
    the one the import wrote, and whose cascade:contradictedEarlierRevision is each revision it contradicts, so naming
    each earlier act and each record that went back. It names no record a finding the pod holds already names with
    each revision the arrival contradicts, acknowledged or not, and is not filed when it would name none: a repeat pull
    of the rolled-back states files nothing. The current pick is unchanged (C2): a state the record held writes
    nothing, and one it never held is written and ranked below the later stamp. A copy by another path, an export or a
    transmitter's, contradicts nothing. It carries no time and names no act, and is named by cascade:FindingNamingRule
    from its triples.

    Example: a pull after the hospital restored a backup files one finding, and shows the later states still
      The restored pull reports the peanut allergy at its first state, which the pod holds, and the latex allergy at a
      state stamped between the first two pulls, which it never held.

      Given a new pod for Finn on 2026-06-01 at 09:00
      And the pull "hospital-first-pull" is imported on 2026-06-08 at 09:00
      And the pull "hospital-second-pull" is imported on 2026-06-15 at 09:00
      When the pull "hospital-restored-pull" is imported on 2026-06-20 at 09:00
      When the query is:
        """
        SELECT ?record ?older ?contradicted WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-restored-pull> prov:generated ?file }
          GRAPH ?file {
            ?finding oa:hasBody cascade:SourceReportedOlderStates ; oa:motivatedBy oa:classifying ;
                     oa:hasTarget ?olderRevision ; cascade:contradictedEarlierRevision ?contradictedRevision
          }
          ?olderRevision cascade:revisionOf ?record ; cascade:version ?older .
          ?contradictedRevision cascade:revisionOf ?record ; cascade:version ?contradicted .
        }
        """
      Then it answers:
        | record                  | older                                | contradicted                         |
        | allergy SNOMED 91935009 | version 1 of allergy SNOMED 91935009 | version 2 of allergy SNOMED 91935009 |
        | allergy "Latex"         | version 3 of allergy "Latex"         | version 2 of allergy "Latex"         |
      And these records have:
        | record                  | field   | value |
        | allergy SNOMED 91935009 | version | 2     |
        | allergy "Latex"         | version | 2     |

    Example: pulling the rolled-back states again names only the record that went back since
      The pull after the restore left out the mango allergy; the next pull returns it at its first state, beside the
      peanut and latex allergies at the states the earlier finding names.

      Given a new pod for Finn on 2026-06-01 at 09:00
      And the pull "hospital-first-pull" is imported on 2026-06-08 at 09:00
      And the pull "hospital-second-pull" is imported on 2026-06-15 at 09:00
      And the pull "hospital-restored-pull" is imported on 2026-06-20 at 09:00
      When the pull "hospital-restored-pull-again" is imported on 2026-06-21 at 09:00
      When the query is:
        """
        SELECT ?record ?older ?contradicted WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-restored-pull-again> prov:generated ?file }
          GRAPH ?file { ?finding oa:hasTarget ?olderRevision ; cascade:contradictedEarlierRevision ?contradictedRevision }
          ?olderRevision cascade:revisionOf ?record ; cascade:version ?older .
          ?contradictedRevision cascade:revisionOf ?record ; cascade:version ?contradicted .
        }
        """
      Then it answers:
        | record          | older                        | contradicted                 |
        | allergy "Mango" | version 1 of allergy "Mango" | version 2 of allergy "Mango" |

    Example: an export of a state older than the one an earlier export holds files nothing
      Apple Health names itself as the transmitter of each export, so each export is a path of its own, and its copy of
      the peanut allergy stamped 4 January, after the export stamped 5 January, is a stale copy.

      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      When the export "stale-copy" is imported on 2026-01-08 at 10:00
      When the query is:
        """
        SELECT ?finding WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:stale-copy> prov:generated ?file }
          GRAPH ?file { ?finding a cascade:FindingForReview }
        }
        """
      Then it answers nothing

  Rule: A19. An act whose revisions show the writer's clock behind files one finding, unless an act in its first-parent ancestry filed one no one answered
    decisions/currency.md, row "wrong writer clock"; decisions/performance.md, row "findings bounded".
    A revision's observation time is the writer's own clock when it is
    an entry session's start, an act's start, or the pav:retrievedOn of a live pull that names no transmitter (A18).
    Two checks run on each revision an act writes: one whose observation time is the writer's clock and precedes the
    cascade:observedAsOf of a head it names (prov:wasRevisionOf), and one from a live pull that names no transmitter
    whose source change time (pav:lastUpdateOn) is after the pull's pav:retrievedOn, each by at least one whole day; the
    second cannot tell a writer's slow clock from a source's fast one.
    After its revisions and before its act (W1), the act files a cascade:FindingForReview whose oa:hasBody is
    cascade:ClockBehind, whose oa:motivatedBy is oa:classifying, whose oa:hasTarget is each revision either check
    found, and whose cascade:writerClockBehindByAtLeastDays is the greatest whole number of days one of them shows; it
    files none when an act in the first-parent ancestry of its snapshot (cascade:firstParentSnapshot, N14) filed one
    that no person's judgment answers, neither a cascade:Acknowledged whose member is the finding nor a
    cascade:ClockDiscounted whose member is the act that filed it, each standing as C7 reads a person's judgment. So a
    writer has one unanswered at a time, and a clock that stays wrong is found once more after each answer; another
    writer's finding, received by a sync, silences nothing. Its name follows cascade:FindingNamingRule.

    Example: a pull on a clock behind the head it revises files a finding of the days between
      Given a new pod for Finn on 2026-05-31 at 09:00
      And the pull "hospital-unstamped-pull" is imported on 2026-06-10 at 09:00
      When the pull "hospital-pull-on-a-clock-behind" is imported on 2026-06-11 at 09:00
      When the query is:
        """
        SELECT ?days ?record ?version WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-pull-on-a-clock-behind> prov:generated ?file }
          GRAPH ?file {
            ?finding oa:hasBody cascade:ClockBehind ; oa:motivatedBy oa:classifying ;
                     cascade:writerClockBehindByAtLeastDays ?days ; oa:hasTarget ?revision
          }
          ?revision cascade:revisionOf ?record ; cascade:version ?version .
        }
        """
      Then it answers:
        | days | record           | version                       |
        | 9    | allergy "Sesame" | version 2 of allergy "Sesame" |

    Example: a pull returning a record its source stamped after the pull's own time files a finding
      Given a new pod for Finn on 2026-05-31 at 09:00
      When the pull "hospital-pull-stamped-after-it" is imported on 2026-06-12 at 09:00
      When the query is:
        """
        SELECT ?days ?record WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-pull-stamped-after-it> prov:generated ?file }
          GRAPH ?file { ?finding oa:hasBody cascade:ClockBehind ; cascade:writerClockBehindByAtLeastDays ?days ; oa:hasTarget ?revision }
          ?revision cascade:revisionOf ?record .
        }
        """
      Then it answers:
        | days | record           |
        | 5    | allergy "Sesame" |

    Example: a writer whose earlier act filed a clock finding files no second
      Given a new pod for Finn on 2026-05-31 at 09:00
      And the pull "hospital-unstamped-pull" is imported on 2026-06-10 at 09:00
      And the pull "hospital-pull-on-a-clock-behind" is imported on 2026-06-11 at 09:00
      When the pull "hospital-pull-stamped-after-it" is imported on 2026-06-12 at 09:00
      When the query is:
        """
        SELECT ?finding WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-pull-stamped-after-it> prov:generated ?file }
          GRAPH ?file { ?finding a cascade:FindingForReview }
        }
        """
      Then it answers nothing

    Example: a writer whose clock finding the person answered files one more
      Finn discounted the clock of the act that filed the first finding, which answers it.

      Given a new pod for Finn on 2026-05-31 at 09:00
      And the pull "hospital-unstamped-pull" is imported on 2026-06-10 at 09:00
      And the pull "hospital-pull-on-a-clock-behind" is imported on 2026-06-11 at 09:00
      And Finn files the judgment "discount-the-clock-behind" on 2026-06-11 at 12:00
      When the pull "hospital-pull-stamped-after-it" is imported on 2026-06-12 at 09:00
      When the query is:
        """
        SELECT ?days ?record WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-pull-stamped-after-it> prov:generated ?file }
          GRAPH ?file { ?finding oa:hasBody cascade:ClockBehind ; cascade:writerClockBehindByAtLeastDays ?days ; oa:hasTarget ?revision }
          ?revision cascade:revisionOf ?record .
        }
        """
      Then it answers:
        | days | record           |
        | 5    | allergy "Sesame" |

  Rule: A20. A pull writes the record of each Organization it holds, and a lab result names the organization that performed it
    decisions/republishing-sources.md, row "organisation"; decisions/naming.md, row "server, organisation".
    An Organization a pull's Bundle holds at the top of an entry, with an id and a fullUrl that is no urn:uuid, is a
    cascade:Organization record named by cascade:OrganizationNamingRule from the pull's fhirBase, normalised,
    Organization and its id, whatever names it, unless another entry holds an Organization with that id, when neither is
    a record. Like any record from a server it states its cascade:sourceUrl, <base>/Organization/<id>, and its
    cascade:sourceRecordId, and its version holds what the resource says, as A2 to A5 write any record's: its name as
    foaf:name, each identifier as org:identifier, typed by its system, and each address as cascade:organizationAddress.
    A lab result from a pull whose performers name one Organization, as Organization/<id> or <base>/Organization/<id>,
    a version's /_history/ dropped, holds that organization's record as prov:wasAttributedTo on its version. The
    reference alone names it, so the result is attributed whether or not the pull holds the Organization, unlike a
    document's interpretation, whose performer names a record only where it resolves to an Organization of the
    document. A reference made from an entry whose fullUrl is a urn:uuid, to an Organization the pull holds under one,
    or to an id two entries hold an Organization under names none, and performers naming two name none. The
    organization is content of the version, so a later pull naming another performer writes a revision of the same
    record. An organization record is never the subject's (M2).

    Example: a pull's Organization is a record named by its server and id, with a version of what it says
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the pull "hospital-pull-with-a-lab" is imported on 2026-06-08 at 09:00
      When the query is:
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX org: <http://www.w3.org/ns/org#>
        SELECT ?organization ?predicate ?value WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-pull-with-a-lab> prov:generated ?recordFile, ?versionFile }
          GRAPH ?recordFile { ?organization a cascade:Organization }
          GRAPH ?versionFile { [] prov:specializationOf ?organization ; ?predicate ?value }
          FILTER (?predicate != prov:specializationOf)
        }
        """
      Then it answers:
        | organization                                    | predicate                   | value                                             |
        | <urn:uuid:7b40ed6a-7e98-86bb-aa22-26e771ea51a3> | foaf:name                   | "Example Hospital Laboratory"                     |
        | <urn:uuid:7b40ed6a-7e98-86bb-aa22-26e771ea51a3> | org:identifier              | "1234567893"^^<http://hl7.org/fhir/sid/us-npi>    |
        | <urn:uuid:7b40ed6a-7e98-86bb-aa22-26e771ea51a3> | cascade:organizationAddress | "12 Harbour Road, Bellingham, WA 98225"           |

    Example: a pulled lab result's version is attributed to the organization its performer names
      Given a new pod for Finn on 2026-06-01 at 09:00
      When the pull "hospital-pull-with-a-lab" is imported on 2026-06-08 at 09:00
      When the query is:
        """
        SELECT ?organization WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:hospital-pull-with-a-lab> prov:generated ?file }
          GRAPH ?file { [] prov:specializationOf ?lab ; prov:wasAttributedTo ?organization }
          ?lab a cascade:LaboratoryTestResult .
        }
        """
      Then it answers:
        | organization                                    |
        | <urn:uuid:7b40ed6a-7e98-86bb-aa22-26e771ea51a3> |
