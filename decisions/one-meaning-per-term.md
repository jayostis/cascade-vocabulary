# Clinical terms with one meaning each

Status: draft, 2026-10-22, from #132 and the FHIR mapping on #128; a proposal per row, for the owner to rule. Applied by
#132 once ruled, which writes the terms, shapes, adapter queries and the feature rules each row names. The duplicate
declarations (`snomedCode`, `sourceRecordId`) and the `status` collision across namespaces are #193's, ruled by
`naming.md` and merged there; this note rules only what the merge leaves: what a status value means. Partial dates on
the date terms renamed here are `partial-dates-and-absent-reasons.md`'s; a lab result's time as the matcher reads it
is `quantities.md` row "matcher". Terms are named by local name, since #193 moves every one of them into the one
unversioned Cascade namespace.

## Question

The clinical terms were copied from a prototype, and mapping them to FHIR R4 (#128, the comment of 2026-10-13) found
that several mean more than one thing, or something other than the FHIR element of the same name:

- **One status term, two kinds of status.** `status` holds the clinical state of a condition and of an allergy
  (FHIR `clinicalStatus`) and the workflow state of a procedure, an immunization, a result and a medication (FHIR
  `status`). After #193 merges `health:status` and `clinical:status`, one term carries nine FHIR value sets. Within
  the medication kind (#69), `MedicationRequest.status` and `MedicationStatement.status` fill the same term.
- **Names that clash with FHIR's:** `vaccineCode` is a CVX string where FHIR's is a CodeableConcept; `reaction` is a
  manifestation's text where FHIR's is the reaction backbone; a lab result's `performedDate` comes from
  `Observation.effective[x]`; the classes `Medication` and `Procedure` share FHIR's names, and `Procedure` claims to be
  `fhir:Procedure`'s subclass.
- **`startDate` falls back to `authoredOn`,** the day a prescription was written.
- **FHIR R6 renames** two elements the FHIR adapter reads.

A pod has no server of record to ask what a value meant: a view shared with a clinician, or read by another runtime,
has only the terms. A term with two meanings is read with one of them, and nothing says which was wrong.

The terms stand as follows, verified at the lines named, on `main` at 8e16762 and the adapters' `main`:

| term | declared | filled from | read by |
|---|---|---|---|
| `status` (health) | `ontologies/health/v1/health.ttl:79-83` | FHIR `Condition.clinicalStatus`, `Immunization.status` (`cascade-bridge-adapter-fhir-r4/in/sparql/condition.rq:81-85`, `immunization.rq:71-72`) | `views/conditions.rq`, `views/immunizations.rq`, `My active conditions.rq:12`, `same-code-and-period.rq:20-30` |
| `status` (clinical) | `ontologies/clinical/v1/clinical.ttl:29-32` | FHIR `AllergyIntolerance.clinicalStatus`, `Procedure.status`, `Observation.status`, `MedicationRequest.status`, `MedicationStatement.status` | the allergy, procedure, lab, medication and variant views; `My active allergies.rq:10`; L1 |
| a status's values | `health.shapes.ttl:61-68` (allergy, Warning), `:127-134` (condition), `:199-206` (immunization), `:304-311` (lab, Warning); `clinical.shapes.ttl:28-33` (procedure) | | each kind's shape already lists one FHIR value set; a medication's lists none (`clinical.shapes.ttl:110-114`) |
| `vaccineCode` | `health.ttl:100-104`, `xsd:string` | the CVX coding only (`immunization.rq:56-60`) | `same-code-and-date.rq:11-12`, `same-vaccine-group-and-date.rq:18-19`, joined as a CVX IRI by M4 |
| `reaction` | `health.ttl:32-36` | each `reaction.manifestation.text` (`allergy-intolerance.rq:119-123`) | the allergy view |
| `performedDate` | `health.ttl:175-179` | `Observation.effective[x]` (`lab-result.rq:133-138`); C-CDA `effectiveTime` | `same-result.rq:12-13`, the lab view, `records.rq:21` |
| `startDate` | `clinical.ttl:103-106` | `effectiveDateTime`, else `effectivePeriod.start`, else `authoredOn` (`medication.rq:154-159`) | the medication view, `records.rq:20` |
| `Procedure` | `clinical.ttl:11-15`, `rdfs:subClassOf fhir:Procedure` at `:13` | | every procedure query |
| `Medication` | `clinical.ttl:75-78` | MedicationRequest and MedicationStatement | every medication query |

No query reads a status across kinds for its meaning: `records.rq:15-23` copies each kind's into `rec:status`, which
`labels.rq` prints and `status-sources.rq` tests only for presence (verified). #193 removes `rec:status`.

## What others do

Each FHIR quotation was read at its source on 2026-10-22 (verified) unless marked.

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
- **FHIR R5 moves medication use out of status.** `MedicationStatement.status` is "recorded | entered-in-error |
  draft", "This status concerns just the recording of the medication statement", and "MedicationStatement.adherence
  should be used for indicating a patient's adherence". The R6 build renames `Procedure.performed[x]` to
  `occurrence[x]`, "Estimated or actual date, date-time, period, or age when the procedure did occur" (verified), and
  makes `medication[x]` a CodeableReference (#128's research; not re-read here).
- **FHIR RDF.** R4 names a property per resource (`fhir:Patient.birthDate`); R5 and the R6 build share names across
  resources, so `fhir:status` is one property whose values come from whichever list the resource binds (#128's
  research, verified there).
- **FHIR's other elements.** `Immunization.vaccineCode` is a CodeableConcept, "Vaccine that was administered or was to
  be administered". `AllergyIntolerance.reaction` is a repeating backbone, "Details about each adverse reaction event";
  its `manifestation` is a CodeableConcept, "Clinical symptoms and/or signs". `Observation.effective[x]` is "The time or
  time-period the observed value is asserted as being true". `MedicationRequest.authoredOn` is "The date (and perhaps
  time) when the prescription was initially written"; MedicationRequest has no `effective[x]`. `MedicationStatement.
  effective[x]` is "The interval of time during which it is being asserted that the patient is/was/will be taking the
  medication".
- **C-CDA.** A Result Observation's `effectiveTime` "Represents the clinically relevant time of the measurement (e.g.,
  … the time the blood sample was obtained for a chemistry test)" (verified). C-CDA statuses are HL7 v3 codes, which
  the C-CDA adapter maps to FHIR codes through SKOS schemes, each concept an `skos:exactMatch` to a FHIR code IRI
  (`cascade-bridge-adapter-ccda/vocab/ccda-allergy-statuses.ttl:7-10`), and then keeps only the code
  (`in/sparql/medication.rq:174`, and the same line in allergy, condition, immunization, procedure and result; verified).
- **openEHR** has no status on OBSERVATION or EVALUATION; workflow state is the Instruction State Machine's, on an
  ACTION's `ISM_TRANSITION.current_state`, ten states from INITIAL to EXPIRED (RM ehr §8.2.5.5, verified). A problem's
  clinical state lives in archetypes, not the reference model (inferred: no RM attribute holds it).
- **OMOP CDM 5.4** has no status on DRUG_EXPOSURE or PROCEDURE_OCCURRENCE; `condition_status_concept_id` is "the point
  during the visit the diagnosis was given", not a clinical status; `stop_reason` is "as it is represented in the
  source" and is to be retired in v6.0 (verified).
- **SPHN** was not checked for statuses (unverified).
- **SSSOM** gives a mapping `object_source_version`, "Version IRI or version string of the source of the object term",
  on a Mapping and on a MappingSet (verified, in its schema).
- **Nothing** defines one status value set across kinds of record: none of the above has an "is it current?" list
  shared by conditions, immunizations and medications.

Sources: FHIR R4 Condition (https://hl7.org/fhir/R4/condition-definitions.html), AllergyIntolerance
(https://hl7.org/fhir/R4/allergyintolerance-definitions.html), Immunization
(https://hl7.org/fhir/R4/immunization-definitions.html), Observation (https://hl7.org/fhir/R4/observation-definitions.html),
MedicationRequest (https://hl7.org/fhir/R4/medicationrequest-definitions.html), MedicationStatement
(https://hl7.org/fhir/R4/medicationstatement-definitions.html); FHIR R5 MedicationStatement
(https://hl7.org/fhir/R5/medicationstatement-definitions.html); the R6 build's Procedure
(https://build.fhir.org/procedure-definitions.html); FHIR RDF (https://hl7.org/fhir/R4/fhir.ttl,
https://build.fhir.org/rdf.html); C-CDA Result Observation
(https://hl7.org/cda/us/ccda/StructureDefinition-ResultObservation-definitions.html); openEHR RM EHR
(https://specifications.openehr.org/releases/RM/latest/ehr.html); OMOP CDM 5.4
(https://ohdsi.github.io/CommonDataModel/cdm54.html); SSSOM's schema
(https://github.com/mapping-commons/sssom/blob/master/src/sssom_schema/schema/sssom_schema.yaml). The FHIR mapping of
the 59 clinical terms (https://github.com/jayostis/cascade-vocabulary/issues/128#issuecomment-6135264321).

## Choice

Every row is proposed, for the owner to rule. "#132" in the last column means the build that applies this note.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| 1. clinical state and workflow state | FHIR R4 and R5 `clinicalStatus` beside `status`; openEHR's ISM for workflow only | two terms: `clinicalStatus` on a condition and an allergy, the person's state; `status` on a procedure, an immunization, a lab result, a variant, a variant interpretation and a medication, the state of the act or the record; `verificationStatus` unchanged. Applied by #132 in the shapes and adapters, and in M14, whose period reads a condition's state | borrowed from FHIR |
| 2. which list a status value is from | FHIR binds one value set per element and resource and writes a bare code; R5 RDF shares `fhir:status` across resources; the C-CDA adapter strips an IRI to its code | the value stays FHIR's code as a string; each kind's shape names exactly one FHIR value set with `sh:in`, as all but the medication's already do, so (term, kind) fixes the list; each such pair gets a row in #128's mapping table naming the CodeSystem, so a value joins as an IRI as `records.ttl:471` joins a literal code. Shapes only; #132 | borrowed from FHIR's binding per element |
| 3. a medication's two lists | R4 MedicationRequest and MedicationStatement status; R5's recorded-status plus `adherence`; C-CDA on FHIR's ConceptMap | the status stays the source's text, listed by no shape, because a person types it and a C-CDA sends v3 codes; its one meaning for any reader is L1's lifecycle class, which already reads both FHIR lists and the v3 codes as one; `clinicalIntent` says which list a FHIR code came from. L1 unchanged | borrowed from C-CDA on FHIR's map, through L1 |
| 4. one status for every kind | nothing: no standard defines one | refused: a page that needs "is it current?" for a kind derives a class from that kind's list, as L1 does for medications | ours, by having none |
| 5. `vaccineCode` | FHIR CodeableConcept; `testCode`, `allergenCode`, `icd10Code` here, one IRI per coding | keeps its name and becomes an IRI per coding in a registered code system (CVX now), so it is the flattened CodeableConcept every code term here is; the two vaccine comparisons and M4's literal example change, in a new rule list version. M4, rewritten by #132 | borrowed from FHIR, flattened as `testCode` is |
| 6. `reaction` | FHIR `reaction` backbone, its `manifestation` a CodeableConcept | renamed `manifestation`, the text beside `manifestationCode`, as `allergen` sits beside `allergenCode`. Shapes and adapters; #132 | borrowed from FHIR's element name |
| 7. a lab result's time | FHIR `effective[x]`; C-CDA "clinically relevant time"; FHIR `performed[x]` is a procedure's | renamed `effectiveDate`, with FHIR's definition; never the time the lab ran the test. M12, and `quantities.md`'s matcher row, read it under the new name; #132 | borrowed from FHIR and C-CDA |
| 8. a medication's start | FHIR `MedicationStatement.effective[x]`; `MedicationRequest.authoredOn`, written; C-CDA `effectiveTime` low | `startDate` never takes `authoredOn`; a new `authoredDate` holds it; `records.rq`'s date for a medication is `startDate`, else `authoredDate`, so a prescription keeps a place on a timeline, and the view shows both. #132 | borrowed from FHIR's split |
| 9. duplicates | `naming.md`; #193 | one declaration each by #193's merge: `snomedCode`, `sourceRecordId`, `status`. Not ruled here; see Why for what the merge must pick | #193's |
| 10. `Procedure rdfs:subClassOf fhir:Procedure` | #128: a close match; FHIR RDF's `fhir:Procedure` is a resource | removed; `rdfs:seeAlso` to FHIR's Procedure definition, and a closeMatch row in #128's mapping table. #132 for the axiom, #128 for the row | diverged from the prototype's claim, toward #128's table |
| 11. class names `Procedure`, `Medication` | FHIR `Medication` is the product; the four classes beside them end in `Record` | renamed `ProcedureRecord` and `MedicationRecord`, as `AllergyRecord`, `ConditionRecord`, `ImmunizationRecord` and `LabResultRecord` are. #132, in the same re-mint as rows 5 to 8 | ours, for one pattern; removes a clash with FHIR |
| 12. R6's renames | R6 `occurrence[x]`, `medication[x]` a CodeableReference; SSSOM `object_source_version` | no term changes: none is named after an element R6 renames; each row of #128's mapping table names the FHIR release in `object_source_version`. #128 | borrowed from SSSOM |
| 13. how a renamed term goes | #132: "deprecated, not deleted, until alpha"; #193: never renamed after its namespace lands | removed outright, not deprecated, in the one re-mint #191 makes after #193, since no pod holds them; if #193 has not merged, in #193's own sweep | ours; departs from #132's wording, see Why |

## Why

**Two statuses, because the standards have two.** FHIR R4 and R5 give a condition and an allergy a `clinicalStatus`
and no `status`, and give the acts a `status` and no `clinicalStatus` (verified); openEHR keeps workflow state on the
ISM and no state on an observation or an evaluation. A condition "resolved" is a fact about the person; an immunization
"completed" is a fact about an act. Putting both in one term is what makes "active" ambiguous: `My active allergies.rq:10`
and `My active conditions.rq:12` test the same string against two terms that #193's merge would make one, and a reader
asking for everything "active" would get prescriptions in force beside conditions the person has: two meanings of one
word in one term. The cost is one term and the queries that name it.

**One list per term and kind, which the kind already says.** After row 1, a status's list is fixed by the term and the
record's kind, exactly as FHIR's is fixed by the element and the resource, and as R5 RDF's shared `fhir:status` relies on
(verified on #128). The shapes already say so for every kind but the medication's (verified, the table under Question). A code IRI
per value would say the list a second time and costs: every query that tests `"active"` changes, L1 reads typed text,
and the FHIR CodeSystem URIs are not stems `records.ttl:471` accepts ("never the FHIR Coding.system URI"). A literal with
a known system already joins as an IRI there, so a page that wants the IRI computes it from the mapping row. This
diverges from `partial-dates-and-absent-reasons.md` row 6, which stores a reason's IRI, because a reason may come from
two systems for one property, and a status from exactly one per kind.

**A medication's status means its lifecycle class.** #69's one kind puts two FHIR lists in one term, and people type
statuses in entries (`runtime/scripted-input/ben/entries/medication-statuses.ttl`). L1 already reads both lists, the v3
codes and free text into five classes (verified, `runtime/lifecycle.feature:8-29`), so a single list on the shape would
reject what L1 is there to read. `clinicalIntent`, which every medication version carries, says which FHIR list a code is
from where that matters. R5's move of "taking" to `adherence` is why the class, not the code, is the meaning: an R5
statement's status says nothing about use.

**No status across kinds.** The steelman for one merged term is a single "is it current?" view. No standard defines one
(none of FHIR, openEHR, OMOP has it, verified), no query here reads one (verified), and L1 shows the honest form: a class
per kind, derived from that kind's list, with the step that chose it recorded.

**Names that say what they hold.** The clinical code terms hold an IRI per coding (`testCode`, `allergenCode`,
`manifestationCode`, `icd10Code`, the condition's `snomedCode`; verified in the adapters' queries and fixtures), except
`cptCode`, the procedure's `snomedCode` and `vaccineCode`, which hold the code as a literal; and M4 already
turns `vaccineCode "141"` into `<http://hl7.org/fhir/sid/cvx/141>` to join a table (`runtime/matcher.feature:89-91`). An
IRI makes `vaccineCode` mean what FHIR's does, flattened as every code term is, and lets an NDC or SNOMED coding join
later without a new term. `manifestation` follows `allergen`'s pattern and FHIR's name. `effectiveDate` takes FHIR's name
for FHIR's element; C-CDA calls the same time "clinically relevant" and gives the sample's draw as its example, so
"performed" says something neither source says.

**A start is not a prescription's date.** FHIR's MedicationRequest has no `effective[x]`, so the FHIR adapter's
`startDate` for every prescription is `authoredOn`, the day it was written (verified, `medication.rq:154-159`). A
person reading "started 2026-03-01" is told when they began taking it, which no source said. Keeping the written date as
its own term, and letting a timeline fall back to it by name, keeps the date and its meaning. A prescription's dosage
timing (`dosageInstruction.timing.repeat.bounds[x]`) may hold a start; whether sources fill it is unmeasured
(unverified).

**What #193's merge must pick, as fallout.** The two `snomedCode` declarations differ in kind and both adapters write
both forms: a condition's an IRI, a procedure's a literal (verified, `cascade-bridge-adapter-ccda/fixtures/expected/narrative-id-twice.ttl:58,76`).
One term needs one kind; row 5's reasoning makes it the IRI. This is said for #193 to apply, not ruled here.

**The subclass claims too much.** Under RDFS a `rdfs:subClassOf fhir:Procedure` makes every Cascade procedure a FHIR
Procedure resource, which FHIR RDF's shapes would then hold to FHIR's cardinalities (inferred); #128 found only a close
match. `rdfs:seeAlso` and a mapping row give a FHIR-aware reader the pointer without the entailment.

**Removed, not deprecated.** #132 asks that a renamed term be deprecated until alpha, and #193 that no term be renamed
after its namespace lands. No pod exists (`epic-alpha/delivery.md`: re-minting is fine, once), so a deprecated term
would be kept for nobody; landing the renames in #191's re-mint keeps to #193's "once" and leaves nothing to deprecate.

## Alternatives that lost

- **Keep one `status` for every kind.** The strongest case: FHIR R5 RDF shares `fhir:status`, and one term is one thing
  for a generic reader. FHIR shares the name `status`, not `clinicalStatus`; it keeps the two elements apart, and so
  does this note.
- **One term per kind** (`conditionClinicalStatus`, `procedureStatus`, …), as R4 RDF names per resource. The strongest
  case: the name alone says the list. R5 and R6 RDF moved away from it (verified on #128), and the kind already says it.
- **Status values as code IRIs.** The strongest case: the value says its list on its own, as row 6 of
  `partial-dates-and-absent-reasons.md` does, and the C-CDA adapter holds the IRI before it strips it. The kind says the
  list already, FHIR CodeSystem URIs are not stems here, people type medication statuses, and every reader changes.
- **A shape list for medication statuses by intent.** The strongest case: a prescription's status is checked against
  MedicationRequest's list. People's text and v3 codes would warn on every entry L1 reads correctly.
- **`cvxCode` for `vaccineCode`,** a literal as `cptCode` is. The strongest case: an honest name with no query changes
  beyond the rename. It keeps the one CVX-only code term and needs a new term for an NDC or SNOMED vaccine coding.
- **`collectedDate` for a lab result's time.** The strongest case: it is what a reader means. A result with no
  specimen, a vital sign or an observation of the person, has an effective time and no collection.
- **Keep `startDate`'s fallback.** The strongest case: a prescription keeps a date in the view. Row 8 keeps that by
  naming the fallback, without saying the person started that day.
- **Deprecate, as #132 says.** The strongest case: the vocabulary's own rule after v1. Before v1 and with no pods, a
  deprecated term is kept for no reader, and #193 wants one re-mint.

## Still open

Each with its lean, and the one fact that decides it:

- **Rows 1 to 13 await the owner's ruling.** Lean: as proposed.
- **A reaction's severity.** `allergySeverity` takes the first reaction's (`allergy-intolerance.rq:139`), and row 6's
  manifestations lose which reaction they belonged to. Lean: leave for a reaction node when a source sends two reactions
  a page needs apart. Decides it: such a source.
- **R5 and R6 sources.** An R5 MedicationStatement's status is the record's, and its use is `adherence`. Lean: an R5
  adapter feeds L1 from `adherence`. Decides it: a source sending R5.
- **The medication class name.** Row 11 names it `MedicationRecord`; whether #69's one kind stays one is #69's.
- **SPHN's statuses**, not checked. Decides nothing here unless SPHN has one status list across kinds.

## What would change our mind

A query, page or partner that needs one status across kinds would reopen row 4, and its list would be derived, as L1
is. A FHIR CodeSystem registering IRI stems for its status codes would make IRIs cheap for row 2. A source sending a
status code from a list other than its kind's would show row 2's premise wrong. Sources filling a prescription's dosage
bounds would give row 8 a real start for prescriptions. A FHIR-aware consumer that needs Cascade procedures typed as
`fhir:Procedure` would reopen row 10, through a view rather than the class.
