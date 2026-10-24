# What a judgment is, and what it borrows

Status: draft, 2026-10-22, opened from the review on #130. Records what `ontologies/judgments/v1-draft/judgments.ttl`
already is, against the vocabularies it could have reused, so that the rubric's second and fourth tests in `naming.md`
have a note behind them; adds `jdg:CascadeMatcher`, the trusted-makers list, and the frame for makers of other
procedures and for makers whose inputs do not determine their answer. Names, claims and assertions are `naming.md`;
the Before and the findings it orders are `currency.md`; the Sames over servers and organisations are
`republishing-sources.md`. The open questions are listed at the end.

## Question

A pod holds beliefs past what any source defines: that two records are one fact, that two servers are one hospital,
that a record is wrong, that a source's patient is this person, that one revision precedes another. A person makes
some and the matcher makes most. Is there a vocabulary for such a belief, with its verdict, its maker, its reason,
its confidence and its retraction, or does the pod define one?

## What others do

- **FHIR** `Linkage` lists resources that "refer to the same real-world occurrence", `Patient.link` merges patients;
  neither carries a maker beyond the server, a reason, or a retraction.
- **OWL** `owl:sameAs` and `owl:differentFrom` state logical identity: a reasoner merges whatever they touch, nobody is
  recorded as having said so, and there is no retraction.
- **SSSOM** records a mapping as a row with a predicate, a `mapping_justification` from **SEMAPV**, an author, and a
  `confidence`; built for terms in ontologies.
- **Nanopublications** carry an assertion graph, a provenance graph and a publication-info graph, and retract one with
  `npx:retracts`, whose domain is an agent.
- **PROV-O** gives the parts: `prov:Collection` with `prov:hadMember`, `prov:Person` and `prov:SoftwareAgent`,
  `prov:Activity`, `prov:wasAttributedTo`, `prov:invalidated`; and `prov:alternateOf`, "two entities present aspects
  of the same thing", which is weaker than a verdict.
- **skos** `exactMatch` and `closeMatch` relate concepts, and the pod uses them for codes, not records.

