Feature: Alex Rivera's pod
  The scenario every runtime must pass, https://github.com/jayostis/cascade-vocabulary/issues/4: Alex's story, the
  planted cases P1 to P25 under the case each shows, and the scenario's other outcomes. Each example reads the pod at
  the smallest set of steps and lenses at which it can fail for its own reason. A record, a profile and a person's
  judgment are named by the handle expected/handles.json gives it.

  Background: Alex's story
    Given a new pod for Alex on 2026-09-01 at 09:55 (E1)
    And the export "x-e2" is imported on 2026-09-01 at 10:00:04 (E2)
    And the matcher runs on the records of "E2" on 2026-09-01 at 10:00:04 (M5)
    And Alex files the judgment "J1" on 2026-09-01 at 10:00:30
    And Alex enters "a1" on 2026-09-01 at 18:30 (E3)
    And the matcher runs on the records of "E3" on 2026-09-01 at 18:30 (M6)
    And the export "x-e4" is imported on 2026-10-14 at 15:42 (E4)
    And Alex files the judgment "J2" on 2026-10-14 at 15:42:30
    And the matcher runs on the records of "E4" on 2026-10-14 at 15:43 (E5)
    And the export "x-e6" is imported on 2026-11-20 at 09:00:04 (E6)
    And the matcher runs on the records of "E6" on 2026-11-20 at 09:00:04 (M7)
    And the export "x-e6" is imported on 2026-11-21 at 20:10 (E7)
    And Alex files the judgment "J8" on 2026-12-02 at 19:00
    And Alex files the judgment "J9" on 2026-12-02 at 19:00
    And Alex files the judgment "J10" on 2026-12-02 at 19:00
    And version "2027-01" of "SNOMED CT to RxNorm ingredient map" arrives on 2027-01-15 at 06:00 (E9)
    And the matcher rechecks on 2027-01-15 at 06:00 (M2)
    And the export "x-e10" is imported on 2027-02-10 at 17:21 (E10)
    And the matcher runs on the records of "E10" on 2027-02-10 at 17:21 (M3)
    And Alex files the judgment "J22" on 2027-02-10 at 17:21:30
    And the export "x-e12" is imported on 2027-03-18 at 12:00:04 (E12)
    And Alex files the judgment "J12" on 2027-03-18 at 12:00:30
    And the matcher runs on the records of "E12" on 2027-03-18 at 12:01 (E13)
    And Alex files the judgment "J19" on 2027-04-02 at 20:00
    And Alex files the judgment "J20" on 2027-04-02 at 20:00
    And Alex files the judgment "J21" on 2027-04-02 at 20:00
    And Alex files the judgment "J23" on 2027-04-02 at 20:00
    And Alex files the judgment "J24" on 2027-04-02 at 20:00
    And the export "x-e15" is imported on 2027-08-20 at 08:00:04 (E15)
    And the matcher runs on the records of "E15" on 2027-08-20 at 08:00:04 (M8)

  Rule: P1. The same allergy at both hospitals, under different ids and code systems
    Penicillin is H1-ALG-PCN (RxNorm 7980) at Meridian, and H2O-ALG-PCN and H2F-ALG-PCN (SNOMED 373270004) at
    Larkspur's old and new servers: three records, joined by the matcher only through a mapped code (J4), then by Alex
    (J21).

    Example: one allergy at two hospitals is three allergy records
      Then these records have:
        | record      | field | value   |
        | H1-ALG-PCN  | kind  | allergy |
        | H2O-ALG-PCN | kind  | allergy |
        | H2F-ALG-PCN | kind  | allergy |

    Example: the matcher joins H1-ALG-PCN only through a mapped code
      Then the matcher's judgments holding H1-ALG-PCN are:
        | justification    | members                 |
        | same mapped code | H1-ALG-PCN, H2O-ALG-PCN |

    Example: under everyday, the mapped code joins H1-ALG-PCN and H2O-ALG-PCN in one entry
      When the pod is read as it stood after "E5"
      Then the allergies view holds these entries:
        | members                 |
        | H1-ALG-PCN, H2O-ALG-PCN |

    Example: under export a mapped code does not count, so H1-ALG-PCN and H2O-ALG-PCN are each an entry of their own
      When the pod is read as it stood after "E5", under the export lens
      Then the allergies view holds these entries:
        | members     |
        | H1-ALG-PCN  |
        | H2O-ALG-PCN |

    Example: once the ingredient map is revised, H1-ALG-PCN stands alone and J14's same code joins the Larkspur records
      When the pod is read as it stood after "E13"
      Then the allergies view holds these entries:
        | members                  |
        | H1-ALG-PCN               |
        | H2O-ALG-PCN, H2F-ALG-PCN |

    Example: J21, Alex's Same, joins the three penicillin records, even under export
      When the pod is read as it stood after "J24", under the export lens
      Then the allergies view holds these entries:
        | members                              |
        | H1-ALG-PCN, H2O-ALG-PCN, H2F-ALG-PCN |

    Example: J21 counts under export
      When the pod is read as it stood after "J24", under the export lens
      Then J21 counts

  Rule: P2. A record revised between two exports
    H1-ALG-LATEX and H1-ALG-SULFA, E2 then E6: a new version and a revision after the first; the new version current.

    Example: H1-ALG-LATEX and H1-ALG-SULFA, revised between E2 and E6, each get a revision after their first
      When the pod is read as it stood after "M7"
      Then the records have these revisions:
        | record       | arrived                | version | after                  |
        | H1-ALG-LATEX | 2026-09-01 at 10:00:04 | 1       |                        |
        | H1-ALG-LATEX | 2026-11-20 at 09:00:04 | 2       | 2026-09-01 at 10:00:04 |
        | H1-ALG-SULFA | 2026-09-01 at 10:00:04 | 1       |                        |
        | H1-ALG-SULFA | 2026-11-20 at 09:00:04 | 2       | 2026-09-01 at 10:00:04 |

    Example: the second version of each is its current version
      When the pod is read as it stood after "M7"
      Then these records have:
        | record       | field   | value |
        | H1-ALG-LATEX | version | 2     |
        | H1-ALG-SULFA | version | 2     |

  Rule: P3. A condition resolved
    H1-CON-BRONCH, E6: its second version is resolved and current, and its entry shows it resolved.

    Example: H1-CON-BRONCH's second version, resolved on 2026-09-20, is current, and its entry shows it resolved
      When the pod is read as it stood after "M7"
      Then these records have:
        | record        | field   | value |
        | H1-CON-BRONCH | version | 2     |
      And the entry of H1-CON-BRONCH shows:
        | field          | value      |
        | status         | resolved   |
        | abatement date | 2026-09-20 |

  Rule: P4. A criticality disagreement between hospitals
    Sulfamethoxazole is low at Meridian and high at Larkspur: from E5 the entry shows high, the most severe, and the
    disagreement is listed for review.

    Example: at E5, the entry holding H1-ALG-SULFA shows the most severe criticality its members give
      When the pod is read as it stood after "E5"
      Then the allergies view holds these entries:
        | members                     |
        | H1-ALG-SULFA, H2O-ALG-SULFA |
      And the entry of H1-ALG-SULFA shows:
        | field       | value |
        | criticality | high  |
      And these records have:
        | record        | field       | value |
        | H1-ALG-SULFA  | criticality | low   |
        | H2O-ALG-SULFA | criticality | high  |

    Example: at E13, the entry holding H1-ALG-SULFA still shows the most severe criticality its members give
      When the pod is read as it stood after "E13"
      Then the allergies view holds these entries:
        | members                                    |
        | H1-ALG-SULFA, H2O-ALG-SULFA, H2F-ALG-SULFA |
      And the entry of H1-ALG-SULFA shows:
        | field       | value |
        | criticality | high  |
      And these records have:
        | record        | field       | value |
        | H1-ALG-SULFA  | criticality | low   |
        | H2O-ALG-SULFA | criticality | high  |
        | H2F-ALG-SULFA | criticality | high  |

  Rule: P5. A record missing from a later export
    H1-ALG-LATEX is absent from x-e15: nothing is written, and latex stays in the view with its second version.

    Example: no file E15 or M8 wrote names H1-ALG-LATEX
      Then no file that "E15" or "M8" wrote names H1-ALG-LATEX

    Example: H1-ALG-LATEX is still at its second version and is an entry of its own
      Then these records have:
        | record       | field   | value |
        | H1-ALG-LATEX | version | 2     |
      And the allergies view holds these entries:
        | members      |
        | H1-ALG-LATEX |

  Rule: P6. Entered in error at the source
    H1-ALG-CODEINE's second version, E6: left out of every view, and still in the pod.

    Example: H1-ALG-CODEINE, entered in error at its source in x-e6, is in no view, for that reason
      Then these records are in no view, for these reasons:
        | record         | reason                     | because |
        | H1-ALG-CODEINE | entered in error at source |         |

    Example: H1-ALG-CODEINE is still an allergy record, with both its versions
      Then H1-ALG-CODEINE has these revisions:
        | arrived                | version | after                  |
        | 2026-09-01 at 10:00:04 | 1       |                        |
        | 2026-11-20 at 09:00:04 | 2       | 2026-09-01 at 10:00:04 |
      And these records have:
        | record         | field | value   |
        | H1-ALG-CODEINE | kind  | allergy |

  Rule: P7. The same flu shot at both hospitals
    H1-IMM-FLU25 and H2O-IMM-FLU25, joined by J6 at E5: one entry.

    Example: the immunizations view is one entry, of H1-IMM-FLU25 and H2O-IMM-FLU25
      When the pod is read as it stood after "E5"
      Then the immunizations view holds these entries:
        | members                     |
        | H1-IMM-FLU25, H2O-IMM-FLU25 |

  Rule: P8. Several patient profiles of one person, each made the subject's by an About
    H1-PAT (J1, E2), H2O-PAT (J2, E4) and H2F-PAT (J12, E12): every record naming any of them is Alex's, and the patient
    view has one entry whose members are the profiles, and no name or birth date, since no profile has content.

    Example: every record whose current version names a claimed profile is Alex's
      When the pod is read as it stood after "J12"
      Then the query "queries/every-record-naming-a-claimed-profile-is-the-subjects.rq" answers:
        | hers | notHers |
        | 22   | 0       |

    Example: the patient view is one entry of the claimed profiles, stating nothing but its type and members
      When the pod is read as it stood after "J12"
      Then the patient-profile view holds these entries:
        | members                           |
        | H1-PAT, H2O-PAT, H2F-PAT, H1P-PAT |
      And the entry of H1-PAT shows only:
        | field | value          |
        | type  | PatientProfile |

    Example: before any About, the patient view has no entry
      When the pod is read as it stood after "E1"
      Then the patient-profile view has no entry

  Rule: P9. A re-import of an identical export
    E7: nothing is written, not even an import.

    Example: E7 imports x-e6 again and writes no file, not even an import
      Then "E7" wrote no file

  Rule: P10. One hospital naming the same allergy twice, because it moved server
    H2O-ALG-SULFA (old server, al-8237462) and H2F-ALG-SULFA (new server, lv-alg-102) are two records, joined by J13 at
    E13; likewise J14 for penicillin.

    Example: Larkspur's old and new servers name one allergy as two records, and one entry holds both
      When the pod is read as it stood after "E13"
      Then the allergies view holds these entries:
        | members                                    |
        | H1-ALG-SULFA, H2O-ALG-SULFA, H2F-ALG-SULFA |
        | H2O-ALG-PCN, H2F-ALG-PCN                   |

  Rule: P11. A Different overriding a machine Same
    J7 is the matcher's Same at E5, and J8 Alex's Different: the colonoscopies are apart from then under both lenses,
    and J7 still counts, though not for that pair.

    Example: J8, Alex's Different, keeps apart the colonoscopies the matcher joined
      When the pod is read as it stood after "J10"
      Then the procedures view holds these entries:
        | members       |
        | H1-PROC-COLO  |
        | H2O-PROC-COLO |

    Example: J7, the matcher's Same of the pair, still counts, and no two procedures are currently the same
      When the pod is read as it stood after "J10"
      Then the matcher's same code of H1-PROC-COLO and H2O-PROC-COLO counts
      And the query "queries/procedures-currently-the-same.rq" answers nothing

  Rule: P12. A Same chain through two kinds of machine sameness
    The flu shots: J6 (same code and date, E5) and J17 (same mapped code and date, E13). One entry under everyday,
    listed for review; under export J17 does not count.

    Example: under everyday the immunizations view is one entry of the three flu shots
      When the pod is read as it stood after "E13"
      Then the immunizations view holds these entries:
        | members                                    |
        | H1-IMM-FLU25, H2O-IMM-FLU25, H2F-IMM-FLU25 |

    Example: under export J17's mapped vaccine group does not count, so H2F-IMM-FLU25 is an entry of its own
      When the pod is read as it stood after "E13", under the export lens
      Then the immunizations view holds these entries:
        | members                     |
        | H1-IMM-FLU25, H2O-IMM-FLU25 |
        | H2F-IMM-FLU25               |

    Example: under everyday the flu entry is joined by Sames of two justifications, which lists it for review
      When the pod is read as it stood after "E13"
      Then the query "queries/flu-entry-justifications.rq" answers:
        | justification             |
        | jdg:SameCodeAndDate       |
        | jdg:SameMappedCodeAndDate |

    Example: under export only J6's justification counts, so the flu entry is not listed
      When the pod is read as it stood after "E13", under the export lens
      Then the query "queries/flu-entry-justifications.rq" answers:
        | justification       |
        | jdg:SameCodeAndDate |

  Rule: P13. A retracted judgment
    J20 retracts J10: bronchitis and asthma are apart again, and nothing replaces J10.

    Example: once J20 retracts J10, H1-CON-BRONCH and H2O-CON-ASTHMA are in different entries
      When the pod is read as it stood after "J24"
      Then the conditions view holds these entries:
        | members                        |
        | H1-CON-BRONCH                  |
        | H2O-CON-ASTHMA, H2F-CON-ASTHMA |

    Example: J20 is a judgment with no member, retracting J10, which no longer counts
      When the pod is read as it stood after "J24"
      Then the query "queries/nothing-replaces-the-retracted-same.rq" answers:
        | retracted | counts |
        | J10       | false  |

  Rule: P14. A machine judgment stops counting under everyday when its reference table is replaced
    J4 and E9: penicillin splits under everyday; nothing is written but the new table version; J4 stays.

    Example: E9 writes one file, the new ingredient map's description, and M2's recheck writes none
      Then "E9" wrote 1 file
      And "E9" wrote these reference descriptions:
        | reference                                          |
        | SNOMED CT to RxNorm ingredient map version 2027-01 |
      And "M2" wrote no file

    Example: J4 is still held, and under everyday no longer counts
      When the pod is read as it stood after "M2"
      Then the matcher's same mapped code of H1-ALG-PCN and H2O-ALG-PCN does not count

    Example: H1-ALG-PCN and H2O-ALG-PCN are apart once the table is revised
      When the pod is read as it stood after "M2"
      Then the allergies view holds these entries:
        | members     |
        | H1-ALG-PCN  |
        | H2O-ALG-PCN |

  Rule: P15. A judgment made against versions that later change
    J3 used H1-ALG-SULFA's first version, and its second arrives at E6: J3 still counts and is listed for review, until
    J9 supersedes it.

    Example: J3 still counts once its member changed, and is listed for review
      When the pod is read as it stood after "M7"
      Then the query "queries/judgments-whose-member-changed.rq" answers:
        | judgment                                                  |
        | the matcher's same code of H1-ALG-SULFA and H2O-ALG-SULFA |

    Example: once J9 supersedes J3, no Same that counts used other than its members' current versions
      When the pod is read as it stood after "J10"
      Then the query "queries/judgments-whose-member-changed.rq" answers nothing

  Rule: P16. An entry the patient adds, the owner's own act
    APP-ALG-PEANUT, E3: the subject's without any About; its criticality counts, and it supplies no status.

    Example: APP-ALG-PEANUT's version names Alex as its patient, and the Abouts claim only profiles
      Then these records have:
        | record         | field   | value |
        | APP-ALG-PEANUT | patient | Alex  |
      And the query "queries/what-the-abouts-claim.rq" answers:
        | member  |
        | H1-PAT  |
        | H2O-PAT |
        | H1P-PAT |
        | H2F-PAT |

    Example: APP-ALG-PEANUT is Alex's, and its entry shows its criticality and no status
      When the pod is read as it stood after "M6"
      Then these records have:
        | record         | field   | value |
        | APP-ALG-PEANUT | subject | Alex  |
      And the entry of APP-ALG-PEANUT shows:
        | field       | value |
        | criticality | high  |
        | status      |       |
        | status from |       |

  Rule: P17. A server version changes and the content does not
    H1-CON-HTN, versionId 3 then 4, E6: nothing is written and the file is not stored.

    Example: E6 and E15 bring H1-CON-HTN under new server versions with its content unchanged, and write nothing of it
      Then no file that "E6" or "E15" wrote names H1-CON-HTN

    Example: H1-CON-HTN has one revision, of its one version
      Then H1-CON-HTN has these revisions:
        | arrived                | version | after |
        | 2026-09-01 at 10:00:04 | 1       |       |

    Example: x-e6's file for H1-CON-HTN is neither described nor stored
      Then the pod neither names nor stores the document "x-e6/apple_health_export/clinical-records/Condition-cond-htn-1.json"

  Rule: P18. A change undone reuses a version
    H1-CON-BACK: active (E2), resolved (E6), active (E15): two versions and three revisions, the third pointing at the
    first version.

    Example: H1-CON-BACK has two versions, and its third revision sets the first again
      Then H1-CON-BACK has these revisions:
        | arrived                | version | after                  |
        | 2026-09-01 at 10:00:04 | 1       |                        |
        | 2026-11-20 at 09:00:04 | 2       | 2026-09-01 at 10:00:04 |
        | 2027-08-20 at 08:00:04 | 1       | 2026-11-20 at 09:00:04 |

    Example: H1-CON-BACK's entry shows it active, with no abatement date
      Then the entry of H1-CON-BACK shows:
        | field          | value  |
        | status         | active |
        | abatement date |        |

  Rule: P19. A record named from its document, not its id
    U-IMM-TDAP has no ClinicalRecord entry in x-e6, and an entry from x-e10 on: it is named from its document's SHA-256
    and "", with a finding; it names no patient, so it is nobody's and in no view; x-e10 and every later export write
    nothing for it.

    Example: U-IMM-TDAP is derived from its document, and its version names no patient
      Then these are named:
        | thing                      | name                                                      |
        | the document of U-IMM-TDAP | ni:///sha-256;lmlQ5kYnBqRHFB4DIMxNuP1nUh4xcHmY7XkQJs4Lq2s |
      And these records have:
        | record     | field   | value |
        | U-IMM-TDAP | patient |       |

    Example: U-IMM-TDAP is in no view, because its version names no patient
      Then these records are in no view, for these reasons:
        | record     | reason     | because |
        | U-IMM-TDAP | no patient |         |

    Example: no file E10, E12 or E15 wrote names U-IMM-TDAP
      Then no file that "E10", "E12" or "E15" wrote names U-IMM-TDAP

  Rule: P20. A Different pair still joined through a third record
    J18 (E13) is a machine Same over all three colonoscopies after J8: one entry of three through H2F-PROC-COLO, listed
    for review, until J19 (E14) separates it.

    Example: J18 joins the three colonoscopies in one entry, though J8 judged two of them different
      When the pod is read as it stood after "E13"
      Then the procedures view holds these entries:
        | members                                    |
        | H1-PROC-COLO, H2O-PROC-COLO, H2F-PROC-COLO |

    Example: the pair judged different shares an entry, which lists it for review
      When the pod is read as it stood after "E13"
      Then the query "queries/different-pairs-in-one-entry.rq" answers:
        | record        | otherRecord  |
        | H2O-PROC-COLO | H1-PROC-COLO |

    Example: J19 judges H1-PROC-COLO and H2F-PROC-COLO different, and H1-PROC-COLO stands alone
      When the pod is read as it stood after "J24"
      Then the procedures view holds these entries:
        | members                      |
        | H1-PROC-COLO                 |
        | H2O-PROC-COLO, H2F-PROC-COLO |

    Example: no pair judged different shares an entry
      When the pod is read as it stood after "J24"
      Then the query "queries/different-pairs-in-one-entry.rq" answers nothing

  Rule: P21. A person's and a machine's Same overlapping
    J9 (Alex's) and J13 (the matcher's) share two sulfa records: one group of three.

    Example: J9 and J13 share two records and make one entry of the three
      When the pod is read as it stood after "E13"
      Then the allergies view holds these entries:
        | members                                    |
        | H1-ALG-SULFA, H2O-ALG-SULFA, H2F-ALG-SULFA |

    Example: J9 and J13 both count
      When the pod is read as it stood after "E13"
      Then J9 counts
      And the matcher's same code of H1-ALG-SULFA, H2O-ALG-SULFA and H2F-ALG-SULFA counts

  Rule: P22. A person's mistaken Same hides a status
    J10 (E8) joins resolved bronchitis with active asthma: the joined entry shows resolved, from the most recent arrival,
    until E13 brings active asthma and J20 retracts J10.

    Example: J10 joins H1-CON-BRONCH and H2O-CON-ASTHMA, and their entry shows H1-CON-BRONCH's resolved status
      When the pod is read as it stood after "J10"
      Then the conditions view holds these entries:
        | members                       |
        | H1-CON-BRONCH, H2O-CON-ASTHMA |
      And the entry of H1-CON-BRONCH shows:
        | field       | value         |
        | status      | resolved      |
        | status from | H1-CON-BRONCH |

    Example: J16 adds H2F-CON-ASTHMA, the latest arrival, whose active status the entry now shows
      When the pod is read as it stood after "E13"
      Then the conditions view holds these entries:
        | members                                       |
        | H1-CON-BRONCH, H2O-CON-ASTHMA, H2F-CON-ASTHMA |
      And the entry of H1-CON-BRONCH shows:
        | field       | value          |
        | status      | active         |
        | status from | H2F-CON-ASTHMA |

    Example: once J20 retracts J10, the asthma entry is active and H1-CON-BRONCH's own entry resolved
      When the pod is read as it stood after "J24"
      Then the conditions view holds these entries:
        | members                        |
        | H1-CON-BRONCH                  |
        | H2O-CON-ASTHMA, H2F-CON-ASTHMA |
      And the entry of H1-CON-BRONCH shows:
        | field       | value         |
        | status      | resolved      |
        | status from | H1-CON-BRONCH |
      And the entry of H2O-CON-ASTHMA shows:
        | field       | value          |
        | status      | active         |
        | status from | H2F-CON-ASTHMA |

  Rule: P23. An unchanged record arriving again is not received again
    H1-ALG-PCN is in x-e4, x-e6, x-e10, x-e12 and x-e15: most recently received still dates it from E2.

    Example: H1-ALG-PCN, unchanged in every later export, has one revision, from E2
      Then H1-ALG-PCN has these revisions:
        | arrived                | version | after |
        | 2026-09-01 at 10:00:04 | 1       |       |

    Example: after E6 resends H1-ALG-PCN unchanged, H2O-ALG-PCN is still its entry's latest member
      When the pod is read as it stood after "M7"
      Then the entry of H1-ALG-PCN shows:
        | field         | value       |
        | latest member | H2O-ALG-PCN |

  Rule: P24. The wrong patient: a family member's records imported as Alex's
    Sam's proxy account is in x-e10; J22 (E10) claims his profile, and J23 retracts J22 (E14). From E10 to E13 H1P-PAT
    is a member of the patient view and Sam's allergy and two conditions are in Alex's views; from E14 none is in any
    view, under both lenses; nothing is changed or deleted, and no judgment names the import E10 wrote.

    Example: J22 claims Sam's profile as Alex's: it joins her patient entry, and each of his records is an entry
      When the pod is read as it stood after "J22"
      Then the patient-profile view holds these entries:
        | members                  |
        | H1-PAT, H2O-PAT, H1P-PAT |
      And the allergies view holds these entries:
        | members      |
        | H1P-ALG-AMOX |
      And the conditions view holds these entries:
        | members        |
        | H1P-CON-ECZEMA |
        | H1P-CON-OTITIS |

    Example: once J23 retracts J22, none of Sam's four is in any view
      When the pod is read as it stood after "J24"
      Then H1P-PAT, H1P-ALG-AMOX, H1P-CON-ECZEMA and H1P-CON-OTITIS are in no view

    Example: the patient view is one entry of H1-PAT, H2O-PAT and H2F-PAT
      When the pod is read as it stood after "J24"
      Then the patient-profile view holds these entries:
        | members                  |
        | H1-PAT, H2O-PAT, H2F-PAT |
      And the entry of H1-PAT shows only:
        | field | value          |
        | type  | PatientProfile |

    Example: each of Sam's three records is left out because no About that counts claims his profile
      When the pod is read as it stood after "J24"
      Then these records are in no view, for these reasons:
        | record         | reason              | because |
        | H1P-ALG-AMOX   | patient not claimed | H1P-PAT |
        | H1P-CON-ECZEMA | patient not claimed | H1P-PAT |
        | H1P-CON-OTITIS | patient not claimed | H1P-PAT |

    Example: J22 no longer counts
      When the pod is read as it stood after "J24"
      Then J22 does not count

    Example: every RDF file E10 wrote is still in the pod, and no judgment names the import E10 wrote
      Then the query "queries/nothing-is-deleted-and-no-judgment-names-the-import.rq" answers nothing

  Rule: P25. A record the patient says is wrong, which the source never corrects
    H1-PROC-ECHO (E6) is judged Erroneous by J24 (E14), and x-e15 carries it unchanged (E15): out of every view from
    E14, under both lenses; still in the pod; x-e15 writes nothing for it.

    Example: before J24, H1-PROC-ECHO is an entry of its own
      When the pod is read as it stood after "E13"
      Then the procedures view holds these entries:
        | members      |
        | H1-PROC-ECHO |

    Example: J24 judges H1-PROC-ECHO erroneous, and it is in no view, for that reason
      When the pod is read as it stood after "J24"
      Then these records are in no view, for these reasons:
        | record       | reason           | because |
        | H1-PROC-ECHO | judged erroneous | J24     |

    Example: H1-PROC-ECHO is still a procedure, with its one version and one revision
      Then H1-PROC-ECHO has these revisions:
        | arrived                | version | after |
        | 2026-11-20 at 09:00:04 | 1       |       |
      And these records have:
        | record       | field | value     |
        | H1-PROC-ECHO | kind  | procedure |

    Example: no file E15 wrote names H1-PROC-ECHO, which x-e15 resends unchanged
      Then no file that "E15" wrote names H1-PROC-ECHO

  Rule: The scenario's other outcomes

    Example: E5 writes J3 to J7 as the scenario gives them, and the reference descriptions it was the first to use
      Then "E5" wrote these matcher judgments:
        | justification      | members                     | used                                                                                                                                        | name                                          |
        | same code          | H1-ALG-SULFA, H2O-ALG-SULFA | Cascade matcher rules version 2026.1, version 1 of H1-ALG-SULFA, version 1 of H2O-ALG-SULFA                                                 | urn:uuid:6180bf81-2731-8f36-8568-3645a1478a14 |
        | same mapped code   | H1-ALG-PCN, H2O-ALG-PCN     | Cascade matcher rules version 2026.1, SNOMED CT to RxNorm ingredient map version 2026-09, version 1 of H1-ALG-PCN, version 1 of H2O-ALG-PCN | urn:uuid:908bf4a0-d3f8-8d7a-a64e-891918f6d10a |
        | same code          | H1-CON-HTN, H2O-CON-HTN     | Cascade matcher rules version 2026.1, version 1 of H1-CON-HTN, version 1 of H2O-CON-HTN                                                     | urn:uuid:52d9b6da-4fd5-8689-93bb-e131d1701242 |
        | same code and date | H1-IMM-FLU25, H2O-IMM-FLU25 | Cascade matcher rules version 2026.1, version 1 of H1-IMM-FLU25, version 1 of H2O-IMM-FLU25                                                 | urn:uuid:3bce4ba5-7594-859e-97ef-44bb6e02fabe |
        | same code          | H1-PROC-COLO, H2O-PROC-COLO | Cascade matcher rules version 2026.1, version 1 of H1-PROC-COLO, version 1 of H2O-PROC-COLO                                                 | urn:uuid:79c361c4-8002-8270-8b0e-a8ed97c477d6 |
      And "E5" wrote these reference descriptions:
        | reference                                          |
        | Cascade matcher rules                              |
        | Cascade matcher rules version 2026.1               |
        | SNOMED CT to RxNorm ingredient map                 |
        | SNOMED CT to RxNorm ingredient map version 2026-09 |

    Example: E13 writes J13 to J18 as the scenario gives them, and the reference descriptions it was the first to use
      Then "E13" wrote these matcher judgments:
        | justification             | members                                    | used                                                                                                                                                             | name                                          |
        | same code                 | H1-ALG-SULFA, H2O-ALG-SULFA, H2F-ALG-SULFA | Cascade matcher rules version 2026.1, version 2 of H1-ALG-SULFA, version 1 of H2O-ALG-SULFA, version 1 of H2F-ALG-SULFA                                          | urn:uuid:8a055107-e7f1-8093-b543-1c626271dc1a |
        | same code                 | H2O-ALG-PCN, H2F-ALG-PCN                   | Cascade matcher rules version 2026.1, version 1 of H2O-ALG-PCN, version 1 of H2F-ALG-PCN                                                                         | urn:uuid:f2a12462-97a3-8d9b-b238-424fa8a9a60a |
        | same code                 | H1-CON-HTN, H2O-CON-HTN, H2F-CON-HTN       | Cascade matcher rules version 2026.1, version 1 of H1-CON-HTN, version 1 of H2O-CON-HTN, version 1 of H2F-CON-HTN                                                | urn:uuid:897a70c2-1267-806a-ae9f-5e0d5ffa3f21 |
        | same code                 | H2O-CON-ASTHMA, H2F-CON-ASTHMA             | Cascade matcher rules version 2026.1, version 1 of H2O-CON-ASTHMA, version 1 of H2F-CON-ASTHMA                                                                   | urn:uuid:e6d7f16f-d87a-88c3-afa4-9e35400248a5 |
        | same mapped code and date | H1-IMM-FLU25, H2O-IMM-FLU25, H2F-IMM-FLU25 | Cascade matcher rules version 2026.1, CVX vaccine group table version 2026-08, version 1 of H1-IMM-FLU25, version 1 of H2O-IMM-FLU25, version 1 of H2F-IMM-FLU25 | urn:uuid:9d785db4-24fd-8a6c-a76d-cbaea82678d7 |
        | same code                 | H1-PROC-COLO, H2O-PROC-COLO, H2F-PROC-COLO | Cascade matcher rules version 2026.1, version 1 of H1-PROC-COLO, version 1 of H2O-PROC-COLO, version 1 of H2F-PROC-COLO                                          | urn:uuid:c024b6a4-fb62-8e18-882e-cb127acfcbf3 |
      And "E13" wrote these reference descriptions:
        | reference                               |
        | CVX vaccine group table                 |
        | CVX vaccine group table version 2026-08 |

    Example: the other matcher runs write nothing
      Then "M5", "M6", "M7", "M2", "M3" and "M8" wrote no file

    Example: each import and entry writes the scenario's numbers of records, versions, revisions, documents and activities
      Then the query "queries/each-step-writes-the-scenarios-counts.rq" answers:
        | step                   | records | versions | revisions | documents | imports | sessions |
        | <urn:cascade:step:E2>  | 9       | 9        | 9         | 9         | 1       | 0        |
        | <urn:cascade:step:E3>  | 1       | 1        | 1         | 0         | 0       | 1        |
        | <urn:cascade:step:E4>  | 6       | 6        | 6         | 6         | 1       | 0        |
        | <urn:cascade:step:E6>  | 2       | 7        | 7         | 7         | 1       | 0        |
        | <urn:cascade:step:E10> | 3       | 3        | 3         | 3         | 1       | 0        |
        | <urn:cascade:step:E12> | 6       | 6        | 6         | 6         | 1       | 0        |
        | <urn:cascade:step:E15> | 0       | 0        | 1         | 1         | 1       | 0        |

    Example: each of the 27 records has the scenario's numbers of versions and revisions
      Then the query "queries/each-record-has-the-scenarios-versions-and-revisions.rq" answers:
        | record         | versions | revisions |
        | APP-ALG-PEANUT | 1        | 1         |
        | H1-ALG-CODEINE | 2        | 2         |
        | H1-ALG-LATEX   | 2        | 2         |
        | H1-ALG-PCN     | 1        | 1         |
        | H1-ALG-SULFA   | 2        | 2         |
        | H1-CON-BACK    | 2        | 3         |
        | H1-CON-BRONCH  | 2        | 2         |
        | H1-CON-HTN     | 1        | 1         |
        | H1-IMM-FLU25   | 1        | 1         |
        | H1-PROC-COLO   | 1        | 1         |
        | H1-PROC-ECHO   | 1        | 1         |
        | H1P-ALG-AMOX   | 1        | 1         |
        | H1P-CON-ECZEMA | 1        | 1         |
        | H1P-CON-OTITIS | 1        | 1         |
        | H2F-ALG-PCN    | 1        | 1         |
        | H2F-ALG-SULFA  | 1        | 1         |
        | H2F-CON-ASTHMA | 1        | 1         |
        | H2F-CON-HTN    | 1        | 1         |
        | H2F-IMM-FLU25  | 1        | 1         |
        | H2F-PROC-COLO  | 1        | 1         |
        | H2O-ALG-PCN    | 1        | 1         |
        | H2O-ALG-SULFA  | 1        | 1         |
        | H2O-CON-ASTHMA | 1        | 1         |
        | H2O-CON-HTN    | 1        | 1         |
        | H2O-IMM-FLU25  | 1        | 1         |
        | H2O-PROC-COLO  | 1        | 1         |
        | U-IMM-TDAP     | 1        | 1         |

    Example: each view and the labels file used the reference versions current at the end, and nothing else
      Then the query "queries/views-name-the-current-reference-versions.rq" answers:
        | view                                                           | used                                               |
        | <https://pod.alex-rivera.example/clinical/allergies.ttl>       | Cascade matcher rules version 2026.1               |
        | <https://pod.alex-rivera.example/clinical/allergies.ttl>       | SNOMED CT to RxNorm ingredient map version 2027-01 |
        | <https://pod.alex-rivera.example/clinical/allergies.ttl>       | CVX vaccine group table version 2026-08            |
        | <https://pod.alex-rivera.example/clinical/conditions.ttl>      | Cascade matcher rules version 2026.1               |
        | <https://pod.alex-rivera.example/clinical/conditions.ttl>      | SNOMED CT to RxNorm ingredient map version 2027-01 |
        | <https://pod.alex-rivera.example/clinical/conditions.ttl>      | CVX vaccine group table version 2026-08            |
        | <https://pod.alex-rivera.example/clinical/immunizations.ttl>   | Cascade matcher rules version 2026.1               |
        | <https://pod.alex-rivera.example/clinical/immunizations.ttl>   | SNOMED CT to RxNorm ingredient map version 2027-01 |
        | <https://pod.alex-rivera.example/clinical/immunizations.ttl>   | CVX vaccine group table version 2026-08            |
        | <https://pod.alex-rivera.example/clinical/procedures.ttl>      | Cascade matcher rules version 2026.1               |
        | <https://pod.alex-rivera.example/clinical/procedures.ttl>      | SNOMED CT to RxNorm ingredient map version 2027-01 |
        | <https://pod.alex-rivera.example/clinical/procedures.ttl>      | CVX vaccine group table version 2026-08            |
        | <https://pod.alex-rivera.example/clinical/patient-profile.ttl> | Cascade matcher rules version 2026.1               |
        | <https://pod.alex-rivera.example/clinical/patient-profile.ttl> | SNOMED CT to RxNorm ingredient map version 2027-01 |
        | <https://pod.alex-rivera.example/clinical/patient-profile.ttl> | CVX vaccine group table version 2026-08            |
        | <https://pod.alex-rivera.example/clinical/labels.ttl>          | Cascade matcher rules version 2026.1               |
        | <https://pod.alex-rivera.example/clinical/labels.ttl>          | SNOMED CT to RxNorm ingredient map version 2027-01 |
        | <https://pod.alex-rivera.example/clinical/labels.ttl>          | CVX vaccine group table version 2026-08            |

    Example: the labels file gives each other thing one label, and states of itself only that it is a view and what it used
      Then the query "queries/labels-name-each-thing-once.rq" answers nothing

    Example: no two things share a label
      Then the query "queries/no-two-things-share-a-label.rq" answers nothing
