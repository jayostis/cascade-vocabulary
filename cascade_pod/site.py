"""The static site that documents an example's pod: every page is questions, each shown with its prose, its answer over
the pod and its query, under the default lens."""

import hashlib
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import jinja2
from rdflib import Literal, URIRef
from rdflib.namespace import RDF, XSD

from . import derive, names, turtle, vocabulary
from .derived_files import LABEL_FILE, VIEW_FILES
from .pod import save
from .store import ENGINES

ENGINE = "oxigraph"
HERE = Path(__file__).absolute().parent
STYLESHEET = "site.css"
COPY = "pod/"
STATED = "pod/Which file states each thing"
CALLED = "pod/What everything is called"
CODE_SYSTEMS = {
    "http://snomed.info/sct/": "SNOMED CT",
    "http://www.nlm.nih.gov/research/umls/rxnorm/": "RxNorm",
    "http://hl7.org/fhir/sid/cvx/": "CVX",
    "http://hl7.org/fhir/sid/icd-10-cm/": "ICD-10-CM",
}


def page(iri):
    return hashlib.sha256(str(iri).encode("utf-8")).hexdigest() + ".html"


def shown(literal):
    """A literal as the site shows it: a time in UTC to the minute, anything else as written."""
    if literal.datatype != XSD.dateTime:
        return str(literal)
    moment = datetime.fromisoformat(str(literal))
    return (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC")


def written(added):
    """Each term the statements a step added write, a type's class or else the predicate, with how many write it."""
    return sorted(Counter(value if predicate == RDF.type else predicate for _, predicate, value in added).items())


def code(iri):
    """The code system and the code an IRI names, or None."""
    return next(((system, str(iri)[len(prefix):]) for prefix, system in CODE_SYSTEMS.items()
                 if str(iri).startswith(prefix)), None)


class Query:
    """A query of the vocabulary with its prose and, for a question, its name, the lens it was asked under and its
    answer: all its rows, or those whose column `about` is `thing`."""

    def __init__(self, relative, name=None, lens=vocabulary.DEFAULT_LENS, columns=(), rows=(), about=None, thing=None):
        self.relative, self.question, self.lens = relative, name, lens
        self.columns, self.rows, self.about, self.thing = list(columns), list(rows), about, thing
        self.text = vocabulary.query(relative)
        self.prose = vocabulary.prose(self.text)
        self.title = Path(relative).stem

    @property
    def shown(self):
        """The columns a reader sees: each label folded into the column it labels, and the one the rows are about
        left out."""
        return [c for c in self.columns if c != self.about and not (c.endswith("Label") and c[:-5] in self.columns)]

    def of(self, column, thing):
        return Query(self.relative, self.question, self.lens, self.columns,
                     [row for row in self.rows if row.get(column) == thing], column, thing)


def term_labels():
    terms = ENGINES[ENGINE]()
    vocabulary.load(terms)
    _, rows = terms.answer(vocabulary.query(vocabulary.questions()[CALLED]))
    return {row["thing"]: row["label"] for row in rows}


class Site:
    def __init__(self, example):
        self.example = example
        self.lenses = sorted(vocabulary.named("lenses"), key=lambda lens: lens != vocabulary.DEFAULT_LENS)
        self.stores = {lens: example.store(ENGINE, lens) for lens in self.lenses}
        self.answers = {lens: self.asked_under(lens) for lens in self.lenses}
        self.questions = self.answers[vocabulary.DEFAULT_LENS]
        self.terms = term_labels()
        self.names = {row["thing"]: row["label"] for row in self.questions[CALLED].rows}
        self.things = self.things_with_pages()
        self.views = [self.iri(path) for path in VIEW_FILES.values()]
        self.pipeline = {lens: self.steps_under(lens) for lens in self.lenses}
        self.built = self.view_files()
        self.copied = example.files() + example.derived
        self.copies = {self.iri(path): COPY + path for path in self.copied}
        self.pages = {thing: page(thing) for things in [*self.things.values(), self.views] for thing in things}
        self.step_writing = self.steps_writing_terms()
        self.stored_bytes = self.documents_stored()
        self.turtles = self.files_arrived_in()

    def iri(self, path):
        return URIRef(self.example.address + path)

    def asked_under(self, lens):
        return {name: Query(relative, name, lens, *self.stores[lens].answer(vocabulary.query(relative)))
                for name, relative in vocabulary.questions().items()}

    def things_with_pages(self):
        kinds = sorted({name.split("/")[0] for name in self.questions} - {"pod"})
        return {kind: list({row[kind]: None for name, question in self.questions.items() if name.startswith(kind + "/")
                            for row in question.rows if isinstance(row.get(kind), URIRef)}) for kind in kinds}

    def steps_under(self, lens):
        return [(Query(relative), added) for relative, added in derive.steps(self.example.loaded(ENGINE), lens)]

    def view_files(self):
        writers = {path: vocabulary.named("views")[view] for view, path in VIEW_FILES.items()} | {LABEL_FILE: "labels.rq"}
        held = self.stores[vocabulary.DEFAULT_LENS]
        return {self.iri(path): (Query(relative), len(held.triples(self.example.address + path)))
                for path, relative in writers.items()}

    def href(self, iri):
        preferred = (self.copies, self.pages, self.step_writing, self.stored_bytes, self.turtles)
        return next((targets[iri] for targets in preferred if iri in targets), None)

    def steps_writing_terms(self):
        found = {}
        for query, added in self.pipeline[vocabulary.DEFAULT_LENS]:
            for term, _ in written(added):
                found.setdefault(term, f"pipeline.html#{query.title}")
        return found

    def documents_stored(self):
        return {URIRef(names.document((self.example.pod / path).read_bytes())): COPY + path
                for path in self.copied if path.startswith("attachments/")}

    def files_arrived_in(self):
        """The copy of the first file each thing arrived in, for a thing a file states rather than only names."""
        found = {}
        for row in self.questions[STATED].rows:
            if not row["named"].toPython() and not row["rebuilt"].toPython():
                found.setdefault(row["thing"], self.copies[row["file"]])
        return found

    def about(self, thing, kind=None):
        """Which files state it, then each question of the kind, with only the rows about this one."""
        asked = [self.questions[STATED].of("thing", thing)]
        return asked + [q.of(kind, thing) for name, q in self.questions.items() if kind and name.startswith(kind + "/")]

    def environment(self):
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(HERE / "templates"), autoescape=True,
                                         undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        environment.filters.update(href=self.href, page=self.pages.get, turtle=self.turtles.get, shown=shown,
                                   written=written, code=code, nt=turtle.term,
                                   prefixed=lambda iri: turtle.prefixed(str(iri)))
        environment.tests.update(iri=lambda term: isinstance(term, URIRef), literal=lambda term: isinstance(term, Literal))
        environment.globals.update(
            site=self, example=self.example, terms=self.terms, copy=COPY, lens=vocabulary.DEFAULT_LENS,
            derived_graph=derive.DERIVED + vocabulary.DEFAULT_LENS,
            queries=vocabulary.QUERIES.relative_to(vocabulary.ROOT).as_posix(),
            folder=Path(os.path.relpath(self.example.folder, vocabulary.ROOT)).as_posix())
        return environment

    def files(self):
        environment = self.environment()

        def render(template, **context):
            return environment.get_template(template).render(**context).encode("utf-8")

        site = {"index.html": render("home.html", questions=self.questions),
                "pipeline.html": render("pipeline.html"),
                "not-shown.html": render("not-shown.html", hidden=self.questions["record/Why it is in no view"]),
                STYLESHEET: (HERE / STYLESHEET).read_bytes()}
        for view in self.views:
            site[page(view)] = render("view.html", view=view, questions=self.about(view))
        for kind, things in self.things.items():
            for thing in things:
                site[page(thing)] = render("thing.html", kind=kind, thing=thing, questions=self.about(thing, kind))
        return site | {COPY + path: (self.example.pod / path).read_bytes() for path in self.copied}


def build(example, out):
    files = Site(example).files()
    save(files, Path(out))
    print(f"{len(files)} files written to {out}")
    return 0
