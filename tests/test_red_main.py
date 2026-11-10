"""The red-main workflow's script: what it does about the latest run of each workflow on a repository's main, decided over
recorded GitHub API answers under tests/vectors/red-main/, and what it sends and reads when it runs."""

import importlib.util
import json
from datetime import datetime, timezone

import pytest

from contract import ROOT

VECTORS = ROOT / "tests" / "vectors" / "red-main"

spec = importlib.util.spec_from_file_location("red_main", ROOT / ".github" / "scripts" / "red_main.py")
red_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(red_main)


def vectors():
    return [pytest.param(json.loads(path.read_text(encoding="utf-8")), id=path.stem) for path in sorted(VECTORS.glob("*.json"))]


NOW = "2026-11-09T12:00:00Z"
JUST_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def decided(vector):
    now = vector.get("now", NOW)
    runs = {id: [{"created_at": now, **run} for run in listed] for id, listed in vector["runs"].items()}
    return red_main.decide(vector["repo"], vector["workflows"], runs, vector["jobs"], vector.get("annotations", {}),
                           vector["issues"], vector["comments"], red_main.parse_time(now))


CHECKS = {"body_has", "body_lacks", "body_count"}


@pytest.mark.parametrize("vector", vectors())
def test_a_vector_is_decided_as_it_says(vector):
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


def a_red_vector_with(messages):
    vector = json.loads((VECTORS / "a-red-run-says-what-its-annotations-say-is-red.json").read_text(encoding="utf-8"))
    vector["annotations"] = {"201": [{"annotation_level": "failure", "message": message} for message in messages]}
    return decided(vector)[0]["body"]


def test_what_failed_is_the_first_five_messages_each_cut_to_one_short_line_and_never_markup():
    body = a_red_vector_with(["one\n  two  \tthree", "x" * 500, "@maintainer ```", "four", "five", "six"])
    listed = body.split("```")[1].strip().splitlines()
    assert listed[0] == "one two three"
    assert len(listed) == 5 and all(len(line) <= 200 for line in listed)
    assert "six" not in body
    assert body.count("```") == 2 and "@maintainer" in listed[2]


def test_a_run_whose_only_failure_message_is_an_exit_code_says_nothing_about_what_failed():
    assert "What failed" not in a_red_vector_with(["Process completed with exit code 1.", "Process completed with exit code 137."])


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


def a_pod_of_repositories():
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


def test_it_reads_only_the_unarchived_cascade_repositories_of_the_owner_and_labels_before_opening():
    api = Fake(a_pod_of_repositories())
    errors = red_main.run(api)
    assert errors == []
    assert [(m, p) for m, p, _ in api.sent] == [
        ("POST", "/repos/jayostis/cascade-a/labels"),
        ("POST", "/repos/jayostis/cascade-a/issues"),
        ("POST", "/repos/jayostis/cascade-b/labels"),
        ("POST", "/repos/jayostis/cascade-b/issues"),
    ]
    assert api.sent[1][2]["labels"] == ["red-main"]


def a_red_repository(annotations):
    answers = a_pod_of_repositories()
    base = "/repos/jayostis/cascade-a"
    answers["/user/repos"] = answers["/user/repos"][:1]
    answers[f"{base}/actions/runs/5/jobs"] = {"jobs": [
        {"id": 50, "name": "ok", "conclusion": "success", "steps": []},
        {"id": 51, "name": "watch", "conclusion": "failure", "steps": [{"name": "echo", "conclusion": "failure"}]},
    ]}
    answers.update({f"{base}/check-runs/{id}/annotations": answer for id, answer in annotations.items()})
    return answers


def test_it_reads_the_annotations_of_the_failed_jobs_of_a_red_run_only():
    api = Fake(a_red_repository({51: [{"annotation_level": "failure", "message": "not checked: ncbi-clinvar"}]}))
    assert red_main.run(api) == []
    assert "not checked: ncbi-clinvar" in api.sent[1][2]["body"]
    assert "/repos/jayostis/cascade-a/check-runs/50/annotations" not in api.asked


def test_a_token_that_cannot_read_annotations_still_opens_the_issue_and_says_so_once():
    api = Fake(a_red_repository({}))
    get = api.get

    def refused(path, **params):
        if "/check-runs/" in path:
            raise red_main.GitHubError("GitHub answered 403 to GET " + path, 403)
        return get(path, **params)

    api.get = refused
    said = []
    assert red_main.run(api, say=said.append) == []
    assert ("POST", "/repos/jayostis/cascade-a/issues") in [(m, p) for m, p, _ in api.sent]
    assert "What failed" not in api.sent[1][2]["body"]
    assert len([line for line in said if "Checks" in line]) == 1


