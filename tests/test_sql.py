import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from functools import cache
from pathlib import Path

import pyoxigraph
import pytest

import sql
from contract import QUERIES, ROOT, named, query
from engines import Oxigraph, bound_to_records
from manifests import entries, expected, lens_name, row
from pods import FIXTURES, built_once, every_fixture

LENSES = sorted(named("lenses"))
UNPORTED = ROOT / "tests" / "sql-unported.txt"
PINS = ROOT / "tests" / "sql-pins.json"
VECTORS = json.loads((QUERIES / "sql-functions.json").read_text(encoding="utf-8"))
SCOPE = [path.relative_to(ROOT).as_posix() for path in sorted(QUERIES.rglob("*.rq"))
         if not path.relative_to(QUERIES).as_posix().startswith("matcher/")]


def sql_beside(relative):
    return (ROOT / relative).with_suffix(".sql")


def ported():
    return [relative for relative in SCOPE if sql_beside(relative).is_file()]


def sql_text(relative):
    return sql_beside(relative).read_text(encoding="utf-8")


def screens():
    """The text of each view's `.sql`: the screens list questions read."""
    return [sql_text(relative) for relative in ported() if relative.startswith("queries/views/")]


def list_questions():
    """Each ported question whose `.sql` takes a page size."""
    return [relative for relative in ported() if ":page_size" in sql_text(relative)]


def unported():
    return [line.strip() for line in UNPORTED.read_text(encoding="utf-8").splitlines() if line.strip()]


def pins():
    return json.loads(PINS.read_text(encoding="utf-8"))


def pin_failures(pinned, texts):
    """Each ported `.rq`, of the texts by path, whose hash is not the one pinned for it, and each pin of a query with no
    `.sql`, as what to fix."""
    found = [f"{relative}: pinned {pinned.get(relative)}, its bytes hash to {digest}; check its .sql against it, then "
             f"pin {digest}" for relative, text in texts.items()
             if pinned.get(relative) != (digest := hashlib.sha256(text).hexdigest())]
    return found + [f"{relative}: pinned, but it has no .sql" for relative in sorted(set(pinned) - set(texts))]


def final_order(text, names):
    """The indexes of the columns the query's rows are ordered by, after its last brace: its ORDER BY's leading
    conditions that are a projected variable, alone or in ASC() or DESC(); the conditions after them order only rows
    these tie. None when the query has no ORDER BY there."""
    tail = text[text.rfind("}"):]
    clause = re.search(r"ORDER\s+BY\s", tail)
    if not clause:
        return None
    rest, keys = tail[clause.end():], []
    while condition := ORDER_CONDITION.match(rest):
        variable = condition.group(1) or condition.group(2)
        if variable not in names:
            break
        keys.append(names.index(variable))
        rest = rest[condition.end():]
    return keys


ORDER_CONDITION = re.compile(r"\s*(?:(?:ASC|DESC)\s*\(\s*\?(\w+)\s*\)|\?(\w+))(?![\w(])", re.IGNORECASE)


def tied(left, right):
    """Whether an ORDER BY may put two terms either way round: one term, two blank nodes, or two literals SPARQL's `<`
    does not order, such as a value with no zone and one with a zone within fourteen hours of it, whose order is the
    engine's own."""
    if left == right:
        return True
    if left is None or right is None or left.kind != right.kind or left.kind == sql.IRI:
        return False
    if left.kind == sql.BLANK:
        return True
    try:
        return sql.sparql_compare(str(left), str(right)) in (None, 0)
    except ValueError:
        return True


def runs(found, keys):
    """The lengths of the rows' runs, in their order: a run ends where the first key column whose term differs from the
    next row's holds two terms an ORDER BY cannot put either way round."""
    lengths = [1] if found else []
    for one, other in zip(found, found[1:]):
        differing = next(((one[k], other[k]) for k in keys if one[k] != other[k]), None)
        if differing is None or tied(*differing):
            lengths[-1] += 1
        else:
            lengths.append(1)
    return lengths


def shown(names, found):
    return " ".join(f"?{name}={value}" for name, value in zip(names, found) if value is not None)


def written(found):
    return [str(value) if value is not None else "" for value in found]


def compared(names, wanted, found, keys):
    """Why rows found are not the rows wanted, as lines, or none when they are: as multisets, and, given the key columns
    of an ORDER BY, as the same runs of rows those keys order, in the same order, the rows of a run being a multiset;
    so where SPARQL leaves two rows' order to the engine, as it does for rows the keys tie, either order passes."""
    lacking, extra = Counter(wanted) - Counter(found), Counter(found) - Counter(wanted)
    lines = [*(f"missing: {shown(names, r)}" for r in sorted(lacking.elements(), key=written)),
             *(f"unexpected: {shown(names, r)}" for r in sorted(extra.elements(), key=written))]
    if lines or keys is None:
        return lines
    at = 0
    for length in runs(wanted, keys):
        run = wanted[at:at + length]
        if Counter(run) != Counter(found[at:at + length]):
            wrong = next((i for i in range(at, at + length) if found[i] not in run), at)
            return [f"the same rows in another order, from row {wrong + 1}: expected "
                    f"{' or '.join(shown(names, r) for r in run)}, found {shown(names, found[wrong])}"]
        at += length
    return lines


