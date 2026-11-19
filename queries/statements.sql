-- A pod's statements as SQLite holds them, for the `.sql` beside each `.rq` to read. It needs SQLite 3.44.0 or later,
-- and each statement of a `.sql` keeps within SQLite's default limits, such as how deep views and subqueries nest: a
-- runtime's SQLite may count that depth more strictly than the check's, so a statement nesting deep is split, through
-- a temporary table, into statements that each nest less.
--
-- A `.sql` gives its `.rq`'s columns, in its order and by its variables' names, each value a term's `nt` or NULL where
-- the variable is unbound; a `.sql` beside a CONSTRUCT gives the columns s, p and o, one row for each triple. It may
-- call the six functions queries/sql-functions.json gives the vectors of, registered under those names.
--
-- `quad` holds the named graphs of a query's default graph, and a query's default graph is their union, a set: a
-- statement in two graphs is in it once, so a `.sql` reads it through EXISTS, or DISTINCT, and never counts a
-- statement once for each graph holding it. A graph outside the default graph, as a table version's rows are, is not
-- held here.
--
-- Screens. A view's `.sql` holds its screen: the view as tables a list question reads a page of. It is in four parts,
-- each opened by a line `-- part: NAME`, and each but triples run as a script:
--   tables   makes the screen's tables, once, after this file, and two views of them that questions read in place of
--            the view's file: `<name>_triples`, the statements the view makes, as s, p and o, and `<name>_shown`,
--            a row for each record the view shows in an entry, with `file` the view's address, `type` the entry's
--            class, `entry` as the view's file names it and `label` its label's term id.
--   fill     works out the entries the run fills, once, into a temporary table of its own, then deletes their rows
--            and gives them again from the kept and derived statements alone. The entries a run fills are each in
--            scope; each a record in scope is in now; each one was in when the screen was last filled, which the
--            screen's own member table remembers; and each the view's `.sql` names as showing what a term in scope
--            states: a document's statements, in the source line of each record whose current revision derives
--            from it, and an agent's name, in those of each document it made; and, for the conditions screen, the
--            entries given for a condition, through the reason a record in scope's current version names, through the
--            reasons the medications, procedures and immunizations screens hold of the entry a record in scope is in,
--            and through the records of those entries the screen remembers. Those screens' fills may run before the
--            conditions fill or after it, and give the same entries: a reason one of them no longer holds was dropped
--            from a record in scope, whose conditions the screen remembers. Every view's fill runs before any view's
--            finish, on one connection, so a screen reads another's tables in finish. A runtime that fills keyed runs
--            often splits each part into its statements once and keeps each compiled on the connection, rather than
--            running the part as a script, which compiles every statement again on each run.
--            A lens is read by every entry, so a change of lens is a whole run, never a keyed one. The patient profile
--            screen is filled whole by every run: a profile is no record, so no run is keyed to one, and its entries
--            come from the judgments alone. The reports screen fills again the entries of the reports naming a record in
--            scope as a result, and the variant interpretations screen those naming one as the variant they interpret,
--            since each is shown as the entry that record is in.
--   finish   gives, for the same entries, the columns that read the labels output or another screen, once the labels
--            are made. The labels output is the rows of queries/labels.sql, which reads the screens' tables as the
--            fills leave them. A runtime that makes the labels in SQL runs it once, after every view's fill and before
--            any view's finish, and keeps its rows as rdfs:label statements of the labels file's graph in `quad`, in
--            place of those of its last run, which a finish reads from there; the check here does so. A runtime that
--            does not yet loads the labels file labels.rq writes, whose rdfs:label statements are the same rows. The
--            labels are of the whole pod, never of the entries a run fills alone.
--   triples  one statement giving the triples the view's CONSTRUCT gives, as s, p and o: a read of `<name>_triples`,
--            from the screen's tables alone. An entry is named as the derived state names it; a runtime writing the
--            view's file names it as N13 says, and a question that reads the view's statements, as What it shows does,
--            names an entry and the nodes after it under the address of the view that gives the entry its members.
-- A screen table has one row per entry. A column holds a term's id, or the N-Triples text of a value the view makes,
-- such as the entry as its view names it, from the layout's address for the view; a fill fails, by that column's NOT
-- NULL, where the layout gives the view no address or two. A column takes min() of a property only where the shapes
-- give that property sh:maxCount 1; a value an entry may have more than once, as a list, has a table of its own,
-- never text glued with U+001F, and a list question glues it as its `.rq` does.
--
-- Paging. A screen table has a `sort_key` for each order its questions give: TEXT, unique, whose order is the
-- ORDER BY's. It writes each condition in turn, the last being the entry, from the text the condition's value orders
-- by: a string's lexical form, which is SPARQL's order for strings; an xsd:dateTime's or xsd:date's `instant`, its
-- term's, since its lexical form does not order times in different zones; and a count, which a screen works out as
-- an SQL integer, as 'p', or 'n' for a negative, then its absolute value in nineteen digits, each digit turned to
-- nine less it for a negative. Then:
--   ascending   the value's kind (0 unbound, 1 a blank node, 2 an IRI, 3 a literal), hex() of its text, then '.';
--   descending  hex() of its text, each hex digit turned around (0 to p, 1 to o, and so on to F to a), then '~'.
-- '.' sorts before every hex digit and '~' after every letter, so a shorter text sorts first ascending and last
-- descending. A key is ASCII. xsd:date and xsd:dateTime values may be one condition's, ordered by `instant`, a date
-- by its start, as a time with and one with no zone are: where SPARQL's `<` orders neither way, the order is the
-- key's. A time whose term has no `instant`, being ill-formed or of a year outside 1 to 9999, keys as a NULL text,
-- which hex() writes as an empty one: first among the times ascending and last descending, an order `<` allows for
-- an ill-formed time, which it orders against none, but not for a well-formed one of such a year, which needs an
-- encoding of its own before a screen orders by it. A condition whose values are not all strings, all times, or
-- all counts, a decimal or a mix of kinds, needs one too, written here before a screen orders by it.
-- A list question's `.sql` takes `:page_size`, a number of entries, and `:after`, a sort key, and gives the rows of the
-- first `:page_size` entries in order whose key is after `:after`; both null give the whole list. After its `.rq`'s
-- columns it gives one more, `page_key`, the key of the row's entry, which a runtime and the check drop. The next page
-- is asked after the last row's `page_key`. A page never splits an entry's rows.
-- A question reads `asked`, never `scope`: `asked` holding records, a list question gives the rows of each entry
-- with one of them, counting only those, as its `.rq` bound to them does; `asked` empty, it gives the whole list. So
-- a question that reads `asked` of records none of which is a term of the pod gives no rows, as the `.rq` bound to
-- them does, without running the `.sql`, which would read the empty `asked` as the whole pod. A question whose `.rq`
-- binds no ?record in its outermost group, as the reports and notes, variants, variant interpretations and person
-- questions, reads no `asked`: a runtime never binds it to a record nor short-circuits it, and always runs it whole,
-- as the `.rq` bound to any record, one the pod lacks too, gives the rows it gives unbound, unless the `.rq` gives a
-- ?record column, as an entry's review does for the records a finding names: a binding would add the record to each row
-- that names none, so a runtime never binds it either.

