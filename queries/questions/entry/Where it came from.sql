WITH
  k (current_revision, generated_at, label, generated_by, derived_from, retrieved_on, attributed, current_version,
     foaf_name) AS (
    SELECT (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedOn>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>')),
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
  chosen (entry, label, record) AS (
    SELECT entry, label, record FROM shown WHERE record IN (SELECT term FROM asked)
    UNION ALL SELECT entry, label, record FROM shown WHERE NOT EXISTS (SELECT 1 FROM asked)),
  arrivals (entry, entry_label, record, revision, arrived) AS (
    SELECT DISTINCT chosen.entry, chosen.label, chosen.record, cr.o, a.o
    FROM chosen CROSS JOIN k CROSS JOIN quad cr ON cr.s = chosen.record AND cr.p = k.current_revision
    CROSS JOIN quad a ON a.s = cr.o AND a.p = k.generated_at),
  documents (revision, document) AS (
    SELECT DISTINCT arrivals.revision, d.o
    FROM arrivals CROSS JOIN k CROSS JOIN quad d ON d.s = arrivals.revision AND d.p = k.derived_from),
  hospitals (document, hospital) AS (
    SELECT documents.document, l.o FROM documents CROSS JOIN k
    CROSS JOIN quad a ON a.s = documents.document AND a.p = k.attributed
    CROSS JOIN quad l ON l.s = a.o AND l.p = k.label
    UNION SELECT documents.document, n.o FROM documents CROSS JOIN k
    CROSS JOIN quad a ON a.s = documents.document AND a.p = k.attributed
    CROSS JOIN quad c ON c.s = a.o AND c.p = k.current_version
    CROSS JOIN quad n ON n.s = c.o AND n.p = k.foaf_name),
  said (entry, entry_label, record, record_label, arrived, import, import_label, document, document_label, retrieved,
        hospital) AS (
    SELECT DISTINCT arrivals.entry, arrivals.entry_label, arrivals.record, rl.o, arrivals.arrived, im.o, il.o,
      doc.document, dl.o, rt.o, hos.hospital
    FROM arrivals CROSS JOIN k
    LEFT JOIN quad rl ON rl.s = arrivals.record AND rl.p = k.label
    LEFT JOIN quad im ON im.s = arrivals.revision AND im.p = k.generated_by
    LEFT JOIN quad il ON il.s = im.o AND il.p = k.label
    LEFT JOIN documents doc ON doc.revision = arrivals.revision
    LEFT JOIN quad dl ON dl.s = doc.document AND dl.p = k.label
    LEFT JOIN quad rt ON rt.s = doc.document AND rt.p = k.retrieved_on
    LEFT JOIN hospitals hos ON hos.document = doc.document)
SELECT said.entry AS entry, entry_label.nt AS entryLabel, record.nt AS record, record_label.nt AS recordLabel,
  arrived.nt AS arrived, import.nt AS import, import_label.nt AS importLabel, document.nt AS document,
  document_label.nt AS documentLabel, hospital.nt AS hospital, retrieved.nt AS retrieved
FROM said CROSS JOIN term record ON record.id = said.record CROSS JOIN term arrived ON arrived.id = said.arrived
LEFT JOIN term entry_label ON entry_label.id = said.entry_label
LEFT JOIN term record_label ON record_label.id = said.record_label
LEFT JOIN term import ON import.id = said.import
LEFT JOIN term import_label ON import_label.id = said.import_label
LEFT JOIN term document ON document.id = said.document
LEFT JOIN term document_label ON document_label.id = said.document_label
LEFT JOIN term hospital ON hospital.id = said.hospital
LEFT JOIN term retrieved ON retrieved.id = said.retrieved
ORDER BY entry_label.kind, entry_label.lex, substr(said.entry, 2, length(said.entry) - 2), arrived.instant,
  record_label.kind, record_label.lex, record.kind, record.lex, document.kind, document.lex, hospital.kind, hospital.lex,
  retrieved.kind, retrieved.instant
