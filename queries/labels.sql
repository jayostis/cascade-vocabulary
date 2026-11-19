-- The triples labels.rq gives, as s, p and o, one row for each: a name for each thing it names, from what the pod says of it.
-- It reads `quad` for everything but the entries, which it reads from the screens' tables, as the entry each view names
-- (N13), so a runtime runs it after every screen's fill and before any screen's finish, and writes its rows to the labels
-- file. A thing that has an rdfs:label outside the labels file is left alone, so the file's own earlier statements do not
-- hide a thing from it. A group's label is the least of the labels its combinations of optional values give, and a
-- combination with a missing value in what labels.rq concatenates gives none, as an unbound value there does.
--
-- Two parts, as a view's `.sql` has: `fill` makes the temporary tables the labels are made from and the labels, a branch of
-- labels.rq each, and `triples` is the one statement giving the rows. Each statement reads a table of the predicate it
-- starts from, never the whole of `quad` by that predicate in a loop, and none reads several of these tables through one
-- common table expression, which SQLite 3.54.1 refuses as nested too deep.

-- part: fill
DROP VIEW IF EXISTS temp.label_terms;
CREATE TEMP VIEW label_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>') AS label,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#recordKind>') AS record_kind,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>') AS current_version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>') AS current_revision,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#displayName>') AS display_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#displayDate>') AS display_date,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>') AS derived_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedFrom>') AS retrieved_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedOn>') AS retrieved_on,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>') AS generated_by,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#qualifiedAssociation>') AS association,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadRole>') AS had_role,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#agent>') AS agent,
  (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>') AS foaf_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#AuthorRole>') AS author_role,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#CustodianRole>') AS custodian_role,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#PatientRole>') AS patient_role,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>') AS generated_at_time,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#specializationOf>') AS specialization_of,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>') AS version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>') AS clinical_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#workflowStatus>') AS workflow_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verificationStatus>') AS verification_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergyCriticality>') AS allergy_criticality,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Revision>') AS revision,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#Entity>') AS entity,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>') AS judgment,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>') AS attributed_to,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>') AS verdict,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>') AS had_member,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#Activity>') AS activity,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#invalidated>') AS invalidated,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAssociatedWith>') AS associated_with,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#startedAtTime>') AS started_at_time,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#assertedJudgment>') AS asserted_judgment,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ReferenceSeries>') AS reference_series,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/version>') AS pav_version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#patient>') AS patient,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Subject>') AS subject,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#inEntry>') AS in_entry,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#dateFrom>') AS date_from,
  (SELECT g.id FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o JOIN term g ON g.nt = '<' || i.lex || '>'
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"labels.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS file,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/patient-profile.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS patient_address;

-- The statements of each predicate a branch starts from, once, so no later statement searches the whole of `quad` by that
-- predicate in a loop.
DROP TABLE IF EXISTS temp.label_record_kinds;
CREATE TEMP TABLE label_record_kinds (record INTEGER NOT NULL, kind INTEGER NOT NULL, PRIMARY KEY (record, kind)) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_record_kinds SELECT s, o FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#recordKind>');
DROP TABLE IF EXISTS temp.label_specializations;
CREATE TEMP TABLE label_specializations (record INTEGER NOT NULL, version INTEGER NOT NULL, PRIMARY KEY (record, version)) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_specializations SELECT o, s FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#specializationOf>');
DROP TABLE IF EXISTS temp.label_derivations;
CREATE TEMP TABLE label_derivations (doc INTEGER NOT NULL, rev INTEGER NOT NULL, PRIMARY KEY (doc, rev)) STRICT, WITHOUT ROWID;
CREATE INDEX label_derivations_rev ON label_derivations (rev);
INSERT OR IGNORE INTO label_derivations SELECT o, s FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>');
DROP TABLE IF EXISTS temp.label_retrievals;
CREATE TEMP TABLE label_retrievals (doc INTEGER NOT NULL, source INTEGER NOT NULL, PRIMARY KEY (doc, source)) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_retrievals SELECT s, o FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedFrom>');
DROP TABLE IF EXISTS temp.label_generations;
CREATE TEMP TABLE label_generations (subject INTEGER NOT NULL, activity INTEGER NOT NULL, PRIMARY KEY (subject, activity)) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_generations SELECT s, o FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>');
DROP TABLE IF EXISTS temp.label_invalidations;
CREATE TEMP TABLE label_invalidations (retracted INTEGER NOT NULL, activity INTEGER NOT NULL, PRIMARY KEY (retracted, activity)) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_invalidations SELECT o, s FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#invalidated>');
DROP TABLE IF EXISTS temp.label_patients;
CREATE TEMP TABLE label_patients (patient INTEGER NOT NULL, version INTEGER NOT NULL, PRIMARY KEY (patient, version)) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_patients SELECT o, s FROM quad WHERE p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#patient>');

-- The names of what made a document: of each agent in an association of its generating activity, in a role, its
-- rdfs:label and the foaf:name of its current version.
DROP TABLE IF EXISTS temp.label_doc_party;
CREATE TEMP TABLE label_doc_party (
  doc INTEGER NOT NULL,
  role INTEGER NOT NULL,
  name TEXT NOT NULL,
  PRIMARY KEY (doc, role, name)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_doc_party
SELECT g.subject, r.o, n.lex
FROM label_terms k CROSS JOIN label_generations g
CROSS JOIN quad a ON a.s = g.activity AND a.p = k.association
CROSS JOIN quad r ON r.s = a.o AND r.p = k.had_role AND r.o IN (k.author_role, k.custodian_role)
CROSS JOIN quad ag ON ag.s = a.o AND ag.p = k.agent
CROSS JOIN quad l ON l.s = ag.o AND l.p = k.label
CROSS JOIN term n ON n.id = l.o
WHERE n.lex IS NOT NULL;
INSERT OR IGNORE INTO label_doc_party
SELECT g.subject, r.o, n.lex
FROM label_terms k CROSS JOIN label_generations g
CROSS JOIN quad a ON a.s = g.activity AND a.p = k.association
CROSS JOIN quad r ON r.s = a.o AND r.p = k.had_role AND r.o IN (k.author_role, k.custodian_role)
CROSS JOIN quad ag ON ag.s = a.o AND ag.p = k.agent
CROSS JOIN quad cv ON cv.s = ag.o AND cv.p = k.current_version
CROSS JOIN quad f ON f.s = cv.o AND f.p = k.foaf_name
CROSS JOIN term n ON n.id = f.o
WHERE n.lex IS NOT NULL;

-- The same for a revision, of each document it derives from.
DROP TABLE IF EXISTS temp.label_rev_party;
CREATE TEMP TABLE label_rev_party (
  rev INTEGER NOT NULL,
  role INTEGER NOT NULL,
  name TEXT NOT NULL,
  PRIMARY KEY (rev, role, name)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_rev_party
SELECT d.rev, p.role, p.name
FROM label_doc_party p CROSS JOIN label_derivations d ON d.doc = p.doc;

-- What a document or a revision says it was made by: its authors, else its custodians; none stated gives no row.
DROP TABLE IF EXISTS temp.label_doc_author;
CREATE TEMP TABLE label_doc_author (
  doc INTEGER NOT NULL,
  author TEXT NOT NULL,
  PRIMARY KEY (doc, author)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_doc_author
SELECT c.doc, c.name
FROM label_terms k CROSS JOIN label_doc_party c
WHERE c.role = k.author_role
   OR (c.role = k.custodian_role
       AND NOT EXISTS (SELECT 1 FROM label_doc_party a WHERE a.doc = c.doc AND a.role = k.author_role));
DROP TABLE IF EXISTS temp.label_rev_author;
CREATE TEMP TABLE label_rev_author (
  rev INTEGER NOT NULL,
  author TEXT NOT NULL,
  PRIMARY KEY (rev, author)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_rev_author
SELECT c.rev, c.name
FROM label_terms k CROSS JOIN label_rev_party c
WHERE c.role = k.author_role
   OR (c.role = k.custodian_role
       AND NOT EXISTS (SELECT 1 FROM label_rev_party a WHERE a.rev = c.rev AND a.role = k.author_role));

-- Where a revision's documents were retrieved from, as the last segment of the address.
DROP TABLE IF EXISTS temp.label_rev_from;
CREATE TEMP TABLE label_rev_from (
  rev INTEGER NOT NULL,
  name TEXT NOT NULL,
  PRIMARY KEY (rev, name)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_rev_from
SELECT d.rev, sparql_replace(f.lex, '^.*/', '')
FROM label_retrievals r CROSS JOIN label_derivations d ON d.doc = r.doc CROSS JOIN term f ON f.id = r.source
WHERE f.lex IS NOT NULL;

-- Where a document was retrieved from, as the last two segments of the address.
DROP TABLE IF EXISTS temp.label_doc_from;
CREATE TEMP TABLE label_doc_from (
  doc INTEGER NOT NULL,
  name TEXT NOT NULL,
  PRIMARY KEY (doc, name)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_doc_from
SELECT r.doc, sparql_replace(f.lex, '^.*/([^/]+/[^/]+)$', '$1')
FROM label_retrievals r CROSS JOIN term f ON f.id = r.source
WHERE f.lex IS NOT NULL;

-- The documents: what a revision derives from, and each entity that is no version and no revision.
DROP TABLE IF EXISTS temp.label_documents;
CREATE TEMP TABLE label_documents (
  doc INTEGER PRIMARY KEY
) STRICT;
INSERT OR IGNORE INTO label_documents
SELECT d.doc FROM label_terms k CROSS JOIN quad r CROSS JOIN label_derivations d ON d.rev = r.s
WHERE r.p = k.type AND r.o = k.revision;
INSERT OR IGNORE INTO label_documents
SELECT e.s FROM label_terms k CROSS JOIN quad e
WHERE e.p = k.type AND e.o = k.entity
  AND NOT EXISTS (SELECT 1 FROM quad s WHERE s.s = e.s AND s.p = k.specialization_of)
  AND NOT EXISTS (SELECT 1 FROM quad r WHERE r.s = e.s AND r.p = k.type AND r.o = k.revision);

-- What a retraction's retracted thing says of itself, or of the judgment it asserts: its verdict, and the name of what
-- the judgment is about.
DROP TABLE IF EXISTS temp.label_retracted_verdict;
CREATE TEMP TABLE label_retracted_verdict (
  retracted INTEGER NOT NULL,
  verdict TEXT NOT NULL,
  PRIMARY KEY (retracted, verdict)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_retracted_verdict
SELECT i.retracted, sparql_replace(n.lex, '^.*#', '')
FROM label_terms k CROSS JOIN (SELECT DISTINCT retracted FROM label_invalidations) i
CROSS JOIN quad v ON v.s = i.retracted AND v.p = k.verdict CROSS JOIN term n ON n.id = v.o
WHERE n.lex IS NOT NULL;
INSERT OR IGNORE INTO label_retracted_verdict
SELECT i.retracted, sparql_replace(n.lex, '^.*#', '')
FROM label_terms k CROSS JOIN (SELECT DISTINCT retracted FROM label_invalidations) i
CROSS JOIN quad a ON a.s = i.retracted AND a.p = k.asserted_judgment
CROSS JOIN quad v ON v.s = a.o AND v.p = k.verdict CROSS JOIN term n ON n.id = v.o
WHERE n.lex IS NOT NULL;
DROP TABLE IF EXISTS temp.label_retracted_about;
CREATE TEMP TABLE label_retracted_about (
  retracted INTEGER NOT NULL,
  about TEXT NOT NULL,
  PRIMARY KEY (retracted, about)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_retracted_about
SELECT i.retracted, n.lex
FROM label_terms k CROSS JOIN (SELECT DISTINCT retracted FROM label_invalidations) i
CROSS JOIN quad m ON m.s = i.retracted AND m.p = k.had_member
CROSS JOIN label_specializations sp ON sp.record = m.o
CROSS JOIN quad d ON d.s = sp.version AND d.p = k.display_name CROSS JOIN term n ON n.id = d.o
WHERE n.lex IS NOT NULL;
INSERT OR IGNORE INTO label_retracted_about
SELECT i.retracted, n.lex
FROM label_terms k CROSS JOIN (SELECT DISTINCT retracted FROM label_invalidations) i
CROSS JOIN quad a ON a.s = i.retracted AND a.p = k.asserted_judgment
CROSS JOIN quad m ON m.s = a.o AND m.p = k.had_member
CROSS JOIN label_specializations sp ON sp.record = m.o
CROSS JOIN quad d ON d.s = sp.version AND d.p = k.display_name CROSS JOIN term n ON n.id = d.o
WHERE n.lex IS NOT NULL;

-- The entries each screen holds, by the entry as its view names it and by its lead, and each patient entry, named after
-- the patient profile view's address.
DROP TABLE IF EXISTS temp.label_entries;
CREATE TEMP TABLE label_entries (
  iri TEXT NOT NULL,
  lead INTEGER NOT NULL,
  PRIMARY KEY (iri, lead)
) STRICT, WITHOUT ROWID;
DROP TABLE IF EXISTS temp.label_patient_entries;
CREATE TEMP TABLE label_patient_entries (
  iri TEXT PRIMARY KEY
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO label_entries
SELECT iri, lead FROM allergy UNION ALL SELECT iri, lead FROM condition
UNION ALL SELECT iri, lead FROM immunization UNION ALL SELECT iri, lead FROM lab_result
UNION ALL SELECT iri, lead FROM medication_dispense UNION ALL SELECT iri, lead FROM medication
UNION ALL SELECT iri, lead FROM note UNION ALL SELECT iri, lead FROM procedure
UNION ALL SELECT iri, lead FROM report UNION ALL SELECT iri, lead FROM variant_interpretation
UNION ALL SELECT iri, lead FROM variant;
INSERT OR IGNORE INTO label_patient_entries
SELECT '<' || k.patient_address || '#' || substr(m.entry, 20, length(m.entry) - 20) || '>'
FROM label_terms k CROSS JOIN patient_profile_member m
WHERE k.patient_address IS NOT NULL;

-- Each thing's label, the least of those its combinations give, by the thing as N-Triples; a branch of labels.rq each.
DROP TABLE IF EXISTS temp.label_named;
CREATE TEMP TABLE label_named (
  thing TEXT NOT NULL,
  label TEXT NOT NULL,
  PRIMARY KEY (thing, label)
) STRICT, WITHOUT ROWID;

-- a record
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(
      kind.lex || ' · ' || coalesce(nm.lex, 'no name') || ' · ' ||
      coalesce(a.author || ' · ' || f.name,
               a.author || ' · received ' || substr(t.lex, 1, 10),
               a.author,
               CASE WHEN EXISTS (SELECT 1 FROM quad dd WHERE dd.s = cr.o AND dd.p = k.derived_from)
                    THEN 'unknown source' ELSE 'own entry' END)) AS label
  FROM label_terms k CROSS JOIN label_record_kinds x
  CROSS JOIN term st ON st.id = x.record
  CROSS JOIN term kind ON kind.id = x.kind
  CROSS JOIN quad cv ON cv.s = x.record AND cv.p = k.current_version
  CROSS JOIN quad cr ON cr.s = x.record AND cr.p = k.current_revision
  LEFT JOIN quad dn ON dn.s = cv.o AND dn.p = k.display_name
  LEFT JOIN term nm ON nm.id = dn.o
  LEFT JOIN label_rev_from f ON f.rev = cr.o
  LEFT JOIN label_rev_author a ON a.rev = cr.o
  LEFT JOIN quad gt ON gt.s = cr.o AND gt.p = k.generated_at_time
  LEFT JOIN term t ON t.id = gt.o
  WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = x.record AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- a version
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(
      kind.lex || ' version · ' || coalesce(nm.lex, 'no name') || ' · ' ||
      coalesce(CASE WHEN ve.lex = 'refuted' THEN 'ruled out' ELSE sa.lex END, sa.lex, ve.lex,
               'criticality ' || cr.lex, dt.lex, 'nothing stated') || ' · ' ||
      coalesce(f.name, a.author,
               CASE WHEN EXISTS (SELECT 1 FROM quad dd WHERE dd.s = rv.s AND dd.p = k.derived_from)
                    THEN 'unknown source' ELSE 'own entry' END) ||
      ' · first received ' || substr(t.lex, 1, 10)) AS label
  FROM label_terms k CROSS JOIN label_specializations sp
  CROSS JOIN term st ON st.id = sp.version
  CROSS JOIN quad rk ON rk.s = sp.record AND rk.p = k.record_kind
  CROSS JOIN term kind ON kind.id = rk.o
  CROSS JOIN quad rv ON rv.o = sp.version AND rv.p = k.version
  CROSS JOIN quad gt ON gt.s = rv.s AND gt.p = k.generated_at_time
  CROSS JOIN term t ON t.id = gt.o
  LEFT JOIN quad dn ON dn.s = sp.version AND dn.p = k.display_name
  LEFT JOIN term nm ON nm.id = dn.o
  LEFT JOIN quad sq ON sq.s = sp.version AND sq.p IN (k.clinical_status, k.workflow_status)
  LEFT JOIN term sa ON sa.id = sq.o
  LEFT JOIN quad vq ON vq.s = sp.version AND vq.p = k.verification_status
  LEFT JOIN term ve ON ve.id = vq.o
  LEFT JOIN quad cq ON cq.s = sp.version AND cq.p = k.allergy_criticality
  LEFT JOIN term cr ON cr.id = cq.o
  LEFT JOIN quad dq ON dq.s = sp.version AND dq.p = k.display_date
  LEFT JOIN term dt ON dt.id = dq.o
  LEFT JOIN label_rev_from f ON f.rev = rv.s
  LEFT JOIN label_rev_author a ON a.rev = rv.s
  WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = sp.version AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- a revision
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(
      'Revision · ' || coalesce(nm.lex, 'no name') || ' · ' ||
      coalesce(f.name, a.author,
               CASE WHEN EXISTS (SELECT 1 FROM quad dd WHERE dd.s = ty.s AND dd.p = k.derived_from)
                    THEN 'unknown source' ELSE 'own entry' END) ||
      ' · received ' || substr(t.lex, 1, 10)) AS label
  FROM label_terms k CROSS JOIN quad ty
  CROSS JOIN term st ON st.id = ty.s
  CROSS JOIN quad rv ON rv.s = ty.s AND rv.p = k.version
  CROSS JOIN quad gt ON gt.s = ty.s AND gt.p = k.generated_at_time
  CROSS JOIN term t ON t.id = gt.o
  LEFT JOIN quad dn ON dn.s = rv.o AND dn.p = k.display_name
  LEFT JOIN term nm ON nm.id = dn.o
  LEFT JOIN label_rev_from f ON f.rev = ty.s
  LEFT JOIN label_rev_author a ON a.rev = ty.s
  WHERE ty.p = k.type AND ty.o = k.revision
    AND NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = ty.s AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- a document
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(
      'Document · ' || coalesce(a.author, 'unknown source') || coalesce(' · ' || f.name, '') ||
      coalesce(' · retrieved ' || substr(rn.lex, 1, 10), '')) AS label
  FROM label_terms k CROSS JOIN label_documents docs
  CROSS JOIN term st ON st.id = docs.doc
  LEFT JOIN label_doc_author a ON a.doc = docs.doc
  LEFT JOIN label_doc_from f ON f.doc = docs.doc
  LEFT JOIN quad ro ON ro.s = docs.doc AND ro.p = k.retrieved_on
  LEFT JOIN term rn ON rn.id = ro.o
  WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = docs.doc AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- a judgment
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(
      sparql_replace(vd.lex, '^.*#', '') || ' · ' ||
      coalesce((SELECT min(mn.lex) FROM quad ml CROSS JOIN term mn ON mn.id = ml.o
                WHERE ml.s = w.o AND ml.p = k.label AND ml.g IS NOT k.file),
               CASE WHEN ro.o IS NULL THEN NULL WHEN ro.o = k.patient_role THEN 'the patient' ELSE 'a person' END) || ' · ' ||
      CASE WHEN t.lex IS NOT NULL THEN substr(t.lex, 1, 10)
           ELSE substr(sparql_replace(st.lex, '^.*[:/#]', ''), 1, 8) END || ' · ' ||
      coalesce(ab.lex, 'a patient profile')) AS label
  FROM label_terms k CROSS JOIN quad j
  CROSS JOIN term st ON st.id = j.s
  CROSS JOIN quad w ON w.s = j.s AND w.p = k.attributed_to
  LEFT JOIN quad gt ON gt.s = j.s AND gt.p = k.generated_at_time
  LEFT JOIN term t ON t.id = gt.o
  LEFT JOIN quad vq ON vq.s = j.s AND vq.p = k.verdict
  LEFT JOIN term vd ON vd.id = vq.o
  LEFT JOIN quad gb ON gb.s = j.s AND gb.p = k.generated_by
  LEFT JOIN quad qa ON qa.s = gb.o AND qa.p = k.association
  LEFT JOIN quad qg ON qg.s = qa.o AND qg.p = k.agent AND qg.o = w.o
  LEFT JOIN quad ro ON ro.s = qg.s AND ro.p = k.had_role
  LEFT JOIN quad hm ON hm.s = j.s AND hm.p = k.had_member
  LEFT JOIN label_specializations sp ON sp.record = hm.o
  LEFT JOIN quad dn ON dn.s = sp.version AND dn.p = k.display_name
  LEFT JOIN term ab ON ab.id = dn.o
  WHERE j.p = k.type AND j.o = k.judgment
    AND NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = j.s AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- a retraction
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(
      'Retraction · ' ||
      coalesce(nm.lex, CASE WHEN wa.o IS NULL THEN 'a release' WHEN ro.o IS NULL THEN NULL
                            WHEN ro.o = k.patient_role THEN 'the patient' ELSE 'a person' END) || ' · ' ||
      CASE WHEN t.lex IS NOT NULL THEN substr(t.lex, 1, 10)
           ELSE substr(sparql_replace(st.lex, '^.*[:/#]', ''), 1, 8) END || ' · of ' ||
      coalesce(rv.verdict, 'a judgment') || ' · ' || coalesce(ra.about, 'a patient profile')) AS label
  FROM label_terms k CROSS JOIN label_invalidations iv
  CROSS JOIN term st ON st.id = iv.activity
  CROSS JOIN quad ty ON ty.s = iv.activity AND ty.p = k.type AND ty.o = k.activity
  LEFT JOIN quad wa ON wa.s = iv.activity AND wa.p = k.associated_with
  LEFT JOIN quad nl ON nl.s = wa.o AND nl.p = k.label AND nl.g IS NOT k.file
  LEFT JOIN term nm ON nm.id = nl.o
  LEFT JOIN quad qa ON qa.s = iv.activity AND qa.p = k.association
  LEFT JOIN quad qg ON qg.s = qa.o AND qg.p = k.agent AND qg.o = wa.o
  LEFT JOIN quad ro ON ro.s = qg.s AND ro.p = k.had_role
  LEFT JOIN quad sq ON sq.s = iv.activity AND sq.p = k.started_at_time
  LEFT JOIN term t ON t.id = sq.o
  LEFT JOIN label_retracted_verdict rv ON rv.retracted = iv.retracted
  LEFT JOIN label_retracted_about ra ON ra.retracted = iv.retracted
  WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = iv.activity AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- a reference version
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing, min(nm.lex || ' · ' || vn.lex) AS label
  FROM label_terms k CROSS JOIN label_specializations sp
  CROSS JOIN term st ON st.id = sp.version
  CROSS JOIN quad ty ON ty.s = sp.record AND ty.p = k.type AND ty.o = k.reference_series
  CROSS JOIN quad sl ON sl.s = sp.record AND sl.p = k.label
  CROSS JOIN term nm ON nm.id = sl.o
  CROSS JOIN quad pv ON pv.s = sp.version AND pv.p = k.pav_version
  CROSS JOIN term vn ON vn.id = pv.o
  WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = sp.version AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- an entry a view holds
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT e.iri AS thing, min(kind.lex || ' entry' || coalesce(' · ' || nm.lex, '') || coalesce(' · ' || dt.lex, '')) AS label
  FROM label_terms k CROSS JOIN label_entries e
  CROSS JOIN quad rk ON rk.s = e.lead AND rk.p = k.record_kind
  CROSS JOIN term kind ON kind.id = rk.o
  LEFT JOIN quad cv ON cv.s = e.lead AND cv.p = k.current_version
  LEFT JOIN quad dn ON dn.s = cv.o AND dn.p = k.display_name
  LEFT JOIN term nm ON nm.id = dn.o
  LEFT JOIN quad ie ON ie.s = e.lead AND ie.p = k.in_entry
  LEFT JOIN quad df ON df.s = ie.o AND df.p = k.date_from
  LEFT JOIN quad dv ON dv.s = df.o AND dv.p = k.current_version
  LEFT JOIN quad dd ON dd.s = dv.o AND dd.p = k.display_date
  LEFT JOIN term dt ON dt.id = dd.o
  WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = (SELECT id FROM term WHERE nt = e.iri) AND l.p = k.label
                    AND l.g IS NOT k.file)
  GROUP BY e.iri) WHERE label IS NOT NULL;

-- a patient entry
INSERT OR IGNORE INTO label_named
SELECT e.iri, 'Patient entry'
FROM label_terms k CROSS JOIN label_patient_entries e
WHERE NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = (SELECT id FROM term WHERE nt = e.iri) AND l.p = k.label
                  AND l.g IS NOT k.file);

-- the patient of a patient profile, where it is no subject
INSERT OR IGNORE INTO label_named
SELECT thing, label FROM (
  SELECT st.nt AS thing,
         min('Patient profile · ' || coalesce(a.author, 'unknown source') || ' · first received ' || substr(t.lex, 1, 10)) AS label
  FROM label_terms k CROSS JOIN label_patients pv
  CROSS JOIN term st ON st.id = pv.patient
  CROSS JOIN quad rv ON rv.o = pv.version AND rv.p = k.version
  CROSS JOIN quad gt ON gt.s = rv.s AND gt.p = k.generated_at_time
  CROSS JOIN term t ON t.id = gt.o
  LEFT JOIN label_rev_author a ON a.rev = rv.s
  WHERE NOT EXISTS (SELECT 1 FROM quad s WHERE s.s = pv.patient AND s.p = k.type AND s.o = k.subject)
    AND NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = pv.patient AND l.p = k.label AND l.g IS NOT k.file)
  GROUP BY st.nt) WHERE label IS NOT NULL;

-- the subject
INSERT OR IGNORE INTO label_named
SELECT st.nt, 'The person this pod is about'
FROM label_terms k CROSS JOIN quad s CROSS JOIN term st ON st.id = s.s
WHERE s.p = k.type AND s.o = k.subject
  AND NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = s.s AND l.p = k.label AND l.g IS NOT k.file);

-- part: triples
SELECT thing AS s, '<http://www.w3.org/2000/01/rdf-schema#label>' AS p,
       '"' || replace(replace(replace(replace(label, '\', '\\'), '"', '\"'), char(10), '\n'), char(13), '\r') || '"' AS o
FROM label_named
