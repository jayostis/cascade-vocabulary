"""The answers `decide()` is held to are recorded GitHub API answers under tests/vectors/red-main/, one file for each."""

import importlib.util
import json
from datetime import datetime, timezone

import pytest

from contract import ROOT

VECTORS = ROOT / "tests" / "vectors" / "red-main"

_script = importlib.util.spec_from_file_location("red_main", ROOT / ".github" / "scripts" / "red_main.py")
red_main = importlib.util.module_from_spec(_script)
_script.loader.exec_module(red_main)


def vectors():
    return [pytest.param(json.loads(path.read_text(encoding="utf-8")), id=path.stem) for path in sorted(VECTORS.glob("*.json"))]


NOW = "2026-11-09T12:00:00Z"
JUST_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
CHECKS = {"body_has", "body_lacks", "body_count"}


def decided(vector):
    now = vector.get("now", NOW)
    runs = {id: [{"created_at": now, **run} for run in listed] for id, listed in vector["runs"].items()}
    return red_main.decide(vector["repo"], vector["workflows"], runs, vector["jobs"], vector.get("annotations", {}),
                           vector["issues"], vector["comments"], red_main.parse_time(now))


def a_red_vector_with(messages):
    vector = json.loads((VECTORS / "a-red-run-says-what-its-annotations-say-is-red.json").read_text(encoding="utf-8"))
    vector["annotations"] = {"201": [{"annotation_level": "failure", "message": message} for message in messages]}
    return decided(vector)[0]["body"]


def listed_in(body):
    return body.split("```")[1].strip().splitlines()


MANY_MESSAGES = ["one\n  two  \tthree", "x" * 500, "@maintainer ```", "four", "five", "six"]


class Fake:
    """GitHub as recorded: answers by path, remembers what was sent."""

    def __init__(self, answers, refuse=()):
        self.answers = answers
        self.refuse = refuse
        self.sent = []
        self.asked = []

    def get(self, path, **params):
        self.asked.append(path)
        return self.answers[path]

    def pages(self, path, key=None, **params):
        answer = self.answers[path]
        return answer[key] if key else answer

    def send(self, method, path, body=None):
        if any(path.startswith(prefix) for prefix in self.refuse):
            raise red_main.GitHubError(f"GitHub answered 403 to {method} {path}: Resource not accessible by personal access token")
        self.sent.append((method, path, body))
        return {"number": 9}


def refusing(api, matches, error):
    """The api, which raises `error(path)` for each path that `matches` and answers the others as it did."""
    get = api.get

    def refused(path, **params):
        if matches(path):
            raise error(path)
        return get(path, **params)

    api.get = refused
    return api


def an_owners_repositories():
    runs = {"workflow_runs": [{"id": 5, "event": "schedule", "status": "completed", "conclusion": "failure", "created_at": JUST_NOW,
                                "html_url": "https://github.com/jayostis/cascade-a/actions/runs/5"}]}
    workflows = {"workflows": [{"id": 1, "name": "nightly", "path": ".github/workflows/nightly.yml", "state": "active"}]}
    answers = {
        "/user/repos": [
            {"full_name": "jayostis/cascade-a", "name": "cascade-a", "archived": False},
            {"full_name": "jayostis/cascade-b", "name": "cascade-b", "archived": False},
            {"full_name": "jayostis/cascade-old", "name": "cascade-old", "archived": True},
            {"full_name": "jayostis/notes", "name": "notes", "archived": False},
            {"full_name": "someone/cascade-c", "name": "cascade-c", "archived": False},
        ],
    }
    for name in ("a", "b"):
        base = f"/repos/jayostis/cascade-{name}"
        answers[f"{base}/actions/workflows"] = workflows
        answers[f"{base}/actions/workflows/1/runs"] = runs
        answers[f"{base}/actions/runs/5/jobs"] = {"jobs": []}
        answers[f"{base}/issues"] = []
    return answers


