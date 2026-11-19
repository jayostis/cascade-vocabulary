-- A list question over the allergies screen, paged as queries/statements.sql says.
WITH
  page (entry, iri, sort_key, name, status, criticality, category, onset, label) AS (
    SELECT a.entry, a.iri, a.sort_key, a.name, a.status, a.criticality, a.category, a.onset, a.label FROM allergy a
    WHERE a.sort_key > coalesce(:after, '')
      AND a.name IS NOT NULL
      AND (a.status IS NULL OR a.status = (SELECT id FROM term WHERE nt = '"active"'))
      AND EXISTS (SELECT 1 FROM allergy_member m WHERE m.entry = a.entry)
      AND EXISTS (SELECT 1 FROM allergy_member_values v WHERE v.entry = a.entry)
      AND (NOT EXISTS (SELECT 1 FROM asked)
           OR EXISTS (SELECT 1 FROM allergy_member m JOIN asked ON asked.term = m.record WHERE m.entry = a.entry))
    ORDER BY a.sort_key
    LIMIT coalesce(:page_size, -1)),
  strings (id, said) AS NOT MATERIALIZED (
    SELECT id, CASE kind WHEN 2 THEN lex WHEN 3 THEN substr(nt, 2, length(nt) - 2 - CASE WHEN lang IS NOT NULL
      THEN length(lang) + 1 WHEN datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
      ELSE length(datatype) + 4 END) END FROM term),
  texts (entry, member, plain, shown) AS (
    SELECT entry, member, group_concat(plain, ', ' ORDER BY plain), group_concat(shown, ', ' ORDER BY plain) FROM (
      SELECT DISTINCT x.entry, x.member, t.lex AS plain, s.said AS shown
      FROM allergy_member_values_reaction_text x JOIN page ON page.entry = x.entry
      JOIN term t ON t.id = x.code JOIN strings s ON s.id = x.code)
    GROUP BY entry, member),
  codes (entry, member, plain, shown) AS (
    SELECT entry, member, group_concat(plain, ', ' ORDER BY plain), group_concat(shown, ', ' ORDER BY plain) FROM (
      SELECT DISTINCT x.entry, x.member, t.lex AS plain, s.said AS shown
      FROM allergy_member_values_reaction_code x JOIN page ON page.entry = x.entry
      JOIN term t ON t.id = x.code JOIN strings s ON s.id = x.code)
    GROUP BY entry, member),
  lines (entry, line, shown) AS (
    SELECT v.entry,
      m.lex || CASE WHEN coalesce(texts.plain, '') <> '' THEN ' ' || texts.plain ELSE '' END
        || CASE WHEN coalesce(codes.plain, '') <> '' THEN ' (' || codes.plain || ')' ELSE '' END
        || coalesce(', ' || severity.lex, ''),
      m.lex || CASE WHEN coalesce(texts.plain, '') <> '' THEN ' ' || texts.shown ELSE '' END
        || CASE WHEN coalesce(codes.plain, '') <> '' THEN ' (' || codes.shown || ')' ELSE '' END
        || coalesce(', ' || severity_said.said, '')
    FROM allergy_member_values v JOIN page ON page.entry = v.entry JOIN term m ON m.id = v.member
    LEFT JOIN texts ON texts.entry = v.entry AND texts.member = v.member
    LEFT JOIN codes ON codes.entry = v.entry AND codes.member = v.member
    LEFT JOIN term severity ON severity.id = v.severity
    LEFT JOIN strings severity_said ON severity_said.id = v.severity
    WHERE coalesce(texts.plain, '') <> '' OR coalesce(codes.plain, '') <> '' OR v.severity IS NOT NULL)
SELECT name.nt AS allergenName, code.nt AS code, criticality.nt AS criticality,
  coalesce(status.nt, '"not stated"') AS status, category.nt AS category, onset.nt AS onset,
  (SELECT '"' || group_concat(l.shown, '\u001F' ORDER BY l.line) || '"' FROM lines l WHERE l.entry = page.entry)
    AS reactionsByRecord,
  '"' || (SELECT count(*) FROM allergy_member m WHERE m.entry = page.entry
          AND (NOT EXISTS (SELECT 1 FROM asked) OR m.record IN (SELECT term FROM asked)))
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"'
   FROM allergy_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page
JOIN term name ON name.id = page.name
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term criticality ON criticality.id = page.criticality
LEFT JOIN term category ON category.id = page.category
LEFT JOIN term onset ON onset.id = page.onset
LEFT JOIN term label ON label.id = page.label
LEFT JOIN allergy_code c ON c.entry = page.entry
LEFT JOIN term code ON code.id = c.code
ORDER BY page.sort_key, code.kind, code.lex
