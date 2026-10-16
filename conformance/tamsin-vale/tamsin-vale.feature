Feature: Tamsin Vale's pod
  The fourth scenario every runtime must pass, cascade-runtime-js#343: one hospital's record pulled twice, a year
  apart, with a medication stopped between the pulls. Cascade North, a demo hospital that keeps every version of a
  record, answers each pull as the record stood on its date: on 2024-02-01 Tamsin's metformin is taken and three of her
  A1c results are in; on 2025-02-01 the metformin was stopped on 2024-04-15 and three more results have come. Both
  pulls were saved by the runtime's own pull, from the demo hospital's versions. Each planted case T1 to T4 is a rule,
  and each example reads the pod at the smallest set of steps at which it can fail for its own reason. A record, a
  profile and a person's judgment are named by the handle expected/handles.json gives it: CN is Cascade North's FHIR,
  MED a medication and A1C a result, numbered in the order it was taken. J1 claims the profile both pulls name for
  her, CN-PAT, so her records are in the views.

  Background: Tamsin's story
    Given a new pod for Tamsin on 2024-02-01 at 09:00 (E1)
    And the pull "north-2024-02" is imported on 2024-02-01 at 09:05 (E2)
    And Tamsin files the judgment "J1" on 2024-02-01 at 09:05:30
    And the pull "north-2025-02" is imported on 2025-02-01 at 09:05 (E3)

  Rule: T1. The first pull sees the metformin taken
    The first pull holds version 1 of CN-MED-METFORMIN, active since 2022-03-01, with no end.

    Example: after the first pull, CN-MED-METFORMIN has one revision, active
      When the pod is read as it stood after "J1"
      Then CN-MED-METFORMIN has these revisions:
        | arrived             | version | status | end date | after |
        | 2024-02-01 at 09:05 | 1       | active |          |       |
      And the entry of CN-MED-METFORMIN shows:
        | field  | value  |
        | status | active |

  Rule: T2. The second pull sees it stopped, as a revision
    The second pull holds the same record with new content: completed, ended 2024-04-15. By A5 it is a revision after
    the first, and the entry shows the record as the second pull has it.

    Example: CN-MED-METFORMIN's second revision sets it completed, after the first
      Then CN-MED-METFORMIN has these revisions:
        | arrived             | version | status    | end date   | after               |
        | 2024-02-01 at 09:05 | 1       | active    |            |                     |
        | 2025-02-01 at 09:05 | 2       | completed | 2024-04-15 | 2024-02-01 at 09:05 |
      And the entry of CN-MED-METFORMIN shows:
        | field  | value     |
        | status | completed |

  Rule: T3. A result pulled again unchanged writes nothing
    CN-A1C-1 to CN-A1C-3 are in both pulls, each with the same content. Each arrives again under the source version its
    revision already carries, so by A3 the second pull writes no revision of them, and each still dates from the first.

    Example: the results of the first pull each have one revision, from E2
      Then the records have these revisions:
        | record   | arrived             | version | after |
        | CN-A1C-1 | 2024-02-01 at 09:05 | 1       |       |
        | CN-A1C-2 | 2024-02-01 at 09:05 | 1       |       |
        | CN-A1C-3 | 2024-02-01 at 09:05 | 1       |       |
      And the lab-results view holds these entries:
        | members  |
        | CN-A1C-1 |
        | CN-A1C-2 |
        | CN-A1C-3 |
        | CN-A1C-4 |
        | CN-A1C-5 |
        | CN-A1C-6 |

  Rule: T4. The results the second pull brought are new records
    CN-A1C-4 to CN-A1C-6 were taken after the first pull, so only the second holds them.

    Example: after the first pull the lab-results view holds its three results only
      When the pod is read as it stood after "J1"
      Then the lab-results view holds these entries:
        | members  |
        | CN-A1C-1 |
        | CN-A1C-2 |
        | CN-A1C-3 |
      And CN-A1C-4, CN-A1C-5 and CN-A1C-6 are in no view

    Example: the second pull's results each have one revision, from E3
      Then the records have these revisions:
        | record   | arrived             | version | after |
        | CN-A1C-4 | 2025-02-01 at 09:05 | 1       |       |
        | CN-A1C-5 | 2025-02-01 at 09:05 | 1       |       |
        | CN-A1C-6 | 2025-02-01 at 09:05 | 1       |       |
