import json
import re

import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF

from cascade_pod import manifest, story
from examples import FIXTURES, ROOT

RUNTIME = ROOT / "runtime"
MANIFEST = RUNTIME / "vectors" / "manifest.ttl"
RULES = RUNTIME / "rules.md"
RULES_WITH_NO_VECTOR = {"N8", "W1"}

MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
EARL = Namespace("http://www.w3.org/ns/earl#")

ENTRIES = manifest.entries(MANIFEST)


@pytest.fixture(scope="session")
def replaying(tmp_path_factory):
    """One engine replays each story once: a vector shows what a runtime writes, which no engine changes, and the
    fixtures show where the engines could disagree."""
    return manifest.Run("oxigraph", tmp_path_factory.mktemp("replays"))


def outcomes(earl):
    """Each assertion's test and outcome."""
    return [(earl.value(assertion, EARL.test), earl.value(earl.value(assertion, EARL.result), EARL.outcome))
            for assertion in earl.subjects(RDF.type, EARL.Assertion)]


def rules():
    """The text of each rule in rules.md, by the ID its heading begins with."""
    found, current = {}, None
    for line in RULES.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"#+\s+(?:([A-Z]\d+)\b)?", line)
        if heading:
            current = heading.group(1)
            if current:
                found[current] = ""
        elif current:
            found[current] += line + "\n"
    return found


def entries_named_in(text):
    return {entry.name for entry in ENTRIES if f"`{entry.name}`" in text}


def test_the_manifest_is_a_w3c_test_manifest_whose_entries_the_runner_reads():
    assert MANIFEST.is_file(), f"{MANIFEST} does not exist"
    graph = Graph().parse(MANIFEST, format="turtle")
    [the_manifest] = graph.subjects(RDF.type, MF.Manifest)
    [listed] = graph.objects(the_manifest, MF.entries)
    listed = list(Collection(graph, listed))
    assert listed
    for entry in listed:
        assert graph.value(entry, MF.name) is not None, entry
        assert graph.value(entry, MF.action) is not None, entry
        assert graph.value(entry, MF.result) is not None, entry
    assert [(URIRef(e.iri), e.name) for e in ENTRIES] == [(entry, str(graph.value(entry, MF.name))) for entry in listed]


def test_every_entry_names_a_story_a_step_in_it_a_lens_file_a_query_and_a_result():
    assert ENTRIES
    for entry in ENTRIES:
        assert entry.story.exists(), entry.name
        assert entry.step in story.steps(entry.story), entry.name
        assert entry.lens.is_file(), entry.name
        assert entry.query, entry.name
        assert entry.result is not None, entry.name


def test_every_entry_is_named_by_a_rule_and_every_rule_names_an_entry_or_says_why_none_can():
    assert RULES.is_file(), f"{RULES} does not exist"
    by_rule = rules()
    assert by_rule
    named = set().union(*(entries_named_in(text) for text in by_rule.values()))
    assert {entry.name for entry in ENTRIES} - named == set()
    assert {rule for rule, text in by_rule.items() if not entries_named_in(text)} == RULES_WITH_NO_VECTOR
    for rule in RULES_WITH_NO_VECTOR:
        assert by_rule[rule].strip(), rule


def test_the_earl_report_has_one_passed_assertion_per_entry_and_no_other():
    [fixture] = [fixture for fixture in FIXTURES if fixture.name == "a-change-undone-reuses-its-first-version"]
    found = outcomes(manifest.run(fixture.manifest, "oxigraph"))
    assert sorted(str(test) for test, _ in found) == sorted(entry.iri for entry in manifest.entries(fixture.manifest))
    assert {outcome for _, outcome in found} == {EARL.passed}


@pytest.mark.parametrize("entry", [pytest.param(entry, id=entry.name, marks=pytest.mark.xdist_group(entry.story.parent.name))
                                   for entry in ENTRIES])
def test_the_entry_passes(entry, replaying):
    outcome, why = replaying.outcome(entry)
    assert outcome == EARL.passed, why


def test_a_story_whose_first_step_is_a_matcher_step_is_rejected_naming_the_step(tmp_path):
    story_file = tmp_path / "story.json"
    story_file.write_text(json.dumps({"address": "https://pod.example/", "subject": "urn:uuid:0", "steps": [
        {"name": "match-first", "when": "2026-05-01T09:00:00Z", "matcher": {}}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="match-first"):
        story.Replay(story_file, tmp_path / "replayed").run()
