Feature: Currency
  Which revision of a record is current, and which member of an entry leads it: derived, never stored, by the ladder
  decisions/currency.md rules, over the two clocks each revision carries, the source's change time and when the source
  was observed, and the person's Befores and Erroneous judgments.

  Each pod starts empty, at https://pod.example/, with Ada as its subject (scripted-input/people.ttl). Ada imports
  Apple Health exports of four allergies, each stamped by its source (pav:lastUpdateOn): first-export, all stamped
  1 December 2025; new-content, the peanut allergy inactive, stamped 5 January; stale-copy, exported on 8 January, a
  copy of the peanut allergy active as its source stamped it on 4 January: an older state, observed later.

  Rule: C1. A revision carries when its source was observed saying its state
    decisions/currency.md, row "two clocks". Its cascade:observedAsOf is the first there is of its document's
    cascade:answeredAsOf, the document's pav:retrievedOn, the source's own change time it carries as pav:lastUpdateOn,
    and the start of the act that generated it; for an entry, the session's start. It is one of the revision's own
    triples (N4), beside prov:generatedAtTime, when the pod wrote it.

    Example: the peanut allergy's revision was observed when its export's document was retrieved
      Given a new pod for Ada on 2026-01-01 at 09:00
      When the export "first-export" is imported on 2026-01-02 at 10:00
      When the query is:
        """
        SELECT ?retrieved ?observed WHERE {
          ?revision cascade:revisionOf ?record ; cascade:observedAsOf ?observed ; prov:wasDerivedFrom ?document .
          ?document pav:retrievedOn ?retrieved .
          FILTER (?record = <urn:uuid:beaefb13-def8-8f7f-882d-eff4a1ee11d9>)
        }
        """
      Then it answers:
        | retrieved                            | observed                             |
        | "2026-01-02T10:00:00Z"^^xsd:dateTime | "2026-01-02T10:00:00Z"^^xsd:dateTime |

  Rule: C2. A record's current revision is the ladder's pick
    decisions/currency.md, rows "current" and "heads", and its ladder. Of the record's revisions, whatever revises
    what: remove each an Erroneous names; remove each a Before places before another still present,
    unless Befores form a cycle (C4); keep those at the latest source change time with those carrying none; of those,
    the greatest cascade:observedAsOf, but between two imports from documents reached by one path, the one whose act's
    snapshot descends from the other's; then the least IRI. queries/derivations/current-revisions.rq and the
    derivations before it derive it, and a record's current version is its current revision's. A record with nothing
    left has no current state and is in no view.

    Example: a copy of an older state, observed later, does not undo the newer one
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      When the export "stale-copy" is imported on 2026-01-08 at 10:00
      Then allergy "Peanut" has these revisions:
        | arrived             | version | clinical status | after               |
        | 2026-01-02 at 10:00 | 1       | active          |                     |
        | 2026-01-06 at 10:00 | 2       | inactive        | 2026-01-02 at 10:00 |
        | 2026-01-08 at 10:00 | 1       | active          | 2026-01-06 at 10:00 |
      And these records have:
        | record           | field   | value |
        | allergy "Peanut" | version | 2     |

  Rule: C3. A person's Before outranks every clock
    decisions/currency.md, row "Before". A cascade:Judgment with the verdict cascade:Before, by a person, of two
    revisions of one record or of two records a Same joins, names the one it places before the other as
    cascade:earlierMember. The ladder removes the earlier before the clocks rank, so they cannot re-admit it.

    Example: Ada places the newer state before the older, and the older is current
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      When Ada files the judgment "new-content-before-first-export" on 2026-01-10 at 09:00
      Then these records have:
        | record           | field   | value |
        | allergy "Peanut" | version | 1     |

  Rule: C4. Befores that form a cycle remove nothing, and the record is listed for review
    decisions/currency.md, rows "Before" and "review page". Two Befores ordering two revisions both ways, directly or
    through others, remove neither, and queries/questions/record/What needs review.rq lists each such Before, as
    tests/fixtures/a-cycle-of-befores-removes-nothing shows.

    Example: two Befores ordering the two states both ways leave the clocks' pick
      Given a new pod for Ada on 2026-01-01 at 09:00
      And the export "first-export" is imported on 2026-01-02 at 10:00
      And the export "new-content" is imported on 2026-01-06 at 10:00
      And Ada files the judgment "new-content-before-first-export" on 2026-01-10 at 09:00
      When Ada files the judgment "first-export-before-new-content" on 2026-01-11 at 09:00
      Then these records have:
        | record           | field   | value |
        | allergy "Peanut" | version | 2     |

  Rule: C5. The review page lists every pick the source's change time did not decide
    decisions/currency.md, row "review page". queries/questions/record/What needs review.rq lists each record whose
    current revision was picked from candidates at other versions by the observation time ("observed later") or the
    least IRI ("no basis"), beside the state shown and each state not shown, but not a pick between two live pulls of
    one source whose snapshots ancestry orders: documents with a pav:retrievedOn and no cascade:answeredAsOf, naming
    one transmitter agent or none. Two exports, a file and a pull, or two transmitters are two paths, which ancestry
    never orders.

    No example shows this rule: every export the scripted input holds is stamped by its source, so its change time
    decides. The fixtures under tests/fixtures/ named for ancestry, two writers and a tie show it.

  Rule: C6. An entry shows every member, its lead's first
    decisions/currency.md, row "entry on a Same group", and its lead. An entry's cascade:leadMember is a record the
    person entered when it holds one; otherwise the member left once a Before outside a cycle has placed the
    others' current revisions before it, ranked as the ladder's last three steps rank revisions. A view takes the
    entry's name and codes from its lead, and holds each member's current values as a node of its own
    (cascade:memberCurrentValues), named after the entry and the member (N13), which names the member it came from
    (cascade:valuesOfMember); queries/questions/entry/What it shows.rq lists them from the view alone, the lead's first.
    No merged record is stored, and no triple of a version is copied into a view, so no count over the union sees one
    twice.

    No example here shows this rule: no scripted input but a kit's joins a record the person entered to an imported
    one. Priya's kit shows it, P15 and P11, and tests/fixtures/the-lead-member and allergies-view show the rest.

  Rule: C7. An act rebuilds only what it reached, and the views it leaves are those of a build of the whole pod
    decisions/currency.md, row "view", and decisions/performance.md, row "current per act, incrementally". After an
    act, the derived state, the views and the labels are those a build of the whole pod gives. A runtime need build
    again only the records the act wrote a revision of and those its judgments, retractions, assertions and findings
    reach through what each names, retracts, replaces, asserts or targets: a revision's record, each record an act
    a judgment names revised, and each record one of whose versions names what a judgment names, as an About's profile; closed
    over every record currently the same as one, before the act or by a judgment it wrote, each a version of one names
    or whose version names one, each with one's source record id once two servers are judged the same, and each member
    of a matcher Same over an older table version with one among its members, which M7 joins by their current versions.
    An act that changes the current version of a reference series the pod described before, a migration of the rule
    list versions (N15), an open, which gives the pod the tables it is read with, and a change to the trusted makers
    change what every record's judgments count, and are built whole; a runtime may build any step whole. The
    manifest's build activity used the writer's last snapshot (prov:used): a view whose manifest names another
    snapshot than the writer's last is stale, and is built again.

    No example shows this rule: an example reads a dataset built whole from the files its story wrote, so a build in
    part and a build whole give it the same rows. Each runtime tests it itself, replaying every kit and building the
    pod both ways after each step.
