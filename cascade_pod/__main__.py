import argparse
import sys
from pathlib import Path

from . import Failure, derive, graphdb, match, write
from .pod import Example
from .store import ENGINES


def parser():
    top = argparse.ArgumentParser(prog="python -m cascade_pod")
    commands = top.add_subparsers(dest="command", required=True)
    commands.add_parser("write", help="files the story into pod/").add_argument("example", type=Path)
    matching = commands.add_parser("match", help="writes the matcher's judgments")
    matching.add_argument("example", type=Path)
    matching.add_argument("--read-through", required=True)
    matching.add_argument("--takes")
    matching.add_argument("--at", required=True)
    matching.add_argument("--out", type=Path, required=True)
    build = commands.add_parser("build", help="writes the views, the labels, index.ttl and manifest.ttl")
    build.add_argument("example", type=Path)
    build.add_argument("--engine", choices=sorted(ENGINES), required=True)
    build.add_argument("--out", type=Path)
    load = commands.add_parser("graphdb", help="creates and fills the example's repository")
    load.add_argument("example", type=Path)
    load.add_argument("url", help="the GraphDB's base URL")
    return top


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        example = Example(arguments.example)
        if arguments.command == "write":
            return write.run(example)
        if arguments.command == "match":
            return match.run(example, arguments.read_through, arguments.takes, arguments.at, arguments.out)
        if arguments.command == "build":
            return derive.write(example, arguments.engine, arguments.out)
        if arguments.command == "graphdb":
            return graphdb.load(example, arguments.url)
    except Failure as failure:
        print(f"cascade_pod {arguments.command}: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
