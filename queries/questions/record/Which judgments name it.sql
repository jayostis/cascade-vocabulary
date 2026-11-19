WITH
  k (type, record_class, judgment_class, member, generated_at, verdict, counts, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Record>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
  asking (record) AS (
    SELECT term FROM asked
    UNION ALL SELECT q.s FROM k CROSS JOIN quad q ON q.p = k.type AND q.o = k.record_class WHERE NOT EXISTS (SELECT 1 FROM asked)),
  named (record, record_label, made, judgment, judgment_label, verdict, counted) AS (
    SELECT DISTINCT r.s, rl.o, ma.o, j.s, jl.o, ve.o, cu.o
    FROM asking CROSS JOIN k CROSS JOIN quad r ON r.s = asking.record AND r.p = k.type AND r.o = k.record_class
    CROSS JOIN quad hm ON hm.o = r.s AND hm.p = k.member
    CROSS JOIN quad j ON j.s = hm.s AND j.p = k.type AND j.o = k.judgment_class
    LEFT JOIN quad ma ON ma.s = j.s AND ma.p = k.generated_at
    LEFT JOIN quad ve ON ve.s = j.s AND ve.p = k.verdict
    LEFT JOIN quad cu ON cu.s = j.s AND cu.p = k.counts
    LEFT JOIN quad rl ON rl.s = r.s AND rl.p = k.label
    LEFT JOIN quad jl ON jl.s = j.s AND jl.p = k.label)
SELECT record.nt AS record, record_label.nt AS recordLabel, made.nt AS made, judgment.nt AS judgment,
  judgment_label.nt AS judgmentLabel, verdict.nt AS verdict,
  coalesce(counted.nt, '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>') AS counts
FROM named CROSS JOIN term record ON record.id = named.record CROSS JOIN term judgment ON judgment.id = named.judgment
LEFT JOIN term record_label ON record_label.id = named.record_label
LEFT JOIN term made ON made.id = named.made
LEFT JOIN term judgment_label ON judgment_label.id = named.judgment_label
LEFT JOIN term verdict ON verdict.id = named.verdict
LEFT JOIN term counted ON counted.id = named.counted
ORDER BY record_label.kind, record_label.lex, record.kind, record.lex, made.kind, made.instant, judgment.kind, judgment.lex
