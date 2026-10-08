from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, timedelta
from typing import Any

from jobscraper import cli
from jobscraper.dashboard import (
    JOB_HEADERS,
    build_dashboard,
    refresh_dashboard,
    write_csv_dir,
)
from jobscraper.models import MatchTier
from jobscraper.models.dashboard import DashboardTable, csv_value, sheet_serial, sheet_value
from jobscraper.storage.google_sheets import GoogleSheetsStorage
from jobscraper.storage.sqlite import SQLiteStorage
from tests.helpers import make_job
from tests.test_storage import FakeBook, FakeWorksheet

NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)  # 06:00 in Nairobi
BREAKDOWN = json.dumps(
    {
        "version": 1,
        "total": 85.5,
        "tier": "top",
        "factors": {
            "title": {"points": 25},
            "skills": {"points": 17.5},
            "location": {"points": 20},
            "experience": {"points": 10},
            "salary": {"points": 5},
            "freshness": {"points": 5},
            "industry": {"points": 3},
        },
        "skills": {
            "required": ["zendesk", "freshdesk", "linux"],
            "preferred": ["crm"],
            "matched": ["zendesk", "crm"],
            "partial": ["linux"],
            "missing": ["freshdesk"],
        },
    }
)


def job_row(i: int = 1, **kw: str) -> dict[str, str]:
    base = {
        "job_id": f"j{i}",
        "title": f"Customer Support Agent {i}",
        "company": "Acme",
        "source": "himalayas",
        "match_tier": "top",
        "match_score": "85.5",
        "application_status": "New",
        "first_seen": NOW.isoformat(),
        "date_posted": "2026-09-29",
        "application_deadline": "2026-10-20",
        "work_type": "remote",
        "remote_eligibility": "africa",
        "location": "Remote - Africa",
        "salary": "USD 800-1,200",
        "is_active": "TRUE",
        "notified_at": "",
        "is_repost": "",
        "skills_matched": "zendesk; crm",
        "skills_missing": "freshdesk",
        "match_breakdown": BREAKDOWN,
        "job_url": f"https://example.com/{i}",
        "notes": "PRIVATE NOTE",
        "description_excerpt": "PRIVATE TEXT",
        "all_urls": "https://a.example/1",
    }
    base.update(kw)
    return base


def build(jobs=(), excluded=(), runs=(), health=(), **kw) -> dict[str, DashboardTable]:
    tables = build_dashboard(
        jobs=list(jobs),
        excluded=list(excluded),
        runs=list(runs),
        health=list(health),
        now=NOW,
        **kw,
    )
    return {t.name: t for t in tables}


def record(table: DashboardTable, index: int = 0) -> dict[str, object]:
    return dict(zip(table.headers, table.rows[index], strict=True))


# ---- the tables ------------------------------------------------------------------------------


def test_there_is_one_table_per_looker_data_source() -> None:
    tables = build()
    assert list(tables) == [
        "Dash_Jobs",
        "Dash_Skills",
        "Dash_Sources",
        "Dash_Runs",
        "Dash_Excluded",
        "Dash_Meta",
    ]
    assert all(
        len(set(t.headers)) == len(t.headers) for t in tables.values()
    )  # one header row, unique names
    assert all(len(row) == len(t.headers) for t in tables.values() for row in t.rows)


def test_jobs_are_typed_and_derived_correctly() -> None:
    rec = record(build([job_row()])["Dash_Jobs"])
    assert (rec["tier"], rec["tier_rank"], rec["score"], rec["status"]) == ("top", 1, 85.5, "New")
    assert (
        rec["first_seen"] == date(2026, 10, 1)
        and rec["posted"] == date(2026, 9, 29)
        and rec["deadline"] == date(2026, 10, 20)
    )
    assert rec["is_active"] is True and rec["notified"] is False and rec["is_repost"] is False
    assert (rec["matched_count"], rec["missing_count"], rec["scoring_version"]) == (2, 1, 1)
    assert [
        rec[f"{f}_pts"]
        for f in ("title", "skills", "location", "experience", "salary", "freshness", "industry")
    ] == [25.0, 17.5, 20.0, 10.0, 5.0, 5.0, 3.0]
    assert rec["url"] == "https://example.com/1"


def test_dates_are_shown_in_nairobi_time() -> None:
    late = datetime(2026, 10, 1, 22, 30, tzinfo=UTC)  # already 1 October 01:30 + a day in Nairobi
    rec = record(build([job_row(first_seen=late.isoformat())])["Dash_Jobs"])
    assert rec["first_seen"] == date(2026, 10, 2)