-- Each term the pod's statements use, once. `nt` is its N-Triples form as Oxigraph writes it, a literal in its
-- canonical form, so two terms are one exactly when their `nt` is. `kind` ranks it as SPARQL's ORDER BY does, after
-- an unbound value: 1 a blank node, 2 an IRI, 3 a literal. `lex` is what STR gives, an IRI's text or a literal's
-- lexical form, unescaped; a blank node has none. A literal has a `datatype`, rdf:langString when it has a `lang`.
-- `instant` and `day` are kept for a valid xsd:dateTime or xsd:date. `instant` is its start in UTC, written
-- YYYY-MM-DDThh:mm:ss and eighteen fractional digits, so text order is time order; a value with no zone is read as if
-- in UTC, so the order agrees with SPARQL's `<` wherever `<` gives one, and none is kept for a year outside 1 to
-- 9999. Where `<` gives none, between a value with no zone and one with a zone within fourteen hours of it, the order
-- is this key's, which need not be any engine's ORDER BY. `day` is the calendar day its lexical form writes,
-- YYYY-MM-DD, whatever its zone.
CREATE TABLE term (
  id INTEGER PRIMARY KEY,
  nt TEXT NOT NULL UNIQUE,
  kind INTEGER NOT NULL CHECK (kind IN (1, 2, 3)),
  lex TEXT,
  datatype TEXT,
  lang TEXT,
  instant TEXT,
  day TEXT
) STRICT;

