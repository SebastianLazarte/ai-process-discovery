"""Set up the GitHub side of the repository with the gh CLI.

Creates labels, milestones (one per release, B0-B13), one issue per backlog item in
docs/requirements.toml, a Project board with Points and Priority fields, the `main` ruleset
and the security settings. Safe to re-run: existing labels, milestones and issues are left
alone. With --sync, existing issues are brought back in line with the file (title, epic,
story, criteria, milestone, area and priority labels); criteria already ticked stay ticked.
The board's Sprint field (an iteration field) is created by hand: see docs/CLAUDE.md.

    uv run python scripts/bootstrap_github.py --repo OWNER/NAME --dry-run
    uv run python scripts/bootstrap_github.py --repo OWNER/NAME
    uv run python scripts/bootstrap_github.py --repo OWNER/NAME --sync --dry-run
"""

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MILESTONES = {
    "B0": "Repository, CI/CD and planning",
    "B1": "Domain and metrics",
    "B2": "Deterministic scoring",
    "B3": "Business case",
    "B4": "Persistence and API",
    "B5": "LLM layer",
    "B6": "Reconciliation",
    "B7": "Blueprint",
    "B8": "Streamlit UI",
    "B9": "Docs and 1.0 release",
    "B10": "Web client",
    "B11": "Production deployment",
    "B12": "Next.js frontend",
    "B13": "Quality gauntlet",
}

LABELS = {
    "type:feature": "1d76db",
    "type:bug": "d73a4a",
    "type:docs": "0075ca",
    "type:ci": "5319e7",
    "type:chore": "cfd3d7",
    "req": "fbca04",
    **{
        f"area:{area}": "c5def5"
        for area in ("domain", "api", "llm", "reconciliation", "blueprint", "ui", "infra")
    },
    "priority:must": "b60205",
    "priority:should": "d93f0b",
    "priority:could": "0e8a16",
    "priority:wont": "cfd3d7",
}

PRIORITY_NAMES = {"must": "Must", "should": "Should", "could": "Could", "wont": "Won't"}
MANAGED_LABEL_PREFIXES = ("area:", "priority:")

REQUIRED_CHECKS = [
    "quality",
    "web",
    "frontend",
    "test (3.12)",
    "test (3.13)",
    "test-postgres",
    "docker",
    "pr-title",
]


