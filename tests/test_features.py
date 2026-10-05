"""Every feature file is Gherkin a standard parser reads, every step it takes is one runtime/steps.md lists, and the
scripted input it names is whole."""

import base64
import hashlib
import re

import pytest
from gherkin.parser import Parser
from gherkin.pickles.compiler import Compiler

from rdflib.namespace import RDF

from contract import QUERIES, REC, ROOT
from engines import parsed

FEATURES = sorted([*ROOT.glob("runtime/*.feature"), *ROOT.glob("conformance/*/*.feature")])
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


@pytest.mark.parametrize("path", FEATURES, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_every_step_is_one_the_step_document_lists(path):
    document = Parser().parse(path.read_text(encoding="utf-8"))
    document["uri"] = path.relative_to(ROOT).as_posix()
    unlisted = {step["text"] for pickle in Compiler().compile(document) for step in pickle["steps"]
                if not any(phrase.fullmatch(LABEL.sub("", step["text"])) for phrase in PHRASES)}
    assert unlisted == set()


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
