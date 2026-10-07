Feature: Arrivals
  Which arrivals a runtime writes, and what each writes: when an import brings a document, an entry brings drafts, or
  the pod is created; and which views the build writes.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Ada
  imports Apple Health exports of four allergies (peanut, latex, shellfish, mango) from one hospital, and later
  exports that change them. Ben enters a peanut allergy and an asthma by hand. Finn brings exports, downloads and
  entries a runtime must refuse, two allergies of one code, and a C-CDA download of one allergy.

  Rule: A1. A document whose bytes the pod already keeps brings nothing new
    It is not converted, and nothing is written. The example saves no Bridge output for it, so a runtime that converted
    it would have none.

    Example: an export bringing a document the pod already keeps writes nothing
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "same-bytes" is imported on 2026-01-03 at 10:00
      Then that step wrote no file

  Rule: A2. A record's first arrival writes the record, its version, and a revision with no prov:wasRevisionOf

    Example: each record's first arrival is its first version and a revision that follows none
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      Then the records have these revisions:
        | record              | arrived             | version | after |
        | allergy "Peanut"    | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Latex"     | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Shellfish" | 2026-01-02 at 10:00 | 1       |       |
        | allergy "Mango"     | 2026-01-02 at 10:00 | 1       |       |

  Rule: A3. An arrival whose source version a revision of the record already carries writes no revision
    The source version is the arrival's pav:version. No revision is written even if the content differs.

    Example: the latex allergy arrives again under a source version it already has, with other content
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "known-source-version" is imported on 2026-01-04 at 10:00
      Then allergy "Latex" has these revisions:
        | arrived             | version | after |
        | 2026-01-02 at 10:00 | 1       |       |

  Rule: A4. An arrival whose version is the one the record is at writes no revision
    Even under a new source version.

    Example: the peanut allergy arrives again unchanged under a new source version
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "current-version-again" is imported on 2026-01-05 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | after |
        | 2026-01-02 at 10:00 | 1       |       |

  Rule: A5. Any other arrival writes a revision after the record's last one

    Example: new content under a new source version is a revision after the last
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "new-content" is imported on 2026-01-06 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | status   | after               |
        | 2026-01-02 at 10:00 | 1       | active   |                     |
        | 2026-01-06 at 10:00 | 2       | inactive | 2026-01-02 at 10:00 |

  Rule: A6. Arrivals with no source version are told apart by their content alone
    So, by A4, one with the content the record is at writes no revision.

    Example: with no source version, new content is a revision and the content the record is at is none
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "no-source-version" is imported on 2026-01-07 at 10:00
      When the export "no-source-version-again" is imported on 2026-01-07 at 12:00
      Then allergy "Shellfish" has these revisions:
        | arrived             | version | status   | after               |
        | 2026-01-02 at 10:00 | 1       | active   |                     |
        | 2026-01-07 at 10:00 | 2       | inactive | 2026-01-02 at 10:00 |

  Rule: A7. A change that is undone at its source reuses the earlier version
    The new revision points at it.

    Example: the peanut allergy changes and changes back, and its third revision sets its first version again
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      When the export "change-undone" is imported on 2026-01-08 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | status   | after               |
        | 2026-01-02 at 10:00 | 1       | active   |                     |
        | 2026-01-06 at 10:00 | 2       | inactive | 2026-01-02 at 10:00 |
        | 2026-01-08 at 10:00 | 1       | active   | 2026-01-06 at 10:00 |

  Rule: A8. A record that is missing from a later export gets nothing written, and nothing of it goes

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

    Example: a revision holds its own five statements and its arrival's, the import that made it shown as its step
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
          GRAPH ?file { ?revision rec:revisionOf <urn:uuid:ce5ac62c-8a4a-8ee4-b7ac-c9f3172d9f82> ; ?predicate ?object }
          BIND(IF(sameTerm(?object, ?import), <urn:cascade:step:first-export>, ?object) AS ?value)
        }
        """
      Then it answers:
        | predicate            | value                                |
        | rdf:type             | rec:Revision                         |
        | rec:revisionOf       | allergy "Peanut"                     |
        | rec:version          | version 1 of allergy "Peanut"        |
        | prov:generatedAtTime | "2026-01-02T10:00:00Z"^^xsd:dateTime |
        | prov:wasGeneratedBy  | <urn:cascade:step:first-export>      |
        | pav:version          | "1"                                  |
        | pav:lastUpdateOn     | "2025-12-01T00:00:00Z"^^xsd:dateTime |
        | bridge:selector      | ""                                   |
        | prov:wasDerivedFrom  | the document of allergy "Peanut"     |

  Rule: A10. A document is kept when it wrote a revision or the Bridge raised findings on it
    Kept is its bytes under attachments/, and its description. Otherwise nothing of it is written.

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
      When the export "known-source-version" is imported on 2026-01-04 at 10:00
      Then that step wrote no file
      And the pod neither names nor stores the document "known-source-version/apple_health_export/clinical-records/AllergyIntolerance-latex.json"

  Rule: A11. An import that kept any document writes its description once
    That description is the label, the start and the association the Bridge gave, and prov:used for each kept document.
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
        | prov:used                 | the document of allergy "Peanut"     |
        | prov:used                 | the document of allergy "Latex"      |
        | prov:used                 | the document of allergy "Shellfish"  |
        | prov:used                 | the document of allergy "Mango"      |

    Example: an import that kept no document writes nothing, not even itself
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "known-source-version" is imported on 2026-01-04 at 10:00
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
        | predicate                 | value                                  |
        | rdf:type                  | prov:Activity                          |
        | rdfs:label                | "C-CDA download"                       |
        | prov:startedAtTime        | "2026-06-07T09:00:00Z"^^xsd:dateTime   |
        | prov:qualifiedAssociation | "ccda"                                 |
        | prov:used                 | the document "allergy-summary.xml"     |

  Rule: A12. An entry writes its session's description
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
            ?revision a rec:Revision ; rec:revisionOf ?record ; rec:version ?version ; prov:generatedAtTime ?at ;
              prov:wasGeneratedBy ?session .
          }
          OPTIONAL { ?revision prov:wasRevisionOf ?previous }
        }
        """
      Then it answers:
        | record             | version                         | at                                   | sessionStarted                       | sessionLabel                 | previous |
        | allergy "Peanut"   | version 1 of allergy "Peanut"   | "2026-02-01T08:30:00Z"^^xsd:dateTime | "2026-02-01T08:30:00Z"^^xsd:dateTime | "entered in the Cascade app" |          |
        | condition "Asthma" | version 1 of condition "Asthma" | "2026-02-01T08:30:00Z"^^xsd:dateTime | "2026-02-01T08:30:00Z"^^xsd:dateTime | "entered in the Cascade app" |          |

  Rule: A13. The pod's creation writes the subject as a rec:Subject
    With it, the owner's profile, saying only who the owner is, where the pod's root is and where the preferences file
    is, and the preferences file, saying only that it is one and where the owner's type index is. The build writes the
    type index, from the views it writes (A15).

    Example: the pod's creation files its subject
      Given a new pod for Ben on 2026-02-01 at 08:00
      When the query is:
        """
        SELECT ?subject WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:pod> prov:generated ?file }
          GRAPH ?file { ?subject a rec:Subject }
        }
        """
      Then it answers:
        | subject |
        | Ben     |

  Rule: A14. Some steps are refused, and a refused step writes no revision and no import
    Refused are: an export or a download no importer recognises, or one its importer cannot read, as an Apple Health
    export whose export.xml it cannot read or a downloaded file that is not well-formed; a document no adapter of its
    media type accepts, as a CDA that is not a C-CDA, or one the Bridge fails on (a bridge:documentFailure); a graph holding a statement about no record,
    version, arrival, document or import; a record or draft of a type the pod files nowhere; one import's documents
    disagreeing on the import's description; an entry holding other than one activity; and an entry whose activity
    states a property by which the layout files an activity elsewhere than an entry's.

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

  Rule: A15. The build writes a view once the pod holds a record of its kind, or the view holds an entry
    And at every build after, so nothing a build wrote goes stale: records are never removed, and a patient-profile
    view whose Abouts are all retracted is written with no entry. The type index registers only the views written,
    and the labels file is written always. So a kind the layout adds changes no pod that holds none of it.

    Example: a pod of an allergy and a condition holds those two views and the labels, and no other
      Given a new pod for Ben on 2026-02-01 at 08:00
      When Ben enters "entry" on 2026-02-01 at 08:30
      And the query is:
        """
        SELECT ?view WHERE {
          GRAPH ?view { ?view a rec:View }
        }
        """
      Then it answers:
        | view                                          |
        | <https://pod.example/clinical/allergies.ttl>  |
        | <https://pod.example/clinical/conditions.ttl> |
        | <https://pod.example/clinical/labels.ttl>     |
