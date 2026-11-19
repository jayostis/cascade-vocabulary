-- The medication dispenses screen: the view as tables, in the parts queries/statements.sql names.
-- `medication_dispense` has a row for each entry with a lead, holding what the view states of it;
-- `medication_dispense_member` its records; `medication_dispense_code`, `_ndc`, `_other_system_code` and
-- `_prescription_entry` the lead's codes and the entries of its prescriptions; `medication_dispense_padded` the lead's
-- padded times; `medication_dispense_member_values` each member's current values, with their codes, prescriptions and
-- padded times. The columns that read the labels output, filled by finish, are `medication_dispense.label` and
-- `medication_dispense_source`. No list question reads this screen yet, so it has no sort key.

-- part: tables
CREATE VIEW medication_dispense_terms AS SELECT
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
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#MedicationDispense>') AS kind,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#drugName>') AS drug_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#rxNormCode>') AS rx_norm_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ndcCode>') AS ndc_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#medicationCodeInOtherSystem>') AS medication_code_in_other_system,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#userSelectedCode>') AS user_selected_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dispensePreparedTime>') AS dispense_prepared_time,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dispenseHandedOverTime>') AS dispense_handed_over_time,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#authorizingPrescription>') AS authorizing_prescription,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#workflowStatus>') AS workflow_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#statusLifecycle>') AS status_lifecycle,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/medication-dispenses.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. Each other column is a term's id:
-- the lead member, the member status was taken from, the name, the code the source chose, the times the dispense was
-- prepared and handed over, the status and its lifecycle class.

CREATE TABLE medication_dispense (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  name INTEGER,
  selected INTEGER,
  prepared INTEGER,
  handed_over INTEGER,
  status INTEGER,
  lifecycle INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE medication_dispense_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX medication_dispense_member_record ON medication_dispense_member (record);
CREATE TABLE medication_dispense_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_ndc (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_other_system_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_prescription_entry (
  entry INTEGER NOT NULL,
  prescription_entry INTEGER NOT NULL,
  PRIMARY KEY (entry, prescription_entry)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_padded (
  entry INTEGER NOT NULL,
  property INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, property, written)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE medication_dispense_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  name INTEGER,
  selected INTEGER,
  prepared INTEGER,
  handed_over INTEGER,
  status INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_member_values_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_member_values_ndc (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_member_values_other_system_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_member_values_prescription (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, member, record)
) STRICT, WITHOUT ROWID;
CREATE TABLE medication_dispense_member_values_padded (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  property INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, member, property, written)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE medication_dispense_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('medication_dispense', 'sqlite_autoindex_medication_dispense_1', '112 1'),
  ('medication_dispense_code', 'medication_dispense_code', '112 1 1'),
  ('medication_dispense_member', 'medication_dispense_member', '112 1 1'),
  ('medication_dispense_member', 'medication_dispense_member_record', '112 1'),
  ('medication_dispense_member_values', 'medication_dispense_member_values', '112 1 1'),
  ('medication_dispense_member_values_code', 'medication_dispense_member_values_code', '112 1 1 1'),
  ('medication_dispense_member_values_ndc', 'medication_dispense_member_values_ndc', '112 1 1 1'),
  ('medication_dispense_member_values_other_system_code', 'medication_dispense_member_values_other_system_code', '112 1 1 1'),
  ('medication_dispense_member_values_padded', 'medication_dispense_member_values_padded', '112 1 1 1 1'),
  ('medication_dispense_member_values_prescription', 'medication_dispense_member_values_prescription', '112 1 1 1'),
  ('medication_dispense_ndc', 'medication_dispense_ndc', '112 1 1'),
  ('medication_dispense_other_system_code', 'medication_dispense_other_system_code', '112 1 1'),
  ('medication_dispense_padded', 'medication_dispense_padded', '112 1 1 1'),
  ('medication_dispense_prescription_entry', 'medication_dispense_prescription_entry', '112 1 1'),
  ('medication_dispense_source', 'medication_dispense_source', '112 1 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS medication_dispense_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM medication_dispense_filled;
INSERT INTO medication_dispense_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM medication_dispense_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM medication_dispense_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM medication_dispense_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM medication_dispense_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM medication_dispense WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_code WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_ndc WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_other_system_code WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_prescription_entry WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_padded WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member_values WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member_values_code WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member_values_ndc WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member_values_other_system_code WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member_values_prescription WHERE entry IN (SELECT entry FROM medication_dispense_filled);
DELETE FROM medication_dispense_member_values_padded WHERE entry IN (SELECT entry FROM medication_dispense_filled);

CREATE TEMP TABLE IF NOT EXISTS medication_dispense_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, name INTEGER, selected INTEGER, prepared INTEGER, handed_over INTEGER, status INTEGER, lifecycle INTEGER) STRICT;
DELETE FROM medication_dispense_stated;
INSERT INTO medication_dispense_stated (entry, lead, status_from, name, selected, prepared, handed_over, status, lifecycle)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM medication_dispense_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM medication_dispense_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM medication_dispense_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
SELECT led.entry, led.lead,
  (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.drug_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.user_selected_code),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.dispense_prepared_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.dispense_handed_over_time),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.workflow_status WHERE f.s = led.entry AND f.p = k.status_from),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.entry AND x.p = k.status_lifecycle)
