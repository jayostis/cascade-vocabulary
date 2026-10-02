import json
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).absolute().parent.parent
EXAMPLE = ROOT / "example-pods" / "alex-rivera"
DOWNLOADS = EXAMPLE / "downloads"
EXPORTS = ["x-e2", "x-e4", "x-e6", "x-e10", "x-e12", "x-e15"]
FIXTURES = "https://github.com/jayostis/cascade-bridge-adapter-fhir-r4/blob/cabd6f52a98d1f0c97284f47347d61f3bb752504/fixtures/in/"

RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED = "http://snomed.info/sct"
CVX = "http://hl7.org/fhir/sid/cvx"
TERMINOLOGY = "http://terminology.hl7.org/CodeSystem/"
ATTRIBUTES = ["type", "identifier", "sourceName", "sourceURL", "fhirVersion", "receivedDate", "resourceFilePath"]
TYPES = {
    "AllergyIntolerance": "HKClinicalTypeIdentifierAllergyRecord",
    "Condition": "HKClinicalTypeIdentifierConditionRecord",
    "Immunization": "HKClinicalTypeIdentifierImmunizationRecord",
    "Procedure": "HKClinicalTypeIdentifierProcedureRecord",
}
MERIDIAN = ("Meridian Health System", "https://FHIR.Meridian.example/api/FHIR/R4")
LARKSPUR_OLD = ("Larkspur Valley Health", "https://EHR.Larkspur.example/fhir/R4")
LARKSPUR_NEW = ("Larkspur Valley Health", "https://fhir.larkspur.example/r4")
ALEX, SAM, H2O, H2F = "Patient/pat-conformance-1", "Patient/pat-rivera-2", "Patient/448812", "Patient/lv-7731"
NO_ENTRY_IN_X_E6 = "Immunization-imm-tdap-2026.json"

