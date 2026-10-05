import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

import recomputed
from cascade_pod import derive, derived_files, vocabulary
from cascade_pod.pod import NOT_RDF
from examples import pod_file
from alex_rivera import ALEX, EXAMPLE, handle, handles, handles_by_name, name, pod

EXPECTED = EXAMPLE / "expected"
POD = ALEX.pod
POD_BASE = ALEX.address
HANDLE_NS = "urn:example:alex-rivera:handle:"
ENGINES = ("oxigraph", "rdflib")
LENSES = ("everyday", "export")
MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
IN_ENTRY = URIRef("https://ns.cascadeprotocol.org/records/v1-draft#inEntry")
REC = Namespace("https://ns.cascadeprotocol.org/records/v1-draft#")
JDG = Namespace("https://ns.cascadeprotocol.org/judgments/v1-draft#")
HEALTH = Namespace("https://ns.cascadeprotocol.org/health/v1#")
CLINICAL = Namespace("https://ns.cascadeprotocol.org/clinical/v1#")
PROV = Namespace("http://www.w3.org/ns/prov#")
PAV = Namespace("http://purl.org/pav/")
SH = Namespace("http://www.w3.org/ns/shacl#")

WEBID = URIRef(POD_BASE + "profile/card.ttl#me")
MERIDIAN = "https://fhir.meridian.example/api/FHIR/R4"
LARKSPUR_OLD = "https://ehr.larkspur.example/fhir/R4"
LARKSPUR_NEW = "https://fhir.larkspur.example/r4"
ARRIVED = {
    "E2": "2026-09-01T10:00:04Z",
    "E6": "2026-11-20T09:00:04Z",
    "E15": "2027-08-20T08:00:04Z",
}
BUILT = ("E1", "E3", "E5", "E6", "E7", "E8", "E9", "E10", "E12", "E13", "E14", "E15")
FROM_E5 = BUILT[BUILT.index("E5"):]
SAM = ("H1P-PAT", "H1P-ALG-AMOX", "H1P-CON-OTITIS", "H1P-CON-ECZEMA")

engines = pytest.mark.parametrize("engine", ENGINES)
lenses = pytest.mark.parametrize("lens", LENSES)


def adds(event):
    for row in ALEX.events:
        if row["event"] == event:
            return row["adds"]
    pytest.fail(f"events.json lists no event {event}")


def files_through(event):
    return tuple(ALEX.files(event))


def is_rdf(relative):
    return not relative.startswith(NOT_RDF)


def graph(triples):
    found = Graph()
    for triple in triples:
        found.add(triple)
    return found


def _string_typed(term):
    if isinstance(term, Literal) and term.datatype is None and term.language is None:
        return Literal(str(term), datatype=XSD.string)
    return term


@dataclass(frozen=True)
class Build:
    state: Graph
    views: dict
    needs_review: dict


@lru_cache(maxsize=None)
def build(engine, lens, event):
    held = ALEX.story_store(engine, event)
    derive.derive(held, lens)
    state = graph(held.triples())
    files = derived_files.add(ALEX, held, event)
    needs_review = {kind: held.select(vocabulary.query(vocabulary.questions()[f"{kind}/What needs review"]))
                    for kind in ("entry", "judgment")}
    views = {view: graph(files[path]) for view, path in ALEX.view_files.items()}
    return Build(state, views, needs_review)


def comparable(term):
    if isinstance(term, BNode):
        pytest.fail(f"a view names a blank node, {term}, as an object")
    if isinstance(term, URIRef):
        found = handles_by_name().get(str(term))
        return URIRef(HANDLE_NS + found) if found is not None else term
    return _string_typed(term)


def _member_handle(term):
    if str(term).startswith(HANDLE_NS):
        return str(term)[len(HANDLE_NS):]
    found = handles_by_name().get(str(term))
    if found is None:
        pytest.fail(f"entry member {term} has no handle")
    return found


