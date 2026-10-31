Feature: Priya Natarajan's pod
  The second scenario every runtime must pass, https://github.com/jayostis/cascade-runtime-js/issues/70: one pod built
  from FHIR and C-CDA together, medications and lab results included. Kestrel Harbor Hospital sends Priya's records as
  FHIR, through Apple Health, and as a C-CDA from its patient portal; Fernhill Family Clinic sends only a C-CDA. Each
  planted case P1 to P17 is a rule, and each example reads the pod at the smallest set of steps and lenses at which it
  can fail for its own reason. A record, a profile and a person's judgment are named by the handle expected/handles.json
  gives it: KHF is Kestrel Harbor's FHIR, KHC its C-CDA, FFC Fernhill's C-CDA and APP Priya's own entry. Her app opens
  her pod as it creates it, with the vocabulary's rule list version 18 and the drug products table her medications are
  in (app-drug-products), so every matcher run of her story is the app's.

  Background: Priya's story
    Given a new pod for Priya on 2025-03-29 at 18:40 (E1)
    And the pod is opened with the tables "app-drug-products" on 2025-03-29 at 18:41
    And the export "x-e2" is imported on 2025-03-29 at 18:45:04 (E2)
    And Priya files the judgment "J1" on 2025-03-29 at 18:45:30
    And the matcher runs on the records of "E2" on 2025-03-29 at 18:46 (M1)
    And the download "kestrel-harbor-health-summary.xml" is imported on 2025-04-03 at 09:20:04 (E3)
    And Priya files the judgment "J2" on 2025-04-03 at 09:20:30
    And the matcher runs on the records of "E3" on 2025-04-03 at 09:21 (M2)
    And the download "kestrel-harbor-health-summary-2.xml" is imported on 2025-04-20 at 08:15:04 (E4)
    And the matcher runs on the records of "E4" on 2025-04-20 at 08:15:04 (M3)
    And the download "kestrel-harbor-health-summary-3.xml" is imported on 2025-05-05 at 17:45:04 (E5)
    And the matcher runs on the records of "E5" on 2025-05-05 at 17:45:04 (M4)
    And the download "fernhill-family-clinic-summary.xml" is imported on 2025-05-20 at 18:50:04 (E6)
    And Priya files the judgment "J3" on 2025-05-20 at 18:50:30
    And the matcher runs on the records of "E6" on 2025-05-20 at 18:51 (M5)
    And Priya enters "a1" on 2025-05-20 at 19:30 (E7)
    And the matcher runs on the records of "E7" on 2025-05-20 at 19:30 (M6)
    And Priya files the judgment "J4" on 2025-05-20 at 19:35
    And the export "x-e8" is imported on 2025-06-15 at 08:05:04 (E8)
    And the matcher runs on the records of "E8" on 2025-06-15 at 08:05:04 (M7)
    And the download "fernhill-family-clinic-summary-2.xml" is imported on 2025-08-12 at 19:05:04 (E9)
    And the matcher runs on the records of "E9" on 2025-08-12 at 19:05:04 (M8)
    And Priya files the judgment "J5" on 2025-08-12 at 19:08
    And the download "export_cda.xml" is imported on 2025-08-12 at 19:10 (E10)
    And the download "kestrel-harbor-health-summary-4.xml" is imported on 2025-08-12 at 19:12 (E11)

  Rule: P1. The same allergy from FHIR and from C-CDA
    Aspirin is KHF-ALG-ASPIRIN in Kestrel Harbor's FHIR and KHC-ALG-ASPIRIN in its C-CDA, both RxNorm 1191: the matcher
    joins them by the same code (M2), and Fernhill's FFC-ALG-ASPIRIN joins them when it arrives (M5).

    Example: Kestrel Harbor's two copies of the aspirin allergy are two records, joined by the same code
      When the pod is read as it stood after "M2"
      Then these records have:
        | record          | field | value   |
        | KHF-ALG-ASPIRIN | kind  | allergy |
        | KHC-ALG-ASPIRIN | kind  | allergy |
      And the matcher's judgments holding KHF-ALG-ASPIRIN are:
        | justification | members                          |
        | same code     | KHF-ALG-ASPIRIN, KHC-ALG-ASPIRIN |
      And the allergies view holds these entries:
        | members                          |
        | KHF-ALG-ASPIRIN, KHC-ALG-ASPIRIN |

    Example: with Fernhill's, the aspirin allergy is one entry of three records
      Then the allergies view holds these entries:
        | members                                           |
        | KHF-ALG-ASPIRIN, KHC-ALG-ASPIRIN, FFC-ALG-ASPIRIN |

  Rule: P2. The same medication from FHIR and from C-CDA
    Lisinopril is a prescription in Kestrel Harbor's FHIR, KHF-MED-LISINOPRIL, RxNorm 314076 in its coding, and an entry
    on the list of what Priya takes in its C-CDA, KHC-MED-LISINOPRIL, whose code is the portal's own with RxNorm 314076
    in a translation. The drug products table her app holds names 314076 a clinical drug, one product, so the matcher
    joins them by the same product code (M16).

    Example: the matcher joins the prescription and the list entry by the same product code
      When the pod is read as it stood after "M2"
      Then these records have:
        | record             | field | value      |
        | KHF-MED-LISINOPRIL | kind  | medication |
        | KHC-MED-LISINOPRIL | kind  | medication |
      And the matcher's judgments holding KHF-MED-LISINOPRIL are:
        | justification     | members                                |
        | same product code | KHF-MED-LISINOPRIL, KHC-MED-LISINOPRIL |
      And the medications view holds these entries:
        | members                                |
        | KHF-MED-LISINOPRIL, KHC-MED-LISINOPRIL |

    Example: one says it was prescribed and the other that she takes it
      When the pod is read as it stood after "M2"
      When the query is:
        """
        SELECT ?intent WHERE {
          ?record pav:hasCurrentVersion ?version .
          ?version cascade:rxNormCode <https://ns.cascadeprotocol.org/codes/rxnorm/314076> ; cascade:prescribedOrReported ?intent .
        }
        """
      Then it answers:
        | intent        |
        | "prescribed"  |
        | "reportedUse" |

  Rule: P3. The same lab result from FHIR and from C-CDA
    Potassium on 2025-03-27 is KHF-LAB-K-0327, at 2025-03-27T12:00:00Z, 4.1 in mmol/L, and KHC-LAB-K-0327, at
    20250327120000+0000, 4.1 in mmol/l: the matcher joins them by the same result, a LOINC code, an instant, a value
    and a unit, the litre's two symbols being one unit to UCUM.

    Example: the two potassium results are joined by the same result
      When the pod is read as it stood after "M2"
      Then these records have:
        | record         | field | value      |
        | KHF-LAB-K-0327 | kind  | lab result |
        | KHC-LAB-K-0327 | kind  | lab result |
      And the matcher's judgments holding KHF-LAB-K-0327 are:
        | justification | members                        |
        | same result   | KHF-LAB-K-0327, KHC-LAB-K-0327 |

    Example: each states its unit as its source wrote it
      When the pod is read as it stood after "M2"
      When the query is:
        """
        SELECT ?unit WHERE {
          ?record pav:hasCurrentVersion ?version .
          ?version cascade:testCode <http://loinc.org/rdf/2823-3> ; cascade:resultQuantity/cascade:ucumUnit ?unit .
        }
        """
      Then it answers:
        | unit     |
        | "mmol/L" |
        | "mmol/l" |

  Rule: P4. A medication only the C-CDA has, until the FHIR has it too
    Amlodipine, started on 2025-04-01, is in Kestrel Harbor's C-CDA from E3 and in its FHIR only from x-e8 (E8).

    Example: until x-e8, amlodipine is an entry of the C-CDA's record alone
      When the pod is read as it stood after "M4"
      Then the medications view holds these entries:
        | members            |
        | KHC-MED-AMLODIPINE |

    Example: x-e8's prescription joins it
      When the pod is read as it stood after "M7"
      Then the medications view holds these entries:
        | members                                |
        | KHC-MED-AMLODIPINE, KHF-MED-AMLODIPINE |

  Rule: P5. A lab result of another time stays apart
    Potassium on 2025-06-10, KHF-LAB-K-0610, has the same code as the March results and another time and value.

    Example: June's potassium is an entry of its own
      Then the lab-results view holds these entries:
        | members                        |
        | KHF-LAB-K-0327, KHC-LAB-K-0327 |
        | KHF-LAB-K-0610                 |
      And the matcher has no judgment holding KHF-LAB-K-0610

  Rule: P6. A record only a C-CDA has
    Fernhill's flu shot, FFC-IMM-FLU, is in no other source.

    Example: the flu shot is an entry of one record
      Then the immunizations view holds these entries:
        | members     |
        | FFC-IMM-FLU |
      And the matcher has no judgment holding FFC-IMM-FLU

  Rule: P7. A download again, with new bytes and narrative IDs that moved, adds no record and no version
    kestrel-harbor-health-summary-2.xml (E4) has a new document id and time, and every narrative ID renamed and two rows
    reordered; its entries say what the first download's said.

    Example: E4 revises no record and the matcher finds nothing new
      When the pod is read as it stood after "M3"
      Then the records have these revisions:
        | record             | arrived                | version | after |
        | KHC-ALG-ASPIRIN    | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-CON-HTN        | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-MED-LISINOPRIL | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-MED-AMLODIPINE | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-LAB-K-0327     | 2025-04-03 at 09:20:04 | 1       |       |
      And "M3" wrote no file

  Rule: P8. A download again with one entry changed adds one version of that record
    kestrel-harbor-health-summary-3.xml (E5) is the second download with the aspirin reaction's severity moderate, not
    mild.

    Example: KHC-ALG-ASPIRIN gets a second version, and no other record a revision
      When the pod is read as it stood after "M4"
      Then the records have these revisions:
        | record          | arrived                | version | allergy severity | after                  |
        | KHC-ALG-ASPIRIN | 2025-04-03 at 09:20:04 | 1       | mild             |                        |
        | KHC-ALG-ASPIRIN | 2025-05-05 at 17:45:04 | 2       | moderate         | 2025-04-03 at 09:20:04 |
      And the records have these revisions:
        | record             | arrived                | version | after |
        | KHC-CON-HTN        | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-MED-LISINOPRIL | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-MED-AMLODIPINE | 2025-04-03 at 09:20:04 | 1       |       |
        | KHC-LAB-K-0327     | 2025-04-03 at 09:20:04 | 1       |       |

  Rule: P9. An entry with no id, downloaded twice, keeps its name
    Fernhill's flu shot has <id nullFlavor="NI"/>: it is named from a key of its fields, the same in both downloads.

    Example: the second Fernhill download revises no flu shot and makes no new one
      Then the records have these revisions:
        | record      | arrived                | version | after |
        | FFC-IMM-FLU | 2025-05-20 at 18:50:04 | 1       |       |

  Rule: P10. An entry whose id repeats in its document is named by its document and its place in it
    decisions/naming.md, row "record from C-CDA": Fernhill writes one id for Claritin and fluticasone, so each is
    named by its download and its place, and the adapter says the source broke its own definition. Claritin in the
    second download, FFC-MED-CLARITIN-2, is a record of its own. Neither Claritin states a start (P13), and a record
    with no start joins no other medication (decisions/medication-matching.md, row "no dates"; M15), so under the rule
    list's version 18 the matcher keeps the two apart, although they share a product code. "What needs review" lists
    the pair as possibly the same medication (M16), and Priya joins it with a Same, J5, which outranks the matcher
    (P15).

    Example: the second download's Claritin is a record of its own
      Then the records have these revisions:
        | record             | arrived                | version | after |
        | FFC-MED-CLARITIN   | 2025-05-20 at 18:50:04 | 1       |       |
        | FFC-MED-CLARITIN-2 | 2025-08-12 at 19:05:04 | 1       |       |

    Example: the matcher keeps it apart from the first, since neither states a start
      When the pod is read as it stood after "M8"
      Then the matcher has no judgment holding FFC-MED-CLARITIN-2
      And the medications view holds these entries:
        | members                              |
        | APP-MED-LORATADINE, FFC-MED-CLARITIN |
        | FFC-MED-CLARITIN-2                   |

    Example: "What needs review" lists the pair as possibly the same medication, until Priya joins it
      When the pod is read as it stood after "M8"
      And the query "questions/entry/What needs review.rq" is asked
      Then it answers:
        | entry                         | entryLabel                                        | needs                          | finding | judgment | judgmentLabel | record           | recordLabel                                                | otherRecord        | otherRecordLabel                                           |
        | the entry of FFC-MED-CLARITIN | "Medication entry · loratadine 10 MG Oral Tablet" | "possibly the same medication" |         |          |               | FFC-MED-CLARITIN | "Medication · Claritin 10 MG Oral Tablet · Fernhill Family Clinic · received 2025-05-20" | FFC-MED-CLARITIN-2 | "Medication · Claritin 10 MG Oral Tablet · Fernhill Family Clinic · received 2025-08-12" |

  Rule: P11. A repeated id with its status changed is a new record, joined to the old one
    In the second Fernhill download fluticasone's status is completed, and, named by its download as P10 says,
    FFC-MED-FLUTICASONE-2 is a record of its own. Both state the same start, 2024-10-15, so their periods share that
    day, and the matcher joins it to FFC-MED-FLUTICASONE-1 by the same product code (M15, M16).

    Example: the matcher joins the two fluticasone records by the same product code
      Then the matcher's judgments holding FFC-MED-FLUTICASONE-2 are:
        | justification     | members                                      |
        | same product code | FFC-MED-FLUTICASONE-1, FFC-MED-FLUTICASONE-2 |
      And the medications view holds these entries:
        | members                                      |
        | FFC-MED-FLUTICASONE-1, FFC-MED-FLUTICASONE-2 |
      And the entry of FFC-MED-FLUTICASONE-2 shows:
        | field         | value                 |
        | status        | completed             |
        | lead member   | FFC-MED-FLUTICASONE-2 |

  Rule: P12. A name read through an originalText reference
    Fernhill's problem is coded SNOMED 367498001 with no display name; its name is the narrative's text, Hay fever.

    Example: the condition is named Hay fever
      Then these records have:
        | record                                 | field | value     |
        | condition SNOMED 367498001 "Hay fever" | kind  | condition |

  Rule: P13. A nullFlavor where a value would be
    Claritin's start is <low nullFlavor="UNK"/>: its version states no start, where fluticasone's states one.

    Example: Claritin states no start date
      When the query is:
        """
        SELECT ?drug ?start WHERE {
          ?record pav:hasCurrentVersion ?version .
          ?version cascade:drugName ?drug .
          OPTIONAL { ?version cascade:medicationUseStartDate ?start }
          FILTER (?drug IN ("Claritin 10 MG Oral Tablet", "fluticasone propionate 50 MCG/ACTUAT Nasal Spray"))
        }
        """
      Then it answers:
        | drug                                               | start                  |
        | "Claritin 10 MG Oral Tablet"                       |                        |
        | "Claritin 10 MG Oral Tablet"                       |                        |
        | "fluticasone propionate 50 MCG/ACTUAT Nasal Spray" | "2024-10-15"^^xsd:date |
        | "fluticasone propionate 50 MCG/ACTUAT Nasal Spray" | "2024-10-15"^^xsd:date |

  Rule: P14. A section the adapter does not map is a finding
    Each C-CDA's vital signs and social history sections are findings the Bridge raises (ccda:sectionNotMapped in each
    saved findings.ttl), never records. A document that revised nothing is still kept for its findings (A10).

    Example: no blood pressure and no smoking status is in the pod
      When the pod is read as it stood after "M5"
      When the query is:
        """
        SELECT ?thing WHERE {
          VALUES ?code { <http://loinc.org/rdf/8480-6> <http://loinc.org/rdf/8462-4> <http://loinc.org/rdf/72166-2> }
          ?thing ?property ?code .
        }
        """
      Then it answers nothing

    Example: E4's download revised nothing and is kept for its findings
      When the pod is read as it stood after "E4"
      When the query is:
        """
        SELECT (COUNT(DISTINCT ?revision) AS ?revisions) (COUNT(DISTINCT ?document) AS ?documents) WHERE {
          GRAPH <urn:cascade:steps> { <urn:cascade:step:E4> prov:generated ?file }
          GRAPH ?file {
            { ?revision a cascade:Revision }
            UNION
            { ?document a prov:Entity }
          }
        }
        """
      Then it answers:
        | revisions | documents |
        | 0         | 1         |

  Rule: P15. A person joins what the matcher does not
    Priya enters loratadine she takes, APP-MED-LORATADINE (RxNorm 311372); Fernhill lists its brand, FFC-MED-CLARITIN
    (RxNorm 206805). The matcher finds no same code; her Same, J4, joins them. The matcher keeps the second download's
    Claritin apart from the first (P10), and her Same, J5, joins it to them. Her own record leads the entry, as a record
    the person entered leads any it is in (C6).

    Example: the matcher does not join her loratadine
      When the pod is read as it stood after "M6"
      Then the matcher has no judgment holding APP-MED-LORATADINE

    Example: J4 joins her loratadine and Fernhill's Claritin, and J5 the second download's Claritin, in one entry
      Then the medications view holds these entries:
        | members                                                  |
        | APP-MED-LORATADINE, FFC-MED-CLARITIN, FFC-MED-CLARITIN-2 |
      And J4 counts
      And J5 counts

    Example: with J5, "What needs review" lists the Claritin pair no more
      When the query "questions/entry/What needs review.rq" is asked
      Then it answers nothing

    Example: her loratadine leads the entry, since she entered it
      Then the entry of APP-MED-LORATADINE shows:
        | field       | value              |
        | lead member | APP-MED-LORATADINE |

  Rule: P16. A file that is not well-formed is refused
    kestrel-harbor-health-summary-4.xml (E11) stops inside an element, as a download cut off does.

    Example: E11 is refused and writes nothing
      When the pod is read as it stood after "E11"
      Then that step is refused
      And "E11" wrote no file

  Rule: P17. A CDA that is not a C-CDA is refused
    export_cda.xml (E10) is Apple's CDA of HealthKit samples, whose header claims no US Realm Header: no adapter of its
    media type accepts it.

    Example: E10 is refused and writes nothing
      When the pod is read as it stood after "E10"
      Then that step is refused
      And "E10" wrote no file

  Rule: Her claims tie three profiles to her
    J1 to J3 each claim the profile one source names for her: KHF-PAT, KHC-PAT and FFC-PAT.

    Example: the patient profile is one entry of the three profiles
      Then the patient-profile view holds these entries:
        | members                   |
        | KHF-PAT, KHC-PAT, FFC-PAT |

  Rule: The tables an app holds name her potassium and class her lisinopril
    An app opens her pod with tables of its own (app-names-classes): the published LOINC names, RxNorm product
    ingredients, MED-RT drug classes and MED-RT names, each only the rows her potassium and her lisinopril need, and the
    vocabulary's rule list version 18. Which names an app shows is its own choice, so the example asks only that her
    potassium's code, LOINC 2823-3, joins the held names version. Lisinopril 10 MG Oral Tablet (RxNorm 314076) bears no
    class row: it maps to lisinopril (29046), and FDA classes lisinopril anhydrous (1546022), which maps to lisinopril
    too, as an angiotensin converting enzyme inhibitor (N0000175562) acting by that mechanism (N0000000181).

    Opening writes no file, by O1: her pod has named the vocabulary's rule list version 18 since her app opened it, and
    these tables join no pair that version had not joined, so there is nothing to file or to describe.

    Example: her potassium's code joins the names version the app holds
      When the pod is opened with the tables "app-names-classes" on 2025-08-13 at 09:00
      Then "app-names-classes" wrote no file
      When the query is:
        """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?record ?name ?version WHERE {
          ?record pav:hasCurrentVersion/cascade:testCode ?code .
          ?version prov:specializationOf/cascade:tableKind cascade:CodeNames .
          GRAPH ?version { ?code skos:prefLabel ?name }
        }
        """
      Then it answers:
        | record         | name                                          | version                                                         |
        | KHF-LAB-K-0327 | "Potassium [Moles/volume] in Serum or Plasma" | Regenstrief LOINC names subset for Priya Natarajan version 2.83 |
        | KHC-LAB-K-0327 | "Potassium [Moles/volume] in Serum or Plasma" | Regenstrief LOINC names subset for Priya Natarajan version 2.83 |
        | KHF-LAB-K-0610 | "Potassium [Moles/volume] in Serum or Plasma" | Regenstrief LOINC names subset for Priya Natarajan version 2.83 |

    Example: her lisinopril is an angiotensin converting enzyme inhibitor through lisinopril anhydrous
      When the pod is opened with the tables "app-names-classes" on 2025-08-13 at 09:00
      And the query "tables/medication-classes.rq" is asked
      Then it answers:
        | entry                           | medication                     | class                                                    | relation                              | origin                                                               | through                                               | stated |
        | the entry of KHF-MED-LISINOPRIL | "lisinopril 10 MG Oral Tablet" | <https://ns.cascadeprotocol.org/codes/medrt/N0000175562> | cascade:establishedPharmacologicClass | VA MED-RT drug classes subset for Priya Natarajan version 2026-10-05 | "https://ns.cascadeprotocol.org/codes/rxnorm/1546022" | false  |
        | the entry of KHF-MED-LISINOPRIL | "lisinopril 10 MG Oral Tablet" | <https://ns.cascadeprotocol.org/codes/medrt/N0000000181> | cascade:mechanismOfActionClass        | VA MED-RT drug classes subset for Priya Natarajan version 2026-10-05 | "https://ns.cascadeprotocol.org/codes/rxnorm/1546022" | false  |
      When the query is:
        """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?class ?name WHERE {
          ?version prov:specializationOf/cascade:tableKind cascade:CodeNames .
          GRAPH ?version { ?class skos:prefLabel ?name }
          FILTER (?class IN (<https://ns.cascadeprotocol.org/codes/medrt/N0000175562>, <https://ns.cascadeprotocol.org/codes/medrt/N0000000181>))
        }
        """
      Then it answers:
        | class                                                    | name                                             |
        | <https://ns.cascadeprotocol.org/codes/medrt/N0000175562> | "Angiotensin Converting Enzyme Inhibitor [EPC]"  |
        | <https://ns.cascadeprotocol.org/codes/medrt/N0000000181> | "Angiotensin-converting Enzyme Inhibitors [MoA]" |

  Rule: Her lab results in a LOINC panel she names
    An app opens her pod with tables of its own (app-panels): the published LOINC panel members rows of the Electrolytes
    1998 panel (24326-1), and the vocabulary's rule list version 18. LOINC lists sodium (2951-2), potassium (2823-3) and
    chloride (2075-0) in it, in that order and required (R), bicarbonate (1963-8) and carbon dioxide (2028-9) as
    alternatives (R-a), and the anion gap (33037-3) as optional. Her two potassium entries are in it, and she has no
    sodium and no chloride: the panel is hers to pick, and nothing says her potassium was drawn in it.

    Opening writes no file, by O1, as it does for app-names-classes: the same rule list judges the same pairs.

    Example: her potassium is in the electrolytes panel, which misses her sodium and chloride
      When the pod is opened with the tables "app-panels" on 2025-08-13 at 09:00
      Then "app-panels" wrote no file
      When the query "tables/panel-results.rq" is asked
      Then it answers:
        | panel                          | member                        | sequence | required | via                            | origin                                                                  | entry                       |
        | <http://loinc.org/rdf/24326-1> | <http://loinc.org/rdf/2951-2> | 1        | "R"      | <http://loinc.org/rdf/24326-1> | Regenstrief LOINC panel members subset for Priya Natarajan version 2.83 |                             |
        | <http://loinc.org/rdf/24326-1> | <http://loinc.org/rdf/2823-3> | 2        | "R"      | <http://loinc.org/rdf/24326-1> | Regenstrief LOINC panel members subset for Priya Natarajan version 2.83 | the entry of KHF-LAB-K-0327 |
        | <http://loinc.org/rdf/24326-1> | <http://loinc.org/rdf/2823-3> | 2        | "R"      | <http://loinc.org/rdf/24326-1> | Regenstrief LOINC panel members subset for Priya Natarajan version 2.83 | the entry of KHF-LAB-K-0610 |
        | <http://loinc.org/rdf/24326-1> | <http://loinc.org/rdf/2075-0> | 3        | "R"      | <http://loinc.org/rdf/24326-1> | Regenstrief LOINC panel members subset for Priya Natarajan version 2.83 |                             |

  Rule: An estradiol tablet is an estrogen, told from a product of fluoroestradiol F-18 by its precise ingredient
    Priya enters estradiol 1 MG Oral Tablet (RxNorm 197658) she takes. An app opens her pod with tables of its own
    (app-precise): RxNorm product ingredients that state precise ingredients, MED-RT drug classes and MED-RT names, each
    only the rows her estradiol needs, and the vocabulary's rule list version 18. Estradiol (4083) and its precise
    ingredient fluoroestradiol F-18 (2372221) are classed differently: FDA gives estradiol Estrogen [EPC] (N0000175825)
    and Estrogen Receptor Agonists [MoA] (N0000000100), and fluoroestradiol F-18 Radioactive Diagnostic Agent [EPC] and
    Positron Emitting Activity [MoA]. The version gives her tablet no precise ingredient, and it states precise
    ingredients (estradiol valerate 10 MG/ML Injectable Solution, 310189, has one), so her tablet holds estradiol itself
    and is in estradiol's own classes. Asked the published tables/medication-classes.rq, which cannot tell the two
    apart, it is in neither.

    Example: her estradiol is an estrogen through estradiol
      Given Priya enters "estradiol" on 2025-08-13 at 08:00
      When the pod is opened with the tables "app-precise" on 2025-08-13 at 09:00
      Then "app-precise" wrote no file
      When the query "tables/medication-classes-through-precise-ingredients.rq" is asked
      Then it answers:
        | entry                                                              | medication                   | class                                                    | relation                              | origin                                                                            | through                                            | stated |
        | the entry of medication RxNorm 197658 "estradiol 1 MG Oral Tablet" | "estradiol 1 MG Oral Tablet" | <https://ns.cascadeprotocol.org/codes/medrt/N0000175825> | cascade:establishedPharmacologicClass | VA MED-RT drug classes, subset for Priya Natarajan's estradiol version 2026-10-05 | "https://ns.cascadeprotocol.org/codes/rxnorm/4083" | false  |
        | the entry of medication RxNorm 197658 "estradiol 1 MG Oral Tablet" | "estradiol 1 MG Oral Tablet" | <https://ns.cascadeprotocol.org/codes/medrt/N0000000100> | cascade:mechanismOfActionClass        | VA MED-RT drug classes, subset for Priya Natarajan's estradiol version 2026-10-05 | "https://ns.cascadeprotocol.org/codes/rxnorm/4083" | false  |
        | the entry of medication RxNorm 197658 "estradiol 1 MG Oral Tablet" | "estradiol 1 MG Oral Tablet" | <http://id.nlm.nih.gov/mesh/M0447348>                    | cascade:chemicalStructureClass        | VA MED-RT drug classes, subset for Priya Natarajan's estradiol version 2026-10-05 | "https://ns.cascadeprotocol.org/codes/rxnorm/4083" | false  |