def oxigraph_answer(store, text, record=None):
    """What the `.rq` gives, bound to the record if one is given, as tests/engines.py binds it for a question and by the engine's own
    substitution for a CONSTRUCT, whose first group is its template: its columns and rows, or for a CONSTRUCT s, p and o
    and its triples, each term a sql.Term, and whether it is a CONSTRUCT."""
    if record is None:
        found = store.query(text)
    elif re.search(r"^\s*CONSTRUCT\b", re.sub(r"^\s*(#.*|PREFIX\s.*|BASE\s.*)$", "", text, flags=re.M), re.I):
        found = store.query(text, substitutions={pyoxigraph.Variable("record"): pyoxigraph.NamedNode(record)})
    else:
        found = store.query(bound_to_records(text, [record]))
    if isinstance(found, pyoxigraph.QueryTriples):
        return ["s", "p", "o"], [tuple(map(sql.from_oxigraph, (t.subject, t.predicate, t.object))) for t in found], True
    names = [variable.value for variable in found.variables]
    return names, [tuple(None if solution[name] is None else sql.from_oxigraph(solution[name]) for name in names)
                   for solution in found], False


@cache
def manifest_entries(fixture):
    return entries(fixture.manifest)


@cache
def pod(fixture, lens):
    return sql.screened(sql.loaded(built_once(fixture, "oxigraph", lens).store.store, f"{fixture.name} under {lens}"),
                        screens())


def as_rdflib(names, found):
    return row({name: Oxigraph._term(sql.to_oxigraph(value)) for name, value in zip(names, found) if value is not None})


def asked_answer(connection, text, records):
    """The `.sql`'s rows asked of each record in turn, `asked` holding it alone, as a runtime asks a question bound to
    it; the question is asked of the whole pod again after."""
    found = []
    try:
        for record in records:
            found += sql.answer(sql.asked(connection, [record]), text)[1]
    finally:
        sql.whole(connection)
    return found


def records_in_entries(connection):
    """Each record the pod puts in an entry, as its IRI."""
    return [lex for (lex,) in connection.execute(
        "SELECT DISTINCT t.lex FROM quad q JOIN term t ON t.id = q.s "
        "WHERE q.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#inEntry>') "
        "AND t.kind = 2 ORDER BY t.lex")]


def failures(fixture, lens, relative, text):
    """Why the `.sql` text, over the fixture's pod under the lens, does not give the rows of the `.rq` at the path: in a
    whole run, in its order when it has one; for a question bound to a record, the `.rq` bound to it and the `.sql`
    with `asked` holding it alone, for each record a manifest entry of the fixture binds and, for a list question, each
    record the pod puts in an entry; and, through the `.sql`, the rows of each manifest entry under that lens that runs
    it. A CONSTRUCT's rows are compared as a set of triples."""
    rq = query(Path(relative).relative_to("queries").as_posix())
    store = built_once(fixture, "oxigraph", lens).store.store
    connection = pod(fixture, lens)
    names, wanted, construct = oxigraph_answer(store, rq)
    try:
        columns, found = sql.answer(connection, text)
    except (sqlite3.Error, ValueError) as error:
        return [f"{fixture.name}, under {lens}, {relative}: the .sql fails: {error}"]
    if columns != names:
        return [f"{fixture.name}, under {lens}, {relative}: the .sql gives the columns {columns}, the .rq {names}"]

    def against(where, wanted, found):
        if construct:
            wanted, found, keys = sorted(set(wanted), key=written), sorted(set(found), key=written), None
        else:
            keys = final_order(rq, names)
        return [f"{fixture.name}, under {lens}, {relative}, {where}: {line}" for line in compared(names, wanted, found, keys)]

    lines = against("against the .rq", wanted, found)
    bound = set() if construct else {record for entry in manifest_entries(fixture) for record in entry.records}
    if ":page_size" in text:
        bound |= set(records_in_entries(connection))
    for record in sorted(bound):
        lines += against(f"keyed to {record}, against the .rq", oxigraph_answer(store, rq, record)[1],
                         asked_answer(connection, text, [record]))
    for entry in manifest_entries(fixture):
        if entry.query is None or Path(entry.query).resolve() != (ROOT / relative).resolve() or lens_name(entry.lens) != lens:
            continue
        pinned = expected(entry.result)
        given = asked_answer(connection, text, entry.records) if entry.records else found
        if isinstance(pinned, bool):
            got = bool(given)
            lines += [] if got == pinned else [f"{fixture.name}, {entry.name}: expected {pinned}, found {got}"]
            continue
        rows = Counter(as_rdflib(columns, value) for value in given)
        lines += [f"{fixture.name}, {entry.name}, under {lens}, {relative}: {kind}: "
                  + " ".join(f"?{name}={term}" for name, term in sorted(r))
                  for kind, side in (("missing", pinned[1] - rows), ("unexpected", rows - pinned[1]))
                  for r in sorted(side.elements(), key=sorted)]
    return lines


CASCADE = "https://ns.cascadeprotocol.org/cascade#"


def term_ids(connection, *iris):
    """Each IRI's term id, or None where the pod has no such term."""
    return [(connection.execute("SELECT id FROM term WHERE nt = ?", (f"<{iri}>",)).fetchone() or (None,))[0]
            for iri in iris]


