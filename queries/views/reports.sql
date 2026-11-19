-- The reports screen: the view as tables, in the parts queries/statements.sql names. `report` has a row for each
-- entry with a lead, holding what the view states of it; `report_member` its records; `report_code`,
-- `report_other_code`, `report_category`, `report_conclusion_code` and `report_result` its codes, categories and
-- the entries of its results; `report_member_values` each member's current values, with their codes, categories,
-- results and padded times. The columns that read the labels output, filled by finish, are `report.label` and
-- `report_source`.

-- part: tables
CREATE VIEW report_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#DiagnosticReport>') AS kind,
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
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>') AS padded,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>') AS padded_property,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>') AS time_as_written,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportName>') AS report_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportCode>') AS report_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportCodeInOtherSystem>') AS report_code_other,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportCategory>') AS report_category,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportEffectiveTime>') AS report_effective_time,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportIssuedTime>') AS report_issued_time,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportConclusion>') AS report_conclusion,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reportConclusionCode>') AS report_conclusion_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#narrativeText>') AS narrative_text,
  (SELECT id FROM term WHERE nt = '<http://purl.obolibrary.org/obo/RO_0002351>') AS result,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>') AS attributed_to,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/reports.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- the day of the time the report took effect, or else was issued, newest first, then that time as written, newest
