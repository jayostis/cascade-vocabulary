# Quantities on lab results

Status: draft, 2026-10-22, proposed for the owner's ruling; from the research on #131. It would add typed terms
beside `health:resultValue`, `health:resultUnit` and `health:referenceRange`, which stay, and replace `same-result.rq`'s
value rule in a new rule list version. Names, nested nodes and a version's hash are `naming.md` and `currency.md`; a
value absent for a reason is #133's. Terms are local names in the one unversioned Cascade namespace (#193).

## Question

A lab result's value, unit and reference range are strings (`ontologies/health/v1/health.ttl:151-167`), so nothing can
compare, sort or check them. The matcher joins two results only when their value strings are identical and ignores
units (`same-result.rq:12-13`), so `6.80` and `6.8` differ and `95 mg/dL` equals `95 mmol/L`. The FHIR adapter glues a
comparator to the number (`"<5.7"`). A pod has no server to ask what a number meant: the typed form must hash alike on
every runtime, since a version is named by its content, and must say no more than the source did.

## What others do

Each quotation was read at its source on 2026-10-22 (verified) unless marked.

- **FHIR R4** `decimal` is the "union of xs:decimal and xs:double", its regex allows `[eE]` exponents, and "0.010 is
  regarded as different to 0.01, and the original precision should be preserved". `Quantity`: "If no comparator is
  specified, the value is a point value (i.e. '='). The comparator element can never be ignored"; R4 has four codes,
  `<` `<=` `>=` `>`; R5 adds `ad`, "Sufficient to achieve this total quantity"; the R6 build adds `~`, "approximately
  equal … A recommended value for the approximation is 10%". "it cannot be assumed that the unit actually contains a
  valid UCUM unit"; US Core 9: "The system SHALL be UCUM for coded quantity units". `SimpleQuantity` sqty-1: "The
  comparator is not used on a SimpleQuantity". `Range`: "The low and the high values are inclusive", and a missing bound
  means "not known". `referenceRange` is 0..*, "interpreted as an 'OR'", and on `low`: "If the low bound is omitted, it
  is assumed to be meaningless (e.g. reference range is <=2.3)". `Ratio` is for "titers (e.g. 1:128)";
  `dataAbsentReason` "SHALL only be present if Observation.value[x] is not present". FHIR RDF, R5 and the build: "any
  value with an 'e' or 'E' in it is an xsd:double, otherwise it is an xsd:decimal"; the R4 RDF page states no rule.
- **CDA and C-CDA.** `PQ.value` is a `REAL`, "the number of significant decimal digits is known as the precision"; the
  XML ITS makes `real` a union of `xsd:decimal` and `xsd:double`. `IVXB_PQ.inclusive` defaults to `true`; a range is
  `IVL_PQ`, a ratio `RTO`, an absent value a `nullFlavor` (with `unit="1"`), including `TRC`, "greater than zero, but too
  small to be quantified". C-CDA 5.0.0 makes `PQ/@unit` 1..1 and "SHOULD be taken from UnitsOfMeasureCaseSensitive
  (preferred)". C-CDA on FHIR maps a one-bound `IVL_PQ` result to a Quantity with `"comparator": "<="` (`<` when
  `inclusive="false"`), and of several reference ranges "only map the one with interpretationCode = 'N'".
- **openEHR** `DV_QUANTITY` has `magnitude: Real`, a separate `precision` in decimal places ("-1 implies no limit"), an
  `accuracy`, and `magnitude_status`, `=` `<` `>` `<=` `>=` `~`, "If not present, assumed meaning is '='", with no
  tolerance for `~`. `normal_range` is one `DV_INTERVAL` with `lower_included` and `upper_included`, plus
  `other_reference_ranges`, each with a `meaning`. Units are UCUM "(case-sensitive form) by default".
- **HL7 v2.5.1** `NM`: "'01.20' and '1.2,' are identical"; no exponent. `SN.1` is `>` `<` `>=` `<=` `=` `<>`, "If this
  component is not valued, it defaults to equal". `OBX-6` defaults to ISO+, and "All unit abbreviations are case
  insensitive". `OBX-7` is one string, "> lower limit (if no upper limit, e.g., >10)".