def entries(graph):
    found = {}
    for subject in set(graph.subjects(MERGED_FROM, None)):
        members = frozenset(_member_handle(m) for m in graph.objects(subject, MERGED_FROM))
        if members in found:
            pytest.fail(f"two entries have the members {sorted(members)}")
        found[members] = {(p, comparable(o)) for p, o in graph.predicate_objects(subject)}
    return found


def values(pairs, predicate):
    return {o for p, o in pairs if p == predicate}


def members_shown(build):
    return {member for graph in build.views.values() for key in entries(graph) for member in key}


def entry_holding(build, view, member):
    held = [key for key in entries(build.views[view]) if member in key]
    assert len(held) == 1, f"{member} is in {len(held)} entries of the {view} view"
    return held[0]


def entry_members(build, entry):
    members = set(build.state.subjects(IN_ENTRY, entry))
    for graph in build.views.values():
        members.update(graph.objects(entry, MERGED_FROM))
    return frozenset(_member_handle(m) for m in members)


def entries_needing(build, needs):
    return [row for row in build.needs_review["entry"] if str(row["needs"]) == needs]


def listed_entries(build, needs):
    return {entry_members(build, row["entry"]) for row in entries_needing(build, needs)}


def listed_judgments(build):
    return {handle(row["judgment"]) for row in build.needs_review["judgment"]}


def listed_pairs(build):
    pairs = set()
    for row in entries_needing(build, "judged different, still joined"):
        record, other = row["record"], row["otherRecord"]
        assert str(record) < str(other), f"?record {record} is not the smaller of the pair by STR"
        pairs.add((handle(record), handle(other), entry_members(build, row["entry"])))
    return pairs


def describe(key, expected, actual):
    lines = [f"entry {sorted(key)}:"]
    lines += [f"  missing {p.n3()} {o.n3()}" for p, o in sorted(expected - actual, key=str)]
    lines += [f"  should not have {p.n3()} {o.n3()}" for p, o in sorted(actual - expected, key=str)]
    return "\n".join(lines)


def view_differences(expected, actual):
    report = []
    for key in sorted(set(expected) | set(actual), key=sorted):
        if key not in actual:
            report.append(f"entry {sorted(key)} is missing")
        elif key not in expected:
            report.append(f"entry {sorted(key)} should not be there")
        elif expected[key] != actual[key]:
            report.append(describe(key, expected[key], actual[key]))
    return report


def date(text):
    return Literal(text, datatype=XSD.date)


def string(text):
    return Literal(text, datatype=XSD.string)


def handle_iri(h):
    return URIRef(HANDLE_NS + h)


def versions_of(graph, record):
    return {handle(v) for v in graph.subjects(PROV.specializationOf, name(record))}


def revisions_of(graph, record):
    return {handle(r) for r in graph.subjects(REC.revisionOf, name(record))}


def counts(b, judgment):
    return any(str(o) in ("true", "1") for o in b.state.objects(name(judgment), REC.counts))


def current_versions(b, record):
    return {handle(v) for v in b.state.objects(name(record), PAV.hasCurrentVersion)}


def currently_same(b, one, other):
    return (name(one), JDG.currentlySame, name(other)) in b.state or (name(other), JDG.currentlySame, name(one)) in b.state


def entry_keys(b, view):
    return set(entries(b.views[view]))


def is_judgment(graph, judgment):
    return (name(judgment), RDF.type, JDG.Judgment) in graph


def names(graph, term):
    return any(term in triple for triple in graph)


def added_graph(event):
    graph = Graph()
    for relative in adds(event):
        if is_rdf(relative):
            graph += pod_file(ALEX, relative)
    return graph


def arrival(graph, revision):
    return str(graph.value(name(revision), PROV.generatedAtTime))


