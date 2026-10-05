"""Every feature file is Gherkin a standard parser reads, and every step it takes is one runtime/steps.md lists."""

import re

import pytest
from gherkin.parser import Parser
from gherkin.pickles.compiler import Compiler

from contract import ROOT

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
