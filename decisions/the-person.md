# The person: gender, death, and the sex no term holds yet

Status: draft, 2026-10-29, written with the terms it rules under phase 1 of the care-gap epic
([#287](https://github.com/jayostis/cascade-vocabulary/issues/287), item 10,
[#297](https://github.com/jayostis/cascade-vocabulary/issues/297)). The area note `clinical-terms-follow-fhir.md` asks
for: what the person's own record borrows from FHIR, and where it departs. Depends on `clinical-terms-follow-fhir.md`
(a term follows FHIR R4 and US Core unless this note says why not), `version-content.md` (row 6 of its borrow table),
`one-meaning-per-term.md` (a coded element FHIR types `code` is held as its code, a string) and
`partial-dates-and-absent-reasons.md` (how a source date is typed, padded and left absent). The adapters' side is the
FHIR and C-CDA adapter pull requests of #287's wave 1, which #297 names.

## Question

A care-gap rule asks a question about a person, and two facts about the person change every question. A person who
has died is asked nothing: a rule that asks a dead person to repeat a test is wrong in a way no wording repairs. And
most screening questions after the first two turn on sex. Both adapters drop the administrative gender today
(`fhirr4:patientGender`, `ccda:patientGender`, each a "no predicate carries it" gap), and neither reads a death. What
does a version of a patient profile hold for gender and death, from FHIR and from C-CDA, and does it hold sex?

What makes it hard: a pod keeps every source's copy, and the sources disagree on form. FHIR states death as a choice of
a boolean or a time; C-CDA has an indicator and a time as two elements, either or both. FHIR and C-CDA code gender in
different systems. And administrative gender is not sex, which a screening rule needs and which few sources send.

## What others do

Read on 2026-10-29 unless marked.

- **FHIR R4 `Patient.gender`**: "Administrative Gender - the gender that the patient is considered to have for
  administration and record keeping purposes", a `code`, 0..1, bound **required** to AdministrativeGender
  (`male | female | other | unknown`). Its comment: "The gender might not match the biological sex as determined by
  genetics or the individual's preferred identification", and "Systems providing decision support or enforcing
  business rules should ideally do this on the basis of Observations dealing with the specific sex or gender aspect of
  interest (anatomical, chromosomal, social, etc.) However, because these observations are infrequently recorded,
  defaulting to the administrative gender is common practice."
- **FHIR R4 `Patient.deceased[x]`**: "Indicates if the individual is deceased or not", `boolean | dateTime`, 0..1, a
  modifier element "because once a patient is marked as deceased, the actions that are appropriate to perform on the
  patient may be significantly different". Its comment: "If there's no value in the instance, it means there is no
  statement on whether or not the individual is deceased."
- **US Core 9.0.0 Patient**: `gender` is required by the profile's binding to AdministrativeGender; `deceased[x]` is
  marked Additional USCDI, and certifying systems "SHALL support at least Patient.deceasedDateTime". The **US Core
  Individual Sex Extension** (trial use, maturity 5) "represents the U.S. Core Data for Interoperability (USCDI) data
  element 'Sex'", "Documentation of a specific instance of sex", a Coding bound extensibly to Federal Administrative
  Sex. The **US Core Birth Sex Extension** is now Informative, "aligns with LOINC 76689-9 (Sex assigned at birth)".
- **C-CDA on FHIR 2.0.0** maps `patient/administrativeGenderCode` to `Patient.gender` through its ConceptMap
  `CF-AdministrativeGender`, from `http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender` to
  `http://hl7.org/fhir/administrative-gender`: `M` to `male` (equivalent), `F` to `female` (equivalent), `UN` to
  `other` (wider). It has no row for a null flavour. It maps `patient/sdtc:deceasedInd` to `deceasedBoolean` and
  `patient/sdtc:deceasedTime` to `deceasedDateTime`: "Only one of deceasedBoolean or deceasedDateTime may exist. If
  both are present in CDA, use deceasedDateTime."
- **C-CDA** carries sex outside the header only as observations: the Birth Sex Observation
  (`2.16.840.1.113883.10.20.22.4.200`, LOINC 76689-9), which is R2.1's, and the Sex Observation
  (`2.16.840.1.113883.10.20.22.4.507`, LOINC 46098-0, template version 2023-06-28), which R2.1 does not have. The kits'
  C-CDA downloads are R2.1 and carry neither.
- **FHIR RDF** keeps a choice element as one property whose value's datatype says which choice it was (memory, not
  re-read; `partial-dates-and-absent-reasons.md` cites its typing by inspection).
- **This vocabulary.** `cascade:dateOfBirth` is the one fact about the person a version holds besides names
  (`ontologies/cascade.ttl`). FHIR elements typed `code` with a required binding, the statuses, are held as their code
  strings with `sh:in` (`one-meaning-per-term.md`); `code-iris.md` gives code IRIs to the systems of `Coding`s.

Sources: https://hl7.org/fhir/R4/patient-definitions.html#Patient.gender,
https://hl7.org/fhir/R4/patient-definitions.html#Patient.deceased_x_,
https://hl7.org/fhir/us/core/StructureDefinition-us-core-patient.html,
https://hl7.org/fhir/us/core/StructureDefinition-us-core-individual-sex.html,
https://hl7.org/fhir/us/core/StructureDefinition-us-core-birthsex.html,
https://hl7.org/fhir/us/ccda/ConceptMap-CF-AdministrativeGender.json, https://hl7.org/fhir/us/ccda/en/CF-patient.html,
https://hl7.org/cda/us/ccda/StructureDefinition-BirthSexObservation.html,
https://hl7.org/cda/us/ccda/StructureDefinition-SexObservation.html. The research behind the borrow is #288 comment 1
(the by-kind comparison), ranked for the care-gap epic as row 6 of `version-content.md`'s borrow table.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| gender | FHIR R4 `Patient.gender`, AdministrativeGender (required); C-CDA `administrativeGenderCode`, HL7 v3 AdministrativeGender | `cascade:administrativeGender` on a version of a patient profile, one of FHIR's four codes, `male`, `female`, `other`, `unknown`, held as the code string as FHIR's other required `code` elements are (`ontologies/cascade.ttl`, `ontologies/cascade.shapes.ttl`) | borrowed |
| a C-CDA gender | C-CDA on FHIR's `CF-AdministrativeGender` | mapped into FHIR's codes at conversion by that concept map, transcribed into the C-CDA adapter: `M` male, `F` female, `UN` other. A null flavour or a code outside the map writes no gender, and the adapter reports it as a value not mapped (#297) | borrowed |
| death | FHIR R4 `Patient.deceased[x]` (`boolean` or `dateTime`); C-CDA `sdtc:deceasedInd`, `sdtc:deceasedTime` | two terms. `cascade:deceased`, an `xsd:boolean`: true where any of the source's elements says the person died (a true indicator, or a time with a value), false where the source says they have not; absent where it says nothing. `cascade:dateOfDeath`: when, typed and padded as every source date is, and absent for a reason only beside a death the source states (`ontologies/cascade.ttl`) | borrowed meaning; diverged in form: FHIR's choice is two terms, so a rule asks one question whichever form arrived |
| sex | US Core 9's Individual Sex extension (USCDI "Sex"); its Birth Sex extension; C-CDA's Sex Observation and Birth Sex Observation | no term in phase 1. The term is added with the first rule that reads sex, the cervical cancer screening question, with its own row here (#287) | diverged, for now: no rule reads it, and the kits' C-CDA R2.1 sources can send only birth sex |

## Why

**Why the gender is FHIR's code, as a string.** (rows "gender", "a C-CDA gender") `Patient.gender` is a `code` with a
required binding, the same kind of element as the statuses `one-meaning-per-term.md` holds as their code strings. It
has one system, so a code IRI under `code-iris.md` would name a system nobody else uses for this element, and add a
`cascade:CodeSystem` that every runtime enumerating systems must learn, for nothing a query gains. A C-CDA gender is
mapped once, at conversion, by HL7's own concept map, so two copies of one person compare by `sameTerm` across
formats. `UN` (undifferentiated) maps to `other` because that is what the map says; mapping it to `unknown` would say
the source did not know, which it did not say. A null flavour is left unwritten because the map has no row for it,
and the adapter's finding keeps the loss visible, as `partial-dates-and-absent-reasons.md` keeps every other loss.

**Why death is two terms.** (row "death") The rule a death decides is "ask this person nothing", and it must hold
however the source said it: a FHIR source that sends only `deceasedDateTime`, as US Core makes the one form a
certified system must support, and a C-CDA source that sends `sdtc:deceasedInd` alone. One boolean answers that in one
triple pattern. The time is a separate term because it is a date like every other source date, and takes their
partial-date union, padding and absent reasons from `partial-dates-and-absent-reasons.md` unchanged. A time absent
for a reason is written only beside a stated death, a true `sdtc:deceasedInd` with a null-flavoured
`sdtc:deceasedTime`: a null-flavoured time alone, or FHIR's absent reason on a `deceasedDateTime` with no value, does
not say the person died, and writing its absent reason would leave a date of death on a person not stated dead.
"Either says so" is C-CDA on FHIR's rule ("if both are present in CDA, use deceasedDateTime"): a time is a death,
whatever the indicator says.
FHIR's own comment makes absence say nothing, so `cascade:deceased` is never written false for a source that is
silent.

**Why sex waits.** (row "sex") No phase 1 rule and neither of the first two rules (B12 on metformin, uACR in diabetes)
reads sex, so a term now would be designed without the question that decides it: which of US Core's Individual Sex,
Birth Sex, or an anatomy record (FHIR's own example is an alert about a hysterectomy) a screening rule needs. The kits'
C-CDA sources are R2.1, which has only the Birth Sex Observation, so a term now would be filled from one format only.
Administrative gender is not a substitute: FHIR's comment on `Patient.gender` says decision support "should ideally"
read observations of the specific aspect, and defaults to administrative gender only because they are rarely
recorded.

## Alternatives that lost

- **One term for death, a boolean or a time, as FHIR's choice.** The strongest case: it is FHIR's form, and FHIR RDF
  keeps a choice as one property. It lost because a property whose range is a boolean or a date must be read by
  datatype in every rule, and C-CDA sends the indicator and the time as two elements, which one value cannot hold.
- **Only a date of death, with "deceased" inferred from it.** The strongest case: one term, and a time is the stronger
  statement. It lost because a source may say a person died without saying when (`deceasedBoolean`,
  `sdtc:deceasedInd` alone), and that is the case a rule must not miss.
- **Gender as a code IRI under `https://ns.cascadeprotocol.org/codes/administrative-gender/`.** The strongest case:
  every other coded value with a system becomes an IRI under `code-iris.md`. It lost because `Patient.gender` is a
  `code`, not a `Coding`, with one fixed system; its siblings of that kind, the statuses, are strings, and an IRI would
  cost a code system every runtime enumerates.
- **Keep the C-CDA code as its source gave it (`F`, `M`, `UN`).** The strongest case: nothing is mapped, nothing is
  lost. It lost because two copies of one person would hold two codes for one gender, and a rule would have to map at
  every read what HL7 already maps once.
- **Borrow US Core's Individual Sex extension now.** The strongest case: it is USCDI's "Sex", the element a screening
  rule will want, and borrowing early means sources' values are kept from the first pull. It lost on the evidence
  above: no rule reads it in phase 1, C-CDA R2.1 cannot fill it, and which sex element a rule needs is that rule's
  question.

## Still open

- **Sex.** Which element the cervical cancer screening question reads: Individual Sex, Birth Sex, an anatomy record,
  or administrative gender as FHIR's stated fallback. Lean: Individual Sex where the source sends it, with the
  question saying when it fell back to administrative gender. Ruled by the rule's own change under #287.
- **A C-CDA gender null flavour.** Whether `UNK` should be written as FHIR's `unknown`, which means the same. Lean:
  no, while C-CDA on FHIR's map has no row for it; revisit if the map gains one.
- **The patient-profile view.** Whether the view of the person shows gender and death. Not ruled here: a kit's
  `expected/` changes only from its scenario.

## What would change our mind

- **A rule that needs sex is written**, which reopens row "sex" with that rule's question.
- **C-CDA on FHIR's map changes**, which changes row "a C-CDA gender" with it.
- **US Core moves to R5's Patient**, whose sex and gender considerations are the "other interoperability
  considerations" US Core 9 points at, which reopens rows "gender" and "sex" together.
