"""The whole `run` command against SQLite, with HTTP mocked. No network, no Telegram, no Sheet."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import respx

from jobscraper import cli
from jobscraper.models import SourceRun, SourceStatus
from jobscraper.storage.sqlite import SQLiteStorage
from jobscraper.utils.http import HttpClient
from tests.conftest import load_fixture

CONFIG = Path(__file__).parent.parent / "config"
HIMALAYAS = "https://himalayas.app/jobs/api"
JOBICY = "https://jobicy.com/api/v2/remote-jobs"
SOURCES_YAML = """
sources:
  himalayas: {enabled: true, status: verified, verified_on: 2026-10-01, terms_url: "https://example.com/t", max_pages: 1}
  jobicy: {enabled: true, status: verified, verified_on: 2026-10-01, terms_url: "https://example.com/t"}
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # output/ lands in the temp folder
    monkeypatch.setattr(cli, "_now", lambda: datetime(2026, 10, 1, 3, 0, tzinfo=UTC))
    monkeypatch.setattr(
        cli,
        "CLIENT_FACTORY",
        lambda adapter: HttpClient(
            adapter.allowed_hosts,
            resolver=lambda h: ["93.184.216.34"],
            sleep=lambda s: None,
            min_interval_s=0,
        ),
    )
    (tmp_path / "sources.yaml").write_text(SOURCES_YAML, encoding="utf-8")
    return tmp_path


def run_cli(env: Path, *extra: str) -> int:
    return cli.main(
        [
            "run",
            "--config",
            str(env / "sources.yaml"),
            "--profile",
            str(CONFIG / "profile.example.yaml"),
            "--scoring",
            str(CONFIG / "scoring.example.yaml"),
            "--storage",
            "sqlite",
            "--db",
            str(env / "jobs.db"),
            "--no-notify",
            "--no-cleanup",
            "--no-csv",
            *extra,
        ]
    )


def mock_sources(jobicy_status: int = 500, himalayas_ok: bool = True) -> None:
    if himalayas_ok:
        respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    else:
        respx.get(HIMALAYAS).respond(500)
    respx.get(JOBICY).respond(jobicy_status)


@respx.mock
def test_a_broken_source_is_recorded_and_the_run_still_succeeds(env: Any, capsys: Any) -> None:
    mock_sources()
    assert run_cli(env) == 0
    out = capsys.readouterr().out
    assert "himalayas: ok" in out and "jobicy: failed" in out and "Excluded: 2" in out
    db = SQLiteStorage(env / "jobs.db")
    assert len(db.load_rows()) == 1  # one Himalayas job passed the filters
    assert {(r.source, r.status) for r in db.load_source_runs()} == {
        ("himalayas", SourceStatus.OK),
        ("jobicy", SourceStatus.FAILED),
    }
    assert len(db.load_table("runs")) == 1 and len(db.load_table("excluded")) == 2


@respx.mock
def test_second_run_adds_nothing(env: Any) -> None:
    mock_sources()
    assert run_cli(env) == 0 and run_cli(env) == 0
    db = SQLiteStorage(env / "jobs.db")
    assert (
        len(db.load_rows()) == 1
        and len(db.load_table("excluded")) == 2
        and len(db.load_table("runs")) == 2
    )


@respx.mock
def test_third_bad_run_in_a_row_raises_the_health_alert(env: Any, capsys: Any) -> None:
    db = SQLiteStorage(env / "jobs.db")
    base = datetime(2026, 9, 29, tzinfo=UTC)
    db.append_source_runs(
        [
            SourceRun(
                run_id=f"r{i}",
                started_utc=base + timedelta(hours=12 * i),
                source="jobicy",
                status=SourceStatus.FAILED,
            )
            for i in range(2)
        ]
    )
    mock_sources()
    assert run_cli(env) == 0
    out = capsys.readouterr().out
    assert (
        "source health alert (not sent)" in out
        and "Jobicy has not been healthy for 3 runs in a row" in out
    )


