# Clinical terms with one meaning each

Status: ruled 2026-10-22, from #132 and the FHIR mapping on #128. The owner ruled the rows on `vaccineCode` (a code IRI
per coding), on renamed terms being removed in the re-mint, and the descriptive-name rule; the remaining rows were
accepted as proposed after the independent critical read, under the owner's delegation, and are listed on #204 for him
to reverse. Applied by #132, which writes the terms, shapes, adapter queries and the feature rules each row names. The
final name of every term is in `epic-alpha/term-map.csv`'s `new` column, which this note follows. Amends M4's
literal example (`health:vaccineCode "141"`), M14's status clause, the time term M12 reads, and #132's "deprecated, not
deleted". The duplicate declarations (`snomedCode`, `sourceRecordId`) and the `status` collision across namespaces are
#193's, ruled by `naming.md` and merged there; this note rules only what the merge leaves: what a status value means.
Partial dates on the date terms renamed here are `partial-dates-and-absent-reasons.md`'s; a lab result's time as the
matcher reads it is `quantities.md` row "matcher". Terms are named by local name, since #193 moves every one of them
into the one unversioned Cascade namespace.

## Question

The clinical terms were copied from a prototype, and mapping them to FHIR R4 (#128, the comment of 2026-10-13) found
that several mean more than one thing, or something other than the FHIR element of the same name:

- **One status term, two kinds of status.** `status` holds the clinical state of a condition and of an allergy
  (FHIR `clinicalStatus`) and the workflow state of a procedure, an immunization, a result and a medication (FHIR
  `status`). After #193 merges `health:status` and `clinical:status`, one term is filled from seven FHIR elements,
  each bound to its own value set. Within the medication kind (#69), `MedicationRequest.status` and
  `MedicationStatement.status` fill the same term.
- **Names that clash with FHIR's:** `vaccineCode` is a CVX string where FHIR's is a CodeableConcept; `reaction` is a
  manifestation's text where FHIR's is the reaction backbone; a lab result's `performedDate` comes from
  `Observation.effective[x]`; the classes `Medication` and `Procedure` share FHIR's names, and `Procedure` claims to be
  `fhir:Procedure`'s subclass.
- **`startDate` falls back to `authoredOn`,** the day a prescription was written.
- **FHIR R5 renames** two elements the R4 adapter reads, and R6 keeps the renames.

A pod has no server of record to ask what a value meant: a view shared with a clinician, or read by another runtime,
has only the terms. A term with two meanings is read with one of them, and nothing says which was wrong.

The terms stand as follows, verified by grep over the vocabulary's `queries/` and both adapters' `in/` and `views/`, on
the vocabulary's `main` at 8e16762 and the adapters' `main`. Each adapter also has its own `views/` reading the same
terms (`cascade-bridge-adapter-fhir-r4/views/*.rq`, `cascade-bridge-adapter-ccda/views/*.rq`), which every rename
touches.

| term | declared | filled from | read by (vocabulary) |
|---|---|---|---|
| `status` (health) | `ontologies/health/v1/health.ttl:79-83` | FHIR `Condition.clinicalStatus`, `Immunization.status` (`cascade-bridge-adapter-fhir-r4/in/sparql/condition.rq:81-85`, `immunization.rq:71-72`) | `views/conditions.rq:14,28`, `views/immunizations.rq:12,24`, `My active conditions.rq:12`, `My immunizations.rq:17`, `records.rq:17-18` |
| `status` (clinical) | `ontologies/clinical/v1/clinical.ttl:29-32` | FHIR `AllergyIntolerance.clinicalStatus`, `Procedure.status`, `Observation.status` (lab results, variants, interpretations: `variant.rq:29`, `variant-interpretation.rq:31`), `MedicationRequest.status`, `MedicationStatement.status` | the allergy, procedure, lab, medication, variant and interpretation views; `My active allergies.rq:10`, `My lab results.rq:16`, `My procedures.rq:17`, `My medication history.rq:25`; `medication-lifecycles.rq:19` (L1); `records.rq:16,19-23` |
| `rec:status`, the copy across kinds | `records.ttl:77-79`, written by `records.rq:12,15-28` | | `same-code-and-period.rq:20-30` (M14) and `What needs review.rq:86-104`, which test `active`, `recurrence`, `relapse` for any kind with a SNOMED or ICD-10 code; `status-sources.rq:13-19` with `rec:statusOnlyFromDocuments`, which choose `rec:statusFrom` for every view; `labels.rq:35`; `What each version says.rq:11` |
| a status's values | `health.shapes.ttl:61-68` (allergy, Warning), `:127-134` (condition), `:199-206` (immunization), `:304-311` (lab, Warning); `clinical.shapes.ttl:28-33` (procedure) | | a medication's shape lists none (`clinical.shapes.ttl:110-114`); the genomics shapes have no status property at all (`genomics.shapes.ttl`) |
| `vaccineCode` | `health.ttl:100-104`, `xsd:string`, `maxCount 1` (`health.shapes.ttl:208-213`) | the CVX coding only (`immunization.rq:56-60`; ccda `immunization.rq:88`) | `same-code-and-date.rq:11-12`, `same-mapped-code-and-date.rq:18-19` (bytes pinned by rule list versions 1 to 8), `same-vaccine-group-and-date.rq:18-19` (version 9), `views/immunizations.rq:11,22`, `My immunizations.rq:13-20`; joined as a CVX IRI by M4 |
| `reaction` | `health.ttl:32-36` | each `reaction.manifestation.text` (fhir-r4 `allergy-intolerance.rq:119-123`; ccda `allergy.rq:198`) | no query |
| `performedDate` | `health.ttl:175-179` | `Observation.effective[x]` (`lab-result.rq:133-138`); C-CDA `effectiveTime` (`result.rq:276,284`) | `same-result.rq:12-13` (M12), `views/lab-results.rq:16,30`, `My lab results.rq:11`, `records.rq:21` |
| `startDate` | `clinical.ttl:103-106` | `effectiveDateTime`, else `effectivePeriod.start`, else `authoredOn` (`medication.rq:154-157`); C-CDA `effectiveTime` (`medication.rq:119,125`) | `views/medications.rq:18,37`, `My active medications.rq:29`, `My medication history.rq:27`, `records.rq:20` |
| `Procedure` | `clinical.ttl:11-15`, `rdfs:subClassOf fhir:Procedure` at `:13` | | `records.rq:19`, `views/procedures.rq`, `My procedures.rq` |
| `Medication` | `clinical.ttl:75-78` | MedicationRequest and MedicationStatement | `records.rq:20`, `medication-lifecycles.rq:18`, the medication view and questions, `tables/medication-classes*.rq`, `records.ttl:31,36,871-883` |

## What others do

Each quotation was read at its source on 2026-10-22 (verified) unless marked.

- **FHIR R4 splits clinical state from workflow state.** Condition has no `status` element: `clinicalStatus`, "The
  clinical status of the condition", is a CodeableConcept "because clinicalStatus has some clinical judgment
  involved", and con-5 says it "SHALL NOT be present if verification Status is entered-in-error". AllergyIntolerance
  likewise has `clinicalStatus` and `verificationStatus` and no `status`. The workflow elements are each bound to
  their own value set, Required: `Immunization.status`, "the current status of the immunization event … completed or
  not done"; `Procedure.status`; `Observation.status`, "The status of the result value"; `MedicationRequest.status`,
  "the current state of the order"; `MedicationStatement.status`, "the patient or other source's judgment about the
  state of the medication used", whose value set mixes "the status of the use of the medication by the patient (for
  example, stopped or on hold)" with "the status of the medication statement itself (for example, entered in error)".
  In FHIR the element names the list; the value is a bare code.
- **FHIR R5 renames and moves.** R5's Procedure has `occurrence[x]`, "Estimated or actual date, date-time, period, or
  age when the procedure did occur", and no `performed[x]`; R5's `MedicationRequest.medication` is a CodeableReference
  (verified); the R6 build keeps both (verified for Procedure; #128's research for medication). R5's
  `MedicationStatement.status` is "recorded | entered-in-error | draft", "This status concerns just the recording of
  the medication statement", and "MedicationStatement.adherence should be used for indicating a patient's adherence".
  R5's `MedicationRequest.effectiveDosePeriod` is "The period over which the medication is to be taken … the earliest
  date and the latest end date of the dosageInstructions".
- **FHIR RDF.** R4 names a property per resource (`fhir:Patient.birthDate`); R5 and the R6 build share names across
  resources, so `fhir:status` is one property whose values come from whichever list the resource binds (#128's
  research; confirmed on rdf.html by the review of this note). A concept IRI needs an IRI stem: where none is defined,
  R5 RDF says the concept IRI is undefined (quoted by the review; not re-read here), and `records.ttl:471` takes THO's
  stem and "never the FHIR Coding.system URI" (verified).
- **FHIR's other elements.** `Immunization.vaccineCode` is a CodeableConcept, "Vaccine that was administered or was to
  be administered". `AllergyIntolerance.reaction` is a repeating backbone, "Details about each adverse reaction event";
  its `manifestation` is a CodeableConcept, "Clinical symptoms and/or signs". `Observation.effective[x]` is "The time or
  time-period the observed value is asserted as being true". `MedicationRequest.authoredOn` is "The date (and perhaps
  time) when the prescription was initially written"; R4's MedicationRequest has no `effective[x]`.
  `MedicationStatement.effective[x]` is "The interval of time during which it is being asserted that the patient
  is/was/will be taking the medication".
- **C-CDA.** A Result Observation's `effectiveTime` "Represents the clinically relevant time of the measurement (e.g.,
  … the time the blood sample was obtained for a chemistry test)" (verified). C-CDA's statuses come from more than one
  system: a problem's and an allergy's are SNOMED CT codes (`cascade-bridge-adapter-ccda/vocab/ccda-problem-statuses.ttl:9-35`,
  `ccda-allergy-statuses.ttl:7-20`), and an act's `statusCode` is an HL7 v3 ActStatus code. The C-CDA adapter
  crosswalks each to a FHIR code at write time, through a SKOS scheme whose `skos:exactMatch` targets are FHIR
  CodeSystem URL plus code (`<http://hl7.org/fhir/event-status/completed>`), which are not concept IRIs FHIR defines,
  and keeps only the code (ccda `allergy.rq:110,128,145`, `condition.rq:130,140,214`, `immunization.rq:114`,
  `medication.rq:174`, `procedure.rq:113`, `result.rq:295`). It crosswalks a medication's v3 code to
  MedicationRequest's list whatever the mood (`ccda-medication-statuses.ttl:4-30`), though an EVN-mood activity is
  `reportedUse` (`medication.rq:51`). A code its scheme lacks, `held`, `new`, `normal` or `obsolete` for a medication,
  is not written, and the adapter raises a finding (`entry-statement-findings.rq:11-14`; all verified).
- **openEHR** has no status on OBSERVATION or EVALUATION; workflow state is the Instruction State Machine's, on an
  ACTION's `ISM_TRANSITION.current_state`, ten states from INITIAL to EXPIRED (RM ehr §8.2.5.5, verified). A problem's
  clinical state lives in archetypes, not the reference model (inferred: no RM attribute holds it).
- **OMOP CDM 5.4** has no status on DRUG_EXPOSURE or PROCEDURE_OCCURRENCE; `condition_status_concept_id` is "the point
  during the visit the diagnosis was given", not a clinical status; `stop_reason` is "as it is represented in the
  source" and is to be retired in v6.0 (verified).
- **SPHN**'s Allergy has only `hasVerificationStatusCode`, a SNOMED code; `hasStatusCode` is on Consent alone; Drug
  Prescription and Drug Administration Event have no status and use `hasReasonToStopCode` (read by the review of this
  note on the 2026 schema; not re-read here).
- **PAV** `authoredOn`: "The date this resource was authored", distinct from `pav:createdOn` (verified).
- **SSSOM** gives a mapping `object_source_version`, "Version IRI or version string of the source of the object term",
  on a Mapping and on a MappingSet (verified, in its schema).
- **Nothing** defines one status value set across kinds of record: none of FHIR, openEHR, OMOP or SPHN has an "is it
  current?" list shared by conditions, immunizations and medications.

Sources: FHIR R4 Condition (https://hl7.org/fhir/R4/condition-definitions.html), AllergyIntolerance
(https://hl7.org/fhir/R4/allergyintolerance-definitions.html), Immunization
(https://hl7.org/fhir/R4/immunization-definitions.html), Observation (https://hl7.org/fhir/R4/observation-definitions.html),
MedicationRequest (https://hl7.org/fhir/R4/medicationrequest-definitions.html), MedicationStatement
(https://hl7.org/fhir/R4/medicationstatement-definitions.html); FHIR R5 MedicationStatement
(https://hl7.org/fhir/R5/medicationstatement-definitions.html), MedicationRequest
(https://hl7.org/fhir/R5/medicationrequest-definitions.html), Procedure (https://hl7.org/fhir/R5/procedure-definitions.html);
the R6 build's Procedure (https://build.fhir.org/procedure-definitions.html); FHIR RDF (https://hl7.org/fhir/R4/fhir.ttl,
https://hl7.org/fhir/R5/rdf.html, https://build.fhir.org/rdf.html); C-CDA Result Observation
(https://hl7.org/cda/us/ccda/StructureDefinition-ResultObservation-definitions.html); openEHR RM EHR
(https://specifications.openehr.org/releases/RM/latest/ehr.html); OMOP CDM 5.4
(https://ohdsi.github.io/CommonDataModel/cdm54.html); SPHN (https://www.biomedit.ch/rdf/sphn-schema/sphn); PAV
(https://pav-ontology.github.io/pav/); SSSOM's schema
(https://github.com/mapping-commons/sssom/blob/master/src/sssom_schema/schema/sssom_schema.yaml). The FHIR mapping of
the 59 clinical terms (https://github.com/jayostis/cascade-vocabulary/issues/128#issuecomment-6135264321).

## Choice

Every row is ruled, as the status line says. "#132" in the last column means the build that applies this note.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| 1. clinical state and workflow state | FHIR R4 and R5 `clinicalStatus` beside `status`; openEHR's ISM for workflow only | two terms: `clinicalStatus` on a condition and an allergy, the person's state; `status`, renamed `workflowStatus` (row 12), on a procedure, an immunization, a lab result, a variant, a variant interpretation and a medication, the state of the act or the record; `verificationStatus` unchanged. Every reader of `rec:status` moves to the term its kind states, as #193 removes the copy: M14 (`same-code-and-period.rq`) and `What needs review.rq` read `clinicalStatus`; `records.rq`'s table, `status-sources.rq`, `rec:statusFrom` and `rec:statusOnlyFromDocuments`, and `labels.rq` read either. Applied by #132 with #193's sweep; M14 rewritten | borrowed from FHIR |
| 2. which list a status value is from | FHIR binds one value set per element and resource and writes a bare code; R5 RDF shares `fhir:status` across resources | the value stays FHIR's code as a string; the term and the record's kind fix its list; each kind's shape names exactly one FHIR value set with `sh:in`, adding Observation.status's list to the two genomics shapes, which have none; #128's mapping table names the CodeSystem per (term, kind). No concept IRI is minted: none is defined until HL7 Terminology registers a stem. Shapes only; #132; `ontologies/cascade.shapes.ttl` | borrowed from FHIR's binding per element |
| 3. a medication's status | R4 MedicationRequest and MedicationStatement status; R5's recorded-status plus `adherence`; C-CDA on FHIR's ConceptMap | the status stays the source's text, listed by no shape, because a person types it in an entry; its one meaning for any reader is L1's lifecycle class. L1 unchanged | borrowed from FHIR's codes and C-CDA on FHIR's map, through L1 |
| 4. the C-CDA crosswalk at write time | C-CDA on FHIR's maps; `partial-dates-and-absent-reasons.md` row 6, no crosswalk for a reason | kept: the C-CDA adapter writes the FHIR code its scheme maps a SNOMED or v3 status to, and a code its scheme lacks is not written and is a finding, as today | borrowed from C-CDA on FHIR; differs from row 6 there, see Why |
| 5. one status for every kind | nothing: no standard defines one | refused: a page that needs "is it current?" for a kind derives a class from that kind's list, as the medication lifecycle does (L1) | ours, by having none |
| 6. `vaccineCode` | FHIR CodeableConcept; `testCode`, `allergenCode`, `icd10Code` here, one IRI per coding | keeps its name, becomes an IRI per coding in a registered code system (CVX now), and becomes repeatable, as `testCode` is; the immunization view and `My immunizations.rq` show the CVX code among them, and the vaccine comparisons change in a new rule list version. M4 rewritten by #132 | borrowed from FHIR, flattened as `testCode` is |
| 7. `reaction` | FHIR `reaction` backbone, its `manifestation` a CodeableConcept | renamed `reactionManifestationText`, beside `manifestationCode` renamed `reactionManifestationCode` (row 12). Shapes and adapters; #132; `ontologies/cascade.ttl` | borrowed from FHIR's element name |
| 8. a lab result's time | FHIR `effective[x]`; C-CDA "clinically relevant time"; FHIR `performed[x]` is an R4 procedure's | renamed `resultClinicallyRelevantTime`, with FHIR's definition; never the time the lab ran the test. M12 and `quantities.md`'s matcher row read it under the new name; #132 | borrowed from FHIR and C-CDA |
| 9. a medication's start | FHIR `MedicationStatement.effective[x]`; `MedicationRequest.authoredOn`, written; R5 `effectiveDosePeriod`; C-CDA `effectiveTime` low; PAV `authoredOn` | `startDate`, renamed `medicationUseStartDate` (row 12), never takes `authoredOn`; a new `prescriptionWrittenDate` holds the day the prescription was written; an R5 source's `effectiveDosePeriod.start` is a start; `records.rq`'s date for a medication becomes `COALESCE(medicationUseStartDate, prescriptionWrittenDate)`, so a prescription keeps a place on a timeline; the view shows both. #132; `ontologies/cascade.ttl`, `queries/derivations/records.rq` | borrowed from FHIR's split; diverges from PAV's term, see Why |
| 10. duplicates | `naming.md`; #193 | one declaration each by #193's merge: `snomedCode`, `sourceRecordId`, `status`. Not ruled here; see Why for what the merge must pick (`ontologies/cascade.ttl`) | #193's |
| 11. `Procedure rdfs:subClassOf fhir:Procedure` | #128: a close match; FHIR RDF's `fhir:Procedure` is a resource | removed; the pointer is a closeMatch row in #128's mapping table naming FHIR R4, the release the adapter reads; no `rdfs:seeAlso` on the class, which the copied-term rule forbids. #132 for the axiom, #128 for the row (`ontologies/cascade.ttl`) | diverged from the prototype's claim, toward #128's table |
| 12. names of the classes and properties this note touches | FHIR resource and element names; OMOP CDM table and column names; openEHR archetypes; SPHN classes; PROV and PAV | the owner's rule: a name says what every instance or value is, read alone in a query, and is as long as that takes and no longer; never a word an instance can falsify, as "administered" or "performed" is by a not-done one; no `Record` suffix, which says nothing of the kind. Classes: `AllergyOrIntolerance`, `ProblemOrDiagnosis`, `Vaccination`, `LaboratoryTestResult`, `MedicalProcedure`, `PrescribedOrReportedMedication`, `GeneticVariantFinding`; `VariantInterpretation` and `PatientProfile` pass. Properties: `workflowStatus`, `clinicalStatus`, `verificationStatus`, `vaccineCode`, `reactionManifestationText`, `reactionManifestationCode`, `resultClinicallyRelevantTime`, `vaccinationOccurrenceTime`, `prescribedOrReported`, `medicationUseStartDate`, `medicationUseEndDate`, `prescriptionWrittenDate`. The table under Why gives each one's today, alternative and reason. Widens #132's scope. #132; `ontologies/cascade.ttl` | borrowed per name, see Why; removes the clashes with FHIR's `Procedure` and `Medication` |
| 13. R5's renames | R5 `occurrence[x]`, `medication[x]` a CodeableReference, kept in R6; SSSOM `object_source_version` | no term changes: none is named after an element R5 renames; each row of #128's mapping table names the FHIR release in `object_source_version`. #128 | borrowed from SSSOM |
| 14. how a renamed term goes | #132: "deprecated, not deleted, until alpha"; #193: never renamed after its namespace lands | removed outright, not deprecated, in #191's re-mint, before #193's promise starts at v1; one `Depends-On` set across the vocabulary, both adapters and cascade-runtime-js | ours; departs from #132's wording, see Why |

## Why

**Two statuses, because the standards have two.** (row "1. clinical state and workflow state") FHIR R4 and R5 give a condition and an allergy a `clinicalStatus`
and no `status`, and give the acts a `status` and no `clinicalStatus` (verified); openEHR keeps workflow state on the
ISM and no state on an observation or an evaluation. A condition "resolved" is a fact about the person; an immunization
"completed" is a fact about an act. One term for both is what makes "active" ambiguous: M14 and `What needs
review.rq` test `rec:status` for `active`, `recurrence` and `relapse` on any kind with the code (verified,
`same-code-and-period.rq:14-30`); only the rule list row's kinds keep M14 to conditions (M4), and once #193 merges
`snomedCode` a procedure's code is the same term, so the query alone would read a procedure's workflow status as a
clinical state (inferred). Reading `clinicalStatus` there makes the query say what it means. The cost is one term and
the readers listed in row 1, which #193's removal of `rec:status` touches anyway.

**One list per term and kind, which the kind already says.** (row "2. which list a status value is from") After row 1, a status's list is fixed by the term and the
record's kind, exactly as FHIR's is fixed by the element and the resource, and as R5 RDF's shared `fhir:status` relies
on. The shapes already say so for every kind but the medication's and the two genomics kinds (verified, the table under
Question). A concept IRI per value would say the list a second time, and none exists to use: FHIR RDF defines a concept
IRI only through a registered stem, `records.ttl:471` takes only THO's stems, and the CodeSystem-URL-plus-code IRIs the
C-CDA adapter's schemes target are not defined concept IRIs. Every query that tests `"active"` would also change. This
differs from `partial-dates-and-absent-reasons.md` row 6, which stores a reason's IRI, because a reason may come from two
systems for one property, and a status from exactly one per term and kind.

**A medication's status means its lifecycle class.** (row "3. a medication's status") People type medication statuses in entries
(`runtime/scripted-input/ben/entries/medication-statuses.ttl`), and L1 reads that text, both FHIR lists and synonyms
into five classes (verified, `runtime/lifecycle.feature:8-29`), so a single list on the shape would reject what L1 is
there to read. R5's move of "taking" to `adherence` is why the class, not the code, is the meaning: an R5 statement's
status says nothing about use.

**The crosswalk at write time stays, unlike a reason's.** (row "4. the C-CDA crosswalk at write time") Row 6 of `partial-dates-and-absent-reasons.md` stores a
reason's own code because HL7's map is a draft covering 9 of 15 codes and the reason may come from either system. A
status's map is the adapter's, published by C-CDA on FHIR, and its target is one list the kind's shape requires, so the
pod holds one list per kind. The cost is what it drops: a code the scheme lacks is not written, with a finding, and a
v3 `held` that L1 would read as paused is lost (verified, the adapter's scheme has no `held`). An EVN-mood medication
gets a MedicationRequest code though it is a list entry; under row 3 that is harmless, since L1 reads both lists alike.

**No status across kinds.** (row "5. one status for every kind") The steelman for one merged term is a single "is it current?" view. No standard defines one
(none of FHIR, openEHR, OMOP or SPHN has it), and L1 shows the honest form: a class per kind, derived from that kind's
list, with the step that chose it recorded.

**Names that say what they hold.** (rows "6. vaccineCode", "7. reaction", "8. a lab result's time") The clinical code terms hold an IRI per coding (`testCode`, `allergenCode`,
`manifestationCode`, `icd10Code`, the condition's `snomedCode`; verified in the adapters' queries and fixtures), except
`cptCode`, the procedure's `snomedCode` and `vaccineCode`, which hold the code as a literal; and M4 already turns
`vaccineCode "141"` into `<http://hl7.org/fhir/sid/cvx/141>` to join a table (`runtime/matcher.feature:89-91`). An IRI
per coding makes `vaccineCode` mean what FHIR's does, flattened as every code term is, and lets an NDC or SNOMED coding
join later without a new term; that is also why it becomes repeatable, and why the readers that assume one code, the
immunization view and `My immunizations.rq`'s GROUP BY, pick the CVX one. The comparisons whose bytes old rule list
versions pin (`same-mapped-code-and-date.rq`, versions 1 to 8; `same-vaccine-group-and-date.rq`, version 9) get a
successor in a new version; whether the old versions survive #191's re-mint is #191's (lean: they go, since no pod
holds a claim under them). `reactionManifestationText` takes FHIR's path, `reaction.manifestation.text`.
`resultClinicallyRelevantTime` takes FHIR's name for FHIR's element, prefixed with what it is the time of, as
`resultValue` is; C-CDA calls the same time "clinically relevant" and gives the sample's draw as its example,
so "performed" says something neither source says.

**A start is not a prescription's date.** (row "9. a medication's start") R4's MedicationRequest has no `effective[x]`, so the FHIR adapter's
`startDate` for every prescription is `authoredOn`, the day it was written (verified, `medication.rq:154-157`). A person
reading "started 2026-03-01" is told when they began taking it, which no source said. The cost: a FHIR prescription
loses its `startDate` in `My active medications.rq` and `My medication history.rq`, and the kits' expected views change;
the timeline keeps it through the COALESCE. The vocabulary's rule is to use PAV's or PROV-O's term where one exists, and
`pav:authoredOn` is the strongest candidate: "The date this resource was authored". On a version it reads as when that
resource, the Cascade version, was authored, which the provenance terms on a version already say otherwise, and a
reader of the version's provenance would take a clinical date for a record-keeping one (inferred). A prescription's
written date is a clinical fact about an act, not about the resource, so it gets a term of its own; the owner may rule
otherwise. R5's `effectiveDosePeriod.start` is the prescription's real start where a source sends it; R4 sources have
only the dosage timing's bounds, filled how often is unmeasured (unverified).

**What #193's merge must pick, as fallout.** (row "10. duplicates") The two `snomedCode` declarations differ in kind and both adapters write
both forms: a condition's an IRI, a procedure's a literal (verified,
`cascade-bridge-adapter-ccda/fixtures/expected/narrative-id-twice.ttl:58,76`). One term needs one kind; row 6's
reasoning makes it the IRI. This is said for #193 to apply, not ruled here.

**The subclass claims too much.** (row "11. Procedure rdfs:subClassOf fhir:Procedure") Under RDFS a `rdfs:subClassOf fhir:Procedure` makes every Cascade procedure a FHIR
Procedure resource, which FHIR RDF's shapes would then hold to FHIR's cardinalities (inferred); #128 found only a close
match. The copied-term rule lets the class carry its superclasses and nothing else, so the pointer to FHIR lives in the
mapping table, which also says which release it names.

**Names that say what the thing is.** (row "12. names of the classes and properties this note touches") The owner's rule of 2026-10-22: a name says what every instance or
value is, read alone in a query and out of its class, and is longer where that takes; living vocabularies, when in
doubt, take the longer name. Two tests follow. A name is true of every instance the adapters write, so a class that
holds not-done, refused or entered-in-error items is named for the kind of act or finding, which its status
qualifies, as FHIR names an Immunization whose status is not-done, and never by a participle that says it happened.
And a suffix every class shares, `Record`, says nothing of the kind. Each name below was checked against what fills
it (verified by grep over both adapters' `in/sparql/`, on their `main`), against FHIR's resource or element names,
OMOP CDM 5.4's tables and columns (verified, its user guide), SPHN 2026's classes (verified, its schema page), and
openEHR's archetype names in its Clinical Knowledge Manager (from knowledge; not re-read, unverified). This widens
#132, which named only the subclass axiom.

| today | what fills it | name | alternative | why |
|---|---|---|---|---|
| `AllergyRecord` | FHIR AllergyIntolerance; C-CDA Allergy Concern; `allergyType` allergy or intolerance, `verificationStatus` up to refuted and entered-in-error | `AllergyOrIntolerance` | `AdverseReactionRisk` (openEHR's archetype; FHIR's and SPHN's definition, "risk of harmful or undesirable, physiological response") | every instance is an allergy or an intolerance, both of which the class holds; FHIR's resource name, spelt out; the alternative is the most exact but reads as an assessment, not as the thing a person reports |
| `ConditionRecord` | FHIR Condition; C-CDA Problem Observation; `category` problem-list-item or encounter-diagnosis | `ProblemOrDiagnosis` | `Condition` (FHIR; OMOP `CONDITION_OCCURRENCE`) | the two categories it holds are exactly a problem and a diagnosis; openEHR's Problem/Diagnosis, SPHN's Problem Condition and Diagnosis; "condition" alone says less, and OMOP's "occurrence" is false of a refuted one |
| `ImmunizationRecord` | FHIR Immunization; C-CDA Immunization Activity; statuses completed, not-done (negationInd), entered-in-error | `Vaccination` | `VaccineAdministration` | the act of giving a vaccine, which a not-done status qualifies; "immunization" claims immunity, which no record shows; OMOP files vaccines under `DRUG_EXPOSURE`, and SPHN has no class for it; the alternative reads as given |
| `LabResultRecord` | FHIR Observations of category laboratory, or uncategorised with a LOINC code that is no vital sign, never a panel; C-CDA Result Observations; statuses up to registered and cancelled | `LaboratoryTestResult` | `LaboratoryObservation` | openEHR's archetype and SPHN's Lab Result; FHIR's Observation.status is "the status of the result value", so a cancelled one is a result, cancelled; OMOP's `MEASUREMENT` holds vital signs too, which this class does not |
| `Procedure` | FHIR Procedure; C-CDA Procedure Activity Procedure; statuses preparation to completed, not-done (negationInd), stopped | `MedicalProcedure` | `ClinicalProcedure` | SPHN's name; says a procedure on the person, not a software one; a not-done status qualifies it as it does a vaccination; OMOP's `PROCEDURE_OCCURRENCE` says "ordered by, or carried out by", which the class matches but "occurrence" does not |
| `Medication` | FHIR MedicationRequest and MedicationStatement; C-CDA Medication Activity in INT and EVN mood; every version's `clinicalIntent`, renamed `prescribedOrReported`, prescribed or reportedUse (`clinical.shapes.ttl:55-65`) | `PrescribedOrReportedMedication` | `MedicationPrescriptionOrUse` | every instance is one of the two, which the shape requires, so the name is true of all; FHIR's `Medication` is the product; OMOP's `DRUG_EXPOSURE` holds "prescriptions written, prescriptions dispensed, and drugs administered" in one table, the precedent for one kind, but "exposure" is false of a prescription never filled; SPHN splits Drug Prescription from Drug Administration Event |
| `Variant` | FHIR Genomics Reporting's Variant observation | `GeneticVariantFinding` | keep `Variant` | read alone, `Variant` may be a catalogue's variant, as ClinVar's is; #202 makes the record a finding about the person |
| `VariantInterpretation` | Genomics Reporting's Diagnostic Implication | keep | `VariantClassification` | says what it is: a report's or ClinVar's interpretation of a variant |
| `PatientProfile` | FHIR Patient | keep | `PatientDemographics` | says what it is, a source's description of the person |
| `status` | the act's state: FHIR Procedure, Immunization, Observation, MedicationRequest and MedicationStatement `status` | `workflowStatus` | `actStatus` (HL7 v3's ActStatus, which C-CDA's statusCode is) | read alone, `status` says nothing of whose; every value is the state of an order, an event or a result, FHIR's workflow pattern, never the person's state |
| `status` (condition, allergy) | FHIR `clinicalStatus` | `clinicalStatus` | `clinicalStatusOfConditionOrAllergy` | FHIR's name, one meaning in both resources; the alternative only repeats the class |
| `verificationStatus` | FHIR `verificationStatus` | keep | | FHIR's name; says it |
| `vaccineCode` | each CVX coding (row 6) | keep | `vaccineProductCode` | FHIR's name, and read alone it says a code naming the vaccine; CVX names a vaccine type, so "product" would be false of most codes |
| `reaction` | each `reaction.manifestation.text` | `reactionManifestationText` | `reactionSymptom` | FHIR's path, `reaction.manifestation.text`, spelt out; "symptom" is false of a sign |
| `manifestationCode` | each SNOMED coding of `reaction.manifestation` | `reactionManifestationCode` | keep | pairs with the text, and says whose manifestation |
| `performedDate` | `Observation.effective[x]`; C-CDA `effectiveTime` | `resultClinicallyRelevantTime` | `specimenCollectionTime` | C-CDA's words, "the clinically relevant time"; FHIR's `effective` is opaque read alone; the alternative is what a reader usually means, but false where the source's time is not the draw |
| `startDate` (medication) | `MedicationStatement.effective[x]` start; C-CDA `effectiveTime` low, the start of use or, in INT mood, its intended start | `medicationUseStartDate` | `dateMedicationStarted` | OMOP's `drug_exposure_start_date` with "use" for "exposure", true of an intended start; `startDate` read alone may be the prescription's validity |
| `endDate` (medication) | `effectivePeriod.end`; C-CDA `effectiveTime` high | `medicationUseEndDate` | `dateMedicationStopped` | the pair of the above, OMOP's `drug_exposure_end_date` |
| `administrationDate` | the vaccination's date, or the date it was meant to occur, which a not-done one has | `vaccinationOccurrenceTime` | `vaccineAdministrationDate` | "administered" is false of a not-done vaccination (row 12's rule); FHIR's `occurrence[x]` names when an immunization event occurred |
| `clinicalIntent` | whether a version came from a prescription or from a list of what the person takes | `prescribedOrReported` | keep | the two values are the two sources, and the class's name now says them |
| new (row 9) | `MedicationRequest.authoredOn` | `prescriptionWrittenDate` | `prescriptionAuthoredDate` | FHIR's definition, "when the prescription was initially written"; PAV's `authoredOn` is about the resource (row 9) |

The rule's pass over every other term of the vocabulary was made in the same re-mint; its result, each term's final
name, is `epic-alpha/term-map.csv`'s `new` column.

**Removed, not deprecated.** (row "14. how a renamed term goes") Deprecation would protect the readers that name the old terms: both adapters, their
views, cascade-runtime-js and the nightly compatibility check; no pod exists (`epic-alpha/delivery.md`). #191's re-mint
already changes every name across those repositories in one `Depends-On` set, so the renames ride it and leave nothing
to deprecate. #193's "never renamed afterwards" is read as starting at v1, which #193 itself times "before anything is
called v1"; if the owner reads it as starting when #193 merges, the renames must ride #193's sweep instead.

## Alternatives that lost

- **Keep one `status` for every kind.** The strongest case: FHIR R5 RDF shares `fhir:status`, and one term is one thing
  for a generic reader. FHIR shares the name `status`, not `clinicalStatus`; it keeps the two elements apart, and M14
  would read either as the other once the codes merge.
- **One term per kind** (`conditionClinicalStatus`, `procedureStatus`, …), as R4 RDF names per resource. The strongest
  case: the name alone says the list. R5 and R6 RDF moved away from it, and the kind already says it.
- **Status values as IRIs.** The strongest case: the value says its list on its own, as row 6 of
  `partial-dates-and-absent-reasons.md` does. No concept IRI is defined for these codes, people type medication
  statuses, and every reader changes.
- **No crosswalk at write time, the source's SNOMED or v3 code kept.** The strongest case: nothing dropped, and the
  absent-reason ruling's consistency. Each kind would then hold two or three lists, which row 2 exists to prevent.
- **A shape list for medication statuses by intent.** The strongest case: a prescription's status is checked against
  MedicationRequest's list. People's text would warn on every entry L1 reads correctly.
- **`cvxCode` for `vaccineCode`,** a literal as `cptCode` is. The strongest case: an honest name with no query changes
  beyond the rename. It keeps the one CVX-only code term and needs a new term for an NDC or SNOMED vaccine coding.
- **`collectedDate` for a lab result's time.** The strongest case: it is what a reader means. A result with no
  specimen, a vital sign or an observation of the person, has an effective time and no collection.
- **`pav:authoredOn` for a prescription's written date.** The strongest case: the vocabulary's own rule, and PAV's
  meaning, "the date this resource was authored", fits a prescription read as a work. On a version it reads as the
  Cascade version's authoring.
- **Keep `startDate`'s fallback.** The strongest case: a prescription keeps a date in the view. Row 9 keeps that by
  naming the fallback, without saying the person started that day.
- **`rdfs:seeAlso` on the class.** The strongest case: a FHIR-aware reader finds FHIR from the term. The copied-term
  rule forbids it, and the mapping table names the release, which a bare link does not.
- **`…Record` for every class.** The strongest case: one pattern, and four classes already have it. The owner ruled
  it out on 2026-10-22: "just putting record on something doesn't really make it any more clear what kind of record is it".
- **Short names, FHIR's where FHIR has one.** The strongest case: a FHIR reader knows them at sight. Read alone, `status`,
  `effective` and `startDate` say nothing of whose state or which start, and the mapping table already names FHIR's
  element for every term.
- **Deprecate, as #132 says.** The strongest case: the readers in other repositories keep working through the change.
  #191's re-mint breaks and repairs them all in one set anyway.

## Still open

Each with its lean, and the one fact that decides it:

- **When #193's promise starts.** Lean: at v1, so the renames ride #191. Decides it: the owner's reading of #193 item 2.
- **Old rule list versions in #191's re-mint.** Lean: dropped. Decides it: #191.
- **A reaction's severity.** `allergySeverity` takes the first reaction's (fhir-r4 `allergy-intolerance.rq:139`), and
  row 7's manifestations lose which reaction they belonged to. Lean: a reaction node when a source sends two reactions
  a page needs apart. Decides it: such a source.
- **R5 sources.** An R5 MedicationStatement's status is the record's, and its use is `adherence`. Lean: an R5 adapter
  feeds L1 from `adherence`. Decides it: a source sending R5.
- **A v3 `held`.** Lean: add it to the C-CDA adapter's scheme as on-hold, as L1's synonym row already reads it.
  Decides it: a C-CDA source sending it.
- **The medication class.** Row 12 names it `PrescribedOrReportedMedication`, a name that holds only while #69's one
  kind stays one; a split would name each half.
- **openEHR's archetype names**, cited from knowledge. Lean: none of row 12's names rests on them alone. Decides it: a
  read of the Clinical Knowledge Manager.

## What would change our mind

A query, page or partner that needs one status across kinds would reopen row 5, and its list would be derived, as L1
is. HL7 Terminology registering IRI stems for its status CodeSystems would make IRIs possible for row 2. A source
sending a status code from a list other than its kind's would show row 2's premise wrong. Sources filling a
prescription's dosage bounds, or sending R5's `effectiveDosePeriod`, would give row 9 a real start for prescriptions.
A FHIR-aware consumer that needs Cascade procedures typed as `fhir:Procedure` would reopen row 11, through a view
rather than the class.
