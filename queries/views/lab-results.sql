-- The lab results screen: the view as tables, in the parts queries/statements.sql names. `lab_result` has a row for
-- each entry with a lead, holding what the view states of it, its value as the view writes it; `lab_result_member`
-- its records; `lab_result_code` and `lab_result_interpretation` its codes and interpretation codes;
-- `lab_result_member_values` each member's current values, with their codes, interpretation codes and padded times.
-- The columns that read the labels output, filled by finish, are `lab_result.label` and `lab_result_source`.

-- part: tables
CREATE VIEW lab_result_terms AS SELECT
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') AS type,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#LaboratoryTestResult>') AS kind,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#inEntry>') AS in_entry,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#leadMember>') AS lead_member,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#statusFrom>') AS status_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/hasCurrentVersion>') AS current_version,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#testName>') AS test_name,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#testCode>') AS test_code,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultValueText>') AS value_text,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultUnitText>') AS unit_text_of_result,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#narrativeText>') AS narrative_text,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultQuantity>') AS quantity,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenValue>') AS written_value,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#quantityComparator>') AS comparator,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#unitText>') AS unit_text,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#ucumUnit>') AS ucum_unit,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#decimalValue>') AS decimal_value,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultRatioNumerator>') AS numerator,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultRatioDenominator>') AS denominator,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultValueRangeLow>') AS value_low,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultValueRangeHigh>') AS value_high,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#workflowStatus>') AS workflow_status,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultClinicallyRelevantTime>') AS performed,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#resultInterpretationCode>') AS interpretation,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#referenceRangeText>') AS range_text,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#referenceRangeLow>') AS range_low,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#referenceRangeHigh>') AS range_high,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>') AS padded,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>') AS padded_property,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>') AS time_as_written,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/2000/01/rdf-schema#label>') AS label,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#currentRevision>') AS current_revision,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasDerivedFrom>') AS derived_from,
  (SELECT id FROM term WHERE nt = '<http://purl.org/pav/retrievedOn>') AS retrieved_on,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#wasGeneratedBy>') AS generated_by,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#qualifiedAssociation>') AS association,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#hadRole>') AS had_role,
  (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/prov#agent>') AS agent,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#AuthorRole>') AS author_role,
  (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#CustodianRole>') AS custodian_role,
  (SELECT id FROM term WHERE nt = '<http://xmlns.com/foaf/0.1/name>') AS foaf_name,
  (SELECT CASE WHEN count(DISTINCT i.lex) = 1 THEN min(i.lex) END
   FROM quad w JOIN quad x ON x.s = w.s JOIN term i ON i.id = x.o
   WHERE w.p = (SELECT id FROM term WHERE nt = '<https://ns.cascadeprotocol.org/cascade#writtenByQueryPath>')
     AND w.o = (SELECT id FROM term WHERE nt = '"views/lab-results.rq"')
     AND x.p = (SELECT id FROM term WHERE nt = '<http://www.w3.org/ns/solid/terms#instance>')) AS address;

-- `entry` is the entry as the derived state names it, `iri` as the view names it. `sort_key` orders the entries by
-- the day they were performed, newest first, then the time as written, newest first, then test and entry, as My lab
-- results does. `value` is the value as the view writes it, N-Triples text; each other column is a term's id: the
-- lead member, the member status was taken from, the test, unit, narrative text, status and time, the time as written
-- of a time padded to a day, and the reference range's text and each bound's decimal, written value and units.
CREATE TABLE lab_result (
  entry INTEGER PRIMARY KEY,
  iri TEXT NOT NULL UNIQUE,
  sort_key TEXT NOT NULL UNIQUE,
  lead INTEGER NOT NULL,
  status_from INTEGER,
  test INTEGER,
  value TEXT,
  unit INTEGER,
  narrative INTEGER,
  status INTEGER,
  performed INTEGER,
  performed_written INTEGER,
  range_text INTEGER,
  low_decimal INTEGER,
  low_written INTEGER,
  low_ucum INTEGER,
  low_unit_text INTEGER,
  high_decimal INTEGER,
  high_written INTEGER,
  high_ucum INTEGER,
  high_unit_text INTEGER,
  label INTEGER
) STRICT;
CREATE TABLE lab_result_member (
  entry INTEGER NOT NULL,
  record INTEGER NOT NULL,
  PRIMARY KEY (entry, record)
) STRICT, WITHOUT ROWID;
CREATE INDEX lab_result_member_record ON lab_result_member (record);
CREATE TABLE lab_result_code (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE lab_result_interpretation (
  entry INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, code)
) STRICT, WITHOUT ROWID;
-- A member's current values, `node` naming them as the derived state names the entry.
CREATE TABLE lab_result_member_values (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  node TEXT NOT NULL,
  test INTEGER,
  value_text INTEGER,
  unit_text INTEGER,
  narrative INTEGER,
  status INTEGER,
  performed INTEGER,
  range_text INTEGER,
  low_decimal INTEGER,
  low_written INTEGER,
  low_ucum INTEGER,
  low_unit_text INTEGER,
  high_decimal INTEGER,
  high_written INTEGER,
  high_ucum INTEGER,
  high_unit_text INTEGER,
  PRIMARY KEY (entry, member)
) STRICT, WITHOUT ROWID;
CREATE TABLE lab_result_member_values_code (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE lab_result_member_values_interpretation (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  code INTEGER NOT NULL,
  PRIMARY KEY (entry, member, code)
) STRICT, WITHOUT ROWID;
CREATE TABLE lab_result_member_values_padded (
  entry INTEGER NOT NULL,
  member INTEGER NOT NULL,
  property INTEGER NOT NULL,
  written INTEGER NOT NULL,
  PRIMARY KEY (entry, member, property, written)
) STRICT, WITHOUT ROWID;
-- Where each of the entry's records came from, `line` as the list questions show it, `shown` the same in N-Triples.
CREATE TABLE lab_result_source (
  entry INTEGER NOT NULL,
  line TEXT NOT NULL,
  shown TEXT NOT NULL,
  PRIMARY KEY (entry, line)
) STRICT, WITHOUT ROWID;

INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES
  ('lab_result', 'sqlite_autoindex_lab_result_1', '8100 1'),
  ('lab_result', 'sqlite_autoindex_lab_result_2', '8100 1'),
  ('lab_result_code', 'lab_result_code', '8100 1 1'),
  ('lab_result_interpretation', 'lab_result_interpretation', '112 1 1'),
  ('lab_result_member', 'lab_result_member', '9000 2 1'),
  ('lab_result_member', 'lab_result_member_record', '9000 1'),
  ('lab_result_member_values', 'lab_result_member_values', '9000 2 1'),
  ('lab_result_member_values_code', 'lab_result_member_values_code', '9000 2 1 1'),
  ('lab_result_member_values_interpretation', 'lab_result_member_values_interpretation', '112 1 1 1'),
  ('lab_result_member_values_padded', 'lab_result_member_values_padded', '3000 2 1 1 1'),
  ('lab_result_source', 'lab_result_source', '9000 2 1');
ANALYZE sqlite_schema;

-- part: fill
CREATE TEMP TABLE IF NOT EXISTS lab_result_filled (entry INTEGER PRIMARY KEY) STRICT;
DELETE FROM lab_result_filled;
INSERT INTO lab_result_filled (entry)
  SELECT term FROM scope
  UNION SELECT q.o FROM lab_result_terms k CROSS JOIN scope JOIN quad q ON q.s = scope.term AND q.p = k.in_entry
  UNION SELECT entry FROM lab_result_member WHERE record IN (SELECT term FROM scope)
  UNION SELECT e.o FROM lab_result_terms k CROSS JOIN scope
    CROSS JOIN quad ag ON ag.o = scope.term AND ag.p = k.agent
    CROSS JOIN quad a ON a.o = ag.s AND a.p = k.association
    CROSS JOIN quad g ON g.o = a.s AND g.p = k.generated_by
    CROSS JOIN quad d ON d.o = g.s AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry
  UNION SELECT e.o FROM lab_result_terms k CROSS JOIN scope
    CROSS JOIN quad d ON d.o = scope.term AND d.p = k.derived_from
    CROSS JOIN quad cr ON cr.o = d.s AND cr.p = k.current_revision
    CROSS JOIN quad e ON e.s = cr.s AND e.p = k.in_entry;

DELETE FROM lab_result WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_member WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_code WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_interpretation WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_member_values WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_member_values_code WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_member_values_interpretation WHERE entry IN (SELECT entry FROM lab_result_filled);
DELETE FROM lab_result_member_values_padded WHERE entry IN (SELECT entry FROM lab_result_filled);

CREATE TEMP TABLE IF NOT EXISTS lab_result_stated (
  entry INTEGER PRIMARY KEY, lead INTEGER, status_from INTEGER, test INTEGER, text INTEGER, text_unit INTEGER,
  narrative INTEGER, quantity INTEGER, numerator INTEGER, denominator INTEGER, low INTEGER, high INTEGER,
  performed INTEGER, performed_written INTEGER, range_text INTEGER, low_at INTEGER, high_at INTEGER) STRICT;
DELETE FROM lab_result_stated;
INSERT INTO lab_result_stated (entry, lead, status_from, test, text, text_unit, narrative, quantity, numerator,
                               denominator, low, high, performed, performed_written, range_text, low_at, high_at)
WITH
  entries (entry, lead) AS (
    SELECT DISTINCT r.o, (SELECT min(l.o) FROM quad l WHERE l.s = r.o AND l.p = k.lead_member)
    FROM lab_result_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM lab_result_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)),
  led (entry, lead, version) AS (
    SELECT entries.entry, entries.lead,
      (SELECT min(v.o) FROM quad v WHERE v.s = entries.lead AND v.p = k.current_version)
    FROM lab_result_terms k CROSS JOIN entries WHERE entries.lead IS NOT NULL)
    SELECT led.entry, led.lead,
      (SELECT min(f.o) FROM quad f WHERE f.s = led.entry AND f.p = k.status_from
         AND EXISTS (SELECT 1 FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
                     WHERE v.s = f.o AND v.p = k.current_version)),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.test_name),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.value_text),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.unit_text_of_result),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.narrative_text),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.quantity
         AND EXISTS (SELECT 1 FROM quad w WHERE w.s = x.o AND w.p = k.written_value)),
      (SELECT min(w.o) FROM quad n
       JOIN quad w ON w.s = n.o AND w.p = k.written_value
       WHERE n.s = led.version AND n.p = k.numerator
         AND EXISTS (SELECT 1 FROM quad d JOIN quad dw ON dw.s = d.o AND dw.p = k.written_value
                     WHERE d.s = led.version AND d.p = k.denominator)),
      (SELECT min(w.o) FROM quad d
       JOIN quad w ON w.s = d.o AND w.p = k.written_value
       WHERE d.s = led.version AND d.p = k.denominator
         AND EXISTS (SELECT 1 FROM quad n JOIN quad nw ON nw.s = n.o AND nw.p = k.written_value
                     WHERE n.s = led.version AND n.p = k.numerator)),
      (SELECT min(w.o) FROM quad b
       JOIN quad w ON w.s = b.o AND w.p = k.written_value WHERE b.s = led.version AND b.p = k.value_low),
      (SELECT min(w.o) FROM quad b
       JOIN quad w ON w.s = b.o AND w.p = k.written_value WHERE b.s = led.version AND b.p = k.value_high),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.performed),
      (SELECT min(w.o) FROM quad d
       JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property AND dp.o = k.performed
       JOIN quad w ON w.s = d.o AND w.p = k.time_as_written WHERE d.s = led.version AND d.p = k.padded),
      (SELECT min(x.o) FROM quad x WHERE x.s = led.version AND x.p = k.range_text),
      (SELECT min(b.o) FROM quad b
       WHERE b.s = led.version AND b.p = k.range_low
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.decimal_value)
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.written_value)),
      (SELECT min(b.o) FROM quad b
       WHERE b.s = led.version AND b.p = k.range_high
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.decimal_value)
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.written_value))
    FROM lab_result_terms k CROSS JOIN led;

