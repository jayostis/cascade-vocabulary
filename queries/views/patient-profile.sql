-- The patient profile screen: the view as tables, in the parts queries/statements.sql names. `patient_profile_member` has
-- a row for each profile a counting About judgment ties to a subject and no counting NotAbout over it for that subject
-- outranks, with the entry the view names after the subject's least such profile; `patient_profile_values` each such
-- profile's current values, a node of the view named after the entry and the profile; `patient_profile_source` where
-- each profile came from. The view's entries are not those the derived state holds, and a profile is no record, so no run
-- is keyed to one: each run fills the screen whole, as it reads the judgments of the lens, which every run reads.
-- The columns that read the labels output are none.

-- part: tables
CREATE VIEW patient_profile_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>') AS counts,
  (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>') AS yes,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>') AS verdict,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#About>') AS about,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#NotAbout>') AS not_about,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>') AS had_member,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#subject>') AS subject,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>') AS current_version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dateOfBirth>') AS date_of_birth,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#administrativeGender>') AS administrative_gender,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#deceased>') AS deceased,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dateOfDeath>') AS date_of_death,
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
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>') AS label;

-- `entry` is the entry as the view names it, N-Triples text: urn:cascade:entry: and the SHA-256 of the subject's least
-- profile. `subject` and `profile` are terms' ids. An entry holds the profiles of each subject it is named for.
CREATE TABLE patient_profile_member (
  entry TEXT NOT NULL,
  subject INTEGER NOT NULL,
  profile INTEGER NOT NULL,
  PRIMARY KEY (entry, subject, profile)
) STRICT, WITHOUT ROWID;
CREATE INDEX patient_profile_member_profile ON patient_profile_member (profile);
-- A profile's current values in an entry, `node` the node of the view holding them, N-Triples text. Each other column is
-- a term's id. A profile with no current version has no row.
CREATE TABLE patient_profile_values (
  entry TEXT NOT NULL,
  profile INTEGER NOT NULL,
  node TEXT NOT NULL,
  date_of_birth INTEGER,
  administrative_gender INTEGER,
  deceased INTEGER,
  date_of_death INTEGER,
  PRIMARY KEY (entry, profile)
) STRICT, WITHOUT ROWID;
-- Where each profile an entry holds came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE patient_profile_source (
  profile INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (profile, line)
) STRICT, WITHOUT ROWID;

-- part: fill
DELETE FROM patient_profile_member;
DELETE FROM patient_profile_values;
INSERT INTO patient_profile_member (entry, subject, profile)
WITH
  counted (subject, profile) AS (
    SELECT DISTINCT su.o, h.o
    FROM patient_profile_terms k CROSS JOIN quad c
    JOIN quad v ON v.s = c.s AND v.p = k.verdict AND v.o = k.about
    JOIN quad h ON h.s = c.s AND h.p = k.had_member
    JOIN quad su ON su.s = c.s AND su.p = k.subject
    WHERE c.p = k.counts AND c.o = k.yes
      AND NOT EXISTS (
        SELECT 1 FROM quad dc
        JOIN quad dv ON dv.s = dc.s AND dv.p = k.verdict AND dv.o = k.not_about
        JOIN quad dh ON dh.s = dc.s AND dh.p = k.had_member AND dh.o = h.o
        JOIN quad ds ON ds.s = dc.s AND ds.p = k.subject AND ds.o = su.o
        WHERE dc.p = k.counts AND dc.o = k.yes)),
  named (subject, entry) AS (
    SELECT counted.subject, '<urn:cascade:entry:' || sparql_sha256(min(t.lex)) || '>'
    FROM counted JOIN term t ON t.id = counted.profile AND t.kind = 2
    GROUP BY counted.subject)
SELECT named.entry, counted.subject, counted.profile
FROM counted JOIN named ON named.subject = counted.subject;

INSERT INTO patient_profile_values (entry, profile, node, date_of_birth, administrative_gender, deceased, date_of_death)
WITH held (entry, profile, version) AS (
  SELECT DISTINCT m.entry, m.profile, (SELECT min(v.o) FROM quad v WHERE v.s = m.profile AND v.p = k.current_version)
  FROM patient_profile_terms k CROSS JOIN patient_profile_member m
  JOIN term p ON p.id = m.profile AND p.kind = 2)
SELECT held.entry, held.profile, '<' || substr(held.entry, 2, length(held.entry) - 2) || '-' || sparql_sha256(p.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = held.version AND x.p = k.date_of_birth),
  (SELECT min(x.o) FROM quad x WHERE x.s = held.version AND x.p = k.administrative_gender),
  (SELECT min(x.o) FROM quad x WHERE x.s = held.version AND x.p = k.deceased),
  (SELECT min(x.o) FROM quad x WHERE x.s = held.version AND x.p = k.date_of_death)
FROM patient_profile_terms k CROSS JOIN held JOIN term p ON p.id = held.profile
WHERE held.version IS NOT NULL;

-- part: finish
DELETE FROM patient_profile_source;
INSERT OR IGNORE INTO patient_profile_source (profile, line, shown)
WITH
  records (record) AS (SELECT DISTINCT profile FROM patient_profile_member),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM patient_profile_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM patient_profile_terms k CROSS JOIN quad g
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
SELECT records.record,
  r.lex || CASE WHEN stated.document_shown IS NULL THEN '' ELSE ' from ' || stated.document END
    || CASE WHEN stated.retrieved_shown IS NULL THEN '' ELSE ', retrieved ' || stated.retrieved END
    || coalesce(', ' || stated.hospitals, ''),
  r.lex || coalesce(' from ' || stated.document_shown, '') || coalesce(', retrieved ' || stated.retrieved_shown, '')
    || coalesce(', ' || stated.hospitals_shown, '')
FROM records JOIN stated ON stated.record = records.record JOIN term r ON r.id = records.record;

-- part: triples
WITH
  said (s, p, o) AS (
    SELECT m.entry, '<https://ns.cascadeprotocol.org/cascade#entryMember>', t.nt
    FROM patient_profile_member m JOIN term t ON t.id = m.profile
    UNION ALL SELECT v.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', t.nt
      FROM patient_profile_values v JOIN term t ON t.id = v.profile
    UNION ALL SELECT v.node, '<https://ns.cascadeprotocol.org/cascade#dateOfBirth>', t.nt
      FROM patient_profile_values v JOIN term t ON t.id = v.date_of_birth
    UNION ALL SELECT v.node, '<https://ns.cascadeprotocol.org/cascade#administrativeGender>', t.nt
      FROM patient_profile_values v JOIN term t ON t.id = v.administrative_gender
    UNION ALL SELECT v.node, '<https://ns.cascadeprotocol.org/cascade#deceased>', t.nt
      FROM patient_profile_values v JOIN term t ON t.id = v.deceased
    UNION ALL SELECT v.node, '<https://ns.cascadeprotocol.org/cascade#dateOfDeath>', t.nt
      FROM patient_profile_values v JOIN term t ON t.id = v.date_of_death
    UNION ALL SELECT v.entry, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', v.node
      FROM patient_profile_values v),
  entries (entry) AS (SELECT DISTINCT entry FROM patient_profile_member)
SELECT s, p, o FROM said
UNION ALL SELECT entry, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
  '<https://ns.cascadeprotocol.org/cascade#PatientProfile>' FROM entries
