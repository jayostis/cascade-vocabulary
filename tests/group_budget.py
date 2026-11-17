"""A budget for the seconds one xdist_group takes. A group runs on one worker, so the longest group is the shortest a
parallel run can be; `--group-budget SECONDS` fails a run in which a group takes longer, and names it. `--budget-groups`
limits the check to the groups it lists, comma-separated; with none, every group is checked. A run with no `-n` has no
groups: a worker names a case's group by the `@group` pytest-xdist adds to its id."""

from collections import defaultdict

CASES = []


def group_of(nodeid):
    return nodeid.rpartition("@")[2] if "@" in nodeid else None


def over_budget(seconds_by_case, budget, groups=()):
    """Each group, of those listed or of all, whose cases' seconds add up to more than the budget, with its seconds,
    longest first. A group `name/part` is a part of `name`: listing `name` lists each of its parts, each by itself. A
    case id with no `@group` has no group and is not counted."""
    totals = defaultdict(float)
    for nodeid, seconds in seconds_by_case:
        group = group_of(nodeid)
        if group is not None and (not groups or group in groups or group.partition("/")[0] in groups):
            totals[group] += seconds
    return sorted(((group, seconds) for group, seconds in totals.items() if seconds > budget), key=lambda found: -found[1])


def unseen(seconds_by_case, groups=()):
    """What the budget could not check: each listed group no case ran in, or, with none listed and no case in any
    group, `any group`; so a run with no `-n`, or a name misspelt, is not one that passed."""
    seen = {group for nodeid, _ in seconds_by_case if (group := group_of(nodeid)) is not None}
    seen |= {group.partition("/")[0] for group in seen}
    return [group for group in groups if group not in seen] or ([] if seen or groups else ["any group"])


def pytest_addoption(parser):
    parser.addoption("--group-budget", type=float, default=None, metavar="SECONDS",
                     help="fail the run when an xdist group takes more seconds than this")
    parser.addoption("--budget-groups", default="", metavar="NAMES",
                     help="comma-separated xdist groups the budget applies to; default every group")


def pytest_runtest_logreport(report):
    CASES.append((report.nodeid, report.duration))


def pytest_sessionfinish(session):
    budget = session.config.getoption("--group-budget")
    if budget is None or hasattr(session.config, "workerinput"):
        return
    groups = [name for name in session.config.getoption("--budget-groups").split(",") if name]
    session.config.over_budget = over_budget(CASES, budget, groups)
    session.config.unchecked = unseen(CASES, groups)
    if session.config.over_budget or session.config.unchecked:
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter, config):
    if getattr(config, "over_budget", None):
        terminalreporter.section("xdist groups over the budget")
        for group, seconds in config.over_budget:
            terminalreporter.write_line(f"{seconds:7.1f} s  {group}  (budget {config.getoption('--group-budget'):g} s)")
    if getattr(config, "unchecked", None):
        terminalreporter.section("xdist groups the budget could not check")
        terminalreporter.write_line("no case ran in: " + ", ".join(config.unchecked))