# P1
@engines
def test_one_allergy_at_two_hospitals_is_three_records_joined_by_a_machine_only_through_a_mapped_code_then_by_the_patient(engine):
    penicillins = ("H1-ALG-PCN", "H2O-ALG-PCN", "H2F-ALG-PCN")
    final = pod("E15")
    assert len({name(h) for h in penicillins}) == 3
    for h in penicillins:
        assert (name(h), RDF.type, HEALTH.AllergyRecord) in final, h

    machine = {
        handle(j)
        for j in final.subjects(PROV.hadMember, name("H1-ALG-PCN"))
        if (j, RDF.type, JDG.Judgment) in final and final.value(j, PROV.wasAttributedTo) != WEBID
    }
    assert machine == {"J4"}
    assert final.value(name("J4"), JDG.justification) == JDG.SameMappedCode

    assert frozenset({"H1-ALG-PCN", "H2O-ALG-PCN"}) in entry_keys(build(engine, "everyday", "E5"), "allergies")
    export = entry_keys(build(engine, "export", "E5"), "allergies")
    assert frozenset({"H1-ALG-PCN"}) in export and frozenset({"H2O-ALG-PCN"}) in export

    assert frozenset({"H1-ALG-PCN"}) in entry_keys(build(engine, "everyday", "E13"), "allergies")

    for lens in LENSES:
        after = build(engine, lens, "E14")
        assert frozenset(penicillins) in entry_keys(after, "allergies"), lens
        assert counts(after, "J21"), lens


# P2
@engines
def test_a_record_revised_between_two_exports_gets_a_new_version_and_a_revision_after_its_first_and_the_new_version_is_current(engine):
    after = pod("E6")
    b = build(engine, "everyday", "E6")
    for record in ("H1-ALG-LATEX", "H1-ALG-SULFA"):
        assert versions_of(after, record) == {f"{record} v1", f"{record} v2"}
        assert (name(f"{record} r2"), PROV.wasRevisionOf, name(f"{record} r1")) in after
        assert current_versions(b, record) == {f"{record} v2"}


# P3
@engines
def test_a_condition_resolved_at_its_source_shows_resolved(engine):
    at_e6 = build(engine, "everyday", "E6")
    assert current_versions(at_e6, "H1-CON-BRONCH") == {"H1-CON-BRONCH v2"}
    pairs = entries(at_e6.views["conditions"])[entry_holding(at_e6, "conditions", "H1-CON-BRONCH")]
    assert values(pairs, HEALTH.status) == {string("resolved")}
    assert values(pairs, CLINICAL.abatementDate) == {date("2026-09-20")}

    at_e14 = build(engine, "everyday", "E14")
    alone = frozenset({"H1-CON-BRONCH"})
    assert alone in entry_keys(at_e14, "conditions")
    assert values(entries(at_e14.views["conditions"])[alone], HEALTH.status) == {string("resolved")}


# P4
@engines
@lenses
@pytest.mark.parametrize("event", FROM_E5)
def test_where_hospitals_disagree_on_criticality_the_entry_shows_the_most_severe_and_the_disagreement_is_listed(engine, lens, event):
    b = build(engine, lens, event)
    key = entry_holding(b, "allergies", "H1-ALG-SULFA")
    assert values(entries(b.views["allergies"])[key], CLINICAL.criticality) == {string("high")}
    assert key in listed_entries(b, "members disagree on criticality")


# P5
@engines
def test_a_record_missing_from_a_later_export_stays_in_the_view_from_its_last_version(engine):
    assert not names(added_graph("E15"), name("H1-ALG-LATEX"))
    b = build(engine, "everyday", "E15")
    assert current_versions(b, "H1-ALG-LATEX") == {"H1-ALG-LATEX v2"}
    assert frozenset({"H1-ALG-LATEX"}) in entry_keys(b, "allergies")


# P6
@engines
@lenses
@pytest.mark.parametrize("event", ("E6", "E15"))
def test_an_allergy_entered_in_error_at_its_source_is_left_out_of_every_view_and_stays_in_the_pod(engine, lens, event):
    assert "H1-ALG-CODEINE" not in members_shown(build(engine, lens, event))
    final = pod("E15")
    assert (name("H1-ALG-CODEINE"), RDF.type, HEALTH.AllergyRecord) in final
    assert versions_of(final, "H1-ALG-CODEINE") == {"H1-ALG-CODEINE v1", "H1-ALG-CODEINE v2"}


