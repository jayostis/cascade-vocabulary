import hashlib
import re

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from contract import CASCADE, KITS, LAYOUT, ROOT, feature_documents
from ontologies import shapes, terms

SOLID = "http://www.w3.org/ns/solid/terms#"
ZIP = URIRef("https://www.iana.org/assignments/media-types/application/zip")


def placement(graph, predicate):
    return next(graph.subjects(URIRef(predicate), None))


def naming_a_file_and_a_folder(graph):
    graph.add((placement(graph, SOLID + "instance"), URIRef(SOLID + "instanceContainer"), URIRef("urn:x:folder/")))


def naming_neither(graph):
    graph.remove((placement(graph, SOLID + "instanceContainer"), URIRef(SOLID + "instanceContainer"), None))


def naming_an_archive_format_by_a_string(graph):
    graph.add((placement(graph, SOLID + "instanceContainer"), CASCADE.holdsFilesInArchivesOfMediaType,
               Literal("application/zip")))


def naming_its_requirements_folder_by_a_string(graph):
    graph.add((placement(graph, SOLID + "instanceContainer"), CASCADE.holdsRequirementsForReadingAPod,
               Literal("true")))


def only_placement(graph, predicate, value):
    [entry] = graph.subjects(predicate, value)
    return entry


def requirement_file(graph, requirement):
    """O4: the path of the file that says the pod requires it, and that file's bytes."""
    folder = graph.value(only_placement(graph, CASCADE.holdsRequirementsForReadingAPod, Literal(True)),
                         URIRef(SOLID + "instanceContainer"))
    name = hashlib.sha256(str(requirement).encode("utf-8")).hexdigest()
    return f"{folder}{name}.ttl", f"<../> <{DCTERMS.requires}> <{requirement}> .\n"


def rule(code):
    """The description of the rule whose name begins with the code, as one paragraph."""
    return next(" ".join(child["rule"]["description"].split()) for _, document, _ in feature_documents()
                for child in document["feature"]["children"]
                if "rule" in child and child["rule"]["name"].startswith(f"{code}. "))


def conforms_to_its_shapes(graph):
    conforms, _, report = validate(graph, shacl_graph=Graph() + shapes(), advanced=True)
    return conforms, report


