# What a judgment is, and what it borrows

Status: placeholder, 2026-10-21, opened from the review on #130. Records what `ontologies/judgments/v1-draft/judgments.ttl`
already is, against the vocabularies it could have reused, so that the rubric's second and fourth tests in `naming.md`
have a note behind them. Nothing here is decided beyond what the ontology states today; the open questions are listed
at the end.

## Question

A pod holds beliefs past what any source defines: that two records are one fact, that two servers are one hospital,
that a record is wrong, that a source's patient is this person, that one revision precedes another. A person makes
some and the matcher makes most. Is there a vocabulary for such a belief, with its verdict, its maker, its reason,
its confidence and its retraction, or does the pod define one?

## What others do

- **OWL** `owl:sameAs` and `owl:differentFrom` state logical identity: a reasoner merges whatever they touch, nobody is
  recorded as having said so, and there is no retraction.
- **SSSOM** records a mapping as a row with a predicate, a `mapping_justification` from **SEMAPV**, an author, and a
  `confidence`; built for terms in ontologies.
- **Nanopublications** carry an assertion graph, a provenance graph and a publication-info graph, and retract one with
  `npx:retracts`, whose domain is an agent.
- **PROV-O** gives the parts: `prov:Collection` with `prov:hadMember`, `prov:Person` and `prov:SoftwareAgent`,
  `prov:Activity`, `prov:wasAttributedTo`, `prov:invalidated`; and `prov:alternateOf`, "two entities present aspects
  of the same thing", which is weaker than a verdict.
- **FHIR** `Linkage` lists resources that "refer to the same real-world occurrence", `Patient.link` merges patients;
  neither carries a maker beyond the server, a reason, or a retraction.
- **skos** `exactMatch` and `closeMatch` relate concepts, and the pod uses them for codes, not records.

Sources: OWL 2 (https://www.w3.org/TR/owl2-syntax/#Individual_Equality); SSSOM
(https://mapping-commons.github.io/sssom/spec-model/) and SEMAPV (https://w3id.org/semapv); nanopublication guidelines
(https://nanopub.net/guidelines/working_draft/) and `npx:retracts` (http://purl.org/nanopub/x/retracts); PROV-O
(https://www.w3.org/TR/prov-o/); FHIR `Linkage` (https://hl7.org/fhir/R4/linkage.html), `Patient.link`
(https://hl7.org/fhir/R4/patient.html#links); SKOS (https://www.w3.org/TR/skos-reference/#mapping).

## What the ontology is today

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| judgment | nanopub assertion; SSSOM row | `jdg:Judgment`, a `prov:Collection` whose `prov:hadMember` are the records; one verdict | borrowed from PROV; the verdict is ours |
| maker | PROV agents | `prov:wasAttributedTo` a `prov:Person` or `prov:SoftwareAgent` | borrowed |
| verdict | `owl:sameAs`; `Linkage`; `Patient.link` | `jdg:Same`, `jdg:Different`, `jdg:Erroneous`, `jdg:About`; a Before is proposed in `currency.md` | ours: a belief with a maker, not an axiom, and Different wins over Same |
| judgment over a source-level thing | | a Same whose members are servers, organisations or documents, and a Before whose member is a rollback finding, each with a derivation to records, per `republishing-sources.md` and `currency.md` | ours: test 3 of the rubric |
| reason | SEMAPV | `jdg:justification`, one of the `jdg:Same…` kinds, each `skos:broadMatch` a SEMAPV matching kind; `jdg:basis` for a person's | borrowed from SEMAPV at the kind level; the kinds are ours |
| confidence | SSSOM `confidence` | none; the justification kind stands in for it, and the review page lists the weaker kinds | diverged; see open |
| retraction | `npx:retracts` | a `prov:Activity` that `prov:invalidated` the judgment, per `naming.md` | diverged: the pod's retraction is an act, not an agent's statement |
| machine claim and run | | a claim named once from its rule, justification and members, and an assertion per matcher run, per `naming.md` | ours |

## Still open

- Whether a confidence term is borrowed from SSSOM, or the justification kind remains the only grade and the review
  page's listing is the whole of the rubric's fourth test.
- Which questions move here from `naming.md`'s open list: what a claim's "used" hashes, whether a retraction covers an
  assertion or a claim, and the naming rows for assertion and retraction.
- Whether a Before verdict, and the edition relation `republishing-sources.md` leaves open, are verdicts of
  `jdg:Judgment` or kinds of their own.
- An acknowledgement: a person's "seen, do nothing" on a finding, so a rollback finding clears from the review page
  while the later states stay. No verdict says it today; whether it is a verdict over the finding, or a mark on the
  finding outside `jdg:`.
- Whether a derivation from a source-level judgment to records is written as a rule term the derived joins cite, so
  a derived Before or Same can say which judgment it came from.
- Whether `jdg:currentlySame` survives the derived joins in `republishing-sources.md`.
- What of this note a shared view may carry: a judgment names records a view may not show.

## What would change our mind

A vocabulary for authored, retractable, graded beliefs about instances rather than terms would replace the verdict
and reason rows. SSSOM extending its scope to instance mappings would be the nearest.
