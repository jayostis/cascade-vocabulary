Feature: Write order

  Rule: W1. Content-addressed files are written first, and the revision and import files last
    A step that stops partway then leaves nothing that passes for finished. The views, the type index and the manifest
    may be stale after a crash, and are rebuilt.

    No example can show this rule, because an example only sees finished steps. Each runtime tests it itself.
