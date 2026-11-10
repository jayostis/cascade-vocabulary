"""Reads the latest run of every workflow on main in each jayostis/cascade-* repository, and keeps one issue there open
for each workflow whose latest run is red: opened on the first red run, commented on once for each later red run, closed
when the latest run is green. An issue is recognised by its label and by a marker in its body naming the workflow."""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

OWNER = "jayostis"
LABEL = "red-main"
RED = {"failure", "timed_out", "startup_failure"}
PULL_REQUEST_EVENTS = {"pull_request", "pull_request_target"}
WORKFLOW_MARKER = re.compile(r"<!-- red-main: (.+?) -->")
MISSING_TOKEN = (
    f"RED_MAIN_TOKEN is not set: create a fine-grained personal access token with Issues read and write, Actions read "
    f"and Metadata read on the {OWNER}/cascade-* repositories, and add it as a repository secret named RED_MAIN_TOKEN."
)


class GitHubError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def latest_run(runs):
    return next((run for run in runs if run["status"] == "completed" and run["event"] not in PULL_REQUEST_EVENTS), None)


def first_failing_step(jobs):
    for job in jobs:
        if job.get("conclusion") == "failure":
            step = next((s for s in job.get("steps", []) if s.get("conclusion") == "failure"), None)
            return f"{job['name']} / {step['name']}" if step else job["name"]
    return "not reported"


def run_marker(run):
    return f"<!-- run: {run['id']} -->"


def decide(repo, workflows, runs, jobs, issues, comments):
    """What to do in one repository, from GitHub's answers: its workflows, each workflow's recent completed runs on main
    by workflow id, the jobs of each red latest run by run id, its open issues labelled red-main, and their comments by
    issue number."""
    opened = {}
    for issue in sorted(issues, key=lambda issue: issue["number"]):
        found = WORKFLOW_MARKER.search(issue.get("body") or "")
        if found:
            opened.setdefault(found.group(1), []).append(issue)

    actions = []
    active = set()
    for workflow in workflows:
        if workflow["state"] != "active":
            continue
        active.add(workflow["path"])
        run = latest_run(runs.get(str(workflow["id"]), []))
        if run is None:
            continue
        mine = opened.get(workflow["path"], [])
        if run["conclusion"] in RED:
            step = first_failing_step(jobs.get(str(run["id"]), []))
            what = f"The latest run of the workflow `{workflow['name']}` ({workflow['path']}) on `main` failed.\n\n"
            where = f"- Run: {run['html_url']}\n- First failing step: `{step}`\n"
            if not mine:
                actions.append({
                    "do": "open", "repo": repo, "labels": [LABEL], "title": f"{workflow['name']} is red on main",
                    "body": f"<!-- red-main: {workflow['path']} -->\n{run_marker(run)}\n{what}{where}\n"
                            f"This issue is kept by the red-main workflow of {OWNER}/cascade-vocabulary. It gets one "
                            f"comment for each later red run and closes when the latest run is green.",
                })
            elif not any(run_marker(run) in (text["body"] or "") for text in [mine[0], *comments.get(str(mine[0]["number"]), [])]):
                actions.append({
                    "do": "comment", "repo": repo, "number": mine[0]["number"],
                    "body": f"{run_marker(run)}\nStill red on `main`.\n\n{where}",
                })
        elif run["conclusion"] == "success":
            actions += [{
                "do": "close", "repo": repo, "number": issue["number"],
                "body": f"{run_marker(run)}\nGreen again on `main`: {run['html_url']}",
            } for issue in mine]

    for path, gone in opened.items():
        if path not in active:
            actions += [{
                "do": "close", "repo": repo, "number": issue["number"],
                "body": f"`{path}` is no longer an active workflow of this repository, so nothing keeps this issue red.",
            } for issue in gone]
    return actions