def test_the_messages_read_before_a_job_whose_annotations_are_refused_are_kept():
    answers = a_red_repository({51: [{"annotation_level": "failure", "message": "not checked: ncbi-clinvar"}]})
    answers["/repos/jayostis/cascade-a/actions/runs/5/jobs"]["jobs"].append({"id": 52, "name": "late", "conclusion": "failure", "steps": []})
    answers["/repos/jayostis/cascade-a/actions/runs/5/jobs"]["jobs"][0] = {"id": 50, "name": "first", "conclusion": "failure", "steps": []}
    answers["/repos/jayostis/cascade-a/check-runs/50/annotations"] = [{"annotation_level": "failure", "message": "first job said this"}]
    api = Fake(answers)
    get = api.get

    def refusing(path, **params):
        if path.endswith("/check-runs/51/annotations"):
            raise red_main.GitHubError("GitHub answered 403 to GET " + path + ": Resource not accessible by personal access token", 403)
        return get(path, **params)

    api.get = refusing
    assert red_main.run(api) == []
    assert "first job said this" in api.sent[1][2]["body"]


def test_a_secondary_rate_limit_is_an_error_for_the_repository_not_a_missing_checks_permission():
    api = Fake(a_red_repository({}))
    get = api.get

    def limited(path, **params):
        if "/check-runs/" in path:
            raise red_main.GitHubError("GitHub answered 403 to GET " + path + ": You have exceeded a secondary rate limit", 403)
        return get(path, **params)

    api.get = limited
    said = []
    errors = red_main.run(api, say=said.append)
    assert len(errors) == 1 and "rate limit" in errors[0]
    assert not any("Checks" in line for line in said)


def test_a_repository_it_cannot_reach_is_one_plain_line_and_the_others_are_still_read():
    api = Fake(a_pod_of_repositories(), refuse=("/repos/jayostis/cascade-a/",))
    errors = red_main.run(api)
    assert len(errors) == 1 and "\n" not in errors[0]
    assert errors[0].startswith("jayostis/cascade-a: GitHub answered 403")
    assert ("POST", "/repos/jayostis/cascade-b/issues") in [(m, p) for m, p, _ in api.sent]


def test_closing_comments_then_closes():
    answers = a_pod_of_repositories()
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
    assert [(m, p) for m, p, _ in api.sent][:2] == [
        ("POST", "/repos/jayostis/cascade-a/issues/7/comments"),
        ("PATCH", "/repos/jayostis/cascade-a/issues/7"),
    ]
    assert api.sent[1][2] == {"state": "closed", "state_reason": "completed"}


def test_without_its_token_it_says_so_in_one_line_and_reads_nothing(capsys):
    assert red_main.main({"GITHUB_REPOSITORY_OWNER": "jayostis", "RED_MAIN_TOKEN": ""}) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err.count("\n") == 1 and "Traceback" not in err
    assert "RED_MAIN_TOKEN" in err and "Issues" in err and "Actions" in err


def test_without_any_token_it_never_falls_back_to_the_workflow_token(capsys):
    assert red_main.main({"GITHUB_TOKEN": "workflow-token"}) == 1
    assert "workflow-token" not in capsys.readouterr().err


def test_a_refusal_never_prints_the_token(capsys, monkeypatch):
    def refuse(self, path, **params):
        raise red_main.GitHubError(f"GitHub answered 401 to GET {path}: Bad credentials")

    monkeypatch.setattr(red_main.Api, "pages", refuse)
    assert red_main.main({"RED_MAIN_TOKEN": "secret-value"}) == 1
    out, err = capsys.readouterr()
    assert "secret-value" not in out + err
    assert err.count("\n") == 1 and "Traceback" not in err


@pytest.mark.parametrize("failure", [ConnectionResetError("reset by peer"), json.JSONDecodeError("Expecting value\nline 1", "<html>", 0)])
def test_any_failure_in_one_repository_is_one_plain_line_and_the_others_are_still_read(failure):
    answers = a_pod_of_repositories()
    api = Fake(answers)
    get = api.get

    def flaky(path, **params):
        if path.startswith("/repos/jayostis/cascade-a/"):
            raise failure
        return get(path, **params)

    api.get = flaky
    errors = red_main.run(api)
    assert len(errors) == 1 and "\n" not in errors[0] and errors[0].startswith("jayostis/cascade-a: ")
    assert ("POST", "/repos/jayostis/cascade-b/issues") in [(m, p) for m, p, _ in api.sent]


def test_a_body_that_is_not_json_is_a_github_error(monkeypatch):
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
