# What a record was given for: a link to the condition's record, and the codes of a reason

Status: draft, 2026-11-17, written with step C4b of the Families Beta epic
([#437](https://github.com/the-cascade-protocol/cascade-vocabulary/issues/437), part of
[#415](https://github.com/the-cascade-protocol/cascade-vocabulary/issues/415)), which applies it. It applies the owner's Ruling 3, 7.7
([#416](https://github.com/the-cascade-protocol/cascade-vocabulary/issues/416#issuecomment-6934505969)): one link term for medicines,
procedures and a visit's reason, naming the condition's record; and the ruled design A, 2.1: a link names a record or a
document, never a version. Depends on `clinical-terms-follow-fhir.md` (a term follows FHIR R4, and a departure is
explained in its area's note: this is the reasons area's), `version-content.md` (a link between records is content of a
version), `naming.md` (the record a link names is named by the rule that names the target's own record) and
`code-iris.md` (a code is an IRI in a listed system, else a literal typed by its system).

## Question

A clinician prescribes an inhaler for asthma; a spirometry is done for it; a visit is about it. The sources say so: FHIR
R4 gives `reasonReference` and `reasonCode` on a MedicationRequest, MedicationStatement, Procedure, Immunization and
Encounter, and C-CDA nests an Indication inside a Medication Activity or a Procedure Activity. A pod dropped all of it,
so a condition's page could not say what was given for it, and a medicine's row could not say what it is for. What
does a version hold of its reason, what does the link name, and which kinds may carry it?

What makes it hard: the condition and the medicine are separate records, each possibly joined with others into an
entry, each possibly judged erroneous later; the link must survive joins and outlive the version it was read from. A
source may name a reason as a record, as a code, or both; and FHIR lets the reason be an Observation, a
DiagnosticReport or another record, not only a Condition.

## What others do

- **FHIR R4** (4.0.1). `MedicationRequest.reasonReference`, 0..*, Reference(Condition | Observation): "Condition or
  observation that supports why the medication was ordered"; `MedicationRequest.reasonCode`, 0..*, CodeableConcept:
  "The reason or the indication for ordering or not ordering the medication … If a full condition record exists or
  additional detail is needed, use reasonReference". `MedicationStatement.reasonReference` takes Condition | Observation
  | DiagnosticReport; `Procedure.reasonReference` takes Condition | Observation | Procedure | DiagnosticReport |
  DocumentReference; `Immunization.reasonReference` takes Condition | Observation | DiagnosticReport;
  `Encounter.reasonReference` takes Condition | Procedure | Observation | ImmunizationRecommendation. Every one has a
  `reasonCode` beside it (verified 2026-11-17 on the definitions pages below).
- **FHIR R5** merges the two into one element, `MedicationRequest.reason`, 0..*, CodeableReference(Condition |
  Observation), with R4's definition (verified). A CodeableReference holds a concept, a reference, or both.
- **C-CDA** (current IG, Indication `2.16.840.1.113883.10.20.22.4.19:2023-05-01`): "The id element can be used to
  reference a problem recorded elsewhere in the document, or can be used with a code and value to record the problem";
  "If the id element is used to reference a problem recorded elsewhere in the document then this id must equal another
  entry/id in the same document instance"; and "If the ID element does not reference a problem recorded elsewhere in the
  document, then observation/value must be populated with a coded entry" (verified).
- **FHIR RDF** writes `fhir:MedicationRequest.reasonReference` (R4) to a `fhir:Reference` node carrying `fhir:link`: one
  predicate per resource and a wire-format node, which `clinical-terms-follow-fhir.md` (row "wire format") does not copy.
- **schema.org** has `MedicalIndication` ("A condition or factor that indicates use of a medical therapy"), a class of a
  therapy's general indications; the current release has no property from a therapy to one, and nothing links one
  person's prescription to their own condition record (verified in `schemaorg-current-https.jsonld`, 2026-11-17).
- **The OBO Relation Ontology**'s "is substance that treats" (RO_0002606) relates a substance to a disease as kinds,
  "c is a substance that treats d if c is a material entity (such as a small molecule or compound) and d is a
  pathological process, phenotype or disease" (verified on OLS), not one record to another.
- **This vocabulary.** `cascade:authorizingPrescription` already links a dispense's version to its prescription's record
  by the record's IRI; the dispenses view names that record's entry (`queries/views/medication-dispenses.rq`).

Sources: https://hl7.org/fhir/R4/medicationrequest-definitions.html#MedicationRequest.reasonReference,
https://hl7.org/fhir/R4/medicationstatement-definitions.html#MedicationStatement.reasonReference,
https://hl7.org/fhir/R4/procedure-definitions.html#Procedure.reasonReference,
https://hl7.org/fhir/R4/immunization-definitions.html#Immunization.reasonReference,
https://hl7.org/fhir/R4/encounter-definitions.html#Encounter.reasonReference,
https://hl7.org/fhir/R5/medicationrequest-definitions.html#MedicationRequest.reason,
https://hl7.org/cda/us/ccda/StructureDefinition-Indication.html, https://hl7.org/fhir/R4/rdf.html,
https://schema.org/MedicalIndication, http://purl.obolibrary.org/obo/RO_0002606.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| the link | FHIR R4 `reasonReference`; this vocabulary's `authorizingPrescription` | `cascade:reasonCondition`, on a version, the IRI of the condition's record, one for each the source named; it may name a record no source of the pod sent (`ontologies/cascade.ttl`) | borrowed from FHIR's element, named for what it names |
| what it may name | FHIR: Condition, Observation, DiagnosticReport, Procedure, DocumentReference | a condition's record only; an adapter reports a reference to anything else, or to a condition the source does not hold, as a finding and writes no link | diverged: the question asked of it is "what was this for", which a condition answers; the others are evidence |
| one term for every kind | FHIR's per-resource elements; Ruling 3, 7.7 | one term whose domain is every kind of record FHIR R4 gives a reason and the vocabulary holds: a medication, a procedure, a vaccination; a visit joins when its kind does (C3) | borrowed from the ruling |
| the codes | FHIR R4 `reasonCode`; C-CDA Indication `value` | `cascade:reasonCode`, a code IRI in any listed system, and `cascade:reasonCodeInOtherSystem`, a literal typed by its system, as every code of the vocabulary is held; carried whenever the source gives them, with a link or without | borrowed |
| R5 | `reason`, a CodeableReference | follows R4's split, which sources send; R5's one element maps to the two terms without loss | borrowed from what sources send |
| a C-CDA Indication | the IG's id rule | an Indication whose id equals the id of a Problem Observation of the same document names that observation's record; its value is a reason code; neither is a finding | borrowed |
| views and questions | | each member's values in the medications, procedures and immunizations views carry its links and codes; `pod/My active medications` and `pod/My medication history` give each record's reasons, a condition by its entry's name and entry; `pod/My active conditions` and `pod/My condition history` give each entry given for one of its records, once (`queries/`) | ours |

## Why

**Why a record, not a version.** A version is one source's statement at one time; the condition's record outlives it,
and its entry is found from the record by the entry's members. A link to a version would break at the next revision of
the condition; a link to the record survives that, survives the condition joining another record, and stops showing
when the condition is judged erroneous, since its record is then in no entry. This is the ruled design A's rule.

**Why only a condition.** A link is read as "this was given for that", and the condition's page is where it is shown. An
Observation or DiagnosticReport as a reason is evidence for a decision, not what was treated; showing it beside a
condition would mislead, and losing it loses nothing the source's narrative and the reason codes do not hold. When a
second kind of target earns a page of its own, a second term names it.

**Why one term across kinds.** "Which medicines are for the asthma" and "which visits were about it" are one question,
asked from the condition, and a model writing a query should not need to know which kind it is reading. FHIR repeats
the element per resource only because its resources are separate documents.

**Why codes beside the link.** FHIR R4 sends both and says a code is used when no full record exists; C-CDA requires the
value when the id names no problem. A code with no link is the only reason some sources give, and carrying it whenever
it is given costs nothing.

## Alternatives that lost

- **One term naming any record as a reason, as FHIR's reasonReference does.** The strongest case: nothing the source
  says is dropped. It lost because every reader would then filter by kind to answer the one question asked, and a
  question listing an Observation as what a medicine is for would be wrong.
- **Follow R5's single `reason`.** The strongest case: one element, the future. It lost because RDF needs no
  CodeableReference: a code and a record are two kinds of value, and two terms hold them without a node in between.
- **A term per kind** (`medicationReasonCondition`, `procedureReasonCondition`). The strongest case: each domain exact.
  It lost to Ruling 3, 7.7, and to the reader who asks the question from the condition.
- **schema.org or RO.** Both relate kinds of things (a drug, a disease), not one person's records; neither names the
  record a source wrote.

## Still open

- **A visit's reason** (C3, wave 2) adds the visit's kind to the three terms' domain; its diagnosis is its own term.
- **An Indication with an id that matches two Problem Observations** in one document: the naming rule already falls
  back for two entries with one id (`naming.md`, row "record from C-CDA"); lean: the link names the record the
  fallback names for each, and the finding the naming rule raises stands.

## What would change our mind

- Sources that send most reasons as Observations a person would call the reason (a lab value as the reason for a
  dose), which would make a second link term worth its question.
- A reader that needs the reason's own version, which no question asks today.