def a_red_repository(annotations):
    answers = an_owners_repositories()
    base = "/repos/jayostis/cascade-a"
    answers["/user/repos"] = answers["/user/repos"][:1]
    answers[f"{base}/actions/runs/5/jobs"] = {"jobs": [
        {"id": 50, "name": "ok", "conclusion": "success", "steps": []},
        {"id": 51, "name": "watch", "conclusion": "failure", "steps": [{"name": "echo", "conclusion": "failure"}]},
    ]}
    answers.update({f"{base}/check-runs/{id}/annotations": answer for id, answer in annotations.items()})
    return answers


def run_refused_the_annotations(refusal=""):
    """A run over a red repository whose annotations GitHub refuses with a 403 and the words `refusal`: the api, what
    `run()` returned and the lines it said."""
    api = refusing(Fake(a_red_repository({})), lambda path: "/check-runs/" in path,
                   lambda path: red_main.GitHubError("GitHub answered 403 to GET " + path + refusal, 403))
    said = []
    return api, red_main.run(api, say=said.append), said


class TestChecksOfTheRedMainAlert:
    """Checks of the red-main alert · .github/scripts/red_main.py

    The red-main workflow reads the latest run of each workflow on main in every cascade repository, and keeps one issue
    open for each workflow whose latest run is red.
    """

    class TestDecide:
        """`decide()`"""

        @pytest.mark.parametrize("vector", vectors())
        def test_returns_the_actions_its_recorded_answers_expect(self, vector):
            """returns the actions its recorded answers expect

            Each vector under `tests/vectors/red-main/` holds GitHub's answers about one repository and the actions
            expected of them. The actions `decide()` returns are compared with those expected: how many, each one's fields
            that the vector names, and the pieces of text its body must hold, lack or hold a number of times.
            """
            actions = decided(vector)
            assert len(actions) == len(vector["expected"])
            for action, expected in zip(actions, vector["expected"]):
                assert {k: v for k, v in action.items() if k in expected} == {k: v for k, v in expected.items() if k not in CHECKS}
                for text in expected.get("body_has", []):
                    assert text in action["body"]
                for text in expected.get("body_lacks", []):
                    assert text not in action["body"]
                for text, count in expected.get("body_count", {}).items():
                    assert action["body"].count(text) == count

        def test_lists_the_first_five_failure_messages_and_no_more(self):
            """lists the first five failure messages and no more

            Given a red run whose annotations hold six failure messages, the issue's body lists five lines and the sixth
            message is nowhere in it.
            """
            body = a_red_vector_with(MANY_MESSAGES)
            assert len(listed_in(body)) == 5 and "six" not in body

        def test_cuts_each_message_to_one_line_of_at_most_200_characters(self):
            """cuts each message to one line of at most 200 characters

            Given messages with line breaks, tabs and a run of 500 characters, each listed line is one line, the white
            space of the first message is collapsed to single spaces, and no line is longer than 200 characters.
            """
            listed = listed_in(a_red_vector_with(MANY_MESSAGES))
            assert listed[0] == "one two three"
            assert all(len(line) <= 200 for line in listed)

        def test_keeps_a_messages_markup_inside_the_one_code_block(self):
            """keeps a message's markup inside the one code block

            Given a message that holds a mention and a code fence, the body has the one pair of code fences it opens with,
            so the message's own fence closes nothing, and the mention is a line inside the block.
            """
            body = a_red_vector_with(MANY_MESSAGES)
            assert body.count("```") == 2 and "@maintainer" in listed_in(body)[2]

        def test_says_nothing_of_what_failed_when_every_message_is_an_exit_code(self):
            """says nothing of what failed when every message is an exit code

            Given a red run whose only failure messages are `Process completed with exit code` and a number, the body
            has no `What failed` heading, because such a message says nothing of what failed.
            """
            body = a_red_vector_with(["Process completed with exit code 1.", "Process completed with exit code 137."])
            assert "What failed" not in body

    class TestRun:
        """`run()`"""

        def test_visits_only_the_owners_unarchived_cascade_repositories(self):
            """visits only the owner's unarchived `cascade-*` repositories

            Given five repositories of which two are the owner's unarchived `cascade-*` ones, the others being archived,
            not named `cascade-*` or someone else's, `run()` returns no error and sends to those two only: a label and an
            issue for each.
            """
            api = Fake(an_owners_repositories())
            assert red_main.run(api) == []
            assert [(method, path) for method, path, _ in api.sent] == [
                ("POST", "/repos/jayostis/cascade-a/labels"),
                ("POST", "/repos/jayostis/cascade-a/issues"),
                ("POST", "/repos/jayostis/cascade-b/labels"),
                ("POST", "/repos/jayostis/cascade-b/issues"),
            ]

        def test_opens_each_issue_with_the_red_main_label_which_it_makes_first(self):
            """opens each issue with the `red-main` label, which it makes first

            Given two repositories with a red workflow, `run()` posts the label to each repository before its issue, and
            each issue it posts carries the label `red-main`.
            """
            api = Fake(an_owners_repositories())
            red_main.run(api)
            sent = [(method, path) for method, path, _ in api.sent]
            for repository in ("cascade-a", "cascade-b"):
                assert sent.index(("POST", f"/repos/jayostis/{repository}/labels")) < sent.index(
                    ("POST", f"/repos/jayostis/{repository}/issues"))
            assert [body["labels"] for _, path, body in api.sent if path.endswith("/issues")] == [["red-main"]] * 2

        def test_puts_a_failed_jobs_annotation_in_the_issue(self):
            """puts a failed job's annotation in the issue

            Given a red run with a job that failed and carries an annotation, `run()` opens an issue whose body holds the
            annotation's message.
            """
            api = Fake(a_red_repository({51: [{"annotation_level": "failure", "message": "not checked: ncbi-clinvar"}]}))
            assert red_main.run(api) == []
            assert "not checked: ncbi-clinvar" in api.sent[1][2]["body"]

        def test_asks_for_no_annotation_of_a_job_that_passed(self):
            """asks for no annotation of a job that passed

            Given a red run with one job that passed and one that failed, `run()` asks GitHub for the annotations of the
            failed job and never for those of the job that passed.
            """
            api = Fake(a_red_repository({51: [{"annotation_level": "failure", "message": "not checked: ncbi-clinvar"}]}))
            assert red_main.run(api) == []
            assert "/repos/jayostis/cascade-a/check-runs/51/annotations" in api.asked
            assert "/repos/jayostis/cascade-a/check-runs/50/annotations" not in api.asked

        def test_opens_the_issue_when_it_is_refused_the_annotations(self):
            """opens the issue when it is refused the annotations

            Given a token that GitHub refuses the annotations of a job, `run()` returns no error and still posts the
            issue for the red workflow.
            """
            api, errors, _ = run_refused_the_annotations()
            assert errors == []
            assert ("POST", "/repos/jayostis/cascade-a/issues") in [(method, path) for method, path, _ in api.sent]

        def test_leaves_out_what_failed_when_it_is_refused_the_annotations(self):
            """leaves out what failed when it is refused the annotations

            Given a token that GitHub refuses the annotations of a job, the issue's body has no `What failed` heading.
            """
            api, errors, _ = run_refused_the_annotations()
            assert errors == []
            assert "What failed" not in api.sent[1][2]["body"]

        def test_says_once_that_github_refused_the_annotations(self):
            """says once that GitHub refused the annotations

            Given a token refused the annotations, `run()` says one line that names the refused annotations, and not one
            for each job or each refusal.
            """
            _, errors, said = run_refused_the_annotations()
            assert errors == []
            assert len([line for line in said if "annotations" in line]) == 1

        def test_keeps_the_messages_read_before_a_job_whose_annotations_are_refused(self):
            """keeps the messages read before a job whose annotations are refused

            Given three failed jobs where the first gives a message and the second is refused its annotations, the issue's
            body holds the first job's message.
            """
            answers = a_red_repository({51: [{"annotation_level": "failure", "message": "not checked: ncbi-clinvar"}]})
            jobs = answers["/repos/jayostis/cascade-a/actions/runs/5/jobs"]["jobs"]
            jobs.append({"id": 52, "name": "late", "conclusion": "failure", "steps": []})
            jobs[0] = {"id": 50, "name": "first", "conclusion": "failure", "steps": []}
            answers["/repos/jayostis/cascade-a/check-runs/50/annotations"] = [
                {"annotation_level": "failure", "message": "first job said this"}]
            api = refusing(Fake(answers), lambda path: path.endswith("/check-runs/51/annotations"),
                           lambda path: red_main.GitHubError(
                               "GitHub answered 403 to GET " + path + ": Resource not accessible by personal access token", 403))
            assert red_main.run(api) == []
            assert "first job said this" in api.sent[1][2]["body"]

        def test_returns_a_secondary_rate_limit_as_an_error_for_the_repository(self):
            """returns a secondary rate limit as an error for the repository

            Given a 403 whose words say that a secondary rate limit was exceeded, `run()` returns one error, which names
            the rate limit, in place of treating the refusal as a missing permission.
            """
            _, errors, _ = run_refused_the_annotations(": You have exceeded a secondary rate limit")
            assert len(errors) == 1 and "rate limit" in errors[0]

        def test_says_nothing_of_refused_annotations_when_the_refusal_is_a_rate_limit(self):
            """says nothing of refused annotations when the refusal is a rate limit

            Given a 403 whose words say that a secondary rate limit was exceeded, none of the lines `run()` says is about
            refused annotations.
            """
            _, _, said = run_refused_the_annotations(": You have exceeded a secondary rate limit")
            assert not any("annotations" in line for line in said)

        def test_returns_one_plain_line_for_a_repository_that_github_refuses(self):
            """returns one plain line for a repository that GitHub refuses

            Given a token that GitHub refuses everything about `cascade-a`, `run()` returns one error, a single line
            that begins with the repository and GitHub's answer.
            """
            errors = red_main.run(Fake(an_owners_repositories(), refuse=("/repos/jayostis/cascade-a/",)))
            assert len(errors) == 1 and "\n" not in errors[0]
            assert errors[0].startswith("jayostis/cascade-a: GitHub answered 403")

        def test_visits_the_other_repositories_after_one_is_refused(self):
            """visits the other repositories after one is refused

            Given a token that GitHub refuses everything about `cascade-a`, `run()` still posts the issue of `cascade-b`.
            """
            api = Fake(an_owners_repositories(), refuse=("/repos/jayostis/cascade-a/",))
            red_main.run(api)
            assert ("POST", "/repos/jayostis/cascade-b/issues") in [(method, path) for method, path, _ in api.sent]

        @pytest.mark.parametrize("failure", [ConnectionResetError("reset by peer"),
                                             json.JSONDecodeError("Expecting value\nline 1", "<html>", 0)],
                                 ids=["a connection reset", "an answer that is not JSON"])
        def test_returns_one_plain_line_for_a_repository_that_fails_and_visits_the_others(self, failure):
            """returns one plain line for a repository that fails, and visits the others

            Given a connection that fails for `cascade-a`, or an answer that is not JSON, `run()` returns one error, a
            single line that begins with the repository, and still posts the issue of `cascade-b`.
            """
            api = refusing(Fake(an_owners_repositories()), lambda path: path.startswith("/repos/jayostis/cascade-a/"),
                           lambda path: failure)
            errors = red_main.run(api)
            assert len(errors) == 1 and "\n" not in errors[0] and errors[0].startswith("jayostis/cascade-a: ")
            assert ("POST", "/repos/jayostis/cascade-b/issues") in [(method, path) for method, path, _ in api.sent]

        def test_comments_on_an_issue_and_then_closes_it_as_completed(self):
            """comments on an issue and then closes it as completed

            Given an open issue of a workflow whose latest run has passed, and a pull request that carries the same marker,
            `run()` posts a comment to the issue, then closes it with the reason `completed`; the pull request is left alone.
            """
            answers = an_owners_repositories()
            answers["/repos/jayostis/cascade-a/actions/workflows/1/runs"] = {"workflow_runs": [
                {"id": 6, "event": "schedule", "status": "completed", "conclusion": "success", "created_at": JUST_NOW,
                 "html_url": "https://github.com/jayostis/cascade-a/actions/runs/6"}]}
            answers["/repos/jayostis/cascade-a/issues"] = [
                {"number": 7, "body": "<!-- red-main: .github/workflows/nightly.yml -->\n<!-- run: 5 -->"},
                {"number": 8, "pull_request": {}, "body": "<!-- red-main: .github/workflows/nightly.yml -->"},
            ]
            answers["/repos/jayostis/cascade-a/issues/7/comments"] = []
            api = Fake(answers)
            red_main.run(api)
            assert [(method, path) for method, path, _ in api.sent][:2] == [
                ("POST", "/repos/jayostis/cascade-a/issues/7/comments"),
                ("PATCH", "/repos/jayostis/cascade-a/issues/7"),
            ]
            assert api.sent[1][2] == {"state": "closed", "state_reason": "completed"}

    class TestMain:
        """`main()`"""

        def test_returns_1_with_nothing_on_standard_output_when_its_token_is_not_set(self, capsys):
            """returns 1 with nothing on standard output when its token is not set

            Given an environment whose `RED_MAIN_TOKEN` is empty, `main()` returns 1 and prints nothing to standard output.
            """
            assert red_main.main({"GITHUB_REPOSITORY_OWNER": "jayostis", "RED_MAIN_TOKEN": ""}) == 1
            out, _ = capsys.readouterr()
            assert out == ""

        def test_prints_one_line_that_names_red_main_token_and_the_permissions_it_needs(self, capsys):
            """prints one line that names `RED_MAIN_TOKEN` and the permissions it needs

            Given an environment whose `RED_MAIN_TOKEN` is empty, the one line `main()` prints to standard error has no
            traceback and names the token, the Issues permission and the Actions permission.
            """
            red_main.main({"GITHUB_REPOSITORY_OWNER": "jayostis", "RED_MAIN_TOKEN": ""})
            _, err = capsys.readouterr()
            assert err.count("\n") == 1 and "Traceback" not in err
            assert "RED_MAIN_TOKEN" in err and "Issues" in err and "Actions" in err

        def test_returns_1_when_only_github_token_is_set_and_prints_no_part_of_it(self, capsys):
            """returns 1 when only `GITHUB_TOKEN` is set, and prints no part of it

            Given an environment that holds the workflow's `GITHUB_TOKEN` and no `RED_MAIN_TOKEN`, `main()` returns 1
            and does not use the workflow's token in its place; the token's value is in no line it prints.
            """
            assert red_main.main({"GITHUB_TOKEN": "workflow-token"}) == 1
            assert "workflow-token" not in capsys.readouterr().err

        def test_prints_one_line_without_the_token_when_github_refuses_it(self, capsys, monkeypatch):
            """prints one line without the token when GitHub refuses it

            Given a token that GitHub answers with 401, `main()` returns 1 and prints one line, with no traceback, in
            which the token's value appears nowhere on standard output or standard error.
            """
            def refuse(self, path, **params):
                raise red_main.GitHubError(f"GitHub answered 401 to GET {path}: Bad credentials")

            monkeypatch.setattr(red_main.Api, "pages", refuse)
            assert red_main.main({"RED_MAIN_TOKEN": "secret-value"}) == 1
            out, err = capsys.readouterr()
            assert "secret-value" not in out + err
            assert err.count("\n") == 1 and "Traceback" not in err

    class TestApiGet:
        """`Api.get()`"""

        def test_raises_github_error_for_a_body_that_is_not_json(self, monkeypatch):
            """raises `GitHubError` for a body that is not JSON

            Given a GitHub answer whose body is an HTML page from a gateway, `Api.get()` raises `GitHubError` in place of
            the JSON decoder's own error.
            """
            class Body:
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

                def read(self):
                    return b"<html>gateway</html>"

            monkeypatch.setattr(red_main.urllib.request, "urlopen", lambda *a, **k: Body())
            with pytest.raises(red_main.GitHubError):
                red_main.Api("t").get("/user/repos")
