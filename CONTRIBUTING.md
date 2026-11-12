# Contributing to cascade-vocabulary

Thank you for helping. This repository holds the contract a Cascade pod is built and read by: the terms and shapes,
the standard queries, the runtime rules, and the conformance kits. [`README.md`](README.md) names the parts, and
[`CLAUDE.md`](CLAUDE.md) holds the rules a change here follows; read it before you propose a new term, query or
fixture.

Report a security problem privately, by email to contact@cascadeprotocol.org, never in a public issue.

## Set up

You need Python 3.12 and git.

```sh
git clone git@github.com:<you>/cascade-vocabulary.git
cd cascade-vocabulary
python3 -m pip install -r requirements.txt
```

The dependencies are pinned in [`requirements.txt`](requirements.txt). Use those versions, so your run measures what CI
measures.

## Run the tests

This is the command CI runs:

```sh
python3 -m pytest -n auto --dist loadgroup
```

While you work, run only what you touched: a file, or `-k <words from a test name>`. A change to a class, a shape or a
fixture should also run every test file that goes over all the fixtures, `tests/test_shapes.py` among them.

The tests run in random order and print their seed. To repeat a failing order, pass it back with
`--randomly-seed=N`.

## What a pull request must pass

CI runs on every pull request. All of it must be green before a merge.

- **`vocabulary`**: the full test command above, then the check that the tests read as a specification. Every test
  sits in a top-level class whose docstring's first paragraph is a heading listed in
  [`tests/spec.json`](tests/spec.json), word for word. That check runs in CI, not in pytest, so a new or renamed test
  class needs its heading added to `tests/spec.json` by hand. A heading's situations name code or begin with "when",
  "given" or "with".
- **`compatibility`**: the reference runtime, [cascade-runtime-js](https://github.com/jayostis/cascade-runtime-js),
  is run over your checkout. A change to a rule, an example or a query that breaks the runtime fails it.
- **`ready-to-merge`**: holds a pull request until every pull request it depends on can merge (see "A change that spans two repositories").

There is no formatter or linter step in this repository. Keep the style of the file you are in; [`CLAUDE.md`](CLAUDE.md)
says what a comment may not do.

## Commits and pull requests

Use conventional commits: `feat(vocab): ...`, `fix(shapes): ...`, `test(queries): ...`, `docs: ...`. When a change
touches a term, a shape or a query, the commit message says why; the file does not.

Write the pull request description so a reader can tell what changed and why. Do not put a closing keyword (`closes`,
`fixes`, `resolves`) before an issue the pull request does not finish: GitHub closes it whatever the rest of the
sentence says.

## A change that spans two repositories

A change the runtime must follow is two pull requests: one here and one in
[cascade-runtime-js](https://github.com/jayostis/cascade-runtime-js). Each names the other in its description on a line
of its own, with the full URL:

```
Depends-On: https://github.com/jayostis/cascade-runtime-js/pull/123
```

The `compatibility` check then runs the other repository's pull request together with yours, and `ready-to-merge`
holds each until the other can merge. Nothing pins one repository to a commit of another, so a pull request that names
no other is tried against the other repository's branch of the same name as the branch it targets, and failing that
its default branch. Editing a description to add or cut a line re-runs the checks that read it. If the named pull
request changes after your checks have run, re-run yours with `gh run rerun`.

A named pull request must be from a branch of the repository itself: one from a fork fails the check. A contributor
without write access to the other repository asks a maintainer to open the counterpart.

The full rules, and where they differ from the OpenStack Zuul model they follow, are in cascade-bridge-spec's
[`compatibility.md`](https://github.com/jayostis/cascade-bridge-spec/blob/main/compatibility.md).

## Terms and decisions

Where PROV-O or PAV has a term, use that. A term copied from another source keeps its `dct:source` and `dct:license`.
A new term goes in the one `cascade#` namespace in `ontologies/cascade.ttl`, and a decision note under
[`decisions/`](decisions) says why it is as it is; [`decisions/README.md`](decisions/README.md) says how a note is
written.

## Licence

Contributions are under the licences the repository states: Apache-2.0, and CC-BY-4.0 for the clinical terms adapted
from the Cascade Protocol specification (see [`NOTICE`](NOTICE)).
