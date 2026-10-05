Feature: Nothing is edited or deleted

  Rule: X1. No file, once written, changes or goes
    A retraction, a later revision and an entered-in-error status each leave everything they follow in the pod.

    Example: a later revision leaves the earlier revision and version in the files the earlier step wrote
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      When the export "new-content" is imported on 2026-01-06 at 10:00
      Then the query "queries/a-later-revision-keeps-the-earlier.rq" answers:
        | step                            | version                       | at                                   |
        | <urn:cascade:step:first-export> | version 1 of allergy "Peanut" | "2026-01-02T10:00:00Z"^^xsd:dateTime |
        | <urn:cascade:step:first-export> | version 1 of allergy "Peanut" |                                      |
        | <urn:cascade:step:new-content>  | version 2 of allergy "Peanut" | "2026-01-06T10:00:00Z"^^xsd:dateTime |
        | <urn:cascade:step:new-content>  | version 2 of allergy "Peanut" |                                      |
