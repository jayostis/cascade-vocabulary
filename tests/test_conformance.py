"""The conformance kit, as runtime/rules.md's "The conformance kit" says a runtime passes it, run on the Python: each case
entry passes, each final view equals expected/, and each name follows its rule from the run's own inputs."""

import json
import re
import subprocess
import sys
import uuid
from collections import defaultdict

import pytest
from rdflib import BNode, Graph, URIRef, Variable
from rdflib.compare import isomorphic
from rdflib.namespace import RDF
from rdflib.plugins.sparql.algebra import traverse
from rdflib.plugins.sparql.parser import parseQuery

import recomputed
from alex_rivera import (ADDRESS, BRIDGE, INPUT, JDG, KIT, MATCHER, PROV, REC, STORY, EVERY_JUDGMENT, document,
                         handle, handles, handles_by_name, saved_output, source_name, sources, step)
from cascade_pod import manifest, names, story, store, vocabulary
from cascade_pod.pod import LAYOUT, NOT_RDF, stem
from examples import pod_file

CASES = KIT / "cases"
ENTRIES = manifest.entries(CASES / "manifest.ttl")
ENGINE = "oxigraph"
MERGED_FROM = URIRef("https://ns.cascadeprotocol.org/core/v1#mergedFrom")
ENTRY = "urn:cascade:entry:"
NAMESPACES = ("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "http://www.w3.org/2000/01/rdf-schema#",
              "http://www.w3.org/2001/XMLSchema#", "http://www.w3.org/ns/prov#", "http://purl.org/pav/",
              "http://purl.org/nanopub/x/", "https://ns.cascadeprotocol.org/")


@pytest.fixture(scope="session")
def replaying(alex, tmp_path_factory):
    return manifest.Run(ENGINE, tmp_path_factory.mktemp("cases"), {KIT / "story.json": alex})


def test_every_entry_names_the_story_a_step_in_it_a_lens_a_query_and_a_result():
    steps = story.steps(KIT / "story.json")
    for entry in ENTRIES:
        assert (entry.type, entry.story) == (str(REC.ReplayTest), KIT / "story.json"), entry.name
        assert entry.step in steps and entry.lens.is_file(), entry.name
        assert entry.query.is_file() and entry.result.is_file(), entry.name


def test_the_kit_holds_data_only_and_its_steps_are_in_time_order():
    assert [path for path in KIT.rglob("*.py")] == []
    times = [names.in_utc(s["when"]) for s in STORY["steps"]]
    assert times == sorted(times)


def test_each_planted_case_is_named_by_an_entry():
    named = {int(match.group(1)) for entry in ENTRIES for match in [re.match(r"p(\d\d)-", entry.name)] if match}
    assert named == set(range(1, 26))


def inputs_name():
    """Every IRI the kit's inputs give without a replay."""
    found = {str(term) for term in handles().values()}
    found |= {str(document(path.relative_to(KIT))) for path in (INPUT / "downloads").rglob("*") if path.is_file()}
    for path in [*INPUT.glob("bridge/*/*/graph.ttl"), *INPUT.glob("judgments/*.ttl"), *INPUT.glob("references/*.ttl"),
                 *INPUT.glob("entries/*.ttl")]:
        found |= {str(term) for triple in store.parsed(path) for term in triple if isinstance(term, URIRef)}
    return found | {f"urn:cascade:step:{s['name']}" for s in STORY["steps"]} | {story.STEPS_GRAPH, MATCHER}


def iris_in_rows(path):
    return {binding["value"] for row in json.loads(path.read_text(encoding="utf-8"))["results"]["bindings"]
            for binding in row.values() if binding["type"] == "uri"}


def test_no_case_and_no_expected_view_names_a_thing_whose_name_depends_on_a_run():
    named = set()
    for path in CASES.glob("*.srj"):
        named |= iris_in_rows(path)
    for path in CASES.glob("*.rq"):
        named |= set(re.findall(r"<([^<>\s]+)>", path.read_text(encoding="utf-8")))
    for path in (KIT / "expected").glob("*.ttl"):
        named |= {str(term) for triple in store.parsed(path) for term in triple if isinstance(term, URIRef)}
    known = inputs_name()
    assert sorted(i for i in named if i not in known and not i.startswith((*NAMESPACES, ADDRESS))) == []


