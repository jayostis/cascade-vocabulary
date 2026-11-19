-- A list question over the immunizations screen, paged as queries/statements.sql says.
WITH page (entry, iri, sort_key, name, status, date, label) AS (
  SELECT i.entry, i.iri, i.sort_key, i.name, i.status, i.date, i.label FROM immunization i
  WHERE i.sort_key > coalesce(:after, '')
    AND EXISTS (SELECT 1 FROM immunization_member m WHERE m.entry = i.entry)
    AND (NOT EXISTS (SELECT 1 FROM asked)
         OR EXISTS (SELECT 1 FROM immunization_member m JOIN asked ON asked.term = m.record WHERE m.entry = i.entry))
  ORDER BY i.sort_key
  LIMIT coalesce(:page_size, -1))
SELECT given.nt AS given, name.nt AS vaccine, code.nt AS code, status.nt AS status,
  '"' || (SELECT count(*) FROM immunization_member m WHERE m.entry = page.entry
          AND (NOT EXISTS (SELECT 1 FROM asked) OR m.record IN (SELECT term FROM asked)))
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"'
   FROM immunization_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page
LEFT JOIN term given ON given.id = page.date
LEFT JOIN term name ON name.id = page.name
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term label ON label.id = page.label
LEFT JOIN immunization_code c ON c.entry = page.entry
LEFT JOIN term code ON code.id = c.code
ORDER BY page.sort_key, code.kind, code.lex