# file: [(versionId, lastUpdated, content)], content by type as below
ALLERGIES = {
    # clinical, verification, type, category, criticality, code, patient, onset, manifestations
    "AllergyIntolerance-alg-pcn-1.json": [("1", "2026-02-10T12:00:00Z", ("active", "confirmed", "allergy", "medication", "high", (RXNORM, "7980", "Penicillin G"), ALEX, "2019-06-14", ["Hives"]))],
    "AllergyIntolerance-alg-sulfa-1.json": [
        ("1", "2026-05-03T16:20:00Z", ("active", "confirmed", "allergy", "medication", "low", (RXNORM, "10180", "Sulfamethoxazole"), ALEX, "2022-05-03", ["Rash"])),
        ("2", "2026-11-12T14:00:00Z", ("active", "confirmed", "allergy", "medication", "low", (RXNORM, "10180", "Sulfamethoxazole"), ALEX, "2022-05-03", ["Rash", "Itching"])),
    ],
    "AllergyIntolerance-alg-latex-1.json": [
        ("1", "2026-07-21T10:15:00Z", ("active", "unconfirmed", "allergy", "environment", "low", (SNOMED, "111088007", "Latex"), ALEX, None, None)),
        ("2", "2026-11-18T09:40:00Z", ("active", "confirmed", "allergy", "environment", "low", (SNOMED, "111088007", "Latex"), ALEX, None, ["Contact dermatitis"])),
    ],
    "AllergyIntolerance-alg-codeine-1.json": [
        ("1", "2026-04-08T13:05:00Z", ("active", "unconfirmed", "intolerance", "medication", "low", (RXNORM, "2670", "Codeine"), ALEX, None, ["Nausea"])),
        ("2", "2026-11-18T09:45:00Z", (None, "entered-in-error", "intolerance", "medication", "low", (RXNORM, "2670", "Codeine"), ALEX, None, ["Nausea"])),
    ],
    "AllergyIntolerance-al-8237461.json": [("1", "2026-08-20T08:00:00Z", ("active", "confirmed", "allergy", "medication", None, (SNOMED, "373270004", "Penicillin"), H2O, None, ["Hives"]))],
    "AllergyIntolerance-al-8237462.json": [("1", "2026-08-20T08:00:00Z", ("active", "confirmed", "allergy", "medication", "high", (RXNORM, "10180", "Sulfamethoxazole"), H2O, None, ["Hives"]))],
    "AllergyIntolerance-alg-amox-2.json": [("1", "2027-01-28T16:00:00Z", ("active", "confirmed", "allergy", "medication", "low", (RXNORM, "723", "Amoxicillin"), SAM, None, ["Rash"]))],
    "AllergyIntolerance-lv-alg-101.json": [("1", "2027-03-01T00:00:00Z", ("active", "confirmed", "allergy", "medication", None, (SNOMED, "373270004", "Penicillin"), H2F, None, ["Hives"]))],
    "AllergyIntolerance-lv-alg-102.json": [("1", "2027-03-01T00:00:00Z", ("active", "confirmed", "allergy", "medication", "high", (RXNORM, "10180", "Sulfamethoxazole"), H2F, None, ["Hives"]))],
}
CONDITIONS = {
    # clinical, code, subject, onset, abatement
    "Condition-cond-htn-1.json": [
        ("3", "2026-01-02T09:00:00Z", ("active", (SNOMED, "38341003", "Essential hypertension"), ALEX, "2021-04-02", None)),
        ("4", "2026-11-15T11:30:00Z", ("active", (SNOMED, "38341003", "Essential hypertension"), ALEX, "2021-04-02", None)),
    ],
    "Condition-cond-bronch-1.json": [
        ("1", "2026-08-12T15:00:00Z", ("active", (SNOMED, "10509002", "Acute bronchitis"), ALEX, "2026-08-12", None)),
        ("2", "2026-10-30T10:00:00Z", ("resolved", (SNOMED, "10509002", "Acute bronchitis"), ALEX, "2026-08-12", "2026-09-20")),
    ],
    "Condition-cond-back-1.json": [
        ("1", "2026-06-01T11:00:00Z", ("active", (SNOMED, "279039007", "Low back pain"), ALEX, "2026-06-01", None)),
        ("2", "2026-11-10T16:00:00Z", ("resolved", (SNOMED, "279039007", "Low back pain"), ALEX, "2026-06-01", "2026-11-10")),
        ("3", "2027-05-14T10:00:00Z", ("active", (SNOMED, "279039007", "Low back pain"), ALEX, "2026-06-01", None)),
    ],
    "Condition-pr-30017.json": [("1", "2026-08-20T08:00:00Z", ("active", (SNOMED, "38341003", "Hypertension"), H2O, "2021-04-02", None))],
    "Condition-pr-30018.json": [("1", "2026-08-20T08:00:00Z", ("active", (SNOMED, "195967001", "Asthma"), H2O, "2008-09-01", None))],
    "Condition-cond-otitis-2.json": [("1", "2027-01-28T16:00:00Z", ("active", (SNOMED, "65363002", "Otitis media"), SAM, "2027-01-28", None))],
    "Condition-cond-eczema-2.json": [("1", "2027-01-28T16:00:00Z", ("active", (SNOMED, "24079001", "Atopic dermatitis"), SAM, "2019-05-10", None))],
    "Condition-lv-cond-201.json": [("1", "2027-03-01T00:00:00Z", ("active", (SNOMED, "38341003", "Essential hypertension"), H2F, "2021-04-02", None))],
    "Condition-lv-cond-202.json": [("1", "2027-03-01T00:00:00Z", ("active", (SNOMED, "195967001", "Asthma"), H2F, "2008-09-01", None))],
}
IMMUNIZATIONS = {
    # code, patient, occurrence
    "Immunization-imm-flu-2025.json": [("1", "2025-10-15T17:00:00Z", ((CVX, "141", "Influenza, seasonal"), ALEX, "2025-10-15"))],
    "Immunization-imm-tdap-2026.json": [("1", "2026-10-30T14:00:00Z", ((CVX, "115", "Tdap"), ALEX, "2026-10-30"))],
    "Immunization-im-5501.json": [("1", "2026-08-20T08:00:00Z", ((CVX, "141", "Influenza, seasonal"), H2O, "2025-10-15"))],
    "Immunization-lv-imm-301.json": [("1", "2027-03-01T00:00:00Z", ((CVX, "150", "Influenza, injectable, quadrivalent, preservative free"), H2F, "2025-10-15"))],
}
PROCEDURES = {
    # code, subject, performed
    "Procedure-proc-colonoscopy-1.json": [("1", "2025-02-18T19:00:00Z", ((SNOMED, "73761001", "Colonoscopy"), ALEX, "2025-02-18"))],
    "Procedure-proc-echo-1.json": [("1", "2026-11-05T15:30:00Z", ((SNOMED, "40701008", "Echocardiography"), ALEX, "2026-11-05"))],
    "Procedure-px-55120.json": [("1", "2026-08-20T08:00:00Z", ((SNOMED, "73761001", "Colonoscopy"), H2O, "2026-08-19"))],
    "Procedure-lv-proc-401.json": [("1", "2027-03-01T00:00:00Z", ((SNOMED, "73761001", "Colonoscopy"), H2F, "2026-08-19"))],
}
SCENARIO = {**ALLERGIES, **CONDITIONS, **IMMUNIZATIONS, **PROCEDURES}