-- first, then the entry, as My reports, notes and documents does. Each other column is a term's id: the lead member,
-- the member status was taken from, the lead's name, time it took effect, time issued, conclusion, narrative text and
-- organization (the organization record itself), the status, and the time as written of a time padded to a day. A
-- result is the entry the record the lead's version names is in, none for a record in no entry.
CREATE TABLE report (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  name INTEGER,
  date INTEGER,
  issued INTEGER,
  conclusion INTEGER,
  narrative INTEGER,
  organization INTEGER,
  date_written INTEGER,
  status INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE report_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX report_member_record ON report_member (record);
CREATE TABLE report_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_other_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_category (
  entry INTEGER NOT NULL,
  category INTEGER NOT NULL,
  PRIMARY KEY (entry, category)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_conclusion_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_result (
  entry INTEGER NOT NULL,
  result_entry INTEGER NOT NULL,
  PRIMARY KEY (entry, result_entry)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE report_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  name INTEGER,
  date INTEGER,
  issued INTEGER,
  conclusion INTEGER,
  narrative INTEGER,
  organization INTEGER,
  status INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_member_values_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_member_values_other_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_member_values_category (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_member_values_conclusion_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_member_values_result (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE report_member_values_padded (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  property INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, member, property, written)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE report_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('report', 'sqlite_autoindex_report_1', '150 1'),
  ('report', 'sqlite_autoindex_report_2', '150 1'),
  ('report_category', 'report_category', '112 1 1'),
  ('report_code', 'report_code', '150 1 1'),
  ('report_conclusion_code', 'report_conclusion_code', '112 1 1'),
  ('report_member', 'report_member', '150 1 1'),
  ('report_member', 'report_member_record', '150 1'),
  ('report_member_values', 'report_member_values', '150 1 1'),
  ('report_member_values_category', 'report_member_values_category', '112 1 1 1'),
  ('report_member_values_code', 'report_member_values_code', '150 1 1 1'),
  ('report_member_values_conclusion_code', 'report_member_values_conclusion_code', '112 1 1 1'),
  ('report_member_values_other_code', 'report_member_values_other_code', '112 1 1 1'),
  ('report_member_values_padded', 'report_member_values_padded', '112 1 1 1 1'),
  ('report_member_values_result', 'report_member_values_result', '600 4 4 1'),
  ('report_other_code', 'report_other_code', '112 1 1'),
  ('report_result', 'report_result', '600 4 1'),
  ('report_source', 'report_source', '150 1 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS report_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM report_filled;
INSERT INTO report_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM report_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM report_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM report_terms k CROSS JOIN scope
    CROSS JOIN quad x ON x.o = scope.term AND x.p = k.result
    CROSS JOIN quad cv ON cv.o = x.s AND cv.p = k.current_version
    CROSS JOIN quad e ON e.s = cv.s AND e.p = k.in_entry
  UNION SELECT e.o FROM report_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM report_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM report WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_code WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_other_code WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_category WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_conclusion_code WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_result WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values_code WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values_other_code WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values_category WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values_conclusion_code WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values_result WHERE entry IN (SELECT entry FROM report_filled);
DELETE FROM report_member_values_padded WHERE entry IN (SELECT entry FROM report_filled);

CREATE TEMP TABLE IF NOT EXISTS report_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, name INTEGER, date INTEGER, issued INTEGER, conclusion INTEGER, narrative INTEGER, organization INTEGER, date_written INTEGER, status INTEGER) STRICT;
DELETE FROM report_stated;
INSERT INTO report_stated (entry, lead, status_from, name, date, issued, conclusion, narrative, organization, date_written, status)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM report_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM report_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM report_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
SELECT led.entry,
  led.lead,
  (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.report_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.report_effective_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.report_issued_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.report_conclusion),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.attributed_to),
  (SELECT min(w.o) FROM quad d
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.report_effective_time
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE d.s = led.version AND d.p = k.padded),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.workflow_status WHERE f.s = led.entry AND f.p = k.status_from)
FROM report_terms k CROSS JOIN led;

INSERT INTO report (entry, iri, sort_key, lead, status_from, name, date, issued, conclusion, narrative, organization, date_written, status)
WITH
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM report_terms k CROSS JOIN report_stated stated CROSS JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(hex(timed.day), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'), '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~'
  || replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(hex(timed.time), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'), '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~'
  || '2' || hex(named.iri) || '.',
  stated.lead,
  stated.status_from,
  stated.name,
  stated.date,
  stated.issued,
  stated.conclusion,
  stated.narrative,
  stated.organization,
  stated.date_written,
  stated.status
FROM report_stated stated JOIN named ON named.entry = stated.entry
JOIN (SELECT stated.entry, CASE WHEN p.kind IN (2, 3) THEN substr(p.lex, 1, 10) ELSE '' END AS day,
    CASE WHEN p.kind IN (2, 3) THEN p.lex ELSE '' END AS time
  FROM report_stated stated LEFT JOIN term p ON p.id = coalesce(stated.date, stated.issued)) timed ON timed.entry = stated.entry;

INSERT INTO report_member (entry, record)
SELECT DISTINCT r.o, r.s FROM report_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM report_filled) AND r.o IN (SELECT entry FROM report)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO report_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM report_terms k CROSS JOIN report c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_code
WHERE c.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_other_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM report_terms k CROSS JOIN report c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_code_other
WHERE c.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_category (entry, category)
SELECT DISTINCT c.entry, x.o FROM report_terms k CROSS JOIN report c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_category
WHERE c.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_conclusion_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM report_terms k CROSS JOIN report c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_conclusion_code
WHERE c.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_result (entry, result_entry)
SELECT DISTINCT c.entry, ie.o FROM report_terms k CROSS JOIN report c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.result
JOIN quad ie ON ie.s = x.o AND ie.p = k.in_entry
WHERE c.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_member_values (entry, member, node, name, date, issued, conclusion, narrative, organization, status)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM report_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM report_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry,
  members.member,
  '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.report_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.report_effective_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.report_issued_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.report_conclusion),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.attributed_to),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.workflow_status)
FROM report_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO report_member_values_code (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM report_terms k CROSS JOIN report_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_code
WHERE mv.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_member_values_other_code (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM report_terms k CROSS JOIN report_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_code_other
WHERE mv.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_member_values_category (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM report_terms k CROSS JOIN report_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_category
WHERE mv.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_member_values_conclusion_code (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM report_terms k CROSS JOIN report_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.report_conclusion_code
WHERE mv.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_member_values_result (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM report_terms k CROSS JOIN report_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.result
WHERE mv.entry IN (SELECT entry FROM report_filled);

INSERT INTO report_member_values_padded (entry, member, property, written)
SELECT DISTINCT mv.entry, mv.member, dp.o, w.o FROM report_terms k CROSS JOIN report_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE mv.entry IN (SELECT entry FROM report_filled);

-- part: finish
UPDATE report SET label = (
  SELECT min(l.o) FROM report_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = report.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM report_filled);

DELETE FROM report_source WHERE entry IN (SELECT entry FROM report_filled);
INSERT OR IGNORE INTO report_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM report_member WHERE entry IN (SELECT entry FROM report_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM report_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM report_terms k CROSS JOIN quad g
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
WITH
  entries (s, entry) AS (SELECT e.nt, c.entry FROM report c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM report_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportName>', c.name FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportEffectiveTime>', c.date FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportIssuedTime>', c.issued FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportConclusion>', c.conclusion FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', c.narrative FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<http://www.w3.org/ns/prov#wasAttributedTo>', c.organization FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportCode>', x.code FROM entries e JOIN report_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportCodeInOtherSystem>', x.code FROM entries e JOIN report_other_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportCategory>', x.category FROM entries e JOIN report_category x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reportConclusionCode>', x.code FROM entries e JOIN report_conclusion_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<http://purl.obolibrary.org/obo/RO_0002351>', x.result_entry FROM entries e JOIN report_result x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', c.status FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN report_member m ON m.entry = e.entry
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-reportEffectiveTime>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', c.date_written
      FROM entries e JOIN report c ON c.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportName>', v.name FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportEffectiveTime>', v.date FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportIssuedTime>', v.issued FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportConclusion>', v.conclusion FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', v.narrative FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<http://www.w3.org/ns/prov#wasAttributedTo>', v.organization FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', v.status FROM members mv JOIN report_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportCode>', x.value FROM members mv JOIN report_member_values_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportCodeInOtherSystem>', x.value FROM members mv JOIN report_member_values_other_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportCategory>', x.value FROM members mv JOIN report_member_values_category x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reportConclusionCode>', x.value FROM members mv JOIN report_member_values_conclusion_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<http://purl.obolibrary.org/obo/RO_0002351>', x.value FROM members mv JOIN report_member_values_result x USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', x.property
      FROM members mv JOIN report_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM members mv JOIN report_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#DiagnosticReport>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>'
      FROM members mv JOIN report_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-reportEffectiveTime>'
      FROM entries e JOIN report c ON c.entry = e.entry WHERE c.date_written IS NOT NULL
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-reportEffectiveTime>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>',
                     '<https://ns.cascadeprotocol.org/cascade#reportEffectiveTime>'
      FROM entries e JOIN report c ON c.entry = e.entry WHERE c.date_written IS NOT NULL)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made