def test_private_columns_never_reach_the_dashboard() -> None:
    tables = build([job_row()], excluded=[], runs=[], health=[])
    everything = " ".join(
        str(c) for t in tables.values() for row in t.rows for c in row
    ) + " ".join(h for t in tables.values() for h in t.headers)
    for private in (
        "PRIVATE NOTE",
        "PRIVATE TEXT",
        "a.example",
        "notes",
        "description_excerpt",
        "all_urls",
    ):
        assert private not in everything


def test_follow_up_due_only_for_applied_jobs() -> None:
    applied = job_row(1, application_status="Applied", applied_on="2026-09-24")
    own_date = job_row(
        2, application_status="Applied", applied_on="2026-09-24", follow_up_date="2026-10-03"
    )
    not_applied = job_row(3, application_status="Saved", applied_on="2026-09-24")
    tables = build([applied, own_date, not_applied])["Dash_Jobs"]
    due = {r["job_id"]: r["follow_up_due"] for r in (record(tables, i) for i in range(3))}
    assert due == {"j1": date(2026, 10, 1), "j2": date(2026, 10, 3), "j3": None}
    assert record(build([applied], follow_up_days=10)["Dash_Jobs"])["follow_up_due"] == date(
        2026, 10, 4
    )


def test_newest_jobs_come_first_and_ties_break_on_score() -> None:
    older = job_row(1, first_seen=(NOW - timedelta(days=3)).isoformat(), match_score="99")
    low, high = job_row(2, match_score="60"), job_row(3, match_score="90")
    assert [r[0] for r in build([older, low, high])["Dash_Jobs"].rows] == ["j3", "j2", "j1"]


def test_unscored_and_malformed_rows_still_produce_a_row() -> None:
    rows = [
        job_row(
            1, match_tier="", match_score="", match_breakdown="not json", application_status=""
        ),
        job_row(2, match_breakdown='["a list"]', first_seen="garbage", date_posted="soon"),
    ]
    rec = record(build(rows)["Dash_Jobs"], 0)
    assert len(build(rows)["Dash_Jobs"].rows) == 2
    for r in (record(build(rows)["Dash_Jobs"], i) for i in range(2)):
        assert r["scoring_version"] is None and r["title_pts"] is None
    by_id = {r[0]: r for r in build(rows)["Dash_Jobs"].rows}
    assert by_id["j1"][4:8] == ["unscored", 5, None, "New"] and rec["job_id"]
    assert by_id["j2"][8] is None and by_id["j2"][9] is None  # unreadable dates become blanks
    assert build([{"title": "no id"}])["Dash_Jobs"].rows == []


def test_skills_are_exploded_one_row_per_job_and_skill() -> None:
    table = build([job_row()])["Dash_Skills"]
    got = {(r[4], r[5], r[6]) for r in table.rows}
    assert got == {
        ("zendesk", "required", "matched"),
        ("freshdesk", "required", "missing"),
        ("linux", "required", "partial"),
        ("crm", "preferred", "matched"),
    }
    assert record(table)["tier"] == "top" and record(table)["first_seen"] == date(2026, 10, 1)
    assert build([job_row(match_breakdown="")])["Dash_Skills"].rows == []


def test_run_history_tables() -> None:
    health = [
        {
            "started_utc": NOW.isoformat(),
            "source": "jobicy",
            "status": "failed",
            "found": "0",
            "new": "0",
            "dropped": "0",
            "excluded": "0",
            "error": "HTTP 500",
        },
        {
            "started_utc": (NOW - timedelta(hours=12)).isoformat(),
            "source": "jobicy",
            "status": "ok",
            "found": "12",
            "new": "3",
            "dropped": "1",
            "excluded": "2",
            "error": "",
        },
        {"started_utc": "garbage", "source": "x", "status": "ok"},
    ]
    runs = [
        {
            "run_id": "r1",
            "started_utc": NOW.isoformat(),
            "duration_s": "41.5",
            "found": "12",
            "new": "3",
            "duplicates": "2",
        }
    ]
    excluded = [
        {
            "job_id": "e1",
            "excluded_at": NOW.isoformat(),
            "source": "himalayas",
            "reason": "off_topic",
            "title": "Dev",
            "company": "X",
            "detail": "d",
        }
    ]
    t = build(health=health, runs=runs, excluded=excluded)
    assert [(r[2], r[3], r[4], r[5]) for r in t["Dash_Sources"].rows] == [
        ("jobicy", "failed", False, 0),
        ("jobicy", "ok", True, 12),
    ]
    assert t["Dash_Sources"].rows[0][0] == datetime(2026, 10, 1, 6, 0) and t["Dash_Sources"].rows[
        0
    ][1] == date(2026, 10, 1)
    assert record(t["Dash_Runs"]) == {
        "run_id": "r1",
        "run_time": datetime(2026, 10, 1, 6, 0),
        "run_date": date(2026, 10, 1),
        "duration_s": 41.5,
        "found": 12,
        "new": 3,
        "duplicates": 2,
    }
    assert record(t["Dash_Excluded"])["reason"] == "off_topic"
    assert record(t["Dash_Meta"]) == {
        "refreshed_at": datetime(2026, 10, 1, 6, 0),
        "jobs": 0,
        "excluded": 1,
        "runs": 1,
        "schema_version": 1,
    }


