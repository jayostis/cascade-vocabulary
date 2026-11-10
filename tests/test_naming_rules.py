import base64
import re

import pytest
from pyoxigraph import BlankNode, CanonicalizationAlgorithm, Dataset, NamedNode, RdfFormat, Store, Triple, Variable
from pyoxigraph import Literal as OxigraphLiteral
from pyoxigraph import parse, serialize

import naming
from naming_vectors import VECTORS, base_urls, flattened, refused_base_urls, v8_query, vectors

NO_QUERY = {"VersionNamingRule", "RevisionNamingRule", "FindingNamingRule", "TableVersionNamingRule",
            "DocumentNamingRule", "MatcherJudgmentNamingRule", "SnapshotNamingRule"}
REFUSED = dict(refused_base_urls())
CONTENT_VECTORS = [v for v in vectors() if v.input is not None]
NAME_SHAPES = [r"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-8[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
               r"ni:///sha-256;[A-Za-z0-9_-]{43}", r"[a-z/-]+\.ttl#[0-9a-f]{64}"]


def reference_name(vector):
    if vector.rule == "DocumentNamingRule":
        return naming.document_name(vector.input.read_bytes())
    if vector.input is not None:
        return naming.content_name(naming.content(vector.input.read_text(encoding="utf-8")))
    return naming.named(vector.rule, list(vector.inputs))


def sparql_sha256(text):
    [solution] = Store().query("SELECT ?text (SHA256(?text) AS ?hash) {}", substitutions={
        Variable("text"): OxigraphLiteral(text)})
    return solution["hash"].value


def ni_from_hex(hexed):
    return "ni:///sha-256;" + base64.urlsafe_b64encode(bytes.fromhex(hexed)).decode().rstrip("=")


