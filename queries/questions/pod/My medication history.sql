-- A list question over the medications screen, paged as queries/statements.sql says.
WITH
  page (entry, iri, sort_key, name, selected, status, lifecycle, started, written, ended, label) AS (
    SELECT m.entry, m.iri, m.sort_key, m.name, m.selected, m.status, m.lifecycle, m.started, m.written, m.ended, m.label
    FROM medication m
    WHERE m.sort_key > coalesce(:after, '')
      AND m.name IS NOT NULL
      AND EXISTS (SELECT 1 FROM medication_member r WHERE r.entry = m.entry)
      AND (NOT EXISTS (SELECT 1 FROM asked)
           OR EXISTS (SELECT 1 FROM medication_member r JOIN asked ON asked.term = r.record WHERE r.entry = m.entry))
    ORDER BY m.sort_key
    LIMIT coalesce(:page_size, -1)),
  strings (id, said) AS NOT MATERIALIZED (
    SELECT id, CASE kind WHEN 2 THEN lex WHEN 3 THEN substr(nt, 2, length(nt) - 2 - CASE WHEN lang IS NOT NULL
      THEN length(lang) + 1 WHEN datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
      ELSE length(datatype) + 4 END) END FROM term),
  statuses (entry, line, shown) AS (
    SELECT v.entry, m.lex || ' ' || coalesce(st.lex, 'with no status') || coalesce(', ended ' || en.lex, '') || char(31),
      m.lex || ' ' || coalesce(st_said.said, 'with no status') || coalesce(', ended ' || en_said.said, '')
    FROM medication_member_values v JOIN page ON page.entry = v.entry JOIN term m ON m.id = v.member
    LEFT JOIN term st ON st.id = v.status LEFT JOIN strings st_said ON st_said.id = v.status
    LEFT JOIN term en ON en.id = v.ended LEFT JOIN strings en_said ON en_said.id = v.ended),
  dosages (entry, key, line, shown) AS (
    SELECT v.entry, coalesce(wr.lex, '~'),
      m.lex || ' ' || d.lex || coalesce(', written ' || wr.lex, '') || char(31),
      m.lex || ' ' || d_said.said || coalesce(', written ' || wr_said.said, '')
    FROM medication_member_values v JOIN page ON page.entry = v.entry JOIN term m ON m.id = v.member
    JOIN term d ON d.id = v.dosage JOIN strings d_said ON d_said.id = v.dosage
    LEFT JOIN term wr ON wr.id = v.written LEFT JOIN strings wr_said ON wr_said.id = v.written),
  said (entry, line, shown) AS (
    SELECT v.entry, m.lex || ' ' || n.lex || char(31), m.lex || ' ' || n_said.said
    FROM medication_member_values v JOIN page ON page.entry = v.entry JOIN term m ON m.id = v.member
    JOIN term n ON n.id = v.narrative JOIN strings n_said ON n_said.id = v.narrative),
  reasons (entry, k1, k2, member, line, shown) AS (
    SELECT DISTINCT v.entry, coalesce(cn.lex, ''), substr(c.iri, 2, length(c.iri) - 2), m.lex,
      m.lex || ' for ' || substr(c.iri, 2, length(c.iri) - 2) || coalesce(', ' || cn.lex, '') || char(31),
      m.lex || ' for ' || substr(c.iri, 2, length(c.iri) - 2) || coalesce(', ' || CASE cn.kind WHEN 2 THEN cn.lex WHEN 3 THEN substr(cn.nt, 2, length(cn.nt) - 2 - CASE WHEN cn.lang IS NOT NULL
        THEN length(cn.lang) + 1 WHEN cn.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(cn.datatype) + 4 END) END, '')
    FROM page CROSS JOIN medication_member_values_reason_condition v ON v.entry = page.entry JOIN term m ON m.id = v.member
    JOIN condition_member cm ON cm.record = v.record JOIN condition c ON c.entry = cm.entry
    LEFT JOIN term cn ON cn.id = c.name
    UNION SELECT v.entry, code.lex, '', m.lex, m.lex || ' for ' || code.lex || char(31), m.lex || ' for ' || CASE code.kind WHEN 2 THEN code.lex WHEN 3 THEN substr(code.nt, 2, length(code.nt) - 2 - CASE WHEN code.lang IS NOT NULL
        THEN length(code.lang) + 1 WHEN code.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(code.datatype) + 4 END) END
    FROM page CROSS JOIN medication_member_values_reason_code v ON v.entry = page.entry JOIN term m ON m.id = v.member
    JOIN term code ON code.id = v.code
    UNION SELECT v.entry, code.lex, code.datatype, m.lex,
      m.lex || ' for ' || code.datatype || ' ' || code.lex || char(31),
      m.lex || ' for ' || code.datatype || ' ' || CASE code.kind WHEN 2 THEN code.lex WHEN 3 THEN substr(code.nt, 2, length(code.nt) - 2 - CASE WHEN code.lang IS NOT NULL
        THEN length(code.lang) + 1 WHEN code.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(code.datatype) + 4 END) END
    FROM page CROSS JOIN medication_member_values_reason_other_system v ON v.entry = page.entry
    JOIN term m ON m.id = v.member JOIN term code ON code.id = v.code),
  candidates (entry, n, only) AS (
    SELECT entry, count(DISTINCT nt), min(nt) FROM (
      SELECT c.entry, CASE t.kind WHEN 2 THEN t.nt ELSE '<https://ns.cascadeprotocol.org/codes/rxnorm/' || sparql_encode_for_uri(t.lex) || '>' END AS nt
      FROM page CROSS JOIN medication_code c ON c.entry = page.entry JOIN term t ON t.id = c.code WHERE t.kind IN (2, 3))
    GROUP BY entry)
SELECT name.nt AS medication,
  coalesce(CASE WHEN instr(chosen.lex, 'https://ns.cascadeprotocol.org/codes/rxnorm/') = 1 THEN chosen.nt END,
           CASE WHEN candidates.n = 1 THEN candidates.only END) AS code,
  status.nt AS status, lifecycle.nt AS lifecycle, started.nt AS started, written.nt AS written, ended.nt AS ended,
  (SELECT '"' || group_concat(s.shown, '' ORDER BY s.line) || '"' FROM statuses s WHERE s.entry = page.entry)
    AS statuses,
  (SELECT '"' || group_concat(s.shown, '' ORDER BY s.key, s.line) || '"' FROM dosages s WHERE s.entry = page.entry)
    AS dosages,
  (SELECT '"' || group_concat(s.shown, '' ORDER BY s.line) || '"' FROM said s WHERE s.entry = page.entry)
    AS narrativeTexts,
  (SELECT '"' || group_concat(s.shown, '' ORDER BY s.k1, s.k2, s.member, s.line) || '"'
   FROM reasons s WHERE s.entry = page.entry) AS reasons,
  '"' || (SELECT count(*) FROM medication_member m WHERE m.entry = page.entry
          AND (NOT EXISTS (SELECT 1 FROM asked) OR m.record IN (SELECT term FROM asked)))
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '' ORDER BY s.line) || '"'
   FROM medication_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page
JOIN term name ON name.id = page.name
LEFT JOIN term chosen ON chosen.id = page.selected
LEFT JOIN candidates ON candidates.entry = page.entry
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term lifecycle ON lifecycle.id = page.lifecycle
LEFT JOIN term started ON started.id = page.started
LEFT JOIN term written ON written.id = page.written
LEFT JOIN term ended ON ended.id = page.ended
LEFT JOIN term label ON label.id = page.label
ORDER BY page.sort_key