@respx.mock
def test_first_bad_run_is_not_an_alert_but_is_in_the_report(env: Any, capsys: Any) -> None:
    mock_sources()
    run_cli(env)
    out = capsys.readouterr().out
    assert "source health alert" not in out and "RUN REPORT" in out


@respx.mock
def test_no_data_at_all_is_a_failed_run(env: Any, capsys: Any) -> None:
    mock_sources(himalayas_ok=False)
    assert run_cli(env) == 5
    assert "no source returned data" in capsys.readouterr().err
    assert (
        len(SQLiteStorage(env / "jobs.db").load_source_runs()) == 2
    )  # the failure is still recorded


@respx.mock
def test_dry_run_touches_no_storage(env: Any, capsys: Any) -> None:
    mock_sources()
    assert (
        cli.main(
            [
                "run",
                "--dry-run",
                "--no-notify",
                "--no-csv",
                "--config",
                str(env / "sources.yaml"),
                "--profile",
                str(CONFIG / "profile.example.yaml"),
                "--scoring",
                str(CONFIG / "scoring.example.yaml"),
            ]
        )
        == 0
    )
    assert not (env / "jobs.db").exists() and "digest preview" in capsys.readouterr().out


@respx.mock
def test_unknown_source_is_a_config_error(env: Any, capsys: Any) -> None:
    assert run_cli(env, "--sources", "nope") == 2 and "unknown source" in capsys.readouterr().err


@respx.mock
def test_a_profile_allowlist_drives_the_fetch_set(env: Any, capsys: Any) -> None:
    """Without --sources, the run fetches the union of the active profiles' allowlists.

    A configured source no profile references must not cost a request (doc 15).
    """
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    respx.get(JOBICY).respond(200, json=load_fixture("jobicy.json"))
    (env / "profiles.yaml").write_text(
        "profiles:\n"
        "  - id: support\n"
        "    label: Customer support\n"
        f"    profile: {CONFIG / 'profile.example.yaml'}\n"
        f"    scoring: {CONFIG / 'scoring.example.yaml'}\n"
        "    sources: [himalayas]\n",
        encoding="utf-8",
    )
    assert run_cli(env, "--profiles", str(env / "profiles.yaml")) == 0
    out = capsys.readouterr().out
    assert "himalayas: ok" in out and "jobicy" not in out
    assert respx.get(JOBICY).call_count == 0


@respx.mock
def test_cleanup_health_and_recover_commands(env: Any, capsys: Any) -> None:
    mock_sources()
    run_cli(env)
    db = ["--storage", "sqlite", "--db", str(env / "jobs.db")]
    assert (
        cli.main(["cleanup", "--dry-run", *db]) == 0 and "Would remove" in capsys.readouterr().out
    )
    assert cli.main(["health", *db]) == 0 and "Himalayas" in capsys.readouterr().out
    assert cli.main(["recover", *db]) == 0 and "no unsaved" in capsys.readouterr().out


def test_recover_re_adds_jobs_saved_after_a_storage_failure(env: Any, capsys: Any) -> None:
    from jobscraper.pipeline import save_unsaved
    from tests.helpers import make_job

    job = make_job(job_id="lost", job_url="https://x.com/lost", source_job_id="lost-1")
    save_unsaved([job], env / "output")
    db = ["--storage", "sqlite", "--db", str(env / "jobs.db")]
    assert cli.main(["recover", *db]) == 0
    assert "Recovered 1 new jobs from 1 file(s)" in capsys.readouterr().out
    assert [p.suffix for p in (env / "output").glob("unsaved-*")] == [".recovered"]
    assert cli.main(["recover", *db]) == 0  # nothing left to recover, and nothing duplicated
    assert len(SQLiteStorage(env / "jobs.db").load_rows()) == 1


def test_sources_check_command_refuses_unverifiable_selection(env: Any, capsys: Any) -> None:
    assert (
        cli.main(["sources", "check", "--config", str(env / "sources.yaml"), "--sources", "nope"])
        == 2
    )
    assert "unknown source" in capsys.readouterr().err