@pytest.mark.parametrize("entry", [pytest.param(entry, id=entry.name, marks=pytest.mark.xdist_group(
    f"alex-{entry.step}-{manifest.lens_name(entry.lens)}")) for entry in ENTRIES])
def test_the_entry_passes(entry, replaying):
    outcome, why = replaying.outcome(entry)
    assert outcome == manifest.EARL.passed, why


def entries(graph):
    """Each entry of a view, by its members, with what it states, each entry IRI a blank node."""
    found = {}
    for subject in set(graph.subjects(MERGED_FROM, None)):
        members = frozenset(str(m) for m in graph.objects(subject, MERGED_FROM))
        found[members] = {(p, BNode() if str(o).startswith(ENTRY) else o) for p, o in graph.predicate_objects(subject)}
    return found


def differences(expected, found):
    """Each entry, keyed by its members' handles, missing, not wanted, or with the statements it lacks or should not
    have."""
    def key(members):
        return sorted(handles_by_name().get(m, m) for m in members)

    report = []
    for members in sorted(set(expected) | set(found), key=key):
        if members not in found:
            report.append(f"entry {key(members)} is missing")
        elif members not in expected:
            report.append(f"entry {key(members)} should not be there")
        elif expected[members] != found[members]:
            report.append(f"entry {key(members)}:")
            report += [f"  missing {p.n3()} {o.n3()}" for p, o in sorted(expected[members] - found[members], key=str)]
            report += [f"  should not have {p.n3()} {o.n3()}" for p, o in sorted(found[members] - expected[members], key=str)]
    return report


def comparable(triples):
    """A view's entries and what they state, each entry IRI a blank node."""
    graph = Graph()
    entry_nodes = defaultdict(BNode)
    kept = {s for s, p, _ in triples if p == MERGED_FROM}
    for s, p, o in triples:
        if s in kept:
            graph.add(tuple(entry_nodes[t] if str(t).startswith(ENTRY) else t for t in (s, p, o)))
    return graph


def test_each_final_view_equals_its_expected_view(alex):
    held = alex.build(ENGINE, vocabulary.DEFAULT_LENS).store
    report = []
    for path in sorted((KIT / "expected").glob("*.ttl")):
        expected = store.parsed(path)
        found = comparable(held.triples(alex.address + alex.view_files[path.stem]))
        if not isomorphic(expected, found):
            report += [f"{path.stem}:"] + differences(entries(expected), entries(found))
    assert not report, "\n".join(report)


@pytest.fixture(scope="module")
def pod(alex):
    """Every RDF file of the pod that a step wrote, by its path."""
    return {path: pod_file(alex, path) for path in alex.files() if not path.startswith(NOT_RDF)}


@pytest.fixture(scope="module")
def whole(pod):
    graph = Graph()
    for part in pod.values():
        graph += part
    return graph


def activity_of(alex, pod, name):
    """The import or entry session the step wrote, found from the files it wrote."""
    [found] = {s for path in alex.event(name)["adds"] if path in pod for s in pod[path].subjects(RDF.type, PROV.Activity)}
    return found


def test_each_record_has_the_name_its_input_gives(whole):
    from_bridge = {record for graph in saved_output() for record in graph.objects(None, PROV.specializationOf)}
    from_entries = {source_name(row) for row in sources()["records"].values() if "entry" in row}
    assert set(whole.objects(None, REC.revisionOf)) == from_bridge | from_entries
    [peanut] = from_entries
    assert peanut == URIRef(recomputed.record_name([STORY["subject"], step("E3")["when"], "0"]))


def content(graph, name, placeholder):
    return {tuple(URIRef(placeholder + str(t)[len(name):]) if str(t).split("#")[0] == name else t for t in triple)
            for triple in graph}


