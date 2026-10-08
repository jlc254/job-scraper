"""Column ownership and row conversion shared by every storage backend (doc 05).

Doc 05's system column list is extended with source_job_id, all_urls,
description_excerpt and is_repost, which the dedupe step needs to read back.
"""

from __future__ import annotations

import json
from datetime import datetime

from jobscraper.models import ExcludedRecord, Job, SourceRun, SourceStatus, StoredJob
from jobscraper.utils.cells import safe_cell
from jobscraper.utils.dedupe import format_salary
from jobscraper.utils.errors import StorageError

SYSTEM_COLUMNS = [
    "job_id", "fingerprint", "title", "company", "location", "work_type", "employment_type",
    "remote_eligibility", "salary", "skills_matched", "skills_missing", "match_score",
    "match_tier", "match_breakdown", "recommended_action", "source", "job_url", "date_posted",
    "application_deadline", "first_seen", "last_seen", "is_active", "notified_at", "checklist",
    "source_job_id", "all_urls", "description_excerpt", "is_repost", "follow_up_reminded_on",
]
USER_COLUMNS = ["application_status", "applied_on", "follow_up_date", "notes", "priority"]
JOBS_HEADERS = [*SYSTEM_COLUMNS, *USER_COLUMNS]
EXCLUDED_HEADERS = ["job_id", "excluded_at", "title", "company", "source", "job_url", "reason", "detail"]
HEALTH_HEADERS = ["key", "run_id", "started_utc", "source", "status", "found", "new", "dropped", "excluded", "error"]
TABLES = ("jobs", "excluded", "runs", "health")
RUNS_HEADERS = ["run_id", "started_utc", "duration_s", "found", "new", "duplicates", "report"]

# Columns the dedupe step may change on an existing row. Scoring columns join in Phase 4.
UPDATABLE_COLUMNS = frozenset(
    {
        "last_seen", "is_active", "all_urls", "job_url", "salary", "application_deadline",
        "notified_at", "follow_up_reminded_on",  # Phase 5: set by the notifier, never by hand
    }
)


def validate_update(fields: dict[str, str]) -> None:
    """Refuse any write to a user-owned or unknown column."""
    bad = sorted(set(fields) - UPDATABLE_COLUMNS)
    if bad:
        raise StorageError(f"refusing to update protected or unknown columns: {', '.join(bad)}")


def job_to_row(job: Job) -> dict[str, str]:
    """System columns for a new job, plus the initial application_status."""
    values: dict[str, object] = {
        "job_id": job.job_id,
        "fingerprint": job.fingerprint,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "work_type": job.work_type.value,
        "employment_type": job.employment_type.value,
        "remote_eligibility": job.remote_eligibility.value,
        "salary": format_salary(job),
        "source": job.source,
        "job_url": job.job_url,
        "date_posted": job.date_posted.isoformat() if job.date_posted else "",
        "application_deadline": job.application_deadline.isoformat() if job.application_deadline else "",
        "first_seen": job.first_seen.isoformat(),
        "last_seen": (job.last_seen or job.first_seen).isoformat(),
        "is_active": job.is_active,
        "source_job_id": job.source_job_id,
        "all_urls": "\n".join(job.all_urls),
        "description_excerpt": job.description_excerpt,
        "is_repost": job.is_repost,
        "skills_matched": job.skills_matched,
        "skills_missing": job.skills_missing,
        "match_score": job.match_score,
        "match_tier": job.match_tier.value if job.match_tier else "",
        "match_breakdown": json.dumps(job.match_breakdown, ensure_ascii=False, separators=(",", ":"))
        if job.match_breakdown else "",
        "recommended_action": job.recommended_action,
        "checklist": job.checklist,
    }
    row = {col: safe_cell(values.get(col)) for col in SYSTEM_COLUMNS}
    row["application_status"] = "New"  # new rows only; existing rows are never touched
    return row


def excluded_to_row(record: ExcludedRecord) -> dict[str, str]:
    values = {
        "job_id": record.job_id,
        "excluded_at": record.excluded_at.isoformat(),
        "title": record.title,
        "company": record.company,
        "source": record.source,
        "job_url": record.job_url,
        "reason": record.reason,
        "detail": record.detail,
    }
    return {k: safe_cell(v) for k, v in values.items()}


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value) if value else None
    except ValueError:
        return None


def row_to_stored(row: dict[str, str]) -> StoredJob | None:
    """Rebuild what dedupe needs from a stored row. Rows without a job_id are skipped."""
    job_id = row.get("job_id", "").strip()
    if not job_id:
        return None
    urls = [u for u in row.get("all_urls", "").splitlines() if u.strip()]
    return StoredJob(
        job_id=job_id,
        fingerprint=row.get("fingerprint", ""),
        title=row.get("title", ""),
        company=row.get("company", ""),
        job_url=row.get("job_url", ""),
        all_urls=urls,
        source=row.get("source", ""),
        source_job_id=row.get("source_job_id") or None,
        description_excerpt=row.get("description_excerpt", ""),
        first_seen=_parse_dt(row.get("first_seen", "")),
        last_seen=_parse_dt(row.get("last_seen", "")),
        salary=row.get("salary", ""),
        application_deadline=row.get("application_deadline", ""),
    )


def source_run_to_row(run: SourceRun) -> dict[str, str]:
    values = {
        "key": run.key, "run_id": run.run_id, "started_utc": run.started_utc.isoformat(),
        "source": run.source, "status": run.status.value, "found": run.found, "new": run.new,
        "dropped": run.dropped, "excluded": run.excluded, "error": run.error[:200],
    }
    return {k: safe_cell(v) for k, v in values.items()}


def _int(value: str) -> int:
    try:
        return int(float(value))
    except ValueError:
        return 0


def row_to_source_run(row: dict[str, str]) -> SourceRun | None:
    """Rebuild a history record. Rows that cannot be read are skipped, not guessed."""
    started = _parse_dt(row.get("started_utc", ""))
    try:
        status = SourceStatus(row.get("status", ""))
    except ValueError:
        return None
    if started is None or not row.get("source"):
        return None
    return SourceRun(
        run_id=row.get("run_id", ""), started_utc=started, source=row["source"], status=status,
        found=_int(row.get("found", "")), new=_int(row.get("new", "")),
        dropped=_int(row.get("dropped", "")), excluded=_int(row.get("excluded", "")),
        error=row.get("error", ""),
    )
