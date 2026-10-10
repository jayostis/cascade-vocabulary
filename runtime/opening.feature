Feature: Opening a pod
  What a runtime does when it opens a pod with the tables it holds: an app opens a pod with its own, and a newer app
  holds newer versions.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Hana
  enters six flu shots in three pairs by date, and later one more, four drug allergies, four conditions and nine whose codes recur. Her pod is made with the
  vector tables, which are Priya's kit's series. App's tables open it: "app", holding version 1 of the vocabulary's rule
  list and version 1 of "CDC CVX vaccine groups", "app-later", holding versions 2 and 3 as well, "app-new-rules",
  holding a version 2 of the rule list and version 1 of the rule list as an app holds it after a query changed, its
  hash no longer the query's, and "app-rxnorm", holding "app"'s and the vocabulary's rule list's version 2, whose R3
  reads version 1 of "NLM RxNorm Prescribable product ingredients", which it also holds, and "app-icd", holding
  "app"'s, the rule list's versions 2 and 3, whose R7 reads version 1 of "CDC ICD-10-CM code conversions", which it
  also holds, and "app-periods", holding "app"'s and the rule list's versions 2 to 4, and no conversions.

  Rule: O1. Opening a pod adopts each series' default version that descends from the version the pod names, and judges what the tables newly join
    The default is M10's; a version descends from another along the tables' line of prov:wasRevisionOf. A series the
    pod names no version of is not adopted, since M10 already gives it the default. Opening, at the open's time:

    1. rechecks (M7), with each adopted version current;
    2. files a Same for each pair the current rule list and tables join and the pod's own do not, by M3 and M5 over
       those pairs. A pair a rule joins with a version's rows is new unless a rule of that justification in the rule
       list the pod names joins it with the version the pod names of that series, or, for a rule reading no table,
       joins it at all. A rule list the pod names that M11 would refuse joins nothing. So a series the pod names no
       version of, or a rule the pod's rule list lacks, judges every pair it joins, but a pair of which a person
       retracted a matcher Same: the everyday lens lets a Same count however a retracted one was made;
    3. writes the reference descriptions last: those M8 writes, and each version on the line after the pod's up to the
       adopted one, oldest first.

    An open that finds nothing new writes nothing, so opening again is always safe.

    Background:
      Given a new pod for Hana on 2026-07-01 at 09:00
      And the pod is opened with the tables "app" on 2026-07-01 at 09:01
      And Hana enters "flu-shots" on 2026-07-02 at 09:00
      And the matcher runs on the records of that entry on 2026-07-02 at 09:05

    Example: adopting describes each version after the pod's up to the adopted one
      When the pod is opened with the tables "app-later" on 2026-07-03 at 09:00
      Then that step wrote these reference descriptions:
        | reference                        |
        | CDC CVX vaccine groups version 2 |
        | CDC CVX vaccine groups version 3 |

    Example: adopting files again each Same the adopted rows still join, and a Same of each pair only they join
      Version 3 withdraws 150's row, so Fluarix and FluLaval are not joined again.

      When the pod is opened with the tables "app-later" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification             | members                                                                    | used                                                                                                                                                             |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | Matcher rules version 1, CDC CVX vaccine groups version 3, version 1 of immunization CVX 141 "Fluad", version 1 of immunization CVX 161 "Fluzone Quadrivalent" |
        | same mapped code and date | immunization CVX 140 "Afluria", immunization CVX 141 "Flublok"            | Matcher rules version 1, CDC CVX vaccine groups version 3, version 1 of immunization CVX 140 "Afluria", version 1 of immunization CVX 141 "Flublok"            |

    Example: a pair the replaced version joined is not judged again, so a Same a person retracted stays retracted
      Version 3 changes 161's row, which does not make its pairs new.

      Given Hana files the judgment "retract-fluad" on 2026-07-02 at 12:00
      When the pod is opened with the tables "app-later" on 2026-07-03 at 09:00
      Then the matcher's judgments holding immunization CVX 141 "Fluad" are:
        | justification             | members                                                                    | at                  |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | 2026-07-02 at 09:05 |

    Example: a rule list the pod names that M11 now refuses joins nothing, so the adopted rule list judges every pair
      When the pod is opened with the tables "app-new-rules" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification             | members                                                                    | used                                                                                                                                                             |
        | same mapped code and date | immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval"           | Matcher rules version 2, CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluarix", version 1 of immunization CVX 150 "FluLaval"           |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | Matcher rules version 2, CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluad", version 1 of immunization CVX 161 "Fluzone Quadrivalent" |

    Example: opening again with the same tables writes nothing
      When the pod is opened with the tables "app-later" on 2026-07-03 at 09:00
      And the pod is opened with the tables "app-later" on 2026-07-04 at 09:00 (again)
      Then that step wrote no file

    Example: after the rule list's version 2 is adopted, R3 joins a brand allergy and its ingredient's, and not a two-ingredient product and one of its ingredients
      Augmentin is amoxicillin and clavulanate, so its ingredient is the concept of both, not amoxicillin.

      When the pod is opened with the tables "app-rxnorm" on 2026-07-03 at 09:00
      And Hana enters "allergies" on 2026-07-04 at 09:00
      And the matcher runs on the records of that entry on 2026-07-04 at 09:05 (match-allergies)
      Then the matcher's judgments holding allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen", allergy RxNorm 151392 "Augmentin" and allergy RxNorm 723 "Amoxicillin" are:
        | justification    | members                                                       | used                                                                                                                                                         |
        | same mapped code | allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen" | Matcher rules version 2, NLM RxNorm Prescribable product ingredients version 1, version 1 of allergy RxNorm 153010 "Advil", version 1 of allergy RxNorm 5640 "Ibuprofen" |

    Example: adopting the rule list's version 2 judges the pairs its new R3 joins among records already matched
      Given Hana enters "allergies" on 2026-07-02 at 10:00
      And the matcher runs on the records of that entry on 2026-07-02 at 10:05 (match-allergies)
      When the pod is opened with the tables "app-rxnorm" on 2026-07-03 at 09:00
      Then the matcher's judgments holding allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen", allergy RxNorm 151392 "Augmentin" and allergy RxNorm 723 "Amoxicillin" are:
        | justification    | members                                                       | at                  | used                                                                                                                                                         |
        | same mapped code | allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen" | 2026-07-03 at 09:00 | Matcher rules version 2, NLM RxNorm Prescribable product ingredients version 1, version 1 of allergy RxNorm 153010 "Advil", version 1 of allergy RxNorm 5640 "Ibuprofen" |
      And that step wrote these reference descriptions:
        | reference                                             |
        | Matcher rules version 2                               |
        | NLM RxNorm Prescribable product ingredients           |
        | NLM RxNorm Prescribable product ingredients version 1 |

    Example: after the rule list's version 3 is adopted, R7 joins a condition on a retired code and one on its conversion, and not a split code and one of its parts
      T84.040A converts to M97.01XA alone; D69.1 split into D69.11 and D69.19, so it has no row.

      When the pod is opened with the tables "app-icd" on 2026-07-03 at 09:00
      And Hana enters "conditions" on 2026-07-04 at 09:00
      And the matcher runs on the records of that entry on 2026-07-04 at 09:05 (match-conditions)
      Then the matcher's judgments holding condition ICD-10-CM T84.040A, condition ICD-10-CM M97.01XA, condition ICD-10-CM D69.1 and condition ICD-10-CM D69.11 are:
        | justification       | members                                                                                                                                                                                 | used                                                                                                                                                                                                                                                                                 |
        | same converted code | condition ICD-10-CM M97.01XA "Periprosthetic fracture around internal prosthetic right hip joint, initial encounter", condition ICD-10-CM T84.040A "Periprosthetic fracture, right hip" | Matcher rules version 3, CDC ICD-10-CM code conversions version 1, version 1 of condition ICD-10-CM M97.01XA "Periprosthetic fracture around internal prosthetic right hip joint, initial encounter", version 1 of condition ICD-10-CM T84.040A "Periprosthetic fracture, right hip" |

    Example: adopting the rule list's version 3 judges the pairs its new R7 joins among records already matched
      Given Hana enters "conditions" on 2026-07-02 at 10:00
      And the matcher runs on the records of that entry on 2026-07-02 at 10:05 (match-conditions)
      When the pod is opened with the tables "app-icd" on 2026-07-03 at 09:00
      Then the matcher's judgments holding condition ICD-10-CM T84.040A, condition ICD-10-CM M97.01XA, condition ICD-10-CM D69.1 and condition ICD-10-CM D69.11 are:
        | justification       | members                                                                                                                                                                                 | at                  | used                                                                                                                                                                                                                                                                                 |
        | same converted code | condition ICD-10-CM M97.01XA "Periprosthetic fracture around internal prosthetic right hip joint, initial encounter", condition ICD-10-CM T84.040A "Periprosthetic fracture, right hip" | 2026-07-03 at 09:00 | Matcher rules version 3, CDC ICD-10-CM code conversions version 1, version 1 of condition ICD-10-CM M97.01XA "Periprosthetic fracture around internal prosthetic right hip joint, initial encounter", version 1 of condition ICD-10-CM T84.040A "Periprosthetic fracture, right hip" |
      And that step wrote these reference descriptions:
        | reference                                |
        | Matcher rules version 2                  |
        | Matcher rules version 3                  |
        | CDC ICD-10-CM code conversions           |
        | CDC ICD-10-CM code conversions version 1 |

    Example: adopting the rule list's version 4 judges the pairs its new R8 joins among records already matched, and the earlier same code of two episodes apart no longer counts
      R1 joined the two pharyngitis episodes under version 1. Version 4 takes conditions out of R1, so nothing is
      filed again for them and the earlier Same is not retracted, but it was made with a version that now has a newer
      current one, so it no longer counts and the episodes split.

      Given Hana enters "episodes" on 2026-07-02 at 10:00
      And the matcher runs on the records of that entry on 2026-07-02 at 10:05 (match-episodes)
      When the pod is opened with the tables "app-periods" on 2026-07-03 at 09:00
      Then the matcher's judgments holding condition SNOMED 195662009 "Acute viral pharyngitis, 2017", condition SNOMED 195662009 "Acute viral pharyngitis, 2020", condition ICD-10-CM J18.9 "Pneumonia, first report", condition ICD-10-CM J18.9 "Pneumonia, second report", condition ICD-10-CM E11.9 "Type 2 diabetes, clinic" and condition ICD-10-CM E11.9 "Type 2 diabetes, hospital" are:
        | justification        | members                                                                                                                 | at                  | used                                                                                                                                                                         |
        | same code            | condition SNOMED 195662009 "Acute viral pharyngitis, 2017", condition SNOMED 195662009 "Acute viral pharyngitis, 2020" | 2026-07-02 at 10:05 | Matcher rules version 1, version 1 of condition SNOMED 195662009 "Acute viral pharyngitis, 2017", version 1 of condition SNOMED 195662009 "Acute viral pharyngitis, 2020"    |
        | same code and period | condition ICD-10-CM J18.9 "Pneumonia, first report", condition ICD-10-CM J18.9 "Pneumonia, second report"               | 2026-07-03 at 09:00 | Matcher rules version 4, version 1 of condition ICD-10-CM J18.9 "Pneumonia, first report", version 1 of condition ICD-10-CM J18.9 "Pneumonia, second report"               |
        | same code and period | condition ICD-10-CM E11.9 "Type 2 diabetes, clinic", condition ICD-10-CM E11.9 "Type 2 diabetes, hospital"              | 2026-07-03 at 09:00 | Matcher rules version 4, version 1 of condition ICD-10-CM E11.9 "Type 2 diabetes, clinic", version 1 of condition ICD-10-CM E11.9 "Type 2 diabetes, hospital"              |
      And the matcher's same code of condition SNOMED 195662009 "Acute viral pharyngitis, 2017" and condition SNOMED 195662009 "Acute viral pharyngitis, 2020" does not count
      And that step wrote these reference descriptions:
        | reference               |
        | Matcher rules version 2 |
        | Matcher rules version 3 |
        | Matcher rules version 4 |

  Rule: O2. A series the tables do not hold the pod's version of is left out, and nothing is written of it
    The tables may not hold the series at all, as for a pod made on other tables, or not the pod's version, as for a
    pod a newer app has opened. Rules reading that series' kind read no version of it, and the rest of the matcher
    runs. Its Sames are not rechecked, since no version the tables hold revises theirs, and they still count; the
    tables' own rules may judge the same pairs anew (O1). The
    runtime tells the app which versions it does not hold; no example can show that.

    Background:
      Given a new pod for Hana on 2026-07-01 at 09:00
      And Hana enters "flu-shots" on 2026-07-02 at 09:00
      And the matcher runs on the records of that entry on 2026-07-02 at 09:05 (match-kit)

    Example: a pod made on the vector tables, opened with an app's, is judged by the app's tables and writes nothing of the vector tables
      When the pod is opened with the tables "app" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification             | members                                                                    | used                                                                                                                                                             |
        | same mapped code and date | immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval"           | Matcher rules version 1, CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluarix", version 1 of immunization CVX 150 "FluLaval"           |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | Matcher rules version 1, CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluad", version 1 of immunization CVX 161 "Fluzone Quadrivalent" |
      And that step wrote these reference descriptions:
        | reference                       |
        | Matcher rules                   |
        | Matcher rules version 1         |
        | CDC CVX vaccine groups          |
        | CDC CVX vaccine groups version 1 |

    Example: the app's tables do not judge a pair of which a person retracted the vector tables' Same
      Given Hana files the judgment "retract-fluarix" on 2026-07-02 at 12:00
      When the pod is opened with the tables "app" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification             | members                                                                    | used                                                                                                                                                             |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | Matcher rules version 1, CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluad", version 1 of immunization CVX 161 "Fluzone Quadrivalent" |

    Example: the vector tables' Same still counts beside the app's
      When the pod is opened with the tables "app" on 2026-07-03 at 09:00
      And the query is:
        """
        PREFIX jdg: <https://ns.cascadeprotocol.org/judgments/v1-draft#>
        SELECT ?rules WHERE {
          ?judgment rec:counts true ; jdg:justification jdg:SameMappedCodeAndDate ; prov:used ?rules .
          ?rules prov:specializationOf/rdfs:label ?label .
          FILTER (?label IN ("Cascade matcher rules", "Matcher rules"))
        }
        """
      Then it answers:
        | rules                           |
        | Cascade matcher rules version 1 |
        | Matcher rules version 1         |
        | Matcher rules version 1         |

    Example: a pod at a version the app does not hold is matched without that series
      When the pod is opened with the tables "app" on 2026-07-03 at 09:00
      And the pod is opened with the tables "app-later" on 2026-07-04 at 09:00
      And the pod is opened with the tables "app" on 2026-07-05 at 09:00 (older)
      And Hana enters "fluarix-again" on 2026-07-06 at 09:00
      And the matcher runs on the records of that entry on 2026-07-06 at 09:05
      Then "older" wrote no file
      And that step wrote these matcher judgments:
        | justification      | members                                                              | used                                                                                                                    |
        | same code and date | immunization CVX 141 "Fluarix Tetra", immunization CVX 141 "Fluarix" | Matcher rules version 1, version 1 of immunization CVX 141 "Fluarix Tetra", version 1 of immunization CVX 141 "Fluarix" |
