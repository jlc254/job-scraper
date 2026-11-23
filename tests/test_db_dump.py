"""Contract tests for scripts/db_dump.sh.

The script is the only thing standing between the project and Neon's six-hour PITR
window, so these tests hold three properties: a dump can never be produced from a pooled
DSN, the published artifact is only ever a verified one (never a partial or truncated
file), and the database password never appears in a process argument list.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "db_dump.sh"

# A direct host and the same branch's pooled host. The pooled check matches the
# `-pooler.` suffix Neon puts in front of the endpoint id.
DIRECT_DSN = (
    "postgresql://publisher:s3cret@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb"
    "?sslmode=require"
)
POOLED_DSN = (
    "postgresql://publisher:s3cret@ep-cool-name-123456-pooler.us-east-2.aws.neon.tech/neondb"
    "?sslmode=require"
)

# Stands in for the docker client. It receives the same argv the real one would, records
# it, and emulates the container side effect that matters: pg_dump writing the dump file
# into the bind-mounted directory, and pg_restore --list succeeding or failing.
SHIM = """#!/usr/bin/env bash
printf '%s\\0' "$@" >> "$DOCKER_ARGV_LOG"
out_dir=""
prev=""
for arg in "$@"; do
  if [ "$prev" = "--volume" ] || [ "$prev" = "-v" ]; then
    out_dir="${arg%%:*}"
  fi
  prev="$arg"
done
if [ -z "$out_dir" ] || [ ! -d "$out_dir" ]; then
  echo "shim: no usable --volume mount" >&2
  exit 90
fi
case "$*" in
  *pg_dump*)
    if [ "${FAKE_DUMP_STATUS:-0}" != "0" ]; then
      exit "${FAKE_DUMP_STATUS}"
    fi
    dd if=/dev/zero of="$out_dir/$DUMP_NAME" bs=1 count="${FAKE_DUMP_BYTES:-20480}" \\
      status=none
    ;;
  *pg_restore*)
    exit "${FAKE_RESTORE_STATUS:-0}"
    ;;
  *)
    echo "shim: unexpected command: $*" >&2
    exit 91
    ;;
