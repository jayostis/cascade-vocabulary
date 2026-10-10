"""Every feature file is Gherkin a standard parser reads, every step it takes is one runtime/steps.md lists, and the
scripted input it names is whole."""

import base64
import hashlib
import re
from functools import cache

import pytest
from gherkin.parser import Parser
from gherkin.pickles.compiler import Compiler

from rdflib import Variable
from rdflib.namespace import RDF
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

from contract import KITS, PROV, QUERIES, REC, ROOT
from engines import parsed

FEATURES = sorted([*ROOT.glob("runtime/*.feature"), *ROOT.glob("conformance/*/*.feature")])
TIME = re.compile(r" on (\d{4}-\d{2}-\d{2}) at (\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)(?: \(|$)")
PREFIXES = "".join(f"PREFIX {prefix}: <{base}>\n" for prefix, base in {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#", "prov": "http://www.w3.org/ns/prov#", "pav": "http://purl.org/pav/",
    "npx": "http://purl.org/nanopub/x/", "bridge": "https://ns.cascadeprotocol.org/bridge/v1-draft#",
    "rec": "https://ns.cascadeprotocol.org/records/v1-draft#",
    "jdg": "https://ns.cascadeprotocol.org/judgments/v1-draft#", "health": "https://ns.cascadeprotocol.org/health/v1#",
    "clinical": "https://ns.cascadeprotocol.org/clinical/v1#", "cascade": "https://ns.cascadeprotocol.org/core/v1#",
}.items())


def documents():
    """Each feature file, parsed, and compiled to its pickles."""
    for path in FEATURES:
        document = Parser().parse(path.read_text(encoding="utf-8"))
        document["uri"] = path.relative_to(ROOT).as_posix()
        yield path, document, Compiler().compile(document)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
STEPS = (ROOT / "runtime" / "steps.md").read_text(encoding="utf-8")
LABEL = re.compile(r" \([A-Za-z0-9][\w-]*\)$")
PARAMETERS = {name: matches.replace(r"\|", "|")
              for names, matches in re.findall(r"^\| (`\{[a-z]+\}`(?:, `\{[a-z]+\}`)*) \| `([^`]+)` \|", STEPS, re.M)
              for name in re.findall(r"\{([a-z]+)\}", names)}


def pattern(phrase):
    """A phrase of runtime/steps.md as a regular expression: each parameter as the table gives it, `(s)` optional, `a/b`
    either."""
    found = ""
    for part in re.split(r"(\{[a-z]+\}|\([a-z]+\)|[A-Za-z']+(?:/[A-Za-z']+)+)", phrase):
        if part.startswith("{"):
            found += f"(?:{PARAMETERS[part[1:-1]]})"
        elif part.startswith("("):
            found += f"(?:{re.escape(part[1:-1])})?"
        elif "/" in part:
            found += "(?:" + "|".join(map(re.escape, part.split("/"))) + ")"
        else:
            found += re.escape(part)
    return re.compile(found)


PHRASES = [pattern(phrase) for heading in re.findall(r"^### (.+)$", STEPS, re.M)
           for phrase in re.findall(r"`([^`]+)`", heading)]


def test_every_step_is_one_the_step_document_lists_and_only_a_given_or_when_is_labelled():
    unlisted = {(path.name, step["text"]) for path, _, pickles in documents() for pickle in pickles
                for step in pickle["steps"]
                if not any(phrase.fullmatch(LABEL.sub("", step["text"])) for phrase in PHRASES)
                or (LABEL.search(step["text"]) and step.get("type") == "Outcome")}
    assert unlisted == set()


def test_each_example_has_a_test_iri_of_its_own_and_takes_its_steps_in_time_order():
    clashes, backwards = [], []
    for path, _, pickles in documents():
        slugs = [slug(pickle["name"]) for pickle in pickles]
        clashes += [(path.name, name) for name in set(slugs) if slugs.count(name) > 1]
        for pickle in pickles:
            times = [f"{found.group(1)}T{found.group(2)}" for step in pickle["steps"]
                     for found in [TIME.search(step["text"])] if found]
            if times != sorted(times):
                backwards.append((path.name, pickle["name"]))
    assert (clashes, backwards) == ([], [])


def test_every_rule_has_an_example_or_says_why_none_can_show_it():
    silent = [(path.name, child["rule"]["name"]) for path, document, _ in documents()
              for child in document["feature"]["children"] if "rule" in child
              if not any("scenario" in inner for inner in child["rule"]["children"])
              and not re.search(r"No example|no test of its own", " ".join(child["rule"]["description"].split()))]
    assert silent == []


def test_every_inline_query_parses():
    broken = []
    for path, _, pickles in documents():
        for pickle in pickles:
            for step in pickle["steps"]:
                query = step.get("argument", {}).get("docString", {}).get("content")
                if query is not None:
                    try:
                        parseQuery(PREFIXES + query)
                    except Exception as error:
                        broken.append((path.name, pickle["name"], str(error)[:80]))
    assert broken == []


