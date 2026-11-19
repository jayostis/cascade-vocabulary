WITH
  k (revision_of, version, generated_at, current_revision, observed_as_of, last_update, label, was_revision_of,
     derived_from, retrieved_on, answered_as_of, attributed, current_version, foaf_name, generated_by, association,
     had_role, agent, transmitter_role, started_at) AS (
    SELECT (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#revisionOf>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#version>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#generatedAtTime>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#observedAsOf>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/lastUpdateOn>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasRevisionOf>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedOn>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#answeredAsOf>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasAttributedTo>'),
      (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>'),
      (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#qualifiedAssociation>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadRole>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#agent>'),
      (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#TransmitterRole>'),
      (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#startedAtTime>')),
  asking (record) AS (
    SELECT term FROM asked
    UNION ALL SELECT DISTINCT q.o FROM k CROSS JOIN quad q ON q.p = k.revision_of WHERE NOT EXISTS (SELECT 1 FROM asked)),
  -- A version is first received when its earliest arrival, in any record's revision, was.
  revisions (record, revision, version, arrived, first) AS (
    SELECT DISTINCT asking.record, r.s, v.o, a.o,
      (SELECT min(t.instant) FROM quad other CROSS JOIN quad g ON g.s = other.s AND g.p = k.generated_at
         CROSS JOIN term t ON t.id = g.o
         WHERE other.p = k.version AND other.o = v.o)
    FROM asking CROSS JOIN k CROSS JOIN quad r ON r.o = asking.record AND r.p = k.revision_of
    CROSS JOIN quad v ON v.s = r.s AND v.p = k.version
    CROSS JOIN quad a ON a.s = r.s AND a.p = k.generated_at),
  documents (revision, document) AS (
    SELECT DISTINCT revisions.revision, d.o
    FROM revisions CROSS JOIN k CROSS JOIN quad d ON d.s = revisions.revision AND d.p = k.derived_from),
  hospitals (document, hospital) AS (
    SELECT documents.document, l.o FROM documents CROSS JOIN k
    CROSS JOIN quad a ON a.s = documents.document AND a.p = k.attributed
    CROSS JOIN quad l ON l.s = a.o AND l.p = k.label
    UNION SELECT documents.document, n.o FROM documents CROSS JOIN k
    CROSS JOIN quad a ON a.s = documents.document AND a.p = k.attributed
    CROSS JOIN quad c ON c.s = a.o AND c.p = k.current_version
    CROSS JOIN quad n ON n.s = c.o AND n.p = k.foaf_name),
  transmitters (document, transmitter) AS (
    SELECT DISTINCT documents.document, tl.o FROM documents CROSS JOIN k
    CROSS JOIN quad g ON g.s = documents.document AND g.p = k.generated_by
    CROSS JOIN quad s ON s.s = g.o AND s.p = k.association
    CROSS JOIN quad ro ON ro.s = s.o AND ro.p = k.had_role AND ro.o = k.transmitter_role
    CROSS JOIN quad ag ON ag.s = s.o AND ag.p = k.agent
    CROSS JOIN quad tl ON tl.s = ag.o AND tl.p = k.label),
  said (record, record_label, arrived, observed, changed, revision, revision_label, current, previous, previous_label,
        version, version_label, change, document, document_label, retrieved, answered_as_of, hospital, transmitter,
        import, import_label, started) AS (
    SELECT DISTINCT revisions.record, rl.o, revisions.arrived, ob.o, ch.o, revisions.revision, vl.o,
      CASE WHEN now.o IS NOT NULL AND now.o = revisions.revision THEN 1 ELSE 0 END,
      pr.o, prl.o, revisions.version, ver.o,
      CASE WHEN t.instant = revisions.first THEN 0 ELSE 1 END,
      doc.document, dl.o, rt.o, aa.o, hos.hospital, tr.transmitter, im.o, il.o, st.o
    FROM revisions CROSS JOIN k CROSS JOIN term t ON t.id = revisions.arrived
    LEFT JOIN quad now ON now.s = revisions.record AND now.p = k.current_revision
    LEFT JOIN quad ob ON ob.s = revisions.revision AND ob.p = k.observed_as_of
    LEFT JOIN quad ch ON ch.s = revisions.revision AND ch.p = k.last_update
    LEFT JOIN quad vl ON vl.s = revisions.revision AND vl.p = k.label
    LEFT JOIN quad rl ON rl.s = revisions.record AND rl.p = k.label
    LEFT JOIN quad ver ON ver.s = revisions.version AND ver.p = k.label
    LEFT JOIN quad pr ON pr.s = revisions.revision AND pr.p = k.was_revision_of
    LEFT JOIN quad prl ON prl.s = pr.o AND prl.p = k.label
    LEFT JOIN documents doc ON doc.revision = revisions.revision
    LEFT JOIN quad dl ON dl.s = doc.document AND dl.p = k.label
    LEFT JOIN quad rt ON rt.s = doc.document AND rt.p = k.retrieved_on
    LEFT JOIN quad aa ON aa.s = doc.document AND aa.p = k.answered_as_of
    LEFT JOIN hospitals hos ON hos.document = doc.document
    LEFT JOIN transmitters tr ON tr.document = doc.document
    LEFT JOIN quad im ON im.s = revisions.revision AND im.p = k.generated_by
    LEFT JOIN quad il ON il.s = im.o AND il.p = k.label
    LEFT JOIN quad st ON st.s = im.o AND st.p = k.started_at)
SELECT record.nt AS record, record_label.nt AS recordLabel, arrived.nt AS arrived, observed.nt AS observed,
  changed.nt AS changed, revision.nt AS revision, revision_label.nt AS revisionLabel,
  CASE said.current WHEN 1 THEN '"true"^^<http://www.w3.org/2001/XMLSchema#boolean>'
    ELSE '"false"^^<http://www.w3.org/2001/XMLSchema#boolean>' END AS current,
  previous.nt AS previous, previous_label.nt AS previousLabel, version.nt AS version, version_label.nt AS versionLabel,
  CASE said.change WHEN 0 THEN '"a new version"' ELSE '"an earlier version again"' END AS change,
  document.nt AS document, document_label.nt AS documentLabel, retrieved.nt AS retrieved,
  answered_as_of.nt AS answeredAsOf, hospital.nt AS hospital, transmitter.nt AS transmitter, import.nt AS import,
  import_label.nt AS importLabel, started.nt AS started
FROM said CROSS JOIN term record ON record.id = said.record CROSS JOIN term arrived ON arrived.id = said.arrived
CROSS JOIN term revision ON revision.id = said.revision CROSS JOIN term version ON version.id = said.version
LEFT JOIN term record_label ON record_label.id = said.record_label
LEFT JOIN term observed ON observed.id = said.observed
LEFT JOIN term changed ON changed.id = said.changed
LEFT JOIN term revision_label ON revision_label.id = said.revision_label
LEFT JOIN term previous ON previous.id = said.previous
LEFT JOIN term previous_label ON previous_label.id = said.previous_label
LEFT JOIN term version_label ON version_label.id = said.version_label
LEFT JOIN term document ON document.id = said.document
LEFT JOIN term document_label ON document_label.id = said.document_label
LEFT JOIN term retrieved ON retrieved.id = said.retrieved
LEFT JOIN term answered_as_of ON answered_as_of.id = said.answered_as_of
LEFT JOIN term hospital ON hospital.id = said.hospital
LEFT JOIN term transmitter ON transmitter.id = said.transmitter
LEFT JOIN term import ON import.id = said.import
LEFT JOIN term import_label ON import_label.id = said.import_label
LEFT JOIN term started ON started.id = said.started
ORDER BY record_label.kind, record_label.lex, record.kind, record.lex, arrived.instant, revision.kind, revision.lex,
  document.kind, document.lex, retrieved.kind, retrieved.instant, answered_as_of.kind, answered_as_of.instant,
  hospital.kind, hospital.lex, transmitter.kind, transmitter.lex
