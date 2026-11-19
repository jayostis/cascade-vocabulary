-- The notes and documents screen: the view as tables, in the parts queries/statements.sql names. `note` has a row
-- for each entry with a lead, holding what the view states of it; `note_member` its records; `note_type_code` and
-- `note_type_other_code` its type codes; `note_member_values` each member's current values, with their codes and
-- padded times. The columns that read the labels output, filled by finish, are `note.label` and `note_source`.

-- part: tables
CREATE VIEW note_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ClinicalNoteOrDocument>') AS kind,
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
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeName>') AS note_type_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeCode>') AS note_type_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeCodeInOtherSystem>') AS note_type_other,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTitle>') AS note_title,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentDate>') AS note_date,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentContentStatus>') AS note_content_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#narrativeText>') AS narrative_text,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>') AS attributed_to,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/notes-and-documents.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- the day of the note's date, newest first, then the date as written, newest first, then the entry, as My reports,
-- notes and documents does. Each other column is a term's id: the lead member, the member status was taken from,
-- the lead's type name, title, date, content status, narrative text and organization (the organization record
-- itself), the status, and the time as written of a date padded to a day.
CREATE TABLE note (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  type_name INTEGER,
  title INTEGER,
  date INTEGER,
  content_status INTEGER,
  narrative INTEGER,
  organization INTEGER,
  date_written INTEGER,
  status INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE note_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX note_member_record ON note_member (record);
CREATE TABLE note_type_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE note_type_other_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE note_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  type_name INTEGER,
  title INTEGER,
  date INTEGER,
  content_status INTEGER,
  narrative INTEGER,
  organization INTEGER,
  status INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE note_member_values_type_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE note_member_values_type_other_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  value INTEGER NOT NULL,
  PRIMARY KEY (entry, member, value)
) STRICT, WITHOUT ROWID;
CREATE TABLE note_member_values_padded (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  property INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, member, property, written)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE note_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

-- The statements the view makes, as s, p and o in N-Triples, the entries and the nodes named after them as the
-- derived state names them.
CREATE VIEW note_triples (s, p, o) AS
WITH
  entries (s, entry) AS (SELECT e.nt, c.entry FROM note c JOIN term e ON e.id = c.entry),
  members (s, node, entry, member) AS (SELECT mv.node, mv.node, mv.entry, mv.member FROM note_member_values mv),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeName>', c.type_name FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTitle>', c.title FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentDate>', c.date FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentContentStatus>', c.content_status FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', c.narrative FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<http://www.w3.org/ns/prov#wasAttributedTo>', c.organization FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeCode>', x.code FROM entries e JOIN note_type_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeCodeInOtherSystem>', x.code FROM entries e JOIN note_type_other_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', c.status FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN note_member m ON m.entry = e.entry
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-noteOrDocumentDate>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', c.date_written
      FROM entries e JOIN note c ON c.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeName>', v.type_name FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTitle>', v.title FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentDate>', v.date FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentContentStatus>', v.content_status FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', v.narrative FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<http://www.w3.org/ns/prov#wasAttributedTo>', v.organization FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', v.status FROM members mv JOIN note_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeCode>', x.value FROM members mv JOIN note_member_values_type_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentTypeCodeInOtherSystem>', x.value FROM members mv JOIN note_member_values_type_other_code x USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', x.property
      FROM members mv JOIN note_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM members mv JOIN note_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#ClinicalNoteOrDocument>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>'
      FROM members mv JOIN note_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-noteOrDocumentDate>'
      FROM entries e JOIN note c ON c.entry = e.entry WHERE c.date_written IS NOT NULL
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-noteOrDocumentDate>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>',
                     '<https://ns.cascadeprotocol.org/cascade#noteOrDocumentDate>'
      FROM entries e JOIN note c ON c.entry = e.entry WHERE c.date_written IS NOT NULL)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made;