def test_each_planted_case_a_kit_names_is_a_rule_of_it_with_an_example():
    planted, shown = {}, {}
    for kit in KITS:
        feature = Parser().parse((kit / f"{kit.name}.feature").read_text(encoding="utf-8"))["feature"]
        named = re.search(r"P1 to P(\d+)", " ".join(feature["description"].split()))
        planted[kit.name] = set(range(1, int(named.group(1)) + 1)) if named else set()
        shown[kit.name] = {int(found.group(1)) for child in feature["children"] if "rule" in child
                           for found in [re.match(r"P(\d+)\.", child["rule"]["name"])]
                           if found and any("scenario" in inner for inner in child["rule"]["children"])}
    assert all(planted.values()), planted
    assert shown == planted


def ni_name(octets):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode().rstrip("=")


def test_every_rule_list_names_a_comparison_whose_bytes_hash_to_its_hash_and_guards_on_its_kind_but_those_examples_break():
    lists = {path.relative_to(ROOT).as_posix(): rows
             for path in sorted(path for top in ("runtime", "conformance")
                                for index in (ROOT / top).rglob("references.ttl") for path in index.parent.glob("*.ttl"))
             for rows in [parsed(path)] if (None, RDF.type, REC.MatcherRule) in rows}
    assert len(lists) == 16
    mismatched, unguarded = set(), set()
    for path, rows in lists.items():
        for row in rows.subjects(RDF.type, REC.MatcherRule):
            query = str(rows.value(row, REC.query))
            assert query.startswith("matcher/"), path
            octets = (QUERIES / query).read_bytes()
            text = octets.decode("utf-8")
            if ni_name(octets) != str(rows.value(row, REC.queryHash)):
                mismatched.add(("/".join(path.split("/")[-3:-1]), query))
            if not guarded(frozenset(rows.objects(row, REC.tableKind)), text):
                unguarded.add((path, query))
    assert mismatched == {("finn/references", "matcher/same-code.rq"),
                          ("tables/app-new-rules", "matcher/same-code-and-date.rq")}
    assert unguarded == set()


@cache
def guarded(kinds, query):
    """Whether a query reads GRAPH ?origin exactly when its row names one table kind, and joins, outside any graph, the
    one triple ?origin prov:specializationOf/rec:tableKind on that kind."""
    origin, guard = Variable("origin"), PROV.specializationOf / REC.tableKind
    found, reads = set(), False

    def walk(node, joined):
        nonlocal reads
        if isinstance(node, list):
            for item in node:
                walk(item, joined)
        elif isinstance(node, CompValue):
            if node.name == "Graph" and node.term == origin:
                reads = True
            if node.name == "BGP" and joined:
                found.update(o for s, p, o in node.triples if s == origin and p == guard)
            for key, value in node.items():
                walk(value, joined and node.name not in ("Graph", "Union", "Minus")
                     and (node.name, key) != ("LeftJoin", "p2"))

    walk(prepareQuery(query).algebra, True)
    return found == kinds and len(kinds) <= 1 and reads == bool(kinds)


@pytest.mark.parametrize("kinds, query, expected", [
    ({REC.VaccineGroups}, "SELECT * { ?origin prov:specializationOf/rec:tableKind rec:VaccineGroups . "
                          "GRAPH ?origin { ?s ?p ?o } }", True),
    ({REC.VaccineGroups}, "# ?origin prov:specializationOf/rec:tableKind rec:VaccineGroups .\n"
                          "SELECT * { GRAPH ?origin { ?s ?p ?o } }", False),
    ({REC.SubstanceIngredients}, "SELECT * { ?origin prov:specializationOf/rec:tableKind rec:VaccineGroups . "
                                 "GRAPH ?origin { ?s ?p ?o } }", False),
    (set(), "SELECT * { ?origin prov:specializationOf/rec:tableKind rec:VaccineGroups . GRAPH ?origin { ?s ?p ?o } }",
     False),
    ({REC.VaccineGroups, REC.SubstanceIngredients}, "SELECT * { ?origin prov:specializationOf/rec:tableKind "
                                                    "rec:VaccineGroups . GRAPH ?origin { ?s ?p ?o } }", False),
    ({REC.VaccineGroups}, "SELECT * { OPTIONAL { ?origin prov:specializationOf/rec:tableKind rec:VaccineGroups . } "
                          "GRAPH ?origin { ?s ?p ?o } }", False),
    ({REC.VaccineGroups}, "SELECT * { ?origin prov:specializationOf ?v . ?v rec:tableKind rec:VaccineGroups . "
                          "GRAPH ?origin { ?s ?p ?o } }", False),
])
def test_a_rule_reads_a_table_graph_exactly_when_its_row_names_the_kind_one_joined_triple_guards_it_on(kinds, query,
                                                                                                        expected):
    assert guarded(frozenset(kinds), PREFIXES + query) == expected
