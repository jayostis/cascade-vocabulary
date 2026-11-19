WITH
  k (type, counts, yes, label, judgment_class, replaces, invalidated, asserted_judgment, derived_from,
     specialization_of, series_class, revision_of, current_version, joined_by_current, asserted_under, matcher_rule,
     query_hash, row_of) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/dc/terms/replaces>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#invalidated>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#assertedJudgment>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#specializationOf>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ReferenceSeries>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasRevisionOf>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#membersJoinedByCurrentTableVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#assertedUnderRuleListVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#matcherRule>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#queryHash>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#rowOfRuleListVersion>')),
  -- A row for each solution of a branch of the .rq: a column holds each variable it hides, so that two solutions
  -- that differ only there are two rows, as they are two solutions.
  said (judgment, happened, actor, hidden, hidden_too) AS (
    SELECT DISTINCT t.s, NULL, NULL, NULL, NULL
    FROM k CROSS JOIN quad t ON t.p = k.type AND t.o = k.judgment_class
    UNION ALL
    SELECT DISTINCT r.o, 'replaced', r.s, NULL, NULL FROM k CROSS JOIN quad r ON r.p = k.replaces
    UNION ALL
    SELECT DISTINCT i.o, 'retracted', i.s, NULL, NULL
    FROM k CROSS JOIN quad i ON i.p = k.invalidated
    CROSS JOIN quad t ON t.s = i.o AND t.p = k.type AND t.o = k.judgment_class
    UNION ALL
    SELECT DISTINCT a.o, 'retracted', i.s, i.o, NULL
    FROM k CROSS JOIN quad i ON i.p = k.invalidated
    CROSS JOIN quad a ON a.s = i.o AND a.p = k.asserted_judgment
    CROSS JOIN quad t ON t.s = a.o AND t.p = k.type AND t.o = k.judgment_class
    UNION ALL
    SELECT DISTINCT j.s, 'made under a reference version since replaced', b.s, j.o, d.o
    FROM k CROSS JOIN quad t ON t.p = k.type AND t.o = k.judgment_class
    CROSS JOIN quad j ON j.s = t.s AND j.p = k.derived_from
    CROSS JOIN quad d ON d.s = j.o AND d.p = k.specialization_of
    CROSS JOIN quad s ON s.s = d.o AND s.p = k.type AND s.o = k.series_class
    CROSS JOIN quad b ON b.p = k.revision_of AND b.o = j.o
    WHERE NOT EXISTS (SELECT 1 FROM quad sp CROSS JOIN quad cv ON cv.s = sp.o AND cv.p = k.current_version
                      CROSS JOIN quad jc ON jc.s = j.s AND jc.p = k.joined_by_current AND jc.o = cv.o
                      WHERE sp.s = j.o AND sp.p = k.specialization_of)
    UNION ALL
    SELECT DISTINCT a.o, 'its rule runs another query since', cv.o, NULL, NULL
    FROM k CROSS JOIN quad a ON a.p = k.asserted_judgment
    CROSS JOIN quad u ON u.s = a.s AND u.p = k.asserted_under
    CROSS JOIN quad sp ON sp.s = u.o AND sp.p = k.specialization_of
    CROSS JOIN quad cv ON cv.s = sp.o AND cv.p = k.current_version
    WHERE cv.o <> u.o
      AND NOT EXISTS (
        SELECT 1 FROM quad pin CROSS JOIN quad cr ON cr.o = cv.o AND cr.p = k.row_of
        CROSS JOIN quad cru ON cru.s = cr.s AND cru.p = k.matcher_rule
        CROSS JOIN quad crh ON crh.s = cr.s AND crh.p = k.query_hash
        CROSS JOIN quad ar ON ar.p = k.matcher_rule AND ar.o = cru.o
        CROSS JOIN quad ah ON ah.s = ar.s AND ah.p = k.query_hash AND ah.o = crh.o
        CROSS JOIN quad av ON av.s = ar.s AND av.p = k.row_of
        CROSS JOIN quad aa ON aa.p = k.asserted_under AND aa.o = av.o
        CROSS JOIN quad aj ON aj.s = aa.s AND aj.p = k.asserted_judgment AND aj.o = a.o
        CROSS JOIN quad jr ON jr.s = a.o AND jr.p = k.matcher_rule AND jr.o = cru.o
        WHERE pin.p = k.current_version AND pin.o = cv.o)),
  solved (judgment, happened, actor, hidden, hidden_too, counted, label, by_label) AS (
    SELECT DISTINCT said.judgment, said.happened, said.actor, said.hidden, said.hidden_too, c.o, l.o, bl.o
    FROM said CROSS JOIN k
    LEFT JOIN quad c ON c.s = said.judgment AND c.p = k.counts
    LEFT JOIN quad l ON l.s = said.judgment AND l.p = k.label
    LEFT JOIN quad bl ON bl.s = said.actor AND bl.p = k.label)
SELECT judgment.nt AS judgment, label.nt AS judgmentLabel,
  coalesce(counted.nt, '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>') AS counts,
  '"' || solved.happened || '"' AS happened, actor.nt AS "by", by_label.nt AS byLabel
FROM solved CROSS JOIN term judgment ON judgment.id = solved.judgment
LEFT JOIN term counted ON counted.id = solved.counted
LEFT JOIN term label ON label.id = solved.label
LEFT JOIN term actor ON actor.id = solved.actor
LEFT JOIN term by_label ON by_label.id = solved.by_label
ORDER BY label.kind, label.lex, judgment.kind, judgment.lex, solved.happened, actor.kind, actor.lex
