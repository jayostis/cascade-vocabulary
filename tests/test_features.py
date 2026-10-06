"""Every feature file is Gherkin a standard parser reads, every step it takes is one runtime/steps.md lists, and the
scripted input it names is whole."""

import base64
import hashlib
import re

import pytest
from gherkin.parser import Parser
from gherkin.pickles.compiler import Compiler

from rdflib.namespace import RDF
from rdflib.plugins.sparql.parser import parseQuery

from contract import QUERIES, REC, ROOT
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


def test_each_planted_case_is_a_rule_of_the_kit_with_an_example():
    document = Parser().parse((ROOT / "conformance" / "alex-rivera" / "alex-rivera.feature").read_text(encoding="utf-8"))
    shown = {int(found.group(1)) for child in document["feature"]["children"] if "rule" in child
             for found in [re.match(r"P(\d+)\.", child["rule"]["name"])]
             if found and any("scenario" in inner for inner in child["rule"]["children"])}
    assert shown == set(range(1, 26))


def ni_name(octets):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(hashlib.sha256(octets).digest()).decode().rstrip("=")


def test_every_rule_list_names_a_comparison_whose_bytes_hash_to_its_hash_but_the_one_an_example_breaks():
    lists = {path.relative_to(ROOT).as_posix(): rows
             for path in sorted([*ROOT.glob("runtime/scripted-input/*/references/*.ttl"),
                                 *ROOT.glob("conformance/*/scripted-input/*/references/*.ttl")])
             for rows in [parsed(path)] if (None, RDF.type, REC.MatcherRule) in rows}
    assert len(lists) == 5
    mismatched = set()
    for path, rows in lists.items():
        for row in rows.subjects(RDF.type, REC.MatcherRule):
            query = str(rows.value(row, REC.query))
            assert query.startswith("matcher/"), path
            if ni_name((QUERIES / query).read_bytes()) != str(rows.value(row, REC.queryHash)):
                mismatched.add((path.split("/")[2], query))
    assert mismatched == {("finn", "matcher/same-code.rq")}
