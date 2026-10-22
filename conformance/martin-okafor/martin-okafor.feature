Feature: Martin Okafor's pod
  The third scenario every runtime must pass, https://github.com/jayostis/cascade-vocabulary/issues/138: one variant
  in two FHIR reports, joined by the matcher, beside what ClinVar says of it. Harbourline Genetics' panel report of
  2022 and St Columba's Hospital's exome of 2024 each reach the pod as a saved pull. Each planted case M1 to M6 is a
  rule, and each example reads the pod at the smallest set of steps at which it can fail for its own reason. The cases
  are this story's, #138's, and are not the matcher's rules M1 to M17 in runtime/matcher.feature. A record, a profile
  and a person's judgment are named by the handle expected/handles.json gives it: HG is Harbourline's report, SC St
  Columba's, V a variant, I an interpretation, and a handle's prime in #138 (V1') is SC-V1.

  The story's table is a subset of the published ClinVar series' current version: the rows of two variations, 90011
  and 8931. Its version is named by a urn:uuid:, never by the N12 name of a published version, since an ni: name over
  a subset would read as a version some feed publishes. tables/clinvar-story/references.ttl says what it was derived
  from.

  Background: Martin's story
    Given a new pod for Martin on 2026-10-13 at 09:00 (E1)
    And the pod is opened with the tables "clinvar-story" on 2026-10-13 at 09:01 (E2)
    And the pull "harbourline-2022" is imported on 2026-10-13 at 09:10:04 (E3)
    And Martin files the judgment "J1" on 2026-10-13 at 09:10:30
    And the matcher runs on the records of "E3" on 2026-10-13 at 09:11 (E4)
    And the pull "st-columba-2024" is imported on 2026-10-13 at 09:20:04 (E5)
    And Martin files the judgment "J2" on 2026-10-13 at 09:20:30
    And the matcher runs on the records of "E5" on 2026-10-13 at 09:21 (E6)

  Rule: M1. Two reports on different transcript versions are one variant, through the table
    Harbourline's HG-V1 is NM_000249.3:c.2042C>T in MLH1 with no ClinVar ID. St Columba's SC-V1 is
    NM_000249.4:c.2042C>T with ClinVar ID 90011. The matcher finds the row 90011 for HG-V1 by its expression, which
    the row holds on both transcripts, and for SC-V1 by its ID. Nothing joins them until the second report arrives.

    Example: before St Columba's report the matcher has joined nothing
      When the pod is read as it stood after "E4"
      Then the matcher has no judgment holding HG-V1

    Example: the matcher joins the two reports through the table, and the view holds one variant
      Then the matcher's judgments holding HG-V1 are:
        | justification                    | members      | used                                                                                                                                      |
        | same variation through the table | HG-V1, SC-V1 | Matcher rules version 8, ClinVar variant classifications subset for Martin Okafor version 2026-10, version 1 of HG-V1, version 1 of SC-V1 |
      And the variants view holds these entries:
        | members      |
        | HG-V1, SC-V1 |

  Rule: M2. One report's classification differs from ClinVar's and another's agrees
    HG-I1, the 2022 report's, says uncertain significance; SC-I2, the 2024 report's, says likely pathogenic. Neither
    overwrites the other: each is an entry of its own, pointing to the one variant entry. Whether each agrees with
    ClinVar's row is not in a view; the vocabulary's tables/agreement.rq fixture and the runtime's tests hold it.

    Example: each interpretation is its own entry, and both point to the variant of M1
      Then the variant-interpretations view holds these entries:
        | members |
        | HG-I1   |
        | SC-I2   |
      When the query is:
        """
        PREFIX cascade: <https://ns.cascadeprotocol.org/cascade#>
        SELECT ?interpretation ?variant WHERE {
          ?entry a cascade:VariantInterpretation ; cascade:mergedFrom ?interpretation ; cascade:variantInterpreted ?variantEntry .
          ?variantEntry a cascade:GeneticVariantFinding ; cascade:clinvarVariationId "90011" ; cascade:mergedFrom ?variant .
        }
        """
      Then it answers:
        | interpretation | variant |
        | HG-I1          | HG-V1   |
        | HG-I1          | SC-V1   |
        | SC-I2          | HG-V1   |
        | SC-I2          | SC-V1   |

  Rule: M3. A benign variant shown without alarm
    Both reports carry V2, NM_000179.3:c.2633T>C in MSH6 with ClinVar ID 8931, and both interpret it as benign.

    Example: V2 is one entry with two interpretations pointing to it
      Then the variants view holds these entries:
        | members      |
        | HG-V2, SC-V2 |
      And the variant-interpretations view holds these entries:
        | members |
        | HG-I3   |
        | SC-I4   |
      When the query is:
        """
        SELECT ?interpretation ?variant WHERE {
          ?entry a cascade:VariantInterpretation ; cascade:mergedFrom ?interpretation ; cascade:variantInterpreted ?variantEntry .
          ?variantEntry a cascade:GeneticVariantFinding ; cascade:clinvarVariationId "8931" ; cascade:mergedFrom ?variant .
        }
        """
      Then it answers:
        | interpretation | variant |
        | HG-I3          | HG-V2   |
        | HG-I3          | SC-V2   |
        | SC-I4          | HG-V2   |
        | SC-I4          | SC-V2   |

  Rule: M4. A gene the version does not cover
    SC-V4 is NM_000059.4:c.7865A>G in BRCA2, a gene outside the five the story's version covers, reported with no
    ClinVar ID. It joins nothing.

    Example: SC-V4 is an entry of its own with its interpretation, and no judgment holds it
      Then the variants view holds these entries:
        | members |
        | SC-V4   |
      And the variant-interpretations view holds these entries:
        | members |
        | SC-I5   |
      And the matcher has no judgment holding SC-V4

  Rule: M5. A covered gene, an expression the table does not hold
    HG-V5 is NM_001258271.2:c.1111A>T in MLH1, reported with no ClinVar ID. MLH1 is covered, but no row of the story's
    version holds that expression, so it finds no row and joins nothing.

    Example: HG-V5 is an entry of its own with its interpretation, and no judgment holds it
      Then the variants view holds these entries:
        | members |
        | HG-V5   |
      And the variant-interpretations view holds these entries:
        | members |
        | HG-I6   |
      And the matcher has no judgment holding HG-V5

  Rule: M6. Two reports carrying one ClinVar ID are one variant without the table
    HG-V2 and SC-V2 carry ID 8931, so the rule that joins by ID has them; the rule that reads the table leaves a pair
    that shares an ID alone, though both carry an expression the story's version holds. The judgment uses no table.

    Example: the matcher joins them as the same variation, and uses no table version
      Then the matcher's judgments holding HG-V2 are:
        | justification  | members      | used                                                            |
        | same variation | HG-V2, SC-V2 | Matcher rules version 8, version 1 of HG-V2, version 1 of SC-V2 |
      And the variants view holds these entries:
        | members      |
        | HG-V2, SC-V2 |

  Rule: Nothing else is joined
    His conditions, medications and colonoscopy are entries of their own views, and no judgment joins any of them to a
    variant. The matcher writes the descriptions of the series it used, with the first judgment that used them (M8 of
    the matcher's rules), and none when it judged nothing.

    Example: St Columba's run wrote the two joins of M1 and M6, and no other
      Then "E6" wrote these matcher judgments:
        | justification                    | members      |
        | same variation through the table | HG-V1, SC-V1 |
        | same variation                   | HG-V2, SC-V2 |
      And "E6" wrote these reference descriptions:
        | reference                                                                |
        | Matcher rules                                                            |
        | Matcher rules version 8                                                  |
        | ClinVar variant classifications subset for Martin Okafor                 |
        | ClinVar variant classifications subset for Martin Okafor version 2026-10 |

    Example: Harbourline's run judged nothing, so wrote no description
      Then "E4" wrote these reference descriptions:
        | reference |

  Rule: His claims tie two profiles to him
    J1 and J2 each claim the profile one report names for him: HG-PAT and SC-PAT.

    Example: the patient profile is one entry of the two profiles
      Then the patient-profile view holds these entries:
        | members        |
        | HG-PAT, SC-PAT |
