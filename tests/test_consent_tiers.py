from functools import cache

import pytest
from pyoxigraph import NamedNode, Quad, RdfFormat, Store
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import SKOS

from contract import CASCADE, ROOT, feature_documents
from test_features import PREFIXES

ONTOLOGY = ROOT / "ontologies" / "cascade.ttl"
TOOLS = NamedNode("urn:cascade:tools")
VOCABULARY = NamedNode("urn:cascade:vocabulary")
TOOL = Namespace("urn:cascade:tool:")


@cache
def ontology():
    return Graph().parse(ONTOLOGY)


def in_scheme(scheme):
    return set(ontology().subjects(SKOS.inScheme, scheme))


@cache
def the_check():
    """The query of Y1's one example, as `runtime/consent.feature` holds it."""
    for path, document, pickles in feature_documents():
        if path.name == "consent.feature":
            return next(step["argument"]["docString"]["content"] for pickle in pickles for step in pickle["steps"]
                        if "argument" in step)
    raise LookupError("runtime/consent.feature holds no query")


def answered(tools):
    """The tools Y1's query names, over a listing of `tools`, each a name with the kind and the tier it declares."""
    store = Store()
    store.load(ONTOLOGY.read_bytes(), format=RdfFormat.TURTLE, to_graph=VOCABULARY)
    for name, kind, tier in tools:
        for predicate, value in ((CASCADE.modelToolActKind, kind), (CASCADE.consentTier, tier)):
            if value is not None:
                store.add(Quad(NamedNode(TOOL[name]), NamedNode(predicate), NamedNode(value), TOOLS))
    return sorted(solution["tool"].value for solution in store.query(PREFIXES + the_check()))


class TestConsentTiers:
    """Consent tiers of the tools a model is offered · ontologies/cascade.ttl, runtime/consent.feature

    A model is offered a pod through tools. Each tool takes one kind of act, and each kind has one consent tier: free,
    ask or never. Y1 checks a runtime's tools against the kinds' tiers with one query.
    """

    class TestGivenEveryKindOfActOfAModelTool:
        """given every kind of act of a model tool, in `cascade:ModelToolActKinds`"""

        def test_has_one_consent_tier_of_the_three(self):
            """has one consent tier, of the three in `cascade:ConsentTiers`"""
            kinds = in_scheme(CASCADE.ModelToolActKinds)
            tiers = in_scheme(CASCADE.ConsentTiers)
            assert len(kinds) >= 8
            assert sorted(kind for kind in kinds for its in [set(ontology().objects(kind, CASCADE.consentTier))]
                          if len(its) != 1 or not its <= tiers) == []

        def test_falls_in_every_tier_between_them(self):
            """falls in every tier, between them"""
            assert {tier for kind in in_scheme(CASCADE.ModelToolActKinds)
                    for tier in ontology().objects(kind, CASCADE.consentTier)} == {
                CASCADE.ConsentTierFree, CASCADE.ConsentTierAsk, CASCADE.ConsentTierNever}

    class TestGivenTheConsentTiers:
        """given the consent tiers, in `cascade:ConsentTiers`"""

        def test_are_free_ask_and_never_each_by_its_one_notation(self):
            """are free, ask and never, each by its one notation, as a tool declares its tier"""
            notations = {tier: list(ontology().objects(tier, SKOS.notation)) for tier in in_scheme(CASCADE.ConsentTiers)}
            assert notations == {CASCADE.ConsentTierFree: [Literal("free")], CASCADE.ConsentTierAsk: [Literal("ask")],
                                 CASCADE.ConsentTierNever: [Literal("never")]}

    class TestGivenY1sQueryOverAListingOfTools:
        """given Y1's query, over a listing of tools and the vocabulary

        Each case lists two tools that agree with their kinds, a read and a write, and one more tool as the case says.
        """

        AGREEING = [("reads", CASCADE.ReadingPodsOrTables, CASCADE.ConsentTierFree),
                    ("writes", CASCADE.WritingToAPod, CASCADE.ConsentTierAsk)]

        def test_answers_nothing_when_every_tool_runs_at_its_kinds_tier(self):
            """answers nothing when every tool runs at its kind's tier"""
            assert answered(self.AGREEING) == []

        @pytest.mark.parametrize("kind, tier", [
            (CASCADE.WritingToAPod, CASCADE.ConsentTierFree),
            (CASCADE.DeletingPods, CASCADE.ConsentTierNever),
            (None, CASCADE.ConsentTierFree),
            (CASCADE.ReadingPodsOrTables, None),
            (URIRef(CASCADE + "NoSuchKind"), CASCADE.ConsentTierFree),
        ], ids=["a write at free", "an act whose tier is never", "with no kind",
                "with no tier", "of a kind the vocabulary does not list"])
        def test_names_the_one_tool(self, kind, tier):
            """names the one tool that runs"""
            assert answered([*self.AGREEING, ("odd", kind, tier)]) == [str(TOOL["odd"])]
