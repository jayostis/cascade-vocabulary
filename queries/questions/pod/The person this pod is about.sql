-- A list question over the patient profile screen, paged as queries/statements.sql says: a page is of subjects.
WITH
  k (type, subject_class, label, counts, yes, verdict, about, had_member, subject) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Subject>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#About>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#subject>')),
  page (subject, sort_key) AS (
    SELECT s.subject, s.sort_key FROM (
      SELECT DISTINCT q.s AS subject, t.kind || hex(coalesce(t.lex, '')) || '.' AS sort_key
      FROM k CROSS JOIN quad q JOIN term t ON t.id = q.s WHERE q.p = k.type AND q.o = k.subject_class) s
    WHERE s.sort_key > coalesce(:after, '')
    ORDER BY s.sort_key
    LIMIT coalesce(:page_size, -1)),
  held (subject, profile) AS (
    SELECT DISTINCT page.subject, h.o
    FROM k CROSS JOIN quad c ON c.p = k.counts AND c.o = k.yes
    CROSS JOIN quad su ON su.s = c.s AND su.p = k.subject
    CROSS JOIN page ON page.subject = su.o
    JOIN quad v ON v.s = su.s AND v.p = k.verdict AND v.o = k.about
    JOIN quad h ON h.s = su.s AND h.p = k.had_member),
  stated (subject, profile, birth, gender, deceased, death) AS (
    SELECT DISTINCT held.subject, p.lex,
      CASE b.kind WHEN 2 THEN b.lex WHEN 3 THEN substr(b.nt, 2, length(b.nt) - 2 - CASE WHEN b.lang IS NOT NULL
        THEN length(b.lang) + 1 WHEN b.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(b.datatype) + 4 END) END,
      CASE g.kind WHEN 2 THEN g.lex WHEN 3 THEN substr(g.nt, 2, length(g.nt) - 2 - CASE WHEN g.lang IS NOT NULL
        THEN length(g.lang) + 1 WHEN g.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(g.datatype) + 4 END) END,
      CASE d.kind WHEN 2 THEN d.lex WHEN 3 THEN substr(d.nt, 2, length(d.nt) - 2 - CASE WHEN d.lang IS NOT NULL
        THEN length(d.lang) + 1 WHEN d.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(d.datatype) + 4 END) END,
      CASE x.kind WHEN 2 THEN x.lex WHEN 3 THEN substr(x.nt, 2, length(x.nt) - 2 - CASE WHEN x.lang IS NOT NULL
        THEN length(x.lang) + 1 WHEN x.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(x.datatype) + 4 END) END
    FROM held JOIN term p ON p.id = held.profile AND p.kind = 2
    JOIN patient_profile_values v ON v.profile = held.profile
    LEFT JOIN term b ON b.id = v.date_of_birth LEFT JOIN term g ON g.id = v.administrative_gender
    LEFT JOIN term d ON d.id = v.deceased LEFT JOIN term x ON x.id = v.date_of_death)
SELECT DISTINCT subject.nt AS subject, label.nt AS subjectLabel,
  (SELECT '"' || group_concat(profile || ' ' || birth, '\u001F' ORDER BY profile) || '"' FROM (
     SELECT DISTINCT profile, birth FROM stated WHERE stated.subject = page.subject AND birth IS NOT NULL)) AS dateOfBirth,
  (SELECT '"' || group_concat(profile || ' ' || gender, '\u001F' ORDER BY profile) || '"' FROM (
     SELECT DISTINCT profile, gender FROM stated WHERE stated.subject = page.subject AND gender IS NOT NULL))
    AS administrativeGender,
  (SELECT '"' || group_concat(profile || ' ' || deceased, '\u001F' ORDER BY profile) || '"' FROM (
     SELECT DISTINCT profile, deceased FROM stated WHERE stated.subject = page.subject AND deceased IS NOT NULL))
    AS deceased,
  (SELECT '"' || group_concat(profile || ' ' || death, '\u001F' ORDER BY profile) || '"' FROM (
     SELECT DISTINCT profile, death FROM stated WHERE stated.subject = page.subject AND death IS NOT NULL)) AS dateOfDeath,
  (SELECT '"' || group_concat(shown, '\u001F' ORDER BY line) || '"' FROM (
     SELECT DISTINCT s.line, s.shown FROM held JOIN patient_profile_source s ON s.profile = held.profile
     WHERE held.subject = page.subject
       AND EXISTS (SELECT 1 FROM patient_profile_member m WHERE m.profile = held.profile))) AS sources,
  page.sort_key AS page_key
FROM page CROSS JOIN k JOIN term subject ON subject.id = page.subject
LEFT JOIN quad l ON l.s = page.subject AND l.p = k.label
LEFT JOIN term label ON label.id = l.o
ORDER BY page.sort_key
