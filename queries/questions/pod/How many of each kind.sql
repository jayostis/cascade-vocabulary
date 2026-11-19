WITH
  k (type, storage) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/pim/space#storage>')),
  counted (type, things) AS (
    SELECT t.o, count(DISTINCT t.s)
    FROM k CROSS JOIN quad s ON s.p = k.storage
    CROSS JOIN term root ON root.id = s.o AND root.kind <> 1
    CROSS JOIN quad t ON t.p = k.type
    CROSS JOIN term file ON file.id = t.g
    WHERE substr(file.lex, 1, length(root.lex)) = root.lex
    GROUP BY t.o)
SELECT type.nt AS type, '"' || counted.things || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS things
FROM counted CROSS JOIN term type ON type.id = counted.type
ORDER BY type.kind, type.lex