esac
"""


@dataclass(frozen=True)
class Stub:
    docker: Path
    out: Path
    log: Path

    def argv(self) -> list[str]:
        return [item.decode() for item in self.log.read_bytes().split(b"\0") if item]


@pytest.fixture
def stub(tmp_path: Path) -> Stub:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    out = tmp_path / "dumps"
    log = tmp_path / "argv.log"
    log.touch()
    docker = bin_dir / "docker"
    docker.write_text(SHIM, encoding="utf-8")
    docker.chmod(0o755)
    return Stub(docker=docker, out=out, log=log)


def run(
    stub: Stub, *, cwd: Path | None = None, **overrides: str | None
) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "DOCKER": str(stub.docker),
        "DOCKER_ARGV_LOG": str(stub.log),
        "DUMP_DIR": str(stub.out),
        "NEON_DATABASE_URL_PUBLISHER": DIRECT_DSN,
    }
    env.update(overrides)
    return subprocess.run(  # noqa: S603
        ["bash", str(SCRIPT)],  # noqa: S607
        capture_output=True,
        text=True,
        cwd=cwd,
        env={k: v for k, v in env.items() if v is not None},
        timeout=60,
    )


def dumps(stub: Stub) -> list[Path]:
    if not stub.out.exists():
        return []
    return sorted(p for p in stub.out.iterdir() if p.name.startswith("backup-"))


SEEDED = b"previous verified dump"


def seed_existing_dump(stub: Stub) -> Path:
    stub.out.mkdir(parents=True, exist_ok=True)
    path = stub.out / "backup-20200101.dump"
    path.write_bytes(SEEDED)
    return path


def assert_only_the_previous_dump_survives(stub: Stub, previous: Path) -> None:
    assert dumps(stub) == [previous]
    assert previous.read_bytes() == SEEDED
    assert list(stub.out.iterdir()) == [previous]


def test_refuses_a_pooled_dsn(stub: Stub) -> None:
    # pgbouncer in transaction mode breaks the session guarantees pg_dump relies on (it
    # can hand the dump different backends mid-run). The audit calls this out as SEC-06's
    # sibling failure: a "backup" that silently holds a truncated snapshot.
    done = run(stub, NEON_DATABASE_URL_PUBLISHER=POOLED_DSN)
    assert done.returncode == 2
    assert len(done.stderr.strip().splitlines()) == 1
    assert "pooled" in done.stderr
    assert dumps(stub) == []
    # The refusal happens before docker is invoked at all.
    assert stub.argv() == []


def test_a_missing_dsn_is_a_usage_error(stub: Stub) -> None:
    done = run(stub, NEON_DATABASE_URL_PUBLISHER=None)
    assert done.returncode == 2
    assert len(done.stderr.strip().splitlines()) == 1
    assert "NEON_DATABASE_URL_PUBLISHER" in done.stderr
    assert dumps(stub) == []
    assert stub.argv() == []


def test_writes_and_verifies_a_custom_format_dump(stub: Stub) -> None:
    done = run(stub)
    assert done.returncode == 0, done.stderr
    files = dumps(stub)
    assert len(files) == 1
    assert re.fullmatch(r"backup-\d{8}\.dump", files[0].name), files[0].name
    assert files[0].stat().st_size == 20480
    # The partial dot-file is renamed only after verification, so it must not survive.
    assert [p.name for p in stub.out.iterdir()] == [files[0].name]
    assert "verified" in done.stdout
    container_argv = " ".join(stub.argv())
    assert "--format=custom" in container_argv
    assert "--no-owner" in container_argv
    assert "--no-privileges" in container_argv
    assert "postgres:18" in stub.argv()


def test_a_dump_below_the_size_floor_is_discarded(stub: Stub) -> None:
    # An empty or header-only custom dump can still be listed by pg_restore; the size
    # floor is what catches "connected, dumped nothing" before it becomes the artifact
    # everyone trusts. The previous verified dump must survive the failure.
    previous = seed_existing_dump(stub)
    done = run(stub, FAKE_DUMP_BYTES="100")
    assert done.returncode == 1
    assert "too small" in done.stderr
    assert_only_the_previous_dump_survives(stub, previous)


def test_a_dump_pg_restore_cannot_list_is_discarded(stub: Stub) -> None:
    previous = seed_existing_dump(stub)
    done = run(stub, FAKE_RESTORE_STATUS="1")
    assert done.returncode == 1
    assert "pg_restore" in done.stderr
    assert_only_the_previous_dump_survives(stub, previous)


def test_a_failed_pg_dump_is_discarded(stub: Stub) -> None:
    previous = seed_existing_dump(stub)
    done = run(stub, FAKE_DUMP_STATUS="1")
    assert done.returncode == 1
    assert "pg_dump failed" in done.stderr
    assert_only_the_previous_dump_survives(stub, previous)


def test_the_password_never_reaches_docker_s_argv(stub: Stub) -> None:
    # docker's argv is visible in /proc to every user on the runner. The DSN travels as an
    # environment variable into the container (`--env PGURL` with no value), so the host
    # expands it from this script's environment instead of naming it on the command line.
    done = run(stub)
    assert done.returncode == 0, done.stderr
    argv = stub.argv()
    assert argv
    assert "s3cret" not in " ".join(argv)
    assert DIRECT_DSN not in argv
    assert "--env" in argv
    assert "PGURL" in argv
    # A value-carrying --env would put the secret in argv; the flag must stand alone.
    assert "PGURL=" not in " ".join(argv)


@pytest.mark.parametrize(
    "dsn",
    [
        # `-pooler.` in the password, database name, and query string, but not the host.
        "postgresql://publisher:s3cret-pooler.invalid@ep-direct.us-east-2.aws.neon.tech"
        "/neondb?sslmode=require",
        "postgresql://publisher:s3cret@ep-direct.us-east-2.aws.neon.tech/some-pooler.db"
        "?sslmode=require",
        "postgresql://publisher:s3cret@ep-direct.us-east-2.aws.neon.tech/neondb"
        "?application_name=x-pooler.y&sslmode=require",
    ],
)
def test_a_pooler_lookalike_outside_the_host_is_accepted(stub: Stub, dsn: str) -> None:
    # The guard must judge the host only. Rejecting a direct URL because its password,
    # database name or query happens to contain `-pooler.` would block a valid backup.
    done = run(stub, NEON_DATABASE_URL_PUBLISHER=dsn)
    assert done.returncode == 0, done.stderr
    assert len(dumps(stub)) == 1


def test_a_pooled_host_is_refused_even_with_a_lookalike_in_the_userinfo(
    stub: Stub,
) -> None:
    dsn = (
        "postgresql://publisher:s3cret-pooler.invalid@ep-cool-name-123456-pooler"
        ".us-east-2.aws.neon.tech/neondb?sslmode=require"
    )
    done = run(stub, NEON_DATABASE_URL_PUBLISHER=dsn)
    assert done.returncode == 2
    assert "pooled" in done.stderr
    assert stub.argv() == []


def test_the_default_dump_directory_is_backups(stub: Stub, tmp_path: Path) -> None:
    # A local run must not drop a production dump in the repository root where a broad
    # `git add` could stage it.
    done = run(stub, cwd=tmp_path, DUMP_DIR=None)
    assert done.returncode == 0, done.stderr
    written = sorted((tmp_path / "backups").iterdir())
    assert len(written) == 1
    assert re.fullmatch(r"backup-\d{8}\.dump", written[0].name)


def test_the_dump_directory_is_created_when_missing(stub: Stub) -> None:
    assert not stub.out.exists()
    done = run(stub)
    assert done.returncode == 0, done.stderr
    assert len(dumps(stub)) == 1
