WITH
  k (type, record_class, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Record>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>')),
  shown (file, entry, label, record) AS NOT MATERIALIZED (
    SELECT file, entry, label, record FROM allergy_shown
    UNION ALL SELECT file, entry, label, record FROM condition_shown
    UNION ALL SELECT file, entry, label, record FROM immunization_shown
    UNION ALL SELECT file, entry, label, record FROM lab_result_shown
    UNION ALL SELECT file, entry, label, record FROM medication_dispense_shown
    UNION ALL SELECT file, entry, label, record FROM medication_shown
    UNION ALL SELECT file, entry, label, record FROM note_shown
    UNION ALL SELECT file, entry, label, record FROM patient_profile_shown
    UNION ALL SELECT file, entry, label, record FROM procedure_shown
    UNION ALL SELECT file, entry, label, record FROM report_shown
    UNION ALL SELECT file, entry, label, record FROM variant_interpretation_shown
    UNION ALL SELECT file, entry, label, record FROM variant_shown),
  chosen (file, entry, label, record) AS (
    SELECT file, entry, label, record FROM shown WHERE record IN (SELECT term FROM asked)
    UNION ALL SELECT file, entry, label, record FROM shown WHERE NOT EXISTS (SELECT 1 FROM asked)),
  named (file, entry, entry_label, record, record_label) AS (
    SELECT DISTINCT chosen.file, chosen.entry, chosen.label, chosen.record, rl.o
    FROM chosen CROSS JOIN k CROSS JOIN quad r ON r.s = chosen.record AND r.p = k.type AND r.o = k.record_class
    LEFT JOIN quad rl ON rl.s = chosen.record AND rl.p = k.label)
SELECT record.nt AS record, record_label.nt AS recordLabel, named.entry AS entry, entry_label.nt AS entryLabel,
  named.file AS view
FROM named CROSS JOIN term record ON record.id = named.record
LEFT JOIN term record_label ON record_label.id = named.record_label
LEFT JOIN term entry_label ON entry_label.id = named.entry_label
ORDER BY record_label.kind, record_label.lex, record.kind, record.lex, substr(named.entry, 2, length(named.entry) - 2)