# export: (files new or changed in it, their account, their receivedDate, files it drops)
X_E2_FILES = [
    "AllergyIntolerance-alg-pcn-1.json", "AllergyIntolerance-alg-sulfa-1.json", "AllergyIntolerance-alg-latex-1.json",
    "AllergyIntolerance-alg-codeine-1.json", "Condition-cond-htn-1.json", "Condition-cond-bronch-1.json",
    "Condition-cond-back-1.json", "Immunization-imm-flu-2025.json", "Procedure-proc-colonoscopy-1.json",
]
CHANGES = {
    "x-e2": (X_E2_FILES, MERIDIAN, "2026-09-01 10:00:00 +0000", []),
    "x-e4": ([f for f in SCENARIO if f.split("-", 1)[1].startswith(("al-", "pr-", "im-", "px-"))], LARKSPUR_OLD, "2026-10-14 15:40:00 +0000", []),
    "x-e6": ([
        "AllergyIntolerance-alg-sulfa-1.json", "AllergyIntolerance-alg-latex-1.json", "AllergyIntolerance-alg-codeine-1.json",
        "Condition-cond-htn-1.json", "Condition-cond-bronch-1.json", "Condition-cond-back-1.json",
        "Procedure-proc-echo-1.json", NO_ENTRY_IN_X_E6,
    ], MERIDIAN, "2026-11-20 09:00:00 +0000", []),
    "x-e10": (["AllergyIntolerance-alg-amox-2.json", "Condition-cond-otitis-2.json", "Condition-cond-eczema-2.json"], MERIDIAN, "2027-02-10 17:19:00 +0000", []),
    "x-e12": ([f for f in SCENARIO if "-lv-" in f], LARKSPUR_NEW, "2027-03-18 12:00:00 +0000", []),
    "x-e15": (["Condition-cond-back-1.json"], MERIDIAN, "2027-08-20 08:00:00 +0000", ["AllergyIntolerance-alg-latex-1.json"]),
}
IMPORTED = {
    "x-e2": "2026-09-01T10:00:04Z", "x-e4": "2026-10-14T15:42:00Z", "x-e6": "2026-11-20T09:00:04Z",
    "x-e10": "2027-02-10T17:21:00Z", "x-e12": "2027-03-18T12:00:04Z", "x-e15": "2027-08-20T08:00:04Z",
}
BASED_ON = {
    "AllergyIntolerance-alg-pcn-1.json": "allergy-with-id.json",
    "Condition-cond-htn-1.json": "condition-with-id-meta-fetch-a.json",
    "Immunization-imm-flu-2025.json": "immunization-with-id.json",
    "Procedure-proc-colonoscopy-1.json": "procedure-with-id.json",
    "Procedure-proc-echo-1.json": "procedure-no-id-echocardiogram.json",
}
CODES_TO_CONFIRM = [
    (RXNORM, "2670"), (RXNORM, "723"), (SNOMED, "111088007"), (SNOMED, "373270004"), (SNOMED, "10509002"),
    (SNOMED, "279039007"), (SNOMED, "195967001"), (SNOMED, "65363002"), (SNOMED, "24079001"), (CVX, "150"), (CVX, "115"),
]