class Api:
    def __init__(self, token):
        self.token = token

    def request(self, method, path, params=None, body=None):
        url = "https://api.github.com" + path + (f"?{urllib.parse.urlencode(params)}" if params else "")
        request = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None, headers={
            "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "red-main-watch",
        })
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                text = response.read().decode()
        except urllib.error.HTTPError as error:
            try:
                message = json.loads(error.read().decode()).get("message", error.reason)
            except (ValueError, AttributeError):
                message = error.reason
            raise GitHubError(f"GitHub answered {error.code} to {method} {path}: {' '.join(str(message).split())[:200]}", error.code) from None
        except (urllib.error.URLError, TimeoutError) as error:
            raise GitHubError(f"GitHub could not be reached for {method} {path}: {getattr(error, 'reason', error)}") from None
        return json.loads(text) if text else {}

    def get(self, path, **params):
        return self.request("GET", path, params)

    def pages(self, path, key=None, **params):
        found = []
        for page in range(1, 100):
            answer = self.get(path, per_page=100, page=page, **params)
            items = answer[key] if key else answer
            found += items
            if len(items) < 100:
                return found
        raise GitHubError(f"GET {path} has more than 99 pages")

    def send(self, method, path, body=None):
        return self.request(method, path, body=body)


def perform(api, repo, actions):
    base = f"/repos/{repo}"
    said = []
    labelled = False
    for action in actions:
        if action["do"] == "open":
            if not labelled:
                try:
                    api.send("POST", f"{base}/labels", {"name": LABEL, "color": "d73a4a", "description": "The latest run of a workflow on main is red"})
                except GitHubError as error:
                    if error.status != 422:
                        raise
                labelled = True
            number = api.send("POST", f"{base}/issues", {k: action[k] for k in ("title", "body", "labels")}).get("number")
            said.append(f"{repo}: opened #{number}, {action['title']}")
        else:
            api.send("POST", f"{base}/issues/{action['number']}/comments", {"body": action["body"]})
            if action["do"] == "close":
                api.send("PATCH", f"{base}/issues/{action['number']}", {"state": "closed", "state_reason": "completed"})
            said.append(f"{repo}: {'closed' if action['do'] == 'close' else 'commented on'} #{action['number']}")
    return said


def visit(api, repo):
    base = f"/repos/{repo}"
    workflows = api.pages(f"{base}/actions/workflows", key="workflows")
    runs, jobs = {}, {}
    for workflow in workflows:
        if workflow["state"] != "active":
            continue
        listed = api.get(f"{base}/actions/workflows/{workflow['id']}/runs", branch="main", status="completed", per_page=10)
        runs[str(workflow["id"])] = listed["workflow_runs"]
        run = latest_run(listed["workflow_runs"])
        if run and run["conclusion"] in RED:
            jobs[str(run["id"])] = api.get(f"{base}/actions/runs/{run['id']}/jobs", filter="latest", per_page=100)["jobs"]
    issues = [i for i in api.pages(f"{base}/issues", labels=LABEL, state="open") if "pull_request" not in i]
    comments = {str(i["number"]): api.pages(f"{base}/issues/{i['number']}/comments") for i in issues}
    return perform(api, repo, decide(repo, workflows, runs, jobs, issues, comments))


def run(api, say=print):
    """Visits every repository; a refusal in one is a line in the returned errors and the others are still visited."""
    errors = []
    for repo in api.pages("/user/repos", affiliation="owner"):
        if repo["archived"] or repo["full_name"].split("/")[0] != OWNER or not repo["name"].startswith("cascade-"):
            continue
        try:
            for line in visit(api, repo["full_name"]):
                say(line)
        except GitHubError as error:
            errors.append(f"{repo['full_name']}: {error}")
    return errors


def main(env=None):
    env = os.environ if env is None else env
    token = env.get("RED_MAIN_TOKEN", "").strip()
    if not token:
        print(MISSING_TOKEN, file=sys.stderr)
        return 1
    try:
        errors = run(Api(token))
    except GitHubError as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