INSERT INTO lab_result (entry, iri, sort_key, lead, status_from, test, value, unit, narrative, status, performed,
                        performed_written, range_text, low_decimal, low_written, low_ucum, low_unit_text, high_decimal,
                        high_written, high_ucum, high_unit_text)
WITH
  stated AS (SELECT * FROM lab_result_stated),
  measured (entry, written, comparator, quantity_unit_text, quantity_ucum) AS (
    SELECT stated.entry,
      (SELECT min(x.o) FROM quad x WHERE x.s = stated.quantity AND x.p = k.written_value),
      (SELECT min(x.o) FROM quad x WHERE x.s = stated.quantity AND x.p = k.comparator),
      (SELECT min(x.o) FROM quad x WHERE x.s = stated.quantity AND x.p = k.unit_text),
      (SELECT min(x.o) FROM quad x WHERE x.s = stated.quantity AND x.p = k.ucum_unit)
    FROM lab_result_terms k CROSS JOIN stated),
  strings (id, said, lang) AS NOT MATERIALIZED (
    SELECT id, substr(nt, 2, length(nt) - 2 - coalesce(length(lang) + 1, 0)), lang FROM term
    WHERE datatype IN ('http://www.w3.org/2001/XMLSchema#string', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#langString')),
  valued (entry, value, unit) AS (
    SELECT stated.entry,
      CASE
        WHEN w.id IS NOT NULL AND (measured.comparator IS NULL OR c.id IS NOT NULL)
          THEN '"' || coalesce(c.said, '') || w.said || '"'
        WHEN n.id IS NOT NULL AND d.id IS NOT NULL THEN '"' || n.said || ':' || d.said || '"'
        WHEN stated.low IS NOT NULL AND stated.high IS NOT NULL AND lo.id IS NOT NULL AND hi.id IS NOT NULL
          THEN '"' || lo.said || '-' || hi.said || '"'
        WHEN stated.low IS NOT NULL AND stated.high IS NULL AND lo.id IS NOT NULL THEN '">=' || lo.said || '"'
        WHEN stated.low IS NULL AND hi.id IS NOT NULL THEN '"<=' || hi.said || '"'
        ELSE t.nt END,
      coalesce(measured.quantity_unit_text, measured.quantity_ucum, stated.text_unit)
    FROM stated JOIN measured ON measured.entry = stated.entry
    LEFT JOIN strings w ON w.id = measured.written LEFT JOIN strings c ON c.id = measured.comparator
    LEFT JOIN strings n ON n.id = stated.numerator LEFT JOIN strings d ON d.id = stated.denominator
    LEFT JOIN strings lo ON lo.id = stated.low LEFT JOIN strings hi ON hi.id = stated.high
    LEFT JOIN term t ON t.id = stated.text),
  named (entry, iri) AS (
    SELECT stated.entry, CASE WHEN substr(e.lex, 1, 18) = 'urn:cascade:entry:'
                              THEN k.address || '#' || substr(e.lex, 19) ELSE e.lex END
    FROM lab_result_terms k CROSS JOIN stated CROSS JOIN term e ON e.id = stated.entry),
  timed (entry, day, time) AS (
    SELECT stated.entry, CASE WHEN p.kind IN (2, 3) THEN substr(p.lex, 1, 10) ELSE '' END,
      CASE WHEN p.kind IN (2, 3) THEN p.lex ELSE '' END
    FROM stated LEFT JOIN term p ON p.id = stated.performed)
SELECT stated.entry, '<' || named.iri || '>',
  replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(
    replace(replace(hex(timed.day), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'),
    '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~'
  || replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(
    replace(replace(hex(timed.time), '0', 'p'), '1', 'o'), '2', 'n'), '3', 'm'), '4', 'l'), '5', 'k'), '6', 'j'),
    '7', 'i'), '8', 'h'), '9', 'g'), 'A', 'f'), 'B', 'e'), 'C', 'd'), 'D', 'c'), 'E', 'b'), 'F', 'a') || '~'
  || CASE WHEN test.id IS NULL THEN '0' ELSE test.kind || hex(coalesce(test.lex, '')) END || '.'
  || '2' || hex(named.iri) || '.',
  stated.lead, stated.status_from, stated.test, valued.value, valued.unit, stated.narrative,
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad v JOIN quad x ON x.s = v.o AND x.p = k.workflow_status
   WHERE v.s = stated.status_from AND v.p = k.current_version),
  stated.performed, stated.performed_written, stated.range_text,
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.low_at AND x.p = k.decimal_value),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.low_at AND x.p = k.written_value),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.low_at AND x.p = k.ucum_unit),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.low_at AND x.p = k.unit_text),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.high_at AND x.p = k.decimal_value),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.high_at AND x.p = k.written_value),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.high_at AND x.p = k.ucum_unit),
  (SELECT min(x.o) FROM lab_result_terms k CROSS JOIN quad x WHERE x.s = stated.high_at AND x.p = k.unit_text)
