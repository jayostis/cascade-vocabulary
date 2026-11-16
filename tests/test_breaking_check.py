"""A pull request's `## Breaking` section is read from the body of the event the workflow runs on."""

import importlib.util
import json

import pytest

from contract import ROOT

_script = importlib.util.spec_from_file_location("breaking_check", ROOT / ".github" / "scripts" / "breaking_check.py")
breaking_check = importlib.util.module_from_spec(_script)
_script.loader.exec_module(breaking_check)


def body(section):
    return f"Closes #1\n\n## Breaking\n{section}\n\n## Tests\nran\n"


REFUSED = [
    (None, "no `## Breaking` section"),
    ("", "no `## Breaking` section"),
    ("## Tests\nran\n", "no `## Breaking` section"),
    ("<!-- ## Breaking\nNone -->", "no `## Breaking` section"),
    (body(""), "empty"),
    (body("<!-- old -> new, or None -->"), "empty"),
    (body("- \n  \n"), "empty"),
    (body("a term was renamed"), '"a term was renamed" is not'),
    (body("None\n- a -> b"), "None beside lines"),
    (body("Nothing"), '"Nothing" is not'),
    (body("->"), '"->" is not'),
    (body("- ->"), '"->" is not'),
    (body("a ->"), '"a ->" is not'),
    (body("-> b"), '"-> b" is not'),
    (body("a ->" + chr(0xA0)), "is not"),
    (body("None" + chr(0x85)), "is not"),
    (body(chr(0xFF11) + ". None"), "is not"),
]


