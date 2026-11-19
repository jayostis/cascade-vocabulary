WITH
  k (type, record_class, current_revision, generated_by, label, derived_from, attributed, current_version, foaf_name) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#Record>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>')),
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
  arrivals (entry, label, record, revision, is_record) AS (
    SELECT DISTINCT shown.entry, shown.label, shown.record, cr.o,
      EXISTS (SELECT 1 FROM quad t WHERE t.s = shown.record AND t.p = k.type AND t.o = k.record_class)
    FROM shown CROSS JOIN k CROSS JOIN quad cr ON cr.s = shown.record AND cr.p = k.current_revision),
  imports (revision, place) AS (
    SELECT DISTINCT arrivals.revision, l.o FROM arrivals CROSS JOIN k
    CROSS JOIN quad g ON g.s = arrivals.revision AND g.p = k.generated_by
    CROSS JOIN quad l ON l.s = g.o AND l.p = k.label),
  hospitals (revision, place) AS (
    SELECT arrivals.revision, l.o FROM arrivals CROSS JOIN k
    CROSS JOIN quad d ON d.s = arrivals.revision AND d.p = k.derived_from
    CROSS JOIN quad a ON a.s = d.o AND a.p = k.attributed
    CROSS JOIN quad l ON l.s = a.o AND l.p = k.label
    UNION SELECT arrivals.revision, n.o FROM arrivals CROSS JOIN k
    CROSS JOIN quad d ON d.s = arrivals.revision AND d.p = k.derived_from
    CROSS JOIN quad a ON a.s = d.o AND a.p = k.attributed
    CROSS JOIN quad c ON c.s = a.o AND c.p = k.current_version
    CROSS JOIN quad n ON n.s = c.o AND n.p = k.foaf_name),
  placed (entry, label, record, is_record, place) AS (
    SELECT DISTINCT arrivals.entry, arrivals.label, arrivals.record, arrivals.is_record, coalesce(h.place, i.place)
    FROM arrivals LEFT JOIN hospitals h ON h.revision = arrivals.revision
    LEFT JOIN imports i ON i.revision = arrivals.revision),
  seen (entry, places) AS (
    SELECT entry, count(DISTINCT CASE WHEN is_record THEN place END)
    FROM placed GROUP BY entry HAVING count(DISTINCT CASE WHEN is_record THEN record END) > 1),
  counted (entry, label, place, records, places) AS (
    SELECT placed.entry, placed.label, placed.place, count(DISTINCT placed.record), seen.places
    FROM placed CROSS JOIN seen ON seen.entry = placed.entry
    GROUP BY placed.entry, placed.label, placed.place, seen.places)
SELECT counted.entry AS entry, entry_label.nt AS entryLabel, place.nt AS place,
  '"' || counted.records || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS records,
  '"' || counted.places || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS places
FROM counted LEFT JOIN term entry_label ON entry_label.id = counted.label
LEFT JOIN term place ON place.id = counted.place
ORDER BY counted.places DESC, entry_label.kind, entry_label.lex, substr(counted.entry, 2, length(counted.entry) - 2),
  place.kind, place.lex