FROM stated JOIN named ON named.entry = stated.entry JOIN valued ON valued.entry = stated.entry
JOIN timed ON timed.entry = stated.entry LEFT JOIN term test ON test.id = stated.test;

INSERT INTO lab_result_member (entry, record)
SELECT DISTINCT r.o, r.s FROM lab_result_terms k CROSS JOIN quad r
WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM lab_result_filled) AND r.o IN (SELECT entry FROM lab_result)
  AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind);

INSERT INTO lab_result_code (entry, code)
SELECT DISTINCT c.entry, x.o FROM lab_result_terms k CROSS JOIN lab_result c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.test_code
WHERE c.entry IN (SELECT entry FROM lab_result_filled);

INSERT INTO lab_result_interpretation (entry, code)
SELECT DISTINCT c.entry, x.o FROM lab_result_terms k CROSS JOIN lab_result c
JOIN quad v ON v.s = c.lead AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.interpretation
WHERE c.entry IN (SELECT entry FROM lab_result_filled);

INSERT INTO lab_result_member_values (entry, member, node, test, value_text, unit_text, narrative, status, performed,
                                      range_text, low_decimal, low_written, low_ucum, low_unit_text, high_decimal,
                                      high_written, high_ucum, high_unit_text)
WITH
  members (entry, member, version) AS (
    SELECT DISTINCT r.o, r.s, (SELECT min(v.o) FROM quad v WHERE v.s = r.s AND v.p = k.current_version)
    FROM lab_result_terms k CROSS JOIN quad r
    WHERE r.p = k.in_entry AND r.o IN (SELECT entry FROM lab_result_filled)
      AND EXISTS (SELECT 1 FROM quad t WHERE t.s = r.s AND t.p = k.type AND t.o = k.kind)
      AND EXISTS (SELECT 1 FROM quad v WHERE v.s = r.s AND v.p = k.current_version)),
  bounded (entry, member, version, low_at, high_at) AS MATERIALIZED (
    SELECT members.entry, members.member, members.version,
      (SELECT min(b.o) FROM quad b
       WHERE b.s = members.version AND b.p = k.range_low
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.decimal_value)
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.written_value)),
      (SELECT min(b.o) FROM quad b
       WHERE b.s = members.version AND b.p = k.range_high
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.decimal_value)
         AND EXISTS (SELECT 1 FROM quad x WHERE x.s = b.o AND x.p = k.written_value))
    FROM lab_result_terms k CROSS JOIN members)
