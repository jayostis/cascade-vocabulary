WITH
  k (type, record_class, left_out_for, reason, because, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Record>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leftOutFor>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leftOutReason>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leftOutBecauseOf>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
  asking (record) AS (
    SELECT term FROM asked
    UNION ALL SELECT q.s FROM k CROSS JOIN quad q ON q.p = k.type AND q.o = k.record_class WHERE NOT EXISTS (SELECT 1 FROM asked)),
  named (record, record_label, why, because, because_label) AS (
    SELECT DISTINCT r.s, rl.o, w.o, b.o, bl.o
    FROM asking CROSS JOIN k CROSS JOIN quad r ON r.s = asking.record AND r.p = k.type AND r.o = k.record_class
    CROSS JOIN quad lo ON lo.s = r.s AND lo.p = k.left_out_for
    CROSS JOIN quad w ON w.s = lo.o AND w.p = k.reason
    LEFT JOIN quad b ON b.s = lo.o AND b.p = k.because
    LEFT JOIN quad bl ON bl.s = b.o AND bl.p = k.label
    LEFT JOIN quad rl ON rl.s = r.s AND rl.p = k.label)
SELECT record.nt AS record, record_label.nt AS recordLabel, why.nt AS why, because.nt AS because,
  because_label.nt AS becauseLabel
FROM named CROSS JOIN term record ON record.id = named.record CROSS JOIN term why ON why.id = named.why
LEFT JOIN term record_label ON record_label.id = named.record_label
LEFT JOIN term because ON because.id = named.because
LEFT JOIN term because_label ON because_label.id = named.because_label
ORDER BY why.kind, why.lex, record_label.kind, record_label.lex, record.kind, record.lex, because.kind, because.lex