def made(connection, nt, kind, lex, datatype=None):
    """The id of the term written nt, made if the pod has none."""
    connection.execute("INSERT OR IGNORE INTO term (nt, kind, lex, datatype) VALUES (?, ?, ?, ?)",
                       (nt, kind, lex, datatype))
    return connection.execute("SELECT id FROM term WHERE nt = ?", (nt,)).fetchone()[0]


def renamed(connection, subjects, predicates):
    """Each statement of the subjects by the predicates given one new name as its object."""
    name = made(connection, '"renamed"', sql.LITERAL, "renamed", sql.XSD + "string")
    for subject in subjects:
        for predicate in predicates:
            connection.execute("UPDATE OR IGNORE quad SET o = ? WHERE s = ? AND p = ?", (name, subject, predicate))


def keyed_changes(connection):
    """Each change a keyed run may be given over the pod, named, as a function that makes it on a copy of the pod and
    gives the terms the run puts in scope."""
    (in_entry, lead, member, agent, label, foaf_name, current, reason, values_of, member_values, *names) = term_ids(
        connection, CASCADE + "inEntry", CASCADE + "leadMember", CASCADE + "entryMember",
        "http://www.w3.org/ns/prov#agent", "http://www.w3.org/2000/01/rdf-schema#label", "http://xmlns.com/foaf/0.1/name",
        "http://purl.org/pav/hasCurrentVersion", CASCADE + "reasonCondition", CASCADE + "valuesOfMember",
        CASCADE + "memberCurrentValues", CASCADE + "drugName", CASCADE + "procedureName", CASCADE + "vaccineName")
    if in_entry is None:
        return []
    changes, entries = [], {}
    for record, entry in connection.execute("SELECT DISTINCT s, o FROM quad WHERE p = ? ORDER BY s, o", (in_entry,)):
        entries.setdefault(entry, []).append(record)
        changes.append((f"record {record} unchanged", lambda c, record=record: [record]))
    for entry, records in entries.items():
        leads = {row[0] for row in connection.execute("SELECT o FROM quad WHERE s = ? AND p = ?", (entry, lead))}
        for record in sorted(set(records) - leads) if len(records) > 1 else []:
            def moved(c, record=record, entry=entry):
                apart = made(c, f"<urn:cascade:entry:moved-{record}>", sql.IRI, f"urn:cascade:entry:moved-{record}")
                c.execute("UPDATE quad SET o = ? WHERE s = ? AND p = ? AND o = ?", (apart, record, in_entry, entry))
                c.execute("UPDATE quad SET s = ? WHERE s = ? AND p = ? AND o = ?", (apart, entry, member, record))
                c.execute("INSERT OR IGNORE INTO quad (s, p, o, g) SELECT ?, ?, ?, g FROM quad WHERE s = ? AND p = ?",
                          (apart, lead, record, entry, lead))
                return [record]
            changes.append((f"record {record} moved out of entry {entry}", moved))
    for (named,) in connection.execute("SELECT DISTINCT o FROM quad WHERE p = ?", (agent,)).fetchall() if agent else []:
        def agent_renamed(c, named=named):
            versions = [row[0] for row in c.execute("SELECT o FROM quad WHERE s = ? AND p = ?", (named, current))]
            renamed(c, [named], [label])
            renamed(c, versions, [foaf_name])
            return [named]
        changes.append((f"agent {named} renamed", agent_renamed))
    given = connection.execute(
        "SELECT DISTINCT v.o, e.s, v.s FROM quad r JOIN quad v ON v.s = r.s AND v.p = ? "
        "JOIN quad e ON e.o = r.s AND e.p = ? WHERE r.p = ?", (values_of, member_values, reason)).fetchall() \
        if None not in (reason, values_of, member_values) else []
    for record, entry, values in given:
        def reasons_dropped(c, record=record, values=values):
            c.execute("DELETE FROM quad WHERE s = ? AND p = ?", (values, reason))
            return [record]

        def entry_renamed(c, record=record, entry=entry):
            renamed(c, [entry], [name for name in names if name is not None])
            return [record]
        changes.append((f"record {record}'s reasons dropped", reasons_dropped))
        changes.append((f"entry {entry} its values give reasons for renamed, {record} in scope", entry_renamed))
    return changes


