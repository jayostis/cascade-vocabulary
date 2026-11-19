WITH
  k (type, storage) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/pim/space#storage>'))
SELECT type.nt AS type, '"' || count(DISTINCT t.s) || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS things
FROM k CROSS JOIN quad t ON t.p = k.type
CROSS JOIN term file ON file.id = t.g
CROSS JOIN term type ON type.id = t.o
WHERE EXISTS (SELECT 1 FROM quad s CROSS JOIN term root ON root.id = s.o AND root.kind <> 1
              WHERE s.p = k.storage AND substr(file.lex, 1, length(root.lex)) = root.lex)
GROUP BY t.o
ORDER BY type.kind, type.lex
