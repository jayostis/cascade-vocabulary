# Partial dates, and values absent for a stated reason

Status: ruled, 2026-10-22, from the research on #133 and the owner's rulings of that day; applied by #133, which
writes the terms, shapes, queries and feature rules. Amends the date shapes at
`ontologies/health/v1/health.shapes.ttl:47-50`, `ontologies/clinical/v1/clinical.shapes.ttl:22-25` and
`ontologies/core/v1/core.shapes.ttl:13-15`, and the matcher queries `same-code-and-date.rq` and
`same-code-and-period.rq`. Which revision is current is `currency.md`, which partial dates never meet (row 4). A result
whose value is absent for a reason is row 7, never a value kind of `quantities.md`; row 5 follows that note's row
"number". The adapters'
side is cascade-bridge-adapter-fhir-r4#20 and cascade-bridge-adapter-ccda#35, which make each loss a finding.

## Question

Every clinical source says two things the vocabulary has no place for, so both adapters drop them. A date stated to
the year or the month, "diagnosed in 2019", fits no shape: each accepts only `xsd:date` and `xsd:dateTime`, and
`dateOfBirth` only `xsd:date`. A value absent for a stated reason, "asked, but the patient did not know", "masked",
has no term, so the C-CDA adapter writes it as absent. A pod has no server of record to ask what a missing value
meant, merges records from several sources whose matcher must never treat "2019" as "2019-06-01", and is read
open-world: a triple that is not there says nothing.

## What others do

- **FHIR** `date` is "a date, or partial date (e.g. just year or year + month)", `YYYY`, `YYYY-MM` or `YYYY-MM-DD`;
  `dateTime` adds a time, which "SHALL" carry a zone, and R4's regex requires seconds; `instant` is always to the
  second with a zone (verified). **FHIR RDF** types each value by "inspecting the literal value": `fhir.ttl` puts
  `owl:unionOf ( xsd:dateTime xsd:date xsd:gYear xsd:gYearMonth )` on `fhir:v` (verified); how its `owl:cardinality 1`
  on `fhir:v` fits an element carrying only a data-absent-reason is unverified. **FHIR search** treats every value as
  the range its precision implies: `eq` when the search range "fully contains" the target, `ap` when they overlap
  (verified). `Observation.dataAbsentReason` holds a reason for value[x] only, and obs-6 says it "SHALL only be
  present if Observation.value[x] is not present"; the `data-absent-reason` extension goes on any element; both draw
  on one 15-code CodeSystem, binding extensible (verified). **US Core** omits a min=0 element with no data and gives a
  min=1 one the extension with `unknown` (verified).
- **CDA** TS "can be of variable precision, omitting parts from the right", and a TS promotes to IVL_TS: "200009" is
  "[200009;200010[" (verified). Document and header times "SHALL be precise to at least the day" (verified).
  `@nullFlavor` goes on any element, from v3 NullFlavor: 17 codes in a hierarchy, NP retired, NI "the most general
  exceptional value", ASKU under UNK under NI (verified). **C-CDA** says "if the sender doesn't know if an act
  occurred, the nullFlavor is on the act"; "no known" is `negationInd` (verified). **C-CDA on FHIR** says to convert
  formats and preserve precision, "'20230531' … would become '2023-05-31' in FHIR (not 2023-05-31T00:00:00+00:00)"
  (verified); its own example "202305312205-0500 → 2023-05-31T22:05-05:00" has no seconds, which R4 and XSD both
  require (inferred). Going to CDA, "use a mapped nullFlavor" (verified). HL7's ConceptMap `cm-data-absent-reason-v3`,
  status draft, maps 9 of FHIR's 15 codes as equal; asked-declined, unsupported, as-text, error, not-a-number and
  not-performed have no target, and NI has no FHIR source (verified).
- **openEHR** `Iso8601_date` allows partial forms, `YYYY-MM` or `YYYY`, and "month_unknown implies day_unknown"
  (verified). A missing value is `ELEMENT.null_flavour`, 4 codes (unknown, no information, masked, not applicable),
  with an optional free-text `null_reason`, "'patient refused to tell me'"; on ELEMENT, not on the value (verified).
