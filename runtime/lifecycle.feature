Feature: Medication lifecycle

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Ben
  enters fourteen medications, each named by the status it states: a FHIR code in capitals, an abbreviation, none, a
  blank one, FHIR codes, the HL7 v3 ActStatus codes a C-CDA medication activity carries, a synonym, phrases and text
  nothing matches.

  Rule: L1. A medication entry's status is classed active, stopped, paused, unknown or entered-in-error by the first step of this order that holds
    The entry's status is the one of the member it takes its status from. The class is the concept of rec:MedicationLifecycle
    the entry shows as rec:lifecycle (derived as rec:statusLifecycle), and the step that gave it as
    rec:statusLifecycleStep. The rows each step reads, and the
    precedence of step 5, are in queries/v1-draft/derivations/medication-lifecycles.rq.

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
          ?record pav:hasCurrentVersion/clinical:drugName ?medication ; rec:inEntry ?entry .
          ?entry rec:lifecycle ?lifecycle ; rec:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication         | lifecycle            | step |
        | "status: ON-HOLD"  | rec:MedicationPaused  | 3    |
        | "status: d/c"      | rec:MedicationStopped | 4    |

    Example: step 2, an absent or a blank status is unknown
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: none" "status: blank" }
          ?record pav:hasCurrentVersion/clinical:drugName ?medication ; rec:inEntry ?entry .
          ?entry rec:lifecycle ?lifecycle ; rec:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication        | lifecycle             | step |
        | "status: none"    | rec:MedicationUnknown | 2    |
        | "status: blank"   | rec:MedicationUnknown | 2    |

    Example: step 3, a FHIR status code has its own class
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: completed" "status: draft" }
          ?record pav:hasCurrentVersion/clinical:drugName ?medication ; rec:inEntry ?entry .
          ?entry rec:lifecycle ?lifecycle ; rec:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication           | lifecycle             | step |
        | "status: completed"  | rec:MedicationStopped | 3    |
        | "status: draft"      | rec:MedicationUnknown | 3    |

    Example: step 4, a synonym has its code's class, as does a C-CDA status the ConceptMap maps
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: discontinued" "status: aborted" "status: nullified" }
          ?record pav:hasCurrentVersion/clinical:drugName ?medication ; rec:inEntry ?entry .
          ?entry rec:lifecycle ?lifecycle ; rec:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication              | lifecycle                      | step |
        | "status: discontinued"  | rec:MedicationStopped          | 4    |
        | "status: aborted"       | rec:MedicationStopped          | 4    |
        | "status: nullified"     | rec:MedicationEnteredInError   | 4    |

    Example: step 5, a fragment gives the most conservative class, so a medication no longer taken is stopped
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: no longer taking" "status: suspended" "status: currently taking" }
          ?record pav:hasCurrentVersion/clinical:drugName ?medication ; rec:inEntry ?entry .
          ?entry rec:lifecycle ?lifecycle ; rec:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication                  | lifecycle             | step |
        | "status: no longer taking"  | rec:MedicationStopped | 5    |
        | "status: suspended"         | rec:MedicationPaused  | 5    |
        | "status: currently taking"  | rec:MedicationActive  | 5    |

    Example: step 6, text nothing matches is unknown and unmatched, as is a C-CDA status the ConceptMap leaves unmapped
      When the query is:
        """
        SELECT ?medication ?lifecycle ?step WHERE {
          VALUES ?medication { "status: see pharmacy" "status: new" }
          ?record pav:hasCurrentVersion/clinical:drugName ?medication ; rec:inEntry ?entry .
          ?entry rec:lifecycle ?lifecycle ; rec:statusLifecycleStep ?step .
        }
        """
      Then it answers:
        | medication              | lifecycle             | step |
        | "status: see pharmacy"  | rec:MedicationUnknown | 6    |
        | "status: new"           | rec:MedicationUnknown | 6    |