class Runner:
    def __init__(self, repo: str, dry_run: bool) -> None:
        self.repo = repo
        self.dry_run = dry_run

    def gh(self, *args: str, input_json: dict[str, Any] | None = None, read: bool = False) -> str:
        command = ["gh", *args]
        if self.dry_run and not read:
            sys.stdout.write(f"[dry-run] {' '.join(command)}\n")
            return ""
        try:
            result = subprocess.run(
                command,
                input=json.dumps(input_json) if input_json else None,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            if self.dry_run:
                return ""  # dry run without gh installed: treat the repo as empty
            raise SystemExit("gh CLI not found. Install it and run `gh auth login`.") from None
        if result.returncode != 0:
            raise SystemExit(f"gh {' '.join(args)} failed:\n{result.stderr}")
        return result.stdout

    def api(self, method: str, path: str, body: dict[str, Any] | None = None) -> str:
        args = ["api", "-X", method, path]
        if body is not None:
            args += ["--input", "-"]
        return self.gh(*args, input_json=body)


def load_requirements() -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    """Epics by id and backlog items, in file order."""
    data = tomllib.loads((ROOT / "docs" / "requirements.toml").read_text(encoding="utf-8"))
    return data["user_requirements"], data["requirement"]


def user_story(story: dict[str, str]) -> str:
    role = story["as_a"]
    article = "an" if role[0].lower() in "aeiou" else "a"
    return f"As {article} {role}, I want {story['i_want']}, so that {story['so_that']}."


_TICKED = re.compile(r"^- \[[xX]\] (.+)$")


def ticked_criteria(body: str) -> set[str]:
    """Criteria already ticked in an issue body, so a sync does not untick them."""
    return {m.group(1).strip() for line in body.splitlines() if (m := _TICKED.match(line.strip()))}


def issue_title(req: dict[str, Any]) -> str:
    return f"{req['id']}: {req['title']}"


def criteria_lines(req: dict[str, Any]) -> list[str]:
    """Criteria as sentences: Given/When/Then when refined, the original list otherwise."""
    if "criteria" in req:
        return [f"Given {c['given']}, when {c['when']}, then {c['then']}" for c in req["criteria"]]
    return list(req["acceptance"])


def issue_body(
    req: dict[str, Any], epics: dict[str, dict[str, str]], ticked: set[str] | None = None
) -> str:
    ticked = ticked or set()
    epic = epics[req["ru"]]
    header = [f"**Requirement:** {req['id']}"]
    if "criteria" in req:
        priority = PRIORITY_NAMES[req["priority"]]
        header = [
            f"**Requirement:** {req['id']} ({req['kind']}, {req['points']} points, {priority})"
        ]
    lines = [
        *header,
        f"**Epic:** {req['ru']} {epic['name']}: {user_story(epic)}",
        f"**Release:** {req['block']}",
    ]
    if req.get("kind") == "story":
        lines += ["", "### User story", "", user_story(req)]
    lines += ["", "### Acceptance criteria", ""]
    lines += [f"- [{'x' if c in ticked else ' '}] {c}" for c in criteria_lines(req)]
    return "\n".join(lines)


def issue_labels(req: dict[str, Any]) -> set[str]:
    """Labels this script manages on an item's issue."""
    labels = {f"area:{req['area']}"}
    if "priority" in req:
        labels.add(f"priority:{req['priority']}")
    return labels


def issue_edits(req: dict[str, Any], body: str, milestone: str, issue: dict[str, Any]) -> list[str]:
    """`gh issue edit` arguments that bring an existing issue in line with the file."""
    args: list[str] = []
    if issue["title"] != issue_title(req):
        args += ["--title", issue_title(req)]
    if (issue.get("body") or "").replace("\r\n", "\n").strip() != body.strip():
        args += ["--body", body]
    if (issue.get("milestone") or {}).get("title") != milestone:
        args += ["--milestone", milestone]
    wanted = issue_labels(req)
    current = {label["name"] for label in issue.get("labels", [])}
    for label in sorted(wanted - current):
        args += ["--add-label", label]
    managed = {name for name in current if name.startswith(MANAGED_LABEL_PREFIXES)}
    for stale in sorted(managed - wanted):
        args += ["--remove-label", stale]
    return args


def ensure_labels(run: Runner) -> None:
    for name, color in LABELS.items():
        run.gh("label", "create", name, "--color", color, "--force", "--repo", run.repo)


def ensure_milestones(run: Runner) -> dict[str, str]:
    existing = json.loads(
        run.gh("api", f"repos/{run.repo}/milestones?state=all", read=True) or "[]"
    )
    titles = {m["title"] for m in existing}
    names = {}
    for block, description in MILESTONES.items():
        title = f"{block} {description}"
        names[block] = title
        if title not in titles:
            run.api(
                "POST",
                f"repos/{run.repo}/milestones",
                {"title": title, "description": f"Block {block} of the build plan"},
            )
    return names


def ensure_issues(
    run: Runner, milestones: dict[str, str], sync: bool = False
) -> list[tuple[str, dict[str, Any]]]:
    """Issue URL and backlog item for every requirement, creating missing issues."""
    epics, requirements = load_requirements()
    existing = json.loads(
        run.gh(
            "issue",
            "list",
            "--repo",
            run.repo,
            "--state",
            "all",
            "--limit",
            "500",
            "--json",
            "title,url,body,milestone,labels",
            read=True,
        )
        or "[]"
    )
    by_prefix = {issue["title"].split(":")[0]: issue for issue in existing}
    items = []
    for req in requirements:
        issue = by_prefix.get(req["id"])
        if issue is not None:
            items.append((issue["url"], req))
            if sync:
                body = issue_body(req, epics, ticked_criteria(issue.get("body") or ""))
                edits = issue_edits(req, body, milestones[req["block"]], issue)
                if edits:
                    run.gh("issue", "edit", issue["url"], *edits)
            continue
        url = run.gh(
            "issue",
            "create",
            "--repo",
            run.repo,
            "--title",
            issue_title(req),
            "--body",
            issue_body(req, epics),
            "--label",
            ",".join(["req", "type:feature", *sorted(issue_labels(req))]),
            "--milestone",
            milestones[req["block"]],
        ).strip()
        items.append((url, req))
    return items


def ensure_project(run: Runner, owner: str, items: list[tuple[str, dict[str, Any]]]) -> None:
    """Board with every issue, plus Points and Priority fields filled from the file."""
    title = "AI Process Discovery"
    projects = json.loads(
        run.gh("project", "list", "--owner", owner, "--format", "json", read=True) or "{}"
    ).get("projects", [])
    number = next((str(p["number"]) for p in projects if p["title"] == title), None)
    if number is None:
        created = run.gh(
            "project", "create", "--owner", owner, "--title", title, "--format", "json"
        )
        number = str(json.loads(created)["number"]) if created else "<new>"
        run.gh("project", "link", number, "--owner", owner, "--repo", run.repo)
    fields = ensure_project_fields(run, owner, number)
    project_id = ""
    if not run.dry_run:
        view = run.gh("project", "view", number, "--owner", owner, "--format", "json", read=True)
        project_id = json.loads(view)["id"]
    for url, req in items:
        if not url:
            continue
        added = run.gh(
            "project", "item-add", number, "--owner", owner, "--url", url, "--format", "json"
        )
        if not added or "criteria" not in req:
            continue
        item_id = json.loads(added)["id"]
        base = ["project", "item-edit", "--id", item_id, "--project-id", project_id]
        run.gh(*base, "--field-id", fields["Points"]["id"], "--number", str(req["points"]))
        option = fields["Priority"]["options"][PRIORITY_NAMES[req["priority"]]]
        run.gh(*base, "--field-id", fields["Priority"]["id"], "--single-select-option-id", option)


def ensure_project_fields(run: Runner, owner: str, number: str) -> dict[str, dict[str, Any]]:
    """Create the Points and Priority fields when missing; return them by name."""

    def current() -> dict[str, dict[str, Any]]:
        listed = run.gh(
            "project", "field-list", number, "--owner", owner, "--format", "json", read=True
        )
        found = {}
        for field in json.loads(listed or "{}").get("fields", []):
            options = {o["name"]: o["id"] for o in field.get("options", [])}
            found[field["name"]] = {"id": field["id"], "options": options}
        return found

    fields = current() if number != "<new>" else {}
    if "Points" not in fields:
        run.gh(
            "project",
            "field-create",
            number,
            "--owner",
            owner,
            "--name",
            "Points",
            "--data-type",
            "NUMBER",
        )
    if "Priority" not in fields:
        run.gh(
            "project",
            "field-create",
            number,
            "--owner",
            owner,
            "--name",
            "Priority",
            "--data-type",
            "SINGLE_SELECT",
            "--single-select-options",
            ",".join(PRIORITY_NAMES.values()),
        )
    return fields if run.dry_run else current()


def ensure_ruleset(run: Runner, checks: list[str]) -> None:
    """Create the `main` ruleset, or update its required checks when it already exists.

    Checks are added as the jobs that produce them land on `main`: a required check
    that no workflow reports would block every pull request.
    """
    existing = json.loads(run.gh("api", f"repos/{run.repo}/rulesets", read=True) or "[]")
    current = next((r for r in existing if r["name"] == "main"), None)
    method, path = ("POST", f"repos/{run.repo}/rulesets")
    if current is not None:
        method, path = ("PUT", f"repos/{run.repo}/rulesets/{current['id']}")
    run.api(
        method,
        path,
        {
            "name": "main",
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
            "rules": [
                {"type": "deletion"},
                {"type": "non_fast_forward"},
                {"type": "required_linear_history"},
                {
                    "type": "pull_request",
                    "parameters": {
                        "required_approving_review_count": 0,
                        "dismiss_stale_reviews_on_push": True,
                        "require_code_owner_review": False,
                        "require_last_push_approval": False,
                        "required_review_thread_resolution": True,
                        "require_extra_approval_for_unattributed_changes": True,
                        "allowed_merge_methods": ["squash"],
                    },
                },
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [{"context": c} for c in checks],
                    },
                },
            ],
        },
    )


