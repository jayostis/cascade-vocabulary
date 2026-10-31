Feature: Medication lifecycle

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Ben
  enters fifteen medications, each named by the status it states: a FHIR code in capitals, an abbreviation, none, a
  blank one, FHIR codes, the HL7 v3 ActStatus codes a C-CDA medication activity carries, a synonym, phrases, run-together text and text
  nothing matches. He also enters five dispenses, each named by the status it states.

  Rule: L1. A medication record's status, and so its entry's, is classed active, stopped, paused, unknown or entered-in-error by the first step of this order that holds
    decisions/one-meaning-per-term.md, rows "3. a medication's status" and "5. one status for every kind", and
    decisions/medications.md, row "a copy's own lifecycle".
    Each record in an entry is classed by the status of its own current version, derived as
    cascade:currentVersionStatusLifecycle and cascade:currentVersionStatusLifecycleStep, which a rule reads. The entry
    has the class and step of the member it takes its status from, and is unknown at step 2 when no member gives one.
    The class is the concept of cascade:MedicationLifecycle the entry shows as cascade:lifecycle (derived as
    cascade:statusLifecycle), and the step that gave it as cascade:statusLifecycleStep. The rows each step reads, and the
    precedence of step 5, are in queries/derivations/medication-lifecycles.rq.

    1. The key is the status lower-cased, each run of other characters than a-z and 0-9 made one space, and trimmed. A
       key also equals a row's text when both agree with their spaces removed.
    2. A blank or absent status is FHIR's data-absent-reason unknown: class unknown. The status of a FHIR resource is
       1..1, so an absent one is not known, not ended.
    3. A key equal to a code of FHIR R4's MedicationRequest.status or MedicationStatement.status has that code's class:
       active is active; completed, stopped, cancelled and not-taken are stopped; on-hold is paused; draft, intended and
       unknown are unknown; entered-in-error is entered-in-error.
    4. A key equal to a synonym has the class of the FHIR code the synonym means. A C-CDA's statuses are HL7 v3
       ActStatus codes, which the C-CDA on FHIR ConceptMap CF-MedicationStatus maps to FHIR's: active to active,
       suspended to on-hold, aborted to stopped, completed to completed and nullified to entered-in-error; held, new,
       cancelled, normal and obsolete it leaves unmapped, but held is a synonym of on-hold, cancelled is FHIR's own
       code, and the rest are step 6. The status is not told from where it came: a FHIR code or synonym is that, whoever
       wrote it.
    5. A key that contains fragments has the most conservative class among them, in the order entered-in-error, stopped,
       paused, unknown, active.
    6. Any other status is unknown, and its step is 6: it is reported as unmatched.

    A negated hold, as "no longer on hold", is not read: no order of fragments reads it right, and it is classed stopped.

    Background:
      Given a new pod for Ben on 2026-02-01 at 08:00
      And Ben enters "medication-statuses" on 2026-02-01 at 08:30

    Example: step 1, the status is read in lower case without punctuation, and with its spaces removed
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: ON-HOLD" "status: d/c" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle ; cascade:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication        | lifecycle                 | step |
        | "status: ON-HOLD" | cascade:MedicationPaused  | 3    |
        | "status: d/c"     | cascade:MedicationStopped | 4    |

    Example: step 2, an absent or a blank status is unknown
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: none" "status: blank" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle ; cascade:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication      | lifecycle                 | step |
        | "status: none"  | cascade:MedicationUnknown | 2    |
        | "status: blank" | cascade:MedicationUnknown | 2    |

    Example: step 3, a FHIR status code has its own class
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: completed" "status: draft" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle ; cascade:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication          | lifecycle                 | step |
        | "status: completed" | cascade:MedicationStopped | 3    |
        | "status: draft"     | cascade:MedicationUnknown | 3    |

    Example: step 4, a synonym has its code's class, as does a C-CDA status the ConceptMap maps
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: discontinued" "status: aborted" "status: nullified" "status: suspended" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle ; cascade:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication             | lifecycle                        | step |
        | "status: discontinued" | cascade:MedicationStopped        | 4    |
        | "status: aborted"      | cascade:MedicationStopped        | 4    |
        | "status: nullified"    | cascade:MedicationEnteredInError | 4    |
        | "status: suspended"    | cascade:MedicationPaused         | 4    |

    Example: step 5, a fragment gives the most conservative class, so a medication no longer taken is stopped, however its words are run together
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: no longer taking" "status: NotActive" "status: currently taking" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle ; cascade:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication                 | lifecycle                 | step |
        | "status: no longer taking" | cascade:MedicationStopped | 5    |
        | "status: NotActive"        | cascade:MedicationStopped | 5    |
        | "status: currently taking" | cascade:MedicationActive  | 5    |

    Example: step 6, text nothing matches is unknown and unmatched, as is a C-CDA status the ConceptMap leaves unmapped
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: see pharmacy" "status: new" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle ; cascade:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication             | lifecycle                 | step |
        | "status: see pharmacy" | cascade:MedicationUnknown | 6    |
        | "status: new"          | cascade:MedicationUnknown | 6    |

  Rule: L2. A pharmacy's dispense is classed completed, in progress, not completed, unknown or entered-in-error by its own status, and never by L1
    decisions/medications.md, row "a dispense's lifecycle".
    Each dispense in an entry is classed by the status of its own current version, derived as
    cascade:currentVersionStatusLifecycle, and the entry has the class of the member it takes its status from, or unknown
    when no member gives one, as cascade:statusLifecycle; the view says it as cascade:lifecycle. The classes are the
    concepts of cascade:MedicationDispenseLifecycle. The key is the status lower-cased with every character other than
    a-z and 0-9 removed. FHIR R4's MedicationDispense.status codes have these classes: completed is completed;
    preparation, in-progress and on-hold are in progress; cancelled, declined and stopped are not completed;
    entered-in-error is entered-in-error; unknown is unknown. An absent status, and any other, is unknown. A completed
    dispense is a fill picked up: it never reads as a stopped medication, and no course ends by it.

    Background:
      Given a new pod for Ben on 2026-02-01 at 08:00
      And Ben enters "medication-dispense-statuses" on 2026-02-01 at 08:30

    Example: a FHIR dispense status has its own class, read without case or punctuation, and an absent or other status is unknown
      When the query is:
        """
        SELECT ?medication ?lifecycle WHERE {
          VALUES ?medication { "dispense: completed" "dispense: In Progress" "dispense: stopped" "dispense: none" "dispense: picked up" }
          ?record pav:hasCurrentVersion/cascade:drugName ?medication ; cascade:inEntry ?entry .
          ?entry cascade:statusLifecycle ?lifecycle .
        }
        """
      Then it answers:
        | medication              | lifecycle                                  |
        | "dispense: completed"   | cascade:MedicationDispenseCompleted        |
        | "dispense: In Progress" | cascade:MedicationDispenseInProgress       |
        | "dispense: stopped"     | cascade:MedicationDispenseNotCompleted     |
        | "dispense: none"        | cascade:MedicationDispenseUnknown          |
        | "dispense: picked up"   | cascade:MedicationDispenseUnknown          |
