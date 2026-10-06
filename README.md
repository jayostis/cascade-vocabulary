# cascade-vocabulary

The contract a Cascade pod is built and read by. It holds no code that builds a pod, and nothing generated.
[`ro-crate-metadata.json`](ro-crate-metadata.json) lists the package a runtime loads:

- [`ontologies/`](ontologies): the terms and shapes a
  [Cascade Bridge Adapter](https://github.com/jayostis/cascade-bridge-spec)'s output and a pod are read against.
  `core`, `health` and `clinical` are copied from
  [the-cascade-protocol/spec](https://github.com/the-cascade-protocol/spec) (CC BY 4.0);
  `records` and `judgments` are first declared here (Apache-2.0).
- [`queries/v1-draft/`](queries/v1-draft): the standard queries over a pod: the derivations and lenses, the views and
  labels, the matcher's comparisons, and the questions.
- [`runtime/`](runtime): what a runtime does when something arrives, as numbered rules in Gherkin feature files, each
  with the examples that show it; [`runtime/steps.md`](runtime/steps.md) lists the steps they are written in, and
  [`runtime/rules.md`](runtime/rules.md) says how a runtime runs them.
- [`runtime/pod-layout.ttl`](runtime/pod-layout.ttl): where a pod files each kind of thing, as RDF.
- [`conformance/alex-rivera/`](conformance/alex-rivera): the conformance kit, the scenario every runtime must pass: Alex
  Rivera's story, its scripted input and its right answers.

Beside them, [`tests/fixtures/`](tests/fixtures) holds the small hand-made pods each query is tested on.

## How a runtime proves it conforms

It runs every example of the feature files, the rules' and the kit's, and passes what
[the conformance kit](runtime/the-kit.feature) says: every example, the final views equal to
`expected/`, every file conforming to the shapes, every name following its rule, and every file where the layout says.
It reports each in EARL.

The reference runtime is [cascade-runtime-js](https://github.com/jayostis/cascade-runtime-js). To see it build Alex's
pod and the site that documents it:

```sh
npm install
npm run build:example alex-rivera
```

## Trying a change against the runtime

Every pull request here, and a nightly run, runs the reference runtime, at its default branch, over this checkout: the
`compatibility` check, through [cascade-bridge-spec's compatibility tooling](https://github.com/jayostis/cascade-bridge-spec/blob/main/compatibility.md),
which [`compatibility.json`](compatibility.json) names it to. A change to a rule, an example or a query that
breaks the runtime fails that check.

A change the runtime must follow lands as a pair: this repository's pull request and the runtime's, each naming the
other on a `Depends-On:` line. The check then runs the runtime's pull request, and `ready-to-merge` holds each until the
other can merge. Nothing pins this repository, as cascade-bridge-spec's `compatibility.md` says, so the check does not
run on a push to `main`: the pair was tried together before it merged.

Locally, with cascade-runtime-js cloned beside this checkout, the runtime reads this checkout as it is on disk:

```sh
npm run conformance -- --report earl.nt   # in cascade-runtime-js
```

## The vocabulary's own tests

```sh
python3 -m pip install -r requirements.txt
python3 -m pytest -n auto --dist loadgroup
```

They check the ontologies, the shapes and the crate; that every feature file uses only the steps `runtime/steps.md`
lists; and each query, over
the fixtures, on two SPARQL engines.
