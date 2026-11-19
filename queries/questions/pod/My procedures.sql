-- A list question over the procedures screen, paged as queries/statements.sql says.
WITH
  page (entry, iri, sort_key, name, status, date, label) AS (
    SELECT p.entry, p.iri, p.sort_key, p.name, p.status, p.date, p.label FROM procedure p
    WHERE p.sort_key > coalesce(:after, '')
      AND EXISTS (SELECT 1 FROM procedure_member m WHERE m.entry = p.entry)
      AND EXISTS (SELECT 1 FROM procedure_member_values v WHERE v.entry = p.entry)
      AND (NOT EXISTS (SELECT 1 FROM asked)
           OR EXISTS (SELECT 1 FROM procedure_member m JOIN asked ON asked.term = m.record WHERE m.entry = p.entry))
    ORDER BY p.sort_key
    LIMIT coalesce(:page_size, -1)),
  strings (id, said) AS NOT MATERIALIZED (
    SELECT id, CASE kind WHEN 2 THEN lex WHEN 3 THEN substr(nt, 2, length(nt) - 2 - CASE WHEN lang IS NOT NULL
      THEN length(lang) + 1 WHEN datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
      ELSE length(datatype) + 4 END) END FROM term)
SELECT performed.nt AS performed, name.nt AS procedure, code.nt AS procedureCode, status.nt AS status,
  (SELECT '"' || group_concat(shown, '\u001F' ORDER BY line) || '"' FROM (
     SELECT m.lex || ' ' || n.lex || char(31) AS line, m.lex || ' ' || s.said AS shown
     FROM procedure_member_values v JOIN term m ON m.id = v.member JOIN term n ON n.id = v.narrative
     JOIN strings s ON s.id = v.narrative
     WHERE v.entry = page.entry)) AS narrativeTexts,
  '"' || (SELECT count(*) FROM procedure_member m WHERE m.entry = page.entry
          AND (NOT EXISTS (SELECT 1 FROM asked) OR m.record IN (SELECT term FROM asked)))
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"'
   FROM procedure_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page
LEFT JOIN term performed ON performed.id = page.date
LEFT JOIN term name ON name.id = page.name
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term label ON label.id = page.label
LEFT JOIN procedure_code first ON first.entry = page.entry
  AND NOT EXISTS (SELECT 1 FROM procedure_code y JOIN term u ON u.id = y.code JOIN term t ON t.id = first.code
                  WHERE y.entry = first.entry AND u.lex < t.lex)
LEFT JOIN term code ON code.id = first.code
ORDER BY page.sort_key, code.kind, code.lex
