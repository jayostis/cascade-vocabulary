-- The procedures screen: the view as tables, in the parts queries/statements.sql names. `procedure` has a row for
-- each entry with a lead, holding what the view states of it; `procedure_member` its records; `procedure_code` its
-- codes; `procedure_member_values` each member's current values, with their codes and the reasons they were done for.
-- The columns that read the labels output, filled by finish, are `procedure.label` and `procedure_source`.

-- part: tables
CREATE VIEW procedure_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#inEntry>') AS in_entry,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leadMember>') AS lead_member,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#statusFrom>') AS status_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>') AS current_version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>') AS padded,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>') AS padded_property,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>') AS time_as_written,
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
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#MedicalProcedure>') AS kind,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#procedureName>') AS procedure_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#procedureCode>') AS procedure_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#narrativeText>') AS narrative_text,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#workflowStatus>') AS workflow_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#procedureDate>') AS procedure_date,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dateFrom>') AS date_from,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reasonCondition>') AS reason_condition,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reasonCode>') AS reason_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reasonCodeInOtherSystem>') AS reason_code_in_other_system,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/procedures.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- the date as written, newest first, then name, then entry, as My procedures does. Each other column is a term's id:
-- the lead member, the member status was taken from, the name, the lead's narrative text, the status and the date.
-- A reason is a condition's record, a code IRI or a code in another system, typed by the system.

