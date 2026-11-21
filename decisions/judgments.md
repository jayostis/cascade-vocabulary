# What a judgment is, and what it borrows

Status: draft, 2026-10-22, opened from the review on #130. Records what `ontologies/judgments/v1-draft/judgments.ttl`
already is, against the vocabularies it could have reused, so that the rubric's second and fourth tests in `naming.md`
have a note behind them; adds `jdg:CascadeMatcher`, the trusted-makers list, and the frame for makers of other
procedures and for makers whose inputs do not determine their answer. Names, matcher judgments and assertions are `naming.md`;
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
(https://mapping-commons.github.io/sssom/1.0/spec-model/) and SEMAPV (https://w3id.org/semapv); nanopublication
guidelines (https://nanopub.net/guidelines/working_draft/), whose `npx:retracts` is
`http://purl.org/nanopub/x/retracts`; PROV-O (https://www.w3.org/TR/prov-o/); SKOS (https://www.w3.org/TR/skos-reference/#mapping).

## Choice

The first table is what the judgments ontology is today, against the vocabularies it could have reused; the second is
who makes judgments.

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| judgment | nanopub assertion; SSSOM row | `jdg:Judgment`, a `prov:Collection` whose `prov:hadMember` are the records; one verdict (`ontologies/cascade.ttl`) | borrowed from PROV; the verdict is ours |
| maker | PROV agents | `prov:wasAttributedTo` a `prov:Person` or `prov:SoftwareAgent` (`runtime/matcher.feature`, M5; `ontologies/cascade.ttl`); a person's judgment also names the part they acted in, `cascade:PatientRole`, on one `prov:qualifiedAssociation` of the act that generated it, a blank node its `prov:wasGeneratedBy` names, whose agent is the person it is attributed to, and the act's one other association, if any, is the model's that proposed it, in `cascade:ModelProposerRole` (`runtime/naming.feature`, N10; `runtime/consent.feature`, Y3; `model-proposed-writes.md`; `cascade:PersonJudgmentShape`) | borrowed; the role sits where PROV-DM puts one, on an association |
| verdict | `owl:sameAs`; `Linkage`; `Patient.link` | `jdg:Same`, `jdg:Different`, `jdg:Erroneous`, `jdg:About`, `cascade:NotAbout`, and `cascade:Before`, of two revisions, naming the earlier as `cascade:earlierMember`, per `currency.md` (`ontologies/cascade.ttl`) | ours: a belief with a maker, not an axiom, and Different wins over Same |
| not about | FHIR `$match`'s `match-grade` `certainly-not`, an engine's grade on a search result | `cascade:NotAbout`, a person's verdict whose one member is a patient profile, naming the `cascade:subject` it is not about and no basis (`cascade:NotAboutVerdictShape`, `cascade:AboutShape`): while it counts, no record naming the profile is the subject's, whatever About counts, and each is left out for `cascade:PatientProfileJudgedNotAbout`, hidden, never deleted (`queries/derivations/subjects.rq`, `excluded-for-their-patient.rq`). It outranks every machine's About and its own maker's earlier About; a person's About it does not outrank stands against it, and the profile is held back: its records are left out for `cascade:PatientProfileJudgedBothAboutAndNotAbout`, and `profile/What needs review` lists it with the names on both sides, beside every profile no one has answered. Only an act that names it, a retraction or a judgment replacing it, lifts it (`runtime/matcher.feature`, M2a) | ours: a grade is a machine's answer to one search, where this is a person's, kept and retractable |
| acknowledgement | FHIR `DetectedIssue.mitigation`; `Flag.status` | `cascade:Acknowledged`, a verdict naming a warning's kind, its `cascade:answersWarningOfKind`, a concept of `cascade:FindingForReviewKinds`, and, as its members, what the warning is about: the records, documents or acts the kind's definition says its targets resolve to, never the finding (`naming.md`, "Nothing kept cites anything derived"). A warning of that kind leaves the review page while an Acknowledged of its kind that stands names every one of those things, however the pod works it out again; the warning still stands, and nothing else changes. A judgment naming a finding is refused (`cascade:JudgmentNamesNoFindingShape`; `runtime/matcher.feature`, M19). A verdict, not a mark outside judgments, because a person's other answers to a warning, a Same, a Different or a Before, are judgments, so they all list, count, retract and sync alike, and writers that file them in any order hold one answer (looked at `DetectedIssue.mitigation`, an action taken on a clinical issue with a practitioner author, and `Flag.status`, which edits the flag in place, where a pod edits nothing) | ours |
| a clock known wrong | | `cascade:ClockDiscounted`, a person's verdict whose one member is an act: every revision the act generated is ranked as carrying no observation time, per `currency.md` (`runtime/currency.feature`, C7). It discounts and carries no offset: the derivation `currency.md` describes needs only that the times are wrong, and an offset would be a guess at how wrong (#204) | ours |
| judgment over a source-level thing | | a Same whose members are servers or organisations, with a derivation to records, per `republishing-sources.md`. A finding is not such a thing, since the pod derives it: a person answers each pair a finding of what a rule list version no longer reaches names with a Same or a Different over the pair's records, which an app may file for every pair of the line at once (`runtime/matcher.feature`, M19), and a Before answering a rollback finding, not yet built, will name what the finding is about, as `currency.md`'s row "Before over a finding" says | ours: test 3 of the rubric |
| reason | SEMAPV | `jdg:justification`, one of the `jdg:Same…` kinds, the matching kinds each `skos:broadMatch` a SEMAPV kind (`jdg:Demographics` and the About bases have none); `jdg:basis` for a person's (`ontologies/cascade.ttl`) | borrowed from SEMAPV at the kind level; the kinds are ours |
| confidence | SSSOM `confidence` | none; the justification kind stands in for it, and the review page lists the weaker kinds (`ontologies/cascade.ttl`) | diverged; see open |
| retraction | `npx:retracts` | a `prov:Activity` that `prov:invalidated` the judgment, per `naming.md` (`runtime/naming.feature`, N10 and N15); a person retracts and replaces anyone's judgment but a matcher's, which carries `cascade:matcherRule` (N16): a retraction or a replacement of a person's judgment by someone else is listed for review (`judgment/What needs review`), except a judgment that counts again because its replacement was taken back | diverged: the pod's retraction is an act, not an agent's statement |
| matcher judgment and assertion | nanopub assertion | a matcher judgment named once from its maker, rule, justification, members and used, its members the record and the least member of each entry it matched, a star that `same-pairs.rq` derives; an assertion per rule list version that reaches it and changed its rule's `rec:queryHash`, per `naming.md` (`runtime/naming.feature`, N6; `runtime/matcher.feature`, M5 and M9) | borrowed split; ours in the parts |
| what a judgment, a finding or a view came from | PROV-O `prov:wasDerivedFrom` and `prov:used` | `prov:wasDerivedFrom`, from each version a machine's judgment or a finding was made from, the document each member of a person's judgment was shown from, never a version (`naming.md`, "Nothing kept cites anything derived"; `runtime/naming.feature`, N16), and each reference version a view was built with, and `prov:used` only on an activity: imports, entry sessions, the manifest's build act, retractions (`runtime/naming.feature`, N6 and N10; `runtime/matcher.feature`, M5, M18 and M21; `runtime/arrivals.feature`, A15) | borrowed; PROV-O gives `prov:wasDerivedFrom` an entity for domain and `prov:used` an activity. A finding has no act and a matcher judgment no act and no time, so no activity stands between them and what they came from; a view takes its own mark and not the manifest's build act, since a view can be built in part; and no lens, `lapsed-sames` or incremental build gains a hop |

Every judgment names its maker, and nothing else about a judgment depends on there being one matcher.

| maker | its term | how its judgment is named | its version | counts while |
|---|---|---|---|---|
| a person | their own IRI | minted once by them | none | always; outranks every machine |
| the Cascade matcher: any runtime following `runtime/matcher.feature` and the Cascade rule list | `jdg:CascadeMatcher`, one `prov:SoftwareAgent`, unversioned | hashed from maker, rule, justification, members and used, per `naming.md` | the rule list version, on the assertion; the runtime, on the run's act | it is asserted under a rule list version whose row for its rule carries the same `rec:queryHash` as the version the app uses, and the used versions are current |
| a matcher of another procedure: an app's own rules | the app's own agent term, in its own namespace, with its rules as its own terms | hashed the same way, under its rule IRIs | the app's version, on the assertion; the app, on the act | the pod trusts that maker and version, and the used versions are current |
| a maker whose answer its inputs do not determine: a model | its own agent term, with model and version | minted once, as a person's is, since no hash of inputs names an answer the inputs do not fix; its reason is text and its confidence a number | the model's version, on the judgment | the pod trusts that maker and version |

The pod's trusted makers are a list the person controls: installing an app adds its maker, removing it drops it, and
a dropped maker's judgments stop counting by derivation with nothing retracted. Makers combine by who first, then
by kind: a person outranks every machine, so a person's Same stands over a machine's Different, but only for the pair it names, so a pair joined only through a third record keeps its Different and "What needs review" lists it as judged different, still joined; among machines a
Different outranks a Same from any maker; and a machine judgment on weaker grounds is surfaced by the rubric's fourth
test, which for a model means its confidence. An app's rule may declare itself `skos:broadMatch` a vocabulary
justification kind, as the vocabulary's own rules do SEMAPV, so a view can treat "the app's lot-number rule" as a
kind of shared-identifier join without knowing the rule.

## Why

**Why a belief with a maker, not an axiom.** (rows "judgment", "maker") That two records are one fact, that two servers are one hospital, that a
source's patient is this person: each is a belief, filed with its reason and its maker, so that it can be wrong and
can be retracted without touching a name (`naming.md`, the rubric's second test).

**Why a person outranks every machine.** A person's Same stands over a machine's Different since the person has seen
the objection and overridden it. The person says so over the records, never by replacing or retracting the matcher's
judgment, whose name is derived (`naming.md`, "Why nothing kept cites anything derived"): a machine's Same whose member
changed is listed for review until a person's Same over its records, naming the documents they were shown, answers it.

**Why Different outranks Same among machines.** (row "verdict") Keeping two records apart is the mistake that can be undone: a later
Same joins them and nothing was lost. A wrong merge hides one record behind the other, and the person may never see
it. So where two makers disagree, the pod errs toward showing two things, and a person's Same settles it.

**Why a person's NotAbout is needed, and outranks a machine's About and its maker's earlier one.** (row "not about")
The import once filed an About for every profile no counting About claimed, signed by the owner in the patient's role,
so a parent's only "these are not my child's" was to retract words they never said, and the next import said them again.
The import now claims nothing by itself, and a person says no with a verdict of its own over the profile record, which
keeps its name across pulls. It does not borrow Different's reason for winning: Different wins so the pod errs toward
showing, and a NotAbout hides. It wins over a machine's About because a person outranks every machine, and over its own
maker's earlier About because the later word of one person is that person's answer.

**Why a person's About after a NotAbout holds the profile back, and does not lift it.** (row "not about") Hiding a real
allergy is as dangerous as showing a sibling's, so where two people answer a profile differently, neither wins silently:
the records stay hidden, nothing is removed, and the profile is listed with both names. It leaves the state three ways: a
retraction of either side; the About's maker filing a later NotAbout of their own, which makes that About their earlier
word; or a judgment that replaces either side (`dct:replaces`). The same holds when one person files an About after their
own NotAbout: only an act that names a NotAbout, its retraction or a judgment that replaces it, lifts it, as anyone
with standing in the pod may retract a statement (a retraction of someone else's is listed under
`judgment/What needs review`), so a later About, from an import, a model the person said yes to, or the person
themselves, is never the act that undoes a no. Read the other way, a later About would let the very import the NotAbout
answers lift it again.

**Why only an About with basis OwnerStatement stands against a NotAbout, and a machine basis needs a software agent.**
(row "not about") A basis says who judged: `cascade:SameDemographics` is a matcher's, `cascade:PortalAuthenticated` a
login's, `cascade:RelatedPersonConnection` a portal's word that a person is related (not a person's statement), and
`cascade:OwnerStatement` the one a person states. The first three are machine bases, and only a `cascade:OwnerStatement`
About by a person stands against a person's NotAbout; the shape (`cascade:MachineBasisShape`) refuses a judgment with
a machine basis that is not attributed to a `prov:SoftwareAgent`, or whose author is also a `prov:Person`, so a person's name never carries a machine's word. Were
it allowed, an import that files a portal or demographics About in the owner's name, which is the claim the import no
longer makes, would put every profile the owner denied back on review after each import.

**Why two people who sign with one author IRI are one maker.** (row "not about") The author IRI is the person: a pod
cannot tell two people apart who file as the same `prov:Person`, so one's About and the other's later NotAbout are one
maker's earlier and later word, and the NotAbout wins with no hold-back and no listing. A pod that wants two answers
names two people.

**Why every maker leaves a trail.** (row "maker") Where a maker went wrong, its trail is what finds the damage: a rule list version
by the assertions under it, a runtime by the acts it performed, an app by its agent and version, and a person's
Erroneous over an act hides bad data from any of them.

**Why a person's role sits on the act that generated the judgment.** (row "maker") PROV-DM allows a role on an
association, a usage, a generation, an invalidation, a start and an end, and never on an attribution
(https://www.w3.org/TR/2013/REC-prov-dm-20130430/#term-attribute), so a judgment names it as a document names its
author's, on an association of the act that generated it (`republishing-sources.md`, row "the part a party played in a
document"). A person's retraction is itself an act, so its role is on its own association already.

**Why a matcher judgment, an assertion per rule list version, and one matcher agent.** (row "matcher judgment and assertion") A matcher judgment is named once, with an
assertion per rule list version because the same inputs give the same name, so a later version that agrees could
otherwise write nothing, and a run that reaches an asserted judgment writes nothing, so a daily run adds no files. The
rule list's version is out of the matcher judgment's name because with it in, every version renamed every matcher judgment, the duplication
the split exists to stop. A matcher judgment counts under any version that keeps its rule's `rec:queryHash` because M11 pins the
rule's bytes, so such versions reach the same matcher judgments; an assertion per matcher judgment per version would be 600k to 1.2M files
over ten years ([#206](https://github.com/the-cascade-protocol/cascade-vocabulary/issues/206)). A matcher judgment's members are a star, the
record and the least member of each entry it matched, because entries come out the same and every earlier copy as a
member expands to about 58M pairs over ten years (#206). The Cascade matcher is one unversioned agent because the
matcher feature promises every runtime that follows it reaches the same matcher judgments, so which runtime ran is forensics, and
it sits on the run's act with every other act's performer (`naming.md`).

**Why a model's judgment is minted, not hashed.** No hash of inputs names an answer the inputs do not fix, so a
model's judgment is minted once, as a person's is.

**Why a retraction is an activity.** (row "retraction") PROV already says how an entity is invalidated (`naming.md`); `npx:retracts` has
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
  two correct runtimes would make two matcher judgments of one conclusion, which the matcher feature forbids. The version is on
  the assertion and the runtime on the act (`naming.md`).
- **A matcher judgment counting while the app uses that rule list version.** The strongest case: each version says for itself
  what it reaches. Every version then asserts every matcher judgment again, 600k to 1.2M assertions in ten years, more than the
  whole pod (computed, #206), where versions with one query hash reach the same matcher judgments (`naming.md`).
- **A matcher judgment whose members are the record and everything it matched.** The strongest case: one file shows the whole
  join. A fact in every monthly summary makes it cubic, about 58M derived pairs in ten years (computed, #206), where a
  star gives the same entries (`naming.md`).

## Still open

- Whether a confidence term is borrowed from SSSOM, or the justification kind remains the only grade and the review
  page's listing is the whole of the rubric's fourth test.
- The shape of the trusted-makers list: per maker, per maker and version, and whether it is a file in the pod (so
  it syncs) or the writer's own, outside the pod.
- A model's judgment: the term for its confidence, and whether a model asked twice about one pair, giving two
  answers, files two judgments or the later supersedes.
- Whether a derivation from a source-level judgment to records is written as a rule term the derived joins cite, so
  a derived Before or Same can say which judgment it came from.
- A declined act leaves no finding, because no act generated one; whether a refusal needs a home.
- How `jdg:currentlySame` is amended for the derived joins, or whether it survives them; `republishing-sources.md`
  leaves the same question open.
- What of this note a shared view may carry: a judgment names records a view may not show.

## What would change our mind

A vocabulary for authored, retractable, graded beliefs about instances rather than terms would replace the verdict
and reason rows. SSSOM extending its scope to instance mappings would be the nearest.