def export_root(export):
    return DOWNLOADS / export / "apple_health_export"


def entries(export):
    return list(ElementTree.parse(export_root(export) / "export.xml").getroot())


def records(export):
    return {path.name: path for path in sorted((export_root(export) / "clinical-records").iterdir())}


def resource(path):
    return json.loads(path.read_text(encoding="utf-8"))


def entry_by_file(export):
    return {e.get("resourceFilePath").removeprefix("/clinical-records/"): e for e in entries(export) if e.tag == "ClinicalRecord"}


def crate():
    return json.loads((EXAMPLE / "ro-crate-metadata.json").read_text(encoding="utf-8"))


def crate_files():
    return [e for e in crate()["@graph"] if e.get("@type") == "File"]


def every_download():
    return sorted(p for p in DOWNLOADS.rglob("*") if p.is_file())


def status(system, code):
    return {"coding": [{"system": TERMINOLOGY + system, "code": code}]}


def concept(code):
    system, value, display = code
    return {"coding": [{"system": system, "code": value, "display": display}], "text": display}


def expected_resource(name, version_id, last_updated, content):
    resource_type, rid = name.removesuffix(".json").split("-", 1)
    expected = {"resourceType": resource_type, "id": rid, "meta": {"versionId": version_id, "lastUpdated": last_updated}}
    if resource_type == "AllergyIntolerance":
        clinical, verification, kind, category, criticality, code, patient, onset, manifestations = content
        if clinical:
            expected["clinicalStatus"] = status("allergyintolerance-clinical", clinical)
        expected["verificationStatus"] = status("allergyintolerance-verification", verification)
        expected |= {"type": kind, "category": [category], "code": concept(code), "patient": {"reference": patient}}
        if criticality:
            expected["criticality"] = criticality
        if onset:
            expected["onsetDateTime"] = onset
        if manifestations:
            expected["reaction"] = [{"manifestation": [{"text": t} for t in manifestations]}]
    elif resource_type == "Condition":
        clinical, code, subject, onset, abatement = content
        expected |= {"clinicalStatus": status("condition-clinical", clinical),
                     "verificationStatus": status("condition-ver-status", "confirmed"),
                     "code": concept(code), "subject": {"reference": subject}, "onsetDateTime": onset}
        if abatement:
            expected["abatementDateTime"] = abatement
    elif resource_type == "Immunization":
        code, patient, occurrence = content
        expected |= {"status": "completed", "vaccineCode": concept(code), "patient": {"reference": patient},
                     "occurrenceDateTime": occurrence}
    else:
        code, subject, performed = content
        expected |= {"status": "completed", "code": concept(code), "subject": {"reference": subject},
                     "performedDateTime": performed}
    return expected


def test_the_six_exports_are_the_only_folders_under_downloads():
    assert sorted(p.name for p in DOWNLOADS.iterdir()) == sorted(EXPORTS)


@pytest.mark.parametrize("export", EXPORTS)
def test_every_export_folder_holds_export_xml_and_clinical_records_and_nothing_else(export):
    assert sorted(p.name for p in (DOWNLOADS / export).iterdir()) == ["apple_health_export"]
    assert sorted(p.name for p in export_root(export).iterdir()) == ["clinical-records", "export.xml"]
    assert all(p.is_file() and p.suffix == ".json" for p in (export_root(export) / "clinical-records").iterdir())


