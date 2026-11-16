"""Whether a pull request's body has a `## Breaking` section that lists `old -> new` lines or says None, read from the
body in the pull request event at GITHUB_EVENT_PATH. Exits 1 and says what is wrong. The runtime repository's
packages/cascade-runtime/pack/breaking.ts reads the same section, in the same way, for the notes of a build."""

import json
import os
import re
import sys

BOM = chr(0xFEFF)
LINE_END = re.compile("\r\n|[\n\r" + chr(0x2028) + chr(0x2029) + "]")
HEADING = re.compile(r"^##[ \t]+Breaking[ \t]*$")
ANY_HEADING = re.compile(r"^#{1,6}[ \t]")
RULE = re.compile(r"^-{3,}$")
DEPENDS_ON = re.compile(r"^Depends-On:", re.IGNORECASE)
ITEM = re.compile(r"^(?:[-*+]|\d+\.)[ \t]+")
NONE = re.compile(r"^none\.?$", re.IGNORECASE)


def breaking_of(body):
    """The lines of the section and the problem with it: the lines are empty when there is a problem or the body says None.

    The section ends at the next heading, a `---` rule or a `Depends-On:` line."""
    text = re.sub(r"<!--.*?-->", "", (body or "").replace(BOM, ""), flags=re.DOTALL)
    rows = LINE_END.split(text)
    start = next((i for i, row in enumerate(rows) if HEADING.match(row)), None)
    if start is None:
        return [], "the body has no `## Breaking` section"
    section = []
    for row in rows[start + 1:]:
        if ANY_HEADING.match(row) or RULE.match(row.strip()) or DEPENDS_ON.match(row.strip()):
            break
        section.append(row)
    lines = [ITEM.sub("", row.strip()).strip() for row in section]
    lines = [line for line in lines if line not in ("", "-", "*", "+")]
    if not lines:
        return [], "the `## Breaking` section is empty: list each `old -> new` or `old -> removed`, or write None"
    nones = sum(1 for line in lines if NONE.match(line))
    if nones == len(lines):
        return [], None
    if nones:
        return [], "the `## Breaking` section has None beside lines"
    loose = next((line for line in lines if "->" not in line), None)
    if loose is not None:
        return [], f'"{loose}" is not `old -> new` or `old -> removed`'
    return lines, None


def main(env=None):
    env = os.environ if env is None else env
    path = env.get("GITHUB_EVENT_PATH")
    if not path:
        print("GITHUB_EVENT_PATH is not set", file=sys.stderr)
        return 2
    with open(path, encoding="utf-8") as handle:
        event = json.load(handle)
    _, problem = breaking_of((event.get("pull_request") or {}).get("body"))
    if problem:
        print(problem, file=sys.stderr)
        if env.get("GITHUB_ACTIONS") == "true":
            print(f"::error::{problem}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
