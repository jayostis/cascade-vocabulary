WITH
  k (type, judgment_class, counts, yes, verdict, about, not_about, member, subject, attributed, current_version,
     specialization_of, patient, label, name, derived_from, version) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#About>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#NotAbout>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#subject>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#specializationOf>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#patient>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>')),
  -- An agent is a hub every file of its documents restates, so its names are looked up once, not once for each document.
  agent_names (agent, hospital) AS (
    SELECT DISTINCT a.o, l.o FROM (SELECT DISTINCT q.o FROM k CROSS JOIN quad q ON q.p = k.attributed) a CROSS JOIN k
    CROSS JOIN quad l ON l.s = a.o AND l.p = k.label
    UNION
    SELECT DISTINCT a.o, n.o FROM (SELECT DISTINCT q.o FROM k CROSS JOIN quad q ON q.p = k.attributed) a CROSS JOIN k
    CROSS JOIN quad cv ON cv.s = a.o AND cv.p = k.current_version CROSS JOIN quad n ON n.s = cv.o AND n.p = k.name),
  hospitals (document, hospital) AS (
    SELECT d.s, n.hospital FROM k CROSS JOIN quad d ON d.p = k.attributed CROSS JOIN agent_names n ON n.agent = d.o),
  sent (profile, hospital, record) AS (
    SELECT pa.o, h.hospital, sp.o
    FROM k CROSS JOIN quad rv ON rv.p = k.version
    CROSS JOIN quad wd ON wd.s = rv.s AND wd.p = k.derived_from
    CROSS JOIN hospitals h ON h.document = wd.o
    CROSS JOIN quad pa ON pa.s = rv.o AND pa.p = k.patient
    CROSS JOIN quad sp ON sp.s = rv.o AND sp.p = k.specialization_of
    UNION
    SELECT pa.o, NULL, sp.o
    FROM k CROSS JOIN quad pa ON pa.p = k.patient
    CROSS JOIN quad sp ON sp.s = pa.s AND sp.p = k.specialization_of
    WHERE NOT EXISTS (SELECT 1 FROM quad rv CROSS JOIN quad wd ON wd.s = rv.s AND wd.p = k.derived_from
                      CROSS JOIN hospitals h ON h.document = wd.o
                      WHERE rv.p = k.version AND rv.o = pa.s)),
  counted (profile, hospital, records) AS (
    SELECT profile, hospital, count(DISTINCT record) FROM sent GROUP BY profile, hospital),
  -- A solution for each About judgment's counted value: it counts when it has one that is true and no counting NotAbout
  -- of the same profile for the same subject.
  claimed (profile, subject, about, counted) AS (
    SELECT DISTINCT h.o, su.o, a.s, cu.o
    FROM k CROSS JOIN quad a ON a.p = k.type AND a.o = k.judgment_class
    CROSS JOIN quad v ON v.s = a.s AND v.p = k.verdict AND v.o = k.about
    CROSS JOIN quad h ON h.s = a.s AND h.p = k.member
    CROSS JOIN quad su ON su.s = a.s AND su.p = k.subject
    LEFT JOIN quad cu ON cu.s = a.s AND cu.p = k.counts),
  solved (profile, hospital, records, subject, about, counts, profile_label, subject_label, about_label) AS (
    SELECT DISTINCT counted.profile, counted.hospital, counted.records, claimed.subject, claimed.about,
      claimed.counted = k.yes AND NOT EXISTS (
        SELECT 1 FROM quad d CROSS JOIN quad dv ON dv.s = d.s AND dv.p = k.verdict AND dv.o = k.not_about
        CROSS JOIN quad dh ON dh.s = d.s AND dh.p = k.member AND dh.o = claimed.profile
        CROSS JOIN quad ds ON ds.s = d.s AND ds.p = k.subject AND ds.o = claimed.subject
        WHERE d.p = k.counts AND d.o = k.yes),
      pl.o, sl.o, al.o
    FROM counted CROSS JOIN k CROSS JOIN claimed ON claimed.profile = counted.profile
    LEFT JOIN quad pl ON pl.s = counted.profile AND pl.p = k.label
    LEFT JOIN quad sl ON sl.s = claimed.subject AND sl.p = k.label
    LEFT JOIN quad al ON al.s = claimed.about AND al.p = k.label)
SELECT profile.nt AS profile, profile_label.nt AS profileLabel, subject.nt AS subject, subject_label.nt AS subjectLabel,
  CASE WHEN solved.counts THEN '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'
       ELSE '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>' END AS counts,
  about.nt AS about, about_label.nt AS aboutLabel, hospital.nt AS hospital,
  '"' || solved.records || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records
FROM solved CROSS JOIN term profile ON profile.id = solved.profile
CROSS JOIN term subject ON subject.id = solved.subject
CROSS JOIN term about ON about.id = solved.about
LEFT JOIN term hospital ON hospital.id = solved.hospital
LEFT JOIN term profile_label ON profile_label.id = solved.profile_label
LEFT JOIN term subject_label ON subject_label.id = solved.subject_label
LEFT JOIN term about_label ON about_label.id = solved.about_label
ORDER BY profile_label.kind, profile_label.lex, profile.kind, profile.lex, about_label.kind, about_label.lex, about.kind,
  about.lex, hospital.kind, hospital.lex