SELECT bounded.entry, bounded.member, '<' || e.lex || '-' || sparql_sha256(m.lex) || '>',
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.test_name),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.value_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.unit_text_of_result),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.narrative_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.workflow_status),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.performed),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.version AND x.p = k.range_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.low_at AND x.p = k.decimal_value),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.low_at AND x.p = k.written_value),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.low_at AND x.p = k.ucum_unit),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.low_at AND x.p = k.unit_text),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.high_at AND x.p = k.decimal_value),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.high_at AND x.p = k.written_value),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.high_at AND x.p = k.ucum_unit),
  (SELECT min(x.o) FROM quad x WHERE x.s = bounded.high_at AND x.p = k.unit_text)
FROM lab_result_terms k CROSS JOIN bounded JOIN term e ON e.id = bounded.entry JOIN term m ON m.id = bounded.member;

INSERT INTO lab_result_member_values_code (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM lab_result_terms k CROSS JOIN lab_result_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.test_code
WHERE mv.entry IN (SELECT entry FROM lab_result_filled);

INSERT INTO lab_result_member_values_interpretation (entry, member, code)
SELECT DISTINCT mv.entry, mv.member, x.o FROM lab_result_terms k CROSS JOIN lab_result_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad x ON x.s = v.o AND x.p = k.interpretation
WHERE mv.entry IN (SELECT entry FROM lab_result_filled);

INSERT INTO lab_result_member_values_padded (entry, member, property, written)
SELECT DISTINCT mv.entry, mv.member, dp.o, w.o FROM lab_result_terms k CROSS JOIN lab_result_member_values mv
JOIN quad v ON v.s = mv.member AND v.p = k.current_version JOIN quad d ON d.s = v.o AND d.p = k.padded
JOIN quad dp ON dp.s = d.o AND dp.p = k.padded_property JOIN quad w ON w.s = d.o AND w.p = k.time_as_written
WHERE mv.entry IN (SELECT entry FROM lab_result_filled);

-- part: finish
UPDATE lab_result SET label = (
  SELECT min(l.o) FROM lab_result_terms k CROSS JOIN quad l
  WHERE l.s = (SELECT id FROM term WHERE nt = lab_result.iri) AND l.p = k.label)
WHERE entry IN (SELECT entry FROM lab_result_filled);

DELETE FROM lab_result_source WHERE entry IN (SELECT entry FROM lab_result_filled);
INSERT OR IGNORE INTO lab_result_source (entry, line, shown)
WITH
  records (entry, record) AS (
    SELECT entry, record FROM lab_result_member WHERE entry IN (SELECT entry FROM lab_result_filled)),
  documents (record, document, retrieved) AS (
    SELECT DISTINCT cr.s, d.o, rt.o FROM lab_result_terms k CROSS JOIN quad cr
    JOIN quad d ON d.s = cr.o AND d.p = k.derived_from
    LEFT JOIN quad rt ON rt.s = d.o AND rt.p = k.retrieved_on
    WHERE cr.p = k.current_revision AND cr.s IN (SELECT record FROM records)),
  hospitals (document, line, shown) AS (
    SELECT DISTINCT g.s,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END || n.lex,
      CASE WHEN r.o = k.author_role THEN 'written by ' ELSE 'kept by ' END
        || substr(n.nt, 2, length(n.nt) - 2 - coalesce(length(n.lang) + 1, 0))
    FROM lab_result_terms k CROSS JOIN quad g
    JOIN quad a ON a.s = g.o AND a.p = k.association
    JOIN quad r ON r.s = a.o AND r.p = k.had_role AND r.o IN (k.author_role, k.custodian_role)
    JOIN quad ag ON ag.s = a.o AND ag.p = k.agent
    JOIN term n ON n.id IN (
      SELECT l.o FROM quad l WHERE l.s = ag.o AND l.p = k.label
      UNION SELECT x.o FROM quad v JOIN quad x ON x.s = v.o AND x.p = k.foaf_name
      WHERE v.s = ag.o AND v.p = k.current_version
        AND NOT EXISTS (SELECT 1 FROM quad l WHERE l.s = ag.o AND l.p = k.label))
    WHERE g.p = k.generated_by AND g.s IN (SELECT document FROM documents)
      AND n.datatype IN ('http://www.w3.org/2001/XMLSchema#string', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#langString')),
  came (record, document, retrieved, hospitals, hospitals_shown) AS (
    SELECT documents.record, documents.document, documents.retrieved,
      (SELECT group_concat(line, ', ' ORDER BY line) FROM hospitals h WHERE h.document = documents.document),
      (SELECT group_concat(shown, ', ' ORDER BY line) FROM hospitals h WHERE h.document = documents.document)
    FROM documents
    UNION ALL
    SELECT record, NULL, NULL, NULL, NULL FROM records
    WHERE record NOT IN (SELECT record FROM documents)),
  stated (record, document, document_shown, retrieved, retrieved_shown, hospitals, hospitals_shown) AS (
    SELECT came.record, d.lex,
      CASE d.kind WHEN 2 THEN d.lex WHEN 3 THEN substr(d.nt, 2, length(d.nt) - 2 - CASE WHEN d.lang IS NOT NULL
        THEN length(d.lang) + 1 WHEN d.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(d.datatype) + 4 END) END,
      t.lex,
      CASE t.kind WHEN 2 THEN t.lex WHEN 3 THEN substr(t.nt, 2, length(t.nt) - 2 - CASE WHEN t.lang IS NOT NULL
        THEN length(t.lang) + 1 WHEN t.datatype = 'http://www.w3.org/2001/XMLSchema#string' THEN 0
        ELSE length(t.datatype) + 4 END) END,
      came.hospitals, came.hospitals_shown
    FROM came LEFT JOIN term d ON d.id = came.document LEFT JOIN term t ON t.id = came.retrieved)
SELECT records.entry,
  r.lex || CASE WHEN stated.document_shown IS NULL THEN '' ELSE ' from ' || stated.document END
    || CASE WHEN stated.retrieved_shown IS NULL THEN '' ELSE ', retrieved ' || stated.retrieved END
    || coalesce(', ' || stated.hospitals, ''),
  r.lex || coalesce(' from ' || stated.document_shown, '') || coalesce(', retrieved ' || stated.retrieved_shown, '')
    || coalesce(', ' || stated.hospitals_shown, '')
FROM records CROSS JOIN stated ON stated.record = records.record JOIN term r ON r.id = records.record;

-- part: triples
WITH
  entries (s, entry) AS (SELECT e.nt, c.entry FROM lab_result c JOIN term e ON e.id = c.entry),
  members (node, entry, member) AS (SELECT node, entry, member FROM lab_result_member_values),
  bounds (low, high, entry, member) AS (
    SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-reference-low>', '<' || substr(e.s, 2, length(e.s) - 2)
           || '-reference-high>', e.entry, NULL FROM entries e
    UNION ALL
    SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-reference-low>', '<' || substr(mv.node, 2,
           length(mv.node) - 2) || '-reference-high>', mv.entry, mv.member FROM members mv),
  ranges (low, high, decimal_low, written_low, ucum_low, unit_text_low, decimal_high, written_high, ucum_high,
          unit_text_high) AS (
    SELECT b.low, b.high, c.low_decimal, c.low_written, c.low_ucum, c.low_unit_text, c.high_decimal, c.high_written,
           c.high_ucum, c.high_unit_text
    FROM bounds b JOIN lab_result c ON c.entry = b.entry WHERE b.member IS NULL
    UNION ALL
    SELECT b.low, b.high, v.low_decimal, v.low_written, v.low_ucum, v.low_unit_text, v.high_decimal, v.high_written,
           v.high_ucum, v.high_unit_text
    FROM bounds b JOIN lab_result_member_values v ON v.entry = b.entry AND v.member = b.member),
  said (s, p, o) AS (
    SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#testName>', c.test FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#testCode>', x.code FROM entries e JOIN lab_result_code x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#resultUnitText>', c.unit FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', c.narrative FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', c.status FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#resultClinicallyRelevantTime>', c.performed FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#resultInterpretationCode>', x.code FROM entries e JOIN lab_result_interpretation x ON x.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#referenceRangeText>', c.range_text FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#leadMember>', c.lead FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#statusFrom>', c.status_from FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#entryMember>', m.record FROM entries e JOIN lab_result_member m ON m.entry = e.entry
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-resultClinicallyRelevantTime>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', c.performed_written
      FROM entries e JOIN lab_result c ON c.entry = e.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#valuesOfMember>', mv.member FROM members mv
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#testName>', v.test FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#testCode>', x.code FROM members mv JOIN lab_result_member_values_code x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#resultValueText>', v.value_text FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#resultUnitText>', v.unit_text FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#narrativeText>', v.narrative FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#workflowStatus>', v.status FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#resultClinicallyRelevantTime>', v.performed FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#resultInterpretationCode>', x.code FROM members mv JOIN lab_result_member_values_interpretation x USING (entry, member)
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#referenceRangeText>', v.range_text FROM members mv JOIN lab_result_member_values v USING (entry, member)
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>', x.property
      FROM members mv JOIN lab_result_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>',
                     '<https://ns.cascadeprotocol.org/cascade#timeAsWritten>', x.written
      FROM members mv JOIN lab_result_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT low, '<https://ns.cascadeprotocol.org/cascade#decimalValue>', decimal_low FROM ranges WHERE written_low IS NOT NULL
    UNION ALL SELECT low, '<https://ns.cascadeprotocol.org/cascade#writtenValue>', written_low FROM ranges
    UNION ALL SELECT low, '<https://ns.cascadeprotocol.org/cascade#ucumUnit>', ucum_low FROM ranges WHERE written_low IS NOT NULL
    UNION ALL SELECT low, '<https://ns.cascadeprotocol.org/cascade#unitText>', unit_text_low FROM ranges WHERE written_low IS NOT NULL
    UNION ALL SELECT high, '<https://ns.cascadeprotocol.org/cascade#decimalValue>', decimal_high FROM ranges WHERE written_high IS NOT NULL
    UNION ALL SELECT high, '<https://ns.cascadeprotocol.org/cascade#writtenValue>', written_high FROM ranges
    UNION ALL SELECT high, '<https://ns.cascadeprotocol.org/cascade#ucumUnit>', ucum_high FROM ranges WHERE written_high IS NOT NULL
    UNION ALL SELECT high, '<https://ns.cascadeprotocol.org/cascade#unitText>', unit_text_high FROM ranges WHERE written_high IS NOT NULL),
  made (s, p, o) AS (
    SELECT s, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', '<https://ns.cascadeprotocol.org/cascade#LaboratoryTestResult>'
    FROM entries
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#resultValueText>', c.value
      FROM entries e JOIN lab_result c ON c.entry = e.entry WHERE c.value IS NOT NULL
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#memberCurrentValues>', mv.node
      FROM members mv JOIN entries e ON e.entry = mv.entry
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(mv.node, 2, length(mv.node) - 2) || '-padded-' || CASE WHEN instr(p.lex, '#') > 0
                       THEN substr(p.lex, instr(p.lex, '#') + 1) ELSE '' END || '>'
      FROM members mv JOIN lab_result_member_values_padded x USING (entry, member) JOIN term p ON p.id = x.property
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#paddedDateTime>',
                     '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-resultClinicallyRelevantTime>'
      FROM entries e JOIN lab_result c ON c.entry = e.entry WHERE c.performed_written IS NOT NULL
    UNION ALL SELECT '<' || substr(e.s, 2, length(e.s) - 2) || '-padded-resultClinicallyRelevantTime>',
                     '<https://ns.cascadeprotocol.org/cascade#paddedDateTimeProperty>',
                     '<https://ns.cascadeprotocol.org/cascade#resultClinicallyRelevantTime>'
      FROM entries e JOIN lab_result c ON c.entry = e.entry WHERE c.performed_written IS NOT NULL
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#referenceRangeLow>', b.low
      FROM entries e JOIN bounds b ON b.entry = e.entry AND b.member IS NULL JOIN lab_result c ON c.entry = e.entry
      WHERE c.low_written IS NOT NULL
    UNION ALL SELECT e.s, '<https://ns.cascadeprotocol.org/cascade#referenceRangeHigh>', b.high
      FROM entries e JOIN bounds b ON b.entry = e.entry AND b.member IS NULL JOIN lab_result c ON c.entry = e.entry
      WHERE c.high_written IS NOT NULL
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#referenceRangeLow>', b.low
      FROM members mv JOIN bounds b ON b.entry = mv.entry AND b.member = mv.member
      JOIN lab_result_member_values v USING (entry, member) WHERE v.low_written IS NOT NULL
    UNION ALL SELECT mv.node, '<https://ns.cascadeprotocol.org/cascade#referenceRangeHigh>', b.high
      FROM members mv JOIN bounds b ON b.entry = mv.entry AND b.member = mv.member
      JOIN lab_result_member_values v USING (entry, member) WHERE v.high_written IS NOT NULL)
SELECT said.s AS s, said.p AS p, o.nt AS o FROM said CROSS JOIN term o ON o.id = said.o
UNION ALL SELECT s, p, o FROM made