class TestNamingVectors:
    """Naming vectors every runtime and adapter reproduces · tests/vectors/naming/

    A naming vector is a worked example of one naming rule: its inputs and the name they give. The runtime and the
    adapters each run these vectors, so every name here is worked out more than one way: by the reference
    implementation, and apart from it by the rule's own query or by Oxigraph's canonical form and SHA-256.

    @rule naming N3
    @rule naming N5
    """

    class TestGivenTheFolderOfVectors:
        """given the folder of vectors"""

        def test_holds_a_vector_of_every_naming_rule(self):
            """holds a vector of every naming rule

            The rules the reference implementation names are compared with the rules the vectors are of, so a rule added
            to the reference implementation with no vector fails.
            """
            assert {vector.rule for vector in vectors()} == set(naming.RULES)

        def test_holds_a_query_for_every_rule_but_the_seven_that_sparql_cannot_compute(self):
            """holds a query for every rule but the seven that SPARQL cannot compute

            The rules that have a vector with a query are compared with the rules the reference implementation names
            less the seven that SPARQL cannot compute, and the `.rq` files in the folder are compared with those rules,
            so a query that no vector uses fails too.
            """
            with_query = {vector.rule for vector in vectors() if vector.query is not None}
            assert with_query == set(naming.RULES) - NO_QUERY
            assert {file.stem for file in VECTORS.glob("*.rq")} == with_query

        def test_gives_every_vector_of_a_rule_that_has_a_query_that_query(self):
            """gives every vector of a rule that has a query that query

            A rule that has a query is found from the vectors; each of its vectors must name that query, and a vector of
            such a rule that names none is listed.
            """
            with_query = {vector.rule for vector in vectors() if vector.query is not None}
            assert [vector.name for vector in vectors() if vector.rule in with_query and vector.query is None] == []

    class TestGivenANamingVector:
        @pytest.mark.parametrize("vector", vectors(), ids=str)
        def test_is_the_name_the_reference_implementation_gives_its_inputs(self, vector):
            """is the name the reference implementation gives its inputs

            The reference implementation is given the vector's inputs, or the file or document it names, and the name
            it gives is compared with the name the vector holds.
            """
            assert reference_name(vector) == vector.expected

    class TestGivenAnyNamingVector:
        def test_has_a_name_that_is_a_hash_in_one_of_three_forms_which_shows_none_of_its_inputs(self):
            """has a name that is a hash in one of three forms, which shows none of its inputs

            Each vector's name is compared with the three forms a name may take: a `urn:uuid:` of the version 8 kind, an
            `ni:` name of a SHA-256, or a file name with a SHA-256 after the `#`. A name that is none of them could show
            what it was made from, such as a patient's id or a hospital's address, and fails.
            """
            assert [v.expected for v in vectors()
                    if not any(re.fullmatch(shape, v.expected) for shape in NAME_SHAPES)] == []

    class TestGivenAVectorOfARuleThatHasAQuery:
        @pytest.mark.parametrize("vector", [v for v in vectors() if v.query is not None], ids=str)
        def test_is_the_one_name_its_rules_query_gives_on_oxigraph(self, vector):
            """is the one name its rule's query gives on Oxigraph

            The rule's published query is run on Oxigraph with the vector's inputs, and the one name it gives is compared
            with the name the vector holds.
            """
            substitutions = {Variable(f"input{n}"): OxigraphLiteral(value) for n, value in enumerate(vector.inputs, 1)}
            solutions = Store().query(vector.query.read_text(encoding="utf-8"), substitutions=substitutions)
            assert [solution["name"].value for solution in solutions] == [vector.expected]

    class TestGivenAVectorOfARuleOverLists:
        @pytest.mark.parametrize("vector", [v for v in vectors() if v.query is None and v.input is None], ids=str)
        def test_is_the_name_one_query_gives_over_its_inputs_each_list_flattened(self, vector):
            """is the name one query gives over its inputs, each list flattened to its count and its sorted members

            These rules have no query of their own, as their inputs are lists. Each list is flattened to its count and
            its sorted members, one query computes the name from the flattened inputs on Oxigraph, and the name it gives
            is compared with the name the vector holds.
            """
            inputs = flattened(vector.inputs)
            substitutions = {Variable(f"input{n}"): OxigraphLiteral(value) for n, value in enumerate(inputs, 1)}
            solutions = Store().query(v8_query(vector.rule, len(inputs)), substitutions=substitutions)
            assert [solution["name"].value for solution in solutions] == [vector.expected]

    class TestGivenAContentVector:
        @pytest.mark.parametrize("vector", CONTENT_VECTORS, ids=str)
        def test_is_the_sha_256_name_of_its_canonical_form_as_oxigraph_works_out_both(self, vector):
            """is the SHA-256 name of its canonical form, as Oxigraph works out both

            Oxigraph writes the vector's file in canonical form, RDFC-1.0, and that is compared with the canonical file
            the vector holds; a document is taken as its bytes. The SHA-256 of the text, which Oxigraph works out
            too, is written as an `ni:` name and compared with the name the vector holds.
            """
            if vector.rule == "DocumentNamingRule":
                text = vector.input.read_bytes().decode("utf-8")
            else:
                dataset = Dataset(parse(vector.input.read_bytes(), format=RdfFormat.N_TRIPLES))
                dataset.canonicalize(CanonicalizationAlgorithm.RDFC_1_0)
                text = "".join(sorted(
                    serialize(dataset, format=RdfFormat.N_QUADS).decode("utf-8").splitlines(keepends=True)))
                assert text == vector.canonical.read_text(encoding="utf-8")
            assert ni_from_hex(sparql_sha256(text)) == vector.expected

    class TestGivenAnyContentVectorThatIsNotADocument:
        def test_has_the_canonical_n_quads_the_reference_implementation_gives_its_input(self):
            """has the canonical N-Quads the reference implementation gives its input

            The reference implementation reads each vector's file and writes it in canonical form, and that is compared
            with the canonical file the vector holds. A name is a hash of this text, so a difference here is a
            different name for what should be one thing.
            """
            files = [v for v in CONTENT_VECTORS if v.rule != "DocumentNamingRule"]
            assert files and {v.name for v in files if naming.canonical_nquads(
                naming.content(v.input.read_text(encoding="utf-8"))) != v.canonical.read_text(encoding="utf-8")} == set()

    class TestGivenAnInputThatHoldsABar:
        def test_has_another_name_than_the_same_text_split_at_the_bar(self):
            """has another name than the same text split at the bar

            Two vectors of one rule have inputs that read alike once joined by a bar, one with the bar inside an input and
            the other with the text split at it. The names of the two are compared, and must differ, or the separator is
            not escaped and two things have one name.
            """
            by_name = {vector.name: vector for vector in vectors()}
            one, other = by_name["record-from-document-pipe-in-selector"], by_name["record-from-document-pipe-in-document"]
            assert "|".join(one.inputs) == "|".join(other.inputs)
            assert one.expected != other.expected

    class TestGivenABaseAddressVector:
        @pytest.mark.parametrize("name, given, expected", base_urls(), ids=[case[0] for case in base_urls()])
        def test_is_normalised_as_rfc_3986_section_6_says(self, name, given, expected):
            """is normalised as RFC 3986 section 6 says

            The reference implementation is given the address as written, and the address it gives back is compared with
            the one the vector holds: the form that RFC 3986 section 6 gives, so one server has one name.
            """
            assert naming.normalised_base_url(given) == expected

    class TestGivenAnyBaseAddressVectorWithAnIpLiteral:
        """given any base address vector whose normalised host is an IP literal"""

        def test_is_an_iri_to_oxigraph(self):
            """is an IRI to Oxigraph

            Each normalised address whose host is an IP address in brackets is given to Oxigraph as an IRI, which must
            accept it, and at least one is tried.
            """
            tried, refused = 0, []
            for name, _, expected in base_urls():
                if "[" in expected:
                    tried += 1
                    try:
                        NamedNode(expected)
                    except ValueError:
                        refused.append(name)
            assert tried and refused == []

    class TestGivenARefusedBaseAddressVector:
        @pytest.mark.parametrize("name, given", refused_base_urls(), ids=[case[0] for case in refused_base_urls()])
        def test_names_no_server(self, name, given):
            """names no server

            The address as written is given to the rule that names a server from an address, which must refuse it with a
            `ValueError` and not name a server from what is no address.
            """
            with pytest.raises(ValueError):
                naming.server_name(given)

        @pytest.mark.parametrize("name, given", refused_base_urls(), ids=[case[0] for case in refused_base_urls()])
        def test_is_refused_in_words_that_do_not_repeat_it(self, name, given):
            """is refused in words that do not repeat it

            The refusal's message is compared with the address as written, and with the address as Python shows it; it
            must hold neither, as an address may hold a token that would then be written to an error log.
            """
            with pytest.raises(ValueError) as refusal:
                naming.normalised_base_url(given)
            assert given not in str(refusal.value) and repr(given) not in str(refusal.value)

        @pytest.mark.parametrize("name", ["base-url-space", "base-url-nul", "base-url-del"])
        def test_is_no_iri_to_oxigraph_when_it_holds_a_forbidden_character(self, name):
            """is no IRI to Oxigraph when it holds a forbidden character

            An address with a space, a NUL or a DEL is given to Oxigraph as an IRI, which must refuse it, so the shape
            that finds such an address with SPARQL has an address to find.
            """
            with pytest.raises(ValueError):
                NamedNode(REFUSED[name])

        @pytest.mark.parametrize("name", ["base-url-bracket-unclosed", "base-url-bracket-unopened", "base-url-bracket-not-ip",
                                          "base-url-bracket-empty", "base-url-ipv6-zone"])
        def test_is_no_iri_to_oxigraph_when_its_bracketed_host_is_malformed(self, name):
            """is no IRI to Oxigraph when its bracketed host is malformed

            An address whose bracketed host is not closed, not opened, not an IP address, empty or an IPv6 address with a
            zone is given to Oxigraph as an IRI, which must refuse it.
            """
            with pytest.raises(ValueError):
                NamedNode(REFUSED[name])

        @pytest.mark.parametrize("name", ["base-url-query", "base-url-empty-query", "base-url-fragment",
                                          "base-url-empty-fragment"])
        def test_holds_the_query_or_fragment_mark_that_a_sparql_regex_finds(self, name):
            """holds the `?` or `#` that a SPARQL `REGEX` finds

            An address with a query or a fragment, empty or not, is given to Oxigraph with the regular expression
            `[?#]`, which must find the mark. This is how a shape that refuses such an address finds it in a pod.
            """
            [solution] = Store().query('SELECT ?given (REGEX(?given, "[?#]") AS ?holds) {}',
                                       substitutions={Variable("given"): OxigraphLiteral(REFUSED[name])})
            assert solution["holds"].value == "true"