# ---- cell conversion ---------------------------------------------------------------------------------


def test_sheet_serials_match_google_sheets() -> None:
    assert sheet_serial(date(2026, 10, 1)) == 46296 and sheet_serial(date(1899, 12, 30)) == 0
    assert (
        sheet_serial(datetime(2026, 10, 1, 6, 0)) == 46296.25
        and sheet_serial(datetime(2026, 10, 1, 18, 0)) == 46296.75
    )


def test_sheet_and_csv_values() -> None:
    assert [
        sheet_value(v) for v in (None, True, 3, 2.5, date(2026, 10, 1), "=HYPERLINK(1)", "plain")
    ] == ["", True, 3, 2.5, 46296, "'=HYPERLINK(1)", "plain"]
    assert [
        csv_value(v)
        for v in (None, True, False, datetime(2026, 10, 1, 6, 5), date(2026, 10, 1), "@x", 7)
    ] == ["", "true", "false", "2026-10-01 06:05:00", "2026-10-01", "'@x", 7]


def test_csv_export(tmp_path: Any) -> None:
    paths = write_csv_dir(list(build([job_row()]).values()), tmp_path / "out")
    assert sorted(p.name for p in paths) == sorted(
        f"{n}.csv"
        for n in (
            "Dash_Jobs",
            "Dash_Skills",
            "Dash_Sources",
            "Dash_Runs",
            "Dash_Excluded",
            "Dash_Meta",
        )
    )
    rows = list(csv.DictReader((tmp_path / "out" / "Dash_Jobs.csv").open(encoding="utf-8")))
    assert (
        rows[0]["first_seen"] == "2026-10-01"
        and rows[0]["is_active"] == "true"
        and rows[0]["url"].startswith("https://")
    )


# ---- writing to the Sheet ------------------------------------------------------------------------------


def sheets() -> tuple[GoogleSheetsStorage, FakeBook]:
    book = FakeBook()
    return GoogleSheetsStorage(FakeWorksheet(title="Jobs"), book=book), book


def tab(book: FakeBook, name: str) -> FakeWorksheet:
    return next(ws for ws in book.worksheets() if ws.title == name)


def test_sheet_tabs_are_created_with_typed_cells_and_date_formats() -> None:
    storage, book = sheets()
    storage.write_dashboard(list(build([job_row()]).values()))
    jobs = tab(book, "Dash_Jobs")
    headers = jobs.values[0]
    row = dict(zip(headers, jobs.values[1], strict=True))
    assert headers == JOB_HEADERS
    assert row["first_seen"] == 46296 and isinstance(
        row["first_seen"], int
    )  # a real Sheets date, not text
    assert (
        row["score"] == 85.5
        and row["is_active"] is True
        and row["title"] == "Customer Support Agent 1"
    )
    assert row["applied_on"] == "" and row["follow_up_due"] == ""  # blanks are empty strings
    assert [ws.title for ws in book.worksheets()] == [
        "Dash_Jobs",
        "Dash_Skills",
        "Dash_Sources",
        "Dash_Runs",
        "Dash_Excluded",
        "Dash_Meta",
    ]

    requests = jobs.spreadsheet.other_requests
    assert (
        requests[0]["updateSheetProperties"]["properties"]["gridProperties"]["frozenRowCount"] == 1
    )
    formatted = {r["repeatCell"]["range"]["startColumnIndex"] for r in requests[1:]}
    assert formatted == {
        headers.index(h)
        for h in ("first_seen", "posted", "deadline", "applied_on", "follow_up_due")
    }
    assert all(
        r["repeatCell"]["cell"]["userEnteredFormat"]["numberFormat"]["type"] == "DATE"
        for r in requests[1:]
    )
    meta = tab(book, "Dash_Meta")
    assert meta.values[1][0] == 46296.25
    assert (
        tab(book, "Dash_Meta").spreadsheet.other_requests[1]["repeatCell"]["cell"][
            "userEnteredFormat"
        ]["numberFormat"]["type"]
        == "DATE_TIME"
    )
    assert {ws.id for ws in book.worksheets()} == set(range(1, 7))


