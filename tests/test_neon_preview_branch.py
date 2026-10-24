from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "neon_preview_branch.sh"


class _NeonHandler(BaseHTTPRequestHandler):
    branches: list[dict[str, Any]] = []
    deleted: list[str] = []
    delete_status: int = 204
    paths: list[str] = []
    # When set, `branches` is ignored and each chunk of `pages` is served as its own
    # cursor-paginated page: page one (no cursor in the query) advertises
    # pagination.next = "c1", whose follow-up request with cursor=c1 gets pages[1].
    # The last page omits `pagination` entirely, exactly what a finished Neon response
    # looks like (the cursor is absent on the last page, per the API reference).
    pages: list[list[dict[str, Any]]] | None = None

    def _contract_ok(self, check_accept: bool = False) -> bool:
        # A fixture response is only honest for the request the script is contractually
        # supposed to make (run() passes NEON_API_KEY='k' and NEON_PROJECT_ID='prj_1').
        # A wrong path, a dropped auth header or a JSON response misparsed by the script
        # would otherwise still receive a 200 full of branches, and a regression would
        # pass by accident. 500 makes the script fail closed instead: the test goes red,
        # and the script's own error text is what the failure cites.
        ok = self.headers.get("Authorization") == "Bearer k"
        if check_accept:
            ok = ok and self.headers.get("Accept") == "application/json"
        return ok

    def _reject(self) -> None:
        self.send_error(500)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's name
        type(self).paths.append(self.path)
        query = parse_qs(urlparse(self.path).query)
        if self.pages is None and query.get("cursor"):
            # A cursor on a single-page fixture means the script split one page over
            # two requests.
            self._reject()
            return
        if not self._contract_ok(check_accept=True) or query.get("limit") != ["100"]:
            self._reject()
            return
        if self.pages is not None:
            index = int(query.get("cursor", ["c0"])[0].lstrip("c"))
            key = f"c{index + 1}" if index + 1 < len(self.pages) else ""  # absent = last
            if key:
                payload: dict[str, Any] = {"pagination": {"next": key}}
            else:
                payload = {}
            payload["branches"] = self.pages[index]
            body = json.dumps(payload).encode()
        else:
            body = json.dumps({"branches": type(self).branches}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's name
        if not self._contract_ok() or not re.fullmatch(
            r"/api/v2/projects/prj_1/branches/[^/?]+", self.path.rstrip("/")
        ):
            self._reject()
            return
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
    _NeonHandler.paths.clear()
    _NeonHandler.pages = None
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


def test_verify_finds_a_preview_branch_listed_on_a_later_page(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # Default ordering is updated_at-descending, so a long-lived project can push the
    # sought name past page one. A check that only read that page would fail verify
    # (and quietly no-op delete) for a branch that actually exists.
    base, handler = neon_api
    handler.pages = [
        [branch("main", default=True), branch("preview/other")],
        [branch("preview/feature", branch_id="br-7")],
    ]
    done = run("verify", base)
    assert done.returncode == 0, done.stderr
    assert "not the default branch" in done.stdout
    # The cursor of page one is what sent the follow-up request; the last page then
    # leaves pagination out entirely, and the script must treat that as the end.
    assert any(path.endswith("?limit=100") for path in handler.paths)
    assert any("?limit=100&cursor=c1" in path for path in handler.paths)
    assert len(handler.paths) == 2


def test_delete_removes_a_preview_branch_listed_on_a_later_page(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    base, handler = neon_api
    handler.pages = [
        [branch("main", default=True)],
        [branch("preview/feature", branch_id="br-7")],
    ]
    done = run("delete", base)
    assert done.returncode == 0, done.stderr
    assert "Deleted Neon branch" in done.stdout
    assert handler.deleted == ["br-7"]
    assert any("?limit=100&cursor=c1" in path for path in handler.paths)


@pytest.mark.parametrize("mode", ["verify", "delete"])
def test_the_api_key_never_reaches_curl_s_argv(
    tmp_path: Path, neon_api: tuple[str, type[_NeonHandler]], mode: str
) -> None:
    # The key must travel only inside curl's --config file: a process's argv is readable
    # by every user on the runner through /proc, so "Authorization: Bearer <key>" on the
    # command line would leak the credential. Intercept curl on PATH and record every
    # argv the script ever passes it.
    base, handler = neon_api
    real_curl = shutil.which("curl")
    assert real_curl is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / f"curl_argv_{mode}.log"
    argv_log.touch()
    shim = bin_dir / "curl"
    shim.write_text(
        f'#!/bin/bash\nprintf "%s\\0" "$@" >> "$CURL_ARGV_LOG"\nexec "{real_curl}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    handler.branches = [branch("main", default=True), branch("preview/feature")]
    done = run(
        mode,
        base,
        PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
        CURL_ARGV_LOG=str(argv_log),
    )
    assert done.returncode == 0, done.stderr
    # The shim wrapped at least one real invocation, so the assertion below is not
    # vacuous.
    argv_items = [item.decode() for item in argv_log.read_bytes().split(b"\0") if item.decode()]
    assert any("--config" in item for item in argv_items)
    assert argv_items
    assert all(item != "k" for item in argv_items)
    assert all("Bearer" not in item for item in argv_items)


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
