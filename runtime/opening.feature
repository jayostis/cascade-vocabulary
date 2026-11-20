Feature: Opening a pod
  What a runtime does when it opens a pod: whether it can read the pod, and what it adopts with the tables it holds: an
  app opens a pod with its own, and a newer app holds newer versions.

  Each pod starts empty, at https://pod.example/, with one person as its subject (scripted-input/people.ttl). Hana
  enters six flu shots in three pairs by date, and later one more, four drug allergies, four conditions and nine whose codes recur. Her pod is made with the
  vector tables, which are Priya's kit's series. App's tables open it, each a folder of the rule list's versions and
  the tables an app holds: "app", holding an earlier version "0" of the rule list, whose rows are R1, which also applies
  to conditions there, R2, R4 and R7 as the vocabulary's version 19 has them, and version 1 of "CDC CVX vaccine groups";
  "app-later", holding versions 2 and 3 of that table as well; "app-rxnorm", "app-icd" and "app-periods", holding
  "app"'s and the vocabulary's version 19, which revises version "0", with version 1 of "NLM RxNorm Prescribable product
  ingredients", of "CDC ICD-10-CM code conversions" and of no further table respectively; "app-later-on-19", holding
  "app-later"'s tables with version 19, which revises version "0"; "app-new-rules", holding the
  vocabulary's version 19 and version "0" as an app holds it after a query changed, R2's hash no longer the query's;
  "app-fewer-rules", holding a version "0a" that revises version "0" and lacks R4; and "app-wrong-rule", holding the
  same but a version "0b" in place of "0a" that also declares R4 wrong.

  Rule: O1. Opening a pod adopts each series' default version that descends from the version the pod names, and judges what the tables newly join
    No note rules this.
    The default is M10's; a version descends from another along the tables' line of prov:wasRevisionOf. A series the
    pod names no version of is not adopted, since M10 already gives it the default. Opening, at the open's time:

    1. rechecks (M7), with each adopted version current;
    2. files a Same for each pair the current rule list and tables join and the pod's own do not, by M3 and M5 over
       those pairs. A pair a rule joins with a version's rows is new unless a rule of that justification in the rule
       list the pod names joins it with the version the pod names of that series, or, for a rule reading no table,
       joins it at all. Each is judged over its own versions alone (M13): the rule list the pod names over the versions
       the pod names, the current one over the current versions, so neither reads the other's rows or descriptions. A
       rule list the pod names that M11 would refuse joins nothing. So a series the pod names no
       version of, or a rule the pod's rule list lacks, judges every pair it joins;
    3. writes the reference descriptions last: those M8 writes, and each version on the line after the pod's up to the
       adopted one, oldest first.

    An open that finds nothing new writes nothing, so opening again is always safe. Before its matcher run, an open
    whose adopted rule list version, or a version it revises, declares a matcher rule wrong performs the migration N15 says.

    A Same the open does not file again stays in the pod. A Same whose members the adopted version joins as the
    version it used did is left as it was and counts on (M7). Once a version it used has a newer current one that does
    not join its members, or no current rule list version runs the query it was asserted with (M5), it has lapsed
    (cascade:lapsed, derived, nothing written for it), unless something retracts it or a judgment not itself retracted replaces it, and "What
    needs review" lists its pair, if now in two entries, until a person judges it: with the finding that names it,
    when the open's run files one of the adopted rule list version's matcher judgments it no longer reaches (M18, M19), and
    otherwise alone. A Same whose rule the adopted rule
    list runs with the query it was asserted with is reached again without anything written (M9), and counts on.

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

    Example: adopting files no Same the adopted rows still join, and a Same of each pair only they join
      Version 3 withdraws 150's row, so Fluarix and FluLaval are not joined again. It still puts 141 and 161 in one
      group, so the Same of Fluad and Fluzone Quadrivalent by version 1 counts on, and 140 newly in it.

      When the pod is opened with the tables "app-later" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification             | members                                                        | used                                                                                                                       |
        | same mapped code and date | immunization CVX 140 "Afluria", immunization CVX 141 "Flublok" | CDC CVX vaccine groups version 3, version 1 of immunization CVX 140 "Afluria", version 1 of immunization CVX 141 "Flublok" |
      And the matcher's same mapped code and date of immunization CVX 141 "Fluad" and immunization CVX 161 "Fluzone Quadrivalent" counts
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" has lapsed

    Example: a rule list the pod names that M11 now refuses joins nothing, so the adopted rule list judges every pair, and finds each matcher judgment asserted with the query it runs
      Version 19 runs the vaccine group query the Sames were asserted with under version "0", so judging the pairs anew
      reaches the matcher judgments the pod holds, asserted already (M9): nothing is written of them, and they count on.

      When the pod is opened with the tables "app-new-rules" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification | members |
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" counts
      And the matcher's same mapped code and date of immunization CVX 141 "Fluad" and immunization CVX 161 "Fluzone Quadrivalent" counts

    Example: opening again with the same tables writes nothing
      When the pod is opened with the tables "app-later" on 2026-07-03 at 09:00
      And the pod is opened with the tables "app-later" on 2026-07-04 at 09:00 (again)
      Then that step wrote no file

    Example: adopting a rule list version that adds R3 judges the pairs R3 joins among records already matched, and asserts no matcher judgment of a rule it left unchanged
      R3 joins a brand allergy and its ingredient's, and not a two-ingredient product and one of its ingredients:
      Augmentin is amoxicillin and clavulanate, so its ingredient is the concept of both, not amoxicillin. Version 19 runs
      version "0"'s vaccine group query, so the flu shots' matcher judgments, asserted with it under version "0", are not
      asserted again, and count on.

      Given Hana enters "allergies" on 2026-07-02 at 10:00
      And the matcher runs on the records of that entry on 2026-07-02 at 10:05 (match-allergies)
      When the pod is opened with the tables "app-rxnorm" on 2026-07-03 at 09:00
      Then the matcher's judgments holding allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen", allergy RxNorm 151392 "Augmentin" and allergy RxNorm 723 "Amoxicillin" are:
        | justification    | members                                                        | used                                                                                                                                            |
        | same mapped code | allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen" | NLM RxNorm Prescribable product ingredients version 1, version 1 of allergy RxNorm 153010 "Advil", version 1 of allergy RxNorm 5640 "Ibuprofen" |
      And that step wrote these matcher judgments:
        | justification    | members                                                        |
        | same mapped code | allergy RxNorm 153010 "Advil", allergy RxNorm 5640 "Ibuprofen" |
      And the matcher's same mapped code and date of immunization CVX 141 "Fluad" and immunization CVX 161 "Fluzone Quadrivalent" counts
      And that step wrote these reference descriptions:
        | reference                                             |
        | Matcher rules version 19                              |
        | NLM RxNorm Prescribable product ingredients           |
        | NLM RxNorm Prescribable product ingredients version 1 |

    Example: adopting a table of a series the pod names no version of judges the pairs its rows join among records already matched
      R7 joins a condition on a retired code and one on the one code it converts to: T84.040A converts to M97.01XA alone,
      1:1, and D69.1 split into D69.11 and D69.19, 1:n, so it joins nothing.

      Given Hana enters "conditions" on 2026-07-02 at 10:00
      And the matcher runs on the records of that entry on 2026-07-02 at 10:05 (match-conditions)
      When the pod is opened with the tables "app-icd" on 2026-07-03 at 09:00
      Then the matcher's judgments holding condition ICD-10-CM T84.040A, condition ICD-10-CM M97.01XA, condition ICD-10-CM D69.1 and condition ICD-10-CM D69.11 are:
        | justification       | members                                                                                                                                                                                 | used                                                                                                                                                                                                                                                        |
        | same converted code | condition ICD-10-CM M97.01XA "Periprosthetic fracture around internal prosthetic right hip joint, initial encounter", condition ICD-10-CM T84.040A "Periprosthetic fracture, right hip" | CDC ICD-10-CM code conversions version 1, version 1 of condition ICD-10-CM M97.01XA "Periprosthetic fracture around internal prosthetic right hip joint, initial encounter", version 1 of condition ICD-10-CM T84.040A "Periprosthetic fracture, right hip" |
      And that step wrote these reference descriptions:
        | reference                                |
        | Matcher rules version 19                 |
        | CDC ICD-10-CM code conversions           |
        | CDC ICD-10-CM code conversions version 1 |

    Example: adopting a rule list version that adds R8 judges the pairs R8 joins among records already matched, and the earlier same code of two episodes apart still counts
      R1 joined the two pharyngitis episodes under version "0". Version 19 takes conditions out of R1, so nothing is
      filed again for them, but its row for R1 carries the query hash the Same was asserted with: a matcher judgment counts while
      its rule runs the query it was asserted with (M5), so the Same counts on and the episodes stay one entry until a
      person judges them different. A version that must undo its rule's matcher judgments changes the rule's query.

      Given Hana enters "episodes" on 2026-07-02 at 10:00
      And the matcher runs on the records of that entry on 2026-07-02 at 10:05 (match-episodes)
      When the pod is opened with the tables "app-periods" on 2026-07-03 at 09:00
      Then the matcher's judgments holding condition SNOMED 195662009 "Acute viral pharyngitis, 2017", condition SNOMED 195662009 "Acute viral pharyngitis, 2020", condition ICD-10-CM J18.9 "Pneumonia, first report", condition ICD-10-CM J18.9 "Pneumonia, second report", condition ICD-10-CM E11.9 "Type 2 diabetes, clinic" and condition ICD-10-CM E11.9 "Type 2 diabetes, hospital" are:
        | justification        | members                                                                                                                | used                                                                                                                                             |
        | same code            | condition SNOMED 195662009 "Acute viral pharyngitis, 2017", condition SNOMED 195662009 "Acute viral pharyngitis, 2020" | version 1 of condition SNOMED 195662009 "Acute viral pharyngitis, 2017", version 1 of condition SNOMED 195662009 "Acute viral pharyngitis, 2020" |
        | same code and period | condition ICD-10-CM J18.9 "Pneumonia, first report", condition ICD-10-CM J18.9 "Pneumonia, second report"              | version 1 of condition ICD-10-CM J18.9 "Pneumonia, first report", version 1 of condition ICD-10-CM J18.9 "Pneumonia, second report"              |
        | same code and period | condition ICD-10-CM E11.9 "Type 2 diabetes, clinic", condition ICD-10-CM E11.9 "Type 2 diabetes, hospital"             | version 1 of condition ICD-10-CM E11.9 "Type 2 diabetes, clinic", version 1 of condition ICD-10-CM E11.9 "Type 2 diabetes, hospital"             |
      And the matcher's same code of condition SNOMED 195662009 "Acute viral pharyngitis, 2017" and condition SNOMED 195662009 "Acute viral pharyngitis, 2020" counts
      And that step wrote these reference descriptions:
        | reference                |
        | Matcher rules version 19 |

    Example: adopting a rule list that drops a rule files nothing again for that rule's Sames, and they lapse
      Version "0a" revises version "0" and lacks R4, which filed the two Sames, so the recheck has no rule to run for
      them: it goes on, and nothing is filed again. No current rule list version runs the query each was asserted with.

      When the pod is opened with the tables "app-fewer-rules" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification | members | used |
      And the matcher's same mapped code and date of immunization CVX 141 "Fluarix" and immunization CVX 150 "FluLaval" has lapsed
      And the matcher's same mapped code and date of immunization CVX 141 "Fluad" and immunization CVX 161 "Fluzone Quadrivalent" has lapsed
      And that step wrote these reference descriptions:
        | reference                |
        | Matcher rules version 0a |

  Rule: O2. A series the tables do not hold the pod's version of is left out, and nothing is written of it
    No note rules this.
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
      When the pod is opened with the tables "app-periods" on 2026-07-03 at 09:00
      Then that step wrote these matcher judgments:
        | justification             | members                                                                   | used                                                                                                                                  |
        | same mapped code and date | immunization CVX 141 "Fluarix", immunization CVX 150 "FluLaval"           | CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluarix", version 1 of immunization CVX 150 "FluLaval"           |
        | same mapped code and date | immunization CVX 141 "Fluad", immunization CVX 161 "Fluzone Quadrivalent" | CDC CVX vaccine groups version 1, version 1 of immunization CVX 141 "Fluad", version 1 of immunization CVX 161 "Fluzone Quadrivalent" |
      And that step wrote these reference descriptions:
        | reference                        |
        | CDC CVX vaccine groups           |
        | CDC CVX vaccine groups version 1 |

    Example: the vector tables' Same still counts beside the app's
      When the pod is opened with the tables "app-periods" on 2026-07-03 at 09:00
      And the query is:
        """
        SELECT ?table WHERE {
          ?judgment cascade:countsUnderLens true ; cascade:justification cascade:SameMappedCodeAndDate ;
            prov:wasDerivedFrom ?table .
          ?table pav:version [] .
        }
        """
      Then it answers:
        | table                             |
        | CVX vaccine group table version 1 |
        | CDC CVX vaccine groups version 1  |
        | CDC CVX vaccine groups version 1  |

    Example: a pod at a version the app does not hold is matched without that series
      When the pod is opened with the tables "app-periods" on 2026-07-03 at 09:00
      And the pod is opened with the tables "app-later-on-19" on 2026-07-04 at 09:00
      And the pod is opened with the tables "app-periods" on 2026-07-05 at 09:00 (older)
      And Hana enters "fluarix-again" on 2026-07-06 at 09:00
      And the matcher runs on the records of that entry on 2026-07-06 at 09:05
      Then "older" wrote no file
      And that step wrote these matcher judgments:
        | justification      | members                                                              | used                                                                                           |
        | same code and date | immunization CVX 141 "Fluarix Tetra", immunization CVX 141 "Fluarix" | version 1 of immunization CVX 141 "Fluarix Tetra", version 1 of immunization CVX 141 "Fluarix" |

  Rule: O3. What an example reads holds the rows of the tables the pod is opened with, each current version a graph of its own
    No note rules this.
    A step reads the tables as the matcher's queries read them (runtime/steps.md, "The dataset a Then reads"): the
    rows of each series' current version in the graph named by the version, outside the default graph, and their
    descriptions in it. Until an open, they are Hana's references/, whose "CVX vaccine group table" maps CVX 141 to its
    group 88; "app" holds that row in "CDC CVX vaccine groups" instead, and no version of the other series.

    Background:
      Given a new pod for Hana on 2026-07-01 at 09:00
      And the pod is opened with the tables "app" on 2026-07-01 at 09:01

    Example: a held version's rows answer a query
      When the query is:
        """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?version ?group WHERE {
          ?version prov:specializationOf/cascade:tableKind cascade:VaccineGroups .
          GRAPH ?version { ?row owl:annotatedSource <https://ns.cascadeprotocol.org/codes/cvx/141> ; owl:annotatedTarget ?group }
        }
        """
      Then it answers:
        | version                          | group                                         |
        | CDC CVX vaccine groups version 1 | <https://ns.cascadeprotocol.org/codes/cvx/88> |

    Example: before the open, the story's references/ answer instead
      When the pod is read as it stood after "pod"
      And the query is:
        """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?version ?group WHERE {
          ?version prov:specializationOf/cascade:tableKind cascade:VaccineGroups .
          GRAPH ?version { ?row owl:annotatedSource <https://ns.cascadeprotocol.org/codes/cvx/141> ; owl:annotatedTarget ?group }
        }
        """
      Then it answers:
        | version                           | group                                         |
        | CVX vaccine group table version 1 | <https://ns.cascadeprotocol.org/codes/cvx/88> |

    Example: after an open with tables that lack a series, its rows answer nothing
      When the query is:
        """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?row WHERE {
          ?version prov:specializationOf/rdfs:label "CVX vaccine group table" .
          GRAPH ?version { ?row owl:annotatedSource <https://ns.cascadeprotocol.org/codes/cvx/141> }
        }
        """
      Then it answers nothing

    Example: rows are not in the default graph
      When the query is:
        """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?row WHERE { ?row owl:annotatedSource <https://ns.cascadeprotocol.org/codes/cvx/141> }
        """
      Then it answers nothing

  Rule: O4. A pod that requires what the runtime cannot do is refused at the open, naming the requirement
    decisions/files-held-in-archives.md, row "what reading a pod requires".
    A pod says what a runtime must be able to do to read it whole, a file for each cascade:RequirementForReadingAPod it
    requires, in the folder pod-layout.ttl gives cascade:holdsRequirementsForReadingAPod. The file is named by N9 from
    the requirement's IRI and holds one statement, that the pod dct:requires the requirement, the pod written <../> so
    that the file's bytes are the same in every pod. The file of cascade:ReadingFilesHeldInArchives is
    format/4c0299bfcb615af1d3456fb1755dea6e0229b4852c7890bae85f0328c453a95d.ttl, and its bytes are the line
    <../> <http://purl.org/dc/terms/requires> <https://ns.cascadeprotocol.org/cascade#ReadingFilesHeldInArchives> .
    ending in a line feed. A pod whose host keeps any file in an archive (X1) holds that file.

    At every open, before it answers or writes anything, a runtime lists that folder; a pod without the folder
    requires nothing. A file named for a requirement the runtime meets is not read. Any other file named as N9 names a
    requirement's file is read, and the open fails: the refusal names each requirement the file states that the runtime
    does not meet, by its IRI, and otherwise the file, as when it states none or cannot be read. Nothing else of the pod is
    read and nothing is written. So a runtime refuses a pod that needs what came after it, rather than read part of
    the pod and write beside what it could not see. A file in the folder not named as N9 names a requirement's file is a
    write that stopped (W1), and is ignored.

    A requirement's file is no file of the pod: it is in no snapshot's set (cascade:Snapshot), no archive holds it (X1),
    no build reads it, and a sync does not carry it (S1). It is written once, before the first file that needs its
    requirement (W1), and is never changed nor removed, even after a clean-up leaves no archive. A runtime from before this rule reads no requirement's file, so a pod that
    must be refused by one is the runtime's to guard by other means.

    No example can show this rule, because an example only sees a pod its runtime can open. Each runtime tests it itself.
