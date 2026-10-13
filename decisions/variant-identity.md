# When two variant records are one variant

Status: draft, 2026-10-13. Rules: R12 `jdg:SameVariation`, R13 `jdg:SameVariationThroughTable`; rule M17.

## Question

Two reports can name one variant on two transcript versions, one with a ClinVar ID and one without. Which codes join them,
and which joins would be wrong?

## What others do

- **GA4GH VRS** gives one variant one digest from any source, set aside here (see `variant-record.md`).
- **FHIR's Variant** carries a variation code and a c.HGVS description and says nothing about when two Variants are one.
- **ClinVar** keys a variation by its VariationID, and `hgvs4variation` lists the expressions that map to it.
- **openEHR** keeps the HGVS string as identity. **OMOP** matches HGVS strings against concept names and synonyms.

## Choice

- **R12** joins two variants whose current versions carry one ClinVar VariationID.
- **R13** joins two variants whose current versions find one row of one version of a variant classifications table. A
  version that carries a VariationID finds the row of that variation, and only that row: its expression is not read. A
  version with none finds the row that holds its expression, percent-encoded. The classification plays no part.
- **Left alone:** a pair that shares an ID (R12's, so no pair has two justifications); a pair whose versions carry
  different IDs, whatever expressions they hold; a version whose expression is on more than one row, rows counted as
  distinct row subjects over every held version of every series of the kind; a version whose ID is on no row.

## Why

An HGVS expression names a transcript version, so two expressions are two strings and nothing in the pod says they are one
variant; only a table does, by listing both under one VariationID. An ID is a stronger claim than an expression, so a
version that carries one is read by it alone: otherwise a report carrying ID 12345 and an expression of another variation
would join that variation's records. Counting distinct row subjects, as `same-product-code.rq` counts, keeps two series
that both hold a variation from leaving every pair alone.

## Alternatives that lost

- **Join any two records that share an expression.** The strongest case: it needs no table. An expression is not unique
  across variations (195 of 3,304,067 submitted coding expressions in the 2026-10 snapshot map to two VariationIDs), and
  sameness is a claim the pod should make from a table that says so.
- **Read both the ID and the expression.** It would join more pairs. A pair of different IDs would join through one's
  expression, against what the IDs say.
- **A string distance between expressions.** The brief's rule is no fuzzy matches; weaker overlaps go to a person.

## What would change our mind

A table that lists IDs for expressions it does not hold as rows, or a source that states an expression and its ID
inconsistently often enough to matter.
