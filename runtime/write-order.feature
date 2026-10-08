Feature: Write order

  Rule: W1. Content-addressed files are written first, and the revision and import files last
    A step that stops partway then leaves nothing that passes for finished. The views, the type index and the manifest
    may be stale after a crash, and are rebuilt. A matcher run writes its judgments before the reference descriptions it
    writes, and an open writes the versions it adopts oldest first: an open that stops partway leaves the pod naming a
    version on the line no later than the adopted one, and the next open adopts from there, M9 skipping the judgments
    written and writing the descriptions still lacking.

    No example can show this rule, because an example only sees finished steps. Each runtime tests it itself.
