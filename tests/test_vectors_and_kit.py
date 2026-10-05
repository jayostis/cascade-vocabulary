"""The rule vectors and the conformance kit are well formed. Whether a runtime passes them is the runtime's to show: CI
runs the reference runtime over this checkout."""

import base64
import hashlib
import json
import re
from datetime import datetime

import pytest
from rdflib import Graph, URIRef, Variable
from rdflib.collection import Collection
from rdflib.namespace import RDF
from rdflib.plugins.sparql.algebra import traverse
from rdflib.plugins.sparql.parser import parseQuery

from contract import QUERIES, REC, ROOT
from engines import parsed
from manifests import MF, entries

RUNTIME = ROOT / "runtime"
KIT = ROOT / "conformance" / "alex-rivera"
VECTORS = RUNTIME / "vectors" / "manifest.ttl"
CASES = KIT / "cases" / "manifest.ttl"
RULES = RUNTIME / "rules.md"
RULES_WITH_NO_VECTOR = {"N8", "W1"}
MANIFESTS = pytest.mark.parametrize("manifest", [VECTORS, CASES], ids=["vectors", "cases"])
STORIES = sorted([*RUNTIME.glob("vectors/*/story.json"), KIT / "story.json"])


def steps(story):
    return json.loads(story.read_text(encoding="utf-8"))["steps"]


@MANIFESTS
def test_the_manifest_is_a_w3c_test_manifest_whose_entries_the_reader_reads(manifest):
    graph = Graph().parse(manifest, format="turtle")
    [the_manifest] = graph.subjects(RDF.type, MF.Manifest)
    [listed] = graph.objects(the_manifest, MF.entries)
    listed = list(Collection(graph, listed))
    assert listed
    for entry in listed:
        assert graph.value(entry, MF.name) is not None, entry
        assert graph.value(entry, MF.action) is not None, entry
        assert graph.value(entry, MF.result) is not None, entry
    assert [(URIRef(e.iri), e.name) for e in entries(manifest)] == [
        (entry, str(graph.value(entry, MF.name))) for entry in listed]


@MANIFESTS
def test_every_entry_is_a_replay_test_naming_a_story_a_step_in_it_a_lens_file_a_query_and_a_result(manifest):
    for entry in entries(manifest):
        assert REC.ReplayTest in entry.types, entry.name
        assert entry.step in [step["name"] for step in steps(entry.story)], entry.name
        assert entry.lens.is_file() and entry.query.is_file() and entry.result.is_file(), entry.name


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


def test_every_vector_is_named_by_a_rule_and_every_rule_names_a_vector_or_says_why_none_can():
    names = {entry.name for entry in entries(VECTORS)}
    by_rule = {rule: {name for name in names if f"`{name}`" in text} for rule, text in rules().items()}
    assert names - set().union(*by_rule.values()) == set()
    assert {rule for rule, named in by_rule.items() if not named} == RULES_WITH_NO_VECTOR
    for rule in RULES_WITH_NO_VECTOR:
        assert rules()[rule].strip(), rule


def test_each_planted_case_is_named_by_an_entry():
    named = {int(match.group(1)) for entry in entries(CASES) for match in [re.match(r"p(\d\d)-", entry.name)] if match}
    assert named == set(range(1, 26))


@pytest.mark.parametrize("story", STORIES, ids=lambda story: story.parent.name)
def test_a_storys_steps_are_in_time_order(story):
    times = [datetime.fromisoformat(step["when"]) for step in steps(story)]
    assert times == sorted(times)


def test_no_query_of_a_vector_or_a_case_selects_as_a_variable_its_pattern_already_binds():
    clashes = {}
    for path in sorted([*RUNTIME.glob("vectors/*/*.rq"), *KIT.glob("cases/*.rq")]):
        query = parseQuery(path.read_text(encoding="utf-8"))[1]
        bound = set()
        traverse(query.where, visitPost=lambda node: bound.add(node) if isinstance(node, Variable) else None)
        aliases = {item["evar"] for item in query.get("projection") or [] if "evar" in item}
        if aliases & bound:
            clashes[path.relative_to(ROOT).as_posix()] = sorted(aliases & bound)
    assert clashes == {}


def ni_name(octets):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode().rstrip("=")


def test_every_rule_names_a_comparison_whose_bytes_hash_to_its_hash_but_the_one_a_vector_breaks():
    lists = {path.relative_to(ROOT).as_posix(): rows
             for path in sorted([*KIT.glob("scripted-input/references/*.ttl"),
                                 *RUNTIME.glob("vectors/*/scripted-input/references/*.ttl")])
             for rows in [parsed(path)] if (None, RDF.type, REC.MatcherRule) in rows}
    assert len(lists) == 5
    mismatched = set()
    for path, rows in lists.items():
        for row in rows.subjects(RDF.type, REC.MatcherRule):
            query = str(rows.value(row, REC.query))
            assert query.startswith("matcher/"), path
            if ni_name((QUERIES / query).read_bytes()) != str(rows.value(row, REC.queryHash)):
                mismatched.add((path.split("/")[2], query))
    assert mismatched == {("refusals", "matcher/same-code.rq")}