class TestWhereAPodKeepsItsFiles:
    """Where a pod keeps its files · runtime/pod-layout.ttl, conformance/*/expected/*.ttl

    The layout says, for each class of thing a pod holds, the file or the folder it is kept in; a runtime reads it with
    the pod's address as its base. A placement is one such line of the layout, and it names a file or a folder, never
    both.
    """

    class TestGivenTheLayout:
        def test_conforms_to_its_shapes(self):
            """conforms to its shapes

            The layout is read with a pod's address as its base and checked against the shapes in
            `ontologies/cascade.shapes.ttl`; the shapes' own report is the message if it does not conform.
            """
            conforms, report = conforms_to_its_shapes(Graph().parse(LAYOUT, publicID="https://pod.example/"))
            assert conforms, report

        def test_gives_one_folder_of_zip_archives_and_places_nothing_else_in_it(self):
            """gives one folder of ZIP archives, and places nothing else in it

            Exactly one placement states `cascade:holdsFilesInArchivesOfMediaType`: it gives a folder by
            `solid:instanceContainer`, its media type is ZIP's, and it states nothing else of a placement. No
            other placement's file or folder is at or under that folder, so a file held in an archive is placed by its
            own path, never by the archive's.
            """
            graph = Graph().parse(LAYOUT, publicID="https://pod.example/")
            archives = list(graph.subjects(CASCADE.holdsFilesInArchivesOfMediaType, None))
            assert len(archives) == 1
            [entry] = archives
            folder = graph.value(entry, URIRef(SOLID + "instanceContainer"))
            assert folder is not None and str(folder).endswith("/")
            assert set(graph.objects(entry, CASCADE.holdsFilesInArchivesOfMediaType)) == {ZIP}
            allowed = {RDF.type, URIRef(SOLID + "instanceContainer"), CASCADE.holdsFilesInArchivesOfMediaType}
            assert sorted(str(predicate) for predicate in set(graph.predicates(entry)) - allowed) == []
            others = {place for other in graph.subjects(RDF.type, CASCADE.Placement) if other != entry
                      for predicate in ("instance", "instanceContainer")
                      for place in graph.objects(other, URIRef(SOLID + predicate))}
            assert sorted(str(place) for place in others if str(place).startswith(str(folder))) == []

        def test_gives_one_folder_of_requirements_for_reading_the_pod_and_places_nothing_else_in_it(self):
            """gives one folder of requirements for reading the pod, and places nothing else in it

            Exactly one placement states `cascade:holdsRequirementsForReadingAPod true`: it gives a folder one level
            below the pod by `solid:instanceContainer`, and states nothing else of a placement. No other placement's file
            or folder is at or under it, and it is not under the archives' folder, so no archive can hold its files (X1).
            """
            graph = Graph().parse(LAYOUT, publicID="https://pod.example/")
            entry = only_placement(graph, CASCADE.holdsRequirementsForReadingAPod, Literal(True))
            folder = str(graph.value(entry, URIRef(SOLID + "instanceContainer")))
            assert re.fullmatch(r"https://pod\.example/[a-z-]+/", folder)
            allowed = {RDF.type, URIRef(SOLID + "instanceContainer"), CASCADE.holdsRequirementsForReadingAPod}
            assert sorted(str(predicate) for predicate in set(graph.predicates(entry)) - allowed) == []
            others = {str(place) for other in graph.subjects(RDF.type, CASCADE.Placement) if other != entry
                      for predicate in ("instance", "instanceContainer")
                      for place in graph.objects(other, URIRef(SOLID + predicate))}
            assert sorted(place for place in others if place.startswith(folder) or folder.startswith(place)) == []

    class TestGivenEveryRequirementForReadingAPod:
        def test_has_a_file_named_by_its_iris_hash_that_reads_as_the_pod_requiring_it(self):
            """has a file named by the SHA-256 of its IRI, whose bytes read as the pod requiring it

            For each `cascade:RequirementForReadingAPod` the ontology declares, `cascade:ReadingFilesHeldInArchives`
            among them, its file is the SHA-256 of its IRI in UTF-8, in lowercase hex, adding `.ttl`, in the
            layout's requirements folder (N9, O4), and O4 gives that path and those bytes; the bytes, read as Turtle at
            that path, are one statement, the pod's address `dct:requires` it, so they are the same in every pod.
            """
            requirements = set(terms().subjects(RDF.type, CASCADE.RequirementForReadingAPod))
            assert CASCADE.ReadingFilesHeldInArchives in requirements
            layout = Graph().parse(LAYOUT, publicID="https://pod.example/")
            for requirement in sorted(requirements):
                path, text = requirement_file(layout, requirement)
                assert path.removeprefix("https://pod.example/") in rule("O4") and text.removesuffix("\n") in rule("O4")
                read = Graph().parse(data=text, format="turtle", publicID=path)
                assert set(read) == {(URIRef("https://pod.example/"), DCTERMS.requires, requirement)}

    class TestGivenTheLayoutWithOnePlacementChanged:
        @pytest.mark.parametrize("breaking", [naming_a_file_and_a_folder, naming_neither,
                                              naming_an_archive_format_by_a_string,
                                              naming_its_requirements_folder_by_a_string],
                                 ids=["a file and a folder", "neither", "its archives' media type by a string",
                                      "its requirements folder by a string"])
        def test_fails_its_shapes_when_the_placement_names(self, breaking):
            """fails its shapes when the placement names

            One placement of the layout is changed to name both a file and a folder, or to name neither; the layout is
            then checked against the shapes and must not conform.
            """
            graph = Graph().parse(LAYOUT, publicID="https://pod.example/")
            breaking(graph)
            conforms, _ = conforms_to_its_shapes(graph)
            assert not conforms

    class TestGivenAnyViewAKitExpects:
        def test_holds_no_iri_at_its_pods_address(self):
            """holds no IRI at its pod's address

            Each IRI a view file holds, as its bytes write it, is compared with the address of the pod its kit is
            about, which `people.ttl` gives as the kit's storage; a view that holds an IRI under that address fails,
            as only that pod's address could match it.
            """
            holding = []
            for kit in KITS:
                address = re.search(r"pim:storage <([^>]+)>",
                                    (kit / "scripted-input" / "people.ttl").read_text(encoding="utf-8"))[1]
                holding += [view.relative_to(ROOT).as_posix() for view in sorted((kit / "expected").glob("*.ttl"))
                            if f"<{address}" in view.read_text(encoding="utf-8")]
            assert KITS and holding == []
