WITH
  k (type, counts, yes, verdict, same, person, attributed, member, current_revision, derived_from, current_version,
     label, judgment_class, invalidated, associated, replaces) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#countsUnderLens>'),
      (SELECT id FROM term WHERE nt = '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Same>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#Person>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#invalidated>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAssociatedWith>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/dc/terms/replaces>')),
  needing (judgment, needs) AS (
    SELECT c.s, 'a member changed since it was judged'
    FROM k CROSS JOIN quad c ON c.p = k.counts AND c.o = k.yes
    CROSS JOIN quad v ON v.s = c.s AND v.p = k.verdict AND v.o = k.same
    CROSS JOIN quad h ON h.s = c.s AND h.p = k.member
    CROSS JOIN quad r ON r.s = h.o AND r.p = k.current_revision
    CROSS JOIN quad d ON d.s = r.o AND d.p = k.derived_from
    WHERE EXISTS (SELECT 1 FROM quad a CROSS JOIN quad t ON t.s = a.o AND t.p = k.type AND t.o = k.person
                  WHERE a.s = c.s AND a.p = k.attributed)
      AND NOT EXISTS (SELECT 1 FROM quad w WHERE w.s = c.s AND w.p = k.derived_from AND w.o = d.o)
    UNION
    SELECT c.s, 'a member changed since it was judged'
    FROM k CROSS JOIN quad c ON c.p = k.counts AND c.o = k.yes
    CROSS JOIN quad v ON v.s = c.s AND v.p = k.verdict AND v.o = k.same
    CROSS JOIN quad h ON h.s = c.s AND h.p = k.member
    CROSS JOIN quad n ON n.s = h.o AND n.p = k.current_version
    WHERE NOT EXISTS (SELECT 1 FROM quad a CROSS JOIN quad t ON t.s = a.o AND t.p = k.type AND t.o = k.person
                      WHERE a.s = c.s AND a.p = k.attributed)
      AND NOT EXISTS (SELECT 1 FROM quad w WHERE w.s = c.s AND w.p = k.derived_from AND w.o = n.o)
      AND NOT EXISTS (
        SELECT 1 FROM quad ah CROSS JOIN quad ac ON ac.s = ah.s AND ac.p = k.counts AND ac.o = k.yes
        CROSS JOIN quad av ON av.s = ac.s AND av.p = k.verdict AND av.o = k.same
        CROSS JOIN quad ad ON ad.s = ac.s AND ad.p = k.derived_from
        CROSS JOIN quad cr ON cr.s = h.o AND cr.p = k.current_revision
        CROSS JOIN quad rd ON rd.s = cr.o AND rd.p = k.derived_from AND rd.o = ad.o
        WHERE ah.p = k.member AND ah.o = h.o
          AND EXISTS (SELECT 1 FROM quad a CROSS JOIN quad t ON t.s = a.o AND t.p = k.type AND t.o = k.person
                      WHERE a.s = ac.s AND a.p = k.attributed)
          AND NOT EXISTS (SELECT 1 FROM quad m WHERE m.s = c.s AND m.p = k.member
                            AND NOT EXISTS (SELECT 1 FROM quad am WHERE am.s = ac.s AND am.p = k.member AND am.o = m.o)))
    UNION
    SELECT i.o, 'retracted by someone other than who made it'
    FROM k CROSS JOIN quad i ON i.p = k.invalidated
    CROSS JOIN quad w ON w.s = i.s AND w.p = k.associated
    CROSS JOIN quad jt ON jt.s = i.o AND jt.p = k.type AND jt.o = k.judgment_class
    CROSS JOIN quad a ON a.s = i.o AND a.p = k.attributed
    CROSS JOIN quad mt ON mt.s = a.o AND mt.p = k.type AND mt.o = k.person
    WHERE w.o <> a.o
    UNION
    SELECT r.o, 'replaced by someone other than who made it'
    FROM k CROSS JOIN quad r ON r.p = k.replaces
    CROSS JOIN quad ra ON ra.s = r.s AND ra.p = k.attributed
    CROSS JOIN quad jt ON jt.s = r.o AND jt.p = k.type AND jt.o = k.judgment_class
    CROSS JOIN quad a ON a.s = r.o AND a.p = k.attributed
    CROSS JOIN quad mt ON mt.s = a.o AND mt.p = k.type AND mt.o = k.person
    WHERE ra.o <> a.o
      AND NOT EXISTS (SELECT 1 FROM quad c WHERE c.s = r.o AND c.p = k.counts AND c.o = k.yes))
SELECT DISTINCT judgment.nt AS judgment, label.nt AS judgmentLabel, '"' || needing.needs || '"' AS needs
FROM needing CROSS JOIN k CROSS JOIN term judgment ON judgment.id = needing.judgment
LEFT JOIN quad l ON l.s = needing.judgment AND l.p = k.label
LEFT JOIN term label ON label.id = l.o
ORDER BY label.kind, label.lex, judgment.kind, judgment.lex
