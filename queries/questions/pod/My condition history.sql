-- A list question over the conditions screen, paged as queries/statements.sql says.
WITH
  page (entry, iri, sort_key, name, status, verification, onset, abatement, label, refuted) AS (
    SELECT c.entry, c.iri, c.sort_key, c.name, c.status, c.verification, c.onset, c.abatement, c.label,
      coalesce(c.verification = (SELECT id FROM term WHERE nt = '"refuted"'), 0)
    FROM condition c
    WHERE c.sort_key > coalesce(:after, '')
      AND c.name IS NOT NULL
      AND EXISTS (SELECT 1 FROM condition_member r WHERE r.entry = c.entry)
      AND EXISTS (SELECT 1 FROM condition_member_values v WHERE v.entry = c.entry)
      AND (NOT EXISTS (SELECT 1 FROM asked)
           OR EXISTS (SELECT 1 FROM condition_member r JOIN asked ON asked.term = r.record WHERE r.entry = c.entry))
    ORDER BY c.sort_key
    LIMIT coalesce(:page_size, -1)),
  strings (id, said) AS NOT MATERIALIZED (
    SELECT id, CASE kind WHEN 2 THEN lex WHEN 3 THEN substr(nt, 2, length(nt) - 2 - CASE WHEN lang IS NOT NULL
      THEN length(lang) + 1 WHEN datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
      ELSE length(datatype) + 4 END) END FROM term),
  statuses (entry, line, shown) AS (
    SELECT v.entry,
      m.lex || ' ' || CASE WHEN v.ruled_out THEN 'ruled out' ELSE coalesce(st.lex, 'with no status') END
        || CASE WHEN v.ruled_out THEN '' ELSE coalesce(', abated ' || ab.lex, '') END || char(31),
      m.lex || ' ' || CASE WHEN v.ruled_out THEN 'ruled out' ELSE coalesce(st_said.said, 'with no status') END
        || CASE WHEN v.ruled_out THEN '' ELSE coalesce(', abated ' || ab_said.said, '') END
    FROM (SELECT v.*, coalesce(v.verification = (SELECT id FROM term WHERE nt = '"refuted"'), 0) AS ruled_out
          FROM condition_member_values v) v
    JOIN page ON page.entry = v.entry JOIN term m ON m.id = v.member
    LEFT JOIN term st ON st.id = v.status LEFT JOIN strings st_said ON st_said.id = v.status
    LEFT JOIN term ab ON ab.id = v.abatement LEFT JOIN strings ab_said ON ab_said.id = v.abatement)
SELECT name.nt AS condition, code.nt AS conditionCode,
  CASE WHEN page.refuted THEN '"ruled out"' ELSE status.nt END AS status,
  verification.nt AS verificationStatus, onset.nt AS onset,
  CASE WHEN NOT page.refuted THEN abated.nt END AS abated,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"' FROM statuses s WHERE s.entry = page.entry)
    AS statuses,
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
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term verification ON verification.id = page.verification
LEFT JOIN term onset ON onset.id = page.onset
LEFT JOIN term abated ON abated.id = page.abatement
LEFT JOIN term label ON label.id = page.label
LEFT JOIN condition_code first ON first.entry = page.entry
  AND NOT EXISTS (SELECT 1 FROM condition_code y JOIN term u ON u.id = y.code JOIN term t ON t.id = first.code
                  WHERE y.entry = first.entry AND u.lex < t.lex)
LEFT JOIN term code ON code.id = first.code
ORDER BY page.sort_key, code.kind, code.lex
