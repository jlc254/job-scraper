"""Static checks that keep the workflows inside the rules in docs 08, 09 and 11.

These read the YAML only. They never run a workflow and never touch the network.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parent.parent
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
SHA = re.compile(r"[0-9a-f]{40}")
# ANY expression inlined into a `run:` body is a script-injection vector. GitHub
# substitutes expressions into the script before bash parses it, and git allows a branch
# name to contain $(...) and backticks, so an inlined github.ref_name would be executed.
# Pass the value through the step's `env:` and reference the variable instead.
EXPRESSION_IN_SHELL = re.compile(r"\$\{\{[^}]*\}\}")
DAILY_SECRET_STEPS = {
    "Run",
    "Alert on failure",
    "Ping dead-man's switch",
    "Ping dead-man's switch on failure",
    "Publish to Neon",
}
# Every workflow in the directory has to be listed here. Adding a file to
# .github/workflows without adding it to this set is what fails, so a workflow can never
# reach a merge unread.
REVIEWED_WORKFLOWS = {"ci.yml", "daily.yml", "deploy.yml", "preview.yml"}


def load(name: str) -> dict[str, Any]:
    res = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))
    return res if isinstance(res, dict) else {}


def triggers(doc: dict[str, Any]) -> dict[str, Any]:
    # YAML 1.1 resolves a bare `on:` to the boolean True, so a workflow that does not quote
    # the key parses under `True` rather than "on". Accept either, or every trigger
    # assertion below silently compares against an empty dict and passes for the wrong
    # reason -- which is how `pull_request_target` went unguarded in three of four files.
    on = doc.get("on", doc.get(True))
    return on if isinstance(on, dict) else {}


def steps(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for job in doc["jobs"].values() for s in job["steps"]]


def test_workflow_files_exist() -> None:
    found = {p.name for p in WORKFLOWS}
    unreviewed = sorted(found - REVIEWED_WORKFLOWS)
    assert not unreviewed, f"workflow(s) present but not reviewed here: {unreviewed}"
    assert {"ci.yml", "daily.yml"} <= found, "ci.yml and daily.yml must exist"


def test_every_action_is_pinned_to_a_commit_sha() -> None:
    problems = []
    for path in WORKFLOWS:
        for step in steps(yaml.safe_load(path.read_text(encoding="utf-8"))):
            uses = step.get("uses")
            if not uses or uses.startswith("./"):
                continue
            _, _, ref = uses.partition("@")
            if not SHA.fullmatch(ref) or ref == "0" * 40:
                problems.append(f"{path.name}: {uses}")
    assert not problems, (
        "Actions must be pinned to a full commit SHA (doc 08). Run `python scripts/pin_actions.py` "
        "with network access and commit the result. Unpinned: " + "; ".join(problems)
    )


def test_least_privilege_and_no_dangerous_triggers() -> None:
    for path in WORKFLOWS:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert doc["permissions"] == {"contents": "read"}, path.name
        assert "pull_request_target" not in triggers(doc), path.name
        for job in doc["jobs"].values():
            if "permissions" in job:
                assert job["permissions"] == {"contents": "read"}, path.name
            assert 0 < job["timeout-minutes"] <= 20, path.name


def test_checkout_does_not_persist_credentials() -> None:
    for path in WORKFLOWS:
        for step in steps(yaml.safe_load(path.read_text(encoding="utf-8"))):
            if str(step.get("uses", "")).startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] is False, path.name


def test_untrusted_inputs_never_reach_the_shell_directly() -> None:
    for path in WORKFLOWS:
        for step in steps(yaml.safe_load(path.read_text(encoding="utf-8"))):
            assert not EXPRESSION_IN_SHELL.search(str(step.get("run", ""))), (
                f"{path.name}: {step.get('name')} inlines a ${{{{ }}}} expression into the "
                "shell; pass it through the step's env: instead"
            )


def test_secrets_only_appear_in_step_env_of_the_expected_steps() -> None:
    daily = load("daily.yml")
    assert "secrets." not in json.dumps(daily.get("env", {}))
    for job in daily["jobs"].values():
        assert "secrets." not in json.dumps(job.get("env", {}))
        for step in job["steps"]:
            assert "secrets." not in json.dumps(step.get("with", {})), step.get("name")
            assert "secrets." not in str(step.get("run", "")), step.get("name")
            if "secrets." in json.dumps(step.get("env", {})):
                assert step["name"] in DAILY_SECRET_STEPS, step["name"]


def test_ci_uses_no_secrets_at_all() -> None:
    assert "secrets." not in (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def test_community_secrets_only_in_run_and_publish_steps() -> None:
    community = ("GOOGLE_SHEET_ID_COMMUNITY", "TELEGRAM_CHAT_ID_COMMUNITY")
    daily = load("daily.yml")
    found_in: dict[str, list[str]] = {name: [] for name in community}
    for job in daily["jobs"].values():
        for step in job["steps"]:
            env_text = json.dumps(step.get("env", {}))
            for name in community:
                if name in env_text:
                    found_in[name].append(step["name"])
    for name, step_names in found_in.items():
        assert step_names == ["Run", "Publish to Neon"], f"{name} in {step_names}"


def test_daily_schedule_matches_the_plan() -> None:
    doc = load("daily.yml")
    on = triggers(doc)
    assert "workflow_dispatch" in on
    crons = [item["cron"].split() for item in on["schedule"]]
    assert sorted(c[1] for c in crons) == ["13", "3"]  # 06:xx and 16:xx EAT
    assert all(c[2:] == ["*", "*", "*"] and c[0].isdigit() for c in crons)
    assert all(int(c[0]) != 0 for c in crons), (
        "avoid the top of the hour, when GitHub delays cron most"
    )


def test_manual_runs_can_rebuild_just_the_dashboard() -> None:
    options = triggers(load("daily.yml"))["workflow_dispatch"]["inputs"]["mode"]["options"]
    assert options == ["normal", "no-notify", "dry-run", "dashboard", "publish"]
    assert "dashboard)" in (ROOT / "scripts" / "ci_run.sh").read_text(encoding="utf-8")


def test_daily_runs_never_overlap_and_are_time_boxed() -> None:
    doc = load("daily.yml")
    assert doc["concurrency"]["group"]
    assert doc["concurrency"]["cancel-in-progress"] is False
    job = doc["jobs"]["run"]
    assert job["timeout-minutes"] == 15
    assert next(s for s in job["steps"] if s["name"] == "Run")["timeout-minutes"] < 15


def test_daily_installs_only_from_hashed_requirements() -> None:
    install = next(s for s in steps(load("daily.yml")) if s["name"].startswith("Install"))
    assert "--require-hashes" in install["run"]
    assert "requirements.txt" in install["run"]


def test_daily_failure_alert_and_dead_mans_switch() -> None:
    by_name = {s["name"]: s for s in steps(load("daily.yml"))}
    alert, ping = by_name["Alert on failure"], by_name["Ping dead-man's switch"]
    assert alert["if"] == "failure()"
    assert alert.get("continue-on-error") is True
    assert ping["if"] == "success()"
    assert "ci_alert" not in alert["run"], "the alert must work even if checkout failed"
    assert "--config -" in alert["run"]
    assert "TELEGRAM_BOT_TOKEN}" in alert["run"]
    assert "${TELEGRAM_BOT_TOKEN}" not in alert["run"].split("<<EOF")[0], (
        "token must not be on the command line"
    )
    fail_ping = by_name["Ping dead-man's switch on failure"]
    assert fail_ping["if"] == "failure()"
    assert "/fail" in fail_ping["run"]
    assert by_name["Keep debugging files"]["if"] == "always()"


def test_preview_database_never_leaks_into_production() -> None:
    # deploy.yml must always use the production database.
    assert "DATABASE_URL_PREVIEW" not in json.dumps(load("deploy.yml"))

    preview = load("preview.yml")
    env = preview["jobs"]["deploy-preview"]["env"]
    assert env["DATABASE_URL"] == "${{ secrets.DATABASE_URL_PREVIEW }}", "preview must use DATABASE_URL_PREVIEW only, never fall back to production"
    # A missing preview database must fail the workflow, not silently deploy against production.
    requirers = [s for s in steps(preview) if "::error" in str(s.get("run", "")) and "DATABASE_URL_PREVIEW" in str(s.get("run", ""))]
    assert requirers, "preview.yml must fail when DATABASE_URL_PREVIEW is missing"


def test_preview_follows_pull_requests_rather_than_raw_branch_pushes() -> None:
    # Previews track review requests, the way the Vercel Git integration does. Keying them
    # to `push` spends a full build on branches nobody is reviewing, and fires a second time
    # when a branch is deleted, where actions/checkout cannot resolve the ref and the run
    # goes red for a branch that was merged and thrown away on purpose.
    on = triggers(load("preview.yml"))
    assert set(on) == {"pull_request"}, "preview.yml must trigger on pull_request only"
    pr = on["pull_request"]
    assert pr["branches"] == ["main"], "previews belong to PRs targeting main"
    # `closed` is deliberately absent: a merge must not build a second time, because
    # deploy.yml is already shipping main to production.
    assert set(pr["types"]) == {"opened", "synchronize", "reopened"}

    # Under pull_request, github.ref is refs/pull/N/merge, so ref_name would read
    # "12/merge" in the step summary instead of the branch name. It has to stay in `env:`
    # rather than be inlined as ${{ }}: git allows a branch name to contain $(...) and
    # backticks, and GitHub substitutes expressions before bash parses the script.
    deploy = next(s for s in steps(load("preview.yml")) if s["name"] == "Deploy")
    assert deploy["env"]["BRANCH_NAME"] == "${{ github.head_ref }}"

    # Production must stay reachable only by pushing to main.
    assert triggers(load("deploy.yml"))["push"]["branches"] == ["main"]


def test_ci_runs_the_checks_doc_11_requires() -> None:
    doc = load("ci.yml")
    text = " ".join(str(s.get("run", "")) for s in steps(doc))
    for command in ("ruff check", "ruff format --check", "mypy src", "pytest", "pip-audit"):
        assert command in text, command

    # Check for --require-hashes in run commands or if the setup-python-env action is used
    has_hashes = "--require-hashes" in text or any(
        s.get("uses") == "./.github/actions/setup-python-env" for s in steps(doc)
    )
    assert has_hashes, (
        "--require-hashes missing from ci.yml (not in run commands and setup-python-env not used)"
    )


def test_dependabot_covers_actions_and_pip() -> None:
    config = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    assert {u["package-ecosystem"] for u in config["updates"]} == {"github-actions", "pip"}


def _requirement_blocks(path: Path) -> list[str]:
    blocks: list[str] = []
    current = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        current += " " + line.rstrip("\\").strip()
        if not line.endswith("\\"):
            blocks.append(current.strip())
            current = ""
    return blocks


@pytest.mark.parametrize("name", ["requirements.txt", "requirements-dev.txt"])
def test_lock_files_are_fully_pinned_with_hashes(name: Any) -> None:
    path = ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not generated yet. Run scripts/lock.sh and commit the result.")
    for block in _requirement_blocks(path):
        if block.startswith("-"):
            continue
        msg = f"{name}: {block[:60]}"
        assert "==" in block, msg
        assert "--hash=sha256:" in block, msg
