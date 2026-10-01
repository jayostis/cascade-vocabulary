import argparse
import sys
from pathlib import Path

from . import Failure, ask, derive, graphdb, match, vocabulary, write
from .pod import Example
from .store import ENGINES


def parser():
    top = argparse.ArgumentParser(prog="python -m cascade_pod")
    commands = top.add_subparsers(dest="command", required=True)

    def command(name, help, run):
        sub = commands.add_parser(name, help=help)
        sub.add_argument("example", type=Path)
        sub.set_defaults(run=run)
        return sub

    command("write", "files the story into pod/", lambda example, _: write.run(example))
    matching = command("match", "writes the matcher's judgments",
                       lambda example, a: match.run(example, a.read_through, a.takes, a.at, a.out))
    matching.add_argument("--read-through", required=True)
    matching.add_argument("--takes")
    matching.add_argument("--at", required=True)
    matching.add_argument("--out", type=Path, required=True)
    build = command("build", "writes the views, the labels, index.ttl and manifest.ttl",
                    lambda example, a: derive.write(example, a.engine, a.out))
    build.add_argument("--engine", choices=sorted(ENGINES), required=True)
    build.add_argument("--out", type=Path)
    command("graphdb", "creates and fills the example's repository",
            lambda example, a: graphdb.load(example, a.url)).add_argument("url", help="the GraphDB's base URL")
    question = command("ask", "prints one question's rows",
                       lambda example, a: ask.ask(example, a.question, a.lens, a.engine))
    question.add_argument("question", help='its path under questions/, such as "record/Why it is in no view"')
    question.add_argument("--lens", choices=sorted(vocabulary.named("lenses")), default=vocabulary.DEFAULT_LENS)
    question.add_argument("--engine", choices=sorted(ENGINES), default="oxigraph")
    return top


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        return arguments.run(Example(arguments.example), arguments)
    except Failure as failure:
        print(f"cascade_pod {arguments.command}: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
