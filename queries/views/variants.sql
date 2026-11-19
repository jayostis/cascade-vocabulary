-- The variants screen: the view as tables, in the parts queries/statements.sql names. `variant` has a row for each
-- entry with a lead; `variant_member` its records; `variant_gene`, `variant_hgvs` and `variant_variation` every gene
-- symbol, HGVS expression and ClinVar VariationID its records' current versions state; `variant_member_values` each
-- member's current values, with those it states. The columns that read the labels output, filled by finish, are
-- `variant.label` and `variant_source`.

-- part: tables
CREATE VIEW variant_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#GeneticVariantFinding>') AS kind,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#inEntry>') AS in_entry,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leadMember>') AS lead_member,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#statusFrom>') AS status_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>') AS current_version,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>') AS label,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>') AS current_revision,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>') AS derived_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedOn>') AS retrieved_on,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>') AS generated_by,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#qualifiedAssociation>') AS association,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadRole>') AS had_role,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#agent>') AS agent,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#AuthorRole>') AS author_role,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#CustodianRole>') AS custodian_role,
  (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>') AS foaf_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#workflowStatus>') AS workflow_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#geneSymbol>') AS gene_symbol,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#hgvsCodingDnaExpression>') AS hgvs,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#clinvarVariationId>') AS variation,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/variants.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- entry, as My genetic variants does. Each other column is a term's id: the lead member, the member status was
