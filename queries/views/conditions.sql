-- The conditions screen: the view as tables, in the parts queries/statements.sql names. `condition` has a row for
-- each entry with a lead, holding what the view states of it; `condition_member` its records; `condition_code` its
-- codes; `condition_member_values` each member's current values, with their codes and padded times. The columns that
-- read the labels output or another view, filled by finish, are `condition.label`, `condition_for` and
-- `condition_source`. The medicines, procedures and vaccinations given for a condition are read from their views'
-- statements in `quad` until those views have screens of their own.

-- part: tables
CREATE VIEW condition_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ProblemOrDiagnosis>') AS kind,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#inEntry>') AS in_entry,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leadMember>') AS lead_member,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#statusFrom>') AS status_from,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dateFrom>') AS date_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>') AS current_version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#conditionName>') AS condition_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#conditionCode>') AS condition_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>') AS clinical_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verificationStatus>') AS verification_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#abatementDate>') AS abatement_date,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#onsetDate>') AS onset_date,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>') AS padded,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>') AS padded_property,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>') AS time_as_written,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>') AS label,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reasonCondition>') AS reason_condition,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>') AS member_values,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>') AS values_of_member,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#drugName>') AS drug_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#procedureName>') AS procedure_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#vaccineName>') AS vaccine_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#lifecycle>') AS lifecycle,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#MedicationEnteredInError>') AS entered_in_error,
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
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/conditions.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- name, then entry, as My active conditions and My condition history do. Each other column is a term's id: the lead
-- member, the member status was taken from, its name, status, verification, abatement and onset, and the time as
-- written of an onset or abatement padded to a day.
CREATE TABLE condition (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  name INTEGER,
  status INTEGER,
  verification INTEGER,
  abatement INTEGER,
  abatement_written INTEGER,
  onset INTEGER,
  onset_written INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE condition_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX condition_member_record ON condition_member (record);
CREATE TABLE condition_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE condition_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  name INTEGER,
  status INTEGER,
  verification INTEGER,
  abatement INTEGER,
  onset INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE condition_member_values_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE condition_member_values_padded (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  property INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, member, property, written)
) STRICT, WITHOUT ROWID;
-- Each medicine, procedure or vaccination entry given for one of the entry's records, `line` as My active conditions
-- shows it, `shown` the same in N-Triples, ordered by `name_key` and then `for_entry`.
CREATE TABLE condition_for (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  name_key TEXT NOT NULL,
  for_entry TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;
-- Each record of each entry given for one of the entry's records, so a run keyed to it fills the entry again.
CREATE TABLE condition_for_record (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX condition_for_record_record ON condition_for_record (record);
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE condition_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS condition_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM condition_filled;
INSERT INTO condition_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM condition_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM condition_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT entry FROM condition_for_record WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM condition_terms k CROSS JOIN scope
    JOIN quad v ON v.o = scope.term AND v.p = k.values_of_member JOIN quad given ON given.o = v.s AND given.p = k.member_values
    JOIN quad w ON w.s = given.s AND w.p = k.member_values JOIN quad rc ON rc.s = w.o AND rc.p = k.reason_condition
    JOIN quad e ON e.s = rc.o AND e.p = k.in_entry
  UNION SELECT e.o FROM condition_terms k CROSS JOIN scope
    JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent JOIN quad a ON a.o = ag.s AND a.p = k.association
    JOIN quad g ON g.o = a.s AND g.p = k.generated_by JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM condition WHERE entry IN (SELECT entry FROM condition_filled);
DELETE FROM condition_member WHERE entry IN (SELECT entry FROM condition_filled);
DELETE FROM condition_code WHERE entry IN (SELECT entry FROM condition_filled);
DELETE FROM condition_member_values WHERE entry IN (SELECT entry FROM condition_filled);
DELETE FROM condition_member_values_code WHERE entry IN (SELECT entry FROM condition_filled);
DELETE FROM condition_member_values_padded WHERE entry IN (SELECT entry FROM condition_filled);

INSERT INTO condition (entry, iri, sort_key, lead, status_from, name, status, verification, abatement,
                       abatement_written, onset, onset_written)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM condition_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM condition_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM condition_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL),
  stated (entry, lead, status_from, name, status, verification, abatement, abatement_written, onset, onset_written)
  AS MATERIALIZED (
    SELECT led.entry, led.lead,
      (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.clinical_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.condition_name),
      (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.clinical_status WHERE f.s = led.entry AND f.p = k.status_from),
      (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.verification_status WHERE f.s = led.entry AND f.p = k.status_from),
      (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.abatement_date WHERE f.s = led.entry AND f.p = k.status_from),
      (SELECT min(w.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad d ON d.s = v.o AND d.p = k.padded
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.abatement_date
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE f.s = led.entry AND f.p = k.status_from),
      (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.onset_date WHERE f.s = led.entry AND f.p = k.date_from),
      (SELECT min(w.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad d ON d.s = v.o AND d.p = k.padded
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.onset_date
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE f.s = led.entry AND f.p = k.date_from)
    FROM condition_terms k CROSS JOIN led),
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM condition_terms k CROSS JOIN stated JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  CASE WHEN n.id IS NULL THEN '0' ELSE n.kind || hex(coalesce(n.lex, '')) END || '.' || '2' || hex(named.iri) || '.',
  stated.lead, stated.status_from, stated.name, stated.status, stated.verification, stated.abatement,
  stated.abatement_written, stated.onset, stated.onset_written
FROM stated JOIN named ON named.entry = stated.entry LEFT JOIN term n ON n.id = stated.name;

INSERT INTO condition_member (entry, record)
SELECT DISTINCT r.o, r.s FROM condition_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM condition_filled) AND r.o IN (SELECT entry FROM condition)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO condition_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM condition_terms k CROSS JOIN condition c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.condition_code
WHERE c.entry IN (SELECT entry FROM condition_filled);

INSERT INTO condition_member_values (entry, member, node, name, status, verification, abatement, onset)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM condition_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM condition_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry, members.member, '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.condition_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.clinical_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.verification_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.abatement_date),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.onset_date)
FROM condition_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO condition_member_values_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM condition_terms k CROSS JOIN condition_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.condition_code
WHERE mv.entry IN (SELECT entry FROM condition_filled);

INSERT INTO condition_member_values_padded (entry, member, property, written)
SELECT DISTINCT mv.entry, mv.member, dp.o, w.o FROM condition_terms k CROSS JOIN condition_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE mv.entry IN (SELECT entry FROM condition_filled);

-- part: finish
UPDATE condition SET label = (
  SELECT min(l.o) FROM condition_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = condition.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM condition_filled);

DELETE FROM condition_for WHERE entry IN (SELECT entry FROM condition_filled);
INSERT OR IGNORE INTO condition_for (entry, line, shown, name_key, for_entry)
WITH given (entry, for_entry, name) AS (
  SELECT DISTINCT c.entry, mv.s,
    coalesce((SELECT min(x.o) FROM quad x WHERE x.s = mv.s AND x.p = k.drug_name),
             (SELECT min(x.o) FROM quad x WHERE x.s = mv.s AND x.p = k.procedure_name),
             (SELECT min(x.o) FROM quad x WHERE x.s = mv.s AND x.p = k.vaccine_name))
  FROM condition_terms k CROSS JOIN condition c JOIN condition_member m ON m.entry = c.entry
  JOIN quad rc ON rc.o = m.record AND rc.p = k.reason_condition
  JOIN quad mv ON mv.o = rc.s AND mv.p = k.member_values
  WHERE c.entry IN (SELECT entry FROM condition_filled)
    AND NOT EXISTS (SELECT 1 FROM quad x WHERE x.s = mv.s AND x.p = k.lifecycle AND x.o = k.entered_in_error)),
  spoken (entry, for_entry, name, said) AS (
    SELECT given.entry, f.lex, n.id,
      CASE WHEN n.datatype IN ('http://www.w3.org/2001/XMLSchema#string', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#langString')
           THEN substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0)) END
    FROM given JOIN term f ON f.id = given.for_entry LEFT JOIN term n ON n.id = given.name)
SELECT spoken.entry,
  spoken.for_entry || CASE WHEN spoken.said IS NULL THEN '' ELSE ', ' || n.lex END,
  spoken.for_entry || coalesce(', ' || spoken.said, ''),
  CASE WHEN n.id IS NULL THEN '0' ELSE n.kind || hex(coalesce(n.lex, '')) END,
  spoken.for_entry
FROM spoken LEFT JOIN term n ON n.id = spoken.name;

DELETE FROM condition_for_record WHERE entry IN (SELECT entry FROM condition_filled);
INSERT OR IGNORE INTO condition_for_record (entry, record)
SELECT m.entry, member.o FROM condition_terms k CROSS JOIN condition_member m
JOIN quad rc ON rc.o = m.record AND rc.p = k.reason_condition
JOIN quad mv ON mv.o = rc.s AND mv.p = k.member_values
JOIN quad w ON w.s = mv.s AND w.p = k.member_values
JOIN quad member ON member.s = w.o AND member.p = k.values_of_member
WHERE m.entry IN (SELECT entry FROM condition_filled);

DELETE FROM condition_source WHERE entry IN (SELECT entry FROM condition_filled);
INSERT OR IGNORE INTO condition_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM condition_member WHERE entry IN (SELECT entry FROM condition_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM condition_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM condition_terms k CROSS JOIN quad g
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
FROM records JOIN stated ON stated.record = records.record JOIN term r ON r.id = records.record;

-- part: triples
WITH
  entries (s, entry) AS (SELECT e.nt, c.entry FROM condition c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM condition_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#conditionName>', c.name FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#conditionCode>', x.code FROM entries e JOIN condition_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>', c.status FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#verificationStatus>', c.verification FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#abatementDate>', c.abatement FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#onsetDate>', c.onset FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN condition_member m ON m.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#conditionName>', v.name FROM members mv JOIN condition_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#conditionCode>', x.code FROM members mv JOIN condition_member_values_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>', v.status FROM members mv JOIN condition_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#verificationStatus>', v.verification FROM members mv JOIN condition_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#abatementDate>', v.abatement FROM members mv JOIN condition_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#onsetDate>', v.onset FROM members mv JOIN condition_member_values v USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', x.property
      FROM members mv JOIN condition_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM members mv JOIN condition_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-onsetDate>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', c.onset_written
      FROM entries e JOIN condition c ON c.entry = e.entry
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-abatementDate>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', c.abatement_written
      FROM entries e JOIN condition c ON c.entry = e.entry),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#ProblemOrDiagnosis>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>'
      FROM members mv JOIN condition_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-onsetDate>'
      FROM entries e JOIN condition c ON c.entry = e.entry WHERE c.onset_written IS NOT NULL
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-onsetDate>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', '<https://ns.cascadeprotocol.org/cascade#onsetDate>'
      FROM entries e JOIN condition c ON c.entry = e.entry WHERE c.onset_written IS NOT NULL
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-abatementDate>'
      FROM entries e JOIN condition c ON c.entry = e.entry WHERE c.abatement_written IS NOT NULL
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-abatementDate>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', '<https://ns.cascadeprotocol.org/cascade#abatementDate>'
      FROM entries e JOIN condition c ON c.entry = e.entry WHERE c.abatement_written IS NOT NULL)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made
