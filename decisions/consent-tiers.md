# What a model may do with a person's pods

Status: draft, 2026-11-13, for #394. Adds `cascade:ConsentTiers`, `cascade:ModelToolActKinds`, `cascade:consentTier`
and `cascade:modelToolActKind`, and the rules Y1 and Y2 of `runtime/consent.feature`. Replaces the tiers the starter
kit's `app/tools.ts` and the reference runtime's `pod-tools.ts` each define for themselves. Leans on `X1` (nothing a
pod holds is edited or deleted).

## Question

A runtime or an app offers a model a person's pods through tools: a chat, an MCP server, a page's WebMCP. Which of
those tools may run when the model calls it, which must wait for the person to say yes, and which may no tool do at
all? Today each implementation answers for itself: the starter kit gives each tool a `tier`, `free` or `ask`, and keeps a
list `NEVER` of the operations no tool calls; the runtime's tools all carry `tier: "free"`. Two apps can disagree on
what a model may do unasked, and a person cannot rely on the same consent from one app to the next.

What makes it hard: there is no server of record to hold a grant, so the rule has to be one every runtime applies
alike; the tools are each implementation's own, named and shaped as it likes, so the rule cannot list them; and a pod
only grows (`X1`), so a write cannot be undone by editing it away afterwards.

## What others do

Each quotation was read at its source on 2026-11-13 (verified), but where a line says otherwise.