def test_a_refresh_replaces_everything_and_does_not_reformat_an_unchanged_layout() -> None:
    storage, book = sheets()
    storage.write_dashboard(
        list(
            build(
                [
                    job_row(1),
                    job_row(2),
                    job_row(3, application_status="Applied", applied_on="2026-09-24"),
                ]
            ).values()
        )
    )
    jobs = tab(book, "Dash_Jobs")
    format_calls = len(jobs.spreadsheet.other_requests)
    assert len(jobs.values) == 4

    storage.write_dashboard(list(build([job_row(1)]).values()))  # the table shrinks
    assert len(jobs.values) == 2 and jobs.values[1][0] == "j1"  # no stale rows left behind
    assert len(jobs.spreadsheet.other_requests) == format_calls  # same headers: formats untouched
    assert len(book.worksheets()) == 6  # tabs are reused, not duplicated


def test_blank_values_overwrite_old_values() -> None:
    storage, book = sheets()
    storage.write_dashboard(
        list(build([job_row(1, application_status="Applied", applied_on="2026-09-24")]).values())
    )
    jobs = tab(book, "Dash_Jobs")
    col = jobs.values[0].index("applied_on")
    assert jobs.values[1][col] == 46289
    storage.write_dashboard(list(build([job_row(1, application_status="New")]).values()))
    assert jobs.values[1][col] == ""  # cleared, not left as the old date


def test_a_changed_layout_is_reformatted() -> None:
    storage, book = sheets()
    table = DashboardTable("Dash_Test", ["d"], [[date(2026, 10, 1)]], {"d": "date"})
    storage.write_dashboard([table])
    ws = tab(book, "Dash_Test")
    first = len(ws.spreadsheet.other_requests)
    storage.write_dashboard(
        [DashboardTable("Dash_Test", ["when"], [[date(2026, 10, 1)]], {"when": "date"})]
    )
    assert len(ws.spreadsheet.other_requests) > first and ws.values[0] == ["when"]


def test_text_from_scraped_listings_cannot_become_formulas() -> None:
    storage, book = sheets()
    storage.write_dashboard(
        list(build([job_row(title='=IMPORTDATA("http://evil")', company="@cmd")]).values())
    )
    jobs = tab(book, "Dash_Jobs")
    row = dict(zip(jobs.values[0], jobs.values[1], strict=True))
    assert row["title"].startswith("'=") and row["company"].startswith("'@")


def test_writing_dashboard_tabs_needs_the_spreadsheet_handle() -> None:
    from jobscraper.utils.errors import StorageError

    try:
        GoogleSheetsStorage(FakeWorksheet()).write_dashboard([DashboardTable("Dash_X", ["a"], [])])
    except StorageError as exc:
        assert "spreadsheet handle" in str(exc)
    else:
        raise AssertionError("expected StorageError")


# ---- end to end -------------------------------------------------------------------------------------------


def test_refresh_dashboard_from_a_real_store(tmp_path: Any) -> None:
    storage = SQLiteStorage()
    storage.append_jobs(
        [
            make_job(
                job_id=f"j{i}",
                source_job_id=str(i),
                job_url=f"https://x.com/{i}",
                match_tier=MatchTier.STRONG,
                match_score=80 + i,
            )
            for i in range(3)
        ]
    )
    tables = refresh_dashboard(storage, NOW)
    stored = storage.load_dashboard("Dash_Jobs")
    assert stored is not None and len(stored["rows"]) == 3 == len(tables[0].rows)
    assert stored["headers"][8] == "first_seen" and isinstance(stored["rows"][0][8], int)
    assert storage.load_dashboard("Dash_Meta")["rows"][0][1] == 3  # type: ignore[index]


def test_dashboard_command_exports_csv_and_refreshes(tmp_path: Any, capsys: Any) -> None:
    db = tmp_path / "jobs.db"
    storage = SQLiteStorage(db)
    storage.append_jobs([make_job(match_tier=MatchTier.TOP, match_score=90)])
    args = ["--storage", "sqlite", "--db", str(db)]
    assert cli.main(["dashboard", "--export", str(tmp_path / "csv"), *args]) == 0
    assert (
        "Wrote 6 CSV files" in capsys.readouterr().out
        and (tmp_path / "csv" / "Dash_Jobs.csv").exists()
    )
    assert cli.main(["dashboard", *args]) == 0
    assert "Dash_Jobs (1 rows)" in capsys.readouterr().out
    assert SQLiteStorage(db).load_dashboard("Dash_Jobs") is not None
