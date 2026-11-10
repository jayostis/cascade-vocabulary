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

from contract import KITS, PROV, QUERIES, CASCADE, ROOT
from engines import parsed
from naming import ni_name

FEATURES = sorted([*ROOT.glob("runtime/*.feature"), *ROOT.glob("conformance/*/*.feature")])
TIME = re.compile(r" on (\d{4}-\d{2}-\d{2}) at (\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)(?: \(|$)")
PREFIXES = "".join(f"PREFIX {prefix}: <{base}>\n" for prefix, base in {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#", "prov": "http://www.w3.org/ns/prov#", "pav": "http://purl.org/pav/",
    "dct": "http://purl.org/dc/terms/", "bridge": "https://ns.cascadeprotocol.org/bridge/v1-draft#",
    "oa": "http://www.w3.org/ns/oa#", "cascade": "https://ns.cascadeprotocol.org/cascade#",
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


@cache
def rule_lists():
    """Each rule list the features and kits carry, parsed, by its path under the vocabulary."""
    return {path.relative_to(ROOT).as_posix(): rows
            for path in sorted(path for top in ("runtime", "conformance")
                               for index in (ROOT / top).rglob("references.ttl") for path in index.parent.glob("*.ttl"))
            for rows in [parsed(path)] if (None, RDF.type, CASCADE.RuleListRow) in rows}


@cache
def guarded(kinds, query):
    """Whether a query reads GRAPH ?origin exactly when its row names one table kind, and joins, outside any graph, the
    one triple ?origin prov:specializationOf/cascade:tableKind on that kind."""
    origin, guard = Variable("origin"), PROV.specializationOf / CASCADE.tableKind
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


class TestFeatureFiles:
    """Feature files any runtime can run · runtime/*.feature, conformance/*/*.feature, runtime/steps.md

    The rules of a pod are Gherkin features, and a runtime proves itself by running them.

    `runtime/steps.md` lists every phrase a Given, a When or a Then may use, so a runtime that implements that list can run
    every feature.
    """

    class TestGivenEveryFeatureFile:
        """given every feature file

        Each file holds examples, and each example is a few lines beginning Given, When or Then. These cases read the
        lines of every example in every file.
        """

        def test_writes_every_given_when_and_then_in_a_phrase(self):
            """writes every Given, When and Then in a phrase that `runtime/steps.md` lists"""
            unlisted = {(path.name, step["text"]) for path, _, pickles in documents() for pickle in pickles
                        for step in pickle["steps"]
                        if not any(phrase.fullmatch(LABEL.sub("", step["text"])) for phrase in PHRASES)}
            assert unlisted == set()

        def test_ends_only_a_given_or_a_when_with_a_name_in_parentheses(self):
            """ends only a Given or a When with a name in parentheses

            A name in parentheses at the end of a Given or a When is how a later line names what that one made.
            """
            named = {(path.name, step["text"]) for path, _, pickles in documents() for pickle in pickles
                     for step in pickle["steps"] if LABEL.search(step["text"]) and step.get("type") == "Outcome"}
            assert named == set()

        def test_gives_each_example_a_name_whose_slug_no_other_example_of_its_file_has(self):
            """gives each example a name whose slug no other example of its file has

            A runtime's report names an example by that slug, as its test IRI.
            """
            clashes = []
            for path, _, pickles in documents():
                slugs = [slug(pickle["name"]) for pickle in pickles]
                clashes += [(path.name, name) for name in set(slugs) if slugs.count(name) > 1]
            assert clashes == []

        def test_puts_each_examples_dated_lines_in_time_order(self):
            """puts each example's dated lines in time order, earliest first

            A dated line is one that gives a moment, as "on 2026-03-01 at 09:30": it ends with that date and time of day, or
            has it just before a name in parentheses. The moments of an example's dated lines never go back.
            """
            backwards = []
            for path, _, pickles in documents():
                for pickle in pickles:
                    times = [f"{found.group(1)}T{found.group(2)}" for step in pickle["steps"]
                             for found in [TIME.search(step["text"])] if found]
                    if times != sorted(times):
                        backwards.append((path.name, pickle["name"]))
            assert backwards == []

        def test_has_for_every_rule_an_example_or_a_sentence(self):
            """has, for every rule, an example or a sentence saying why none can show it"""
            silent = [(path.name, child["rule"]["name"]) for path, document, _ in documents()
                      for child in document["feature"]["children"] if "rule" in child
                      if not any("scenario" in inner for inner in child["rule"]["children"])
                      and not re.search(r"No example|no test of its own", " ".join(child["rule"]["description"].split()))]
            assert silent == []

        def test_parses_every_query_written_inline_in_an_example(self):
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

    class TestGivenTheKitsFeatures:
        """given the kits' features"""

        def test_has_for_every_planted_case_a_kit_names_a_rule_with_an_example(self):
            """has, for every planted case a kit names, a rule with an example"""
            planted, shown = {}, {}
            for kit in KITS:
                feature = Parser().parse((kit / f"{kit.name}.feature").read_text(encoding="utf-8"))["feature"]
                named = re.search(r"\bplanted cases? ([A-Z])1 to \1(\d+)", " ".join(feature["description"].split()))
                planted[kit.name] = set(range(1, int(named.group(2)) + 1)) if named else set()
                letter = named.group(1) if named else "P"
                shown[kit.name] = {int(found.group(1)) for child in feature["children"] if "rule" in child
                                   for found in [re.match(rf"{letter}(\d+)\.", child["rule"]["name"])]
                                   if found and any("scenario" in inner for inner in child["rule"]["children"])}
            assert all(planted.values()), planted
            assert shown == planted


class TestRuleLists:
    """Rule lists the features and kits carry · runtime/rule-list/, **/references/*.ttl

    A rule list names each comparison the matcher runs by its path and by the hash of its bytes, and the table kind it
    reads. The lists under the features' and kits' scripted input are held to that, but for two that show a mismatch.

    @rule matcher M4
    @rule matcher M7
    """

    class TestGivenEveryRuleList:
        """given every rule list a feature or a kit carries

        The files that hold rule list rows beside a `references.ttl` under `runtime/` or `conformance/`.
        """

        def test_names_only_comparisons_under_matcher(self):
            """names only comparisons under `matcher/`"""
            lists = rule_lists()
            assert lists
            elsewhere = sorted((path, str(rows.value(row, CASCADE.queryPath))) for path, rows in lists.items()
                               for row in rows.subjects(RDF.type, CASCADE.RuleListRow)
                               if not str(rows.value(row, CASCADE.queryPath)).startswith("matcher/"))
            assert elsewhere == []

        def test_names_the_hash_of_its_comparisons_bytes(self):
            """names the hash of its comparison's bytes, but for the two lists that show a mismatch"""
            lists = rule_lists()
            assert lists
            mismatched = {("/".join(path.split("/")[-3:-1]), str(rows.value(row, CASCADE.queryPath)))
                          for path, rows in lists.items() for row in rows.subjects(RDF.type, CASCADE.RuleListRow)
                          if ni_name((QUERIES / str(rows.value(row, CASCADE.queryPath))).read_bytes())
                          != str(rows.value(row, CASCADE.queryHash))}
            assert mismatched == {("finn/references", "matcher/same-code.rq"),
                                  ("tables/app-new-rules", "matcher/same-code-and-date.rq")}

        def test_reads_a_tables_rows_exactly_when_its_row_names_one_table_kind(self):
            """reads a table's rows exactly when its row names one table kind, joined on that kind"""
            lists = rule_lists()
            assert lists
            unguarded = {(path, str(rows.value(row, CASCADE.queryPath))) for path, rows in lists.items()
                         for row in rows.subjects(RDF.type, CASCADE.RuleListRow)
                         if not guarded(frozenset(rows.objects(row, CASCADE.tableKind)),
                                        (QUERIES / str(rows.value(row, CASCADE.queryPath))).read_text(encoding="utf-8"))}
            assert unguarded == set()


class TestChecksOfTheRuleListCheck:
    """Checks of the checks on a rule list · tests/test_features.py

    The rule above is checked by a function of this module. These cases show it a query that joins the guard and queries
    that only seem to, so a rule that every list keeps is known to be checked.
    """

    class TestGuarded:
        """`guarded()`"""

        def test_accepts_a_query_that_joins_the_guard_on_the_one_kind_its_row_names(self):
            query = ("SELECT * { ?origin prov:specializationOf/cascade:tableKind cascade:VaccineGroups . "
                     "GRAPH ?origin { ?s ?p ?o } }")
            assert guarded(frozenset({CASCADE.VaccineGroups}), PREFIXES + query)

        @pytest.mark.parametrize("kinds, query", [
            ({CASCADE.VaccineGroups}, "# ?origin prov:specializationOf/cascade:tableKind cascade:VaccineGroups .\n"
                                      "SELECT * { GRAPH ?origin { ?s ?p ?o } }"),
            ({CASCADE.SubstanceIngredients}, "SELECT * { ?origin prov:specializationOf/cascade:tableKind cascade:VaccineGroups . "
                                             "GRAPH ?origin { ?s ?p ?o } }"),
            (set(), "SELECT * { ?origin prov:specializationOf/cascade:tableKind cascade:VaccineGroups . GRAPH ?origin { ?s ?p ?o } }"),
            ({CASCADE.VaccineGroups, CASCADE.SubstanceIngredients}, "SELECT * { ?origin prov:specializationOf/cascade:tableKind "
                                                                    "cascade:VaccineGroups . GRAPH ?origin { ?s ?p ?o } }"),
            ({CASCADE.VaccineGroups}, "SELECT * { OPTIONAL { ?origin prov:specializationOf/cascade:tableKind cascade:VaccineGroups . } "
                                      "GRAPH ?origin { ?s ?p ?o } }"),
            ({CASCADE.VaccineGroups}, "SELECT * { ?origin prov:specializationOf ?v . ?v cascade:tableKind cascade:VaccineGroups . "
                                      "GRAPH ?origin { ?s ?p ?o } }"),
        ], ids=["a guard only in a comment", "a guard on another kind", "a guard with no kind in the row",
                "a row naming two kinds", "a guard inside an OPTIONAL", "a guard written as two triples"])
        def test_refuses(self, kinds, query):
            assert not guarded(frozenset(kinds), PREFIXES + query)
