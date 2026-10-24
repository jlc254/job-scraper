from __future__ import annotations

import json
import os
import subprocess
import threading
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
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


def run(
    cwd: Path, mode: str | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT), *([mode] if mode else [])],  # noqa: S607
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=60,
    )


def run_env(cwd: Path, mode: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run with exactly the given deploy variables, so an unset one really is unset.

    PATH is carried over because the script needs find and node.
    """
    base = {"PATH": os.environ.get("PATH", "")}
    return run(cwd, mode, {**base, **env})


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
    make_app("frontend")
    # A nested app within the resolver's maxdepth 3, mirroring packages/admin.
    nested = tmp_path / "packages" / "admin"
    nested.mkdir(parents=True, exist_ok=True)
    (nested / "package.json").write_text(
        json.dumps({"name": "admin", "dependencies": {"next": "16.0.0"}}), encoding="utf-8"
    )
    (nested / "next.config.mjs").write_text("export default {};", encoding="utf-8")
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "More than one Next.js app" in done.stderr
    assert "'packages/admin'" in done.stderr
    assert "'frontend'" in done.stderr


def test_no_next_app_is_reported(tmp_path: Path) -> None:
    project(tmp_path, rootDirectory="frontend")
    done = run(tmp_path, "link")
    assert done.returncode == 1
    assert "No Next.js app found" in done.stderr


def test_build_mode_accepts_output_at_the_repository_root(
    tmp_path: Path, make_app: MakeApp
) -> None:
    """This is where the CLI actually put it: a settings.rootDirectory of "frontend" still
    produced output at the repository root."""
    make_app()
    (tmp_path / ".vercel" / "output").mkdir(parents=True)
    done = run(tmp_path, "build")
    assert done.returncode == 0, done.stderr
    assert "'.vercel/output'" in done.stdout


def test_build_mode_accepts_output_at_the_app_root(tmp_path: Path, make_app: MakeApp) -> None:
    name = make_app()
    (tmp_path / name / ".vercel" / "output").mkdir(parents=True)
    done = run(tmp_path, "build")
    assert done.returncode == 0, done.stderr
    assert f"'{name}/.vercel/output'" in done.stdout


def test_build_mode_fails_when_there_is_no_output_anywhere(
    tmp_path: Path, make_app: MakeApp
) -> None:
    name = make_app()
    done = run(tmp_path, "build")
    assert done.returncode == 1
    assert "No build output" in done.stderr
    # The error must list both places it looked.
    assert ".vercel/output" in done.stderr
    # Require the app-root candidate explicitly: it contains ".vercel/output" as a
    # substring, so checking only that would not catch a regression that dropped it.
    assert f"{name}/.vercel/output" in done.stderr


def secrets_env(**overrides: str) -> dict[str, str]:
    env = {"VERCEL_TOKEN": "t", "DATABASE_URL": "postgresql://u:p@h/db"}
    for key in ("DB_USE_PG", "DASH_PROFILE_LABELS", "DASH_DEFAULT_PROFILE"):
        env[key] = "set"
    env.update(overrides)
    return {k: v for k, v in env.items() if v is not None}


def test_secrets_pass_when_the_app_has_what_it_needs(tmp_path: Path, make_app: MakeApp) -> None:
    make_app()
    done = run_env(tmp_path, "secrets", secrets_env())
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("missing", ["VERCEL_TOKEN", "DATABASE_URL"], ids=["token", "db"])
def test_secrets_fail_when_a_required_variable_is_empty(
    tmp_path: Path, make_app: MakeApp, missing: str
) -> None:
    make_app()
    done = run_env(tmp_path, "secrets", secrets_env(**{missing: ""}))
    assert done.returncode == 1
    assert missing in done.stderr


def test_secrets_reject_a_non_postgres_url(tmp_path: Path, make_app: MakeApp) -> None:
    # Mirrors lib/db.ts, which throws on anything but postgres:// or postgresql://.
    make_app()
    done = run_env(tmp_path, "secrets", secrets_env(DATABASE_URL="mysql://h/db"))
    assert done.returncode == 1
    assert "postgres://" in done.stderr


def test_secrets_tolerate_unset_optional_variables(tmp_path: Path, make_app: MakeApp) -> None:
    # These have code defaults, so unset must not fail the deploy.
    make_app()
    done = run_env(
        tmp_path,
        "secrets",
        secrets_env(DB_USE_PG=None, DASH_PROFILE_LABELS=None, DASH_DEFAULT_PROFILE=None),
    )
    assert done.returncode == 0, done.stderr
    assert "code defaults" in done.stdout


def preview_secrets_env(**overrides: str) -> dict[str, str]:
    env = {"VERCEL_TOKEN": "t", "NEON_API_KEY": "k", "NEON_PROJECT_ID": "prj_1"}
    env.update(overrides)
    return {k: v for k, v in env.items() if v is not None}


def test_preview_secrets_pass_without_a_static_database_url(
    tmp_path: Path, make_app: MakeApp
) -> None:
    make_app()
    done = run_env(tmp_path, "preview-secrets", preview_secrets_env())
    assert done.returncode == 0, done.stderr
    assert "no static DATABASE_URL" in done.stdout


@pytest.mark.parametrize(
    "missing",
    ["VERCEL_TOKEN", "NEON_API_KEY", "NEON_PROJECT_ID"],
    ids=["token", "neon-key", "project"],
)
def test_preview_secrets_fail_closed_without_neon_access(
    tmp_path: Path, make_app: MakeApp, missing: str
) -> None:
    # Without these the post-deploy branch check cannot run, so the preview must not start.
    make_app()
    done = run_env(tmp_path, "preview-secrets", preview_secrets_env(**{missing: ""}))
    assert done.returncode == 1
    assert missing in done.stderr


def test_preview_secrets_reject_a_static_database_url(tmp_path: Path, make_app: MakeApp) -> None:
    # This is the old DATABASE_URL_PREVIEW link coming back: it pins every preview to one
    # database instead of the branch Neon creates for the deployment.
    make_app()
    done = run_env(
        tmp_path,
        "preview-secrets",
        preview_secrets_env(DATABASE_URL="postgresql://u:p@production/db"),
    )
    assert done.returncode == 1
    assert "per-deployment branch" in done.stderr


class FlatEnvList(list):  # noqa: FURB189 - a real list is what json.dumps serialises
    """Marker for a test that wants the v10 flat-array response shape."""


class _EnvHandler(BaseHTTPRequestHandler):
    envs: list[dict[str, Any]] = []
    paths: list[str] = []

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's name
        type(self).paths.append(self.path)
        # v10 returns {"envs": [...]} or, for a project with a single page, a bare array.
        # FlatEnvList marks a test that wants the second shape.
        payload: Any = (
            list(self.envs) if isinstance(self.envs, FlatEnvList) else {"envs": self.envs}
        )
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def vercel_api() -> Iterator[tuple[str, type[_EnvHandler]]]:
    server = HTTPServer(("127.0.0.1", 0), _EnvHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", _EnvHandler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def preview_env_vars(api: str, **overrides: str) -> dict[str, str]:
    env = {
        "VERCEL_TOKEN": "t",
        "VERCEL_PROJECT_ID": "prj_1",
        "VERCEL_ORG_ID": "team_1",
        "VERCEL_API_BASE": api,
    }
    env.update(overrides)
    return {k: v for k, v in env.items() if v is not None}


def test_preview_env_allows_a_production_only_database_url(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    make_app()
    base, handler = vercel_api
    handler.envs = [{"key": "DATABASE_URL", "target": ["production"]}]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 0, done.stderr
    assert "No unowned Preview-scoped DATABASE_URL" in done.stdout


def test_preview_env_uses_the_documented_v10_collection_endpoint(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    # v10 is the documented list endpoint, and its items are the ones that expose
    # configurationId. A legacy path could silently stop returning it, which would make
    # the integration-owned exemption above stop working.
    make_app()
    base, handler = vercel_api
    handler.envs = []
    handler.paths.clear()
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 0, done.stderr
    assert handler.paths == ["/v10/projects/prj_1/env?teamId=team_1"]


@pytest.mark.parametrize("key", ["DATABASE_URL", "DATABASE_URL_UNPOOLED"])
def test_preview_env_rejects_a_preview_scoped_database_url(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]], key: str
) -> None:
    make_app()
    base, handler = vercel_api
    handler.envs = [{"key": key, "target": ["preview"], "id": "env_manual", "type": "encrypted"}]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 1
    # Name the variable and its id: "a Preview DATABASE_URL exists" alone sends the
    # operator hunting through the dashboard.
    assert key in done.stderr
    assert "env_manual" in done.stderr


def test_preview_env_allows_the_integration_owned_preview_database_url(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    # The Neon integration owns a Preview entry and overrides its value per deployment.
    # Treating it as a static link blocks every preview, which is what happened in CI.
    make_app()
    base, handler = vercel_api
    handler.envs = [
        {
            "key": "DATABASE_URL",
            "target": ["preview"],
            "id": "env_integration",
            "type": "secret",
            "configurationId": "icfg_neon",
        }
    ]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 0, done.stderr
    assert "No unowned Preview-scoped DATABASE_URL" in done.stdout


def test_preview_env_allows_a_marketplace_storage_variable_by_its_store_hint(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    # Marketplace storage products (Neon among them) mark their variables with a
    # contentHint store id instead of, or as well as, a configurationId.
    make_app()
    base, handler = vercel_api
    handler.envs = [
        {
            "key": "DATABASE_URL",
            "target": ["preview"],
            "id": "env_store",
            "contentHint": {"type": "postgres-url", "storeId": "store_neon"},
        }
    ]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 0, done.stderr


def test_preview_env_accepts_the_flat_array_response_shape(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    # v10 may return the variables as a bare array rather than {"envs": [...]}. Rejecting
    # that shape would fail the preflight on a healthy API response.
    make_app()
    base, handler = vercel_api
    handler.envs = FlatEnvList([{"key": "DATABASE_URL", "target": ["preview"], "id": "env_manual"}])
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 1
    assert "env_manual" in done.stderr


def test_preview_env_still_rejects_an_unowned_entry_next_to_the_integration_one(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    # Exempting integration ownership must not exempt the manual variable beside it.
    make_app()
    base, handler = vercel_api
    handler.envs = [
        {"key": "DATABASE_URL", "target": ["preview"], "configurationId": "icfg_neon"},
        {"key": "DATABASE_URL_UNPOOLED", "target": ["preview"], "id": "env_manual"},
    ]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 1
    assert "env_manual" in done.stderr


def test_preview_env_reports_an_unparseable_response_as_such(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    # A shape change in the API is not evidence of a database variable. Reporting it as
    # one would send the operator looking for a variable that does not exist.
    make_app()
    base, handler = vercel_api
    handler.envs = "not-a-list"  # type: ignore[assignment]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 1
    assert "Could not parse" in done.stderr
    assert "Preview-scoped DATABASE_URL (or DATABASE_URL_UNPOOLED)\nthat was not" not in done.stderr


def test_preview_env_reads_a_string_target_as_preview(
    tmp_path: Path, make_app: MakeApp, vercel_api: tuple[str, type[_EnvHandler]]
) -> None:
    make_app()
    base, handler = vercel_api
    handler.envs = [{"key": "DATABASE_URL", "target": "preview"}]
    done = run_env(tmp_path, "preview-env", preview_env_vars(base))
    assert done.returncode == 1


def test_preview_env_fails_closed_when_vercel_is_unreachable(
    tmp_path: Path, make_app: MakeApp
) -> None:
    # No answer from Vercel means no proof that previews are isolated, so do not deploy.
    make_app()
    done = run_env(tmp_path, "preview-env", preview_env_vars("http://127.0.0.1:1"))
    assert done.returncode == 1
    assert "Refusing to deploy" in done.stderr


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
