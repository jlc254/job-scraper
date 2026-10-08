"""Build the Dash_* tables that feed the Looker Studio dashboard.

Pure functions over stored rows. Private notes and descriptions never leave the Jobs tab: only
the columns listed below are copied. All dates are shown in Africa/Nairobi (EAT).
"""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jobscraper.models.dashboard import DashboardTable, csv_value
from jobscraper.utils.dates import EAT, parse_timestamp, parse_user_date

if TYPE_CHECKING:
    from jobscraper.storage.base import Storage

SCHEMA_VERSION = 1
TIER_RANK = {"top": 1, "strong": 2, "potential": 3, "weak": 4, "unscored": 5}
FACTORS = ("title", "skills", "location", "experience", "salary", "freshness", "industry")

JOB_HEADERS = [
    "job_id", "title", "company", "source", "tier", "tier_rank", "score", "status", "first_seen",
    "posted", "deadline", "applied_on", "follow_up_due", "work_type", "remote_eligibility",
    "location", "salary", "is_active", "notified", "is_repost", "matched_count", "missing_count",
    "scoring_version", *[f"{f}_pts" for f in FACTORS], "url",
]
SKILL_HEADERS = ["job_id", "first_seen", "tier", "status", "skill", "importance", "match"]
SOURCE_HEADERS = [
    "run_time", "run_date", "source", "status", "healthy", "found", "new", "dropped", "excluded", "error",
]
RUN_HEADERS = ["run_id", "run_time", "run_date", "duration_s", "found", "new", "duplicates"]
EXCLUDED_HEADERS = ["job_id", "excluded_on", "source", "reason", "title", "company", "detail"]
META_HEADERS = ["refreshed_at", "jobs", "excluded", "runs", "schema_version"]


def _local_dt(text: str | None) -> datetime | None:
    stamp = parse_timestamp(text)
    return stamp.astimezone(EAT).replace(tzinfo=None) if stamp else None


def _local_date(text: str | None) -> date | None:
    stamp = _local_dt(text)
    return stamp.date() if stamp else None


def _float(text: Any) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _int(text: Any) -> int:
    value = _float(text)
    return int(value) if value is not None else 0


