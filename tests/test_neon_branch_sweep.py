"""Contract tests for scripts/neon_branch_sweep.sh.

The sweep deletes Neon branches that Vercel's preview integration left behind when a PR
closed without its cleanup running. Every branch it may touch has to satisfy all three
conditions at once (preview/* name, not the default branch, older than MAX_AGE_DAYS), so
these tests pin each condition plus the failure modes that would make the script delete a
live branch instead of aborting.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "neon_branch_sweep.sh"

# Well clear of the default MAX_AGE_DAYS=7 either way, so the fixture does not start
# failing on a slow day or a timezone slip.
OLD_DAYS = 30
NEW_DAYS = 1


def stamp(days: float) -> str:
    moment = datetime.now(UTC) - timedelta(days=days)
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


class _NeonHandler(BaseHTTPRequestHandler):
    branches: list[dict[str, Any]] = []
    deleted: list[str] = []
    delete_status: int = 204
    paths: list[str] = []
    # When set, `branches` is ignored and each chunk of `pages` is served as its own
    # cursor-paginated page, the same shape tests/test_neon_preview_branch.py uses.
    pages: list[list[dict[str, Any]]] | None = None
    # When set, the branch list is answered with this body regardless of `branches`, so a
    # response the script must not trust can be exercised.
    raw_body: bytes | None = None

    def _contract_ok(self, check_accept: bool = False) -> bool:
        # A regression in the request (wrong project, dropped auth header, missing
        # limit) must fail the test rather than receive branches anyway. 500 makes the
        # script abort with its own error text.
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
            self._reject()
            return
        if not self._contract_ok(check_accept=True) or query.get("limit") != ["100"]:
            self._reject()
            return
        if self.raw_body is not None:
            body = self.raw_body
        elif self.pages is not None:
            index = int(query.get("cursor", ["c0"])[0].lstrip("c"))
            key = f"c{index + 1}" if index + 1 < len(self.pages) else ""
            payload: dict[str, Any] = {"branches": self.pages[index]}
            if key:
                payload["pagination"] = {"next": key}
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
    _NeonHandler.raw_body = None
    server = HTTPServer(("127.0.0.1", 0), _NeonHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/api/v2", _NeonHandler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run(base: str, **overrides: str) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "NEON_API_BASE": base,
        "NEON_API_KEY": "k",
        "NEON_PROJECT_ID": "prj_1",
    }
    env.update(overrides)
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT)],  # noqa: S607
        capture_output=True,
        text=True,
        env={k: v for k, v in env.items() if v is not None},
        timeout=30,
    )


def branch(
    name: str,
    *,
    days_old: float,
    default: bool = False,
    branch_id: str = "br-1",
    updated_at: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": branch_id,
        "name": name,
        "default": default,
        "updated_at": stamp(days_old) if updated_at is None else updated_at,
    }
    return item


def test_deletes_only_old_preview_branches(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    # The four branches from the plan: one of each reason to keep something. Only b1
    # satisfies preview/* + non-default + old, and the three survivors prove the sweep
    # does not delete by age or by name alone.
    base, handler = neon_api
    handler.branches = [
        branch("preview/old", days_old=OLD_DAYS, branch_id="b1"),
        branch("preview/new", days_old=NEW_DAYS, branch_id="b2"),
        branch("main", days_old=OLD_DAYS, branch_id="b3", default=True),
        branch("devtest", days_old=OLD_DAYS, branch_id="b4"),
    ]
    done = run(base)
    assert done.returncode == 0, done.stderr
    assert handler.deleted == ["b1"]
    assert "deleted=1 kept=3" in done.stdout


def test_refuses_when_the_default_branch_matches_the_preview_pattern(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # A branch marked default is production by definition, whatever its name. If Neon or
    # a future Vercel change ever reports a default branch with a preview/* name, the
    # sweep must abort before deleting anything -- including the harmless old preview
    # listed alongside it, which is what makes "collect, validate, then delete" testable.
    base, handler = neon_api
    handler.branches = [
        branch("preview/x", days_old=OLD_DAYS, branch_id="b1", default=True),
        branch("preview/old", days_old=OLD_DAYS, branch_id="b2"),
    ]
    done = run(base)
    assert done.returncode == 1
    assert handler.deleted == []
    assert "preview/x" in done.stderr
    assert "default" in done.stderr


def test_dry_run_reports_what_it_would_delete_and_deletes_nothing(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    base, handler = neon_api
    handler.branches = [
        branch("preview/old", days_old=OLD_DAYS, branch_id="b1"),
        branch("main", days_old=OLD_DAYS, branch_id="b2", default=True),
    ]
    done = run(base, DRY_RUN="1")
    assert done.returncode == 0, done.stderr
    assert handler.deleted == []
    assert "Would delete 'preview/old'" in done.stdout
    # Nothing was deleted, so both branches are still there: the summary has to say 0,
    # not report the candidate as gone.
    assert "deleted=0 kept=2" in done.stdout


def test_finds_an_old_preview_listed_on_a_later_page(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # Branch lists are updated_at-descending by default, so a project with many recent
    # branches can push an old one to page two. Missing it would leave the cap full.
    base, handler = neon_api
    handler.pages = [
        [branch("main", days_old=OLD_DAYS, branch_id="b1", default=True)],
        [branch("preview/old", days_old=OLD_DAYS, branch_id="br-7")],
    ]
    done = run(base)
    assert done.returncode == 0, done.stderr
    assert handler.deleted == ["br-7"]
    assert any(path.endswith("?limit=100") for path in handler.paths)
    assert any("?limit=100&cursor=c1" in path for path in handler.paths)
    assert len(handler.paths) == 2


@pytest.mark.parametrize("updated_at", [None, "not-a-date", "2020-01-01T00:00:00"])
def test_unusable_updated_at_aborts_without_deleting(
    neon_api: tuple[str, type[_NeonHandler]], updated_at: str | None
) -> None:
    # Age is the only guard against deleting a live branch. A timestamp the script cannot
    # interpret must fail the sweep, never default to "old" or to "new".
    base, handler = neon_api
    item = branch("preview/old", days_old=OLD_DAYS, branch_id="b1")
    if updated_at is None:
        del item["updated_at"]
    else:
        item["updated_at"] = updated_at
    handler.branches = [item, branch("preview/other", days_old=OLD_DAYS, branch_id="b2")]
    done = run(base)
    assert done.returncode == 1
    assert handler.deleted == []
    assert "updated_at" in done.stderr


def test_a_future_timestamp_is_kept_not_treated_as_ancient(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # Clock skew or a bad API response must not turn a negative age into "older than
    # MAX_AGE_DAYS".
    base, handler = neon_api
    handler.branches = [branch("preview/future", days_old=-30, branch_id="b1")]
    done = run(base)
    assert done.returncode == 0, done.stderr
    assert handler.deleted == []
    assert "deleted=0 kept=1" in done.stdout


def test_max_age_days_overrides_the_default(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    # MAX_AGE_DAYS is the operator's only knob; a 3-day-old branch is kept at the default
    # 7 and deleted at 2.
    base, handler = neon_api
    handler.branches = [branch("preview/three-days", days_old=3, branch_id="b1")]

    default = run(base)
    assert default.returncode == 0, default.stderr
    assert handler.deleted == []

    shortened = run(base, MAX_AGE_DAYS="2")
    assert shortened.returncode == 0, shortened.stderr
    assert handler.deleted == ["b1"]


def test_delete_treats_404_as_success(neon_api: tuple[str, type[_NeonHandler]]) -> None:
    # Vercel deletes the branch when the last deployment for it goes away, so the branch
    # can vanish between the list call and the DELETE. The end state is the same.
    base, handler = neon_api
    handler.branches = [branch("preview/old", days_old=OLD_DAYS, branch_id="b1")]
    handler.delete_status = 404
    done = run(base)
    assert done.returncode == 0, done.stderr
    assert "deleted=1" in done.stdout


def test_delete_fails_loudly_on_any_other_error(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    base, handler = neon_api
    handler.branches = [branch("preview/old", days_old=OLD_DAYS, branch_id="b1")]
    handler.delete_status = 401
    done = run(base)
    assert done.returncode == 1
    assert "HTTP 401" in done.stderr


def test_the_api_key_never_reaches_curl_s_argv(
    tmp_path: Path, neon_api: tuple[str, type[_NeonHandler]]
) -> None:
    # The key travels only inside curl's --config file. A process's argv is readable by
    # every user on the runner through /proc, so "Authorization: Bearer <key>" on the
    # command line would leak it. Intercept curl on PATH and record every argv.
    base, handler = neon_api
    real_curl = shutil.which("curl")
    assert real_curl is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "curl_argv.log"
    argv_log.touch()
    shim = bin_dir / "curl"
    shim.write_text(
        f'#!/bin/bash\nprintf "%s\\0" "$@" >> "$CURL_ARGV_LOG"\nexec "{real_curl}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    handler.branches = [branch("preview/old", days_old=OLD_DAYS, branch_id="b1")]
    done = run(
        base,
        PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
        CURL_ARGV_LOG=str(argv_log),
    )
    assert done.returncode == 0, done.stderr
    argv_items = [item.decode() for item in argv_log.read_bytes().split(b"\0") if item.decode()]
    assert argv_items
    assert any("--config" in item for item in argv_items)
    assert all(item != "k" for item in argv_items)
    assert all("Bearer" not in item for item in argv_items)


@pytest.mark.parametrize("value", ["0", "-1", "seven", "7.5", ""])
def test_max_age_days_must_be_a_positive_integer(
    neon_api: tuple[str, type[_NeonHandler]], value: str
) -> None:
    # A typo here must be a usage error, not "0 days, delete every preview" or "never
    # delete anything and let the branch cap fill".
    base, _ = neon_api
    done = run(base, MAX_AGE_DAYS=value)
    assert done.returncode == 2
    assert len(done.stderr.strip().splitlines()) == 1
    assert "MAX_AGE_DAYS" in done.stderr


def test_missing_credentials_are_a_usage_failure(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    base, _ = neon_api
    done = run(base, NEON_API_KEY=None)
    assert done.returncode != 0
    assert "NEON_API_KEY is required" in done.stderr


def test_an_unparseable_branch_list_aborts_without_deleting(
    neon_api: tuple[str, type[_NeonHandler]],
) -> None:
    # A captive portal, proxy error page or truncated body must never be read as "no
    # branches to delete" or as a list of branches. Fail closed.
    base, handler = neon_api
    handler.raw_body = b"<html>not json</html>"
    done = run(base)
    assert done.returncode == 1
    assert handler.deleted == []
    assert "could not be parsed" in done.stderr