- **HL7 v2** DTM: "the number of characters populated … specifies the precision" (verified). TS once had a separate
  degree-of-precision component, "retained only for purposes of backward compatibility as of v 2.3" (verified). `""`
  means "the old value should be changed to null", a delete, not "unknown"; OBX-11 status N is "not asked", X
  "results cannot be obtained" (verified).
- **SPHN** splits a birth or death date into `hasYear` 1..1 `xsd:gYear`, `hasMonth` 0..1 and `hasDay` 0..1; its other
  dates are `xsd:dateTime` (verified). It has no absent-reason term (inferred: no match in the 2026.1 schema).
  **OMOP** requires `year_of_birth` and makes month and day optional; `condition_start_date` is a required full date,
  with nothing saying it was imputed (verified); `value_as_concept_id` is NULL when there is no result (verified).
  **CDISC ADaM** pads and flags the level imputed; trial plans impute the 1st, the 15th or 30 June (secondary,
  unverified at CDISC).
- **XSD 1.1** §2.2.3: "the value spaces of primitive datatypes are disjoint … values from different value spaces are
  incomparable", and `gYear`, `gYearMonth` and `date` each denote an interval (verified). **SPARQL 1.1** maps `=` and
  `<` for dates only to `xsd:dateTime`, and "does not define a total ordering of all possible RDF terms" (verified).
  **Oxigraph 0.5.11**, pinned by the suite and by cascade-runtime-js, returns false for `=` across date types, a type
  error for `<`, and orders ORDER BY lexically, so "2019" < "2019-06" < "2019-06-01" (verified, in its code).
  **rdflib 7.6.0** orders incompatible literals "by their datatype URIs", so every `xsd:date` sorts before every
  `xsd:gYear` whatever the year (verified, in its code). Jena: unverified.
- **ISO 8601-1:2019** allows reduced precision such as "1981-04" (secondary sources; the text is paywalled,
  unverified). **EDTF** Level 0 has `1985` and `1985-04`; Level 1 adds `?`, `~`, `%` and `X` digits (verified).
  **DCAT 3** types dates "using the appropriate XML Schema datatype (xsd:gYear, xsd:gYearMonth, xsd:date, or
  xsd:dateTime)" (verified); before it, Cyganiak in 2012 preferred not to, "as it makes the creation of clients
  significantly harder" (verified). **OWL 2 Primer**: a missing fact "may simply be missing (but possibly true)";
  **RDF 1.1 Semantics** makes entailment monotonic (verified). No PROV or W3C idiom for "absent because" was found.
- **Frequency:** no published rate of partial dates or of nullFlavor and dataAbsentReason in real C-CDA or FHIR data
  was found (unverified). USCDI's Date of Onset submission says onset "may sometimes only be available as an estimate
  such as a year or month" (verified); the adapters' fixtures are not real-world data.

