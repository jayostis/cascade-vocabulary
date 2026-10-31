# Medications: each copy's own lifecycle, and how long it was taken

Status: draft, 2026-10-29, written with #292 (phase 1 of #287), which applies it; #299 adds a request's supply, its dosage's bounds and its dispensing window (rows "exposure start", "exposure end", "a supply"); #300 adds a pharmacy's dispense (rows "a dispense", "a dispense's prescription", "a dispense's lifecycle"). Acceptance waits on the departures: rows "exposure start", "exposure end", "no end", "a partial date" and "a supply". Depends on `version-content.md`
(row "what rules read": rules read each member's own version and a small layer of derivations that defines exposure as
`CumulativeMedicationDuration` does), `clinical-terms-follow-fhir.md` (a departure from FHIR is explained in its area's
note, and this is the medications area's), `one-meaning-per-term.md` (the lifecycle classes, rule L1) and
`partial-dates-and-absent-reasons.md` (the four date types a source date may take). The medication matching rules M15
and M16, which decide which copies are one entry, still need their own note (#286).

## Question

"You have taken metformin for two years" is a question about how long a medication was taken, and a pod holds that
medication as several copies, one per source and per course, joined into one entry. A rule that reads the entry reads
one copy's dates and one copy's status: the entry shows its latest arrival's. The experiment on #288 (comment 3, cases
c3c and c7b0) found both failures. A brand copy a second hospital first recorded in 2025, arriving after the generic
the first hospital had recorded since 2022, gave the entry a 2025 start and shortened the exposure by three years (c3c).
A course from 2019 to 2021 joined with a course started in 2026 lost the first course entirely (c7b0). And a copy with
no end date borrowed the entry's status, so a stopped copy in an active entry read as still taken. The pod has no server
of record to say which copy is right; each copy is what one source said, and a rule must read each.

## What others do

- **The CMS eCQM library `CumulativeMedicationDuration`** (4.1.000, in cqframework's `ecqm-content-qicore-2024`) is
  the community's definition of a medication's period, used by the CMS FHIR measures. `MedicationRequestPeriod` starts
  a request's period at "Coalesce(date from start of boundsPeriod, date from R.authoredOn, date from start of
  R.dispenseRequest.validityPeriod)", runs it for "Coalesce(daysSupply, quantity.value / (dose.value * dosesPerDay)) *
  (1 + refills)" days, or else to "date from end of boundsPeriod", "else null" (verified). A dispense's period runs from
  `Coalesce(whenHandedOver, whenPrepared)` for its days' supply. An administration's would need a "therapeutic duration … this logic is
  incomplete and should not be used" (verified). The library has **no function for `MedicationStatement`** (verified, in
  4.1.000 and 3.3.000), and says "MedicationRequest status is not considered by this calculation, as the list … should
  already have considered appropriate statuses" (verified). Combining periods is a separate step: `CumulativeDuration`
  "collapses" overlapping intervals, `RolloutIntervals` lays them "end-to-end" (verified). Its periods are
  `Interval<Date>`, closed at both ends (verified).
- **FHIR R4** `MedicationStatement.effective[x]` is "The interval of time during which it is being asserted that the
  patient is/was/will be taking the medication"; `MedicationRequest.authoredOn` is "The date (and perhaps time) when
  the prescription was initially written" (verified, as quoted in `one-meaning-per-term.md`). R4's MedicationRequest has
  no `effective[x]`; R5 adds `effectiveDosePeriod` (`one-meaning-per-term.md`). FHIR's `date` and `dateTime` may stop at
  the year or month (`partial-dates-and-absent-reasons.md`).
- **C-CDA** carries a Medication Activity's period in its first `effectiveTime`, `low` and `high`; both adapters fill
  `cascade:medicationUseStartDate` and `cascade:medicationUseEndDate` from these and from `effective[x]`
  (`cascade-bridge-adapter-ccda/in/sparql/medication.rq:124-158`, `cascade-bridge-adapter-fhir-r4/in/sparql/medication.rq:166-185`;
  verified).
- **OMOP CDM 5.4** requires `drug_exposure_end_date`: "If this information is not explicitly available in the data,
  infer the end date from start date and duration", from days' supply for pharmacy data; eras then merge exposures with
  "A standard Persistence Window of 30 days" (verified). OMOP imputes an end; it keeps the exposure and the era apart.
