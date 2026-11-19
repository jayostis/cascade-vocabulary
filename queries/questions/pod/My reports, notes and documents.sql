-- A list question over the reports and the notes and documents screens, paged as queries/statements.sql says: the two
-- screens' entries are one list, in the order their sort keys give, a page taking the first entries of each screen
-- and then the first of those.
WITH
  k (record_kind, current_version, attachment, content_type, title) AS (
    SELECT (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#recordKind>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#attachment>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#attachmentContentType>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#attachmentTitle>')),
  page (src, entry, iri, sort_key, lead, name, title, date, issued, content_status, conclusion, narrative, status,
        label) AS (
    SELECT * FROM (
      SELECT 0, r.entry, r.iri, r.sort_key, r.lead, r.name, NULL, r.date, r.issued, NULL, r.conclusion, r.narrative,
             r.status, r.label
      FROM report r CROSS JOIN k
      WHERE r.sort_key > coalesce(:after, '')
        AND EXISTS (SELECT 1 FROM quad kd WHERE kd.s = r.lead AND kd.p = k.record_kind)
      ORDER BY r.sort_key
      LIMIT coalesce(:page_size, -1))
    UNION ALL
    SELECT * FROM (
      SELECT 1, n.entry, n.iri, n.sort_key, n.lead, n.type_name, n.title, n.date, NULL, n.content_status, NULL,
             n.narrative, n.status, n.label
      FROM note n CROSS JOIN k
      WHERE n.sort_key > coalesce(:after, '')
        AND EXISTS (SELECT 1 FROM quad kd WHERE kd.s = n.lead AND kd.p = k.record_kind)
      ORDER BY n.sort_key
      LIMIT coalesce(:page_size, -1))
    ORDER BY 4
    LIMIT coalesce(:page_size, -1))
SELECT date.nt AS date, issued.nt AS issued, kind.nt AS kind,
  (SELECT '"' || group_concat(part, '\u001F' ORDER BY grp, ord, ord2) || '"' FROM (
     SELECT 0 AS grp, t.lex AS ord, '' AS ord2, t.lex AS part
     FROM report_code c JOIN term t ON t.id = c.code WHERE page.src = 0 AND c.entry = page.entry
     UNION SELECT 1, t.lex, t.datatype, substr(t.nt, 2, length(t.nt) - 2 - CASE WHEN t.lang IS NOT NULL
         THEN length(t.lang) + 1 WHEN t.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
         ELSE length(t.datatype) + 4 END) || ' in ' || t.datatype
     FROM report_other_code c JOIN term t ON t.id = c.code WHERE page.src = 0 AND c.entry = page.entry
     UNION SELECT 2, t.lex, '', t.lex
     FROM note_type_code c JOIN term t ON t.id = c.code WHERE page.src = 1 AND c.entry = page.entry
     UNION SELECT 3, t.lex, t.datatype, substr(t.nt, 2, length(t.nt) - 2 - CASE WHEN t.lang IS NOT NULL
         THEN length(t.lang) + 1 WHEN t.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
         ELSE length(t.datatype) + 4 END) || ' in ' || t.datatype
     FROM note_type_other_code c JOIN term t ON t.id = c.code WHERE page.src = 1 AND c.entry = page.entry)) AS codes,
  name.nt AS name, title.nt AS title, status.nt AS status, content_status.nt AS contentStatus,
  conclusion.nt AS conclusion, narrative.nt AS text,
  (SELECT '"' || group_concat(shown, '\u001F' ORDER BY line) || '"' FROM (
     SELECT DISTINCT ct.lex || coalesce(' ' || ti.lex, '') AS line,
       substr(ct.nt, 2, length(ct.nt) - 2 - CASE WHEN ct.lang IS NOT NULL THEN length(ct.lang) + 1
         WHEN ct.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0 ELSE length(ct.datatype) + 4 END)
       || coalesce(' ' || substr(ti.nt, 2, length(ti.nt) - 2 - CASE WHEN ti.lang IS NOT NULL THEN length(ti.lang) + 1
         WHEN ti.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0 ELSE length(ti.datatype) + 4 END), '') AS shown
     FROM (SELECT record FROM report_member WHERE page.src = 0 AND entry = page.entry
           UNION ALL SELECT record FROM note_member WHERE page.src = 1 AND entry = page.entry) m
     JOIN quad cv ON cv.s = m.record AND cv.p = k.current_version
     JOIN quad att ON att.s = cv.o AND att.p = k.attachment
     JOIN quad cq ON cq.s = att.o AND cq.p = k.content_type
     JOIN term ct ON ct.id = cq.o
     LEFT JOIN quad tq ON tq.s = att.o AND tq.p = k.title
     LEFT JOIN term ti ON ti.id = tq.o)) AS attachments,
  (SELECT '"' || group_concat(shown, '\u001F' ORDER BY shown) || '"' FROM (
     SELECT DISTINCT
       CASE WHEN lab.entry IS NOT NULL THEN substr(lab.iri, 2, length(lab.iri) - 2)
            WHEN substr(re.lex, 1, 18) = 'urn:cascade:entry:' THEN rt.address || '#' || substr(re.lex, 19)
            ELSE re.lex END
       || coalesce(' ' || substr(test.nt, 2, length(test.nt) - 2 - CASE WHEN test.lang IS NOT NULL
            THEN length(test.lang) + 1 WHEN test.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
            ELSE length(test.datatype) + 4 END), '')
       || coalesce(' ' || CASE WHEN vt.id IS NOT NULL THEN substr(vt.nt, 2, length(vt.nt) - 2 - CASE
            WHEN vt.lang IS NOT NULL THEN length(vt.lang) + 1
            WHEN vt.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0 ELSE length(vt.datatype) + 4 END)
          ELSE substr(lab.value, 2, length(lab.value) - 2) END, '')
       || coalesce(' ' || substr(unit.nt, 2, length(unit.nt) - 2 - CASE WHEN unit.lang IS NOT NULL
            THEN length(unit.lang) + 1 WHEN unit.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
            ELSE length(unit.datatype) + 4 END), '')
       || coalesce(', reference range ' || substr(range_text.nt, 2, length(range_text.nt) - 2 - CASE
            WHEN range_text.lang IS NOT NULL THEN length(range_text.lang) + 1
            WHEN range_text.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
            ELSE length(range_text.datatype) + 4 END), '')
       || coalesce(', flagged ' || (
            SELECT group_concat(flag, ', ' ORDER BY flag) FROM (
              SELECT DISTINCT sparql_replace(t.lex, '^.*/', '') AS flag
              FROM lab_result_interpretation i JOIN term t ON t.id = i.code WHERE i.entry = rr.result_entry)), '')
       AS shown
     FROM report_result rr CROSS JOIN report_terms rt JOIN term re ON re.id = rr.result_entry
     LEFT JOIN lab_result lab ON lab.entry = rr.result_entry
     LEFT JOIN term test ON test.id = lab.test
     LEFT JOIN term vt ON vt.nt = lab.value
     LEFT JOIN term unit ON unit.id = lab.unit
     LEFT JOIN term range_text ON range_text.id = lab.range_text
     WHERE page.src = 0 AND rr.entry = page.entry)) AS results,
  page.iri AS entry, label.nt AS entryLabel,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"' FROM (
     SELECT line, shown FROM report_source WHERE page.src = 0 AND entry = page.entry
     UNION ALL SELECT line, shown FROM note_source WHERE page.src = 1 AND entry = page.entry) s) AS sources,
  page.sort_key AS page_key
FROM page CROSS JOIN k
CROSS JOIN quad kd ON kd.s = page.lead AND kd.p = k.record_kind CROSS JOIN term kind ON kind.id = kd.o
LEFT JOIN term date ON date.id = page.date
LEFT JOIN term issued ON issued.id = page.issued
LEFT JOIN term name ON name.id = page.name
LEFT JOIN term title ON title.id = page.title
LEFT JOIN term status ON status.id = page.status
LEFT JOIN term content_status ON content_status.id = page.content_status
LEFT JOIN term conclusion ON conclusion.id = page.conclusion
LEFT JOIN term narrative ON narrative.id = page.narrative
LEFT JOIN term label ON label.id = page.label
ORDER BY page.sort_key
