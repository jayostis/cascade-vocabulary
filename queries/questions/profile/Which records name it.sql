WITH
  k (current_version, patient, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#patient>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
  -- The version is a variable the .rq hides: a record with two current versions naming one profile is two rows.
  named (record, version, profile, profile_label, record_label) AS (
    SELECT DISTINCT cv.s, cv.o, pa.o, pl.o, rl.o
    FROM k CROSS JOIN quad cv ON cv.p = k.current_version
    CROSS JOIN quad pa ON pa.s = cv.o AND pa.p = k.patient
    LEFT JOIN quad pl ON pl.s = pa.o AND pl.p = k.label
    LEFT JOIN quad rl ON rl.s = cv.s AND rl.p = k.label
    WHERE NOT EXISTS (SELECT 1 FROM asked) OR EXISTS (SELECT 1 FROM asked WHERE asked.term = cv.s))
SELECT profile.nt AS profile, profile_label.nt AS profileLabel, record.nt AS record, record_label.nt AS recordLabel
FROM named CROSS JOIN term profile ON profile.id = named.profile CROSS JOIN term record ON record.id = named.record
LEFT JOIN term profile_label ON profile_label.id = named.profile_label
LEFT JOIN term record_label ON record_label.id = named.record_label
ORDER BY profile_label.kind, profile_label.lex, profile.kind, profile.lex, record_label.kind, record_label.lex,
  record.kind, record.lex
