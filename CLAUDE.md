# cascade-vocabulary — Agent Context

The contract a Cascade pod is built and read by; [`README.md`](README.md) names the parts.

## The rules

- **An adapter names a file by its path here:** removing a term or moving a file it lists breaks it.
- **A copied term keeps its IRI** and carries its type, label, domain, range and superclasses,
  and nothing else. Its shape is the source's, trimmed to the terms here.
- **A new term goes in a namespace first declared here** (`records`, `judgments`). Where PROV-O
  or PAV has a term, that term is used instead.
- **Content is on a version, not on its record.** A class's shape targets the class and the
  subjects of the properties only that class's content carries; nothing about a version's
  content is required, because a source may omit any of it.
- **Each question is asked once.** Before adding one, look under its kind for the question that
  already returns those rows.
- **A kit's `expected/` and its examples come from [the scenario](https://github.com/jayostis/cascade-vocabulary/issues/4)**,
  and a rule's examples under `runtime/` from the rule they sit under, never from a runtime's output.
- **A query is tested on fixtures under [`tests/fixtures/`](tests/fixtures), one per behaviour, never on an
  example.** Its expected rows are written from what the query says it does. A check true of any pod runs over every
  fixture, with `every_fixture` from [`tests/pods.py`](tests/pods.py).
- **A change here is tried against the reference runtime** by the `compatibility` check, on each pull request and
  nightly. One the runtime must follow is a pair of pull requests, here and in cascade-runtime-js, each naming the other
  on a `Depends-On:` line.
- **The suite runs in parallel** (`python3 -m pytest -n auto --dist loadgroup`): what a test builds is built once per
  worker, and the cases that share it are put on one worker with `xdist_group`.

## Conventions

- Conventional commits: `feat(vocab): ...`, `fix(shapes): ...`; a change to a term, a shape or a
  query says why in its message, never in the file.
- No comment that restates a name, a constraint or another file.
