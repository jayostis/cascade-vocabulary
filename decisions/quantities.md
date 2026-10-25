# Quantities on lab results

Status: ruled, 2026-10-22, from the research on #131 and the owner's rulings of that day; applied by #131, which writes
the terms, shapes, queries and feature rules. It adds typed terms beside `health:resultValue`, `health:resultUnit` and
`health:referenceRange`, which stay, and replaces `same-result.rq`'s value rule in a new rule list version. Names,
nested nodes and a version's hash are `naming.md` and `currency.md`; a value absent for a reason is
`partial-dates-and-absent-reasons.md`'s (#133). Terms are local names in the one unversioned Cascade namespace (#193).

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

Every row is ruled, 2026-10-22. Where the research corrected a premise of #131, the row says so.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| quantity node | FHIR `Quantity`; openEHR `DV_QUANTITY`; `naming.md`'s `#source-version` | a `Quantity` nested in the version as `<version>#value`, `#reference-low`, `#reference-high`, hashed with it, carrying `decimalValue`, `writtenValue`, `quantityComparator`, `ucumUnit`, `unitText`; reached by `resultQuantity`, `referenceRangeLow`, `referenceRangeHigh` (and a ratio's `resultRatioNumerator` and `resultRatioDenominator`, a range's `resultRangeLow` and `resultRangeHigh`); `resultValue` and `referenceRange` stay as text, and `resultUnit` is no longer written for a quantity, whose unit is on its node and which the lab-results view shows from there, but is written beside a value an adapter refused to type and kept as text (`ontologies/cascade.shapes.ttl`) | borrowed from FHIR's parts; the nesting is `naming.md`'s |
| number | FHIR keeps the written form; v2 and XSD say it carries nothing; SPHN, OMOP a float | two literals on the quantity node, both hashed into the version: `decimalValue`, an `xsd:decimal` by value, which the store canonicalises (`"6.80"` to `"6.8"`), for comparison, sorting and bounds; `writtenValue`, a plain string of the exact characters the source sent (`"6.80"`), which no store normalises; openEHR's precision is derivable by counting places and is not stored; an exponent (`1.2e3`) is a plain decimal in the typed literal and kept as sent in the string; the written form no longer rides on `health:resultValue` (`ontologies/cascade.shapes.ttl`) | borrowed from FHIR for precision, kept in the written form, and from XSD for the value; diverges from SPHN's and OMOP's float; corrects #131's "exact `xsd:decimal` as the source wrote it", which the Bridge's store cannot keep |
| comparator | FHIR R4 and SPHN four; openEHR adds `=` `~`; v2 adds `=` `<>`; R5 `ad` | `sh:in ("<" "<=" ">=" ">")`; `=` written as none; `~`, `<>` and `ad` refused with a finding, the text kept; a comparator makes the value a bound (`ontologies/cascade.shapes.ttl`) | borrowed from FHIR R4; diverges from openEHR's `~` |
| reference range | FHIR 0..*; C-CDA on FHIR the `N` one; openEHR one normal plus others; v2, SPHN, OMOP one | bounds inclusive, never a comparator on one (sqty-1); a missing bound one-sided; one typed range, the one the source marks normal or the only one, the rest as text; a one-bound `IVL_PQ` result from C-CDA becomes a quantity with a comparator, as C-CDA on FHIR maps it, never a Range result, since a bound with nothing on the other side is what a comparator says (`ontologies/cascade.shapes.ttl`) | borrowed from FHIR's `referenceRange` and C-CDA on FHIR; corrects #131's "a missing bound means unknown", which is `Range`'s wording, and the #183 table's keeping a one-bound result as a range |
| unit | FHIR `code` when `system` is UCUM; C-CDA "SHOULD" UCUM; v2 ISO+, case-insensitive; UCUM §6 | `ucumUnit` is the source's exact string, case and `{annotations}` kept, only where the source says it is case-sensitive UCUM (FHIR `system`, C-CDA `@unit` under a Warning shape); `unitText` is the display unit; a unit outside UCUM, and every v2 `OBX-6`, is `unitText` alone. The alternatives: store the annotation-stripped form instead, or both (`ontologies/cascade.shapes.ttl`) | borrowed from FHIR; corrects #183's "a non-UCUM C-CDA unit is a source error" |
| unit IRI | UCUM none; SPHN UCUM classes; QUDT `ucumCode`, dotted | none; a QUDT or SPHN IRI, if ever, is a table beside the string (`ontologies/cascade.shapes.ttl`) | borrowed from UCUM; corrects #131's "no IRIs for units": UCUM defines none, others do |
| value kinds | FHIR `value[x]`; CDA `PQ`, `RTO`, `IVL_PQ`, `CD`, `ST`; openEHR `DV_QUANTITY`, `DV_PROPORTION`, `DV_INTERVAL`, `DV_CODED_TEXT`, `DV_TEXT` | five, the set the three agree on, and one property naming which a result's value is: Quantity (row "number"); Ratio, a numerator and a denominator each a quantity node, a titre `1:64` a ratio with no unit; Range, a low and a high bound, the node shape the reference range row defines, reused; Coded, the answer as a code IRI, as every coded thing here is; Text, what is left, named as text and never matched by value. A value absent for a reason is no kind: it is row 7 of `partial-dates-and-absent-reasons.md` (`ontologies/cascade.shapes.ttl`) | borrowed from FHIR, CDA and openEHR |
| matcher | no standard defines a duplicate; HL7 v2 filler order number and observation id; FHIR `identifier`; C-CDA entry `id`; Particle every field; de Graauw code, value, datetime | four tiers, a new rule list version: (i) a shared business identifier within one organisation joins for certain, first; (ii) same code, same instant, equal value, same unit is a strong join; (iii) same code and instant with a different value, or a value of another kind, is never Same and is a finding for review, coded answers only when of one code system; (iv) same code and instant with units that are not one UCUM unit is a finding for review, not joined, until conversion is in scope; units are one UCUM unit when equal once annotations are dropped and the litre's `l` and `L` are read as one, with any prefix, every other case kept; a different instant never joins, a time with no zone is compared only with another with none, as written, and a day-only time drops to likely, surfaced. Replaces M12's value clause; the four cases become examples in `runtime/matcher.feature`: rule M21 applies tiers (ii), (iii) as R16's finding for review and (iv) as R17's, the day-only drop as R15; rule M22 applies tier (i) as R18, a shared `dct:identifier` of a named system, a shared code and one time, from documents naming one organisation or two judged one (#270) | ours: no standard defines a duplicate; the identifiers are the standards' |
| conversion | ucum-lhc within a dimension; LOINC molar masses | out of scope; a unit that differs goes to review (the matcher's tier iv) (`runtime/matcher.feature`, M21) | waits on UCUM's licence |

## Why

**Two literals, one job each.** (rows "quantity node", "number") A version is named by a hash of its triples (`currency.md`), so two runtimes must
write one lexical form for one state. XSD defines one canonical decimal and Oxigraph prints it whatever it was given
(verified in its code), so `decimalValue` is alike on every runtime, and `writtenValue` is a string no store rewrites,
so the hash over both is deterministic. The decimal compares, sorts and bounds, XSD's rule; the string keeps the
precision FHIR says "should be preserved", and openEHR's decimal places are counted from it. FHIR says `0.010` and
`0.01` differ, v2 and XSD that they do not; with a literal for each answer the pod need not take a side.
`health:resultValue` no longer carries the written form: it is off the node and glues on a comparator (`"<5.7"`).

**A decimal, not a float.** (row "number") FHIR `decimal` and v3 `REAL` admit an exact decimal, and a double turns `0.1` into another
number. An exponent is exact as a plain decimal, so `1.2e3` as `1200` loses only the spelling, which `writtenValue`
keeps.

**Four comparators, because four is what every source agrees on.** (row "comparator") The four are the intersection of FHIR R4, openEHR,
v2, SPHN and OMOP. `=` means the same as none in all three that have it. `~` is openEHR's and an R6 CI build's, with no
tolerance in one and 10% recommended in the other; a value that is "about" something can neither be compared as a
point nor as a bound. `ad` is about dosing and `<>` is v2's alone. A comparator makes the value a bound, which FHIR
says "can never be ignored", so a query testing the number still knows it is a bound.

**One range, and a missing bound is one-sided.** (row "reference range") FHIR's `referenceRange.low` says an omitted bound is "meaningless
(e.g. reference range is <=2.3)": a range with a high only is everything below it, which is how a lab writes `<5.7`.
`Range`'s "not known" is the generic type's, not the reference range's. One typed range is what v2, SPHN and OMOP hold
and what C-CDA on FHIR keeps; FHIR says "most observations only have one generic reference range", and the rest stay in
`health:referenceRange`, so nothing is dropped. A bound carries no comparator because FHIR forbids one and the
inclusivity is the range's.

**The unit as the source wrote it, compared as UCUM says.** (row "unit") UCUM is case-sensitive and its case-insensitive variant is
"incompatible", so a v2 unit, case-insensitive by default, is display text and never `ucumUnit`. Storing the exact
string keeps what the source said; UCUM §6 says annotations carry nothing and a conformant parser discards them, so the
matcher strips them rather than the store, and `{beats}/min` equals `/min` while both strings survive. UCUM also
defines the litre twice, `l` and `L`, `L` being "1 l", both metric so prefixable (§31, Table 5), and says "In the case
sensitive variant the liter is defined both with an upper case 'L' and a lower case 'l'" (https://ucum.org/ucum, read
2026-10-24): `mmol/l` and `mmol/L` are one unit by UCUM's own definitions, so the matcher reads the two symbols as one.
That is not conversion: no factor is applied, and every other case difference is kept, since UCUM is case-sensitive
and `Mmol/L` is another unit.

**No unit IRIs yet.** (row "unit IRI") UCUM defines none. QUDT's codes are dotted, so `mg.dL-1` never string-matches the `mg/dL` labs
send, and `10*3/uL` and `U/L`, among the commonest lab units, are absent (verified, counted). SPHN's classes exist, but
under what permission it republishes UCUM was not found (unverified). An IRI needs a normaliser and a gap table, and a
string needs neither.

**Five kinds, because three standards agree on five.** (row "value kinds") FHIR's `value[x]`, CDA's datatypes and openEHR's `DV_` types
each type a quantity, a ratio, a range, a code and text, so the set is borrowed whole. Deferring four of them left the
matcher half a rule: a titre or a "positive" could never dedupe. The cost is two small node shapes mirroring the
quantity, one kind property, and a matcher rule per kind. The adapter knows a ratio from a quantity because FHIR sends
a `Ratio` and CDA an `RTO`, never by reading `1:64` as text. A range result reuses the reference range row's bounds,
so one shape checks both; a coded answer is an IRI, as every coded thing here is; text is what is left, and two
spellings of one finding are not one value. An absent value is a reason, not a kind: row 7 of
`partial-dates-and-absent-reasons.md`.

**What a same result needs, tiered.** (row "matcher") No standard defines a duplicate, so the rule is ours, its strongest input is
the standards' identifiers, and the rubric's fourth test orders it by how sure each tier is. (i) Within one
organisation a shared business identifier is certain: HL7 v2's filler order number with the observation id, "a
permanent identifier for an order and its associated observations" (quoted in the ruling; not re-read here), FHIR's
`identifier`, C-CDA's entry `id`; it is `republishing-sources.md`'s within-organisation rule, run first. R18 compares
the identifier as the literal #212 made an organisation's, its value typed by its system, which a C-CDA `id` reaches
through HL7's CDA-to-FHIR identifier mapping, so one result in a hospital's FHIR and C-CDA summaries carries one
identifier; one with no system is never compared, since nothing says which of an organisation's systems issued it. It
also asks for one code, as `naming.md` says a judgment does ("share one plus a code"): a source copying an organizer's
accession onto each member would otherwise join a whole panel. And it asks for one clinically relevant time, compared
as tier (ii) compares instants, or one of the two stating none: a source that files serial draws under one accession
would otherwise join every draw of a day, or of a year, into one; a correction keeps its specimen's time, so it still
joins. It does not compare the value, so a correction's second value is not tier (iii)'s finding to be resolved by
hand: the review page leaves a finding of two results R18 joins out when one of the two says it was corrected or
amended (`workflowStatus`), and lists it otherwise, since two channels of one organisation disagreeing on a value
neither marks as a correction is what a person should see. The organisation is an organisation record a record's
documents name as custodian or author; an agent with no record, as Apple Health's export names its author, is no
organisation, and a pull names none, so R18 joins no pulled record, holding them apart while which organisation a
record from a shared server belongs to is open in `republishing-sources.md`. Two organisation records are one only by
a person's judgment of organisations (`cascade:currentlySameOrganization`), never because a join of two servers made
two organisations pulled from them one record, for the same reason.

**The identifier term.** (row "matcher") `dct:identifier`, "an unambiguous reference to the resource within a given context", with
range `rdfs:Literal` and no domain, so a literal typed by its system is one, as #212 writes an organisation's
`org:identifier`. Of a version of a lab result it is a business identifier its source gave the result: a FHIR
`Observation.identifier`'s value typed by its system, a C-CDA observation's `id` as HL7's CDA-to-FHIR identifier
mapping makes it one, a UUID in lower case in both; one with no system is a plain string. Looked at
and failed: `org:identifier`, whose domain `org:Organization` would make a lab result an organisation; `skos:notation`,
a concept's notation within its scheme, not a record's identifier; FHIR RDF's `fhir:identifier` and ADMS's
`adms:identifier`, each a node with a system and a value, where #212 settled one literal; `schema:identifier`, whose
range is a `PropertyValue`, text or a URL; SPHN's `hasSharedIdentifier`, a sameness asserted across providers, not an
identifier a source gave. (ii) Same
code, instant, value and unit is strong. Values are equal by kind: quantities by `decimalValue` through `FILTER(?a =
?b)`, never a shared variable, which joins `"6.8"` and `"6.80"` only on a store that canonicalises (inferred), with
the same comparator or none on both; ratios by both parts; ranges by both bounds; coded by the same IRI; text never.
Units are equal after UCUM's annotations are stripped (§6), the litre's two symbols read as one (§31), other case
kept. A time with no zone, as a C-CDA `TS` may be written, names no moment, so it is compared only with another written
with none, as written; one with a zone and one without never compare. (iii) A different value at the same code and
instant is never Same: a correction should have arrived as a new version, and here it did not, so a person sees it.
Values of two kinds are different values too. Coded answers of two code systems are not, since a rule cannot tell them
from one answer coded twice.
(iv) Units that are not one UCUM unit may not differ in dimension, mmol/L against mg/dL, so the pair goes to review
unjoined until conversion is in scope, as a finding the matcher files, so the review page reads it rather than
comparing every pair of results on each read (0.20 s against 1.30 s for the review question over 3,000 results). A different instant never joins; a result stamped only to the day is compared by day
and drops to likely, surfaced, since two draws in a day are common for inpatients. A changed rule is a new rule list
version, as `naming.md` requires, so the old rule's claims stop counting by derivation.

**Conversion waits.** (row "conversion") Within a dimension it is mechanical, but mass to molar needs a molar mass per LOINC code, and
UCUM's licence forbids derivative works; whether a published LOINC-keyed table is one is a legal question (unverified).

## Alternatives that lost

- **A float or double, as SPHN and OMOP do.** The strongest case: two of the standards the vocabulary cites, and every
  engine compares doubles. A double is not the number a lab reported, and FHIR and v3 admit an exact decimal.
- **The value alone, the written form on `health:resultValue`.** The strongest case: one literal, and the text held
  `"6.80"`. That text is off the node with a comparator glued on, so a page reading precision would parse it.
- **A precision attribute, as openEHR has.** The strongest case: twenty years of practice, and it survives any store.
  The places are counted from `writtenValue`, and a second field to keep in step is a second place to disagree.
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
- **Text only, named as such, for every value but a quantity.** The strongest case: nothing new to build for alpha.
  A titre or a "positive" could then never dedupe, and all three standards already type them.
- **One rule for a same result.** The strongest case: it is today's rule plus units. It treats a certain join and a
  weak one alike, and is silent on one code and instant with two values, the case a person most needs to see.

## Still open

Each with its lean, and the one fact that decides it:

- **Order of landing.** Settled as fallout: #193 landed first, so #131 renames every lab version by its new content.
- **Stripping annotations.** Whether a SPARQL `REPLACE` strips as UCUM's grammar does, a lone annotation being `1`.
- **Conversion.** Out of scope. A reading of UCUM's licence on a LOINC-keyed table.

## What would change our mind

A store every runtime uses keeping a decimal's lexical form would let `decimalValue` carry the written form and retire
`writtenValue`. A value none of the five kinds holds would add a kind. A business identifier found reissued for
another result within one organisation would demote tier (i). Lab sources sending `~` or exclusive reference bounds
would add them. Sources sending several typed ranges a page needs would add a `ReferenceRange` node. QUDT covering the
lab-sent forms, or SPHN's UCUM classes found under an open licence, would make an IRI cheap. A pair the matcher joins
that a person files Different over, or one it keeps apart that a person files Same over, would show a tier wrong.
