WITH RECURSIVE
  k (candidate, later, current_revision, version, observed, discount, judged_before, same_record_before, revision_of,
     has_body, has_target, older_states, clock_behind, contradicted, derived_from, counts, yes, verdict, acknowledged,
     answers, member, days, generated_by, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevisionCandidate>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#laterInAncestryThan>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#observedAsOf>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#observationTimeDiscountedBy>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#judgedBefore>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#judgedBeforeRevisionOfSameRecord>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#revisionOf>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/oa#hasBody>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/oa#hasTarget>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#SourceReportedOlderStates>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ClockBehind>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#contradictedEarlierRevision>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Acknowledged>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#answersWarningOfKind>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writerClockBehindByAtLeastDays>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
  -- A Before between two revisions of one record, and every revision a chain of them reaches.
  reach (src, dst) AS (
    SELECT e.s, e.o FROM k CROSS JOIN quad e ON e.p = k.same_record_before
    UNION SELECT reach.src, e.o FROM k CROSS JOIN reach CROSS JOIN quad e ON e.s = reach.dst AND e.p = k.same_record_before),
  -- A current revision beside another candidate at another version, which no later live pull of the source follows.
  tied (record, revision, other, needs) AS (
    SELECT DISTINCT cand.s, cur.o, cand.o,
      CASE WHEN seen.instant > other_seen.instant AND d.o IS NULL AND od.o IS NULL THEN 'observed later' ELSE 'no basis' END
    FROM k CROSS JOIN quad cand ON cand.p = k.candidate
    CROSS JOIN quad cur ON cur.s = cand.s AND cur.p = k.current_revision
    CROSS JOIN quad v ON v.s = cur.o AND v.p = k.version
    CROSS JOIN quad ob ON ob.s = cur.o AND ob.p = k.observed
    CROSS JOIN term seen ON seen.id = ob.o
    CROSS JOIN quad ov ON ov.s = cand.o AND ov.p = k.version
    CROSS JOIN quad oob ON oob.s = cand.o AND oob.p = k.observed
    CROSS JOIN term other_seen ON other_seen.id = oob.o
    LEFT JOIN quad d ON d.s = cur.o AND d.p = k.discount
    LEFT JOIN quad od ON od.s = cand.o AND od.p = k.discount
    WHERE ov.o <> v.o
      AND NOT EXISTS (SELECT 1 FROM quad later WHERE later.p = k.later AND later.o = cand.o)
      AND (NOT EXISTS (SELECT 1 FROM asked) OR cand.s IN (SELECT term FROM asked))),
  cycles (record, revision, other) AS (
    SELECT DISTINCT r.o, e.s, e.o
    FROM k CROSS JOIN quad e ON e.p = k.same_record_before
    CROSS JOIN quad r ON r.s = e.s AND r.p = k.revision_of
    CROSS JOIN term a ON a.id = e.s CROSS JOIN term b ON b.id = e.o
    WHERE EXISTS (SELECT 1 FROM reach WHERE reach.src = e.o AND reach.dst = e.s)
      AND (a.lex < b.lex OR NOT EXISTS (SELECT 1 FROM quad back WHERE back.s = e.o AND back.p = k.same_record_before AND back.o = e.s))
      AND (NOT EXISTS (SELECT 1 FROM asked) OR r.o IN (SELECT term FROM asked))),
  -- A finding that a source reported older states, one row for each revision it names.
  older_targets (finding, target) AS (
    SELECT DISTINCT b.s, t.o FROM k CROSS JOIN quad b ON b.p = k.has_body AND b.o = k.older_states
    CROSS JOIN quad t ON t.s = b.s AND t.p = k.has_target),
  contradicts (finding, revision) AS (
    SELECT DISTINCT b.s, c.o FROM k CROSS JOIN quad b ON b.p = k.has_body AND b.o = k.older_states
    CROSS JOIN quad c ON c.s = b.s AND c.p = k.contradicted),
  answered_by_before (finding, target) AS (
    SELECT DISTINCT t.finding, t.target FROM k CROSS JOIN older_targets t
    CROSS JOIN contradicts c ON c.finding = t.finding
    CROSS JOIN quad jb ON jb.p = k.judged_before AND jb.s = t.target AND jb.o = c.revision
    UNION SELECT DISTINCT t.finding, t.target FROM k CROSS JOIN older_targets t
    CROSS JOIN contradicts c ON c.finding = t.finding
    CROSS JOIN quad jb ON jb.p = k.judged_before AND jb.s = c.revision AND jb.o = t.target),
  -- An acknowledgement that names the record, the target's document and every document of the contradicted states.
  acknowledgements (finding, target, acknowledgement, documents, named) AS (
    SELECT t.finding, t.target, a.s, count(DISTINCT cd.o),
      count(DISTINCT CASE WHEN EXISTS (SELECT 1 FROM quad n WHERE n.s = a.s AND n.p = k.member AND n.o = cd.o) THEN cd.o END)
    FROM k CROSS JOIN older_targets t
    CROSS JOIN quad rf ON rf.s = t.target AND rf.p = k.revision_of
    CROSS JOIN quad od ON od.s = t.target AND od.p = k.derived_from
    CROSS JOIN quad a ON a.p = k.member AND a.o = rf.o
    CROSS JOIN quad a2 ON a2.s = a.s AND a2.p = k.member AND a2.o = od.o
    CROSS JOIN contradicts c ON c.finding = t.finding
    CROSS JOIN quad cr ON cr.s = c.revision AND cr.p = k.revision_of AND cr.o = rf.o
    CROSS JOIN quad cd ON cd.s = c.revision AND cd.p = k.derived_from
    WHERE EXISTS (SELECT 1 FROM quad x WHERE x.s = a.s AND x.p = k.counts AND x.o = k.yes)
      AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a.s AND x.p = k.verdict AND x.o = k.acknowledged)
      AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a.s AND x.p = k.answers AND x.o = k.older_states)
    GROUP BY t.finding, t.target, a.s),
  open_targets (finding, target) AS (
    SELECT t.finding, t.target FROM older_targets t
    WHERE NOT EXISTS (SELECT 1 FROM answered_by_before b WHERE b.finding = t.finding AND b.target = t.target)
      AND NOT EXISTS (SELECT 1 FROM acknowledgements a WHERE a.finding = t.finding AND a.target = t.target
                      AND a.documents = a.named)),
  went_back (finding, records) AS (SELECT finding, count(*) FROM open_targets GROUP BY finding),
  last_reported (finding, last) AS (
    SELECT c.finding, (SELECT x.lex FROM contradicts c2 CROSS JOIN quad ob ON ob.s = c2.revision AND ob.p = k.observed
                         CROSS JOIN term x ON x.id = ob.o
                         WHERE c2.finding = c.finding ORDER BY x.instant DESC, x.lex LIMIT 1)
    FROM k CROSS JOIN (SELECT DISTINCT finding FROM contradicts) c),
  went_older (record, revision, other, finding, needs) AS (
    SELECT DISTINCT cr.s, cr.o, t.target, t.finding,
      'this source reports ' || went_back.records || CASE WHEN went_back.records = 1 THEN ' record' ELSE ' records' END
        || ' at states older than it reported on ' || substr(last_reported.last, 1, 10)
    FROM open_targets t CROSS JOIN k
    CROSS JOIN went_back ON went_back.finding = t.finding
    CROSS JOIN last_reported ON last_reported.finding = t.finding AND last_reported.last IS NOT NULL
    CROSS JOIN quad rf ON rf.s = t.target AND rf.p = k.revision_of
    CROSS JOIN quad cr ON cr.s = rf.o AND cr.p = k.current_revision
    WHERE NOT EXISTS (SELECT 1 FROM asked) OR rf.o IN (SELECT term FROM asked)),
  behind (record, revision, finding, needs) AS (
    SELECT DISTINCT r.o, t.o, b.s,
      'this writer''s clock was at least ' || dd.lex || CASE WHEN CAST(dd.lex AS REAL) = 1 THEN ' day' ELSE ' days' END || ' behind'
    FROM k CROSS JOIN quad b ON b.p = k.has_body AND b.o = k.clock_behind
    CROSS JOIN quad t ON t.s = b.s AND t.p = k.has_target
    CROSS JOIN quad d ON d.s = b.s AND d.p = k.days
    CROSS JOIN term dd ON dd.id = d.o
    CROSS JOIN quad r ON r.s = t.o AND r.p = k.revision_of
    CROSS JOIN quad g ON g.s = t.o AND g.p = k.generated_by
    WHERE NOT EXISTS (SELECT 1 FROM quad a
                      WHERE a.p = k.member AND a.o = g.o
                        AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a.s AND x.p = k.counts AND x.o = k.yes)
                        AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a.s AND x.p = k.verdict AND x.o = k.acknowledged)
                        AND EXISTS (SELECT 1 FROM quad x WHERE x.s = a.s AND x.p = k.answers AND x.o = k.clock_behind))
      AND NOT EXISTS (SELECT 1 FROM quad x WHERE x.s = t.o AND x.p = k.discount)
      AND (NOT EXISTS (SELECT 1 FROM asked) OR r.o IN (SELECT term FROM asked))),
  needing (record, needs, finding, revision, other) AS (
    SELECT record, needs, NULL, revision, other FROM tied
    UNION SELECT record, 'Befores that form a cycle', NULL, revision, other FROM cycles
    UNION SELECT record, needs, finding, revision, other FROM went_older
    UNION SELECT record, needs, finding, revision, NULL FROM behind),
  said (record, record_label, needs, finding, revision, revision_label, other, other_label) AS (
    SELECT DISTINCT needing.record, rl.o, needing.needs, needing.finding, needing.revision, vl.o, needing.other, ol.o
    FROM needing CROSS JOIN k
    LEFT JOIN quad rl ON rl.s = needing.record AND rl.p = k.label
    LEFT JOIN quad vl ON vl.s = needing.revision AND vl.p = k.label
    LEFT JOIN quad ol ON ol.s = needing.other AND ol.p = k.label)
SELECT record.nt AS record, record_label.nt AS recordLabel, '"' || said.needs || '"' AS needs, finding.nt AS finding,
  revision.nt AS revision, revision_label.nt AS revisionLabel, other.nt AS otherRevision,
  other_label.nt AS otherRevisionLabel
FROM said CROSS JOIN term record ON record.id = said.record CROSS JOIN term revision ON revision.id = said.revision
LEFT JOIN term record_label ON record_label.id = said.record_label
LEFT JOIN term finding ON finding.id = said.finding
LEFT JOIN term revision_label ON revision_label.id = said.revision_label
LEFT JOIN term other ON other.id = said.other
LEFT JOIN term other_label ON other_label.id = said.other_label
ORDER BY said.needs, finding.kind, finding.lex, record_label.kind, record_label.lex, record.kind, record.lex,
  revision.kind, revision.lex, other.kind, other.lex
