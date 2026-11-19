WITH
  k (type, series_class, current_version, label) AS (
    SELECT (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ReferenceSeries>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'))
SELECT DISTINCT series.nt AS series, series_label.nt AS seriesLabel, version.nt AS version, version_label.nt AS versionLabel
FROM k CROSS JOIN quad t ON t.p = k.type AND t.o = k.series_class
CROSS JOIN quad c ON c.s = t.s AND c.p = k.current_version
CROSS JOIN term series ON series.id = t.s
CROSS JOIN term version ON version.id = c.o
LEFT JOIN quad sl ON sl.s = t.s AND sl.p = k.label
LEFT JOIN term series_label ON series_label.id = sl.o
LEFT JOIN quad vl ON vl.s = c.o AND vl.p = k.label
LEFT JOIN term version_label ON version_label.id = vl.o
ORDER BY series.kind, series.lex, version.kind, version.lex