- **PROV-O and PAV** say nothing about exposure; a derived value written on the record follows the derivations' rule in
  #287's settlements (S8): on the record, never the version, never the entry.

Sources: CumulativeMedicationDuration 4.1.000
(https://github.com/cqframework/ecqm-content-qicore-2024/blob/07c68e5e76d96d167627469f0face771c702023f/input/cql/CumulativeMedicationDuration.cql)
and 3.3.000 (https://github.com/cqframework/ecqm-content-qicore-2023/blob/da1a856e10a7ed96236009ee65840c64bc16b076/input/cql/CumulativeMedicationDuration.cql);
FHIR R4 MedicationStatement (https://hl7.org/fhir/R4/medicationstatement-definitions.html#MedicationStatement.effective_x_)
and MedicationRequest (https://hl7.org/fhir/R4/medicationrequest-definitions.html#MedicationRequest.authoredOn); OMOP
CDM 5.4 (https://ohdsi.github.io/CommonDataModel/cdm54.html); the experiment
(https://github.com/jayostis/cascade-vocabulary/issues/288, comment 3).

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| a copy's own lifecycle | FHIR's status on each resource; `one-meaning-per-term.md`'s classes | each medication record in an entry is classed by L1 from its own current version's status (`cascade:currentVersionStatusLifecycle` and its step), and the entry has the class of the member it takes its status from, or unknown where none gives one, so L1's table is written once; a rule reads the copy's class, never the entry's; rule L1 | ours, as the lifecycle is (`clinical-terms-follow-fhir.md`, row "a departure") |
| exposure start | CMD: start of `boundsPeriod`, else `authoredOn`, else start of `dispenseRequest.validityPeriod`, of the request's `singleton from` dosage; FHIR `MedicationStatement.effective[x]` | the start of use (`effective[x]`, C-CDA `effectiveTime/low`), else the start of the bounds of the version's one structured dosage (`cascade:dosageBoundsPeriodStart`), else the day the prescription was written (`authoredOn`), else the start of its dispensing window (`cascade:dispenseValidityPeriodStart`); a version with several dosages is read from these without any dosage's bounds; `cascade:medicationExposureStart` (`queries/derivations/medication-exposure-periods.rq`) | borrowed from CMD's request start; diverged for a version with several dosages, where CQL's `singleton from` over more than one element is a run-time error and CMD gives no period: we read its start and its supply as for one dosage and leave out only the bounds, which belong to one dosage each; a statement's start is FHIR's, since CMD has no statement function |
| exposure end | CMD: start plus days' supply times one plus refills, less one day, or the end of `boundsPeriod`; FHIR `effective[x]` | the end of use (`effective[x]`, C-CDA `effectiveTime/high`), else the start plus the supply (`cascade:expectedSupplyDuration`) times one plus the repeats (`cascade:numberOfRepeatsAllowed`, none stated read as 0), less one day, else the end of the one dosage's bounds (`cascade:dosageBoundsPeriodEnd`); a dispensing window's end is never an end; a dispense's days' supply is not read here (row "a dispense"); `cascade:medicationExposureEnd` (`queries/derivations/medication-exposure-periods.rq`) | borrowed; diverged where a request states an end of use as well, which no FHIR request does, and for a version with several dosages, as in row "exposure start" |
| a supply | CMD: `convert expectedSupplyDuration to days`, else `quantity.value / (dose.value * dosesPerDay)`, and `startDate + Quantity(totalDaysSupplied - 1, 'day')`, where CQL ignores the decimal portion of a quantity of days; UCUM's units of time; FHIR Duration drt-1; Timing's UnitsOfTime | the supply in one of the seven codes of Timing's UnitsOfTime, read in days (a week 7, a month 30.4375, a year 365.25, UCUM's mean Julian month and year), times one plus the repeats, rounded down to whole days, counted from the first day the start may be; a supply under a day ends on its start; a supply with a comparator, or with no UCUM unit, is not read; a supply from the quantity dispensed and the dose is not computed (`queries/derivations/medication-exposure-periods.rq`; `ontologies/cascade.shapes.ttl`, `DurationQuantityShape`) | borrowed from CMD's arithmetic, its rounding and its end for a supply under a day among it; diverged in counting from the earliest start, so exposure is never overstated, and in leaving out the quantity's fallback, whose quantity term is not carried |
| no end | CMD: null; OMOP: an imputed end | with no end, `cascade:medicationExposureOngoing true` when the copy's own lifecycle is active, and neither an end nor the flag otherwise (`queries/derivations/medication-exposure-periods.rq`) | diverged: CMD measures closed periods inside a measurement period, a pod asks about today, and an active status says the period has not closed, known through the current revision's `cascade:observedAsOf` |
| a partial date | `partial-dates-and-absent-reasons.md` row "1. datatype"; CMD's `date from` | a start given to the year or month is its last day, an end its first, and a time its day, so exposure is never overstated (`queries/derivations/medication-exposure-periods.rq`) | borrowed from FHIR search's implied range (as row 3 of `partial-dates-and-absent-reasons.md` does; `queries/matcher/same-code-and-period-read-as-ranges.rq`), taking the range's inner edge; diverged from reading the day a source gave: CQL's `date from` keeps the source's precision, so a year stays a year |
| no period | CMD: "else null"; CQL's interval needs its low at or before its high | a copy with no start, or whose end so read falls before its start, has no exposure (`queries/derivations/medication-exposure-periods.rq`) | borrowed |
| no collapse | CMD's `CumulativeDuration` and `RolloutIntervals`; OMOP's eras | the derivation writes each copy's period and never combines them: collapsing or rolling out over an entry's members is the rule's, #287 phase 3 | borrowed from CMD's split between a period and a cumulative duration |
| the derived dates' type | CMD's `Interval<Date>` | `xsd:date` only, never the partial-date union, which is for dates a source wrote (`ontologies/cascade.ttl`) | borrowed |
| a dispense | FHIR R4 `MedicationDispense`, US Core 6.1.0's profile (Must Support: `status`, `medication[x]`, `authorizingPrescription`, `quantity`, `whenHandedOver`, `type`, `performer.actor`, `dosageInstruction`); CMD's dispense period from `Coalesce(whenHandedOver, whenPrepared)` for its `daysSupply` | a record of its own kind, `cascade:MedicationDispense` ("Medication dispense"), filed under `records/medication-dispenses/` with a view of its own (`queries/views/medication-dispenses.rq`); its drug in the medication's own drug terms (`cascade:drugName`, `rxNormCode`, `ndcCode`, `medicationCodeInOtherSystem`, `userSelectedCode`), its status in `cascade:workflowStatus`, and `cascade:dispensePreparedTime`, `cascade:dispenseHandedOverTime`, `cascade:dispenseQuantity` and `cascade:dispenseDaysSupply` (`<version>#dispense-days-supply`, a UCUM unit of time); dated by the time it was handed over, else prepared (`queries/derivations/records.rq`); left out at source when entered in error | borrowed: FHIR's split of a request from its supply (the maintainer's ruling on Q2, 2026-10-31, [#300](https://github.com/jayostis/cascade-vocabulary/issues/300#issuecomment-6540381251)); `type`, `performer` beyond the record's attribution, and `dosageInstruction` are not carried yet |
| a dispense's prescription | FHIR `MedicationDispense.authorizingPrescription`, a reference to a `MedicationRequest` | `cascade:authorizingPrescription`, the prescription's medication record by its IRI, one per reference; the view names that record's medications entry; no matcher rule joins a dispense to anything, since kinds never join (`tests/fixtures/kinds-never-join`) and, under the M15/M16 ruling, records join only on periods with no gap, which monthly fills are not | borrowed |
| a dispense's lifecycle | FHIR R4 `MedicationDispense.status` (required binding, nine codes) | each dispense in an entry is classed by its own current version's status (`cascade:currentVersionStatusLifecycle`), and the entry by the member it takes its status from, into `cascade:MedicationDispenseLifecycle`: completed; in progress (preparation, in-progress, on-hold); not completed (cancelled, declined, stopped); entered-in-error; unknown (unknown, absent, anything else); rule L2, `queries/derivations/medication-dispense-lifecycles.rq`. L1's table is never read for a dispense, so a completed fill is never a stopped medication and ends no course | ours, as L1 is (`clinical-terms-follow-fhir.md`, row "a departure"): the classes group FHIR's codes; stopped, which FHIR says halted "before all of them occurred", is not completed, so a part-fill is never read as received |

## Why

**Why intent is the rule's.** (rows "exposure start", "exposure end") The derivation reads what the copy states. A
rule filters `cascade:medicationRequestIntent` (a proposal or a plan is not an order) and status, as CMD's callers do
with the list they hand it ("MedicationRequest status is not considered by this calculation").

**Why the copy's own status.** (row "a copy's own lifecycle") An entry takes its status from one member, the latest
that states one (`queries/derivations/status-sources.rq`). That answers "is it still taken" for the entry, and nothing
about the other copies: a copy completed in 2021 is stopped whatever a 2026 copy says. A rule that read the entry's
class for every member would extend the 2021 course to today. Classing every record with the same L1 table, and giving
the entry its status member's class, keeps one table and one meaning; a second table for records would drift.

**Why CMD's definition.** (rows "exposure start", "exposure end", "no period") CMD is what the CMS FHIR measures run,
so a rule built on it counts exposure as a quality measure does, and a reviewer can check it against published logic.
A request's start falls back from its one dosage's bounds to `authoredOn` and then to its dispensing window exactly as
CMD's does, and with no end of use its end is CMD's supply end, else its bounds' end. A version with several dosages
is a departure: CQL's `singleton from` over more than one element is a run-time error, so CMD gives such a request no
period at all. A taper or a split dose states several dosages and was still written on a day and supplied for a time,
so its start and supply end are read as for any request; only the dosages' bounds are left out, since each belongs to
one dosage and none is the request's. Where CMD has no answer, a statement, FHIR's own definition of
`effective[x]` is the period, the same element CMD would read if it had the function.

**Why an ongoing flag and not an end.** (row "no end") A rule asking "taken for two years" needs to know a period runs
to today, and CMD's null would drop every current medication with no supply data, which is most of US Core's
(`version-content.md`, row 4). Writing today as the end would make derived state change each day with nothing new in
the pod. A flag on the copy says the period is open. It is known only through the current revision's `cascade:observedAsOf`,
the last instant a source said the copy was active, so a rule closes the period at the earlier of that and the day it
asks, never at the day it asks alone. The flag is never written false; absent means not known. It is written only for
an active copy: a copy with no end that is stopped, paused or unknown is not known to have lasted past its start, so
neither an end nor a flag is written, and a rule cannot overstate it.

**Why the supply is read as it is.** (row "a supply") CMD converts the supply to days and adds days to a date, so a
supply in weeks, months or years is read in days by UCUM's own definitions of its units of time; FHIR's Duration must
be a UCUM expression of time (drt-1), and the seven read are the codes of Timing's UnitsOfTime. A fraction of a day is
dropped, as CQL drops it when it adds days to a date, since adding it would end the period on a day no supply reaches;
a supply under a day so ends on its start, the one day it covers. The
supply is counted from the first day the start may be: a prescription written in "April 2025" with 60 days' supply ran
out by 30 May at the latest, and counting from 30 April would credit a month no supply covered. A comparator makes the
supply a bound, which says nothing certain about its length in the direction that matters, and a supply with no UCUM
unit cannot be converted, so neither is read. CMD's other supply, the quantity dispensed over the daily dose, needs
`dispenseRequest.quantity`, which no term carries yet. A supply end is an inner bound, as a partial date's is: the
supply covers the days to it, and an order may be renewed, or the medication taken from another supply, after it. With
a supply end an active order is not flagged ongoing, so a rule asking how long it was taken never counts past it; a rule
asking about absence reads the copy's lifecycle and its current revision's `cascade:observedAsOf`, never a
supply-capped end.

**Why the conservative bounds.** (row "a partial date") A start written "2022" may be any day of 2022; reading it as
1 January would credit up to a year of exposure no source stated, and a rule asking "at least two years" would fire on
a guess. Reading the start as the last day and the end as the first gives the shortest period the source allows: these are the
dates the medication was certainly taken, the inner bounds, and a supply end is one too (row "a supply"). So a rule
asking about absence ("no statin") must not read missing exposure triples, or an end before today, as "not taken": a
course stated within one month or one year can have no exposure, and a supply runs out while the order stays active. It
reads the copy's own lifecycle and its `cascade:observedAsOf` instead. A time is
read as its day in its own zone, as CMD's `date from` does.

**Why no collapse here.** (row "no collapse") Two copies of one course overlap and two courses of one entry do not;
whether to collapse, roll out or count each is the question a rule asks, with a gap it chooses, as OMOP's era does with
30 days. Collapsing in the derivation would decide it for every rule and lose the copies a rule may need to cite.

**Why `xsd:date`.** (row "the derived dates' type") The conservative bounds turn every partial date into a day, so a
derived period is always to the day, and one type compares on every engine (`partial-dates-and-absent-reasons.md`, row
"2. comparison and order").

**Why a dispense is its own kind.** (rows "a dispense", "a dispense's prescription", "a dispense's lifecycle") FHIR
keeps the order (`MedicationRequest`), the person's account (`MedicationStatement`) and the pharmacy's supply
(`MedicationDispense`) apart, and a dispense's statuses mean the supply, not the course: its `completed` is "The
dispensed product has been picked up" (R4 CodeSystem medicationdispense-status). Read through L1, every filled
prescription's fills would read as stopped and end the course (`tests/fixtures/a-completed-dispense-neither-stops-nor-ends-its-prescription`).
A fill names its order, so it reaches its course by that reference, not by the matcher, which joins no records across
a gap in their periods and none of two kinds.

## Alternatives that lost

- **A dispense as a third `prescribedOrReported` value, `"dispensed"`, in the medication kind.** The strongest case:
  one view, and the NDC and product-code rules already join a fill to its prescription. It lost on the maintainer's
  ruling on Q2 (2026-10-31): L1 reads a dispense's `completed` as stopped, so every filled prescription's fills would end
  their course, and monthly fills are short periods the matcher, after the M15/M16 ruling, keeps apart.
- **Exposure on the entry, collapsed across its members.** The strongest case: one period per medication is what a
  person means, and a rule would read one triple. It lost because it decides the rule's question in the derivation, and
  because the entry's members are decided by the matcher, whose rules for medications (M15, M16) are still open (#286):
  a wrong join would be baked into the period.
- **Imputing an end as OMOP does.** The strongest case: every period is closed and every rule computes a duration the
  same way. It lost because an end beyond what the copy states, its end of use, its supply or its dosage's bounds, is a
  guess a person cannot see in any source; the supply end is CMD's and the source's own figures.
- **The earliest possible start (1 January for "2022").** The strongest case: it is what a person usually means by
  "since 2022". It lost because it overstates exposure, and a question raised on overstated exposure is a false one.
  The same bounds understate it for a rule about absence, which therefore never reads their silence as "not taken".

## Still open

- A fill's own period, CMD's `Coalesce(whenHandedOver, whenPrepared)` for its days' supply: #300 carries both and its prescription, and derives no period. Lean: phase 3's rule reads a completed dispense's period beside its prescription's, through `cascade:authorizingPrescription`, and a derivation is written once a second rule needs it.
- A C-CDA Medication Dispense (`4.18`), and FHIR's `type`, `dosageInstruction` and `performer` on a dispense. Lean: carried when a source in the kits sends them.
- A supply computed from `dispenseRequest.quantity` and the dose, CMD's fallback. Lean: carry the quantity when a rule
  needs it; until then a request with a quantity and no supply has no supply end.
- An active copy with an end in the future: the end is written as stated and no flag. Lean: the rule reads the earlier
  of the end and the day it asks.
- A stale active order with only `authoredOn`, no end and no supply: its flag runs only to its `observedAsOf`. One with
  a supply is capped at the supply's end (#299, row "a supply"). Lean: the `observedAsOf` bound stands, and a rule
  never reads `cascade:courseOfTherapyType` "continuous" as extending it past that.
- Whether reported use counts as exposure is phase 3's rule's (#287).

## What would change our mind

- A CMD release with a `MedicationStatement` function that reads `effective[x]` otherwise than as its period.
- Evidence that sources write a year or month start meaning its first day often enough that the conservative bound
  misses most long-term use.
- A rule that needs the entry's collapsed period often enough that each rule's own collapse is repeated work worth a
  derivation.
