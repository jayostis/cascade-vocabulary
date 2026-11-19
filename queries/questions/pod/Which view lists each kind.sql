WITH
  k (type, registration, for_class, instance, title) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#TypeRegistration>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#forClass>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/dc/terms/title>')),
  shown (type, entry) AS (
    SELECT type, entry FROM allergy_shown
    UNION ALL SELECT type, entry FROM condition_shown
    UNION ALL SELECT type, entry FROM immunization_shown
    UNION ALL SELECT type, entry FROM lab_result_shown
    UNION ALL SELECT type, entry FROM medication_dispense_shown
    UNION ALL SELECT type, entry FROM medication_shown
    UNION ALL SELECT type, entry FROM note_shown
    UNION ALL SELECT type, entry FROM patient_profile_shown
    UNION ALL SELECT type, entry FROM procedure_shown
    UNION ALL SELECT type, entry FROM report_shown
    UNION ALL SELECT type, entry FROM variant_interpretation_shown
    UNION ALL SELECT type, entry FROM variant_shown),
  kinds (title, type, view) AS (
    SELECT DISTINCT ti.o, fc.o, ins.o
    FROM k CROSS JOIN quad reg ON reg.p = k.type AND reg.o = k.registration
    CROSS JOIN quad fc ON fc.s = reg.s AND fc.p = k.for_class
    CROSS JOIN quad ins ON ins.s = reg.s AND ins.p = k.instance
    CROSS JOIN quad ti ON ti.s = reg.s AND ti.p = k.title)
SELECT title.nt AS title, type.nt AS type, view.nt AS view,
  '"' || (SELECT count(DISTINCT shown.entry) FROM shown WHERE shown.type = type.nt)
    || '"^^<http://www.w3.org/2001/XMLSchema#integer>' AS entries
FROM kinds CROSS JOIN term title ON title.id = kinds.title CROSS JOIN term type ON type.id = kinds.type
CROSS JOIN term view ON view.id = kinds.view
ORDER BY title.kind, title.lex, view.kind, view.lex