Sources: FHIR R4 datatypes (https://hl7.org/fhir/R4/datatypes.html), resource `Meta`
(https://hl7.org/fhir/R4/resource.html), RDF (https://hl7.org/fhir/R4/rdf.html, https://build.fhir.org/rdf.html),
search (https://hl7.org/fhir/R4/search.html), Observation (https://hl7.org/fhir/R4/observation-definitions.html), the
extension (http://hl7.org/fhir/StructureDefinition/data-absent-reason) and its CodeSystem
(http://terminology.hl7.org/CodeSystem/data-absent-reason); v3 NullFlavor
(http://terminology.hl7.org/CodeSystem/v3-NullFlavor); HL7 v3 Data Types abstract
(https://www.oasis-open.org/committees/ubl/lcsc/doc/qateam/Comment%20work%20from%20HL7/datatypes.html); C-CDA on FHIR
mapping guidance (https://hl7.org/fhir/us/ccda/en/mappingGuidance.html); C-CDA general guidance
(http://hl7.org/cda/us/ccda/generalguidance.html); HL7 v2.5.1 (https://www.hl7.eu/HL7v2x/v251/std251/ch02a.html,
https://www.hl7.eu/HL7v2x/v251/std251/ch02.html); EDTF (https://www.loc.gov/standards/datetime/); XSD 1.1 Part 2
(https://www.w3.org/TR/xmlschema11-2/); SPARQL 1.1 (https://www.w3.org/TR/sparql11-query/); DCAT 3
(https://www.w3.org/TR/vocab-dcat-3/) and the GLD thread (https://lists.w3.org/Archives/Public/public-gld-wg/2012Jan/0037.html);
W3CDTF (https://www.w3.org/TR/NOTE-datetime); SPHN (https://www.biomedit.ch/docroot/sphn/latest/sphn_ontology.html);
OMOP CDM 5.4 (https://ohdsi.github.io/CommonDataModel/cdm54.html); USCDI Date of Onset
(https://isp.healthit.gov/uscdi-data/date-onset?page=1); OWL 2 Primer (https://www.w3.org/TR/owl2-primer/). The
research on #133, with the Oxigraph and rdflib code it read
(https://github.com/jayostis/cascade-vocabulary/issues/133#issuecomment-6345860418).

## Choice

Every row is ruled, 2026-10-22. Rows 1 to 5 are partial dates, 6 to 8 absent reasons.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| 1. datatype | FHIR RDF's union; DCAT 3; openEHR's reduced-accuracy string; against: HL7 v2's retired precision component, CDISC's flags, SPHN's and OMOP's parts | one property per date, typed `xsd:gYear`, `xsd:gYearMonth`, `xsd:date` or `xsd:dateTime` by the precision the source wrote, through `sh:or`; nothing padded; `dateOfBirth` takes the same four; rule M23 | borrowed from FHIR RDF, union and all |
| 2. comparison and order | XSD's disjoint value spaces; SPARQL 1.1; Oxigraph 0.5.11; rdflib 7.6.0 | "2019" never equals "2019-06-01", by term or by value, which is the matcher's requirement met by the datatype alone; a query that sorts mixed precisions orders by the written form, `STR()` of the date, so a year sorts before its months and its days on every engine; rule M23 | borrowed from XSD; the sort rule is ours, since SPARQL defines none |
| 3. matching partial to full | FHIR search's implied range, `eq` contains, `ap` overlaps; v3's TS to IVL_TS | `same-code-and-date.rq:11-12` stays term-equal, so a year never joins a day, and from the rule list's version 14 R2 and R4 join only a day or a time written to the second, since two shots dated to one year or one padded hour may be two; `same-code-and-period.rq` reads each bound as the range its type implies, replacing the ten-character string compare at lines 23-31, as `same-code-and-period-read-as-ranges.rq` in the rule list's version 14; rule M23 | borrowed from FHIR search's ranges for periods; term equality for dates is ours |
| 4. the currency ladder | FHIR `meta.lastUpdated`, an `instant`; CDA document `effectiveTime`, at least the day | partial dates never reach `currency.md`'s ladder: no source change time and no `rec:asOf` is a clinical date | borrowed; nothing to decide past saying so |
| 5. hour precision from CDA | C-CDA on FHIR's precision rule; FHIR and XSD `dateTime`, which need seconds; `quantities.md` row "number" | kept, the pattern of `quantities.md`'s decimal: an `xsd:dateTime` padded with zeros to the second (`2023-05-31T14:00:00`), with no timezone where the source gave none, which sorts, compares and falls in a range; and `writtenDate`, a plain string of the characters the source sent (`2023053114`), only where the typed form was padded, below the day; no finding, since nothing is dropped; a padded time is never read as exact, and a query needing the precision reads the string; the string sits on a node of the version naming its property, `cascade:PaddedDateTime`, and from the rule list's version 14 the lab rules R6, R16 and R17 read no padded time as an instant and R15 counts it as a day alone; rule M23 | borrowed from C-CDA on FHIR's precision rule and from `quantities.md` row "number" |
| 6. the reason's code | FHIR data-absent-reason, 15 codes; v3 NullFlavor, 17 in a hierarchy; the draft map, 9 of 15 | one term, `cascade:absentReasonCode`, whose value is exactly the code IRI the source gave, FHIR's (`cascade:DataAbsentReason`) or NullFlavor's (`cascade:NullFlavor`), with no crosswalk at write time; a view that needs one list applies HL7's `cm-data-absent-reason-v3` at read, where it maps, and the source's own term where it does not (NI, and the six FHIR codes it leaves out); the map is a versioned table like the matcher's code tables, cited as used, replaceable when HL7 finishes it; no view needs one list yet, so the table waits for the first that does (Still open) | borrowed from both systems, and from HL7's map, applied at read |
| 7. where it sits | FHIR obs-6 and the extension; CDA `@nullFlavor` anywhere; openEHR ELEMENT; HL7 v2 `""` | on the record's version, naming the property it stands for, and only where that property is absent: `cascade:ValueAbsentForReason`, a node of the version named `<version>#absent-` and the property's local name; a result's absent value is this row, naming `cascade:resultValueKind`, and no value kind of `quantities.md`; v2's `""` is a delete and is never read as a reason | borrowed from obs-6, widened to any property as the extension is |
| 8. negation | C-CDA `negationInd`; US Core | out of scope: "no known allergies" is a statement, not an absent value, and is #152's "no known X" | borrowed from C-CDA's split |

## Why

**Why the union.** Every health standard carries precision in the form as written and none pads: FHIR, CDA and HL7 v2
drop digits from the right, openEHR keeps a reduced-accuracy string, and C-CDA on FHIR says "not
2023-05-31T00:00:00+00:00" (verified). FHIR RDF already writes the union and DCAT 3 does the same, so the vocabulary
adds two types to an `sh:or` that already mixes two incomparable ones, `xsd:date` and `xsd:dateTime`. XSD defines
each type as an interval, so the range FHIR search wants is the literal itself, with no second triple to keep in step.

**Why disjointness is the requirement, not the cost.** #133 asks that the matcher never treat "2019" as "2019-06-01".
Under the union it cannot: XSD makes the values incomparable and Oxigraph 0.5.11 returns false for `=` (verified),
so a term-equal join is safe by construction. The cost is order: SPARQL defines none across types, Oxigraph falls
back to the written form and rdflib to the datatype IRI (verified), so two engines sort one list two ways. A query
that sorts dates says it sorts by the written form, which puts "2019" before "2019-03" before "2019-03-14"; that is
start order with the coarser value first, which a timeline can show as a span.

**Why the period query changes.** `same-code-and-period.rq:23-31` takes `SUBSTR(STR(?onset), 1, 10)` as a string and
admits an abatement only if it is `xsd:date` or `xsd:dateTime`. With a year onset "2019" the rules as written give an
active condition the period "2019" to "9999-12-31", which overlaps a 2019-06-01 onset, while an inactive one does not
match, since "2019-06-01" <= "2019" is false, and a `gYear` abatement counts as none (inferred, not run). The same
pair matching or not by status is a bug the union exposes; reading a year as 1 January to 31 December, as FHIR search
and v3's IVL_TS do (verified), fixes it.

**Why the ladder never meets them.** `currency.md` ranks by source change time, then `rec:asOf`. FHIR's change time
is `Meta.lastUpdated`, an `instant`; a C-CDA document's `effectiveTime` "SHALL be precise to at least the day"; and
`rec:asOf` is an exporter's stamp or a device clock (verified). A partial date is a clinical date and is on a version,
never a clock (inferred). The ladder has its own mix, a day-precision C-CDA `effectiveTime` beside a FHIR `instant`,
which Oxigraph cannot order with `<`; that is `currency.md`'s to note, not this note's.

**Why pad the hour, and keep what was sent.** A CDA time to the hour has no FHIR or XSD form short of padding the
minutes and seconds (inferred), so it follows `quantities.md` row "number": a typed literal that does the typed jobs
and a plain string that keeps the source's characters. Padded to the second, `2023-05-31T14:00:00` sorts, compares and
falls in a range as every other `xsd:dateTime` does, where keeping only the day, as the C-CDA adapter does today
(`in/sparql/result.rq:319-322`), dropped the hour. XSD allows a `dateTime` with no timezone, and a source that gave
none gets none, since inventing one would be a lie. The padding is the risk the standards guard against, so the padded
literal is never read as "at 14:00:00 exactly": `writtenDate` holds `2023053114`, the precision is recoverable from it,
and a query that needs the precision reads it. It is written only where the adapter padded, which the adapter knows;
a year, a month or a day carries its precision in its own type (row 1), so this is the separate written property that
lost for row 1, used only where no typed form holds the precision. Nothing is dropped, so no finding is written. How
often a source sends hours is not counted (unverified).

**Why the source's own code, and HL7's map at read.** The draft map covers 9 of FHIR's 15 codes, and NI, CDA's default
and the most general code, has no FHIR counterpart (verified). Mapping at write time would invent a counterpart for NI
or drop it, and the adapter would then be stating HL7's draft as fact, so the version stores exactly the IRI the
source gave. A view that needs one list, as the review page does, applies `cm-data-absent-reason-v3` at read where it
maps and shows the source's own term where it does not. The map is a table like the code tables the matcher reads,
versioned and cited as used, so a view says which map it applied; when HL7 finishes it, the table is replaced and every
view improves without touching a record. Nothing is lost and nothing invented.

**Why on the version, beside the property.** Open-world RDF makes a missing triple say nothing (verified), so only a
written term can say "absent because", and no PROV or W3C term does (none found). FHIR's obs-6 already gives the shape:
a reason only where the value is absent. Putting it on the version keeps the vocabulary's rule that content is on a
version, and naming the property says which absence it explains, as CDA's attribute does by sitting on the element.
HL7 v2's `""` means "the old value should be changed to null" (verified), so an adapter reading it as a reason would
turn a delete into a statement.

## Alternatives that lost

- **A precision term beside a padded date.** The strongest case: every date sorts and compares, with one datatype and
  no union for clients to handle, which is Cyganiak's objection met. Every query that forgets the precision term
  equates a padded "2019-01-01" with a real 1 January, the error #133 forbids; HL7 v2 retired exactly this in v2.3,
  and FHIR and C-CDA on FHIR say not to pad (verified).
- **A separate property for the date as written.** The strongest case: SPHN does it for birth and death, and the typed
  property stays a full date that every engine orders. A record with only a year then has no date at all to sort or
  match, every query reads two properties, and no health standard carries an event date this way (verified).
- **A plain string of the date as written.** The strongest case: nothing is lost, and the written form is the
  precision. A string is not a date to any engine, the shapes reject it, and a `"2019"^^xsd:string` sorts beside
  "abc"; the union keeps the written form and types it.
- **Imputation to the 1st or the 15th.** The strongest case: trial practice and OMOP's full event dates, and every
  date is comparable. It invents a day that the matcher then joins on, and the flag CDISC adds is option b again; no
  OMOP rule for it was found (unverified).
- **NullFlavor as the only set.** The strongest case: 17 codes in an explicit hierarchy, and CDA, the larger source,
  sends it unchanged. FHIR's asked-declined, not-performed, as-text and error have no NullFlavor target, and the map
  that would carry the rest is a draft (verified).
- **A finding only.** The strongest case: OMOP leaves the field NULL, SPHN has no term, US Core omits a min=0 element,
  and a finding already says what was dropped. A finding is on the act, so a view of the record cannot show "masked"
  beside the missing value, and "never sent", "dropped" and "absent because" become one graph.
- **Refusing the hour with a finding, keeping the day.** The strongest case: no padded value ever lies. The hour is
  then lost, though a string holds it at no risk, and a finding stands for something that need not have been dropped.
- **Padding the hour with a flag, as CDISC does.** The strongest case: a flag is queryable. The string is the flag and
  more: its presence says the time was padded, and its characters say to what precision.
- **Mapping the reason at write time.** The strongest case: one list in the pod. It writes HL7's draft into every
  record as fact, and invents or drops a counterpart for NI and the six FHIR codes the map leaves out.
- **The source's code, never aligned.** The strongest case: no draft map in or near the pod. The review page then
  shows two lists for one question, and the map applied at read leaves every record as the source wrote it.

## Settled while applying it

By #133, 2026-10-24, under the owner's delegation (jayostis/cascade-vocabulary#204):

- **The reason term's name and namespace.** Everything is in `cascade#`. The reason is a node of the version,
  `cascade:ValueAbsentForReason`, named `<version>#absent-` and the local name of the property it stands for, as a
  quantity is a node named by its role: `cascade:absentValueProperty` names the property, and `cascade:absentReasonCode`
  holds one code IRI for each coding the source gave, so a source that gives two reasons for one property loses
  neither. A node, not a property per absent property, since any property may be absent.
- **Which date a `writtenDate` belongs to.** A medication's start and end and a condition's onset and abatement can each
  be written to the hour in C-CDA, so a version can carry two dates below the day: the string sits on a node,
  `cascade:PaddedDateTime`, named `<version>#padded-` and its property's local name, which `cascade:paddedDateTimeProperty`
  names.
- **The codes' IRIs.** HL7 Terminology registers no IRI stem for `data-absent-reason` or `v3-NullFlavor` (UTG at
  `05d22fc`: `grep -rl iri-stem` finds LOINC and MeSH only), and Bioregistry's `hl7.v3codesystem` names a code
  system, not a code, so neither passes `code-iris.md`'s rubric; both are in Cascade's own space,
  `https://ns.cascadeprotocol.org/codes/data-absent-reason/` and `.../codes/nullflavor/`, each code as its system
  writes it, and the shapes list exactly the codes of HL7's CodeSystems (15 and 17, NP retired but kept, since a source
  may still send it).
- **Which properties a reason may stand for.** The nine date properties and a lab result's `cascade:resultValueKind`,
  the ones an adapter writes a reason for, listed by `cascade:absentValueProperty`'s shape; a property is added with the
  first adapter that writes a reason for it.
- **A padded time in a view.** A view copies each padded time it shows with its node, so no view shows one as exact;
  the node is named after its holder, the entry or a member's values, `-padded-` and the local name, since a view
  entry's IRI has its fragment already (`naming.md`, row "view entry").
- **A variant interpretation's date.** `cascade:interpretedDate` takes `xsd:gYear`, `xsd:gYearMonth` or `xsd:date`: the
  day the interpretation was issued, as before, or its year or month where the source wrote no day. A time still gives
  its day, since the property is a date.
- **Two immunizations of one year.** Term equality keeps a year from joining a day, but two shots dated "2019" are
  term-equal and may be two shots, as may two at one padded hour: R2 and R4 read only a day or a time written to the
  second from the rule list's version 14.

## Still open

Each with the lean and the one fact that decides it:

- How often partial dates, hours and absent reasons occur in real FHIR and C-CDA data. Unmeasured (unverified); rows 1,
  5 and 7 rest on the standards, not on counts.
- The view that first needs one list of reasons, and so HL7's map as a table (row 6). Lean: the review page, when it
  lists a result with no value. Decides it: a view that shows the reason.
- Which date an entry shows when a newer member gives a coarser date than an older one: the member a date comes from
  is chosen by currency (`currency.md`), so a newer "2019" replaces an older "2019-06-14" in the entry's display. Lean:
  prefer the finer when it falls inside the coarser, since both say the same and one says more. Decides it: a view or a
  story where a source sends a coarser date after a finer one.

## What would change our mind

A measurement, none of which exists (unverified): partial dates rare enough in real FHIR and C-CDA data that a
finding is cheaper than a union every client must handle would favour Cyganiak's case; absent reasons rare enough
would favour a finding only. A health standard or FHIR RDF moving to a precision term would reopen row 1. HL7
publishing the crosswalk as final, with NI mapped, would favour mapping at write time. An engine the runtime adopts
that orders across date types would let the sort rule follow it. A query or view found reading a padded time as exact
would reopen row 5.
