from typing import Any
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jobscraper.models import MatchTier
from jobscraper.retention import RetentionSettings, plan_retention, run_retention
from jobscraper.storage.google_sheets import GoogleSheetsStorage
from jobscraper.storage.sqlite import SQLiteStorage
from tests.helpers import make_job
from tests.test_storage import FakeWorksheet

NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)


def ago(days: float) -> str:
    return (NOW - timedelta(days=days)).isoformat()


def job_row(
    job_id: str,
    first_seen_days: float = 1,
    last_seen_days: float = 0,
    status: str = "New",
    active: str = "TRUE",
    **kw: str,
) -> dict[str, str]:
    return {
        "job_id": job_id,
        "first_seen": ago(first_seen_days),
        "last_seen": ago(last_seen_days),
        "application_status": status,
        "is_active": active,
        **kw,
    }


def plan(jobs=(), excluded=(), runs=(), health=(), **kw):
    return plan_retention(
        list(jobs), list(excluded), list(runs), list(health), NOW, RetentionSettings(**kw)
    )


def test_old_new_jobs_are_deleted_but_worked_jobs_are_kept() -> None:
    jobs = [
        job_row("old-new", 61, 61),
        job_row("young", 59),
        job_row("old-applied", 90, 90, status="Applied"),
        job_row("old-ignored", 90, 90, status="Ignored"),
        job_row("old-saved", 90, 90, status="Saved"),
        job_row("old-blank-status", 61, 61, status=""),
        job_row("bad-date", first_seen_days=0) | {"first_seen": "sometime", "last_seen": ""},
    ]
    result = plan(jobs)
    assert sorted(result.delete_jobs) == ["old-blank-status", "old-new"]


def test_jobs_not_seen_for_a_week_become_inactive_once() -> None:
    jobs = [
        job_row("stale", 20, 8),
        job_row("fresh", 20, 6),
        job_row("already", 20, 30, active="FALSE"),
        job_row("doomed", 70, 70),
    ]
    result = plan(jobs)
    assert [u.job_id for u in result.deactivate] == ["stale"] and result.deactivate[0].fields == {
        "is_active": "FALSE"
    }
    assert result.delete_jobs == ["doomed"]  # a row being deleted is not also deactivated


def test_logs_and_audit_rows_use_their_own_ages() -> None:
    result = plan(
        excluded=[
            {"job_id": "e1", "excluded_at": ago(31)},
            {"job_id": "e2", "excluded_at": ago(29)},
        ],
        runs=[{"run_id": "r1", "started_utc": ago(31)}, {"run_id": "r2", "started_utc": ago(2)}],
        health=[
            {"key": "r1:x", "started_utc": ago(40)},
            {"key": "r2:x", "started_utc": ago(1)},
            {"key": "", "started_utc": ago(99)},
        ],
    )
    assert (result.delete_excluded, result.delete_runs, result.delete_health) == (
        ["e1"],
        ["r1"],
        ["r1:x"],
    )


def test_a_plan_that_deletes_most_of_the_sheet_is_blocked() -> None:
    jobs = [job_row(f"j{i}", 70, 70) for i in range(30)] + [job_row(f"k{i}") for i in range(5)]
    assert plan(jobs).blocked and "refusing to delete 30 of 35" in plan(jobs).blocked
    assert plan(jobs[:10]).blocked is None  # small sheets are not second-guessed
    assert (
        plan(
            [job_row(f"j{i}", 70, 70) for i in range(30)] + [job_row(f"k{i}") for i in range(60)]
        ).blocked
        is None
    )


def stored(days_old: list[float]) -> SQLiteStorage:
    storage = SQLiteStorage()
    storage.append_jobs(
        [
            make_job(
                job_id=f"j{i}",
                source_job_id=str(i),
                job_url=f"https://x.com/{i}",
                match_tier=MatchTier.TOP,
                match_score=90,
                first_seen=NOW - timedelta(days=d),
                last_seen=NOW - timedelta(days=d),
            )
            for i, d in enumerate(days_old)
        ]
    )
    return storage


def test_run_retention_applies_the_plan_and_leaves_user_work_alone() -> None:
    storage = stored([70, 70, 3, 70])
    storage.set_user_cell("j3", "application_status", "Applied")
    storage.append_excluded([])
    result = run_retention(storage, NOW)
    assert sorted(result.delete_jobs) == ["j0", "j1"]
    remaining = {r["job_id"]: r for r in storage.load_rows()}
    assert set(remaining) == {"j2", "j3"} and remaining["j3"]["application_status"] == "Applied"


def test_dry_run_and_blocked_plans_change_nothing() -> None:
    storage = stored([70] * 25 + [1])
    blocked = run_retention(storage, NOW)
    assert blocked.blocked and len(storage.load_rows()) == 26
    small = stored([70, 1])
    run_retention(small, NOW, dry_run=True)
    assert len(small.load_rows()) == 2


def test_stale_jobs_are_marked_inactive_in_storage() -> None:
    storage = stored([20])
    storage.update_jobs([])
    row_before = storage.load_rows()[0]
    assert row_before["is_active"] == "TRUE"
    run_retention(storage, NOW)
    assert storage.load_rows()[0]["is_active"] == "FALSE"


def test_sheet_deletes_by_key_in_one_batched_request_and_keeps_other_rows() -> None:
    jobs_ws, health_ws = FakeWorksheet(), FakeWorksheet()
    storage = GoogleSheetsStorage(jobs_ws, None, None, health_ws)
    storage.append_jobs(
        [
            make_job(job_id=f"j{i}", source_job_id=str(i), job_url=f"https://x.com/{i}")
            for i in range(6)
        ]
    )
    assert storage.delete_rows("jobs", "job_id", {"j1", "j2", "j4"}) == 3
    headers = jobs_ws.values[0]
    left = [row[headers.index("job_id")] for row in jobs_ws.values[1:]]
    assert left == ["j0", "j3", "j5"] and jobs_ws.values[0] == headers
    assert jobs_ws.spreadsheet.calls == 1
    assert (
        storage.delete_rows("jobs", "job_id", {"nope"}) == 0
        and storage.delete_rows("jobs", "job_id", set()) == 0
    )


def test_sheet_health_tab_round_trip_and_cleanup() -> None:
    from jobscraper.models import SourceRun, SourceStatus

    health_ws = FakeWorksheet()
    storage = GoogleSheetsStorage(FakeWorksheet(), None, None, health_ws)
    storage.append_source_runs(
        [
            SourceRun(
                run_id="old",
                started_utc=NOW - timedelta(days=40),
                source="a",
                status=SourceStatus.OK,
                found=3,
            ),
            SourceRun(run_id="new", started_utc=NOW, source="a", status=SourceStatus.FAILED),
        ]
    )
    assert [r.run_id for r in storage.load_source_runs()] == ["new", "old"]
    storage.delete_rows(
        "health", "key", set(plan(health=storage.load_table("health")).delete_health)
    )
    assert [r.run_id for r in storage.load_source_runs()] == ["new"]