def test_each_version_and_revision_is_named_from_its_content(pod):
    checked = 0
    for path, graph in pod.items():
        for version in graph.subjects(PROV.specializationOf, None):
            if path.startswith("records/"):
                named, _ = recomputed.versions(recomputed.parsed_ntriples(graph.serialize(format="nt")))
                assert list(named) == [str(version)] == [names.content(content(graph, str(version), names.THIS_VERSION))], path
                checked += 1
        for revision in graph.subjects(RDF.type, REC.Revision):
            assert names.content(content(graph, str(revision), names.THIS_REVISION)) == str(revision), path
            checked += 1
    assert checked == 32 + 33


def test_each_revision_is_generated_by_its_steps_activity_and_follows_an_earlier_revision_of_its_record(alex, pod, whole):
    by_step = {path: event["event"] for event in alex.events for path in event["adds"]}
    for path, graph in pod.items():
        for revision in graph.subjects(RDF.type, REC.Revision):
            assert graph.value(revision, PROV.wasGeneratedBy) == activity_of(alex, pod, by_step[path]), path
            earlier = graph.value(revision, PROV.wasRevisionOf)
            if earlier is not None:
                assert whole.value(earlier, REC.revisionOf) == graph.value(revision, REC.revisionOf), path
                assert (names.in_utc(str(whole.value(earlier, PROV.generatedAtTime)))
                        < names.in_utc(str(graph.value(revision, PROV.generatedAtTime)))), path


def test_each_stored_document_is_named_by_its_bytes_and_described(alex, whole):
    stored = [path for path in alex.files() if path.startswith(NOT_RDF)]
    assert len(stored) == 32
    for path in stored:
        name = URIRef(recomputed.ni_name((alex.pod / path).read_bytes()))
        assert path == LAYOUT.stored_bytes.path(name) and (name, RDF.type, PROV.Entity) in whole, path


def test_each_matcher_judgment_is_named_from_its_members_and_what_it_used(whole):
    judged = sorted(whole.subjects(PROV.wasAttributedTo, URIRef(MATCHER)))
    assert [handle(j) for j in judged] and len(judged) == sum(1 for j in EVERY_JUDGMENT.values() if j.author == "matcher")
    for judgment in judged:
        assert judgment == URIRef(recomputed.record_name([
            MATCHER, str(whole.value(judgment, JDG.justification)),
            *sorted(map(str, whole.objects(judgment, PROV.hadMember))), *sorted(map(str, whole.objects(judgment, PROV.used)))]))


def test_each_import_and_session_is_a_new_version_4_uuid(alex, pod):
    made = {activity_of(alex, pod, s["name"]) for s in STORY["steps"] if ("import" in s or "entry" in s)
            and any(path in pod for path in alex.event(s["name"])["adds"])}
    assert len(made) == 7
    given = "".join(path.read_text(encoding="utf-8") for path in KIT.rglob("*")
                    if path.is_file() and path.suffix in (".json", ".ttl", ".rq", ".srj", ".xml"))
    for activity in made:
        assert str(activity).startswith("urn:uuid:") and uuid.UUID(str(activity)[9:]).version == 4, activity
        assert str(activity)[9:] not in given, activity


def test_every_file_is_at_the_path_its_things_name_gives(pod):
    for path, graph in pod.items():
        if path.startswith(("subject/", "records/", "provenance/", "judgments/", "references/")):
            things = {str(s).split("#")[0] for s in graph.subjects() if str(s).startswith(("urn:uuid:", "ni:"))}
            [named] = [stem(thing) for thing in things if path.endswith(f"/{stem(thing)}.ttl")] or [None]
            assert path == f"{path.rsplit('/', 2)[0]}/{(named or '')[:2]}/{named}.ttl", path


