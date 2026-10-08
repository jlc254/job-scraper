from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jobscraper.models import Job, WorkType
from jobscraper.parsers.normalize import normalize_job

T0 = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)


def make_job(**overrides: Any) -> Job:
    """A normalized Job with sensible defaults. Override any field."""
    base: dict[str, Any] = {
        "job_id": "job-a",
        "title": "Customer Support Agent",
        "company": "Acme Cloud Inc.",
        "job_url": "https://himalayas.app/jobs/acme-1",
        "source": "himalayas",
        "source_url": "https://himalayas.app/jobs",
        "source_job_id": "h-1",
        "location": "Worldwide",
        "work_type": WorkType.REMOTE,
        "description_excerpt": "Help customers with Zendesk and ticketing every day.",
        "first_seen": T0,
    }
    base.update(overrides)
    return normalize_job(Job(**base))


def later(days: float) -> datetime:
    return T0 + timedelta(days=days)