@pytest.mark.parametrize("export", EXPORTS)
def test_export_xml_is_health_data_with_one_export_date_then_clinical_records_in_file_path_order(export):
    text = (export_root(export) / "export.xml").read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
    root = ElementTree.fromstring(text.encode("utf-8"))
    assert root.tag == "HealthData" and root.attrib == {"locale": "en_US"}
    children = list(root)
    assert children[0].tag == "ExportDate" and list(children[0].attrib) == ["value"]
    assert [c.tag for c in children[1:]] == ["ClinicalRecord"] * (len(children) - 1)
    paths = [c.get("resourceFilePath") for c in children[1:]]
    assert paths == sorted(paths)
    assert all(list(c.attrib) == ATTRIBUTES for c in children[1:])


@pytest.mark.parametrize("export", EXPORTS)
def test_export_date_is_two_seconds_before_the_import_starts(export):
    value = datetime.strptime(entries(export)[0].get("value"), "%Y-%m-%d %H:%M:%S %z")
    started = datetime.strptime(IMPORTED[export], "%Y-%m-%dT%H:%M:%S%z")
    assert started - value == timedelta(seconds=2)


@pytest.mark.parametrize("export", EXPORTS)
def test_every_entry_names_a_file_and_every_file_but_one_has_an_entry(export):
    by_file = entry_by_file(export)
    files = records(export)
    assert set(by_file) <= set(files)
    without = set(files) - set(by_file)
    assert without == ({NO_ENTRY_IN_X_E6} if export == "x-e6" else set())


@pytest.mark.parametrize("export", EXPORTS)
def test_every_entry_agrees_with_its_file(export):
    files = records(export)
    for name, entry in entry_by_file(export).items():
        r = resource(files[name])
        assert entry.get("identifier") == r["id"]
        assert name == f"{r['resourceType']}-{r['id']}.json"
        assert entry.get("sourceURL").endswith(f"/{r['resourceType']}/{r['id']}")
        assert entry.get("type") == TYPES[r["resourceType"]]
        assert entry.get("fhirVersion") == "4.0.1"


@pytest.mark.parametrize("before, after", list(zip(EXPORTS, EXPORTS[1:])))
def test_every_file_of_an_export_is_in_the_next_byte_for_byte_with_the_same_entry_unless_the_scenario_changes_it(before, after):
    changed, _, _, dropped = CHANGES[after]
    earlier, later = records(before), records(after)
    earlier_entries, later_entries = entry_by_file(before), entry_by_file(after)
    for name, path in earlier.items():
        if name in dropped:
            assert name not in later
        elif name not in changed:
            assert later[name].read_bytes() == path.read_bytes(), name
            if name in earlier_entries:
                assert later_entries[name].attrib == earlier_entries[name].attrib, name
    assert set(earlier) - set(later) == set(dropped)


@pytest.mark.parametrize("export", EXPORTS)
def test_each_exports_new_or_changed_files_and_their_received_date_are_the_scenarios(export):
    changed, account, received, _ = CHANGES[export]
    index = EXPORTS.index(export)
    previous = records(EXPORTS[index - 1]) if index else {}
    current = records(export)
    differs = {n for n, p in current.items() if n not in previous or previous[n].read_bytes() != p.read_bytes()}
    assert differs == set(changed)
    by_file = entry_by_file(export)
    for name in changed:
        if name == NO_ENTRY_IN_X_E6:
            continue
        entry = by_file[name]
        assert (entry.get("sourceName"), entry.get("receivedDate")) == (account[0], received)
        assert entry.get("sourceURL").startswith(account[1] + "/")


def test_the_unknown_server_file_gets_its_entry_from_x_e10_dated_to_x_e6():
    for export in EXPORTS[EXPORTS.index("x-e10"):]:
        entry = entry_by_file(export)[NO_ENTRY_IN_X_E6]
        assert entry.get("sourceName") == "Meridian Health System"
        assert entry.get("sourceURL") == "https://FHIR.Meridian.example/api/FHIR/R4/Immunization/imm-tdap-2026"
        assert entry.get("receivedDate") == "2026-11-20 09:00:00 +0000"


