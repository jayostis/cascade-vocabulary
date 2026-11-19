-- A list question over the variant interpretations screen, paged as queries/statements.sql says: a page is of reports,
-- each with the variant it interprets, in the order the question gives.
WITH
  page (entry, variant_iri, sort_key) AS (
    SELECT x.entry, x.variant_iri, x.sort_key FROM variant_interpretation_variant x
    WHERE x.sort_key > coalesce(:after, '')
      AND EXISTS (SELECT 1 FROM variant_interpretation_member m WHERE m.entry = x.entry)
    ORDER BY x.sort_key
    LIMIT coalesce(:page_size, -1))
SELECT DISTINCT i.iri AS report, page.variant_iri AS variant, classification.nt AS classification, date.nt AS date,
  lab.nt AS lab, name.nt AS labName, page.sort_key AS page_key
FROM page CROSS JOIN variant_interpretation_terms k JOIN variant_interpretation i ON i.entry = page.entry
LEFT JOIN term classification ON classification.id = i.classification
LEFT JOIN term date ON date.id = i.date
LEFT JOIN term lab ON lab.id = i.lab
LEFT JOIN quad cv ON cv.s = i.lab AND cv.p = k.current_version
LEFT JOIN quad n ON n.s = cv.o AND n.p = k.foaf_name
LEFT JOIN term name ON name.id = n.o
ORDER BY page.sort_key