class TestSqlBesideEachQuery:
    """SQL beside each query, giving its rows on every fixture · queries/**/*.sql, queries/statements.sql, queries/sql-functions.json

    A runtime answers a query from SQLite through the `.sql` beside its `.rq`, over the tables queries/statements.sql
    makes, calling the six functions whose vectors are in queries/sql-functions.json. The `.rq` stays the definition: each
    `.sql` is held to its rows on every fixture, under each lens, and to the rows the fixtures' manifests pin for it. A
    view's `.sql` makes and fills its screen, the tables a list question reads a page of, and is held to its CONSTRUCT's
    triples; a list question is held to its whole list a page at a time. A query outside queries/matcher/ with no `.sql`
    yet is named in tests/sql-unported.txt.
    """

    class TestGivenAnyFixture:
        @every_fixture
        def test_gives_through_each_sql_the_rows_of_its_rq_and_of_each_manifest_entry_under_each_lens(self, fixture):
            """gives through each `.sql` the rows its `.rq` gives, and those each manifest entry running it pins, under each lens

            The fixture is built on Oxigraph under each lens and loaded into SQLite as tests/sql.py loads it. Each `.sql`
            beside a `.rq` outside queries/matcher/ gives the `.rq`'s columns and the same multiset of rows, each term
            compared in N-Triples form, in the same order where the `.rq` ends with an ORDER BY, and a CONSTRUCT's `.sql`
            the same set of triples; a manifest entry of the fixture that runs the `.rq` under that lens gives its pinned
            rows through the `.sql` too.
            """
            found = [line for lens in LENSES for relative in ported()
                     for line in failures(fixture, lens, relative, sql.statement(sql_text(relative)))]
            assert not found, "\n".join(found)

        @every_fixture
        def test_gives_each_list_question_a_page_at_a_time_as_the_whole_list_under_each_lens(self, fixture):
            """gives each list question's rows a page at a time, pages of one and of two entries joined in order, as its whole list

            Each `.sql` that takes `:page_size` gives a `page_key` last, the key of the row's entry, and is asked a page
            of one entry, then of two, at a time, each after the last row's key of the page before; the pages joined
            give the rows and keys the whole list gives, in its order, under each lens. No page holds more entries
            than its size, or splits an entry's rows.
            """
            found = []
            for lens in LENSES:
                connection = pod(fixture, lens)
                for relative in list_questions():
                    text = sql_text(relative)
                    whole = sql.keyed(connection, text)[1]
                    keys = [key for _, key in whole]
                    if None in keys:
                        found.append(f"{fixture.name}, under {lens}, {relative}: it gives no page_key")
                        continue
                    if keys != sorted(keys):
                        found.append(f"{fixture.name}, under {lens}, {relative}: its page keys are not in order")
                    for size in (1, 2):
                        try:
                            joined = sql.paged(connection, text, size)
                        except ValueError as error:
                            found.append(f"{fixture.name}, under {lens}, {relative}: {error}")
                            continue
                        if joined != whole:
                            at = next((i for i, (a, b) in enumerate(zip(joined, whole)) if a != b),
                                      min(len(joined), len(whole)))
                            found.append(f"{fixture.name}, under {lens}, {relative}: pages of {size} give {len(joined)} "
                                         f"rows, the whole list {len(whole)}, the first apart at row {at + 1}")
            assert not found, "\n".join(found)

        @every_fixture
        def test_fills_each_screen_keyed_to_what_changed_as_a_whole_fill_does_under_each_lens(self, fixture):
            """fills each screen, keyed to what a change touched, as a whole fill of the changed pod does, under each lens

            Over each fixture's screens, filled whole, each change a keyed run may be given is made to the pod's
            statements and the screens filled again with scope holding what it touched: each record in an entry,
            unchanged; each record but the lead of an entry of two or more, moved to an entry of its own; each agent,
            renamed; each record whose values give a reason condition, its reasons dropped; and each entry those values
            are of, renamed, the record in scope. Every screen table then holds the rows a whole fill of the changed
            pod gives from empty tables.
            """
            found = []
            for lens in LENSES:
                connection = pod(fixture, lens)
                for name, change in keyed_changes(connection):
                    changed = sql.copied(connection)
                    touched = change(changed)
                    keyed = sql.copied(changed)
                    keyed.execute("DELETE FROM scope")
                    keyed.executemany("INSERT INTO scope (term) VALUES (?)", [(term,) for term in touched])
                    sql.refilled(keyed, screens())
                    whole = sql.copied(changed)
                    for table in sql.screen_tables(whole):
                        whole.execute(f"DELETE FROM {table}")
                    sql.refilled(sql.whole(whole), screens())
                    kept, wanted = sql.screen_tables(keyed), sql.screen_tables(whole)
                    found += [f"{fixture.name}, under {lens}, {name}: {table} holds {sorted(set(kept[table]) - set(rows))} "
                              f"a whole fill does not, and lacks {sorted(set(rows) - set(kept[table]))}"
                              for table, rows in wanted.items() if kept[table] != rows]
            assert not found, "\n".join(found)

    class TestGivenTheQueries:
        def test_leaves_no_query_without_a_sql_but_those_tests_sql_unported_names(self):
            """leaves no query outside queries/matcher/ without a `.sql`, but those tests/sql-unported.txt names, and that names no other

            A `.rq` outside queries/matcher/ with no `.sql` beside it that the list does not name fails; so does a name
            on the list that is no such `.rq`, or one that has its `.sql`, and a `.sql` with no `.rq` beside it.
            """
            listed, done = set(unported()), set(ported())
            stray = sorted(path.relative_to(ROOT).as_posix() for path in QUERIES.rglob("*.sql")
                           if path != sql.SCHEMA and not path.with_suffix(".rq").is_file())
            assert sorted(set(SCOPE) - done - listed) == []
            assert sorted(listed - set(SCOPE)) == []
            assert sorted(listed & done) == []
            assert stray == []
            assert unported() == sorted(listed)

        def test_pins_each_ported_rq_by_the_hash_its_sql_was_checked_against(self):
            """pins each ported `.rq` by the hash of the bytes its `.sql` was last checked against

            tests/sql-pins.json holds, for each `.rq` with a `.sql`, the SHA-256 of its bytes. A `.rq` whose bytes hash to
            another, so changed since its `.sql` was checked, fails, even where no fixture's rows tell the two apart; so
            does a pin of a query with no `.sql`.
            """
            assert pin_failures(pins(), {relative: (ROOT / relative).read_bytes() for relative in ported()}) == []

        def test_runs_on_an_sqlite_no_older_than_the_schema_needs(self, record_property):
            """runs on an SQLite no older than the version queries/statements.sql names, and records the one it ran on"""
            record_property("sqlite_version", sqlite3.sqlite_version)
            assert sqlite3.sqlite_version_info >= sql.MINIMUM_VERSION, sqlite3.sqlite_version

        @pytest.mark.parametrize("view, fixture", [("conditions", "conditions-view"), ("lab-results", "lab-results-view")])
        def test_refuses_to_fill_a_screen_whose_view_the_layout_places_at_two_addresses(self, view, fixture):
            """refuses to fill a screen whose view the pod's layout places at two addresses

            The fixture's pod, its layout given a second address for the view, is filled whole from empty screen
            tables; the fill fails rather than name the view's entries after either address.
            """
            connection = sql.copied(pod(next(f for f in FIXTURES if f.name == fixture), "everyday"))
            registered = connection.execute(
                "SELECT w.s, w.g FROM quad w JOIN term p ON p.id = w.p JOIN term o ON o.id = w.o "
                "WHERE p.nt = ? AND o.nt = ?", (f"<{CASCADE}writtenByQueryPath>", f'"views/{view}.rq"')).fetchone()
            elsewhere = made(connection, "<https://pod.example/elsewhere.ttl>", sql.IRI, "https://pod.example/elsewhere.ttl")
            instance = made(connection, "<http://www.w3.org/ns/solid/terms#instance>", sql.IRI,
                            "http://www.w3.org/ns/solid/terms#instance")
            connection.execute("INSERT INTO quad (s, p, o, g) VALUES (?, ?, ?, ?)",
                               (registered[0], instance, elsewhere, registered[1]))
            for table in sql.screen_tables(connection):
                connection.execute(f"DELETE FROM {table}")
            with pytest.raises(sqlite3.IntegrityError):
                sql.refilled(sql.whole(connection), screens())

        def test_orders_strings_times_and_counts_by_their_paging_keys_as_oxigraph_orders_them(self):
            """orders strings, times and counts by the keys queries/statements.sql's paging convention gives, as Oxigraph does

            Strings, xsd:dateTime and xsd:date values with and without a zone, and integers of either sign, each given
            the ascending and the descending key the convention writes, a time from its term's `instant` and a count
            from the SQL integer, sort by those keys as Oxigraph's ORDER BY and ORDER BY DESC sort them.
            """
            connection = sqlite3.connect(":memory:")
            turned = "hex(:text)"
            for digit, letter in zip("0123456789ABCDEF", "ponmlkjihgfedcba"):
                turned = f"replace({turned}, '{digit}', '{letter}')"
            nines = ":digits"
            for digit in "0123456789":
                nines = f"replace({nines}, '{digit}', '{chr(ord('a') + int(digit))}')"
            for digit in "0123456789":
                nines = f"replace({nines}, '{chr(ord('a') + int(digit))}', '{9 - int(digit)}')"

            def keys(text):
                return connection.execute(f"SELECT '3' || hex(:text) || '.', {turned} || '~'", {"text": text}).fetchone()

            def count_text(value):
                digits = f"{abs(value):019d}"
                if value >= 0:
                    return "p" + digits
                return "n" + connection.execute(f"SELECT {nines}", {"digits": digits}).fetchone()[0]

            store = pyoxigraph.Store()
            date_time, date, integer = (XSD + name for name in ("dateTime", "date", "integer"))
            cases = [
                [sql.Term(sql.LITERAL, value, XSD + "string") for value in ("", "a", "ab", "b", "B", "\u00e9", "Z", "a b")],
                [sql.Term(sql.LITERAL, value, date_time) for value in (
                    "2025-01-01T10:00:00+05:00", "2025-01-01T06:00:00Z", "2025-01-01T05:30:00Z", "2024-12-31T23:00:00-08:00",
                    "2025-01-01T05:00:00.5Z")],
                [sql.Term(sql.LITERAL, value, date) for value in ("2024-06-01", "2023-01-01Z", "2024-06-02+13:00")],
                [sql.Term(sql.LITERAL, str(value), integer) for value in (0, 7, -7, 12, -12, 100, -100, 9, -1)],
            ]
            for values in cases:
                def text(term):
                    if term.datatype == integer:
                        return count_text(int(term.value))
                    if term.datatype in (date_time, date):
                        return sql.instant_key(term)
                    return term.value
                listed = " ".join(str(term) for term in values)
                for direction, at in (("", 0), ("DESC", 1)):
                    oxigraph = [sql.from_oxigraph(solution["x"]) for solution in store.query(
                        f"SELECT ?x WHERE {{ VALUES ?x {{ {listed} }} }} ORDER BY {direction}(?x)")]
                    by_key = sorted(values, key=lambda term: keys(text(term))[at])
                    assert by_key == oxigraph, (direction, [str(term) for term in by_key])

    class TestGivenEachFunction:
        @pytest.mark.parametrize("name", sorted(VECTORS["functions"]))
        def test_gives_each_vectors_output(self, name):
            """gives each vector's output from its input, in Python, and refuses each input a vector marks refused

            Each vector of the function in queries/sql-functions.json is given to tests/sql.py's function of that name;
            each whose output differs fails, and so does each marked refused that the function does not refuse with
            ValueError.
            """
            function = sql.FUNCTIONS.get(name)
            vectors = VECTORS["functions"][name]["vectors"]
            found = [(vector["input"], "refused" if "refused" in vector else vector["output"], outcome(function, vector))
                     for vector in vectors]
            assert [wrong for wrong in found if wrong[1] != wrong[2]] == []

        @pytest.mark.parametrize("name", sorted(VECTORS["functions"]))
        def test_has_vectors_whose_outputs_oxigraph_gives_but_where_they_mark_its_own(self, name):
            """has vectors whose outputs Oxigraph's SPARQL gives, but where a vector marks Oxigraph's own answer

            Each vector's input, but one marked refused, is given to the SPARQL the function stands for, on Oxigraph,
            as literals; each whose output is not Oxigraph's, an unbound answer as null, fails. A vector whose output is
            SPARQL 1.1's where Oxigraph gives another marks Oxigraph's answer and why, and fails if Oxigraph gives any
            other. So the vectors are SPARQL's answers, not the Python function's.
            """
            vectors = [vector for vector in VECTORS["functions"][name]["vectors"] if "refused" not in vector]
            found = [(vector["input"], vector.get("oxigraph", vector["output"]), in_sparql(name, vector["input"]))
                     for vector in vectors]
            assert [wrong for wrong in found if wrong[1] != wrong[2]] == []

        def test_refuses_exactly_the_unassigned_characters_oxigraph_lower_cases(self):
            """refuses exactly the characters Python's Unicode does not assign and Oxigraph's lower-cases

            Every unassigned character of the first two planes is lower-cased by Oxigraph's LCASE and by tests/sql.py's
            sparql_lcase; the characters on which Oxigraph's answer is another than the character's own are those
            sparql_lcase refuses, and no other.
            """
            store = pyoxigraph.Store()
            unassigned = [c for c in map(chr, range(0x20000)) if unicodedata.category(c) == "Cn"
                          and not 0xFDD0 <= ord(c) <= 0xFDEF and ord(c) & 0xFFFE != 0xFFFE]
            values = " ".join(f'"{c}"' for c in unassigned)
            lowered = {solution["t"].value for solution in store.query(
                f"SELECT ?t WHERE {{ VALUES ?t {{ {values} }} FILTER (LCASE(?t) != ?t) }}")}
            refused = {c for c in unassigned if outcome(sql.sparql_lcase, {"input": [c]}) == "refused"}
            assert refused == lowered
            assert len(lowered) == 55

        def test_binds_a_record_in_a_construct_through_the_engine(self):
            """binds a record in a CONSTRUCT through the engine, not by a VALUES block opening the template

            A CONSTRUCT's first group is its template, where a VALUES block is a syntax error: oxigraph_answer binds the
            record as the engine does, so a CONSTRUCT gives the triples of that record alone.
            """
            store = pyoxigraph.Store()
            for record, text in (("urn:a", "1"), ("urn:b", "2")):
                store.add(pyoxigraph.Quad(pyoxigraph.NamedNode(record), pyoxigraph.NamedNode("urn:p"),
                                          pyoxigraph.Literal(text)))
            text = "CONSTRUCT { ?record <urn:q> ?o } WHERE { ?record <urn:p> ?o }"
            assert [row[0].value for row in oxigraph_answer(store, text, "urn:a")[1]] == ["urn:a"]