def ensure_settings(run: Runner) -> None:
    run.api(
        "PATCH",
        f"repos/{run.repo}",
        {
            "allow_squash_merge": True,
            "allow_merge_commit": False,
            "allow_rebase_merge": False,
            "squash_merge_commit_title": "PR_TITLE",
            "squash_merge_commit_message": "PR_BODY",
            "delete_branch_on_merge": True,
            "security_and_analysis": {
                "secret_scanning": {"status": "enabled"},
                "secret_scanning_push_protection": {"status": "enabled"},
            },
        },
    )
    run.api("PUT", f"repos/{run.repo}/vulnerability-alerts")
    # Security updates skip the version-update cooldown (ADR 0010).
    run.api("PUT", f"repos/{run.repo}/automated-security-fixes")
    run.api("PUT", f"repos/{run.repo}/private-vulnerability-reporting")
    # release-please opens its release pull request with GITHUB_TOKEN.
    run.api(
        "PUT",
        f"repos/{run.repo}/actions/permissions/workflow",
        {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": True},
    )
    # Holds ANTHROPIC_API_KEY for the manual llm-contract workflow.
    run.api("PUT", f"repos/{run.repo}/environments/llm", {})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="OWNER/NAME")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-project", action="store_true")
    parser.add_argument(
        "--sync", action="store_true", help="Also update existing issues to match the file"
    )
    parser.add_argument(
        "--checks",
        default=",".join(REQUIRED_CHECKS),
        help="Comma-separated required status checks for main",
    )
    parser.add_argument(
        "--only-ruleset", action="store_true", help="Only create or update the ruleset"
    )
    args = parser.parse_args()
    checks = [c.strip() for c in args.checks.split(",") if c.strip()]

    run = Runner(args.repo, args.dry_run)
    if args.only_ruleset:
        ensure_ruleset(run, checks)
        sys.stdout.write(f"Ruleset updated: {', '.join(checks)}\n")
        return
    ensure_settings(run)
    ensure_labels(run)
    milestones = ensure_milestones(run)
    items = ensure_issues(run, milestones, sync=args.sync)
    if not args.skip_project:
        try:
            ensure_project(run, args.repo.split("/")[0], items)
        except SystemExit as exc:
            sys.stderr.write(
                f"Project board skipped ({exc}).\nRun `gh auth refresh -s project` and re-run.\n"
            )
    ensure_ruleset(run, checks)
    sys.stdout.write(f"Done: {len(items)} backlog issues on {args.repo}\n")


if __name__ == "__main__":
    main()