@pytest.mark.parametrize("export", EXPORTS)
def test_each_resource_holds_exactly_the_scenarios_content_for_its_handle(export):
    for name, path in records(export).items():
        r = resource(path)
        assert r["resourceType"] != "Patient"
        versions = {v: (v, updated, content) for v, updated, content in SCENARIO[name]}
        assert r == expected_resource(name, *versions[r["meta"]["versionId"]]), name


def test_the_metadata_only_changes_differ_from_their_x_e2_file_in_meta_alone():
    first = records("x-e2")
    for export, name in [(e, "Condition-cond-htn-1.json") for e in EXPORTS[2:]] + [("x-e15", "Condition-cond-back-1.json")]:
        a, b = resource(first[name]), resource(records(export)[name])
        assert a["meta"] != b["meta"]
        assert {k: v for k, v in a.items() if k != "meta"} == {k: v for k, v in b.items() if k != "meta"}
        assert list(a) == list(b)


def test_sams_files_name_his_patient_and_look_like_alexs_meridian_account():
    by_file = entry_by_file("x-e10")
    for name in CHANGES["x-e10"][0]:
        r = resource(records("x-e10")[name])
        assert (r.get("patient") or r.get("subject")) == {"reference": SAM}
        assert by_file[name].get("sourceName") == MERIDIAN[0]
        assert by_file[name].get("sourceURL").startswith(MERIDIAN[1] + "/")


def test_every_file_is_utf8_with_lf_endings_and_one_final_newline():
    for path in every_download():
        data = path.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf") and b"\r" not in data, path
        assert data.endswith(b"\n") and not data.endswith(b"\n\n"), path
        data.decode("utf-8")
        if path.suffix == ".json":
            assert data.decode("utf-8") == json.dumps(json.loads(data), indent=2, ensure_ascii=False) + "\n", path


def test_every_is_based_on_and_citation_in_the_crate_is_on_a_file_that_exists():
    described = [e["@id"] for e in crate()["@graph"] if "isBasedOn" in e or "citation" in e]
    assert described and [f for f in described if not (EXAMPLE / f).is_file()] == []


def _references(value):
    if isinstance(value, dict):
        return {value["@id"]} if set(value) == {"@id"} else set().union(*map(_references, value.values()))
    if isinstance(value, list):
        return set().union(*map(_references, value))
    return set()


def test_every_entity_in_the_crate_is_reached_from_its_metadata_descriptor():
    entities = {entity["@id"]: entity for entity in crate()["@graph"]}
    reached, todo = set(), ["ro-crate-metadata.json"]
    while todo:
        found = todo.pop()
        if found in entities and found not in reached:
            reached.add(found)
            todo.extend(_references(entities[found]))
    assert sorted(set(entities) - reached) == []


def test_every_resource_that_starts_from_a_fixture_names_it_by_is_based_on():
    entities = {entity["@id"]: entity for entity in crate_files()}
    for path in every_download():
        relative = path.relative_to(EXAMPLE).as_posix()
        based_on = entities.get(relative, {}).get("isBasedOn")
        assert based_on == ({"@id": FIXTURES + BASED_ON[path.name]} if path.name in BASED_ON else None), relative
    assert [e for e in entities if "isBasedOn" in entities[e] and not e.startswith("downloads/")] == []


def codes(path):
    r = resource(path)
    return {(c["system"], c["code"]) for field in ("code", "vaccineCode") for c in r.get(field, {}).get("coding", [])}


def test_every_code_to_confirm_has_its_source_recorded_on_the_first_file_that_uses_it():
    cited = {e["@id"]: {c["@id"] for c in e.get("citation", [])} for e in crate_files()}
    sources = {e["@id"] for e in crate()["@graph"] if e.get("@type") == "CreativeWork"}
    uses = [(export, name, path) for export in EXPORTS for name, path in records(export).items()]
    for code in CODES_TO_CONFIRM:
        export, name, _ = next(use for use in uses if code in codes(use[2]))
        citations = cited[f"downloads/{export}/apple_health_export/clinical-records/{name}"]
        assert len(citations) == 1 and citations <= sources, (code, name)
