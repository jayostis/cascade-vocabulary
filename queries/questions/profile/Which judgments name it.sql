WITH
  k (type, judgment_class, patient, member, generated_at, verdict, counts, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#patient>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
  named (profile, profile_label, made, judgment, judgment_label, verdict, counted) AS (
    SELECT DISTINCT p.o, pl.o, ma.o, j.s, jl.o, ve.o, cu.o
    FROM k CROSS JOIN quad j ON j.p = k.type AND j.o = k.judgment_class
    CROSS JOIN quad p ON p.s = j.s AND p.p = k.member
    CROSS JOIN quad ma ON ma.s = j.s AND ma.p = k.generated_at
    CROSS JOIN quad pa ON pa.o = p.o AND pa.p = k.patient
    LEFT JOIN quad ve ON ve.s = j.s AND ve.p = k.verdict
    LEFT JOIN quad cu ON cu.s = j.s AND cu.p = k.counts
    LEFT JOIN quad pl ON pl.s = p.o AND pl.p = k.label
    LEFT JOIN quad jl ON jl.s = j.s AND jl.p = k.label)
SELECT profile.nt AS profile, profile_label.nt AS profileLabel, made.nt AS made, judgment.nt AS judgment,
  judgment_label.nt AS judgmentLabel, verdict.nt AS verdict,
  coalesce(counted.nt, '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>') AS counts
FROM named CROSS JOIN term profile ON profile.id = named.profile CROSS JOIN term made ON made.id = named.made
CROSS JOIN term judgment ON judgment.id = named.judgment
LEFT JOIN term profile_label ON profile_label.id = named.profile_label
LEFT JOIN term judgment_label ON judgment_label.id = named.judgment_label
LEFT JOIN term verdict ON verdict.id = named.verdict
LEFT JOIN term counted ON counted.id = named.counted
ORDER BY profile_label.kind, profile_label.lex, profile.kind, profile.lex, made.instant, judgment.kind, judgment.lex
