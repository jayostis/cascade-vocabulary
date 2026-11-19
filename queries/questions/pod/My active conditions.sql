-- A list question over the conditions screen, paged as queries/statements.sql says.
WITH page (entry, iri, sort_key, name, onset, label) AS (
  SELECT c.entry, c.iri, c.sort_key, c.name, c.onset, c.label FROM condition c
  WHERE c.sort_key > coalesce(:after, '')
    AND c.name IS NOT NULL
    AND c.status = (SELECT id FROM term WHERE nt = '"active"')
    AND (c.verification IS NULL OR c.verification IS NOT (SELECT id FROM term WHERE nt = '"refuted"'))
    AND (NOT EXISTS (SELECT 1 FROM asked)
         OR EXISTS (SELECT 1 FROM condition_member m JOIN asked ON asked.term = m.record WHERE m.entry = c.entry))
  ORDER BY c.sort_key
  LIMIT coalesce(:page_size, -1))
SELECT name.nt AS condition, code.nt AS conditionCode, onset.nt AS onset,
  (SELECT '"' || group_concat(f.shown, '\u001F' ORDER BY f.name_key, f.for_entry) || '"'
   FROM condition_for f WHERE f.entry = page.entry) AS entriesForIt,
  '"' || (SELECT count(*) FROM condition_member m WHERE m.entry = page.entry
          AND (NOT EXISTS (SELECT 1 FROM asked) OR m.record IN (SELECT term FROM asked)))
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"'
   FROM condition_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page
JOIN term name ON name.id = page.name
LEFT JOIN term onset ON onset.id = page.onset
LEFT JOIN term label ON label.id = page.label
LEFT JOIN condition_code first ON first.entry = page.entry
  AND NOT EXISTS (SELECT 1 FROM condition_code y JOIN term u ON u.id = y.code JOIN term t ON t.id = first.code
                  WHERE y.entry = first.entry AND u.lex < t.lex)
LEFT JOIN term code ON code.id = first.code
ORDER BY page.sort_key, code.kind, code.lex