- **FHIR R4 Consent.** `Consent.provision.type` is the "Action to take - permit or deny - when the rule conditions are
  met"; `Consent.provision.action` is the "Actions controlled by this Rule", bound (example) to Consent Action Codes:
  `collect` ("Gather retrieved information for storage"), `access` ("Retrieval without permitting collection, use or
  disclosure"), `use` ("Utilize the retrieved information"), `disclose` ("Transfer retrieved information") and
  `correct` ("Allow retrieval of a patient's information for the purpose of update or rectify"). A Consent records one
  person's grant to named actors, permit or deny; it has no third answer, "ask me each time", and its actions are about
  disclosing records to others, not about software acting inside the person's own store.
- **SMART App Launch 2.2.0 scopes.** An app is granted, per resource type, `c` (create), `r` (read), `u` (update),
  `d` (delete) and `s` (search): "To convey support for reading and searching observations, use scope
  `patient/Observation.rs`." A scope is granted once, at sign-in, for the life of the token: a permit, never a question
  per call.
- **openEHR, C-CDA.** Neither defines what software acting for the person may do with their own record (inferred, not
  read for this note).
- **ODRL 2.2** (W3C Recommendation). A `Policy` is "A non-empty group of Permissions and/or Prohibitions"; a
  `Permission` is "The ability to perform an Action over an Asset", a `Prohibition` "The inability to perform an Action
  over an Asset", and a permission may carry a `Duty`, "The obligation to perform an Action". The duty
  `obtainConsent` is "To obtain verifiable consent to perform the requested action in relation to the Asset", from the
  `consentingParty`, "The Party to obtain consent from". Actions include `read` ("To obtain data from the Asset"),
  `display` ("To create a static and transient rendition of an Asset"), `modify` ("To change existing content of the
  Asset. A new asset is not created by this action.") and `delete` ("To permanently remove all copies of the Asset
  after it has been used"). Looked here, failed because: the three tiers are exactly ODRL's three shapes (a permission;
  a permission with an `obtainConsent` duty; a prohibition), but a shape is not a value a tool can declare, and its
  actions miss the kinds that decide consent here (below).
- **DPV 2.3** (W3C Data Privacy Vocabularies and Controls Community Group, final report 2026-02-25). Processing
  operations include `Consult` ("to consult or query data"), `Display` ("to present or show data"), `Store` ("to keep
  data for future use"), `Collect` ("to gather data from someone") and `Erase` ("to remove data from existence i.e.
  without the possibility of retrieval"); rules are `Permission`, `Prohibition` and `Obligation`; consent has
  `ExplicitlyExpressedConsent`, "Consent that is expressed through an explicit action solely conveying a consenting
  decision", and states such as `ConsentRequested`, `ConsentGiven` and `ConsentRefused`. Looked here, failed because:
  its operations describe data processing in general, and none is "sign in as the person" or "unlock their encrypted
  store"; its rules, like ODRL's, are shapes rather than a value a tool declares.
- **PROV-O.** Records who did an act and in what role (`prov:qualifiedAssociation`, `prov:hadRole`), after the fact;
  it says nothing of what was permitted beforehand. `model-proposed-writes.md` records a confirmed write with it.
- **MCP 2025-06-18.** `ToolAnnotations` carry `readOnlyHint` ("If true, the tool does not modify its environment") and
  `destructiveHint` ("If true, the tool may perform destructive updates to its environment. If false, the tool performs
  only additive updates."), but "all properties in ToolAnnotations are **hints**" and "Clients should never make tool
  use decisions based on ToolAnnotations received from untrusted servers". Elicitation is "A request from the server
  to elicit additional information from the user via the client": the means by which an MCP server can ask the person.
- **The two implementations.** The starter kit (`app/tools.ts`, `app/AGENTS.md`): `free` "reads or moves the app",
  `ask` "writes once the person has said yes", and `NEVER` lists PodApi operations no tool calls, each with why, from
  making an encrypted pod to `deleteAll`. The runtime (`packages/cascade-runtime/src/pod-tools.ts`): every tool is a
  read, `tier: "free"`.

Sources: FHIR R4 Consent (https://hl7.org/fhir/R4/consent-definitions.html), Consent Action Codes
(https://hl7.org/fhir/R4/valueset-consent-action.html), SMART App Launch scopes
(https://hl7.org/fhir/smart-app-launch/scopes-and-launch-context.html), ODRL 2.2 vocabulary
(https://www.w3.org/TR/odrl-vocab/), DPV 2.3 (https://w3id.org/dpv, served from
https://w3c-cg.github.io/dpv/2.3/dpv/dpv.ttl), PROV-O (https://www.w3.org/TR/prov-o/), MCP schema 2025-06-18
(https://modelcontextprotocol.io/specification/2025-06-18/schema); the starter kit and the runtime at their main on
2026-11-13; the comments on #394 and on jayostis/cascade-runtime-js#758.

## Choice

| thing | prior art | what we do | borrowed or diverged |
|---|---|---|---|
| kind of act | ODRL actions, DPV operations, FHIR consent actions, SMART's `cruds` | the vocabulary lists the kinds of act a tool lets a model take, `cascade:ModelToolActKinds`, and each tool takes one: reading pods or tables, moving the app's view, writing to a pod, making a pod that is not encrypted, changing the app's tables or settings, making, unlocking or locking an encrypted pod, signing in at a source, importing records from a source, deleting pods (`Y1`) | ours, mapped with `skos:closeMatch` where an ODRL action or a DPV operation is close: none of them has the kinds that decide consent here |
| tier | ODRL permission, permission with `obtainConsent`, prohibition | three tiers, `cascade:ConsentTiers`: free, ask, never, each with its `skos:notation`; each kind of act has one, as its `cascade:consentTier` (`Y1`) | borrowed: ODRL's three shapes; diverged: named values, which a tool can declare |
| a tool's tier | the kit's and the runtime's `tier` | a tool declares its kind and its tier, by the tier's notation, and the tier is its kind's; a runtime shows it by listing its tools (`Y1`) | ours |
| free | SMART's granted scope; ODRL permission | runs when the model calls it: the person consented when they offered the model their pods; reading and moving the app's view; writes nothing to a pod (`Y1`) | borrowed: a standing grant |
| ask | ODRL `obtainConsent`; DPV `ExplicitlyExpressedConsent` | runs only once the person, shown what this call will do, says yes to it; a no, a dismissal or no answer does nothing; a yes is for one call: writing to a pod, making a pod that is not encrypted, changing the app's tables or settings (`Y2`) | borrowed: consent per act, expressed explicitly |
| a door that cannot ask | MCP elicitation, which a client may lack | a door that cannot ask the person offers no tool at ask (`Y2`) | ours: fail closed |
| never | ODRL prohibition; the kit's `NEVER` | the tier of a kind of act no tool takes, whatever the person says: the person takes it in the app. A tool carries free or ask, never this tier (`Y1`) | borrowed: a prohibition on an act, not a tool that exists and is hidden |
| what a confirmed write records | PROV-O qualified association | the model, in `cascade:ModelProposerRole`, and the person who said yes, in `cascade:PatientRole`, each on an association of the act that wrote it (`Y3`; `model-proposed-writes.md`) | borrowed from PROV-DM; ruled in `model-proposed-writes.md` |

## Why

**Why the tier belongs to a kind of act, not to a tool.** (rows "kind of act", "a tool's tier") The tools are each
implementation's own: the kit has `open_trend`, the runtime `find_changes`, and another app will have neither. What
must be alike from app to app is what the person is asked before, and that depends on what the tool does, not on its
name. So the protocol names what tools do, in nine kinds, and gives each kind its tier; a tool declares which kind it
takes. A tool whose declared tier is not its kind's is the one mistake a check can catch without knowing the tool, and
`Y1`'s query catches it.

**Why three tiers, and these.** (rows "tier", "free", "ask") ODRL's permission, permission with an `obtainConsent`
duty, and prohibition are the same three answers, and the kit's two tiers and its `NEVER` list already sort every
tool it has and the ten operations of `NEVER` into them with nothing left over. A read, and a move of what the app shows, change
nothing the person keeps: they are what offering a model the pods means, as a SMART read scope is granted once. A write
to a pod cannot be undone by editing it away (`X1`): a judgment can be retracted, but the pod keeps both, so the person
says yes before it exists. Changing the app's tables or settings writes no pod, but changes what every later read says,
so it waits for a yes too.

**Why `never` is a kind's tier, and a tool never carries it.** (row "never") The kit uses `NEVER` for a list of
operations no tool calls; jayostis/cascade-runtime-js#758's design treats `never` as a tool's tier, a tool that exists
and is not listed. The first fails closed: a tool that does not exist cannot be offered by a door that forgets to hide
it, and a door has nothing to filter. The second makes every door responsible for hiding a tool that should not have
been made. So `never` is the tier of a kind of act, and the kit's `NEVER` list is the operations whose kind it is; a
tool listed at never fails `Y1`. The kinds at never are those that need what is the person's alone (their encrypted
pod's words and password, their sign-in at a hospital), that bring in records a source gives rather than the person
states, and that delete pods, which `X1` gives no other path to.

**Why a door that cannot ask offers no ask tool.** (rows "ask", "a door that cannot ask") An MCP client may lack
elicitation, and a page may have no box to show. A door that ran the tool anyway would write without a yes; one that
refused each call would offer a tool that always fails. Not offering it is the only answer that neither writes unasked
nor misleads the model. Annotations such as `readOnlyHint` may be set from the tier, but they are hints a client may
ignore, so they are never the safeguard.

**Why our own terms, mapped to ODRL and DPV.** (rows "kind of act", "tier") ODRL's `modify` is "To change existing
content of the Asset", and nothing a pod holds is changed: a write only adds. ODRL's `annotate`, "to add explanatory
notations/commentaries to the Asset without modifying the Asset in any other way", is close to writing to a pod, a
judgment or an entry added and nothing edited, but it stops at notes, and a person's entry is not a note on an asset,
so it is a `skos:closeMatch` and no more. Neither ODRL nor DPV has an action for
signing in as the person, or for unlocking their encrypted store, and those are the acts that most need a name here.
A tier expressed as an ODRL policy is a shape (a permission with or without a duty), so a tool could not declare it as
one value, and every reader would rebuild it from three patterns. The kinds that do match carry `skos:closeMatch` to
ODRL's `read`, `display`, `annotate` and `delete` and DPV's `Consult`, `Display` and `Erase`, and importing has DPV's `Collect` as
its `skos:broadMatch`, so a reader who knows those schemes can follow. The three tiers carry `skos:relatedMatch` to
the ODRL shapes they borrow, `Permission`, `obtainConsent` and `Prohibition`: related, not close, because each ODRL
term is a policy part and a tier is one value a tool declares.

## Alternatives that lost

- **The protocol's tiers as an ODRL policy.** The strongest case: ODRL is a W3C Recommendation whose three shapes
  are these tiers, and `obtainConsent` with a `consentingParty` is exactly ask. It lost because a tool has to declare
  one value, and ODRL has none for a tier; because its actions do not have the kinds that decide consent here; and
  because a policy names an assignee, while this rule holds for every model alike. The shapes are borrowed in the
  definitions; the encoding is not.
- **DPV operations as the kinds.** The strongest case: a community vocabulary with a taxonomy of processing operations,
  made for consent records. It lost because none is signing in as the person or unlocking their store, and because
  `Store`, `Record` and `Alter` each fit a pod write only in part; mapping where one is close keeps the link.
- **`never` as a tool's tier, the tool not listed.** The strongest case: a door can show why it offers no such tool,
  and a runtime can keep one tool for a person-only act. It lost because it fails open: a door that forgets to filter
  offers the tool.
- **Only a tier on each tool, no kinds.** The strongest case: fewer terms, and each implementation knows its tools
  best. It lost because two apps would again disagree on what needs a yes, which is the problem #394 states.
- **MCP's annotations as the tiers.** The strongest case: clients already read `readOnlyHint` and `destructiveHint`.
  It lost because they are hints that "Clients should never make tool use decisions based on" from an untrusted
  server, and because they say nothing of consent.
- **SMART-style scopes, per record class and operation.** The strongest case: health apps already know them. It lost
  because a scope is granted once, at sign-in, and ask is a question per call.

## Still open

- **A yes for more than one call** (as "allow for this chat"). Lean: no; each call is asked, until a person's use shows
  the questions are too many.
- **Whether a hosted model may read real records at all.** The kit warns of it; it is the person's choice of model,
  which no tier decides.

## What would change our mind

- A tool any app needs whose act is none of the nine kinds, or two kinds at once: the list grows, or a kind splits.
- A person, shown ask's question each time, saying yes without reading it: a per-session yes, or a different kind of
  question, would then serve consent better.
- ODRL or DPV gaining an action for acting under the person's own credentials, or a value for a tier: the terms would
  then defer to it.