CREATE TABLE procedure (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  name INTEGER,
  narrative INTEGER,
  status INTEGER,
  date INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE procedure_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX procedure_member_record ON procedure_member (record);
CREATE TABLE procedure_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE procedure_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  name INTEGER,
  narrative INTEGER,
  status INTEGER,
  date INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE procedure_member_values_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE procedure_member_values_reason_condition (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, member, record)
) STRICT, WITHOUT ROWID;
CREATE TABLE procedure_member_values_reason_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE procedure_member_values_reason_other_system (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE procedure_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

-- The statements the view makes, as s, p and o in N-Triples, the entries and the nodes named after them as the
-- derived state names them.
CREATE VIEW procedure_triples (s, p, o) AS
WITH
  entries (s, entry) AS (SELECT e.nt, c.entry FROM procedure c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM procedure_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#procedureName>', c.name FROM entries e JOIN procedure c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', c.narrative FROM entries e JOIN procedure c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', c.status FROM entries e JOIN procedure c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#procedureDate>', c.date FROM entries e JOIN procedure c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#procedureCode>', x.code FROM entries e JOIN procedure_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN procedure c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN procedure c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN procedure_member m ON m.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#procedureName>', v.name FROM members mv JOIN procedure_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', v.narrative FROM members mv JOIN procedure_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', v.status FROM members mv JOIN procedure_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#procedureDate>', v.date FROM members mv JOIN procedure_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#procedureCode>', x.code FROM members mv JOIN procedure_member_values_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reasonCondition>', x.record FROM members mv JOIN procedure_member_values_reason_condition x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reasonCode>', x.code FROM members mv JOIN procedure_member_values_reason_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reasonCodeInOtherSystem>', x.code FROM members mv JOIN procedure_member_values_reason_other_system x USING (entry, member)),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#MedicalProcedure>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made;
-- Each record the view shows in an entry, `file` the view's address, `entry` as the view names it, `label` the
-- entry's label's term id.
CREATE VIEW procedure_shown (file, type, entry, label, record) AS
SELECT '<' || k.address || '>', '<https://ns.cascadeprotocol.org/cascade#MedicalProcedure>', e.iri, e.label, m.record
FROM procedure_terms k CROSS JOIN procedure e CROSS JOIN procedure_member m ON m.entry = e.entry;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('procedure', 'sqlite_autoindex_procedure_1', '675 1'),
  ('procedure', 'sqlite_autoindex_procedure_2', '675 1'),
  ('procedure_code', 'procedure_code', '675 1 1'),
  ('procedure_member', 'procedure_member', '750 2 1'),
  ('procedure_member', 'procedure_member_record', '750 1'),
  ('procedure_member_values', 'procedure_member_values', '750 2 1'),
  ('procedure_member_values_code', 'procedure_member_values_code', '750 2 1 1'),
  ('procedure_member_values_reason_code', 'procedure_member_values_reason_code', '112 1 1 1'),
  ('procedure_member_values_reason_condition', 'procedure_member_values_reason_condition', '112 1 1 1'),
  ('procedure_member_values_reason_other_system', 'procedure_member_values_reason_other_system', '112 1 1 1'),
  ('procedure_source', 'procedure_source', '750 2 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS procedure_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM procedure_filled;
INSERT INTO procedure_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM procedure_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM procedure_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM procedure_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM procedure_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM procedure WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_member WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_code WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_member_values WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_member_values_code WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_member_values_reason_condition WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_member_values_reason_code WHERE entry IN (SELECT entry FROM procedure_filled);
DELETE FROM procedure_member_values_reason_other_system WHERE entry IN (SELECT entry FROM procedure_filled);

CREATE TEMP TABLE IF NOT EXISTS procedure_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, name INTEGER, narrative INTEGER, status INTEGER, date INTEGER) STRICT;
DELETE FROM procedure_stated;
INSERT INTO procedure_stated (entry, lead, status_from, name, narrative, status, date)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM procedure_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM procedure_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM procedure_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
SELECT led.entry, led.lead,
  (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.procedure_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.workflow_status WHERE f.s = led.entry AND f.p = k.status_from),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.procedure_date WHERE f.s = led.entry AND f.p = k.date_from)
FROM procedure_terms k CROSS JOIN led;

INSERT INTO procedure (entry, iri, sort_key, lead, status_from, name, narrative, status, date)
WITH
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM procedure_terms k CROSS JOIN procedure_stated stated CROSS JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(hex(coalesce(t_date.lex, '')), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'), '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~' || CASE WHEN t_name.id IS NULL THEN '0' ELSE t_name.kind || hex(coalesce(t_name.lex, '')) END || '.' || '2' || hex(named.iri) || '.',
  stated.lead, stated.status_from, stated.name, stated.narrative, stated.status, stated.date
FROM procedure_stated stated JOIN named ON named.entry = stated.entry
LEFT JOIN term t_date ON t_date.id = stated.date
LEFT JOIN term t_name ON t_name.id = stated.name;

INSERT INTO procedure_member (entry, record)
SELECT DISTINCT r.o, r.s FROM procedure_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM procedure_filled) AND r.o IN (SELECT entry FROM procedure)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO procedure_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM procedure_terms k CROSS JOIN procedure c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.procedure_code
WHERE c.entry IN (SELECT entry FROM procedure_filled);

INSERT INTO procedure_member_values (entry, member, node, name, narrative, status, date)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM procedure_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM procedure_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry, members.member, '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.procedure_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.workflow_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.procedure_date)
FROM procedure_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO procedure_member_values_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM procedure_terms k CROSS JOIN procedure_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.procedure_code
WHERE mv.entry IN (SELECT entry FROM procedure_filled);

INSERT INTO procedure_member_values_reason_condition (entry, member, record)
SELECT DISTINCT mv.entry, mv.member, x.o FROM procedure_terms k CROSS JOIN procedure_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reason_condition
WHERE mv.entry IN (SELECT entry FROM procedure_filled);

INSERT INTO procedure_member_values_reason_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM procedure_terms k CROSS JOIN procedure_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reason_code
WHERE mv.entry IN (SELECT entry FROM procedure_filled);

INSERT INTO procedure_member_values_reason_other_system (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM procedure_terms k CROSS JOIN procedure_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reason_code_in_other_system
WHERE mv.entry IN (SELECT entry FROM procedure_filled);

-- part: finish
UPDATE procedure SET label = (
  SELECT min(l.o) FROM procedure_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = procedure.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM procedure_filled);

DELETE FROM procedure_source WHERE entry IN (SELECT entry FROM procedure_filled);
INSERT OR IGNORE INTO procedure_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM procedure_member WHERE entry IN (SELECT entry FROM procedure_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM procedure_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM procedure_terms k CROSS JOIN quad g
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
SELECT s, p, o FROM procedure_triples
