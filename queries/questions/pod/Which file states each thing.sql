-- A list question over the pod's files, a page of things at a time, as queries/statements.sql says: a file is the
-- graph of a statement, and a thing's key is the one the things sort by.
WITH
  k (type, view_class, storage) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#View>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/pim/space#storage>')),
  roots (root) AS (
    SELECT DISTINCT t.lex FROM k CROSS JOIN quad st ON st.p = k.storage CROSS JOIN term t ON t.id = st.o
    WHERE t.kind IN (2, 3)),
  files (file, rebuilt) AS (
    SELECT DISTINCT f.id, EXISTS (SELECT 1 FROM quad v WHERE v.s = f.id AND v.p = k.type AND v.o = k.view_class)
    FROM k CROSS JOIN roots
    CROSS JOIN term f ON f.nt >= '<' || roots.root AND f.nt < '<' || roots.root || char(1114111)
    WHERE f.kind = 2 AND EXISTS (SELECT 1 FROM quad q WHERE q.g = f.id)),
  pairs (thing, file, named) AS (
    SELECT DISTINCT q.s, files.file, 0
    FROM files CROSS JOIN quad q ON q.g = files.file CROSS JOIN term t ON t.id = q.s AND t.kind = 2
    UNION SELECT DISTINCT q.o, files.file, 1
    FROM files CROSS JOIN quad q ON q.g = files.file CROSS JOIN term t ON t.id = q.o AND t.kind = 2),
  page (thing, sort_key) AS (
    SELECT t.id, '2' || hex(t.lex) || '.'
    FROM (SELECT DISTINCT thing FROM pairs) p CROSS JOIN term t ON t.id = p.thing
    WHERE '2' || hex(t.lex) || '.' > coalesce(:after, '')
    ORDER BY 2
    LIMIT coalesce(:page_size, -1))
SELECT thing.nt AS thing, file.nt AS file,
  CASE pairs.named WHEN 1 THEN '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'
    ELSE '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>' END AS named,
  CASE files.rebuilt WHEN 1 THEN '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'
    ELSE '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>' END AS rebuilt,
  page.sort_key AS page_key
FROM page CROSS JOIN pairs ON pairs.thing = page.thing CROSS JOIN files ON files.file = pairs.file
CROSS JOIN term thing ON thing.id = page.thing CROSS JOIN term file ON file.id = pairs.file
ORDER BY page.sort_key, files.rebuilt, pairs.named, file.lex