def outcome(function, vector):
    if function is None:
        return "no such function"
    try:
        return function(*vector["input"])
    except ValueError:
        return "refused"


XSD = "http://www.w3.org/2001/XMLSchema#"
SPARQL = {
    "sparql_replace": lambda *arguments: f"REPLACE({', '.join(f'?a{i}' for i in range(len(arguments)))})",
    "sparql_sha256": lambda _: "SHA256(?a0)",
    "sparql_encode_for_uri": lambda _: "ENCODE_FOR_URI(?a0)",
    "sparql_lcase": lambda _: "LCASE(?a0)",
}


def in_sparql(name, arguments):
    """What Oxigraph gives for the SPARQL a function stands for, as the function gives it, or None where it is unbound."""
    store = pyoxigraph.Store()
    if name == "sparql_compare":
        text = (f"SELECT (IF(?a < ?b, -1, IF(?a = ?b, 0, IF(?a > ?b, 1, 1/0))) AS ?r) "
                f"WHERE {{ VALUES (?a ?b) {{ ({arguments[0]} {arguments[1]}) }} }}")
        found = list(store.query(text))[0]["r"]
        return None if found is None else int(found.value)
    if name == "sparql_decimal":
        operator, *operands = arguments
        expression = "FLOOR(?a1)" if operator == "floor" else f"?a1 {operator} ?a2"
        values = [None, *(pyoxigraph.Literal(value, datatype=pyoxigraph.NamedNode(XSD + "decimal")) for value in operands)]
    else:
        expression = SPARQL[name](*arguments)
        values = [pyoxigraph.Literal(value) for value in arguments]
    bound = {pyoxigraph.Variable(f"a{i}"): value for i, value in enumerate(values) if value is not None}
    projected = " ".join(f"?{variable.value}" for variable in bound)
    found = list(store.query(f"SELECT {projected} ({expression} AS ?r) WHERE {{}}", substitutions=bound))[0]["r"]
    return None if found is None else found.value


