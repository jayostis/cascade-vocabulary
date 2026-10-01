"""The static site that documents an example's pod: every page is questions, each shown with its prose, its answer over
the pod and its query, under the default lens."""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import jinja2
from rdflib import Literal, URIRef
from rdflib.namespace import XSD

from . import derive, names, turtle, vocabulary
from .derived_files import LABEL_FILE, VIEW_FILES
from .pod import save
from .store import ENGINES, to_rdflib

ENGINE = "oxigraph"
HERE = Path(__file__).absolute().parent
STYLESHEET = "site.css"
COPY = "pod/"
ANY_THING = "thing"
STATED = "pod/Which file states each thing"
CALLED = "pod/What everything is called"


def page(iri):
    return hashlib.sha256(str(iri).encode("utf-8")).hexdigest() + ".html"


def shown(literal):
    """A literal as the site shows it: a time in UTC to the minute, anything else as written."""
    if literal.datatype != XSD.dateTime:
        return str(literal)
    moment = datetime.fromisoformat(str(literal))
    return (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC")


class Query:
    """A query of the vocabulary with its prose and, for a question, its name and its answer, all its rows or those
    about one thing."""

    def __init__(self, relative, columns=(), rows=(), about=None):
        self.relative, self.columns, self.rows, self.about = relative, list(columns), list(rows), about
        self.text = vocabulary.query(relative)
        self.prose = vocabulary.prose(self.text)
        self.title = Path(relative).stem
        self.question = relative[len("questions/"):-len(".rq")] if relative.startswith("questions/") else None

    @property
    def shown(self):
        """The columns a reader sees: each label folded into the column it labels, and the one the rows are about
        left out."""
        return [c for c in self.columns if c != self.about and not (c.endswith("Label") and c[:-5] in self.columns)]

    def of(self, column, thing):
        return Query(self.relative, self.columns, [row for row in self.rows if row.get(column) == thing], column)


class Site:
    def __init__(self, example):
        self.example = example
        held = example.store(ENGINE, vocabulary.DEFAULT_LENS)
        self.questions = {name: Query(relative, *self._answer(held, relative))
                          for name, relative in vocabulary.questions().items()}
        self.terms = self._terms()
        self.names = {row["thing"]: row["label"] for row in self.questions[CALLED].rows}
        self.things = {kind: self._things(kind) for kind in sorted({name.split("/")[0] for name in self.questions} - {"pod"})}
        writers = {path: vocabulary.named("views")[view] for view, path in VIEW_FILES.items()} | {LABEL_FILE: "labels.rq"}
        self.built = {URIRef(example.address + path): (Query(relative), len(held.triples(example.address + path)))
                      for path, relative in writers.items()}
        self.views = [URIRef(example.address + path) for path in VIEW_FILES.values()]
        self.pipeline = {lens: [(Query(relative), added) for relative, added in self._steps(lens)]
                         for lens in vocabulary.named("lenses")}
        self.copied = example.files() + example.derived
        self.links = self._links()

    @staticmethod
    def _answer(held, relative):
        columns, rows = held.answer(vocabulary.query(relative))
        return columns, [{name: to_rdflib(term) for name, term in row.items()} for row in rows]

    def _terms(self):
        terms = ENGINES[ENGINE]()
        vocabulary.load(terms)
        _, rows = self._answer(terms, vocabulary.questions()[CALLED])
        return {row["thing"]: row["label"] for row in rows}

    def _steps(self, lens):
        return [(relative, {tuple(map(to_rdflib, triple)) for triple in added})
                for relative, added in derive.steps(self.example.loaded(ENGINE), lens)]

    def _things(self, kind):
        found = {row[kind]: None for name, question in self.questions.items() if name.startswith(kind + "/")
                 for row in question.rows if isinstance(row.get(kind), URIRef)}
        return list(found)

    def _links(self):
        """Where a cell naming each IRI links to: its page, the step that writes it, its stored bytes, its copy if it is
        a file, or the first file that states it."""
        copies = {URIRef(self.example.address + path): COPY + path for path in self.copied}
        stated = {}
        for row in self.questions[STATED].rows:
            stated.setdefault(row["thing"], row["file"])
        stored = {URIRef(names.document((self.example.pod / path).read_bytes())): COPY + path
                  for path in self.copied if path.startswith("attachments/")}
        made = {}
        for query, added in self.pipeline[vocabulary.DEFAULT_LENS]:
            for _, predicate, _ in added:
                made.setdefault(predicate, f"pipeline.html#{query.title}")
        pages = {thing: page(thing) for things in [*self.things.values(), self.views] for thing in things}
        return {thing: copies[file] for thing, file in stated.items()} | copies | stored | made | pages

    def about(self, thing, kind=None):
        """Which files state it, each other pod question about any thing, then each question of the kind, with only the
        rows about this one."""
        anything = sorted((name != STATED, name) for name, q in self.questions.items()
                          if name.startswith("pod/") and ANY_THING in q.columns)
        asked = [(ANY_THING, self.questions[name]) for _, name in anything]
        asked += [(kind, q) for name, q in self.questions.items() if kind and name.startswith(kind + "/")]
        return [question.of(column, thing) for column, question in asked]

    def environment(self):
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(HERE / "templates"), autoescape=True,
                                         undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        environment.filters.update(href=self.links.get, shown=shown, nt=turtle.term,
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
