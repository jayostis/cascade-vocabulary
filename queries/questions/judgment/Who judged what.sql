WITH
  k (type, judgment_class, activity_class, attributed, generated_at, started_at, label, verdict, generated_by,
     qualified_association, agent, had_role, member, description, replaces, asserted_judgment, asserted_under,
     invalidated, associated) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Judgment>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#Activity>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#startedAtTime>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#verdict>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#qualifiedAssociation>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#agent>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadRole>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadMember>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/dc/terms/description>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/dc/terms/replaces>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#assertedJudgment>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#assertedUnderRuleListVersion>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#invalidated>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAssociatedWith>')),
  generated (judgment, author, generation, association, role) AS (
    SELECT DISTINCT j.s, ag.o, ge.o, qa.o, ro.o FROM k CROSS JOIN quad j ON j.p = k.type AND j.o = k.judgment_class
    CROSS JOIN quad ge ON ge.s = j.s AND ge.p = k.generated_by
    CROSS JOIN quad qa ON qa.s = ge.o AND qa.p = k.qualified_association
    CROSS JOIN quad ag ON ag.s = qa.o AND ag.p = k.agent
    CROSS JOIN quad ro ON ro.s = qa.o AND ro.p = k.had_role),
  -- A judgment names its maker, a hub every judgment file restates, so a maker is looked up once, not once for each statement of it.
  makers (agent, label) AS (
    SELECT DISTINCT m.o, l.o FROM (SELECT DISTINCT q.o FROM k CROSS JOIN quad q ON q.p IN (k.attributed, k.associated)) m CROSS JOIN k
    CROSS JOIN quad l ON l.s = m.o AND l.p = k.label),
  asserting (judgment, assertion, under) AS (
    SELECT DISTINCT an.o, an.s, aun.o FROM k CROSS JOIN quad an ON an.p = k.asserted_judgment
    CROSS JOIN quad aun ON aun.s = an.s AND aun.p = k.asserted_under),
  retracting (activity, author, association, role) AS (
    SELECT DISTINCT rt.s, ag.o, qa.o, ro.o FROM k CROSS JOIN quad rt ON rt.p = k.invalidated
    CROSS JOIN quad qa ON qa.s = rt.s AND qa.p = k.qualified_association
    CROSS JOIN quad ag ON ag.s = qa.o AND ag.p = k.agent
    CROSS JOIN quad ro ON ro.s = qa.o AND ro.p = k.had_role),
  said (judgment, label, made, verdict, author, author_label, generation, association, role, member, member_label,
        reason, replaces, replaces_label, assertion, asserted_under, retracts, retracts_label) AS (
    SELECT DISTINCT j.s, jl.o, ma.o, ve.o, au.o, al.label, g.generation, g.association, g.role, hm.o, ml.o, de.o, rp.o, rl.o, an.assertion, an.under,
      NULL, NULL
    FROM k CROSS JOIN quad j ON j.p = k.type AND j.o = k.judgment_class
    CROSS JOIN quad au ON au.s = j.s AND au.p = k.attributed
    LEFT JOIN quad ma ON ma.s = j.s AND ma.p = k.generated_at
    LEFT JOIN quad jl ON jl.s = j.s AND jl.p = k.label
    LEFT JOIN makers al ON al.agent = au.o
    LEFT JOIN quad ve ON ve.s = j.s AND ve.p = k.verdict
    LEFT JOIN generated g ON g.judgment = j.s AND g.author = au.o
    LEFT JOIN quad hm ON hm.s = j.s AND hm.p = k.member
    LEFT JOIN quad ml ON ml.s = hm.o AND ml.p = k.label
    LEFT JOIN quad de ON de.s = j.s AND de.p = k.description
    LEFT JOIN quad rp ON rp.s = j.s AND rp.p = k.replaces
    LEFT JOIN quad rl ON rl.s = rp.o AND rl.p = k.label
    LEFT JOIN asserting an ON an.judgment = j.s
    UNION ALL
    SELECT DISTINCT j.s, jl.o, ma.o, NULL, au.o, al.label, NULL, r.association, r.role, NULL, NULL, de.o, NULL, NULL, NULL, NULL,
      rt.o, rtl.o
    FROM k CROSS JOIN quad j ON j.p = k.type AND j.o = k.activity_class
    CROSS JOIN quad rt ON rt.s = j.s AND rt.p = k.invalidated
    CROSS JOIN quad au ON au.s = j.s AND au.p = k.associated
    LEFT JOIN quad ma ON ma.s = j.s AND ma.p = k.started_at
    LEFT JOIN quad jl ON jl.s = j.s AND jl.p = k.label
    LEFT JOIN makers al ON al.agent = au.o
    LEFT JOIN retracting r ON r.activity = j.s AND r.author = au.o
    LEFT JOIN quad de ON de.s = j.s AND de.p = k.description
    LEFT JOIN quad rtl ON rtl.s = rt.o AND rtl.p = k.label)
SELECT DISTINCT judgment.nt AS judgment, label.nt AS judgmentLabel, made.nt AS made, verdict.nt AS verdict, author.nt AS author,
  author_label.nt AS authorLabel, role.nt AS role, member.nt AS member, member_label.nt AS memberLabel,
  reason.nt AS reason, replaces.nt AS replaces, replaces_label.nt AS replacesLabel, retracts.nt AS retracts,
  retracts_label.nt AS retractsLabel, asserted_under.nt AS assertedUnder
FROM said CROSS JOIN term judgment ON judgment.id = said.judgment
CROSS JOIN term author ON author.id = said.author
LEFT JOIN term label ON label.id = said.label
LEFT JOIN term made ON made.id = said.made
LEFT JOIN term verdict ON verdict.id = said.verdict
LEFT JOIN term author_label ON author_label.id = said.author_label
LEFT JOIN term role ON role.id = said.role
LEFT JOIN term member ON member.id = said.member
LEFT JOIN term member_label ON member_label.id = said.member_label
LEFT JOIN term reason ON reason.id = said.reason
LEFT JOIN term replaces ON replaces.id = said.replaces
LEFT JOIN term replaces_label ON replaces_label.id = said.replaces_label
LEFT JOIN term retracts ON retracts.id = said.retracts
LEFT JOIN term retracts_label ON retracts_label.id = said.retracts_label
LEFT JOIN term asserted_under ON asserted_under.id = said.asserted_under
ORDER BY made.kind, made.instant, label.kind, label.lex, judgment.kind, judgment.lex, member_label.kind, member_label.lex,
  member.kind, member.lex, role.kind, role.lex, replaces.kind, replaces.lex, retracts.kind, retracts.lex,
  asserted_under.kind, asserted_under.lex
