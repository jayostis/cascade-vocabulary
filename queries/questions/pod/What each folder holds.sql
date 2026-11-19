-- A list question over the pod's files, a page of folders at a time, as queries/statements.sql says: a file is the
-- graph of a statement.
WITH
  k (type, view_class, storage) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#View>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/pim/space#storage>')),
  roots (root) AS (
    SELECT DISTINCT t.lex FROM k CROSS JOIN quad st ON st.p = k.storage CROSS JOIN term t ON t.id = st.o
    WHERE t.kind IN (2, 3)),
  files (file, root, rebuilt, folder) AS (
    SELECT DISTINCT f.id, roots.root, EXISTS (SELECT 1 FROM quad v WHERE v.s = f.id AND v.p = k.type AND v.o = k.view_class),
      '/' || sparql_replace(substr(f.lex, length(roots.root) + 1), '([0-9a-f]{2}/)?[^/]*$', '', '')
    FROM k CROSS JOIN roots
    CROSS JOIN term f ON f.nt >= '<' || roots.root AND f.nt < '<' || roots.root || char(1114111)
    WHERE f.kind = 2 AND EXISTS (SELECT 1 FROM quad q WHERE q.g = f.id)),
  things (file, folder, rebuilt, thing) AS (
    SELECT DISTINCT files.file, files.folder, files.rebuilt, q.s
    FROM files CROSS JOIN quad q ON q.g = files.file CROSS JOIN term t ON t.id = q.s AND t.kind = 2
    WHERE substr(t.lex, 1, length(files.root)) <> files.root
       OR substr(t.lex, 1, length(files.root) + length(files.folder) - 1) = files.root || substr(files.folder, 2)),
  typed (folder, type, thing) AS (
    SELECT things.folder, ty.o, things.thing
    FROM k CROSS JOIN things CROSS JOIN quad ty ON ty.s = things.thing AND ty.g = things.file AND ty.p = k.type
    UNION SELECT things.folder, NULL, things.thing
    FROM k CROSS JOIN things
    WHERE NOT things.rebuilt
      AND NOT EXISTS (SELECT 1 FROM quad ty WHERE ty.s = things.thing AND ty.g = things.file AND ty.p = k.type)),
  counted (folder, type, things) AS (
    SELECT folder, type, count(DISTINCT thing) FROM typed GROUP BY folder, type),
  page (folder, sort_key) AS (
    SELECT folder, '3' || hex(folder) || '.' FROM (SELECT DISTINCT folder FROM counted)
    WHERE '3' || hex(folder) || '.' > coalesce(:after, '')
    ORDER BY 2
    LIMIT coalesce(:page_size, -1))
SELECT '"' || replace(replace(page.folder, '\', '\\'), '"', '\"') || '"' AS folder,
  coalesce(type.nt, '"no type stated"') AS type,
  '"' || counted.things || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS things,
  page.sort_key AS page_key
FROM page CROSS JOIN counted ON counted.folder = page.folder
LEFT JOIN term type ON type.id = counted.type
ORDER BY page.sort_key, coalesce(type.kind, 3), coalesce(type.lex, 'no type stated')
