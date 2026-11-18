WITH
  counting (judgment) AS (
    SELECT DISTINCT c.s FROM quad c
    WHERE c.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>')
      AND c.o = (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>')),
  made_by (kind) AS (
    SELECT id FROM term WHERE nt IN ('<http://www.w3.org/ns/prov#Person>', '<http://www.w3.org/ns/prov#SoftwareAgent>')),
  judged (judgment, kind) AS (
    SELECT DISTINCT counting.judgment, made_by.kind FROM counting, made_by
    WHERE EXISTS (
      SELECT 1 FROM quad a JOIN quad t ON t.s = a.o
      WHERE a.s = counting.judgment
        AND a.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>')
        AND t.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
        AND t.o = made_by.kind)),
  said (judgment, kind, verdict, justification) AS (
    SELECT DISTINCT judged.judgment, judged.kind, v.o, j.o FROM judged
    LEFT JOIN quad v ON v.s = judged.judgment
      AND v.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>')
    LEFT JOIN quad j ON j.s = judged.judgment
      AND j.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#justification>'))
SELECT verdict.nt AS verdict, justification.nt AS justification, made_by.nt AS madeBy,
       '"' || count(DISTINCT said.judgment) || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS judgments
FROM said
JOIN term made_by ON made_by.id = said.kind
LEFT JOIN term verdict ON verdict.id = said.verdict
LEFT JOIN term justification ON justification.id = said.justification
GROUP BY said.verdict, said.justification, said.kind
ORDER BY verdict.kind, verdict.lex, justification.kind, justification.lex, made_by.kind, made_by.lex