def _breakdown(row: dict[str, str]) -> dict[str, Any]:
    try:
        data = json.loads(row.get("match_breakdown") or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _names(text: str | None) -> list[str]:
    return [part.strip() for part in (text or "").split(";") if part.strip()]


def _tier(row: dict[str, str]) -> str:
    return (row.get("match_tier") or "").strip().lower() or "unscored"


def _status(row: dict[str, str]) -> str:
    return (row.get("application_status") or "").strip() or "New"


def _points(breakdown: dict[str, Any], factor: str) -> float | None:
    factors = breakdown.get("factors")
    entry = factors.get(factor) if isinstance(factors, dict) else None
    value = entry.get("points") if isinstance(entry, dict) else None
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _job_row(row: dict[str, str], follow_up_days: int) -> list[Any]:
    breakdown = _breakdown(row)
    tier, status = _tier(row), _status(row)
    applied = parse_user_date(row.get("applied_on"))
    follow = parse_user_date(row.get("follow_up_date"))
    due = None
    if status.lower() == "applied":  # same rule as the Telegram reminders
        due = follow or (applied + timedelta(days=follow_up_days) if applied else None)
    version = breakdown.get("version")
    return [
        row.get("job_id", ""), row.get("title", ""), row.get("company", ""), row.get("source", ""),
        tier, TIER_RANK.get(tier, 5), _float(row.get("match_score")), status,
        _local_date(row.get("first_seen")), parse_user_date(row.get("date_posted")),
        parse_user_date(row.get("application_deadline")), applied, due,
        row.get("work_type", ""), row.get("remote_eligibility", ""), row.get("location", ""),
        row.get("salary", ""), (row.get("is_active") or "TRUE").strip().upper() != "FALSE",
        bool((row.get("notified_at") or "").strip()), (row.get("is_repost") or "").strip().upper() == "TRUE",
        len(_names(row.get("skills_matched"))), len(_names(row.get("skills_missing"))),
        version if isinstance(version, int) and not isinstance(version, bool) else None,
        *[_points(breakdown, f) for f in FACTORS], row.get("job_url", ""),
    ]


def _skill_rows(row: dict[str, str]) -> list[list[Any]]:
    skills = _breakdown(row).get("skills")
    if not isinstance(skills, dict):
        return []
    matched, partial = set(skills.get("matched") or []), set(skills.get("partial") or [])
    out: list[list[Any]] = []
    for importance in ("required", "preferred"):
        for skill in skills.get(importance) or []:
            if not isinstance(skill, str):
                continue
            outcome = "matched" if skill in matched else "partial" if skill in partial else "missing"
            out.append([row.get("job_id", ""), _local_date(row.get("first_seen")), _tier(row),
                        _status(row), skill, importance, outcome])
    return out


def build_dashboard(
    *,
    jobs: Sequence[dict[str, str]],
    excluded: Sequence[dict[str, str]],
    runs: Sequence[dict[str, str]],
    health: Sequence[dict[str, str]],
    now: datetime,
    follow_up_days: int = 7,
) -> list[DashboardTable]:
    """Six tables, one per Looker Studio data source."""
    job_rows = [r for r in jobs if r.get("job_id")]
    job_table = sorted(
        (_job_row(r, follow_up_days) for r in job_rows),
        key=lambda x: (x[8] or date.min, x[6] or 0), reverse=True,
    )
    skill_table = [s for r in job_rows for s in _skill_rows(r)]

    source_table: list[list[Any]] = []
    for r in health:
        when = _local_dt(r.get("started_utc"))
        if when is None or not r.get("source"):
            continue
        status = (r.get("status") or "").strip()
        source_table.append([when, when.date(), r["source"], status, status == "ok", _int(r.get("found")),
                             _int(r.get("new")), _int(r.get("dropped")), _int(r.get("excluded")),
                             (r.get("error") or "")[:200]])
    source_table.sort(key=lambda x: x[0], reverse=True)

    run_table: list[list[Any]] = []
    for r in runs:
        when = _local_dt(r.get("started_utc"))
        if when is None:
            continue
        run_table.append([r.get("run_id", ""), when, when.date(), _float(r.get("duration_s")),
                          _int(r.get("found")), _int(r.get("new")), _int(r.get("duplicates"))])
    run_table.sort(key=lambda x: x[1], reverse=True)

    excluded_table = sorted(
        ([r.get("job_id", ""), _local_date(r.get("excluded_at")), r.get("source", ""), r.get("reason", ""),
          r.get("title", ""), r.get("company", ""), r.get("detail", "")] for r in excluded if r.get("job_id")),
        key=lambda x: x[1] or date.min, reverse=True,
    )
    refreshed = now.astimezone(EAT).replace(tzinfo=None)
    return [
        DashboardTable("Dash_Jobs", JOB_HEADERS, job_table,
                       {h: "date" for h in ("first_seen", "posted", "deadline", "applied_on", "follow_up_due")}),
        DashboardTable("Dash_Skills", SKILL_HEADERS, skill_table, {"first_seen": "date"}),
        DashboardTable("Dash_Sources", SOURCE_HEADERS, source_table, {"run_time": "datetime", "run_date": "date"}),
        DashboardTable("Dash_Runs", RUN_HEADERS, run_table, {"run_time": "datetime", "run_date": "date"}),
        DashboardTable("Dash_Excluded", EXCLUDED_HEADERS, excluded_table, {"excluded_on": "date"}),
        DashboardTable("Dash_Meta", META_HEADERS,
                       [[refreshed, len(job_table), len(excluded_table), len(run_table), SCHEMA_VERSION]],
                       {"refreshed_at": "datetime"}),
    ]


def build_from_storage(storage: Storage, now: datetime, follow_up_days: int = 7) -> list[DashboardTable]:
    return build_dashboard(
        jobs=storage.load_table("jobs"), excluded=storage.load_table("excluded"),
        runs=storage.load_table("runs"), health=storage.load_table("health"),
        now=now, follow_up_days=follow_up_days,
    )


def refresh_dashboard(storage: Storage, now: datetime, follow_up_days: int = 7) -> list[DashboardTable]:
    """Rebuild every Dash_* table from the stored data and write them. Raises StorageError."""
    tables = build_from_storage(storage, now, follow_up_days)
    storage.write_dashboard(tables)
    return tables


def write_csv_dir(tables: Sequence[DashboardTable], directory: Path) -> list[Path]:
    """One CSV per table, for a quick look or for Looker Studio's file-upload connector."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for table in tables:
        path = directory / f"{table.name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(table.headers)
            for row in table.rows:
                writer.writerow([csv_value(cell) for cell in row])
        paths.append(path)
    return paths
