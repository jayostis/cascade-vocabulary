# cascade-vocabulary

The contract a Cascade pod is built and read by. It holds no code that builds a pod, and nothing generated.
[`ro-crate-metadata.json`](ro-crate-metadata.json) lists the package a runtime loads:

- [`ontologies/`](ontologies): the terms and shapes a
  [Cascade Bridge Adapter](https://github.com/jayostis/cascade-bridge-spec)'s output and a pod are read against, every
  one in the namespace `https://ns.cascadeprotocol.org/cascade#`: [`cascade.ttl`](ontologies/cascade.ttl) and
  [`cascade.shapes.ttl`](ontologies/cascade.shapes.ttl), under `Apache-2.0 AND CC-BY-4.0`. The clinical terms and
  their shapes are adapted from "The Cascade Protocol specification" by Cascade Agentic Labs LLC,
  [the-cascade-protocol/spec](https://github.com/the-cascade-protocol/spec/tree/d819bc2c045266f9f79ebf9398cbbb82a6156d27/ontologies),
  licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): trimmed to type, label, domain, range and
  superclasses, renamed into this namespace, and merged; each carries its `dct:source` and `dct:license`. Every other
  term is first declared here, under Apache-2.0.
- [`decisions/`](decisions): why a term or a rule is as it is, one note for each, with what others do, the alternatives
  that lost and what would change our mind.
- [`queries/`](queries): the standard queries over a pod: the derivations and lenses, the views and
  labels, the matcher's comparisons, and the questions.
- [`runtime/`](runtime): what a runtime does when something arrives, as numbered rules in Gherkin feature files, each
  with the examples that show it; [`runtime/steps.md`](runtime/steps.md) lists the steps they are written in, and
  [`runtime/rules.md`](runtime/rules.md) says how a runtime runs them.
- [`runtime/pod-layout.ttl`](runtime/pod-layout.ttl): where a pod files each kind of thing, as RDF.
- [`runtime/rule-list/`](runtime/rule-list): the matcher's rule list an app uses, apart from every table. The table
  kinds its rules read, each kind's row shape and the code systems' IRI forms are in `cascade.ttl` and
  `cascade.shapes.ttl`.
- [`conformance/`](conformance): the conformance kits, the scenarios every runtime must pass, each a story, its
  scripted input and its right answers: [Alex Rivera's](conformance/alex-rivera), from FHIR, and
  [Priya Natarajan's](conformance/priya-natarajan), from FHIR and C-CDA together, with medications and lab results, and
  [Martin Okafor's](conformance/martin-okafor), one variant in two FHIR reports beside what ClinVar says of it. An
  example reads the tables its story holds as the matcher's queries do, so a kit may ask a published query by its file,
  as Priya's asks `tables/medication-classes.rq` of an app's tables, and `tables/panel-results.rq`, her lab results in
  a LOINC panel she names; Alex's asks `tables/joined-by.rq`, the tables that joined her flu shots.
- [`people/`](people): the hand-written test people, each the one place their name, birth date and gender are written,
  with what each hospital holds of them, checked to agree.

Beside them, [`tests/fixtures/`](tests/fixtures) holds the small hand-made pods each query is tested on.

## Docs

- [The Cascade hub](https://jayostis.github.io/cascade-runtime-js/): where to go for each thing, and every repository.
- [Term reference](https://jayostis.github.io/cascade-runtime-js/terms/): every term the vocabulary defines or copies.
- [The rules](https://jayostis.github.io/cascade-runtime-js/spec/): the rules, feature by feature.
- [Decision notes](https://jayostis.github.io/cascade-runtime-js/decisions/): why a term or a rule is as it is.
- [Latest conformance run](https://jayostis.github.io/cascade-runtime-js/conformance/): the reference runtime's result for every example of the features and conformance kits.
- [Unit-test reports](https://jayostis.github.io/cascade-runtime-js/conformance/tests/cascade-vocabulary/): each case of the vocabulary's tests, with its result, from the newest run on main; [the runtime's](https://jayostis.github.io/cascade-runtime-js/conformance/tests/cascade-runtime-js/) are beside it.

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

## Red-main alerts

The [`red-main` workflow](.github/workflows/red-main.yml) tells you when a Cascade repository's `main` is red. Every day
at 06:41 UTC, and when dispatched by hand, it reads the latest `push`, `schedule` and `workflow_run` run of each workflow
on `main` in every unarchived `jayostis/cascade-*` repository, and keeps one issue labelled `red-main` open there for each
workflow whose latest run failed. A run on a pull request or a manual run is not the state of `main`, and a run older
than 14 days is ignored.

- **Opens** on the first red run: the issue links the run, names its first failing step and lists the failure messages
  the run printed as annotations (a step that continues on error is green, so a feed check names its failed feeds
  there). **Comments** once for each later red run. A workflow says what is red by printing `::error::<what>` lines;
  the alert quotes them, and without them it names only the step.
- **Closes** at the first red-main run after the latest `push`, `schedule` and `workflow_run` run of that workflow are all
  green. A manual run does not close it, and a run still going or cancelled holds it as it is. Dispatch `red-main` to
  close it sooner than its next daily run.
- **Needs** the repository secret `RED_MAIN_TOKEN`, a fine-grained personal access token on the `jayostis/cascade-*`
  repositories with Issues read and write, Actions read, Checks read and Metadata read. Without the token the run fails
  with one line saying so; without Checks read the issues open but name only the failing step.

When one opens, read the run and the failure messages, fix the cause or, when it is known and not yours to fix, comment
the issue that tracks it. Do not close the issue by hand: the next red run opens another.

## The vocabulary's own tests

```sh
python3 -m pip install -r requirements.txt
python3 -m pytest -n auto --dist loadgroup
```

They check the ontologies, the shapes and the crate; that every feature file uses only the steps `runtime/steps.md`
lists; and each query, over
the fixtures, on two SPARQL engines. The tests are classes named for what the files are held to, and they run in random
order; `tests/spec.json` lists the headings of the tests page, each one a top-level class.

A run prints its seed. To repeat a red run's order, pass it back with `-p randomly --randomly-seed=N`; `-p no:randomly`
turns the shuffle off.
