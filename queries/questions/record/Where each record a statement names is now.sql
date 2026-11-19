WITH
  k (type, record_class, judgment_class, member, matcher_rule, counts, yes, label, left_out_for, left_out_reason) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Record>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#matcherRule>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leftOutFor>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leftOutReason>')),
  shown (entry, label, record) AS (
    SELECT entry, label, record FROM allergy_shown
    UNION ALL SELECT entry, label, record FROM condition_shown
    UNION ALL SELECT entry, label, record FROM immunization_shown
    UNION ALL SELECT entry, label, record FROM lab_result_shown
    UNION ALL SELECT entry, label, record FROM medication_dispense_shown
    UNION ALL SELECT entry, label, record FROM medication_shown
    UNION ALL SELECT entry, label, record FROM note_shown
    UNION ALL SELECT entry, label, record FROM patient_profile_shown
    UNION ALL SELECT entry, label, record FROM procedure_shown
    UNION ALL SELECT entry, label, record FROM report_shown
    UNION ALL SELECT entry, label, record FROM variant_interpretation_shown
    UNION ALL SELECT entry, label, record FROM variant_shown),
  base (statement, statement_label, counted, record, record_label, entry, entry_label) AS (
    SELECT DISTINCT j.s, jl.o, cu.o, hm.o, rl.o, sh.entry, sh.label
    FROM k CROSS JOIN quad j ON j.p = k.type AND j.o = k.judgment_class
    CROSS JOIN quad hm ON hm.s = j.s AND hm.p = k.member
    LEFT JOIN quad cu ON cu.s = j.s AND cu.p = k.counts
    LEFT JOIN quad jl ON jl.s = j.s AND jl.p = k.label
    LEFT JOIN quad rl ON rl.s = hm.o AND rl.p = k.label
    LEFT JOIN shown sh ON sh.record = hm.o
    WHERE NOT EXISTS (SELECT 1 FROM quad r WHERE r.s = j.s AND r.p = k.matcher_rule)
      AND (NOT EXISTS (SELECT 1 FROM asked) OR hm.o IN (SELECT term FROM asked))),
  pairs (statement, record) AS (SELECT DISTINCT statement, record FROM base),
  reached (statement, entries) AS (
    SELECT b.statement, count(DISTINCT sh.entry)
    FROM (SELECT DISTINCT statement FROM base) b CROSS JOIN k
    LEFT JOIN quad sib ON sib.s = b.statement AND sib.p = k.member
    LEFT JOIN shown sh ON sh.record = sib.o
    GROUP BY b.statement),
  of_entry (statement, record, other, grew) AS (
    SELECT DISTINCT pairs.statement, pairs.record, s2.record,
      CASE WHEN EXISTS (SELECT 1 FROM quad n WHERE n.s = pairs.statement AND n.p = k.member AND n.o = s2.record) THEN 0 ELSE 1 END
    FROM pairs CROSS JOIN k CROSS JOIN shown s1 ON s1.record = pairs.record
    CROSS JOIN shown s2 ON s2.entry = s1.entry AND s2.record <> s1.record),
  others (statement, record, list, grew) AS (
    SELECT pairs.statement, pairs.record,
      (SELECT group_concat(ot.lex, '\u001F' ORDER BY ot.kind, ot.lex)
       FROM of_entry f CROSS JOIN term ot ON ot.id = f.other WHERE f.statement = pairs.statement AND f.record = pairs.record),
      (SELECT coalesce(sum(f.grew), 0) FROM of_entry f WHERE f.statement = pairs.statement AND f.record = pairs.record)
    FROM pairs),
  of_statements (statement, record, other, unnamed) AS (
    SELECT DISTINCT pairs.statement, pairs.record, om.s,
      CASE WHEN EXISTS (SELECT 1 FROM quad n WHERE n.s = pairs.statement AND n.p = k.member AND n.o = s2.record) THEN 0 ELSE 1 END
    FROM pairs CROSS JOIN k CROSS JOIN shown s1 ON s1.record = pairs.record
    CROSS JOIN shown s2 ON s2.entry = s1.entry
    CROSS JOIN quad om ON om.o = s2.record AND om.p = k.member
    CROSS JOIN quad oc ON oc.s = om.s AND oc.p = k.counts AND oc.o = k.yes
    WHERE om.s <> pairs.statement
      AND NOT EXISTS (SELECT 1 FROM quad r WHERE r.s = om.s AND r.p = k.matcher_rule)),
  per_statement (statement, record, other, merges) AS (
    SELECT statement, record, other, max(unnamed) FROM of_statements GROUP BY statement, record, other),
  merged (statement, record, list, merges) AS (
    SELECT pairs.statement, pairs.record,
      (SELECT group_concat(ot.lex, '\u001F' ORDER BY ot.kind, ot.lex)
       FROM per_statement f CROSS JOIN term ot ON ot.id = f.other WHERE f.statement = pairs.statement AND f.record = pairs.record),
      (SELECT coalesce(sum(f.merges), 0) FROM per_statement f WHERE f.statement = pairs.statement AND f.record = pairs.record)
    FROM pairs),
  left_out (record, reason) AS (
    SELECT DISTINCT r.record, lr.o
    FROM (SELECT DISTINCT record FROM base) r CROSS JOIN k
    CROSS JOIN quad lo ON lo.s = r.record AND lo.p = k.left_out_for
    CROSS JOIN quad lr ON lr.s = lo.o AND lr.p = k.left_out_reason),
  reasons (record, n, list) AS (
    SELECT r.record, (SELECT count(*) FROM left_out f WHERE f.record = r.record),
      (SELECT group_concat(CASE rt.kind WHEN 2 THEN rt.lex ELSE substr(rt.nt, 2, length(rt.nt) - 2 - CASE WHEN rt.lang IS NOT NULL
         THEN length(rt.lang) + 1 WHEN rt.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
         ELSE length(rt.datatype) + 4 END) END, '\u001F' ORDER BY rt.kind, rt.lex)
       FROM left_out f CROSS JOIN term rt ON rt.id = f.reason WHERE f.record = r.record)
    FROM (SELECT DISTINCT record FROM base) r)