- **SPHN** types a value `xsd:double`, has four comparator individuals, one `ReferenceRange` (0..1), and a `Unit` whose
  code is a UCUM class IRI such as `ucum:cblbeatscbrpermin`. **OMOP** keeps `value_as_number` as a float, an
  `operator_concept_id` of `<` `<=` `=` `>=` `>` with "NULL if there's an exact numeric value", one `range_low` and
  `range_high`, and the verbatim `value_source_value` and `unit_source_value`.
- **UCUM 2.2** defines codes as strings and no IRIs. §6: "any fully conformant parser must discard all annotations";
  §12: `%{vol}`, `kg{total}` and `{RBC}` "are equivalent to '%', 'kg'" and "1". Its case-insensitive variant is
  "incompatible" with the case-sensitive one. Its licence 1.1 grants use "for the purposes of developing and
  commercializing Software Applications" and says "You may not … use the Work to create Derivative Works".
- **QUDT** v3.5.3 (CC-BY-4.0 by the GitHub API) gives 2,438 of 2,940 units a `ucumCode`, all dotted (`mg.dL-1`);
  `10*3.uL-1`, `U.L-1` and `k[IU].L-1` are absent (verified, counted from its units file).
- **XSD 1.1** `decimal`: "Precision is not reflected in this value space; the number 2.0 is not distinct from the number
  2.00"; its lexical space has no exponent. **SPARQL 1.1**: `=` on numerics is `op:numeric-equal`, `sameTerm` is "the
  same RDF term", and a basic graph pattern joins on the term, so `"6.80"` and `"6.8"` join only through a filter.
- **Oxigraph 0.5.11**, which `cascade-bridge-rs` pins, stores a parsable `xsd:decimal` by value and prints it in
  canonical form; its own test turns `"1.0"` into `"1"` (verified in its code; that a Bridge run emits `"6.8"` for
  `"6.80"` is inferred, not observed). The FHIR adapter keeps `"6.80"` today only because it writes an `xsd:string`
  (`cascade-bridge-adapter-fhir-r4/fixtures/expected/lab-every-mapped-element.ttl:20`, verified).
- **Matching.** No standard defines a same result. Particle: "Every non UUID field has to have an identical value"; de
  Graauw matches "the same code and value on the same datetime", units unmentioned.