-- Each record the view shows in an entry, `file` the view's address, `entry` as the view names it, `label` the
-- entry's label's term id.
CREATE VIEW note_shown (file, type, entry, label, record) AS
SELECT '<' || k.address || '>', '<https://ns.cascadeprotocol.org/cascade#ClinicalNoteOrDocument>', e.iri, e.label, m.record
FROM note_terms k CROSS JOIN note e CROSS JOIN note_member m ON m.entry = e.entry;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('note', 'sqlite_autoindex_note_1', '150 1'),
  ('note', 'sqlite_autoindex_note_2', '150 1'),
  ('note_member', 'note_member', '150 1 1'),
  ('note_member', 'note_member_record', '150 1'),
  ('note_member_values', 'note_member_values', '150 1 1'),
  ('note_member_values_padded', 'note_member_values_padded', '112 1 1 1 1'),
  ('note_member_values_type_code', 'note_member_values_type_code', '150 1 1 1'),
  ('note_member_values_type_other_code', 'note_member_values_type_other_code', '112 1 1 1'),
  ('note_source', 'note_source', '150 1 1'),
  ('note_type_code', 'note_type_code', '150 1 1'),
  ('note_type_other_code', 'note_type_other_code', '112 1 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS note_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM note_filled;
INSERT INTO note_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM note_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM note_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM note_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM note_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM note WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_member WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_type_code WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_type_other_code WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_member_values WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_member_values_type_code WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_member_values_type_other_code WHERE entry IN (SELECT entry FROM note_filled);
DELETE FROM note_member_values_padded WHERE entry IN (SELECT entry FROM note_filled);

CREATE TEMP TABLE IF NOT EXISTS note_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, type_name INTEGER, title INTEGER, date INTEGER, content_status INTEGER, narrative INTEGER, organization INTEGER, date_written INTEGER, status INTEGER) STRICT;
DELETE FROM note_stated;
INSERT INTO note_stated (entry, lead, status_from, type_name, title, date, content_status, narrative, organization, date_written, status)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM note_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM note_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM note_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
SELECT led.entry,
  led.lead,
  (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.note_type_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.note_title),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.note_date),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.note_content_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.attributed_to),
  (SELECT min(w.o) FROM quad d
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.note_date
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE d.s = led.version AND d.p = k.padded),
  (SELECT min(x.o) FROM quad f JOIN quad v ON v.s = f.o AND v.p = k.current_version
       JOIN quad x ON x.s = v.o AND x.p = k.workflow_status WHERE f.s = led.entry AND f.p = k.status_from)
FROM note_terms k CROSS JOIN led;

INSERT INTO note (entry, iri, sort_key, lead, status_from, type_name, title, date, content_status, narrative, organization, date_written, status)
WITH
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM note_terms k CROSS JOIN note_stated stated CROSS JOIN term e ON e.id = stated.entry)
SELECT stated.entry, '<' || named.iri || '>',
  replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(hex(timed.day), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'), '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~'
  || replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(hex(timed.time), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'), '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~'
  || '2' || hex(named.iri) || '.',
  stated.lead,
  stated.status_from,
  stated.type_name,
  stated.title,
  stated.date,
  stated.content_status,
  stated.narrative,
  stated.organization,
  stated.date_written,
  stated.status
FROM note_stated stated JOIN named ON named.entry = stated.entry
JOIN (SELECT stated.entry, CASE WHEN p.kind IN (2, 3) THEN substr(p.lex, 1, 10) ELSE '' END AS day,
    CASE WHEN p.kind IN (2, 3) THEN p.lex ELSE '' END AS time
  FROM note_stated stated LEFT JOIN term p ON p.id = stated.date) timed ON timed.entry = stated.entry;

INSERT INTO note_member (entry, record)
SELECT DISTINCT r.o, r.s FROM note_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM note_filled) AND r.o IN (SELECT entry FROM note)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO note_type_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM note_terms k CROSS JOIN note c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.note_type_code
WHERE c.entry IN (SELECT entry FROM note_filled);

INSERT INTO note_type_other_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM note_terms k CROSS JOIN note c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.note_type_other
WHERE c.entry IN (SELECT entry FROM note_filled);

INSERT INTO note_member_values (entry, member, node, type_name, title, date, content_status, narrative, organization, status)
WITH members (entry, member, version) AS (
  SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
  FROM note_terms k CROSS JOIN quad r
  WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM note_filled)
    AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
    AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version))
SELECT members.entry,
  members.member,
  '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.note_type_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.note_title),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.note_date),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.note_content_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.attributed_to),
  (SELECT min(x.o) FROM quad x WHERE x.s = members.version AND x.p = k.workflow_status)
FROM note_terms k CROSS JOIN members JOIN term e ON e.id = members.entry JOIN term m ON m.id = members.member;

INSERT INTO note_member_values_type_code (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM note_terms k CROSS JOIN note_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.note_type_code
WHERE mv.entry IN (SELECT entry FROM note_filled);

INSERT INTO note_member_values_type_other_code (entry, member, value)
SELECT DISTINCT mv.entry, mv.member, x.o FROM note_terms k CROSS JOIN note_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.note_type_other
WHERE mv.entry IN (SELECT entry FROM note_filled);

INSERT INTO note_member_values_padded (entry, member, property, written)
SELECT DISTINCT mv.entry, mv.member, dp.o, w.o FROM note_terms k CROSS JOIN note_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE mv.entry IN (SELECT entry FROM note_filled);

-- part: finish
UPDATE note SET label = (
  SELECT min(l.o) FROM note_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = note.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM note_filled);

DELETE FROM note_source WHERE entry IN (SELECT entry FROM note_filled);
INSERT OR IGNORE INTO note_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM note_member WHERE entry IN (SELECT entry FROM note_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM note_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM note_terms k CROSS JOIN quad g
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
SELECT s, p, o FROM note_triples
