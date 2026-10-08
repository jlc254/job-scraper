"""Retention (FR-13, doc 03): remove what has aged out, never touch what the owner is working on.

Jobs: deleted after 60 days only while application_status is still New. Anything the owner moved
past New (Saved, Applied, Interview, Offer, Rejected, Ignored) is kept. Excluded audit rows and the
run and health logs are kept 30 days. Jobs not seen for 7 days are marked inactive.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from jobscraper.models import JobUpdate
from jobscraper.storage.base import Storage
from jobscraper.utils.dates import parse_timestamp

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetentionSettings:
    job_days: int = 60
    excluded_days: int = 30
    runs_days: int = 30
    health_days: int = 30
    inactive_after_days: int = 7
    # Safety net: a plan that would delete most of the sheet is almost certainly a bug.
    max_delete_fraction: float = 0.5
    guard_min_rows: int = 20


@dataclass
class RetentionPlan:
    delete_jobs: list[str] = field(default_factory=list)
    deactivate: list[JobUpdate] = field(default_factory=list)
    delete_excluded: list[str] = field(default_factory=list)
    delete_runs: list[str] = field(default_factory=list)
    delete_health: list[str] = field(default_factory=list)
    blocked: str | None = None

    def counts(self) -> dict[str, int]:
        return {
            "jobs deleted": len(self.delete_jobs),
            "jobs marked inactive": len(self.deactivate),
            "excluded rows deleted": len(self.delete_excluded),
            "run rows deleted": len(self.delete_runs),
            "health rows deleted": len(self.delete_health),
        }


def _older_than(value: str | None, now: datetime, days: int) -> bool:
    """Unreadable or empty timestamps are never treated as old, so nothing is deleted by guesswork."""
    stamp = parse_timestamp(value)
    return stamp is not None and now - stamp > timedelta(days=days)


def plan_retention(
    jobs: Sequence[dict[str, str]],
    excluded: Sequence[dict[str, str]],
    runs: Sequence[dict[str, str]],
    health: Sequence[dict[str, str]],
    now: datetime,
    settings: RetentionSettings | None = None,
) -> RetentionPlan:
    cfg = settings or RetentionSettings()
    plan = RetentionPlan()
    for row in jobs:
        job_id = row.get("job_id", "")
        if not job_id:
            continue
        status = (row.get("application_status") or "New").strip().lower()
        if status in ("new", "") and _older_than(row.get("first_seen"), now, cfg.job_days):
            plan.delete_jobs.append(job_id)
        elif (row.get("is_active") or "TRUE").strip().upper() != "FALSE" and _older_than(
            row.get("last_seen"), now, cfg.inactive_after_days
        ):
            plan.deactivate.append(JobUpdate(job_id=job_id, fields={"is_active": "FALSE"}))
    plan.delete_excluded = [
        r["job_id"]
        for r in excluded
        if r.get("job_id") and _older_than(r.get("excluded_at"), now, cfg.excluded_days)
    ]
    plan.delete_runs = [
        r["run_id"]
        for r in runs
        if r.get("run_id") and _older_than(r.get("started_utc"), now, cfg.runs_days)
    ]
    plan.delete_health = [
        r["key"]
        for r in health
        if r.get("key") and _older_than(r.get("started_utc"), now, cfg.health_days)
    ]
    if (
        len(plan.delete_jobs) > cfg.guard_min_rows
        and len(plan.delete_jobs) / max(len(jobs), 1) > cfg.max_delete_fraction
    ):
        plan.blocked = (
            f"refusing to delete {len(plan.delete_jobs)} of {len(jobs)} job rows in one go. "
            "Check first_seen values in the Sheet, then run `cleanup` by hand."
        )
    return plan


def run_retention(
    storage: Storage,
    now: datetime,
    settings: RetentionSettings | None = None,
    *,
    dry_run: bool = False,
) -> RetentionPlan:
    """Plan from the stored tables and, unless dry_run, apply. Raises StorageError on read failure."""
    plan = plan_retention(
        storage.load_table("jobs"),
        storage.load_table("excluded"),
        storage.load_table("runs"),
        storage.load_table("health"),
        now,
        settings,
    )
    if dry_run or plan.blocked:
        return plan
    if plan.deactivate:
        storage.update_jobs(plan.deactivate)
    if plan.delete_jobs:
        storage.delete_rows("jobs", "job_id", set(plan.delete_jobs))
    if plan.delete_excluded:
        storage.delete_rows("excluded", "job_id", set(plan.delete_excluded))
    if plan.delete_runs:
        storage.delete_rows("runs", "run_id", set(plan.delete_runs))
    if plan.delete_health:
        storage.delete_rows("health", "key", set(plan.delete_health))
    return plan
