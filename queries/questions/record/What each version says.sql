WITH
  k (revision_of, version, specialization_of, label, display_name, display_date) AS (
    SELECT (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#revisionOf>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>'),
      coalesce((SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#specializationOf>'), 0),
      coalesce((SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'), 0),
      coalesce((SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#displayName>'), 0),
      coalesce((SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#displayDate>'), 0)),
  asking (record) AS (
    SELECT term FROM asked
    UNION ALL SELECT DISTINCT q.o FROM k CROSS JOIN quad q ON q.p = k.revision_of WHERE NOT EXISTS (SELECT 1 FROM asked)),
  versions (record, version) AS (
    SELECT DISTINCT asking.record, v.o
    FROM asking CROSS JOIN k CROSS JOIN quad r ON r.o = asking.record AND r.p = k.revision_of
    CROSS JOIN quad v ON v.s = r.s AND v.p = k.version),
  said (record, record_label, version, version_label, field, value, value_label) AS (
    SELECT DISTINCT versions.record, rl.o, versions.version, vl.o, f.p, f.o, xl.o
    FROM versions CROSS JOIN k CROSS JOIN quad f ON f.s = versions.version
    LEFT JOIN quad rl ON rl.s = versions.record AND rl.p = k.label
    LEFT JOIN quad vl ON vl.s = versions.version AND vl.p = k.label
    LEFT JOIN quad xl ON xl.s = f.o AND xl.p = k.label
    WHERE f.p NOT IN (k.specialization_of, k.label, k.display_name, k.display_date))
SELECT record.nt AS record, record_label.nt AS recordLabel, version.nt AS version, version_label.nt AS versionLabel,
  field.nt AS field, value.nt AS value, value_label.nt AS valueLabel
FROM said CROSS JOIN term record ON record.id = said.record CROSS JOIN term version ON version.id = said.version
CROSS JOIN term field ON field.id = said.field CROSS JOIN term value ON value.id = said.value
LEFT JOIN term record_label ON record_label.id = said.record_label
LEFT JOIN term version_label ON version_label.id = said.version_label
LEFT JOIN term value_label ON value_label.id = said.value_label
ORDER BY record_label.kind, record_label.lex, record.kind, record.lex, version.kind, version.lex, field.kind, field.lex,
  value.kind, value.instant, value.lex
