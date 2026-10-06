# Runtime rules

What a runtime does when it fills a pod: how it names what it writes, which arrivals it writes, how the matcher judges,
the order it writes in, and what passing a kit means. Each section is a [Gherkin](https://cucumber.io/docs/gherkin/)
feature file beside this one. Each numbered rule is a `Rule:` whose title is the rule and whose description holds the
rest of its prose, with the examples that show it beneath it; a rule no example can show says why.

| Section | File |
|---|---|
| Naming | [`naming.feature`](naming.feature) |
| Arrivals | [`arrivals.feature`](arrivals.feature) |
| The matcher's procedure | [`matcher.feature`](matcher.feature) |
| Nothing is edited or deleted | [`nothing-is-edited.feature`](nothing-is-edited.feature) |
| Write order | [`write-order.feature`](write-order.feature) |
| The conformance kit | [`the-kit.feature`](the-kit.feature) |

[`steps.md`](steps.md) lists every step the files use, what each means, the dataset a `Then` reads and where the
scripted input is. Each example's expected values are written from the rule it sits under, or from
[the scenario](https://github.com/jayostis/cascade-vocabulary/issues/4) for a kit, never from a runtime's output.

## How a runtime runs these files

A runtime reads every feature file here and each kit's under [`conformance/`](../conformance) with a standard Gherkin
parser, and implements each step of [`steps.md`](steps.md) once. Each example (a pickle, its background's steps
first) is replayed into a new pod and its `Then` steps read the result; examples that begin with the same steps may
share the replay of them, since a step's writes depend only on the steps before it and its input.

It reports in EARL as
[`engine/executing.md`](https://github.com/jayostis/cascade-bridge-spec/blob/main/engine/executing.md) describes, with
the runtime as `earl:subject`: one assertion per example, and one per check 2 to 5 of each kit as
[`the-kit.feature`](the-kit.feature) names them. An example's test is the feature file's IRI followed by `#` and the
example's name in lower case, each run of other characters than letters and digits made one hyphen; two examples
that would share a test, as the rows of an outline whose name has no `<placeholder>`, each fail. A failed example's
assertion says the rule it is under and the step that failed.