Sources: FHIR `Linkage` (https://hl7.org/fhir/R4/linkage.html), `Patient.link`
(https://hl7.org/fhir/R4/patient.html#links); OWL 2 (https://www.w3.org/TR/owl2-syntax/#Individual_Equality); SSSOM
(https://mapping-commons.github.io/sssom/spec-model/) and SEMAPV (https://w3id.org/semapv); nanopublication guidelines
(https://nanopub.net/guidelines/working_draft/) and `npx:retracts` (http://purl.org/nanopub/x/retracts); PROV-O
(https://www.w3.org/TR/prov-o/); SKOS (https://www.w3.org/TR/skos-reference/#mapping).

## Choice

The first table is what the judgments ontology is today, against the vocabularies it could have reused; the second is
who makes judgments.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| judgment | nanopub assertion; SSSOM row | `jdg:Judgment`, a `prov:Collection` whose `prov:hadMember` are the records; one verdict | borrowed from PROV; the verdict is ours |
| maker | PROV agents | `prov:wasAttributedTo` a `prov:Person` or `prov:SoftwareAgent` | borrowed |
| verdict | `owl:sameAs`; `Linkage`; `Patient.link` | `jdg:Same`, `jdg:Different`, `jdg:Erroneous`, `jdg:About`; a Before is proposed in `currency.md` | ours: a belief with a maker, not an axiom, and Different wins over Same |
| acknowledgement | FHIR `DetectedIssue.mitigation`; `Flag.status` | `cascade:Acknowledged`, a verdict whose one member is a finding: the finding leaves the review page, still stands, and nothing else changes (`runtime/matcher.feature`, M19). A verdict, not a mark outside judgments, because a person's other answers to a finding, a Same or a Before, are judgments whose member is the finding, so the three list, count, retract and sync alike, and writers that file them in any order hold one answer (looked at `DetectedIssue.mitigation`, an action taken on a clinical issue with a practitioner author, and `Flag.status`, which edits the flag in place, where a pod edits nothing) | ours |
| judgment over a source-level thing | | a Same whose members are servers or organisations, a Before whose member is a rollback finding, and a Same whose member is the finding of what a rule list version no longer reaches, each with a derivation to records or pairs, per `republishing-sources.md`, `currency.md` and `naming.md` | ours: test 3 of the rubric |
| reason | SEMAPV | `jdg:justification`, one of the `jdg:Same…` kinds, the matching kinds each `skos:broadMatch` a SEMAPV kind (`jdg:Demographics` and the About bases have none); `jdg:basis` for a person's | borrowed from SEMAPV at the kind level; the kinds are ours |
| confidence | SSSOM `confidence` | none; the justification kind stands in for it, and the review page lists the weaker kinds | diverged; see open |
| retraction | `npx:retracts` | a `prov:Activity` that `prov:invalidated` the judgment, per `naming.md` | diverged: the pod's retraction is an act, not an agent's statement |
| machine claim and assertion | nanopub assertion | a claim named once from its maker, rule, justification, members and used, its members the record and the least member of each entry it matched, a star that `same-pairs.rq` derives; an assertion per rule list version that reaches it and changed its rule's `rec:queryHash`, per `naming.md` | borrowed split; ours in the parts |

Every judgment names its maker, and nothing else about a judgment depends on there being one matcher.

| maker | its term | how its judgment is named | its version | counts while |
|---|---|---|---|---|
| a person | their own IRI | minted once by them | none | always; outranks every machine |
| the Cascade matcher: any runtime following `runtime/matcher.feature` and the Cascade rule list | `jdg:CascadeMatcher`, one `prov:SoftwareAgent`, unversioned | hashed from maker, rule, justification, members and used, per `naming.md` | the rule list version, on the assertion; the runtime, on the run's act | it is asserted under a rule list version whose row for its rule carries the same `rec:queryHash` as the version the app uses, and the used versions are current |
| a matcher of another procedure: an app's own rules | the app's own agent term, in its own namespace, with its rules as its own terms | hashed the same way, under its rule IRIs | the app's version, on the assertion; the app, on the act | the pod trusts that maker and version, and the used versions are current |
| a maker whose answer its inputs do not determine: a model | its own agent term, with model and version | minted once, as a person's is, since no hash of inputs names an answer the inputs do not fix; its reason is text and its confidence a number | the model's version, on the judgment | the pod trusts that maker and version |

The pod's trusted makers are a list the person controls: installing an app adds its maker, removing it drops it, and
a dropped maker's judgments stop counting by derivation with nothing retracted. Makers combine by who first, then
by kind: a person outranks every machine, so a person's Same stands over a machine's Different; among machines a
Different outranks a Same from any maker; and a machine judgment on weaker grounds is surfaced by the rubric's fourth
test, which for a model means its confidence. An app's rule may declare itself `skos:broadMatch` a vocabulary
justification kind, as the vocabulary's own rules do SEMAPV, so a view can treat "the app's lot-number rule" as a
kind of shared-identifier join without knowing the rule.

## Why

**Why a belief with a maker, not an axiom.** That two records are one fact, that two servers are one hospital, that a
source's patient is this person: each is a belief, filed with its reason and its maker, so that it can be wrong and
can be retracted without touching a name (`naming.md`, the rubric's second test).

**Why a person outranks every machine.** A person's Same stands over a machine's Different since the person has seen
the objection and overridden it.

**Why Different outranks Same among machines.** Keeping two records apart is the mistake that can be undone: a later
Same joins them and nothing was lost. A wrong merge hides one record behind the other, and the person may never see
it. So where two makers disagree, the pod errs toward showing two things, and a person's Same settles it.

**Why every maker leaves a trail.** Where a maker went wrong, its trail is what finds the damage: a rule list version
by the assertions under it, a runtime by the acts it performed, an app by its agent and version, and a person's
Erroneous over an act hides bad data from any of them.

**Why a claim, an assertion per rule list version, and one matcher agent.** A machine judgment is one claim with an
assertion per rule list version because the same inputs give the same name, so a later version that agrees could
otherwise write nothing, and a run that reaches an asserted claim writes nothing, so a daily run adds no files. The
rule list's version is out of the claim's name because with it in, every version renamed every claim, the duplication
the split exists to stop. A claim counts under any version that keeps its rule's `rec:queryHash` because M11 pins the
rule's bytes, so such versions reach the same claims; an assertion per claim per version would be 600k to 1.2M files
over ten years ([#206](https://github.com/jayostis/cascade-vocabulary/issues/206)). A claim's members are a star, the
record and the least member of each entry it matched, because entries come out the same and every earlier copy as a
member expands to about 58M pairs over ten years (#206). The Cascade matcher is one unversioned agent because the
matcher feature promises every runtime that follows it reaches the same claims, so which runtime ran is forensics, and
it sits on the run's act with every other act's performer (`naming.md`).

**Why a model's judgment is minted, not hashed.** No hash of inputs names an answer the inputs do not fix, so a
model's judgment is minted once, as a person's is.

**Why a retraction is an activity.** PROV already says how an entity is invalidated (`naming.md`); `npx:retracts` has
domain `foaf:Agent`, making the retractor an agent and the retracted a nanopublication.

## Alternatives that lost

- **OWL `owl:sameAs` and `owl:differentFrom`.** The strongest case: they are the web's statement of logical identity,
  and a reasoner acts on them. A reasoner merges whatever they touch, nobody is recorded as having said so, and there
  is no retraction, where a judgment must be able to be wrong and be retracted without touching a name.
- **`npx:retracts` for retraction.** The strongest case: nanopublication vocabulary built for retraction. Its domain
  is an agent, so the retractor would be an agent and the retracted a nanopublication, where ours is an activity over
  any entity.
- **The matcher named per rule list version, or per runtime.** The strongest case: the agent would say which rules
  and which code. Per version, the maker changes every release, which is the duplicate problem again; per runtime,
  two correct runtimes would make two claims of one conclusion, which the matcher feature forbids. The version is on
  the assertion and the runtime on the act (`naming.md`).
- **A claim counting while the app uses that rule list version.** The strongest case: each version says for itself
  what it reaches. Every version then asserts every claim again, 600k to 1.2M assertions in ten years, more than the
  whole pod (computed, #206), where versions with one query hash reach the same claims (`naming.md`).
- **A claim whose members are the record and everything it matched.** The strongest case: one file shows the whole
  join. A fact in every monthly summary makes it cubic, about 58M derived pairs in ten years (computed, #206), where a
  star gives the same entries (`naming.md`).

## Still open

- Whether a confidence term is borrowed from SSSOM, or the justification kind remains the only grade and the review
  page's listing is the whole of the rubric's fourth test.
- The shape of the trusted-makers list: per maker, per maker and version, and whether it is a file in the pod (so
  it syncs) or the writer's own, outside the pod.
- A model's judgment: the term for its confidence, and whether a model asked twice about one pair, giving two
  answers, files two judgments or the later supersedes.
- Whether a Before verdict is a verdict of `jdg:Judgment` or a kind of its own, now that it orders revisions of one
  record and, for a lead, of two records a Same joins.
- Whether a derivation from a source-level judgment to records is written as a rule term the derived joins cite, so
  a derived Before or Same can say which judgment it came from.
- A verdict over an act saying its observation times are known wrong, per `currency.md`: its name, and whether it
  carries an offset or only discounts.
- A declined act leaves no finding, because no act generated one; whether a refusal needs a home.
- How `jdg:currentlySame` is amended for the derived joins, or whether it survives them; `republishing-sources.md`
  leaves the same question open.
- What of this note a shared view may carry: a judgment names records a view may not show.

## What would change our mind

A vocabulary for authored, retractable, graded beliefs about instances rather than terms would replace the verdict
and reason rows. SSSOM extending its scope to instance mappings would be the nearest.
