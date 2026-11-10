import json
import re

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS

from contract import ROOT, feature_documents
from naming import CASCADE, matcher_judgment_name, named, record_from_server_name

PAV = Namespace("http://purl.org/pav/")
MATCHER_JUDGMENT_VERSIONS = json.loads((ROOT / "tests" / "matcher-judgment-versions.json").read_text(encoding="utf-8"))


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


def names_beside_inputs():
    for _, _, pickles in feature_documents():
        for pickle in pickles:
            for step in pickle["steps"]:
                header, *rows = [[cell["value"] for cell in row["cells"]]
                                 for row in step.get("argument", {}).get("dataTable", {}).get("rows", [])] or [[]]
                if {"inputs", "name"} <= set(header):
                    yield from ((row[header.index("inputs")], row[header.index("name")]) for row in rows)


def matcher_judgments_written_with_what_they_used():
    """Each kit matcher judgment a feature writes with its justification, members, the rule list versions it is
    asserted under, what it used and its name, with its kit."""
    for path, _, pickles in feature_documents():
        kit = path.parent
        if kit.parent != ROOT / "conformance":
            continue
        for pickle in pickles:
            for step in pickle["steps"]:
                header, *rows = [[cell["value"] for cell in row["cells"]]
                                 for row in step.get("argument", {}).get("dataTable", {}).get("rows", [])] or [[]]
                columns = ("justification", "members", "asserted under", "used", "name")
                if set(columns) <= set(header):
                    yield from ((kit, *(row[header.index(column)] for column in columns)) for row in rows)


def resolver(kit):
    """A kit's matcher judgment labels as IRIs: a record by its handle, a reference version by its series' label and
    version, a record's version by tests/matcher-judgment-versions.json (the names its saved Bridge outputs give,
    re-minted), and a justification by its label."""
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
            return MATCHER_JUDGMENT_VERSIONS[kit.name][version[2]][int(version[1]) - 1]
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


class TestNamesAFeatureWrites:
    """Names a feature writes beside their inputs · runtime/*.feature, conformance/*/*.feature, runtime/steps.md

    A table in a feature may give a thing's name in a `name` column beside an `inputs` column: the naming rule, then
    what the rule is given. A runtime that runs the feature compares names, so one wrong cell fails every runtime.

    @rule naming N6
    """

    class TestGivenAnyTableWithInputsAndAName:
        """given any table with an `inputs` and a `name` column"""

        def test_holds_no_name_that_its_rule_does_not_give(self):
            """holds no name that the rule its inputs begin with does not give

            Each `inputs` cell, the rule then what the rule is given, is read and the name that rule gives from those
            inputs is compared with the name written beside it; at least thirteen pairs are read, and a pair whose
            names differ fails.
            """
            pairs = sorted(set(names_beside_inputs()))
            assert len(pairs) >= 13
            assert [(inputs, name) for inputs, name in pairs if named(*inputs_of(inputs)) != name] == []

    class TestGivenAKitsTableOfMatcherJudgments:
        """given a kit's table of matcher judgments"""

        def test_holds_no_name_that_the_naming_rule_does_not_give(self):
            """holds no name that N6's rule does not give from the members, the justification and what the row says it
            used

            Each kit's table of matcher judgments, at least eleven, is read with its justification, its members and
            the reference versions it says it used; the records and versions are looked up from the kit's own files, and
            the name N6's rule gives from them is compared with the name the row writes. It takes longer than any other case
            of this module, as each kit's references are read once for each row.
            """
            judgments = list(matcher_judgments_written_with_what_they_used())
            assert len(judgments) >= 11
            wrong = []
            for kit, justified, members, asserted_under, used_labels, name in judgments:
                record, used, justification, matcher_rule = resolver(kit)
                justified_as = justification(justified)
                uses = [used(label.strip()) for label in used_labels.split(",")]
                rule = next(filter(None, (matcher_rule(used(label.strip()), justified_as)
                                          for label in asserted_under.split(","))))
                computed = matcher_judgment_name(CASCADE + "CascadeMatcher", rule, justified_as,
                                                 [record(m.strip()) for m in members.split(",")], uses)
                if computed != name:
                    wrong.append((kit.name, justified, members, name, computed))
            assert wrong == []


class TestChecksOfTheNameCheck:
    """Checks of the check on a feature's names · tests/test_naming.py

    The rule above is checked by functions of this module. This case shows the reader of a cell a cell with a list in it,
    so a table whose names are all right is not passed only because its cells were misread.
    """

    class TestInputsOf:
        """`inputs_of()`"""

        def test_reads_a_cell_as_the_rule_then_its_inputs_with_a_list_in_parentheses(self):
            """reads a cell as the rule, then its inputs, with a list in parentheses

            Given a cell of the matcher judgment rule with two lists and one of the snapshot rule with an empty list,
            `inputs_of()` returns the rule's name and its inputs in order, each list as a list and `cascade:` written
            out as the namespace.
            """
            assert inputs_of("cascade:MatcherJudgmentNamingRule, cascade:m, r, j, (b, a), (u)") == (
                "MatcherJudgmentNamingRule", [CASCADE + "m", "r", "j", ["b", "a"], ["u"]])
            assert inputs_of("cascade:SnapshotNamingRule, a, (), (p), h") == ("SnapshotNamingRule", ["a", [], ["p"], "h"])
