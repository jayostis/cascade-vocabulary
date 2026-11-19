WITH
  k (type, subject_class, person, counts, yes, verdict, about, not_about, member, subject, attributed, generated_at,
     current_version, patient, label, name, derived_from, version) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Subject>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#Person>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#About>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#NotAbout>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#subject>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#patient>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>')),
  counting (judgment, verdict) AS (
    SELECT c.s, v.o FROM k CROSS JOIN quad c ON c.p = k.counts AND c.o = k.yes
    CROSS JOIN quad v ON v.s = c.s AND v.p = k.verdict AND v.o IN (k.about, k.not_about)),
  named (profile) AS (
    SELECT DISTINCT pa.o FROM k CROSS JOIN quad pa ON pa.p = k.patient
    CROSS JOIN quad cv ON cv.o = pa.s AND cv.p = k.current_version),
  -- Each profile a counting judgment's verdict does not settle, nor the profile being the subject.
  unsettled (profile) AS (
    SELECT named.profile FROM named CROSS JOIN k
    WHERE NOT EXISTS (SELECT 1 FROM quad t WHERE t.s = named.profile AND t.p = k.type AND t.o = k.subject_class)
      AND NOT EXISTS (SELECT 1 FROM counting c CROSS JOIN quad h ON h.s = c.judgment AND h.p = k.member
                      WHERE h.o = named.profile)),
  -- Each person who made a counting About of the profile, for a subject a counting NotAbout of it is for, that no
  -- counting NotAbout of the same maker, made after it, outranks.
  said_about (profile, who) AS (
    SELECT DISTINCT p.o, ag.o
    FROM k CROSS JOIN counting op CROSS JOIN quad ov ON ov.s = op.judgment AND ov.p = k.verdict AND ov.o = k.not_about
    CROSS JOIN counting ag_c CROSS JOIN quad agv ON agv.s = ag_c.judgment AND agv.p = k.verdict AND agv.o = k.about
    CROSS JOIN quad p ON p.s = op.judgment AND p.p = k.member
    CROSS JOIN quad ap ON ap.s = ag_c.judgment AND ap.p = k.member AND ap.o = p.o
    CROSS JOIN quad os ON os.s = op.judgment AND os.p = k.subject
    CROSS JOIN quad ags ON ags.s = ag_c.judgment AND ags.p = k.subject AND ags.o = os.o
    CROSS JOIN quad ag ON ag.s = ag_c.judgment AND ag.p = k.attributed
    CROSS JOIN quad ma ON ma.s = ag_c.judgment AND ma.p = k.generated_at
    CROSS JOIN quad pt ON pt.s = ag.o AND pt.p = k.type AND pt.o = k.person
    WHERE NOT EXISTS (
      SELECT 1 FROM counting ou CROSS JOIN quad ouv ON ouv.s = ou.judgment AND ouv.p = k.verdict AND ouv.o = k.not_about
      CROSS JOIN quad oup ON oup.s = ou.judgment AND oup.p = k.member AND oup.o = p.o
      CROSS JOIN quad ous ON ous.s = ou.judgment AND ous.p = k.subject AND ous.o = os.o
      CROSS JOIN quad oua ON oua.s = ou.judgment AND oua.p = k.attributed AND oua.o = ag.o
      CROSS JOIN quad oul ON oul.s = ou.judgment AND oul.p = k.generated_at
      WHERE sparql_compare((SELECT nt FROM term WHERE id = oul.o), (SELECT nt FROM term WHERE id = ma.o)) = 1)),
  said_not_about (profile, who) AS (
    SELECT DISTINCT p.o, a.o FROM k CROSS JOIN counting d
    CROSS JOIN quad dv ON dv.s = d.judgment AND dv.p = k.verdict AND dv.o = k.not_about
    CROSS JOIN quad p ON p.s = d.judgment AND p.p = k.member
    CROSS JOIN quad a ON a.s = d.judgment AND a.p = k.attributed),
  held_back (profile, said_about, said_not_about) AS (
    SELECT a.profile, a.said, n.said
    FROM (SELECT profile, group_concat(t.lex, '\u001F' ORDER BY t.lex) AS said
          FROM said_about CROSS JOIN term t ON t.id = said_about.who GROUP BY profile) a
    CROSS JOIN (SELECT profile, group_concat(t.lex, '\u001F' ORDER BY t.lex) AS said
          FROM said_not_about CROSS JOIN term t ON t.id = said_not_about.who GROUP BY profile) n ON n.profile = a.profile),
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
    SELECT pa.o, h.hospital, cv.s
    FROM k CROSS JOIN quad rv ON rv.p = k.version
    CROSS JOIN quad wd ON wd.s = rv.s AND wd.p = k.derived_from
    CROSS JOIN hospitals h ON h.document = wd.o
    CROSS JOIN quad cv ON cv.o = rv.o AND cv.p = k.current_version
    CROSS JOIN quad pa ON pa.s = rv.o AND pa.p = k.patient
    UNION
    SELECT pa.o, NULL, cv.s
    FROM k CROSS JOIN quad pa ON pa.p = k.patient
    CROSS JOIN quad cv ON cv.o = pa.s AND cv.p = k.current_version
    WHERE NOT EXISTS (SELECT 1 FROM quad rv CROSS JOIN quad wd ON wd.s = rv.s AND wd.p = k.derived_from
                      CROSS JOIN hospitals h ON h.document = wd.o
                      WHERE rv.p = k.version AND rv.o = pa.s)),
  counted (profile, hospital, records) AS (
    SELECT profile, hospital, count(DISTINCT record) FROM sent GROUP BY profile, hospital),
  needing (profile, needs, said_about, said_not_about) AS (
    SELECT profile, 'no one has said whether it is the subject''s', NULL, NULL FROM unsettled
    UNION ALL
    SELECT profile, 'judged both about and not about the subject', said_about, said_not_about FROM held_back),
  solved (profile, needs, said_about, said_not_about, hospital, records, label) AS (
    SELECT DISTINCT needing.profile, needing.needs, needing.said_about, needing.said_not_about, counted.hospital,
      counted.records, l.o
    FROM needing CROSS JOIN k CROSS JOIN counted ON counted.profile = needing.profile
    LEFT JOIN quad l ON l.s = needing.profile AND l.p = k.label)
SELECT profile.nt AS profile, label.nt AS profileLabel, '"' || solved.needs || '"' AS needs, hospital.nt AS hospital,
  '"' || solved.records || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  '"' || solved.said_about || '"' AS saidAbout, '"' || solved.said_not_about || '"' AS saidNotAbout
FROM solved CROSS JOIN term profile ON profile.id = solved.profile
LEFT JOIN term label ON label.id = solved.label
LEFT JOIN term hospital ON hospital.id = solved.hospital
ORDER BY solved.needs, label.kind, label.lex, profile.kind, profile.lex, hospital.kind, hospital.lex
