-- A pod's statements as SQLite holds them, for the `.sql` beside each `.rq` to read. It needs SQLite 3.37.0 or later.
--
-- A `.sql` gives its `.rq`'s columns, in its order and by its variables' names, each value a term's `nt` or NULL where
-- the variable is unbound; a `.sql` beside a CONSTRUCT gives the columns s, p and o, one row for each triple. It may
-- call the six functions queries/sql-functions.json gives the vectors of, registered under those names.
--
-- A query's default graph is the union of the named graphs, a set: a statement in two graphs is in it once, so a
-- `.sql` reads it through EXISTS, or DISTINCT, and never counts a statement once for each graph holding it.

-- Each term the pod's statements use, once. `nt` is its N-Triples form as Oxigraph writes it, a literal in its
-- canonical form, so two terms are one exactly when their `nt` is. `kind` ranks it as SPARQL's ORDER BY does, after
-- an unbound value: 1 a blank node, 2 an IRI, 3 a literal. `lex` is what STR gives, an IRI's text or a literal's
-- lexical form, unescaped; a blank node has none. A literal has a `datatype`, rdf:langString when it has a `lang`.
-- `instant` and `day` are kept for a valid xsd:dateTime or xsd:date. `instant` is its start in UTC, written
-- YYYY-MM-DDThh:mm:ss and eighteen fractional digits, so text order is time order; a value with no zone is read as if
-- in UTC, which is SPARQL's order wherever SPARQL gives one, and none is kept for a year outside 1 to 9999. `day` is
-- the calendar day its lexical form writes, YYYY-MM-DD, whatever its zone.
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
