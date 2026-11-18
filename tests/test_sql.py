import hashlib
import json
import re
import sqlite3
from collections import Counter
from functools import cache
from pathlib import Path

import pyoxigraph
import pytest

import sql
from contract import QUERIES, ROOT, named, query
from engines import Oxigraph
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


def final_order(text):
    """Whether the query's rows are ordered: an ORDER BY after its last brace."""
    return "ORDER BY" in text[text.rfind("}"):]


def shown(names, found):
    return " ".join(f"?{name}={value}" for name, value in zip(names, found) if value is not None)


def written(found):
    return [str(value) if value is not None else "" for value in found]


def compared(names, wanted, found, ordered):
    """Why rows found are not the rows wanted, as lines, or none when they are: as multisets, and as lists when
    ordered."""
    lacking, extra = Counter(wanted) - Counter(found), Counter(found) - Counter(wanted)
    lines = [*(f"missing: {shown(names, r)}" for r in sorted(lacking.elements(), key=written)),
             *(f"unexpected: {shown(names, r)}" for r in sorted(extra.elements(), key=written))]
    if not lines and ordered and wanted != found:
        at = next(i for i, (one, other) in enumerate(zip(wanted, found)) if one != other)
        lines = [f"the same rows in another order, from row {at + 1}: expected {shown(names, wanted[at])}, "
                 f"found {shown(names, found[at])}"]
    return lines


def oxigraph_answer(store, text):
    """What the `.rq` gives: its columns and rows, or for a CONSTRUCT s, p and o and its triples, each term a sql.Term,
    and whether it is a CONSTRUCT."""
    found = store.query(text)
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
    store = built_once(fixture, "oxigraph", lens).store.store
    quads = sorted(str(q) for q in store.quads_for_pattern(None, None, None, None)
                   if not isinstance(q.graph_name, pyoxigraph.DefaultGraph))
    return sql.loaded(store, hashlib.sha256("\n".join(quads).encode("utf-8")).hexdigest())


def as_rdflib(names, found):
    return row({name: Oxigraph._term(sql.to_oxigraph(value)) for name, value in zip(names, found) if value is not None})


def failures(fixture, lens, relative, text):
    """Why the `.sql` text, over the fixture's pod under the lens, does not give the rows of the `.rq` at the path, in
    its order when it has one, and of each manifest entry under that lens that runs it; a CONSTRUCT's as a set of
    triples."""
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
    lines = [f"{fixture.name}, under {lens}, {relative}, against the .rq: {line}"
             for line in compared(names, sorted(set(wanted), key=written) if construct else wanted,
                                  sorted(set(found), key=written) if construct else found,
                                  not construct and final_order(rq))]
    for entry in manifest_entries(fixture):
        if entry.query is None or Path(entry.query).resolve() != (ROOT / relative).resolve() or lens_name(entry.lens) != lens:
            continue
        pinned = expected(entry.result)
        if isinstance(pinned, bool):
            got = bool(found)
            lines += [] if got == pinned else [f"{fixture.name}, {entry.name}: expected {pinned}, found {got}"]
            continue
        rows = Counter()
        for record in entry.records or [None]:
            if record is not None:
                sql.scoped(connection, [record])
            rows += Counter(as_rdflib(columns, value) for value in sql.answer(connection, text)[1])
        if entry.records:
            sql.whole(connection)
        lines += [f"{fixture.name}, {entry.name}, under {lens}, {relative}: {kind}: "
                  + " ".join(f"?{name}={term}" for name, term in sorted(r))
                  for kind, side in (("missing", pinned[1] - rows), ("unexpected", rows - pinned[1]))
                  for r in sorted(side.elements(), key=sorted)]
    return lines


class TestSqlBesideEachQuery:
    """SQL beside each query, giving its rows on every fixture · queries/**/*.sql, queries/statements.sql, queries/sql-functions.json

    A runtime answers a query from SQLite through the `.sql` beside its `.rq`, over the tables queries/statements.sql
    makes, calling the six functions whose vectors are in queries/sql-functions.json. The `.rq` stays the definition: each
    `.sql` is held to its rows on every fixture, under each lens, and to the rows the fixtures' manifests pin for it. A
    query outside queries/matcher/ with no `.sql` yet is named in tests/sql-unported.txt.
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
                     for line in failures(fixture, lens, relative, sql_beside(relative).read_text(encoding="utf-8"))]
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

    class TestGivenEachFunction:
        @pytest.mark.parametrize("name", sorted(VECTORS["functions"]))
        def test_gives_each_vectors_output(self, name):
            """gives each vector's output from its input, in Python

            Each vector of the function in queries/sql-functions.json is given to tests/sql.py's function of that name;
            each whose output differs fails.
            """
            function = sql.FUNCTIONS.get(name)
            vectors = VECTORS["functions"][name]["vectors"]
            found = [(vector["input"], vector["output"], function(*vector["input"]) if function else "no such function")
                     for vector in vectors]
            assert [wrong for wrong in found if wrong[1] != wrong[2]] == []

        @pytest.mark.parametrize("name", sorted(VECTORS["functions"]))
        def test_has_vectors_whose_outputs_oxigraph_gives(self, name):
            """has vectors whose outputs Oxigraph's SPARQL gives

            Each vector's input is given to the SPARQL the function stands for, on Oxigraph, as literals; each vector
            whose output is not Oxigraph's, an unbound answer as null, fails. So the vectors are SPARQL's answers, not
            the Python function's.
            """
            vectors = VECTORS["functions"][name]["vectors"]
            found = [(vector["input"], vector["output"], in_sparql(name, vector["input"])) for vector in vectors]
            assert [wrong for wrong in found if wrong[1] != wrong[2]] == []


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

    def test_reports_a_ported_rq_whose_bytes_changed_without_its_pin(self):
        """reports a ported `.rq` whose bytes changed since its pin, with the hash to pin once its `.sql` is checked

        The bytes of `How many judgments count.rq`, with a comment added, are checked against tests/sql-pins.json; the
        check names the query and the new hash.
        """
        changed = (ROOT / self.JUDGMENTS).read_bytes() + b"# changed\n"
        digest = hashlib.sha256(changed).hexdigest()
        found = pin_failures(pins(), {self.JUDGMENTS: changed})
        assert len(found) == 1 and found[0].startswith(f"{self.JUDGMENTS}: ") and digest in found[0]
