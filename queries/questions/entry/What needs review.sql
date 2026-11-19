WITH
  k (type, current_version, allergy_criticality, counts, yes, verdict, same, different, acknowledged, justification, attributed, software_agent, member, currently_different, lapsed, has_body, has_target, not_reached, answers, record_kind, condition_code, display_date, abatement_date, clinical_status, rx_norm_code, ndc_code, derived_from, workflow_status, business_identifier_same, one_day, different_values, different_units, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#allergyCriticality>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Same>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Different>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Acknowledged>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#justification>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#SoftwareAgent>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentlyDifferent>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#lapsed>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/oa#hasBody>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/oa#hasTarget>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#MatcherJudgmentsNoLongerReached>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#answersWarningOfKind>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#recordKind>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#conditionCode>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#displayDate>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#abatementDate>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#clinicalStatus>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#rxNormCode>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ndcCode>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#workflowStatus>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#SameBusinessIdentifierAndTestCodeWithinOneOrganization>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#SameResultOnOneDay>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#DifferentResultValuesAtOneInstant>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#DifferentResultUnitsAtOneInstant>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
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
  entry_labels (entry, label) AS (SELECT DISTINCT entry, label FROM shown),
  periods (record, entry, code, dated, begins, ends, open) AS (
    SELECT DISTINCT sh.record, sh.entry, cc.o, ds.o IS NOT NULL,
      CASE WHEN ds.o IS NULL THEN NULL WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYear' THEN substr(dst.lex, 1, 4) || '-01-01'
           WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYearMonth' THEN substr(dst.lex, 1, 7) || '-01' ELSE substr(dst.lex, 1, 10) END,
      CASE WHEN ds.o IS NULL THEN NULL
           WHEN coalesce(ends.reach, '') <> '' AND ends.reach >= CASE WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYear' THEN substr(dst.lex, 1, 4) || '-01-01'
                WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYearMonth' THEN substr(dst.lex, 1, 7) || '-01' ELSE substr(dst.lex, 1, 10) END THEN ends.reach
           WHEN st.nt IN ('"active"', '"recurrence"', '"relapse"') THEN '9999-12-31'
           WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYear' THEN substr(dst.lex, 1, 4) || '-12-31'
           WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYearMonth' THEN substr(dst.lex, 1, 7) || '-31' ELSE substr(dst.lex, 1, 10) END,
      CASE WHEN ds.o IS NULL THEN NULL
           WHEN coalesce(ends.reach, '') <> '' AND ends.reach >= CASE WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYear' THEN substr(dst.lex, 1, 4) || '-01-01'
                WHEN dst.datatype = 'http://www.w3.org/2001/XMLSchema#gYearMonth' THEN substr(dst.lex, 1, 7) || '-01' ELSE substr(dst.lex, 1, 10) END THEN 0
           WHEN st.nt IN ('"active"', '"recurrence"', '"relapse"') THEN 0 ELSE 1 END
    FROM k CROSS JOIN shown sh
    CROSS JOIN quad rk ON rk.s = sh.record AND rk.p = k.record_kind AND rk.o = (SELECT id FROM term WHERE nt = '"Condition"')
    CROSS JOIN quad cv ON cv.s = sh.record AND cv.p = k.current_version
    CROSS JOIN quad cc ON cc.s = cv.o AND cc.p = k.condition_code
    LEFT JOIN quad ds ON ds.s = cv.o AND ds.p = k.display_date
    LEFT JOIN term dst ON dst.id = ds.o
    LEFT JOIN (SELECT ab.s AS version, ab.o AS term_id,
                 CASE WHEN at.kind = 3 AND at.datatype IN ('http://www.w3.org/2001/XMLSchema#date', 'http://www.w3.org/2001/XMLSchema#dateTime') THEN substr(at.lex, 1, 10)
                      WHEN at.kind = 3 AND at.datatype = 'http://www.w3.org/2001/XMLSchema#gYearMonth' THEN substr(at.lex, 1, 7) || '-31'
                      WHEN at.kind = 3 AND at.datatype = 'http://www.w3.org/2001/XMLSchema#gYear' THEN substr(at.lex, 1, 4) || '-12-31' ELSE '' END AS reach
               FROM k k2 CROSS JOIN quad ab ON ab.p = k2.abatement_date CROSS JOIN term at ON at.id = ab.o) ends ON ends.version = cv.o
    LEFT JOIN quad cs ON cs.s = cv.o AND cs.p = k.clinical_status
    LEFT JOIN term st ON st.id = cs.o),
  needing (entry, needs, finding, judgment, record, other) AS (
    -- Members that disagree on how severe an allergy is.
    SELECT sh.entry, 'members disagree on criticality', NULL, NULL, NULL, NULL
    FROM k CROSS JOIN shown sh
    CROSS JOIN quad cv ON cv.s = sh.record AND cv.p = k.current_version
    CROSS JOIN quad cr ON cr.s = cv.o AND cr.p = k.allergy_criticality
    GROUP BY sh.entry HAVING count(DISTINCT cr.o) > 1
    UNION
    -- An entry joined for more than one kind of machine sameness.
    SELECT sh.entry, 'joined through two kinds of machine sameness', NULL, NULL, NULL, NULL
    FROM k CROSS JOIN quad same ON same.p = k.verdict AND same.o = k.same
    CROSS JOIN quad c ON c.s = same.s AND c.p = k.counts AND c.o = k.yes
    CROSS JOIN quad why ON why.s = same.s AND why.p = k.justification AND why.o IS NOT k.business_identifier_same
    CROSS JOIN quad hm ON hm.s = same.s AND hm.p = k.member
    CROSS JOIN shown sh ON sh.record = hm.o
    WHERE EXISTS (SELECT 1 FROM quad a CROSS JOIN quad t ON t.s = a.o AND t.p = k.type AND t.o = k.software_agent
                  WHERE a.s = same.s AND a.p = k.attributed)
    GROUP BY sh.entry
    HAVING count(DISTINCT why.o) > 1
      AND sum(CASE WHEN why.o IN (SELECT id FROM term WHERE nt IN ('<https://ns.cascadeprotocol.org/cascade#SameMedicationCode>', '<https://ns.cascadeprotocol.org/cascade#SameProductCode>')) THEN 0 ELSE 1 END) > 0
      AND sum(CASE WHEN why.o IN (SELECT id FROM term WHERE nt IN ('<https://ns.cascadeprotocol.org/cascade#SameNoteTypeAndTextGrownWithinOneOrganization>',
                                                                   '<https://ns.cascadeprotocol.org/cascade#SameNoteTypeAndText>',
                                                                   '<https://ns.cascadeprotocol.org/cascade#SameNoteOrDocumentMasterIdentifier>')) THEN 0 ELSE 1 END) > 0
    UNION
    -- Two records judged different that an entry still joins.
    SELECT DISTINCT s1.entry, 'judged different, still joined', NULL, jj.j, cd.s, cd.o
    FROM k CROSS JOIN quad cd ON cd.p = k.currently_different
    CROSS JOIN term a ON a.id = cd.s CROSS JOIN term b ON b.id = cd.o AND a.lex < b.lex
    CROSS JOIN shown s1 ON s1.record = cd.s CROSS JOIN shown s2 ON s2.record = cd.o AND s2.entry = s1.entry
    LEFT JOIN (SELECT h1.s AS j, h1.o AS r, h2.o AS o
               FROM k k2 CROSS JOIN quad h1 ON h1.p = k2.member
               CROSS JOIN quad h2 ON h2.s = h1.s AND h2.p = k2.member
               CROSS JOIN quad c ON c.s = h1.s AND c.p = k2.counts AND c.o = k2.yes
               CROSS JOIN quad v ON v.s = h1.s AND v.p = k2.verdict AND v.o = k2.different) jj ON jj.r = cd.s AND jj.o = cd.o
    UNION
    -- A matcher's Same of two records now in two entries, which has lapsed, by the least judgment that names both.
    SELECT DISTINCT s1.entry, 'joined before, apart under newer tables or rules', NULL, first.j, first.r, first.o
    FROM (SELECT h1.o AS r, h2.o AS o, min(ja.lex) AS least, ja.id AS j
          FROM k CROSS JOIN quad l ON l.p = k.lapsed AND l.o = k.yes
          CROSS JOIN quad h1 ON h1.s = l.s AND h1.p = k.member
          CROSS JOIN quad h2 ON h2.s = l.s AND h2.p = k.member
          CROSS JOIN term ra ON ra.id = h1.o CROSS JOIN term rb ON rb.id = h2.o AND ra.lex < rb.lex
          CROSS JOIN term ja ON ja.id = l.s
          WHERE NOT EXISTS (SELECT 1 FROM quad n CROSS JOIN quad nb ON nb.s = n.s AND nb.p = k.has_body AND nb.o = k.not_reached
                            WHERE n.p = k.has_target AND n.o = l.s)
          GROUP BY h1.o, h2.o) first
    CROSS JOIN k
    CROSS JOIN shown s1 ON s1.record = first.r CROSS JOIN shown s2 ON s2.record = first.o AND s2.entry <> s1.entry
    WHERE NOT EXISTS (SELECT 1 FROM quad d WHERE d.s = first.r AND d.p = k.currently_different AND d.o = first.o)
    UNION
    -- A finding of matcher judgments a rule list version no longer reaches, with each pair it names.
    SELECT DISTINCT s1.entry, 'no longer joined under a newer rule list version', first.finding, first.j, first.r, first.o
    FROM (SELECT b.s AS finding, h1.o AS r, h2.o AS o, min(ja.lex) AS least, ja.id AS j
          FROM k CROSS JOIN quad b ON b.p = k.has_body AND b.o = k.not_reached
          CROSS JOIN quad t ON t.s = b.s AND t.p = k.has_target
          CROSS JOIN quad l ON l.s = t.o AND l.p = k.lapsed AND l.o = k.yes
          CROSS JOIN quad h1 ON h1.s = t.o AND h1.p = k.member
          CROSS JOIN quad h2 ON h2.s = t.o AND h2.p = k.member
          CROSS JOIN term ra ON ra.id = h1.o CROSS JOIN term rb ON rb.id = h2.o AND ra.lex < rb.lex
          CROSS JOIN term ja ON ja.id = t.o
          GROUP BY b.s, h1.o, h2.o) first
    CROSS JOIN k
    CROSS JOIN shown s1 ON s1.record = first.r CROSS JOIN shown s2 ON s2.record = first.o AND s2.entry <> s1.entry
    WHERE NOT EXISTS (SELECT 1 FROM quad d WHERE d.s = first.r AND d.p = k.currently_different AND d.o = first.o)
      AND NOT EXISTS (
        SELECT 1 FROM quad a1 CROSS JOIN quad a2 ON a2.s = a1.s AND a2.p = k.member AND a2.o = first.o
        WHERE a1.p = k.member AND a1.o = first.r
          AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a1.s AND x.p = k.counts AND x.o = k.yes)
          AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a1.s AND x.p = k.verdict AND x.o = k.acknowledged)
          AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a1.s AND x.p = k.answers AND x.o = k.not_reached)
          AND NOT EXISTS (SELECT 1 FROM quad third WHERE third.s = a1.s AND third.p = k.member
                          AND third.o NOT IN (first.r, first.o)))
    UNION
    -- Two conditions of one code in two entries whose dates cannot tell whether they are one condition.
    SELECT DISTINCT p1.entry, 'same code, dates cannot tell', NULL, NULL, p1.record, p2.record
    FROM k CROSS JOIN periods p1 CROSS JOIN periods p2 ON p2.code = p1.code AND p2.entry <> p1.entry
    CROSS JOIN term a ON a.id = p1.record CROSS JOIN term b ON b.id = p2.record AND a.lex < b.lex
    WHERE NOT EXISTS (SELECT 1 FROM quad d WHERE d.s = p1.record AND d.p = k.currently_different AND d.o = p2.record)
      AND (NOT p1.dated OR NOT p2.dated OR (p1.open AND p1.begins <= p2.ends) OR (p2.open AND p2.begins <= p1.ends))
    UNION
    -- Two medications in two entries that share an RxNorm code or an NDC.
    SELECT DISTINCT s1.entry, 'possibly the same medication', NULL, NULL, r1.s, r2.s
    FROM k CROSS JOIN quad r1 ON r1.p = k.record_kind AND r1.o = (SELECT id FROM term WHERE nt = '"Medication"')
    CROSS JOIN quad v1 ON v1.s = r1.s AND v1.p = k.current_version
    CROSS JOIN quad c1 ON c1.s = v1.o AND c1.p IN (k.rx_norm_code, k.ndc_code)
    CROSS JOIN quad c2 ON c2.p = c1.p AND c2.o = c1.o
    CROSS JOIN quad v2 ON v2.o = c2.s AND v2.p = k.current_version
    CROSS JOIN quad r2 ON r2.s = v2.s AND r2.p = k.record_kind AND r2.o = r1.o
    CROSS JOIN term a ON a.id = r1.s CROSS JOIN term b ON b.id = r2.s AND a.lex < b.lex
    CROSS JOIN shown s1 ON s1.record = r1.s CROSS JOIN shown s2 ON s2.record = r2.s AND s2.entry <> s1.entry
    WHERE NOT EXISTS (SELECT 1 FROM quad d WHERE d.s = r1.s AND d.p = k.currently_different AND d.o = r2.s)
      AND NOT EXISTS (SELECT 1 FROM quad l CROSS JOIN quad h1 ON h1.s = l.s AND h1.p = k.member AND h1.o = r1.s
                      CROSS JOIN quad h2 ON h2.s = l.s AND h2.p = k.member AND h2.o = r2.s
                      WHERE l.p = k.lapsed AND l.o = k.yes)
    UNION
    -- A Same joined on one day, which the build cannot tell from two draws.
    SELECT DISTINCT sh.entry, 'joined on one day, with no time to tell two draws apart', NULL, same.s, NULL, NULL
    FROM k CROSS JOIN quad same ON same.p = k.justification AND same.o = k.one_day
    CROSS JOIN quad c ON c.s = same.s AND c.p = k.counts AND c.o = k.yes
    CROSS JOIN quad v ON v.s = same.s AND v.p = k.verdict AND v.o = k.same
    CROSS JOIN quad hm ON hm.s = same.s AND hm.p = k.member
    CROSS JOIN shown sh ON sh.record = hm.o
    UNION
    -- A finding of two results of one test at one instant that differ in value or in unit.
    SELECT DISTINCT s1.entry, CASE b.o WHEN k.different_values THEN 'one test at one instant, two values'
                                       ELSE 'one test at one instant, in units that differ' END,
      b.s, NULL, t1.o, t2.o
    FROM k CROSS JOIN quad b ON b.p = k.has_body AND b.o IN (k.different_values, k.different_units)
    CROSS JOIN quad t1 ON t1.s = b.s AND t1.p = k.has_target
    CROSS JOIN quad t2 ON t2.s = b.s AND t2.p = k.has_target
    CROSS JOIN term a ON a.id = t1.o CROSS JOIN term z ON z.id = t2.o AND a.lex < z.lex
    CROSS JOIN quad d1 ON d1.s = b.s AND d1.p = k.derived_from
    CROSS JOIN quad d2 ON d2.s = b.s AND d2.p = k.derived_from
    CROSS JOIN quad cv1 ON cv1.s = t1.o AND cv1.p = k.current_version AND cv1.o = d1.o
    CROSS JOIN quad cv2 ON cv2.s = t2.o AND cv2.p = k.current_version AND cv2.o = d2.o
    CROSS JOIN shown s1 ON s1.record = t1.o
    WHERE NOT EXISTS (SELECT 1 FROM quad d WHERE d.s = t1.o AND d.p = k.currently_different AND d.o = t2.o)
      AND NOT EXISTS (
        SELECT 1 FROM quad a1 CROSS JOIN quad a2 ON a2.s = a1.s AND a2.p = k.member AND a2.o = t2.o
        WHERE a1.p = k.member AND a1.o = t1.o
          AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a1.s AND x.p = k.counts AND x.o = k.yes)
          AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a1.s AND x.p = k.verdict AND x.o = k.acknowledged)
          AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a1.s AND x.p = k.answers AND x.o = b.o)
          AND NOT EXISTS (SELECT 1 FROM quad third WHERE third.s = a1.s AND third.p = k.member
                          AND third.o NOT IN (t1.o, t2.o)))
      AND NOT EXISTS (
        SELECT 1 FROM quad a1 CROSS JOIN quad a2 ON a2.s = a1.s AND a2.p = k.member AND a2.o = t2.o
        CROSS JOIN quad c ON c.s = a1.s AND c.p = k.counts AND c.o = k.yes
        CROSS JOIN quad v ON v.s = a1.s AND v.p = k.verdict AND v.o = k.same
        WHERE a1.p = k.member AND a1.o = t1.o
          AND NOT EXISTS (SELECT 1 FROM quad at CROSS JOIN quad sw ON sw.s = at.o AND sw.p = k.type AND sw.o = k.software_agent
                          WHERE at.s = a1.s AND at.p = k.attributed))
      AND NOT EXISTS (
        SELECT 1 FROM quad a1 CROSS JOIN quad a2 ON a2.s = a1.s AND a2.p = k.member AND a2.o = t2.o
        CROSS JOIN quad c ON c.s = a1.s AND c.p = k.counts AND c.o = k.yes
        CROSS JOIN quad v ON v.s = a1.s AND v.p = k.verdict AND v.o = k.same
        CROSS JOIN quad j ON j.s = a1.s AND j.p = k.justification AND j.o = k.business_identifier_same
        CROSS JOIN quad a3 ON a3.s = a1.s AND a3.p = k.member
        CROSS JOIN quad ws ON ws.s = a3.o AND ws.p = k.current_version
        CROSS JOIN quad wf ON wf.s = ws.o AND wf.p = k.workflow_status
        CROSS JOIN term wt ON wt.id = wf.o
        WHERE a1.p = k.member AND a1.o = t1.o AND a3.o IN (t1.o, t2.o) AND wt.nt IN ('"corrected"', '"amended"'))),
  said (entry, entry_label, needs, finding, judgment, judgment_label, record, record_label, other, other_label) AS (
    SELECT DISTINCT needing.entry, el.label, needing.needs, needing.finding, needing.judgment, jl.o, needing.record, rl.o,
      needing.other, ol.o
    FROM needing CROSS JOIN k LEFT JOIN entry_labels el ON el.entry = needing.entry
    LEFT JOIN quad jl ON jl.s = needing.judgment AND jl.p = k.label
    LEFT JOIN quad rl ON rl.s = needing.record AND rl.p = k.label
    LEFT JOIN quad ol ON ol.s = needing.other AND ol.p = k.label)
SELECT said.entry AS entry, entry_label.nt AS entryLabel, '"' || said.needs || '"' AS needs, finding.nt AS finding,
  judgment.nt AS judgment, judgment_label.nt AS judgmentLabel, record.nt AS record, record_label.nt AS recordLabel,
  other.nt AS otherRecord, other_label.nt AS otherRecordLabel
FROM said LEFT JOIN term entry_label ON entry_label.id = said.entry_label
LEFT JOIN term finding ON finding.id = said.finding
LEFT JOIN term judgment ON judgment.id = said.judgment
LEFT JOIN term judgment_label ON judgment_label.id = said.judgment_label
LEFT JOIN term record ON record.id = said.record
LEFT JOIN term record_label ON record_label.id = said.record_label
LEFT JOIN term other ON other.id = said.other
LEFT JOIN term other_label ON other_label.id = said.other_label
ORDER BY said.needs, finding.kind, finding.lex, entry_label.kind, entry_label.lex, substr(said.entry, 2, length(said.entry) - 2),
  judgment.kind, judgment.lex, record.kind, record.lex, other.kind, other.lex
