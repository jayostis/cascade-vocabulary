-- A pod's statements as SQLite holds them, for the `.sql` beside each `.rq` to read. It needs SQLite 3.44.0 or later.
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
--   tables   makes the screen's tables, once, after this file.
--   fill     deletes the rows of each entry in scope and of each entry a record in scope is in, and gives them again
--            from the kept and derived statements alone. Every view's fill runs before any view's finish.
--   finish   gives, for the same entries, the columns that read the labels output or another view, once the labels
--            are made. Until labels.rq has a `.sql`, the labels output is the rdfs:label statements in `quad`, which
--            labels.rq makes from the view graphs; until a view has a screen, another view reads its statements there.
--   triples  one statement giving the triples the view's CONSTRUCT gives, as s, p and o, from the screen's tables
--            alone. An entry is named as the derived state names it; a runtime writing the view's file names it as
--            N13 says.
-- A screen table has one row per entry. A column holds a term's id, or the N-Triples text of a value the view makes,
-- such as the entry as its view names it, from the layout's address for the view. A value an entry may have more than
-- once, as a list, has a table of its own, never text glued with U+001F; a list question glues it as its `.rq` does.
--
-- Paging. A screen table has a `sort_key` for each order its questions give: TEXT, unique, whose order is the
-- ORDER BY's. It writes each condition in turn, the last being the entry:
--   ascending   a term's kind (0 unbound, 1 a blank node, 2 an IRI, 3 a literal), hex() of its lex, then '.';
--   descending  hex() of the string the condition gives, each hex digit turned around (0 to p, 1 to o, and so on to F
--               to a), then '~'.
-- '.' sorts before every hex digit and '~' after every letter, so a shorter string sorts first ascending and last
-- descending. A key is ASCII. A literal sorts by its lexical form, which is SPARQL's order for strings; an order over
-- numbers would need a part of its own.
-- A list question's `.sql` takes `:page_size`, a number of entries, and `:after`, a sort key, and gives the rows of the
-- first `:page_size` entries in order whose key is after `:after`; both null give the whole list. After its `.rq`'s
-- columns it gives one more, `page_key`, the key of the row's entry, which a runtime and the check drop. The next page
-- is asked after the last row's `page_key`. A page never splits an entry's rows.
-- A list question reads `scope` as its `.rq` bound to records reads them: the rows of each entry with a record in
-- scope, counting only those records. So a runtime asks it with every record in scope.

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

-- The records and entries a run covers: those a keyed run is given, or every one for a whole run.
CREATE TABLE scope (
  term INTEGER PRIMARY KEY
) STRICT;

-- What the tables were built from: one row, `built` 'pod', with the fingerprint of the files the whole was built from.
-- A row for each table built apart may take its place.
CREATE TABLE ledger (
  built TEXT PRIMARY KEY,
  fingerprint TEXT NOT NULL
) STRICT;