Sources: FHIR R4 datatypes (https://hl7.org/fhir/R4/datatypes.html), SimpleQuantity
(https://hl7.org/fhir/R4/simplequantity.profile.json.html), Observation (https://hl7.org/fhir/R4/observation-definitions.html),
comparator value sets (https://hl7.org/fhir/R4/valueset-quantity-comparator.html,
https://hl7.org/fhir/R5/valueset-quantity-comparator.html, https://build.fhir.org/valueset-quantity-comparator.html),
reference-range meanings (https://hl7.org/fhir/R4/valueset-referencerange-meaning.html), FHIR RDF
(https://hl7.org/fhir/R4/rdf.html, https://hl7.org/fhir/R5/rdf.html, https://build.fhir.org/rdf.html), the R4 Turtle
example (https://hl7.org/fhir/R4/observation-example.ttl.html), US Core 9.0.0 lab
(https://hl7.org/fhir/us/core/StructureDefinition-us-core-observation-lab.html); CDA PQ
(https://hl7.org/cda/stds/core/StructureDefinition-PQ-definitions.html) and its IVXB-PQ, RTO-PQ-PQ and REAL pages, CDA
null flavours (https://hl7.org/cda/stds/core/ValueSet-CDANullFlavor.html), the v3 XML ITS from the OASIS mirror
(https://www.oasis-open.org/committees/ubl/lcsc/doc/qateam/Comment%20work%20from%20HL7/datatypes-its-xml.html), C-CDA
5.0.0 Result Observation (https://hl7.org/cda/us/ccda/StructureDefinition-ResultObservation-definitions.html), C-CDA on
FHIR 2.0.0 (https://hl7.org/fhir/us/ccda/en/CF-results.html, https://hl7.org/fhir/us/ccda/en/mappingGuidance.html);
openEHR (https://specifications.openehr.org/releases/RM/latest/data_types.html,
https://specifications.openehr.org/releases/BASE/latest/foundation_types.html,
https://specifications.openehr.org/releases/RM/latest/data_structures.html); HL7 v2.5.1
(https://www.hl7.eu/HL7v2x/v251/std251/ch02a.html, https://www.hl7.eu/HL7v2x/v251/std251/ch07.html) and the v2-to-FHIR SN
map (https://hl7.org/fhir/uv/v2mappings/ConceptMap-datatype-sn-to-quantity.html); SPHN
(https://www.biomedit.ch/rdf/sphn-schema/sphn,
https://sphn-semantic-framework.readthedocs.io/en/latest/user_guide/data_generation.html); OMOP CDM 5.4
(https://ohdsi.github.io/CommonDataModel/cdm54.html); UCUM 2.2 (https://ucum.org/ucum), its licence
(https://ucum.org/license); QUDT (https://github.com/qudt/qudt-public-repo/blob/v3.5.3/src/main/rdf/vocab/unit/VOCAB_QUDT-UNITS-ALL.ttl);
w3id.org/uom (https://github.com/units-of-measurement/units-of-measurement); Vreeman et al. 2018 on LOINC's example
units (https://pmc.ncbi.nlm.nih.gov/articles/PMC6251552); XSD 1.1 (https://www.w3.org/TR/xmlschema11-2/); SPARQL 1.1
(https://www.w3.org/TR/sparql11-query/); ucum-lhc (https://github.com/lhncbc/ucum-lhc); Oxigraph v0.5.11's
`numeric_encoder.rs` and `decimal.rs`; Particle (https://docs.particlehealth.com/docs/data-deduplication), Health
Gorilla (https://apidocs.healthgorilla.com/getting-started/platform-overview/data-lifecycle), de Graauw
(https://www.marcdegraauw.com/2024/01/09/deduplicating-patient-summaries/), Marley #1258
(https://github.com/earthians/marley/pull/1258). The research on #131
(https://github.com/jayostis/cascade-vocabulary/issues/131#issuecomment-6345803866); the quantity pattern
(https://github.com/jayostis/cascade-runtime-js/issues/183#issuecomment-6093896826) and its review against FHIR,
openEHR, UCUM, SPHN and OMOP (https://github.com/jayostis/cascade-runtime-js/issues/183#issuecomment-6135136922).

## Choice

Every row is a proposal for the owner's ruling. Where the research corrected a premise of #131, the row says so.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| quantity node | FHIR `Quantity`; openEHR `DV_QUANTITY`; `naming.md`'s `#source-version` | proposed: a `Quantity` nested in the version as `<version>#value`, `#reference-low`, `#reference-high`, hashed with it, carrying `decimalValue`, `comparator`, `ucumUnit`, `unitText`; reached by `value`, `referenceLow`, `referenceHigh`; the text terms stay | borrowed from FHIR's parts; the nesting is `naming.md`'s |
| number | FHIR keeps the written form; v2 and XSD say it carries nothing; SPHN, OMOP a float | proposed: `xsd:decimal` by value, written in its canonical form; the written form stays in `health:resultValue`. The alternatives: the value plus a separate written string, kept only if trailing zeros must survive on the node; refusing to canonicalise, which Oxigraph does not allow. An exponent is written as a plain decimal, or refused | diverges from FHIR's "precision should be preserved" on the node, and from SPHN's and OMOP's float; corrects #131's "exact `xsd:decimal` as the source wrote it", which the Bridge's store cannot keep |
| comparator | FHIR R4 and SPHN four; openEHR adds `=` `~`; v2 adds `=` `<>`; R5 `ad` | proposed: `sh:in ("<" "<=" ">=" ">")`; `=` written as none; `~`, `<>` and `ad` refused with a finding, the text kept; a comparator makes the value a bound | borrowed from FHIR R4; diverges from openEHR's `~` |
| reference range | FHIR 0..*; C-CDA on FHIR the `N` one; openEHR one normal plus others; v2, SPHN, OMOP one | proposed: bounds inclusive, never a comparator on one (sqty-1); a missing bound one-sided; one typed range, the one the source marks normal or the only one, the rest as text; a one-bound `IVL_PQ` result from C-CDA becomes a quantity with a comparator, as C-CDA on FHIR maps it, or stays a range | borrowed from FHIR's `referenceRange` and C-CDA on FHIR; corrects #131's "a missing bound means unknown", which is `Range`'s wording, and the #183 table's keeping a one-bound result as a range |
| unit | FHIR `code` when `system` is UCUM; C-CDA "SHOULD" UCUM; v2 ISO+, case-insensitive; UCUM §6 | proposed: `ucumUnit` is the source's exact string, case and `{annotations}` kept, only where the source says it is case-sensitive UCUM (FHIR `system`, C-CDA `@unit` under a Warning shape); `unitText` is the display unit; a unit outside UCUM, and every v2 `OBX-6`, is `unitText` alone. The alternatives: store the annotation-stripped form instead, or both | borrowed from FHIR; corrects #183's "a non-UCUM C-CDA unit is a source error" |
| unit IRI | UCUM none; SPHN UCUM classes; QUDT `ucumCode`, dotted | proposed: none; a QUDT or SPHN IRI, if ever, is a table beside the string | borrowed from UCUM; corrects #131's "no IRIs for units": UCUM defines none, others do |
| text only | FHIR `Ratio`, `Range`, `dataAbsentReason`; CDA `RTO`, `IVL_PQ`, `nullFlavor`; openEHR `DV_PROPORTION` | proposed: a ratio, a titre, a range given as a result and a value absent for a reason get no `value`, each named as such; the text stays; the absent reason is #133's | diverges: every standard types these, and none is typed here yet |
| matcher | none; Particle every field; de Graauw code, value, datetime | proposed: same test code and same instant, as `same-result.rq` has today; values equal by `FILTER(?a = ?b)`, never a shared variable; the same comparator or none on both; units equal after UCUM's annotations are stripped, or the exact strings, or none on both; the text rule where either side has no `value`; a new rule list version | ours: no standard defines a duplicate |
| conversion | ucum-lhc within a dimension; LOINC molar masses | proposed: out of scope; a unit that differs goes to review | waits on UCUM's licence |

## Why

**The value is the number, not the spelling.** A version is named by a hash of its triples (`currency.md`), so two
runtimes must write one lexical form for one number or they mint two versions of one state. Oxigraph prints a decimal
in canonical form whatever it was given (verified in its code), and a runtime on another store may not (inferred), so
the only form every runtime can agree on is the canonical one. The written form is not lost: `health:resultValue` keeps
`"6.80"` as the source wrote it, which is what a person reads. The standards themselves disagree on whether `0.010` and
`0.01` differ, FHIR yes, v2 and XSD no, so a node that compares by value takes the side the store already takes.

**A decimal, not a float.** FHIR `decimal` and v3 `REAL` admit an exact decimal, and a double turns `0.1` into another
number. An exponent is exact as a plain decimal, so `1.2e3` as `1200` loses only the spelling, which the text keeps.

**Four comparators, because four is what every source agrees on.** The four are the intersection of FHIR R4, openEHR,
v2, SPHN and OMOP. `=` means the same as none in all three that have it. `~` is openEHR's and an R6 CI build's, with no
tolerance in one and 10% recommended in the other; a value that is "about" something can neither be compared as a
point nor as a bound. `ad` is about dosing and `<>` is v2's alone. A comparator makes the value a bound, which FHIR
says "can never be ignored", so a query testing the number still knows it is a bound.

**One range, and a missing bound is one-sided.** FHIR's `referenceRange.low` says an omitted bound is "meaningless
(e.g. reference range is <=2.3)": a range with a high only is everything below it, which is how a lab writes `<5.7`.
`Range`'s "not known" is the generic type's, not the reference range's. One typed range is what v2, SPHN and OMOP hold
and what C-CDA on FHIR keeps; FHIR says "most observations only have one generic reference range", and the rest stay in
`health:referenceRange`, so nothing is dropped. A bound carries no comparator because FHIR forbids one and the
inclusivity is the range's.

**The unit as the source wrote it, compared as UCUM says.** UCUM is case-sensitive and its case-insensitive variant is
"incompatible", so a v2 unit, case-insensitive by default, is display text and never `ucumUnit`. Storing the exact
string keeps what the source said; UCUM §6 says annotations carry nothing and a conformant parser discards them, so the
matcher strips them rather than the store, and `{beats}/min` equals `/min` while both strings survive.

**No unit IRIs yet.** UCUM defines none. QUDT's codes are dotted, so `mg.dL-1` never string-matches the `mg/dL` labs
send, and `10*3/uL` and `U/L`, among the commonest lab units, are absent (verified, counted). SPHN's classes exist, but
under what permission it republishes UCUM was not found (unverified). An IRI needs a normaliser and a gap table, and a
string needs neither.

**Text only, named.** A titre is a ratio in every standard, a range result is not a point, and an absent value is a
reason; any of them in a `decimalValue` would say what the source did not.

**What a same result needs.** No standard defines one, so the rule is ours: today's code and instant, plus value,
comparator and unit. The filter makes the rule mean one thing on any store: a shared variable joins `"6.8"` and
`"6.80"` in a store that canonicalises and not in one that does not (inferred). A changed rule is a new rule list
version, as `naming.md` requires, so the claims the old rule made stop counting by derivation.

**Conversion waits.** Within a dimension it is mechanical, but mass to molar needs a molar mass per LOINC code, and
UCUM's licence forbids derivative works; whether a published LOINC-keyed table is one is a legal question (unverified).

## Alternatives that lost

- **A float or double, as SPHN and OMOP do.** The strongest case: two of the standards the vocabulary cites, and every
  engine compares doubles. A double is not the number a lab reported, and FHIR and v3 admit an exact decimal.
- **A precision attribute, as openEHR has.** The strongest case: twenty years of practice, and it survives any store.
  The text term already holds the written form, and a second field to keep in step is a second place to disagree.
- **A string, as today.** The strongest case: lossless. Nothing can compare or check it, and `"<5.7"` hides a bound.
- **Many typed ranges, as FHIR allows.** The strongest case: lossless, and FHIR's model. A range per age, sex and phase
  needs a typed `appliesTo` the pod has no use for yet; the text keeps them, and a `ReferenceRange` node can come later.
- **Unit IRIs as the unit.** The strongest case: an IRI is what RDF joins on, and SPHN does it. UCUM defines none, the
  best-kept set is dotted and lacks common lab units, and the table would be ours to maintain.
- **`~` as a fifth comparator.** The strongest case: openEHR has it and FHIR R6 may. No R4 source can send it, its
  tolerance is undefined or 10% by recommendation, and the matcher could compare it with nothing.
- **Units compared as exact strings, as #131 says.** The strongest case: simplest, and never wrong when it says equal.
  UCUM says a conformant parser discards annotations, so equal units with and without `{beats}` would go to review.
- **Refusing to canonicalise.** The strongest case: FHIR's "the original precision should be preserved". Oxigraph,
  which the Bridge pins, stores by value, so the form a Bridge writes is not the adapter's to choose (inferred).

## Still open

Every Choice row is the owner's ruling; each with its lean, and the one fact that decides it:

- **Quantity node.** As proposed, with #193's re-mint, so each lab version is renamed once. Whether #193 lands first.
- **Number.** The value alone, canonical; an exponent as a plain decimal. What a Bridge run emits for `"6.80"`.
- **Comparator.** The four, `=` as none, the rest refused with a finding. A lab source observed sending `~`.
- **Reference range.** One-sided, one typed range, an exclusive reference bound as text, a one-bound C-CDA result as a
  comparator. A source observed sending `inclusive="false"` on a reference range.
- **Unit.** The exact string stored, stripped only in the matcher. Whether a SPARQL `REPLACE` strips as UCUM's grammar
  does, including a unit that is only an annotation, which is `1`.
- **Unit IRI.** None. A consumer of the pod that needs an IRI to join on.
- **Text only.** As proposed. A page that must compare titres.
- **Matcher.** Annotation-stripped units, equal comparators. Two sources' units differing only by an annotation.
- **Conversion.** Out of scope. A reading of UCUM's licence on a LOINC-keyed table.

## What would change our mind

A runtime whose store keeps a decimal's lexical form, with a page that must show trailing zeros from the node, would
bring back the written string. Lab sources sending `~` or exclusive reference bounds would add them. Sources sending
several typed ranges a page needs would add a `ReferenceRange` node. QUDT covering the lab-sent forms, or SPHN's UCUM
classes found under an open licence, would make an IRI cheap. A pair of results the matcher joins that a person files
Different over, or one it keeps apart that a person files Same over, would show the unit or comparator rule wrong.