SELECT statement.nt AS statement, statement_label.nt AS statementLabel,
  coalesce(counted.nt, '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>') AS counts,
  record.nt AS record, record_label.nt AS recordLabel,
  '"' || CASE WHEN base.entry IS NOT NULL THEN CASE WHEN reached.entries > 1 THEN 'split' ELSE 'one' END
              WHEN reasons.n > 0 THEN 'hidden'
              WHEN EXISTS (SELECT 1 FROM k CROSS JOIN quad h WHERE h.s = base.record
                             AND h.p NOT IN (SELECT id FROM term WHERE nt IN (
                               '<https://ns.cascadeprotocol.org/cascade#currentlySame>',
                               '<https://ns.cascadeprotocol.org/cascade#currentlyDifferent>',
                               '<https://ns.cascadeprotocol.org/cascade#currentlySameOrganization>',
                               '<https://ns.cascadeprotocol.org/cascade#inEntry>',
                               '<https://ns.cascadeprotocol.org/cascade#leftOutFor>',
                               '<https://ns.cascadeprotocol.org/cascade#subject>',
                               '<https://ns.cascadeprotocol.org/cascade#recordKind>',
                               '<https://ns.cascadeprotocol.org/cascade#statusOnlyFromDocuments>',
                               '<https://ns.cascadeprotocol.org/cascade#currentRevision>',
                               '<https://ns.cascadeprotocol.org/cascade#currentRevisionCandidate>',
                               '<https://ns.cascadeprotocol.org/cascade#laterInAncestryThan>',
                               '<https://ns.cascadeprotocol.org/cascade#judgedBefore>',
                               '<https://ns.cascadeprotocol.org/cascade#judgedBeforeRevisionOfSameRecord>',
                               '<https://ns.cascadeprotocol.org/cascade#revisionJudgedErroneousBy>',
                               '<https://ns.cascadeprotocol.org/cascade#observationTimeDiscountedBy>',
                               '<https://ns.cascadeprotocol.org/cascade#lapsed>',
                               '<https://ns.cascadeprotocol.org/cascade#currentVersionStatusLifecycle>',
                               '<https://ns.cascadeprotocol.org/cascade#currentVersionStatusLifecycleStep>',
                               '<https://ns.cascadeprotocol.org/cascade#medicationExposureStart>',
                               '<https://ns.cascadeprotocol.org/cascade#medicationExposureEnd>',
                               '<https://ns.cascadeprotocol.org/cascade#medicationExposureOngoing>',
                               '<http://purl.org/pav/hasCurrentVersion>'))
                             AND NOT (h.p IS k.type AND h.o IS k.record_class))
                THEN 'in no entry' ELSE 'not in the pod' END || '"' AS outcome,
  base.entry AS entry, entry_label.nt AS entryLabel,
  CASE WHEN length(reasons.list) > 0 THEN '"' || reasons.list || '"' END AS why,
  CASE WHEN length(others.list) > 0 THEN '"' || others.list || '"' END AS otherMembers,
  CASE WHEN base.entry IS NOT NULL THEN '"' || others.grew || '"^^<http://www.w3.org/2001/XMLSchema#integer>' END AS grewBy,
  CASE WHEN length(merged.list) > 0 THEN '"' || merged.list || '"' END AS otherStatements,
  CASE WHEN base.entry IS NOT NULL THEN '"' || merged.merges || '"^^<http://www.w3.org/2001/XMLSchema#integer>' END AS mergedWith
FROM base CROSS JOIN term statement ON statement.id = base.statement CROSS JOIN term record ON record.id = base.record
CROSS JOIN reached ON reached.statement = base.statement
CROSS JOIN others ON others.statement = base.statement AND others.record = base.record
CROSS JOIN merged ON merged.statement = base.statement AND merged.record = base.record
CROSS JOIN reasons ON reasons.record = base.record
LEFT JOIN term statement_label ON statement_label.id = base.statement_label
LEFT JOIN term counted ON counted.id = base.counted
LEFT JOIN term record_label ON record_label.id = base.record_label
LEFT JOIN term entry_label ON entry_label.id = base.entry_label
ORDER BY statement.kind, statement.lex, record_label.kind, record_label.lex, record.kind, record.lex
