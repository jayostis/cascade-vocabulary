# cascade-vocabulary — Agent Context

The vocabulary jayostis/cascade-bridge-adapter-fhir-r4 is read against, as a package a
program loads. Holds exactly the terms an adapter pinned to it, or an example pod,
writes, and nothing more.

## The rules

- **A term arrives because an adapter, or an example pod, writes it.** No
  term for later, none for completeness. Removing a term an adapter still lists is a breaking change for it.
- **A copied term keeps its IRI** and names the file and commit it came from with
  `dct:source`. It carries its type, label, domain, range and superclasses, and nothing
  else: the rest is at its source. Its shape is the source's, trimmed to the terms here,
  and names its source the same way.
- **A new term goes in a namespace first declared here** (`records`, `judgments`), never
  in a copied one. Where PROV-O or PAV has a term, that term is used instead.
- **Content is on a version, not on its record.** A class's shape targets the class and
  the subjects of the properties only that class's content carries; nothing about a
  version's content is required, because a source may omit any of it.
- **The crate lists every file.** A file an adapter lists is named by its path from this
  repository's root, as `ontologies/<name>/<version>/<name>.ttl` and `<name>.shapes.ttl`.

## Conventions

- Conventional commits: `feat(vocab): ...`, `fix(shapes): ...`; a change to a term or a
  shape says why in its message, never in the file.
- No comment that restates a name, a constraint or another file.
