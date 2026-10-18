from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "verify_vercel_project.sh"
APP = ROOT / "frontend"

MakeApp = Callable[[str], str]


@pytest.fixture
def make_app(tmp_path: Path) -> MakeApp:
    """Put a minimal Next.js app in tmp_path and return its repo-relative directory name."""

    def _make(name: str = "frontend") -> str:
        app = tmp_path / name
        app.mkdir(parents=True, exist_ok=True)
        (app / "package.json").write_text(
            json.dumps({"name": "x", "dependencies": {"next": "16.0.0"}}), encoding="utf-8"
        )
        (app / "next.config.mjs").write_text("export default {};", encoding="utf-8")
        return name

    return _make


def run(cwd: Path, mode: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT), *([mode] if mode else [])],  # noqa: S607
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=60,
    )


def project(root: Path, **settings: Any) -> None:
    (root / ".vercel").mkdir(exist_ok=True)
    (root / ".vercel" / "project.json").write_text(
        json.dumps({"projectId": "prj_1", "settings": settings}), encoding="utf-8"
    )


def test_app_root_follows_the_app_not_a_baked_in_string(tmp_path: Path, make_app: MakeApp) -> None:
    """Renaming the app must not require editing the workflows."""
    project(tmp_path, rootDirectory=make_app("web"))
    done = run(tmp_path, "link")
    assert done.returncode == 0, done.stderr
    assert "'web'" in done.stdout


def test_matching_root_directory_passes(tmp_path: Path, make_app: MakeApp) -> None:
    project(tmp_path, rootDirectory=make_app())
    done = run(tmp_path, "link")
    assert done.returncode == 0, done.stderr
    assert "'frontend'" in done.stdout


def test_wrong_root_directory_fails_and_names_both_sides(tmp_path: Path, make_app: MakeApp) -> None:
    project(tmp_path, rootDirectory="web")
    make_app()
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "Root Directory" in done.stderr
    # Must say what it is, what it should be and where to change it, since vercel.json
    # cannot express this setting.
    assert "'web'" in done.stderr
    assert "'frontend'" in done.stderr
    assert "Project > Settings" in done.stderr


@pytest.mark.parametrize(
    "settings",
    [
        pytest.param({"rootDirectory": None}, id="null"),
        pytest.param({"rootDirectory": ""}, id="empty"),
        pytest.param({}, id="key-absent"),
    ],
)
def test_unset_root_directory_is_reported_as_unset(
    tmp_path: Path, make_app: MakeApp, settings: dict[str, Any]
) -> None:
    project(tmp_path, **settings)
    make_app()
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "<unset>" in done.stderr


def test_missing_project_json_points_at_the_link_secrets(tmp_path: Path, make_app: MakeApp) -> None:
    make_app()
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "not linked" in done.stderr
    assert "VERCEL_PROJECT_ID" in done.stderr


def test_malformed_project_json_reports_cleanly(tmp_path: Path, make_app: MakeApp) -> None:
    make_app()
    (tmp_path / ".vercel").mkdir()
    (tmp_path / ".vercel" / "project.json").write_text("{not json", encoding="utf-8")
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "not valid JSON" in done.stderr
    assert "node:internal" not in done.stderr


def test_two_next_apps_are_rejected_rather_than_guessed(tmp_path: Path, make_app: MakeApp) -> None:
    project(tmp_path, rootDirectory="frontend")
    make_app("admin")
    make_app("frontend")
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "More than one Next.js app" in done.stderr


def test_no_next_app_is_reported(tmp_path: Path) -> None:
    project(tmp_path, rootDirectory="frontend")
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "No Next.js app found" in done.stderr


def test_build_mode_requires_output_in_the_app_root(tmp_path: Path, make_app: MakeApp) -> None:
    make_app()
    done = run(tmp_path, "build")
    assert done.returncode == 1
    assert "frontend/.vercel/output" in done.stderr


def test_build_mode_passes_once_output_exists(tmp_path: Path, make_app: MakeApp) -> None:
    name = make_app()
    (tmp_path / name / ".vercel" / "output").mkdir(parents=True)
    done = run(tmp_path, "build")
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("argv", [[], ["deploy"], ["pull"]], ids=["no-mode", "typo", "wrong-verb"])
def test_bad_mode_is_a_usage_error(tmp_path: Path, make_app: MakeApp, argv: list[str]) -> None:
    make_app()
    done = run(tmp_path, argv[0] if argv else None)
    assert done.returncode == 2
    assert "usage:" in done.stderr


def test_both_deploy_workflows_run_both_checks() -> None:
    # The checks only help if they run where the project is linked and built.
    for name in ("deploy.yml", "preview.yml"):
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "bash scripts/verify_vercel_project.sh link" in text, name
        assert "bash scripts/verify_vercel_project.sh build" in text, name
        # The app root must not be hard-coded in the workflows any more.
        assert "verify_vercel_project.sh link frontend" not in text, name


def test_the_real_dashboard_lives_in_frontend() -> None:
    """The premise of the resolver: exactly one Next.js app, in frontend/."""
    pkg = json.loads((APP / "package.json").read_text(encoding="utf-8"))
    assert pkg["dependencies"]["next"]
    assert list(APP.glob("next.config.*"))
    assert (APP / "package-lock.json").exists()
    others = [
        p.parent
        for p in ROOT.glob("*/next.config.*")
        if "node_modules" not in p.parts and p.parent != APP
    ]
    assert not others, f"unexpected second Next.js app(s): {others}"
