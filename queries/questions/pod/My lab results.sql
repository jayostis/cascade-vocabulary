-- A list question over the lab results screen, paged as queries/statements.sql says.
WITH
  page (entry, iri, sort_key, test, value, unit, status, performed, range_text, low_written, low_ucum, low_unit_text,
        high_written, high_ucum, high_unit_text, label) AS (
    SELECT r.entry, r.iri, r.sort_key, r.test, r.value, r.unit, r.status, r.performed, r.range_text, r.low_written,
           r.low_ucum, r.low_unit_text, r.high_written, r.high_ucum, r.high_unit_text, r.label
    FROM lab_result r
    WHERE r.sort_key > coalesce(:after, '')
      AND (NOT EXISTS (SELECT 1 FROM asked)
           OR EXISTS (SELECT 1 FROM lab_result_member m JOIN asked ON asked.term = m.record WHERE m.entry = r.entry))
    ORDER BY r.sort_key
    LIMIT coalesce(:page_size, -1)),
  strings (id, said) AS NOT MATERIALIZED (
    SELECT id, substr(nt, 2, length(nt) - 2 - coalesce(length(lang) + 1, 0)) FROM term
    WHERE datatype IN ('http://www.w3.org/2001/XMLSchema#string', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#langString'))
SELECT performed.nt AS performed, test.nt AS test, code.nt AS code, page.value AS value, unit.nt AS unit,
  status.nt AS status,
  (SELECT '"' || nullif(group_concat(flag, '\u001F' ORDER BY flag), '') || '"' FROM (
     SELECT DISTINCT sparql_replace(t.lex, '^.*/', '') AS flag
     FROM lab_result_interpretation i JOIN term t ON t.id = i.code WHERE i.entry = page.entry)) AS interpretations,
  range_text.nt AS referenceRangeText,
  CASE WHEN low.id IS NOT NULL THEN '"' || low.said || coalesce(' ' || CASE WHEN page.low_unit_text IS NOT NULL
    THEN low_unit_text.said ELSE low_ucum.said END, '') || '"' END AS referenceRangeLow,
  CASE WHEN high.id IS NOT NULL THEN '"' || high.said || coalesce(' ' || CASE WHEN page.high_unit_text IS NOT NULL
    THEN high_unit_text.said ELSE high_ucum.said END, '') || '"' END AS referenceRangeHigh,
  (SELECT '"' || group_concat(shown, '\u001F' ORDER BY line) || '"' FROM (
     SELECT m.lex || ' ' || n.lex || char(31) AS line, m.lex || ' ' || s.said AS shown
     FROM lab_result_member_values v JOIN term m ON m.id = v.member JOIN term n ON n.id = v.narrative
     JOIN strings s ON s.id = v.narrative
     WHERE v.entry = page.entry)) AS narrativeTexts,
  '"' || (SELECT count(*) FROM lab_result_member m WHERE m.entry = page.entry
          AND (NOT EXISTS (SELECT 1 FROM asked) OR m.record IN (SELECT term FROM asked)))
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"'
   FROM lab_result_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page
LEFT JOIN term performed ON performed.id = page.performed
LEFT JOIN term test ON test.id = page.test
LEFT JOIN term unit ON unit.id = page.unit
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term range_text ON range_text.id = page.range_text
LEFT JOIN strings low ON low.id = page.low_written
LEFT JOIN strings low_unit_text ON low_unit_text.id = page.low_unit_text
LEFT JOIN strings low_ucum ON low_ucum.id = page.low_ucum
LEFT JOIN strings high ON high.id = page.high_written
LEFT JOIN strings high_unit_text ON high_unit_text.id = page.high_unit_text
LEFT JOIN strings high_ucum ON high_ucum.id = page.high_ucum
LEFT JOIN term label ON label.id = page.label
LEFT JOIN lab_result_code c ON c.entry = page.entry
LEFT JOIN term code ON code.id = c.code
ORDER BY page.sort_key, code.kind, code.lex
