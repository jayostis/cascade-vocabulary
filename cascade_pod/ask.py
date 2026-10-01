"""Asks one question of an example's pod, by its path under questions/, and prints a line for each row."""

import sys

from . import Failure, derive, store, turtle, vocabulary


def line(row):
    return "\t".join(f"?{name}={turtle.term(store.to_rdflib(term))}" for name, term in row.items())


def ask(example, question, lens, engine):
    questions = vocabulary.questions()
    if question not in questions:
        raise Failure(f"no question {question}; there are {', '.join(sorted(questions))}")
    held = derive.build(example, engine, lens).store
    for row in held.select(vocabulary.query(questions[question])):
        sys.stdout.buffer.write((line(row) + "\n").encode("utf-8"))
    return 0
