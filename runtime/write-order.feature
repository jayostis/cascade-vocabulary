Feature: Write order

  Rule: W1. Content-addressed files are written first, and the revision and import files last
    A step that stops partway then leaves nothing that passes for finished. The views, the type index and the manifest
    may be stale after a crash, and are rebuilt. A matcher run writes its judgments before the reference descriptions it
    writes, and an open writes the versions it adopts oldest first: an open that stops partway leaves the pod at its old
    versions, and the next open does it again, M9 skipping what was written.

    No example can show this rule, because an example only sees finished steps. Each runtime tests it itself.
