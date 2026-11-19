WITH
  k (label) AS (SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'))
SELECT DISTINCT thing.nt AS thing, label.nt AS label
FROM k CROSS JOIN quad l ON l.p = k.label
CROSS JOIN term thing ON thing.id = l.s AND thing.kind = 2
CROSS JOIN term label ON label.id = l.o
ORDER BY thing.lex, label.kind, label.lex