class TestChecksOfThePullRequestBodyCheck:
    """Checks of the check on a pull request's Breaking section · .github/scripts/breaking_check.py

    A pull request names each term, shape or named question it renames or removes under `## Breaking`, one
    `old -> new` or `old -> removed` line each, or says None, so that a consumer pinned to a build reads it in the
    build's notes.
    """

    class TestBreakingOf:
        """`breaking_of()`"""

        def test_returns_the_lines_of_the_section_each_without_its_bullet(self):
            """returns the lines of the section, each without its bullet

            Given lines written with a dash, a star and none, and a blank line between, they come back in order with
            the bullet gone and no problem.
            """
            lines, problem = breaking_check.breaking_of(
                body("- `mergedFrom` -> `entryMember`\n* `look` -> removed\n\n`claimed` -> `claimedProfiles`")
            )
            assert problem is None
            assert lines == ["`mergedFrom` -> `entryMember`", "`look` -> removed", "`claimed` -> `claimedProfiles`"]

        def test_returns_no_lines_and_no_problem_for_none(self):
            """returns no lines and no problem for None

            None, in any case and with a full stop, is the answer of a pull request that renames and removes nothing.
            """
            assert breaking_check.breaking_of(body("None")) == ([], None)
            assert breaking_check.breaking_of(body("<!-- say which -->\nnone.\n")) == ([], None)

        def test_reads_a_body_written_with_windows_line_ends(self):
            """reads a body written with Windows line ends

            A body from a browser form has carriage returns; the section is the same one.
            """
            assert breaking_check.breaking_of(body("- a -> b").replace("\n", "\r\n")) == (["a -> b"], None)

        def test_reads_a_body_written_with_lone_carriage_returns_a_byte_order_mark_and_unicode_line_ends(self):
            """reads a body written with lone carriage returns, a byte order mark and unicode line ends

            A lone carriage return, U+2028 and U+2029 end a line as a line feed does, and a byte order mark is dropped,
            as the runtime repository's reader of the same section does.
            """
            bom, separator, paragraph = chr(0xFEFF), chr(0x2028), chr(0x2029)
            assert breaking_check.breaking_of(f"{bom}## Breaking\r- a -> b\r- c -> d") == (["a -> b", "c -> d"], None)
            assert breaking_check.breaking_of(f"## Breaking{separator}- a -> b{paragraph}- c -> d") == (
                ["a -> b", "c -> d"],
                None,
            )
            assert breaking_check.breaking_of(f"## Breaking{separator}None{paragraph}## Tests") == ([], None)

        def test_strips_a_number_from_a_numbered_item_as_it_does_a_bullet(self):
            """strips a number from a numbered item as it does a bullet

            A line written `1. a -> b` comes back as `a -> b`.
            """
            assert breaking_check.breaking_of(body("1. a -> b\n2. c -> removed")) == (["a -> b", "c -> removed"], None)

        def test_reads_a_next_line_character_a_full_width_digit_and_an_arrow_beside_one_as_text(self):
            """reads a next line character, a full-width digit and an arrow beside one as text

            The runtime repository's reader, which counts only ASCII digits and a fixed set of spaces, reads them so too.
            """
            nel, one = chr(0x85), chr(0xFF11)
            assert breaking_check.breaking_of(body(f"a ->{nel}\n{nel}-> b")) == ([f"a ->{nel}", f"{nel}-> b"], None)
            assert breaking_check.breaking_of(body(f"{one}. a -> b")) == ([f"{one}. a -> b"], None)

        def test_stops_the_section_at_a_rule_or_a_depends_on_line(self):
            """stops the section at a rule or a Depends-On line

            A footer under a final Breaking heading is not a line of the section.
            """
            assert breaking_check.breaking_of("## Breaking\n- a -> b\n\n---\nGenerated with a tool\n") == (["a -> b"], None)
            assert breaking_check.breaking_of("## Breaking\nNone\nDepends-On: https://github.com/o/r/pull/1\n") == ([], None)
            assert breaking_check.breaking_of("## Breaking\n- a -> b\ndepends-on: https://github.com/o/r/pull/1") == (
                ["a -> b"],
                None,
            )

        def test_stops_the_section_at_the_next_heading(self):
            """stops the section at the next heading

            A line under a later heading, arrow or not, is not part of the section.
            """
            assert breaking_check.breaking_of("## Breaking\n- a -> b\n### Why\n- not a -> line\n") == (["a -> b"], None)

        @pytest.mark.parametrize("text,problem", REFUSED, ids=[f"{i}" for i in range(len(REFUSED))])
        def test_reports_a_problem_saying_what_is_wrong_for_each_body_the_check_must_refuse(self, text, problem):
            """reports a problem saying what is wrong for each body the check must refuse

            A missing section, an empty one, one holding only a comment, None beside lines and a line without an arrow
            each come back with no lines and a problem that names it.
            """
            lines, found = breaking_check.breaking_of(text)
            assert lines == []
            assert problem in found

    class TestMain:
        """`main()`"""

        @staticmethod
        def event(tmp_path, text):
            path = tmp_path / "event.json"
            path.write_text(json.dumps({"pull_request": {"body": text}}), encoding="utf-8")
            return {"GITHUB_EVENT_PATH": str(path)}

        def test_returns_0_for_a_body_that_lists_lines_or_says_none(self, tmp_path):
            """returns 0 for a body that lists lines or says None

            Given the event of a pull request whose body lists a line, and of one whose body says None, the exit code is 0.
            """
            assert breaking_check.main(self.event(tmp_path, body("- a -> b"))) == 0
            assert breaking_check.main(self.event(tmp_path, body("None"))) == 0

        def test_returns_1_saying_what_is_wrong_for_a_body_with_no_section_or_an_empty_one(self, tmp_path, capsys):
            """returns 1 saying what is wrong for a body with no section or an empty one

            Given the event of a pull request whose body has no section, whose section is empty, or has no body at all, the
            exit code is 1 and the problem is written to stderr.
            """
            assert breaking_check.main(self.event(tmp_path, "## Tests\nran")) == 1
            assert "no `## Breaking` section" in capsys.readouterr().err
            assert breaking_check.main(self.event(tmp_path, body(""))) == 1
            assert "empty" in capsys.readouterr().err
            assert breaking_check.main(self.event(tmp_path, None)) == 1
