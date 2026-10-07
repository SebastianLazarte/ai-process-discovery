"""Set up the GitHub side of the repository with the gh CLI.

Creates labels, milestones (B0-B9), one issue per requirement in docs/requirements.toml,
a Project board, the `main` ruleset and the security settings. Safe to re-run: existing
labels, milestones and issues are left alone.

    uv run python scripts/bootstrap_github.py --repo OWNER/NAME --dry-run
    uv run python scripts/bootstrap_github.py --repo OWNER/NAME
"""

import argparse
import json
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
}

REQUIRED_CHECKS = ["quality", "test (3.12)", "test (3.13)", "test-postgres", "docker", "pr-title"]


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


def load_requirements() -> tuple[dict[str, str], list[dict[str, Any]]]:
    data = tomllib.loads((ROOT / "docs" / "requirements.toml").read_text(encoding="utf-8"))
    return data["user_requirements"], data["requirement"]


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


def ensure_issues(run: Runner, milestones: dict[str, str]) -> list[str]:
    user_reqs, requirements = load_requirements()
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
            "title,url",
            read=True,
        )
        or "[]"
    )
    by_prefix = {issue["title"].split(":")[0]: issue["url"] for issue in existing}
    urls = []
    for req in requirements:
        if req["id"] in by_prefix:
            urls.append(by_prefix[req["id"]])
            continue
        body = "\n".join(
            [
                f"**Requirement:** {req['id']}",
                f"**User requirement:** {req['ru']}: {user_reqs[req['ru']]}",
                f"**Block:** {req['block']}",
                "",
                "### Acceptance criteria",
                "",
                *[f"- [ ] {criterion}" for criterion in req["acceptance"]],
            ]
        )
        url = run.gh(
            "issue",
            "create",
            "--repo",
            run.repo,
            "--title",
            f"{req['id']}: {req['title']}",
            "--body",
            body,
            "--label",
            f"req,type:feature,area:{req['area']}",
            "--milestone",
            milestones[req["block"]],
        ).strip()
        urls.append(url)
    return urls


def ensure_project(run: Runner, owner: str, issue_urls: list[str]) -> None:
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
    for url in issue_urls:
        if url:
            run.gh("project", "item-add", number, "--owner", owner, "--url", url)


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
    urls = ensure_issues(run, milestones)
    if not args.skip_project:
        try:
            ensure_project(run, args.repo.split("/")[0], urls)
        except SystemExit as exc:
            sys.stderr.write(
                f"Project board skipped ({exc}).\nRun `gh auth refresh -s project` and re-run.\n"
            )
    ensure_ruleset(run, checks)
    sys.stdout.write(f"Done: {len(urls)} requirement issues on {args.repo}\n")


if __name__ == "__main__":
    main()