# P7
@engines
def test_one_flu_shot_at_two_hospitals_is_one_entry(engine):
    b = build(engine, "everyday", "E5")
    assert entry_keys(b, "immunizations") == {frozenset({"H1-IMM-FLU25", "H2O-IMM-FLU25"})}


# P8
@engines
def test_every_profile_an_about_makes_the_subjects_makes_the_records_naming_it_hers_and_the_patient_view_lists_the_profiles_and_no_name(engine):
    b = build(engine, "everyday", "E12")
    profiles = {name(h) for h in ("H1-PAT", "H2O-PAT", "H2F-PAT")}
    naming = [
        record
        for record, version in b.state.subject_objects(PAV.hasCurrentVersion)
        if b.state.value(version, REC.patient) in profiles
    ]
    assert naming
    for record in naming:
        assert (record, REC.subject, name("S")) in b.state, handle(record)

    patients = entries(b.views["patient-profile"])
    assert set(patients) == {frozenset({"H1-PAT", "H2O-PAT", "H1P-PAT", "H2F-PAT"})}
    for pairs in patients.values():
        assert {p for p, _ in pairs} <= {RDF.type, MERGED_FROM}

    assert entries(build(engine, "everyday", "E1").views["patient-profile"]) == {}


# P9
def test_importing_an_identical_export_again_writes_nothing_not_even_an_import():
    assert adds("E7") == []
    assert set(files_through("E7")) == set(files_through("E6"))


# P10
@engines
def test_one_hospital_moving_server_names_one_allergy_twice_as_two_records_and_one_entry(engine):
    old = recomputed.record_name([LARKSPUR_OLD, "AllergyIntolerance", "al-8237462"])
    new = recomputed.record_name([LARKSPUR_NEW, "AllergyIntolerance", "lv-alg-102"])
    assert str(name("H2O-ALG-SULFA")) == old
    assert str(name("H2F-ALG-SULFA")) == new
    assert old != new

    b = build(engine, "everyday", "E13")
    assert {"H2O-ALG-SULFA", "H2F-ALG-SULFA"} <= entry_holding(b, "allergies", "H2O-ALG-SULFA")
    assert {"H2O-ALG-PCN", "H2F-ALG-PCN"} <= entry_holding(b, "allergies", "H2O-ALG-PCN")


# P11
@engines
@lenses
@pytest.mark.parametrize("event", ("E8", "E9", "E10", "E12"))
def test_a_patients_different_keeps_apart_a_pair_a_machine_judged_the_same_under_both_lenses(engine, lens, event):
    b = build(engine, lens, event)
    assert entry_holding(b, "procedures", "H1-PROC-COLO") != entry_holding(b, "procedures", "H2O-PROC-COLO")
    assert counts(b, "J7")
    assert not currently_same(b, "H1-PROC-COLO", "H2O-PROC-COLO")


# P12
@engines
def test_a_group_joined_through_two_kinds_of_machine_sameness_is_one_entry_listed_for_review_and_under_export_the_mapped_code_does_not_count(engine):
    flu = frozenset({"H1-IMM-FLU25", "H2O-IMM-FLU25", "H2F-IMM-FLU25"})
    everyday = build(engine, "everyday", "E13")
    assert entry_keys(everyday, "immunizations") == {flu}
    assert listed_entries(everyday, "joined through two kinds of machine sameness") == {flu}

    export = build(engine, "export", "E13")
    assert entry_keys(export, "immunizations") == {
        frozenset({"H1-IMM-FLU25", "H2O-IMM-FLU25"}),
        frozenset({"H2F-IMM-FLU25"}),
    }
    assert listed_entries(export, "joined through two kinds of machine sameness") == set()
    assert not counts(export, "J17")


# P13
@engines
def test_a_retracted_same_stops_joining_its_records_and_nothing_replaces_it(engine):
    b = build(engine, "everyday", "E14")
    assert entry_holding(b, "conditions", "H1-CON-BRONCH") != entry_holding(b, "conditions", "H2O-CON-ASTHMA")
    assert not counts(b, "J10")
    assert is_judgment(pod("E14"), "J20")
    assert pod("E14").value(name("J20"), PROV.hadMember) is None