-- Each statement of each named graph, by its terms' ids, g naming the graph.
CREATE TABLE quad (
  s INTEGER NOT NULL,
  p INTEGER NOT NULL,
  o INTEGER NOT NULL,
  g INTEGER NOT NULL,
  PRIMARY KEY (s, p, o, g)
) STRICT, WITHOUT ROWID;
CREATE INDEX quad_pos ON quad (p, o, s, g);
CREATE INDEX quad_osp ON quad (o, s, p, g);
CREATE INDEX quad_g ON quad (g, s, p, o);

-- The terms a run covers: for a keyed run, those it is given, each a record, an entry, an agent or a document whose
-- statements changed; for a whole run, every record and entry.
CREATE TABLE scope (
  term INTEGER PRIMARY KEY
) STRICT;

-- The records a question is asked of, as its `.rq` bound to them is: empty, it is asked of the whole pod. A runtime
-- fills it for a bound question and empties it after, and asks no question of records the pod has no term for; a
-- question reads it, never `scope`, which is the build's.
CREATE TABLE asked (
  term INTEGER PRIMARY KEY
) STRICT;

-- What the tables were built from: one row, `built` 'pod', with the fingerprint of the files the whole was built from.
-- A row for each table built apart may take its place.
CREATE TABLE ledger (
  built TEXT PRIMARY KEY,
  fingerprint TEXT NOT NULL
) STRICT;

-- Planner statistics: the rows ANALYZE wrote for the tables above on a pod of 15,000 records, 986,560 statements, so
-- every plan is the same in every runtime and at every size of pod. `scope` and `asked` have the one row a keyed run
-- gives them, not the pod's: a screen's statements join what they read to `scope`, and a `scope` of the pod's size lets
-- the plan read a predicate's whole range of `quad` and look `scope` up for each of them, a cost that grows with the
-- pod on every keyed run. A table or index added above gets its row here.
--
-- A runtime loads the rows with `ANALYZE sqlite_schema` after it makes the indexes: a row for an index that does not
-- exist is ignored, so a runtime that makes them after it loads the statements, as one that builds the pod in bulk
-- does, plans on none of the `quad` rows. It never runs a full ANALYZE: written after a whole fill, a `scope` of the
-- pod's size makes a keyed refill 21% slower, and on an empty pod it deletes every shipped row.
--
-- A screen's tables do not exist when this file is loaded, so each screen ships the rows for its own at the end of its
-- `tables` part, followed by the same `ANALYZE sqlite_schema`. A table with none is planned as if it held a million
-- rows and drives its statement from `term`: 175 whole scans of it in the screens' triples and the patient profile's
-- fill. The counts are what ANALYZE wrote on the same pod after a whole fill. A table that pod leaves empty takes
-- 112 rows, a tenth of the median of the eight `_member` tables it holds, and no more than its own screen's `_member`
-- table holds: the kinds it leaves empty are rare, and any small count is what lets the planner start from them.
ANALYZE sqlite_schema;
INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('asked', NULL, '1'),
  ('ledger', 'sqlite_autoindex_ledger_1', '1 1'),
  ('quad', 'quad', '986560 8 1 1 1'),
  ('quad', 'quad_g', '986560 21 5 1 1'),
  ('quad', 'quad_osp', '986560 5 2 1 1'),
  ('quad', 'quad_pos', '986560 7769 3 1 1'),
  ('scope', NULL, '1'),
  ('term', 'sqlite_autoindex_term_1', '306736 1');
ANALYZE sqlite_schema;
