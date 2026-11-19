-- The allergies screen: the view as tables, in the parts queries/statements.sql names. `allergy` has a row for each
-- entry with a lead, holding what the view states of it; `allergy_member` its records; `allergy_code`,
-- `allergy_reaction_text` and `allergy_reaction_code` the lead's allergen codes and reactions; `allergy_member_values`
-- each member's current values, with their codes, reactions and padded onset. The columns that read the labels
-- output, filled by finish, are `allergy.label` and `allergy_source`.

-- part: tables
CREATE VIEW allergy_terms AS SELECT
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
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#AllergyOrIntolerance>') AS kind,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergenName>') AS allergen_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergenCode>') AS allergen_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergyCategory>') AS allergy_category,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#onsetDate>') AS onset_date,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reactionManifestationText>') AS reaction_manifestation_text,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#reactionManifestationCode>') AS reaction_manifestation_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergySeverity>') AS allergy_severity,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>') AS clinical_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergyCriticality>') AS allergy_criticality,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#topCriticality>') AS top_criticality,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergyCategoryFrom>') AS allergy_category_from,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#onsetDateFrom>') AS onset_date_from,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/allergies.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- allergen name, then entry, as My active allergies does. Each other column is a term's id: the lead member, the
-- member status was taken from, the allergen name, the category and onset (the lead's, else the member chosen for it),
-- the time as written of an onset padded to a day, the severity, the status, the highest criticality any member
-- states.

CREATE TABLE allergy (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  name INTEGER,
  category INTEGER,
  onset INTEGER,
  severity INTEGER,
  status INTEGER,
  criticality INTEGER,
  onset_written INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE allergy_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX allergy_member_record ON allergy_member (record);
CREATE TABLE allergy_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE allergy_reaction_text (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE allergy_reaction_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE allergy_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  name INTEGER,
  severity INTEGER,
  status INTEGER,
  criticality INTEGER,
  category INTEGER,
  onset INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE allergy_member_values_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE allergy_member_values_reaction_text (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE allergy_member_values_reaction_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE allergy_member_values_padded (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, member, written)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE allergy_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('allergy', 'sqlite_autoindex_allergy_1', '675 1'),
  ('allergy', 'sqlite_autoindex_allergy_2', '675 1'),
  ('allergy_code', 'allergy_code', '675 1 1'),
  ('allergy_member', 'allergy_member', '750 2 1'),
  ('allergy_member', 'allergy_member_record', '750 1'),
  ('allergy_member_values', 'allergy_member_values', '750 2 1'),
  ('allergy_member_values_code', 'allergy_member_values_code', '750 2 1 1'),
  ('allergy_member_values_padded', 'allergy_member_values_padded', '112 1 1 1'),
  ('allergy_member_values_reaction_code', 'allergy_member_values_reaction_code', '112 1 1 1'),
  ('allergy_member_values_reaction_text', 'allergy_member_values_reaction_text', '112 1 1 1'),
  ('allergy_reaction_code', 'allergy_reaction_code', '112 1 1'),
  ('allergy_reaction_text', 'allergy_reaction_text', '112 1 1'),
  ('allergy_source', 'allergy_source', '750 2 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS allergy_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM allergy_filled;
INSERT INTO allergy_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM allergy_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM allergy_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM allergy_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM allergy_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM allergy WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_member WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_code WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_reaction_text WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_reaction_code WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_member_values WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_member_values_code WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_member_values_reaction_text WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_member_values_reaction_code WHERE entry IN (SELECT entry FROM allergy_filled);
DELETE FROM allergy_member_values_padded WHERE entry IN (SELECT entry FROM allergy_filled);

CREATE TEMP TABLE IF NOT EXISTS allergy_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, name INTEGER, category INTEGER, onset INTEGER, severity INTEGER, status INTEGER, criticality INTEGER, onset_written INTEGER) STRICT;
DELETE FROM allergy_stated;
INSERT INTO allergy_stated (entry, lead, status_from, name, category, onset, severity, status, criticality, onset_written)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM allergy_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM allergy_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM allergy_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
SELECT led.entry, led.lead,
  (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.clinical_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.allergen_name),
  coalesce((SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.allergy_category),
    (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.allergy_category WHERE f.s = led.entry AND f.p = k.allergy_category_from)),
  coalesce((SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.onset_date),
    (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.onset_date WHERE f.s = led.entry AND f.p = k.onset_date_from)),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.allergy_severity),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.clinical_status WHERE f.s = led.entry AND f.p = k.status_from),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.entry AND x.p = k.top_criticality),
  CASE WHEN (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.onset_date) IS NOT NULL THEN (SELECT min(w.o) FROM quad d
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.onset_date
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE d.s = led.version AND d.p = k.padded) ELSE (SELECT min(w.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad d ON d.s = v.o AND d.p = k.padded
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.onset_date
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE f.s = led.entry AND f.p = k.onset_date_from) END
FROM allergy_terms k CROSS JOIN led;

INSERT INTO allergy (entry, iri, sort_key, lead, status_from, name, category, onset, severity, status, criticality, onset_written)
WITH
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM allergy_terms k CROSS JOIN allergy_stated stated JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  CASE WHEN t_name.id IS NULL THEN '0' ELSE t_name.kind || hex(coalesce(t_name.lex, '')) END || '.' || '2' || hex(named.iri) || '.',
  stated.lead, stated.status_from, stated.name, stated.category, stated.onset, stated.severity, stated.status, stated.criticality, stated.onset_written
FROM allergy_stated stated JOIN named ON named.entry = stated.entry
LEFT JOIN term t_name ON t_name.id = stated.name;

INSERT INTO allergy_member (entry, record)
SELECT DISTINCT r.o, r.s FROM allergy_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM allergy_filled) AND r.o IN (SELECT entry FROM allergy)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO allergy_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM allergy_terms k CROSS JOIN allergy c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.allergen_code
WHERE c.entry IN (SELECT entry FROM allergy_filled);

INSERT INTO allergy_reaction_text (entry, code)
SELECT DISTINCT c.entry, x.o FROM allergy_terms k CROSS JOIN allergy c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reaction_manifestation_text
WHERE c.entry IN (SELECT entry FROM allergy_filled);

INSERT INTO allergy_reaction_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM allergy_terms k CROSS JOIN allergy c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reaction_manifestation_code
WHERE c.entry IN (SELECT entry FROM allergy_filled);

INSERT INTO allergy_member_values (entry, member, node, name, severity, status, criticality, category, onset)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM allergy_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM allergy_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry, members.member, '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.allergen_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.allergy_severity),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.clinical_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.allergy_criticality),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.allergy_category),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.onset_date)
FROM allergy_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO allergy_member_values_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM allergy_terms k CROSS JOIN allergy_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.allergen_code
WHERE mv.entry IN (SELECT entry FROM allergy_filled);

INSERT INTO allergy_member_values_reaction_text (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM allergy_terms k CROSS JOIN allergy_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reaction_manifestation_text
WHERE mv.entry IN (SELECT entry FROM allergy_filled);

INSERT INTO allergy_member_values_reaction_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM allergy_terms k CROSS JOIN allergy_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.reaction_manifestation_code
WHERE mv.entry IN (SELECT entry FROM allergy_filled);

INSERT INTO allergy_member_values_padded (entry, member, written)
SELECT DISTINCT mv.entry, mv.member, w.o FROM allergy_terms k CROSS JOIN allergy_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.onset_date
JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE mv.entry IN (SELECT entry FROM allergy_filled);

-- part: finish
UPDATE allergy SET label = (
  SELECT min(l.o) FROM allergy_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = allergy.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM allergy_filled);

DELETE FROM allergy_source WHERE entry IN (SELECT entry FROM allergy_filled);
INSERT OR IGNORE INTO allergy_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM allergy_member WHERE entry IN (SELECT entry FROM allergy_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM allergy_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM allergy_terms k CROSS JOIN quad g
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
  entries (s, entry) AS (SELECT e.nt, c.entry FROM allergy c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM allergy_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#allergenName>', c.name FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#allergyCategory>', c.category FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#onsetDate>', c.onset FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#allergySeverity>', c.severity FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>', c.status FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#allergyCriticality>', c.criticality FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#allergenCode>', x.code FROM entries e JOIN allergy_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reactionManifestationText>', x.code FROM entries e JOIN allergy_reaction_text x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#reactionManifestationCode>', x.code FROM entries e JOIN allergy_reaction_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN allergy c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN allergy_member m ON m.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#allergenName>', v.name FROM members mv JOIN allergy_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#allergySeverity>', v.severity FROM members mv JOIN allergy_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>', v.status FROM members mv JOIN allergy_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#allergyCriticality>', v.criticality FROM members mv JOIN allergy_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#allergyCategory>', v.category FROM members mv JOIN allergy_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#onsetDate>', v.onset FROM members mv JOIN allergy_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#allergenCode>', x.code FROM members mv JOIN allergy_member_values_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reactionManifestationText>', x.code FROM members mv JOIN allergy_member_values_reaction_text x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#reactionManifestationCode>', x.code FROM members mv JOIN allergy_member_values_reaction_code x USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-onsetDate>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM members mv JOIN allergy_member_values_padded x USING (entry, member)
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-onsetDate>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', c.onset_written
      FROM entries e JOIN allergy c ON c.entry = e.entry),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#AllergyOrIntolerance>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>', '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-onsetDate>'
      FROM members mv JOIN allergy_member_values_padded x USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-onsetDate>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', '<https://ns.cascadeprotocol.org/cascade#onsetDate>'
      FROM members mv JOIN allergy_member_values_padded x USING (entry, member)
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>', '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-onsetDate>'
      FROM entries e JOIN allergy c ON c.entry = e.entry WHERE c.onset_written IS NOT NULL
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-onsetDate>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', '<https://ns.cascadeprotocol.org/cascade#onsetDate>'
      FROM entries e JOIN allergy c ON c.entry = e.entry WHERE c.onset_written IS NOT NULL)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made