# P14
@engines
def test_a_machine_judgment_stops_counting_under_everyday_when_a_reference_version_it_used_is_replaced_and_nothing_is_written_but_the_new_version(engine):
    added = adds("E9")
    assert len(added) == 1
    assert names(pod_file(ALEX, added[0]), name("RS-XWALK-2027-01"))

    assert is_judgment(pod("E9"), "J4")
    assert not counts(build(engine, "everyday", "E9"), "J4")
    for lens in LENSES:
        b = build(engine, lens, "E9")
        assert entry_holding(b, "allergies", "H1-ALG-PCN") != entry_holding(b, "allergies", "H2O-ALG-PCN"), lens


# P15
@engines
@lenses
def test_a_judgment_whose_members_changed_since_it_was_made_still_counts_and_is_listed_until_it_is_superseded(engine, lens):
    for event in ("E6", "E7"):
        b = build(engine, lens, event)
        assert counts(b, "J3"), event
        assert listed_judgments(b) == {"J3"}, event
    b = build(engine, lens, "E8")
    assert not counts(b, "J3")
    assert listed_judgments(b) == set()


# P16
@engines
def test_an_entry_the_patient_adds_is_the_subjects_without_any_about_and_supplies_its_criticality_and_no_status(engine):
    final = pod("E15")
    assert final.value(name("APP-ALG-PEANUT v1"), REC.patient) == name("S")
    abouts = set(final.subjects(JDG.verdict, JDG.About))
    assert not any((j, PROV.hadMember, name("APP-ALG-PEANUT")) in final for j in abouts)

    b = build(engine, "everyday", "E3")
    assert (name("APP-ALG-PEANUT"), REC.subject, name("S")) in b.state
    pairs = entries(b.views["allergies"])[frozenset({"APP-ALG-PEANUT"})]
    assert values(pairs, CLINICAL.criticality) == {string("high")}
    assert values(pairs, CLINICAL.status) == set()
    assert values(pairs, REC.statusFrom) == set()


# P17
def test_a_server_version_that_changes_while_its_content_does_not_writes_nothing():
    record = name("H1-CON-HTN")
    for event in ("E6", "E15"):
        added = added_graph(event)
        assert not list(added.subjects(PROV.specializationOf, record)), event
        assert not list(added.subjects(REC.revisionOf, record)), event
    final = pod("E15")
    assert versions_of(final, "H1-CON-HTN") == {"H1-CON-HTN v1"}
    assert revisions_of(final, "H1-CON-HTN") == {"H1-CON-HTN r1"}


# P18
@engines
def test_a_change_undone_at_its_source_reuses_its_first_version(engine):
    final = pod("E15")
    assert versions_of(final, "H1-CON-BACK") == {"H1-CON-BACK v1", "H1-CON-BACK v2"}
    assert revisions_of(final, "H1-CON-BACK") == {"H1-CON-BACK r1", "H1-CON-BACK r2", "H1-CON-BACK r3"}
    assert final.value(name("H1-CON-BACK r3"), REC.version) == name("H1-CON-BACK v1")
    assert (name("H1-CON-BACK r3"), PROV.wasRevisionOf, name("H1-CON-BACK r2")) in final
    for revision, event in (("r1", "E2"), ("r2", "E6"), ("r3", "E15")):
        assert arrival(final, f"H1-CON-BACK {revision}") == ARRIVED[event], revision

    b = build(engine, "everyday", "E15")
    pairs = entries(b.views["conditions"])[entry_holding(b, "conditions", "H1-CON-BACK")]
    assert values(pairs, HEALTH.status) == {string("active")}
    assert values(pairs, CLINICAL.abatementDate) == set()


