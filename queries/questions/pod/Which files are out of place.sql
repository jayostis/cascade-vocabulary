-- A list question over the pod's files, a page of files at a time, as queries/statements.sql says: a file is the
-- graph of a statement.
WITH
  k (type, placement, filed_with, subfolder, for_class, for_subjects_of, instance, container, view_class, subclass_of) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Placement>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#filedWith>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#subfolderPrefixLength>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#forClass>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#forSubjectsOf>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instanceContainer>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#View>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#subClassOf>')),
  placements (entry) AS (SELECT DISTINCT p.s FROM k CROSS JOIN quad p ON p.p = k.type AND p.o = k.placement),
  filings (entry, with_p, fan_out) AS (
    SELECT DISTINCT placements.entry, f.o, fo.o
    FROM placements CROSS JOIN k CROSS JOIN quad f ON f.s = placements.entry AND f.p = k.filed_with
    LEFT JOIN quad fo ON fo.s = placements.entry AND fo.p = k.subfolder),
  views_at (folder) AS (
    SELECT DISTINCT t.lex FROM placements CROSS JOIN k
    CROSS JOIN quad fc ON fc.s = placements.entry AND fc.p = k.for_class AND fc.o = k.view_class
    CROSS JOIN quad c ON c.s = placements.entry AND c.p = k.container
    CROSS JOIN term t ON t.id = c.o),
  containers (class, place) AS (
    SELECT DISTINCT fc.o, c.o
    FROM placements CROSS JOIN k CROSS JOIN quad fc ON fc.s = placements.entry AND fc.p = k.for_class
    CROSS JOIN quad c ON c.s = placements.entry AND c.p = k.container
    WHERE NOT EXISTS (SELECT 1 FROM quad n WHERE n.s = placements.entry AND n.p = k.for_subjects_of)),
  placed (entry, class, place, is_file, fan_out, narrowed) AS (
    SELECT DISTINCT placements.entry, fc.o, coalesce(i.o, c.o), i.o IS NOT NULL, fo.o,
      EXISTS (SELECT 1 FROM quad n WHERE n.s = placements.entry AND n.p = k.for_subjects_of)
    FROM placements CROSS JOIN k CROSS JOIN quad fc ON fc.s = placements.entry AND fc.p = k.for_class
    LEFT JOIN quad i ON i.s = placements.entry AND i.p = k.instance
    LEFT JOIN quad c ON c.s = placements.entry AND c.p = k.container
    LEFT JOIN quad fo ON fo.s = placements.entry AND fo.p = k.subfolder
    WHERE coalesce(i.o, c.o) IS NOT NULL),
  candidates (file, thing, place, is_file, fan_out) AS (
    -- A thing that states a filing property, filed with the container of the class of the value.
    SELECT DISTINCT q.g, q.s, v.place, 0, filings.fan_out
    FROM filings CROSS JOIN quad q ON q.p = filings.with_p
    CROSS JOIN term th ON th.id = q.s AND th.kind = 2
    CROSS JOIN k CROSS JOIN quad vt ON vt.s = q.o AND vt.p = k.type
    CROSS JOIN containers v ON v.class = vt.o
    CROSS JOIN term pt ON pt.id = v.place
    WHERE EXISTS (SELECT 1 FROM views_at WHERE substr(pt.lex, 1, length(views_at.folder)) <> views_at.folder)
      AND NOT EXISTS (SELECT 1 FROM quad w WHERE w.s = q.g AND w.p = k.type AND w.o = k.view_class)
    UNION
    -- A thing of a class the layout narrows to the things that state a property, and that states it in the file.
    SELECT DISTINCT q.g, q.s, e.place, e.is_file, e.fan_out
    FROM k CROSS JOIN quad q ON q.p = k.type
    CROSS JOIN term th ON th.id = q.s AND th.kind = 2
    CROSS JOIN placed e ON e.class = q.o AND e.narrowed
    CROSS JOIN quad n ON n.s = e.entry AND n.p = k.for_subjects_of
    CROSS JOIN quad stated ON stated.g = q.g AND stated.s = q.s AND stated.p = n.o
    WHERE NOT EXISTS (SELECT 1 FROM quad w WHERE w.s = q.g AND w.p = k.type AND w.o = k.view_class)
      AND NOT EXISTS (SELECT 1 FROM filings f2 CROSS JOIN quad s2 ON s2.s = q.s AND s2.p = f2.with_p)
    UNION
    -- A thing of a class the layout files, unless what it states or a subclass of it the layout places files it.
    SELECT DISTINCT q.g, q.s, e.place, e.is_file, e.fan_out
    FROM k CROSS JOIN quad q ON q.p = k.type
    CROSS JOIN term th ON th.id = q.s AND th.kind = 2
    CROSS JOIN placed e ON e.class = q.o AND NOT e.narrowed
    CROSS JOIN term pt ON pt.id = e.place
    WHERE EXISTS (SELECT 1 FROM views_at
                  WHERE (substr(pt.lex, 1, length(views_at.folder)) = views_at.folder)
                    = EXISTS (SELECT 1 FROM quad w WHERE w.s = q.g AND w.p = k.type AND w.o = k.view_class))
      AND NOT EXISTS (SELECT 1 FROM filings f2 CROSS JOIN quad s2 ON s2.s = q.s AND s2.p = f2.with_p)
      AND NOT EXISTS (SELECT 1 FROM placements pn
                      CROSS JOIN quad nc ON nc.s = pn.entry AND nc.p = k.for_class AND nc.o = q.o
                      CROSS JOIN quad n ON n.s = pn.entry AND n.p = k.for_subjects_of
                      CROSS JOIN quad stated ON stated.s = q.s AND stated.p = n.o)
      AND NOT EXISTS (SELECT 1 FROM quad sub
                      CROSS JOIN quad sc ON sc.s = sub.o AND sc.p = k.subclass_of AND sc.o = q.o
                      CROSS JOIN placements pe
                      CROSS JOIN quad ec ON ec.s = pe.entry AND ec.p = k.for_class AND ec.o = sub.o
                      WHERE sub.s = q.s AND sub.p = k.type)),
  measured (file, thing, place, is_file, fan_out, file_lex, place_lex, rest) AS (
    SELECT c.file, c.thing, c.place, c.is_file,
      CASE WHEN fo.datatype = 'http://www.w3.org/2001/XMLSchema#integer' THEN CAST(fo.lex AS INTEGER) END,
      f.lex, pl.lex,
      CASE WHEN instr(f.lex, pl.lex) = 0 THEN '' ELSE substr(f.lex, instr(f.lex, pl.lex) + length(pl.lex)) END
    FROM candidates c CROSS JOIN term f ON f.id = c.file CROSS JOIN term pl ON pl.id = c.place
    LEFT JOIN term fo ON fo.id = c.fan_out),
  out_of_place (file, thing, place) AS (
    SELECT file, thing, place FROM (
      SELECT *, CASE WHEN instr(rest, '/') = 0 THEN '' ELSE substr(rest, 1, instr(rest, '/') - 1) END AS fan,
        CASE WHEN instr(rest, '/') = 0 THEN '' ELSE substr(rest, instr(rest, '/') + 1) END AS after FROM measured)
    WHERE CASE WHEN is_file THEN file_lex <> place_lex
      ELSE substr(file_lex, 1, length(place_lex)) <> place_lex
        OR CASE WHEN fan_out IS NOT NULL
             THEN length(fan) <> fan_out OR substr(after, 1, length(fan)) <> fan OR instr(after, '/') > 0
             ELSE instr(rest, '/') > 0 END END),
  page (file, sort_key) AS (
    SELECT f.id, f.kind || hex(coalesce(f.lex, '')) || '.'
    FROM (SELECT DISTINCT file FROM out_of_place) o CROSS JOIN term f ON f.id = o.file
    WHERE f.kind || hex(coalesce(f.lex, '')) || '.' > coalesce(:after, '')
    ORDER BY 2
    LIMIT coalesce(:page_size, -1))
SELECT file.nt AS file, thing.nt AS thing, place.nt AS place, page.sort_key AS page_key
FROM page CROSS JOIN out_of_place o ON o.file = page.file
CROSS JOIN term file ON file.id = o.file CROSS JOIN term thing ON thing.id = o.thing
CROSS JOIN term place ON place.id = o.place
ORDER BY page.sort_key, thing.kind, thing.lex, place.kind, place.lex
