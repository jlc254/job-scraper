from __future__ import annotations

import json
import os
import subprocess
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "neon_preview_branch.sh"


class _NeonHandler(BaseHTTPRequestHandler):
    branches: list[dict[str, Any]] = []
    deleted: list[str] = []
    delete_status: int = 204

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's name
        body = json.dumps({"branches": type(self).branches}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's name
        type(self).deleted.append(self.path.rstrip("/").rsplit("/", 1)[-1])
        self.send_response(type(self).delete_status)
        self.end_headers()

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def neon_api() -> Iterator[tuple[str, type[_NeonHandler]]]:
    _NeonHandler.branches = []
    _NeonHandler.deleted = []
    _NeonHandler.delete_status = 204
    server = HTTPServer(("127.0.0.1", 0), _NeonHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/api/v2", _NeonHandler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run(mode: str, base: str, **overrides: str) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "NEON_API_BASE": base,
        "NEON_API_KEY": "k",
        "NEON_PROJECT_ID": "prj_1",
        "NEON_BRANCH_NAME": "preview/feature",
        "NEON_VERIFY_ATTEMPTS": "2",
        "NEON_VERIFY_DELAY": "0",
    }
    env.update(overrides)
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT), mode],  # noqa: S607
        capture_output=True,
        text=True,
        env={k: v for k, v in env.items() if v is not None},
        timeout=30,
    )


def branch(name: str, default: bool = False, branch_id: str = "br-1") -> dict[str, Any]:
    return {"id": branch_id, "name": name, "default": default}


def test_verify_passes_for_a_non_default_preview_branch(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    base, handler = neon_api
    handler.branches = [branch("main", default=True), branch("preview/feature")]
    done = run("verify", base)
    assert done.returncode == 0, done.stderr
    assert "not the default branch" in done.stdout


def test_verify_fails_closed_when_the_integration_created_no_branch(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    base, handler = neon_api
    handler.branches = [branch("main", default=True)]
    done = run("verify", base)
    assert done.returncode == 1
    assert "did not create a preview branch" in done.stderr


def test_verify_refuses_to_call_the_default_branch_a_preview(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # A ref that somehow resolves to the production branch must never pass verification.
    base, handler = neon_api
    handler.branches = [branch("preview/feature", default=True)]
    done = run("verify", base)
    assert done.returncode == 1
    assert "default (production) branch" in done.stderr


def test_delete_removes_the_matching_branch(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    base, handler = neon_api
    handler.branches = [branch("main", default=True), branch("preview/feature", branch_id="br-9")]
    done = run("delete", base)
    assert done.returncode == 0, done.stderr
    assert handler.deleted == ["br-9"]


def test_delete_is_successful_when_the_branch_never_existed(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # A PR that closed before its preview deployed must not turn cleanup red.
    base, handler = neon_api
    handler.branches = [branch("main", default=True)]
    done = run("delete", base)
    assert done.returncode == 0, done.stderr
    assert "nothing to delete" in done.stdout
    assert handler.deleted == []


def test_delete_refuses_the_default_branch(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    base, handler = neon_api
    handler.branches = [branch("preview/feature", default=True, branch_id="br-9")]
    done = run("delete", base)
    assert done.returncode == 1
    assert "refusing to delete" in done.stderr
    assert handler.deleted == []


def test_delete_treats_a_404_race_as_success(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # Vercel deletes the branch when it removes the last deployment for a branch, so the
    # branch can vanish between the lookup and the DELETE. The end state is the same.
    base, handler = neon_api
    handler.branches = [branch("preview/feature", branch_id="br-9")]
    handler.delete_status = 404
    done = run("delete", base)
    assert done.returncode == 0, done.stderr
    assert "already gone" in done.stdout


def test_delete_fails_loudly_on_any_other_error(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # A bad API key or wrong project must not look like a successful cleanup.
    base, handler = neon_api
    handler.branches = [branch("preview/feature", branch_id="br-9")]
    handler.delete_status = 401
    done = run("delete", base)
    assert done.returncode == 1
    assert "HTTP 401" in done.stderr


@pytest.mark.parametrize("mode", ["verify", "delete"])
@pytest.mark.parametrize("name", ["main", "production", "preview/", "preview"])
def test_non_preview_names_are_refused_before_any_request(mode: str, name: str) -> None:
    # Port 1 is closed: reaching the network at all would fail differently. These names
    # must be rejected by the prefix check first, so the script can never be aimed at
    # production even if the branch ref is malformed.
    done = run(mode, "http://127.0.0.1:1", NEON_BRANCH_NAME=name)
    assert done.returncode == 1
    assert "only preview/<branch> names are allowed" in done.stderr


def test_missing_credentials_are_a_usage_failure(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    base, _ = neon_api
    done = run("verify", base, NEON_API_KEY=None)
    assert done.returncode != 0
    assert "NEON_API_KEY is required" in done.stderr


def test_bad_mode_is_a_usage_error(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    base, _ = neon_api
    done = run("drop", base)
    assert done.returncode == 2
    assert "usage:" in done.stderr
