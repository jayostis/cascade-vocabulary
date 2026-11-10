"""The status codes are HL7's CodeSystems for FHIR R4, pinned under tests/terminology/hl7-fhir-r4/ (CC0)."""

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
DISPENSE_DERIVATION = "derivations/medication-dispense-lifecycles.rq"
DISPENSE_CLASSES = {
    "completed": "MedicationDispenseCompleted",
    "preparation": "MedicationDispenseInProgress", "in-progress": "MedicationDispenseInProgress",
    "on-hold": "MedicationDispenseInProgress",
    "cancelled": "MedicationDispenseNotCompleted", "declined": "MedicationDispenseNotCompleted",
    "stopped": "MedicationDispenseNotCompleted",
    "entered-in-error": "MedicationDispenseEnteredInError", "unknown": "MedicationDispenseUnknown",
}


def codes(file):
    def walk(concepts):
        for concept in concepts:
            yield concept["code"]
            yield from walk(concept.get("concept", []))

    return set(walk(json.loads((CODE_SYSTEMS / file).read_text(encoding="utf-8"))["concept"]))


FHIR_CODES = sorted(codes("codesystem-medicationrequest-status.json") | codes("codesystem-medication-statement-status.json"))


def derived(engine, record_class, derivation, statuses):
    """What the derivation gives a record of the class that states each status (None: states none), alone in an entry of
    its own, by the local name of the property: the record's class and, where the derivation gives one, the step that
    gave it."""
    store = ENGINES[engine]()
    triples = set()
    for number, status in enumerate(statuses):
        record, entry, version = (URIRef(f"urn:x:{name}{number}") for name in ("record", "entry", "version"))
        triples |= {(record, RDF.type, URIRef(CASCADE + record_class)), (record, URIRef(CASCADE + "inEntry"), entry),
                    (record, URIRef(PAV + "hasCurrentVersion"), version)}
        if status is not None:
            triples.add((version, URIRef(CASCADE + "workflowStatus"), Literal(status)))
    store.add(triples)
    found = store.construct(query(derivation))
    return {status: {p.removeprefix(CASCADE): o for s, p, o in found if s == URIRef(f"urn:x:record{number}")}
            for number, status in enumerate(statuses)}


def medication_lifecycles(engine):
    """The step that gave each code of the two medication status lists its class."""
    found = derived(engine, "PrescribedOrReportedMedication", DERIVATION, FHIR_CODES)
    return {code: int(found[code]["currentVersionStatusLifecycleStep"]) for code in FHIR_CODES}


def dispense_lifecycles(engine, statuses):
    """The class the dispense derivation gives each status, by its local name."""
    found = derived(engine, "MedicationDispense", DISPENSE_DERIVATION, statuses)
    return {status: found[status]["currentVersionStatusLifecycle"].removeprefix(CASCADE) for status in statuses}


class TestMedicationStatusCodes:
    """Medication status codes the lifecycle derivations class · queries/derivations/medication-lifecycles.rq,
    queries/derivations/medication-dispense-lifecycles.rq

    A medication's status is classed as active, stopped, paused, unknown or entered in error, and a pharmacy's dispense
    by a table of its own. HL7 publishes the status codes a FHIR server may send; these derivations class every one of
    them by name, so none falls through to unknown.

    @rule lifecycle L1
    @rule lifecycle L2
    """

    class TestGivenAMedicationThatStatesEachCode:
        """given a medication that states each code of HL7's two medication status lists"""

        @pytest.mark.parametrize("engine", sorted(ENGINES))
        def test_classes_every_code_by_a_row_of_its_own(self, engine):
            """classes every code by a row of its own, the third place in L1's order

            One medication states each code of the two lists, `MedicationRequest.status` and `MedicationStatement.status`.
            The derivation gives each the class of the row for that code, which is the third place in L1's order, and not
            the second, where an absent or unlisted status falls to unknown.
            """
            assert medication_lifecycles(engine) == dict.fromkeys(FHIR_CODES, 3)

    class TestGivenAMedicationThatStatesNoCode:
        @pytest.mark.parametrize("engine", sorted(ENGINES))
        def test_is_unknown_by_the_second_step_of_l1(self, engine):
            """is unknown by the second step of L1, on the record and not only on its entry

            One medication whose current version states no status is given to the derivation. The record's own class
            is unknown and the step that gave it is 2, as L1's order says.
            """
            record = derived(engine, "PrescribedOrReportedMedication", DERIVATION, [None])[None]
            assert record["currentVersionStatusLifecycle"].removeprefix(CASCADE) == "MedicationUnknown"
            assert int(record["currentVersionStatusLifecycleStep"]) == 2

    class TestGivenHl7sListOfDispenseStatusCodes:
        """given HL7's list of MedicationDispense status codes"""

        def test_holds_exactly_the_nine_codes_that_l2_gives_a_class(self):
            """holds exactly the nine codes that L2 gives a class

            The codes in HL7's `MedicationDispense.status` list are compared with the nine codes the test holds as the
            ones L2 gives a class, so a code HL7 adds, or one L2 names that HL7 does not, fails here.
            """
            assert set(codes("codesystem-medicationdispense-status.json")) == set(DISPENSE_CLASSES)

    class TestGivenADispenseThatStatesEachCode:
        """given a dispense that states each of those codes"""

        @pytest.mark.parametrize("engine", sorted(ENGINES))
        def test_has_the_class_l2_gives_its_code(self, engine):
            """has the class L2 gives its code

            One dispense states each of the nine codes. The class the derivation gives it is compared with the class L2
            names for that code: completed, in progress, not completed, entered in error or unknown.
            """
            assert dispense_lifecycles(engine, sorted(DISPENSE_CLASSES)) == DISPENSE_CLASSES

    class TestGivenADispenseThatStatesNoCode:
        @pytest.mark.parametrize("engine", sorted(ENGINES))
        def test_is_unknown_on_the_record_and_not_only_on_its_entry(self, engine):
            """is unknown on the record and not only on its entry

            One dispense whose current version states no status is given to the derivation. The record's own class is
            unknown, as L2 says an absent status is.
            """
            assert dispense_lifecycles(engine, [None]) == {None: "MedicationDispenseUnknown"}
