WITH
  k (type, import_kind, session_kind, started_at, was_generated_by, revision_of, version, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#DocumentImport>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#HandEntrySession>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#startedAtTime>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#revisionOf>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'))
SELECT DISTINCT started.nt AS started, import.nt AS import, import_label.nt AS importLabel, record.nt AS record,
  record_label.nt AS recordLabel, revision.nt AS revision, revision_label.nt AS revisionLabel, version.nt AS version,
  version_label.nt AS versionLabel
FROM k CROSS JOIN quad i ON i.p = k.type AND i.o IN (k.import_kind, k.session_kind)
CROSS JOIN quad s ON s.s = i.s AND s.p = k.started_at
CROSS JOIN quad r ON r.o = i.s AND r.p = k.was_generated_by
CROSS JOIN quad rf ON rf.s = r.s AND rf.p = k.revision_of
CROSS JOIN quad v ON v.s = r.s AND v.p = k.version
CROSS JOIN term started ON started.id = s.o
CROSS JOIN term import ON import.id = i.s
CROSS JOIN term record ON record.id = rf.o
CROSS JOIN term revision ON revision.id = r.s
CROSS JOIN term version ON version.id = v.o
LEFT JOIN quad il ON il.s = i.s AND il.p = k.label
LEFT JOIN term import_label ON import_label.id = il.o
LEFT JOIN quad rl ON rl.s = rf.o AND rl.p = k.label
LEFT JOIN term record_label ON record_label.id = rl.o
LEFT JOIN quad vrl ON vrl.s = r.s AND vrl.p = k.label
LEFT JOIN term revision_label ON revision_label.id = vrl.o
LEFT JOIN quad vl ON vl.s = v.o AND vl.p = k.label
LEFT JOIN term version_label ON version_label.id = vl.o
WHERE NOT EXISTS (SELECT 1 FROM asked) OR EXISTS (SELECT 1 FROM asked WHERE asked.term = rf.o)
ORDER BY started.instant, import.kind, import.lex, record_label.kind, record_label.lex, revision.kind, revision.lex
