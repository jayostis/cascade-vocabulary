-- A list question over the variants screen, paged as queries/statements.sql says.
WITH
  page (entry, iri, sort_key) AS (
    SELECT v.entry, v.iri, v.sort_key FROM variant v
    WHERE v.sort_key > coalesce(:after, '')
      AND EXISTS (SELECT 1 FROM variant_member m WHERE m.entry = v.entry)
    ORDER BY v.sort_key
    LIMIT coalesce(:page_size, -1)),
  shaped (entry, gene, hgvs, variation) AS (
    SELECT page.entry, g.gene, h.hgvs, NULL FROM page
      JOIN variant_hgvs h ON h.entry = page.entry LEFT JOIN variant_gene g ON g.entry = page.entry
    UNION SELECT page.entry, g.gene, NULL, x.variation FROM page
      JOIN variant_variation x ON x.entry = page.entry LEFT JOIN variant_gene g ON g.entry = page.entry
    UNION SELECT page.entry, g.gene, NULL, NULL FROM page
      LEFT JOIN variant_gene g ON g.entry = page.entry
      WHERE NOT EXISTS (SELECT 1 FROM variant_hgvs h WHERE h.entry = page.entry)
        AND NOT EXISTS (SELECT 1 FROM variant_variation x WHERE x.entry = page.entry))
SELECT page.iri AS variant, gene.nt AS gene, hgvs.nt AS hgvs, variation.nt AS variation,
  (SELECT '"' || group_concat(s.shown, '\u001F' ORDER BY s.line) || '"'
   FROM variant_source s WHERE s.entry = page.entry) AS sources,
  page.sort_key AS page_key
FROM page JOIN shaped ON shaped.entry = page.entry
LEFT JOIN term gene ON gene.id = shaped.gene
LEFT JOIN term hgvs ON hgvs.id = shaped.hgvs
LEFT JOIN term variation ON variation.id = shaped.variation
ORDER BY page.sort_key, hgvs.kind, hgvs.lex, variation.kind, variation.lex