# P19
@engines
def test_a_resource_file_with_no_clinical_record_entry_is_named_from_its_document_with_a_finding_and_is_in_no_view(engine):
    document = EXAMPLE / "downloads" / "x-e6" / "apple_health_export" / "clinical-records" / "Immunization-imm-tdap-2026.json"
    digest = recomputed.ni_name(document.read_bytes())
    assert digest == str(name("D-U-IMM-TDAP r1"))
    assert pod("E15").value(name("U-IMM-TDAP v1"), REC.patient) is None

    findings = Graph().parse(EXAMPLE / "conversions" / "e6" / "Immunization-imm-tdap-2026" / "findings.ttl", format="turtle")
    assert "Patient/pat-conformance-1" in {str(o) for o in findings.objects(None, SH.value)}

    for event in BUILT:
        for lens in LENSES:
            assert "U-IMM-TDAP" not in members_shown(build(engine, lens, event)), (event, lens)
    for event in ("E10", "E12", "E15"):
        assert not names(added_graph(event), name("U-IMM-TDAP")), event


# P20
@engines
@lenses
def test_a_different_pair_still_joined_through_a_third_record_is_one_entry_listed_for_review_until_it_is_separated(engine, lens):
    colonoscopies = frozenset({"H1-PROC-COLO", "H2O-PROC-COLO", "H2F-PROC-COLO"})
    at_e13 = build(engine, lens, "E13")
    assert colonoscopies in entry_keys(at_e13, "procedures")
    first, second = sorted(("H1-PROC-COLO", "H2O-PROC-COLO"), key=lambda h: str(name(h)))
    assert listed_pairs(at_e13) == {(first, second, colonoscopies)}

    at_e14 = build(engine, lens, "E14")
    keys = entry_keys(at_e14, "procedures")
    assert frozenset({"H1-PROC-COLO"}) in keys
    assert frozenset({"H2O-PROC-COLO", "H2F-PROC-COLO"}) in keys
    assert listed_pairs(at_e14) == set()


# P21
@engines
def test_a_persons_and_a_machines_same_sharing_two_records_make_one_group_of_three(engine):
    b = build(engine, "everyday", "E13")
    assert frozenset({"H1-ALG-SULFA", "H2O-ALG-SULFA", "H2F-ALG-SULFA"}) in entry_keys(b, "allergies")
    assert counts(b, "J9")
    assert counts(b, "J13")


# P22
@engines
def test_a_persons_mistaken_same_hides_a_status_until_a_newer_arrival_and_a_retraction_undo_it(engine):
    def entry(event, key):
        conditions = entries(build(engine, "everyday", event).views["conditions"])
        assert frozenset(key) in conditions, (event, key)
        return conditions[frozenset(key)]

    for event in ("E8", "E12"):
        pairs = entry(event, {"H1-CON-BRONCH", "H2O-CON-ASTHMA"})
        assert values(pairs, HEALTH.status) == {string("resolved")}, event
        assert values(pairs, REC.statusFrom) == {handle_iri("H1-CON-BRONCH")}, event

    pairs = entry("E13", {"H1-CON-BRONCH", "H2O-CON-ASTHMA", "H2F-CON-ASTHMA"})
    assert values(pairs, HEALTH.status) == {string("active")}
    assert values(pairs, REC.statusFrom) == {handle_iri("H2F-CON-ASTHMA")}

    assert values(entry("E14", {"H2O-CON-ASTHMA", "H2F-CON-ASTHMA"}), HEALTH.status) == {string("active")}
    assert values(entry("E14", {"H1-CON-BRONCH"}), HEALTH.status) == {string("resolved")}


# P23
@engines
def test_an_unchanged_record_arriving_again_keeps_the_arrival_it_had(engine):
    final = pod("E15")
    assert revisions_of(final, "H1-ALG-PCN") == {"H1-ALG-PCN r1"}
    assert arrival(final, "H1-ALG-PCN r1") == ARRIVED["E2"]

    b = build(engine, "everyday", "E6")
    pairs = entries(b.views["allergies"])[frozenset({"H1-ALG-PCN", "H2O-ALG-PCN"})]
    assert values(pairs, REC.latestMember) == {handle_iri("H2O-ALG-PCN")}


