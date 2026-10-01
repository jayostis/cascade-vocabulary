import argparse
import sys
from pathlib import Path

from . import Failure, write


def parser():
    top = argparse.ArgumentParser(prog="python -m cascade_pod")
    commands = top.add_subparsers(dest="command", required=True)
    commands.add_parser("write", help="files the story into pod/").add_argument("example", type=Path)
    return top


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        if arguments.command == "write":
            return write.run(arguments.example)
    except Failure as failure:
        print(f"cascade_pod {arguments.command}: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