FROM medication_dispense_terms k CROSS JOIN led;

INSERT INTO medication_dispense (entry, iri, lead, status_from, name, selected, prepared, handed_over, status, lifecycle)
WITH
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM medication_dispense_terms k CROSS JOIN medication_dispense_stated stated CROSS JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  stated.lead, stated.status_from, stated.name, stated.selected, stated.prepared, stated.handed_over, stated.status, stated.lifecycle
FROM medication_dispense_stated stated JOIN named ON named.entry = stated.entry;

INSERT INTO medication_dispense_member (entry, record)
SELECT DISTINCT r.o, r.s FROM medication_dispense_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM medication_dispense_filled) AND r.o IN (SELECT entry FROM medication_dispense)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO medication_dispense_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.rx_norm_code
WHERE c.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_ndc (entry, code)
SELECT DISTINCT c.entry, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.ndc_code
WHERE c.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_other_system_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.medication_code_in_other_system
WHERE c.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_prescription_entry (entry, prescription_entry)
SELECT DISTINCT c.entry, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad y ON y.s = v.o AND y.p = k.authorizing_prescription
JOIN quad x ON x.s = y.o AND x.p = k.in_entry
WHERE c.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_padded (entry, property, written)
SELECT DISTINCT c.entry, dp.o, w.o FROM medication_dispense_terms k CROSS JOIN medication_dispense c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE c.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_member_values (entry, member, node, name, selected, prepared, handed_over, status)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM medication_dispense_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM medication_dispense_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry, members.member, '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.drug_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.user_selected_code),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.dispense_prepared_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.dispense_handed_over_time),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.workflow_status)
FROM medication_dispense_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO medication_dispense_member_values_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.rx_norm_code
WHERE mv.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_member_values_ndc (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.ndc_code
WHERE mv.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_member_values_other_system_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.medication_code_in_other_system
WHERE mv.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_member_values_prescription (entry, member, record)
SELECT DISTINCT mv.entry, mv.member, x.o FROM medication_dispense_terms k CROSS JOIN medication_dispense_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.authorizing_prescription
WHERE mv.entry IN (SELECT entry FROM medication_dispense_filled);

INSERT INTO medication_dispense_member_values_padded (entry, member, property, written)
SELECT DISTINCT mv.entry, mv.member, dp.o, w.o FROM medication_dispense_terms k CROSS JOIN medication_dispense_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE mv.entry IN (SELECT entry FROM medication_dispense_filled);

-- part: finish
UPDATE medication_dispense SET label = (
  SELECT min(l.o) FROM medication_dispense_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = medication_dispense.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM medication_dispense_filled);

DELETE FROM medication_dispense_source WHERE entry IN (SELECT entry FROM medication_dispense_filled);
INSERT OR IGNORE INTO medication_dispense_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM medication_dispense_member WHERE entry IN (SELECT entry FROM medication_dispense_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM medication_dispense_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM medication_dispense_terms k CROSS JOIN quad g
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
  entries (s, entry) AS (SELECT e.nt, c.entry FROM medication_dispense c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM medication_dispense_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#drugName>', c.name FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#userSelectedCode>', c.selected FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#dispensePreparedTime>', c.prepared FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#dispenseHandedOverTime>', c.handed_over FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', c.status FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#lifecycle>', c.lifecycle FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#rxNormCode>', x.code FROM entries e JOIN medication_dispense_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#ndcCode>', x.code FROM entries e JOIN medication_dispense_ndc x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#medicationCodeInOtherSystem>', x.code FROM entries e JOIN medication_dispense_other_system_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#authorizingPrescription>', x.prescription_entry FROM entries e JOIN medication_dispense_prescription_entry x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN medication_dispense c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN medication_dispense_member m ON m.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#drugName>', v.name FROM members mv JOIN medication_dispense_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#userSelectedCode>', v.selected FROM members mv JOIN medication_dispense_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#dispensePreparedTime>', v.prepared FROM members mv JOIN medication_dispense_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#dispenseHandedOverTime>', v.handed_over FROM members mv JOIN medication_dispense_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', v.status FROM members mv JOIN medication_dispense_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#rxNormCode>', x.code FROM members mv JOIN medication_dispense_member_values_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#ndcCode>', x.code FROM members mv JOIN medication_dispense_member_values_ndc x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#medicationCodeInOtherSystem>', x.code FROM members mv JOIN medication_dispense_member_values_other_system_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#authorizingPrescription>', x.record FROM members mv JOIN medication_dispense_member_values_prescription x USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', x.property
      FROM members mv JOIN medication_dispense_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM members mv JOIN medication_dispense_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', x.property
      FROM entries e JOIN medication_dispense_padded x ON x.entry = e.entry JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM entries e JOIN medication_dispense_padded x ON x.entry = e.entry JOIN term p ON p.id = x.property),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#MedicationDispense>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>'
      FROM members mv JOIN medication_dispense_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>'
      FROM entries e JOIN medication_dispense_padded x ON x.entry = e.entry JOIN term p ON p.id = x.property)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made