# P24
@engines
@lenses
def test_a_family_members_records_imported_as_the_patients_are_in_her_views_until_she_retracts_the_about_and_nothing_is_deleted(engine, lens):
    for event in ("E10", "E13"):
        b = build(engine, lens, event)
        assert "H1P-PAT" in {m for key in entry_keys(b, "patient-profile") for m in key}, event
        assert frozenset({"H1P-ALG-AMOX"}) in entry_keys(b, "allergies"), event
        assert frozenset({"H1P-CON-OTITIS"}) in entry_keys(b, "conditions"), event
        assert frozenset({"H1P-CON-ECZEMA"}) in entry_keys(b, "conditions"), event

    for event in ("E14", "E15"):
        b = build(engine, lens, event)
        assert not set(SAM) & members_shown(b), event
        assert entry_keys(b, "patient-profile") == {frozenset({"H1-PAT", "H2O-PAT", "H2F-PAT"})}, event
        assert not counts(b, "J22"), event

    final = pod("E15")
    assert is_judgment(final, "J22")
    later = [f for event in ("E12", "E13", "E14", "E15") for f in adds(event)]
    for relative in adds("E10"):
        assert (POD / relative).is_file(), relative
        assert relative not in later, relative
    import_e10 = name("I-E10")
    for judgment in final.subjects(RDF.type, JDG.Judgment):
        assert import_e10 not in set(final.objects(judgment, None)), handle(judgment)


# P25
@engines
def test_a_record_the_patient_judges_erroneous_leaves_every_view_stays_in_the_pod_and_an_unchanged_resend_writes_nothing(engine):
    assert frozenset({"H1-PROC-ECHO"}) in entry_keys(build(engine, "everyday", "E13"), "procedures")
    for event in ("E14", "E15"):
        for lens in LENSES:
            assert "H1-PROC-ECHO" not in members_shown(build(engine, lens, event)), (event, lens)

    final = pod("E15")
    assert (name("H1-PROC-ECHO"), RDF.type, CLINICAL.Procedure) in final
    assert versions_of(final, "H1-PROC-ECHO") == {"H1-PROC-ECHO v1"}
    assert revisions_of(final, "H1-PROC-ECHO") == {"H1-PROC-ECHO r1"}
    assert not names(added_graph("E15"), name("H1-PROC-ECHO"))
    assert final.value(name("J24"), JDG.verdict) == JDG.Erroneous
    assert set(final.objects(name("J24"), PROV.hadMember)) == {name("H1-PROC-ECHO")}


def expected_view(kind):
    return entries(Graph().parse(EXPECTED / f"{kind}.ttl", format="turtle"))


def actual_view(kind, source):
    if source == "committed":
        relative = ALEX.view_files[kind]
        return entries(Graph().parse(POD / relative, format="turtle", publicID=POD_BASE + relative))
    return entries(build(source, "everyday", "E15").views[kind])


@pytest.mark.parametrize("source", ("committed",) + ENGINES)
@pytest.mark.parametrize("kind", tuple(ALEX.view_files))
def test_each_final_view_equals_its_expected_view(kind, source):
    differences = view_differences(expected_view(kind), actual_view(kind, source))
    assert not differences, "\n".join(differences)


HANDLE = re.compile(
    r'"((?:H1P?|H2[OF]|U|APP)-[A-Z0-9]+(?:-[A-Z0-9]+)?(?: [vr]\d+)?|D-[A-Z0-9-]+ r\d+|J\d+|RS-[A-Z]+-[0-9.-]+|I-E\d+|S)"'
)


def test_every_handle_an_expected_file_or_planted_case_names_names_something_in_the_pod():
    named = set(HANDLE.findall(Path(__file__).read_text(encoding="utf-8")))
    for path in EXPECTED.glob("*.ttl"):
        for members, entry in expected_view(path.stem).items():
            named.update(members)
            named.update(str(o)[len(HANDLE_NS):] for _, o in entry if str(o).startswith(HANDLE_NS))
    missing = sorted(named - set(handles()))
    assert not missing, f"handles that name nothing in the pod: {missing}"


@engines
def test_the_state_a_build_gives_is_the_pod_with_its_derived_state_and_none_of_the_files_built_from_them(engine):
    b = build(engine, "everyday", "E15")
    assert (None, MERGED_FROM, None) not in b.state
    assert (None, REC.counts, None) in b.state