-- taken from, and the status.
CREATE TABLE variant (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  status INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE variant_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX variant_member_record ON variant_member (record);
CREATE TABLE variant_gene (
  entry INTEGER NOT NULL,
  gene INTEGER NOT NULL,
  PRIMARY KEY (entry, gene)
) STRICT, WITHOUT ROWID;
CREATE TABLE variant_hgvs (
  entry INTEGER NOT NULL,
  hgvs INTEGER NOT NULL,
  PRIMARY KEY (entry, hgvs)
) STRICT, WITHOUT ROWID;
CREATE TABLE variant_variation (
  entry INTEGER NOT NULL,
  variation INTEGER NOT NULL,
  PRIMARY KEY (entry, variation)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE variant_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  status INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE variant_member_values_gene (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE variant_member_values_hgvs (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE variant_member_values_variation (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE variant_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

-- The statements the view makes, as s, p and o in N-Triples, the entries and the nodes named after them as the
-- derived state names them.
CREATE VIEW variant_triples (s, p, o) AS
WITH
  entries (s, entry) AS (SELECT e.nt, c.entry FROM variant c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM variant_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#geneSymbol>', x.gene FROM entries e JOIN variant_gene x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#hgvsCodingDnaExpression>', x.hgvs FROM entries e JOIN variant_hgvs x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#clinvarVariationId>', x.variation FROM entries e JOIN variant_variation x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', c.status FROM entries e JOIN variant c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN variant c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN variant c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN variant_member m ON m.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', v.status FROM members mv JOIN variant_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#geneSymbol>', x.value FROM members mv JOIN variant_member_values_gene x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#hgvsCodingDnaExpression>', x.value FROM members mv JOIN variant_member_values_hgvs x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#clinvarVariationId>', x.value FROM members mv JOIN variant_member_values_variation x USING (entry, member)),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#GeneticVariantFinding>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made;
-- Each record the view shows in an entry, `file` the view's address, `entry` as the view names it, `label` the
-- entry's label's term id.
CREATE VIEW variant_shown (file, type, entry, label, record) AS
SELECT '<' || k.address || '>', '<https://ns.cascadeprotocol.org/cascade#GeneticVariantFinding>', e.iri, e.label, m.record
FROM variant_terms k CROSS JOIN variant e CROSS JOIN variant_member m ON m.entry = e.entry;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('variant', 'sqlite_autoindex_variant_1', '112 1'),
  ('variant', 'sqlite_autoindex_variant_2', '112 1'),
  ('variant_gene', 'variant_gene', '112 1 1'),
  ('variant_hgvs', 'variant_hgvs', '112 1 1'),
  ('variant_member', 'variant_member', '112 1 1'),
  ('variant_member', 'variant_member_record', '112 1'),
  ('variant_member_values', 'variant_member_values', '112 1 1'),
  ('variant_member_values_gene', 'variant_member_values_gene', '112 1 1 1'),
  ('variant_member_values_hgvs', 'variant_member_values_hgvs', '112 1 1 1'),
  ('variant_member_values_variation', 'variant_member_values_variation', '112 1 1 1'),
  ('variant_source', 'variant_source', '112 1 1'),
  ('variant_variation', 'variant_variation', '112 1 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS variant_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM variant_filled;
INSERT INTO variant_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM variant_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM variant_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM variant_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM variant_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM variant WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_member WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_gene WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_hgvs WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_variation WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_member_values WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_member_values_gene WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_member_values_hgvs WHERE entry IN (SELECT entry FROM variant_filled);
DELETE FROM variant_member_values_variation WHERE entry IN (SELECT entry FROM variant_filled);

CREATE TEMP TABLE IF NOT EXISTS variant_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, status INTEGER) STRICT;
DELETE FROM variant_stated;
INSERT INTO variant_stated (entry, lead, status_from, status)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM variant_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM variant_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM variant_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
SELECT led.entry,
  led.lead,
  (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.workflow_status WHERE f.s = led.entry AND f.p = k.status_from)
FROM variant_terms k CROSS JOIN led;

INSERT INTO variant (entry, iri, sort_key, lead, status_from, status)
WITH
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM variant_terms k CROSS JOIN variant_stated stated CROSS JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  '2' || hex(named.iri) || '.',
  stated.lead,
  stated.status_from,
  stated.status
FROM variant_stated stated JOIN named ON named.entry = stated.entry
;

INSERT INTO variant_member (entry, record)
SELECT DISTINCT r.o, r.s FROM variant_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM variant_filled) AND r.o IN (SELECT entry FROM variant)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO variant_gene (entry, gene)
SELECT DISTINCT m.entry, x.o FROM variant_terms k CROSS JOIN variant_member m
JOIN quad v ON v.s = m.record AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.gene_symbol
WHERE m.entry IN (SELECT entry FROM variant_filled);

INSERT INTO variant_hgvs (entry, hgvs)
SELECT DISTINCT m.entry, x.o FROM variant_terms k CROSS JOIN variant_member m
JOIN quad v ON v.s = m.record AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.hgvs
WHERE m.entry IN (SELECT entry FROM variant_filled);

INSERT INTO variant_variation (entry, variation)
SELECT DISTINCT m.entry, x.o FROM variant_terms k CROSS JOIN variant_member m
JOIN quad v ON v.s = m.record AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.variation
WHERE m.entry IN (SELECT entry FROM variant_filled);

INSERT INTO variant_member_values (entry, member, node, status)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM variant_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM variant_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry,
  members.member,
  '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.workflow_status)
FROM variant_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO variant_member_values_gene (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM variant_terms k CROSS JOIN variant_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.gene_symbol
WHERE mv.entry IN (SELECT entry FROM variant_filled);

INSERT INTO variant_member_values_hgvs (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM variant_terms k CROSS JOIN variant_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.hgvs
WHERE mv.entry IN (SELECT entry FROM variant_filled);

INSERT INTO variant_member_values_variation (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM variant_terms k CROSS JOIN variant_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.variation
WHERE mv.entry IN (SELECT entry FROM variant_filled);

-- part: finish
UPDATE variant SET label = (
  SELECT min(l.o) FROM variant_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = variant.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM variant_filled);

DELETE FROM variant_source WHERE entry IN (SELECT entry FROM variant_filled);
INSERT OR IGNORE INTO variant_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM variant_member WHERE entry IN (SELECT entry FROM variant_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM variant_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM variant_terms k CROSS JOIN quad g
    JOIN quad a ON a.s = g.o AND a.p = k.association
    JOIN quad r ON r.s = a.o AND r.p = k.had_role AND r.o IN (k.author_role, k.custodian_role)
    JOIN quad ag ON ag.s = a.o AND ag.p = k.agent
    JOIN term n ON n.id IN (
      SELECT l.o FROM quad l WHERE l.s = ag.o AND l.p = k.label
      UNION SELECT x.o FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.foaf_name
      WHERE v.s = ag.o AND v.p = k.current_version
        AND NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = ag.o AND l.p = k.label))
    WHERE g.p = k.generated_by AND g.s IN (SELECT document FROM documents)
      AND n.datatype IN ('http://www.w3.org/2001/XMLSchema#string', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#langString')),
  came (record, document, retrieved, hospitals, hospitals_shown) AS (
    SELECT documents.record, documents.document, documents.retrieved,
      (SELECT group_concat(line, ', ' ORDER BY line) FROM hospitals h WHERE h.document = documents.document),
      (SELECT group_concat(shown, ', ' ORDER BY line) FROM hospitals h WHERE h.document = documents.document)
    FROM documents
    UNION ALL
    SELECT record, NULL, NULL, NULL, NULL FROM records
    WHERE record NOT IN (SELECT record FROM documents)),
  stated (record, document, document_shown, retrieved, retrieved_shown, hospitals, hospitals_shown) AS (
    SELECT came.record, d.lex,
      CASE d.kind WHEN 2 THEN d.lex WHEN 3 THEN substr(d.nt, 2, length(d.nt) - 2 - CASE WHEN d.lang IS NOT NULL
        THEN length(d.lang) + 1 WHEN d.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(d.datatype) + 4 END) END,
      t.lex,
      CASE t.kind WHEN 2 THEN t.lex WHEN 3 THEN substr(t.nt, 2, length(t.nt) - 2 - CASE WHEN t.lang IS NOT NULL
        THEN length(t.lang) + 1 WHEN t.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(t.datatype) + 4 END) END,
      came.hospitals, came.hospitals_shown
    FROM came LEFT JOIN term d ON d.id = came.document LEFT JOIN term t ON t.id = came.retrieved)
SELECT records.entry,
  r.lex || CASE WHEN stated.document_shown IS NULL THEN '' ELSE ' from ' || stated.document END
    || CASE WHEN stated.retrieved_shown IS NULL THEN '' ELSE ', retrieved ' || stated.retrieved END
    || coalesce(', ' || stated.hospitals, ''),
  r.lex || coalesce(' from ' || stated.document_shown, '') || coalesce(', retrieved ' || stated.retrieved_shown, '')
    || coalesce(', ' || stated.hospitals_shown, '')
FROM records CROSS JOIN stated ON stated.record = records.record JOIN term r ON r.id = records.record;

-- part: triples
SELECT s, p, o FROM variant_triples
