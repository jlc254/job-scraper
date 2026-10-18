from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "verify_vercel_link.sh"


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT), *args],  # noqa: S607
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=60,
    )


def link(tmp_path: Path, project: dict[str, Any] | str | None) -> Path:
    """Create a .vercel/project.json the way `vercel pull` would, or leave it absent."""
    if project is None:
        return tmp_path
    vercel = tmp_path / ".vercel"
    vercel.mkdir()
    body = project if isinstance(project, str) else json.dumps(project)
    (vercel / "project.json").write_text(body, encoding="utf-8")
    return tmp_path


def test_matching_root_directory_passes(tmp_path: Path) -> None:
    project = {"projectId": "prj_1", "settings": {"rootDirectory": "frontend"}}
    done = run(link(tmp_path, project), "frontend")
    assert done.returncode == 0, done.stderr
    assert "frontend" in done.stdout


def test_wrong_root_directory_fails_and_names_the_setting(tmp_path: Path) -> None:
    project = {"projectId": "prj_1", "settings": {"rootDirectory": "web"}}
    done = run(link(tmp_path, project), "frontend")
    assert done.returncode == 1
    assert "Root Directory" in done.stderr
    # The message has to say where to fix it, since vercel.json cannot express this.
    assert "Project > Settings" in done.stderr
    assert "web" in done.stderr and "frontend" in done.stderr


@pytest.mark.parametrize(
    "project",
    [
        pytest.param({"projectId": "prj_1", "settings": {"rootDirectory": None}}, id="null"),
        pytest.param({"projectId": "prj_1", "settings": {"rootDirectory": ""}}, id="empty"),
        pytest.param({"projectId": "prj_1", "settings": {}}, id="key-absent"),
        pytest.param({"projectId": "prj_1"}, id="settings-absent"),
    ],
)
def test_unset_root_directory_is_reported_as_unset(tmp_path: Path, project: dict[str, Any]) -> None:
    done = run(link(tmp_path, project), "frontend")
    assert done.returncode == 1
    assert "<unset>" in done.stderr


def test_missing_project_json_points_at_the_link_secrets(tmp_path: Path) -> None:
    done = run(link(tmp_path, None), "frontend")
    assert done.returncode == 1
    assert "not linked" in done.stderr
    assert "VERCEL_PROJECT_ID" in done.stderr


def test_malformed_project_json_reports_cleanly(tmp_path: Path) -> None:
    # Must not surface a raw interpreter stack trace.
    done = run(link(tmp_path, "{not json"), "frontend")
    assert done.returncode == 1
    assert "not valid JSON" in done.stderr
    assert "at Object." not in done.stderr and "node:internal" not in done.stderr


def test_expected_root_directory_is_required(tmp_path: Path) -> None:
    done = run(tmp_path)
    assert done.returncode == 2
    assert "usage:" in done.stderr


def test_both_deploy_workflows_call_the_check() -> None:
    # The check only helps if it actually runs where the project is linked.
    for name in ("deploy.yml", "preview.yml"):
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "bash scripts/verify_vercel_link.sh frontend" in text, name
