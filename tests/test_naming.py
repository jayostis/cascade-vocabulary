"""Every name a feature file writes beside its inputs follows the rule its inputs name first, as tests/naming.py computes
it: the rule's term, then its inputs in order, a list in parentheses."""

import re

from naming import CASCADE, named
from test_features import documents


def inputs_of(cell):
    """A cell's rule and its inputs: items separated by commas, a list as its items in parentheses, cascade: standing for
    the namespace."""
    items = []
    for listed, single in re.findall(r"\(([^()]*)\)|([^,()]+)", cell):
        if single.strip():
            items.append(single.strip())
        elif not single:
            items.append([part.strip() for part in listed.split(",") if part.strip()])
    full = lambda item: CASCADE + item.removeprefix("cascade:") if item.startswith("cascade:") else item
    rule, *rest = [[full(i) for i in item] if isinstance(item, list) else full(item) for item in items]
    return rule.removeprefix(CASCADE), rest


def written():
    for _, _, pickles in documents():
        for pickle in pickles:
            for step in pickle["steps"]:
                header, *rows = [[cell["value"] for cell in row["cells"]]
                                 for row in step.get("argument", {}).get("dataTable", {}).get("rows", [])] or [[]]
                if {"inputs", "name"} <= set(header):
                    yield from ((row[header.index("inputs")], row[header.index("name")]) for row in rows)


def test_the_inputs_are_read_as_the_rule_then_its_inputs_a_list_in_parentheses():
    assert inputs_of("cascade:ClaimNamingRule, cascade:m, r, j, (b, a), (u)") == (
        "ClaimNamingRule", [CASCADE + "m", "r", "j", ["b", "a"], ["u"]])
    assert inputs_of("cascade:SnapshotNamingRule, a, (), (p), h") == ("SnapshotNamingRule", ["a", [], ["p"], "h"])


def test_every_name_written_beside_its_inputs_follows_its_rule():
    pairs = sorted(set(written()))
    assert len(pairs) >= 13
    assert [(inputs, name) for inputs, name in pairs if named(*inputs_of(inputs)) != name] == []
