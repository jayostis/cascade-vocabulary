"""The medication lifecycle: every code of the two FHIR R4 medication status value sets is a row of the derivation, a
record with no status is unknown, an entry has the class of the record it takes its status from, and the engines agree
on all of them. The value sets are HL7's CodeSystems, pinned under
tests/terminology/hl7-fhir-r4/ (CC0)."""

import json
from pathlib import Path

import pytest
from rdflib import Literal, URIRef
from rdflib.namespace import RDF

from contract import query
from engines import ENGINES

CODE_SYSTEMS = Path(__file__).parent / "terminology" / "hl7-fhir-r4"
CASCADE = "https://ns.cascadeprotocol.org/cascade#"
PAV = "http://purl.org/pav/"
DERIVATION = "derivations/medication-lifecycles.rq"


def codes(file):
    def walk(concepts):
        for concept in concepts:
            yield concept["code"]
            yield from walk(concept.get("concept", []))

    return set(walk(json.loads((CODE_SYSTEMS / file).read_text(encoding="utf-8"))["concept"]))


FHIR_CODES = sorted(codes("codesystem-medicationrequest-status.json") | codes("codesystem-medication-statement-status.json"))


def lifecycles(engine, statuses):
    """What the derivation gives a record of one medication, alone in its entry, for each status, None for an absent
    one: its class and the step that gave it, and the entry's."""
    store = ENGINES[engine]()
    triples = set()
    for number, status in enumerate(statuses):
        record, entry, version = (URIRef(f"urn:x:{name}{number}") for name in ("record", "entry", "version"))
        triples |= {(record, RDF.type, URIRef(CASCADE + "PrescribedOrReportedMedication")), (record, URIRef(CASCADE + "inEntry"), entry),
                    (entry, URIRef(CASCADE + "statusFrom"), record), (record, URIRef(PAV + "hasCurrentVersion"), version)}
        if status is not None:
            triples.add((version, URIRef(CASCADE + "workflowStatus"), Literal(status)))
    store.add(triples)
    found = store.construct(query(DERIVATION))
    def of(subject, number, name):
        return next(o for s, p, o in found if s == URIRef(f"urn:x:{subject}{number}") and p == URIRef(CASCADE + name))

    return {number: ((of("record", number, "currentVersionStatusLifecycle"), int(of("record", number, "currentVersionStatusLifecycleStep"))),
                     (of("entry", number, "statusLifecycle"), int(of("entry", number, "statusLifecycleStep"))))
            for number in range(len(statuses))}


@pytest.mark.parametrize("engine", sorted(ENGINES))
def test_every_fhir_medication_status_code_is_a_row_of_its_own_an_absent_status_is_unknown_and_the_entry_has_its_records_class(engine):
    found = lifecycles(engine, [*FHIR_CODES, None])
    assert {code: found[number][0][1] for number, code in enumerate(FHIR_CODES)} == dict.fromkeys(FHIR_CODES, 3)
    assert found[len(FHIR_CODES)][0] == (URIRef(CASCADE + "MedicationUnknown"), 2)
    assert all(record == entry for record, entry in found.values())