class TestReferenceImplementation:
    """Reference implementation of the naming rules · tests/naming.py

    `tests/naming.py` has one function for each naming rule, and is what a runtime author ports. These are the things it
    does that no vector's name shows.
    """

    class TestNormalisedBaseUrl:
        """`normalised_base_url()`"""

        @pytest.mark.parametrize("given", ["https://s3cr3t@fhir.example.org/r4", "https://fhir.example.org/r4?tok=s3cr3t",
                                           "https://fhir.example.org:s3cr3t/r4", "https://s3cr3t%zz.example.org/r4",
                                           "https://[s3cr3t]/r4", "https://fhir.example.org/r4#s3cr3t"],
                                 ids=["in the user part", "in the query", "in the port", "in a malformed host",
                                      "in a bracketed host", "in the fragment"])
        def test_refuses_without_repeating_a_credential(self, given):
            """refuses without repeating a credential

            Given an address with a secret in its user part, its query, its port, a malformed host, a bracketed host or
            its fragment, the function refuses it with a `ValueError` whose message does not hold the secret.
            """
            with pytest.raises(ValueError) as refusal:
                naming.normalised_base_url(given)
            assert "s3cr3t" not in str(refusal.value)

    class TestCodeIri:
        """`code_iri()`"""

        def test_joins_a_code_to_its_stem_as_encode_for_uri_writes_it(self):
            """joins a code to its stem as Oxigraph's `ENCODE_FOR_URI` writes it

            Five codes, with reserved characters, parentheses, a leading zero and non-ASCII text, are each given to the
            function with a stem, and the IRI it gives is compared with the stem and what Oxigraph's `ENCODE_FOR_URI`
            gives the same code.
            """
            codes = ["NM_000249.4:c.2042C>T", "NM_000249.4:c.(116+1_117-1)_(380+1_381-1)del", "E11.65", "08",
                     "Ñ \U0001F95C~"]
            [solution] = Store().query("SELECT " + " ".join(f'(ENCODE_FOR_URI("{c}") AS ?c{n})' for n, c in enumerate(codes))
                                       + " {}")
            assert [naming.code_iri("s/", c) for c in codes] == ["s/" + solution[f"c{n}"].value for n in range(len(codes))]

    class TestVersionName:
        """`version_name()`"""

        def test_refuses_content_that_holds_a_blank_node(self):
            """refuses content that holds a blank node

            Given statements with a blank node as their subject, the function raises a `ValueError` that says so, as a
            blank node's label changes between readings and would change the name.
            """
            with pytest.raises(ValueError, match="blank node"):
                naming.version_name({Triple(BlankNode(), NamedNode("urn:x:p"), NamedNode("urn:x:o"))})

    class TestContent:
        """`content()`"""

        def test_keeps_each_turtle_number_as_written(self):
            """keeps each Turtle number as written

            Given Turtle with the numbers `007`, `+5`, `.5` and `-0`, the canonical form of what the function reads holds
            each number as it was written, with its datatype, so that `007` and `7` are not named alike.
            """
            triples = naming.content("<urn:x:s> <urn:x:p> 007, +5, .5, -0 .", "turtle")
            integer, decimal = "http://www.w3.org/2001/XMLSchema#integer", "http://www.w3.org/2001/XMLSchema#decimal"
            assert naming.canonical_nquads(triples) == "".join(sorted(
                f'<urn:x:s> <urn:x:p> "{form}"^^<{kind}> .\n'
                for form, kind in [("007", integer), ("+5", integer), (".5", decimal), ("-0", integer)]))