class TestTheSqlCheck:
    """Checks of the SQL check · tests/test_sql.py, tests/sql.py

    The check of each `.sql` is itself checked: given a `.sql` it should refuse, or a `.rq` changed since its pin, it says
    which fixture, query and row, or which pin.
    """

    JUDGMENTS = "queries/questions/pod/How many judgments count.rq"
    PINNED = next(fixture for fixture in FIXTURES if fixture.name == "which-judgments-count")
    KEYED = next(fixture for fixture in FIXTURES
                 if fixture.name == "matcher-same-business-identifier-and-test-code-within-one-organization-bound-per-side")
    EXPOSURE = "queries/derivations/medication-exposure-periods.rq"
    ZERO_SUPPLY = next(fixture for fixture in FIXTURES if fixture.name == "exposure-from-a-supply-of-zero")

    @pytest.mark.xdist_group(PINNED.name)
    def test_reports_the_fixture_query_and_row_of_a_sql_that_drops_a_value_from_a_row(self):
        """reports the fixture, the query and the row, for a `.sql` that drops one column's value from one row

        `How many judgments count.sql` is wrapped to leave the justification unbound on the row whose justification is
        `cascade:SameMappedCode`, which `which-judgments-count` pins under everyday; the check of it over that fixture
        names the fixture, the query, the row the `.rq` gives and the manifest pins, and the row the `.sql` gives.
        """
        text = sql_beside(self.JUDGMENTS).read_text(encoding="utf-8")
        mapped = "<https://ns.cascadeprotocol.org/cascade#SameMappedCode>"
        broken = (f"SELECT verdict, CASE WHEN justification = '{mapped}' THEN NULL ELSE justification END AS justification, "
                  f"madeBy, judgments FROM ({text})")
        found = "\n".join(failures(self.PINNED, "everyday", self.JUDGMENTS, broken))
        row_shown = f"?justification={mapped}"
        assert f"which-judgments-count, under everyday, {self.JUDGMENTS}, against the .rq: missing: " in found
        assert re.search(rf"against the \.rq: missing: [^\n]*{re.escape(row_shown)}", found)
        assert re.search(rf"how-many-count-everyday, under everyday, {re.escape(self.JUDGMENTS)}: missing: [^\n]*"
                         rf"{re.escape(row_shown)}", found)
        assert re.search(r"unexpected: \?verdict=<https://ns.cascadeprotocol.org/cascade#Same> "
                         r"\?madeBy=<http://www.w3.org/ns/prov#SoftwareAgent> \?judgments=\"1\"", found)

    @pytest.mark.xdist_group(KEYED.name)
    def test_reports_a_sql_whose_keyed_run_gives_other_rows_than_the_rq_bound_to_the_record(self):
        """reports a `.sql` that gives its `.rq`'s rows asked of the whole pod but not asked of a record an entry binds

        `How many judgments count.sql`, wrapped to give no row when `asked` holds one record, is checked over a fixture
        whose manifest's entries bind records; the check names each of those records with the `.rq`'s row the bound
        `.sql` misses, and finds nothing wrong with the whole run.
        """
        text = sql_beside(self.JUDGMENTS).read_text(encoding="utf-8")
        found = failures(self.KEYED, "everyday", self.JUDGMENTS,
                         f"SELECT * FROM ({text}) WHERE (SELECT count(*) FROM asked) != 1")
        records = {record for entry in manifest_entries(self.KEYED) for record in entry.records}
        assert records and not [line for line in found if f"{self.JUDGMENTS}, against the .rq: " in line]
        assert {record for record in records
                if any(f"keyed to {record}, against the .rq: missing: " in line for line in found)} == records

    @pytest.mark.xdist_group(ZERO_SUPPLY.name)
    def test_reports_each_triple_a_construct_sql_misses_and_each_it_adds_once_however_often_it_gives_it(self):
        """reports each triple a CONSTRUCT's `.sql` misses, and each it gives that the `.rq` does not, once however often

        A `.sql` beside medication-exposure-periods.rq that gives one stray triple twice, over
        exposure-from-a-supply-of-zero under everyday, is reported missing the exposure start the `.rq` makes for each
        record, and giving the stray triple, once.
        """
        stray = "SELECT '<urn:x:a>' AS s, '<urn:x:b>' AS p, '<urn:x:c>' AS o"
        found = failures(self.ZERO_SUPPLY, "everyday", self.EXPOSURE, f"{stray} UNION ALL {stray}")
        start = "<https://ns.cascadeprotocol.org/cascade#medicationExposureStart>"
        assert [line for line in found if "unexpected" in line] == [
            f"exposure-from-a-supply-of-zero, under everyday, {self.EXPOSURE}, against the .rq: "
            "unexpected: ?s=<urn:x:a> ?p=<urn:x:b> ?o=<urn:x:c>"]
        assert [record for record in ("months", "years")
                if sum(f"missing: ?s=<urn:x:{record}> ?p={start}" in line for line in found) == 1] == ["months", "years"]

    def test_compares_rows_an_order_by_ties_as_a_multiset_and_the_runs_it_orders_in_order(self):
        """compares rows an ORDER BY ties as a multiset, and the runs of rows it orders in their order

        Rows ordered by a dateTime pass in either order where SPARQL's `<` does not order them, a value with no zone
        and one with a zone within fourteen hours of it, and where they hold one term; rows it does order fail turned
        round, naming the row. The key columns are the ORDER BY's leading projected variables.
        """
        def at(value):
            return (sql.Term(sql.LITERAL, value, XSD + "dateTime"),)
        unzoned, zoned, later = at("2024-01-01T10:00:00"), at("2024-01-01T05:00:00-08:00"), at("2024-01-03T00:00:00Z")
        assert compared(["t"], [unzoned, zoned, later], [zoned, unzoned, later], [0]) == []
        assert compared(["t"], [later, later], [later, later], [0]) == []
        assert compared(["t"], [unzoned, later], [unzoned, later], [0]) == []
        assert compared(["t"], [unzoned, later], [later, unzoned], [0]) == [
            f"the same rows in another order, from row 1: expected ?t={unzoned[0]}, found ?t={later[0]}"]
        assert final_order("SELECT ?a ?b ?c WHERE { } ORDER BY DESC(?b) ?a STR(?c) ?c", ["a", "b", "c"]) == [1, 0]
        assert final_order("SELECT ?a WHERE { } ORDER BY ?z ?a", ["a"]) == []
        assert final_order("SELECT ?a WHERE { } GROUP BY ?a", ["a"]) is None

    def test_loads_only_the_named_graphs_of_the_default_graph_and_refuses_a_default_graph_they_do_not_make(self):
        """loads only the named graphs a store's default graph holds, and refuses a store whose default graph they do not make

        A named graph with a statement outside the default graph, as a table version's rows are, is left out of the
        pod; a store whose default graph has a statement no named graph it holds has is refused.
        """
        def quad(subject, graph):
            return pyoxigraph.Quad(pyoxigraph.NamedNode(subject), pyoxigraph.NamedNode("urn:x:p"),
                                   pyoxigraph.NamedNode("urn:x:o"), graph)
        store = pyoxigraph.Store()
        store.extend([quad("urn:x:kept", pyoxigraph.NamedNode("urn:x:file")), quad("urn:x:kept", pyoxigraph.DefaultGraph()),
                      quad("urn:x:row", pyoxigraph.NamedNode("urn:x:rows"))])
        held = sorted(sql.loaded(store, "test").execute(
            "SELECT s.nt, g.nt FROM quad JOIN term s ON s.id = quad.s JOIN term g ON g.id = quad.g"))
        assert held == [("<urn:x:kept>", "<urn:x:file>")]
        store.add(quad("urn:x:alone", pyoxigraph.DefaultGraph()))
        with pytest.raises(ValueError, match="in no named graph"):
            sql.loaded(store, "test")

    def test_reports_a_ported_rq_whose_bytes_changed_without_its_pin(self):
        """reports a ported `.rq` whose bytes changed since its pin, with the hash to pin once its `.sql` is checked

        The bytes of `How many judgments count.rq`, with a comment added, are checked against tests/sql-pins.json; the
        check names the query and the new hash.
        """
        changed = (ROOT / self.JUDGMENTS).read_bytes() + b"# changed\n"
        digest = hashlib.sha256(changed).hexdigest()
        found = pin_failures({self.JUDGMENTS: pins()[self.JUDGMENTS]}, {self.JUDGMENTS: changed})
        assert len(found) == 1 and found[0].startswith(f"{self.JUDGMENTS}: ") and digest in found[0]

    def test_refuses_pages_that_ignore_the_key_to_continue_after_or_the_page_size(self):
        """refuses a list question whose pages ignore the key to continue after, or the page size

        Over three keyed rows, a `.sql` that keeps to both parameters is asked in pages of two and gives the three in
        order; one that ignores `:after` gives a second page that is not after the first, and one that ignores
        `:page_size` a page of three; each is refused, naming the page.
        """
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE listed (k TEXT)")
        connection.executemany("INSERT INTO listed VALUES (?)", [("a",), ("b",), ("c",)])
        rows = "SELECT '\"' || k || '\"' AS shown, k AS page_key FROM listed"
        kept = f"{rows} WHERE k > coalesce(:after, '') ORDER BY k LIMIT coalesce(:page_size, -1)"
        assert [key for _, key in sql.paged(connection, kept, 2)] == ["a", "b", "c"]
        assert sql.answer(connection, kept, 2, "a") == (["shown"], [(sql.Term(sql.LITERAL, "b", XSD + "string"),),
                                                                    (sql.Term(sql.LITERAL, "c", XSD + "string"),)])
        for text in (f"{rows} ORDER BY k LIMIT coalesce(:page_size, -1)",
                     f"{rows} WHERE k > coalesce(:after, '') ORDER BY k"):
            with pytest.raises(ValueError, match="a page of 2 after"):
                sql.paged(connection, text, 2)