def test_each_saved_bridge_output_is_in_the_pod_less_its_arrivals_with_the_import_its_step_wrote(alex, pod, whole):
    """A9, A10 and A11: a kept document is described as the Bridge described it, its import is the one its step wrote,
    and each revision holds its arrival's statements; a document not kept is named nowhere."""
    stored = {path.rsplit("/", 1)[-1] for path in alex.files() if path.startswith(NOT_RDF)}
    named = {str(term) for triple in whole for term in triple}
    for imports in (s for s in STORY["steps"] if "import" in s):
        for folder in sorted((KIT / imports["import"]["converted"]).iterdir()):
            graph = store.parsed(folder / "graph.ttl")
            [doc] = graph.subjects(RDF.type, PROV.Entity)
            if stem(str(doc)) not in stored:
                assert str(doc) not in named, folder
                continue
            this_import, [activity] = activity_of(alex, pod, imports["name"]), graph.subjects(PROV.used, doc)
            expected, found = Graph(), Graph()
            for s, p, o in graph:
                if graph.value(s, BRIDGE.arrivedAs) is None:
                    expected.add((this_import if s == activity else s, p, o))
            for s in {s for s in expected.subjects() if not isinstance(s, BNode)}:
                for p, o in whole.predicate_objects(s):
                    if not (s == this_import and p == PROV.used and o != doc):
                        found.add((s, p, o))
                        found += closure(whole, o)
            assert isomorphic(expected, found), folder
            for arrival in graph.subjects(BRIDGE.arrivedAs, None):
                statements = {(p, o) for p, o in graph.predicate_objects(arrival)
                              if p not in (BRIDGE.arrivedAs, PROV.wasGeneratedBy)}
                [revision] = [r for r in whole.subjects(REC.version, graph.value(arrival, BRIDGE.arrivedAs))
                              if (r, PROV.wasDerivedFrom, doc) in whole]
                assert statements <= set(whole.predicate_objects(revision)), folder


def closure(graph, node):
    found = Graph()
    if isinstance(node, BNode):
        for p, o in graph.predicate_objects(node):
            found.add((node, p, o))
            found += closure(graph, o)
    return found


def test_each_scripted_judgment_names_only_what_the_pod_holds_at_its_step(alex):
    steps = [s["name"] for s in STORY["steps"]]
    for scripted in (s for s in STORY["steps"] if "judgment" in s):
        held = alex.story_store(ENGINE, steps[steps.index(scripted["name"]) - 1]).triples()
        things = {s for s, _, _ in held} | {o for _, p, o in held if p == REC.patient}
        judgment = store.parsed(KIT / scripted["judgment"])
        named = {o for p in (JDG.subject, PROV.hadMember, PROV.used, NPX_SUPERSEDES, NPX_RETRACTS)
                 for o in judgment.objects(None, p)}
        assert named and named <= things, (scripted["name"], sorted(map(str, named - things)))


NPX_SUPERSEDES = URIRef("http://purl.org/nanopub/x/supersedes")
NPX_RETRACTS = URIRef("http://purl.org/nanopub/x/retracts")


def test_no_case_selects_as_a_variable_its_pattern_already_binds():
    clashes = {}
    for path in sorted(CASES.glob("*.rq")):
        query = parseQuery(path.read_text(encoding="utf-8"))[1]
        bound = set()
        traverse(query.where, visitPost=lambda node: bound.add(node) if isinstance(node, Variable) else None)
        aliases = {item["evar"] for item in query.get("projection") or [] if "evar" in item}
        if aliases & bound:
            clashes[path.name] = sorted(aliases & bound)
    assert clashes == {}


def test_the_kit_has_one_title_however_its_path_is_written():
    assert vocabulary.title(KIT.parent / ".." / KIT.parent.name / KIT.name) == vocabulary.title(KIT) is not None


def test_a_replay_out_that_is_a_file_is_refused_in_one_line_without_a_traceback(tmp_path):
    out = tmp_path / "a-file"
    out.write_text("kept", encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "cascade_pod", "replay", str(KIT), "--out", str(out)],
                            capture_output=True, text=True, cwd=vocabulary.ROOT)
    assert result.returncode == 2
    assert result.stderr.startswith("cascade_pod replay: ") and "Traceback" not in result.stderr, result.stderr
    assert out.read_text(encoding="utf-8") == "kept"
