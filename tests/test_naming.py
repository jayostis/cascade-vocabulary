"""Every name a feature file writes beside its inputs follows the rule its inputs name first, as tests/naming.py computes
it: the rule's term, then its inputs in order, a list in parentheses."""

import json
import re

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS

from contract import ROOT
from naming import CASCADE, claim_name, named, record_from_server_name
from test_features import documents

PAV = Namespace("http://purl.org/pav/")
CLAIM_VERSIONS = json.loads((ROOT / "tests" / "claim-versions.json").read_text(encoding="utf-8"))


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


def claims_written_with_what_they_used():
    """Each kit claim a feature writes with its justification, members, what it used and its name, with its kit."""
    for path, _, pickles in documents():
        kit = path.parent
        if kit.parent != ROOT / "conformance":
            continue
        for pickle in pickles:
            for step in pickle["steps"]:
                header, *rows = [[cell["value"] for cell in row["cells"]]
                                 for row in step.get("argument", {}).get("dataTable", {}).get("rows", [])] or [[]]
                if {"justification", "members", "used", "name"} <= set(header):
                    yield from ((kit, *(row[header.index(column)] for column in ("justification", "members", "used",
                                                                                "name"))) for row in rows)


def resolver(kit):
    """A kit's claim labels as IRIs: a record by its handle, a reference version by its series' label and version, a
    record's version by tests/claim-versions.json (the names its saved Bridge outputs give, re-minted), and a
    justification by its label."""
    handles = json.loads((kit / "expected" / "handles.json").read_text(encoding="utf-8"))["records"]
    references = Graph()
    for file in kit.glob("scripted-input/*/references/references.ttl"):
        references.parse(file, format="turtle")
    vocabulary = Graph().parse(ROOT / "ontologies" / "cascade.ttl", format="turtle")

    def record(handle):
        given = handles[handle]
        return record_from_server_name(given["server"], given["type"], given["id"])

    def used(label):
        if version := re.fullmatch(r"version (\d+) of (.+)", label):
            return CLAIM_VERSIONS[kit.name][version[2]][int(version[1]) - 1]
        series_label, number = label.rsplit(" version ", 1)
        series = references.value(None, RDFS.label, Literal(series_label))
        return str(next(v for v in references.subjects(PROV.specializationOf, series)
                        if references.value(v, PAV.version) == Literal(number)))

    def justification(label):
        return str(vocabulary.value(None, RDFS.label, Literal(label, lang="en")))

    def matcher_rule(rule_list, justified_as):
        rows = Graph()
        for file in kit.glob(f"scripted-input/*/references/{rule_list.removeprefix('urn:uuid:')}.ttl"):
            rows.parse(file, format="turtle")
        term = lambda local: URIRef(CASCADE + local)
        return next((str(rows.value(row, term("matcherRule"))) for row in rows.subjects(RDF.type, term("RuleListRow"))
                     if rows.value(row, term("justifiedAs")) == URIRef(justified_as)), None)

    return record, used, justification, matcher_rule


def test_every_claim_a_kit_writes_with_what_it_used_is_named_by_the_claim_rule_over_them():
    claims = list(claims_written_with_what_they_used())
    assert len(claims) >= 11
    wrong = []
    for kit, justified, members, used_labels, name in claims:
        record, used, justification, matcher_rule = resolver(kit)
        justified_as = justification(justified)
        uses = [used(label.strip()) for label in used_labels.split(",")]
        rule = next(filter(None, (matcher_rule(u, justified_as) for u in uses if u.startswith("urn:uuid:"))))
        computed = claim_name(CASCADE + "CascadeMatcher", rule, justified_as,
                              [record(m.strip()) for m in members.split(",")], uses)
        if computed != name:
            wrong.append((kit.name, justified, members, name, computed))
    assert wrong == []
