"""CSV export and the plain-text run report (doc 07 format)."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from jobscraper.models import Job, SourceResult, SourceStatus
from jobscraper.utils.cells import safe_cell

CSV_COLUMNS = [
    "job_id", "title", "company", "location", "work_type", "employment_type",
    "remote_eligibility", "posting_country_restrictions", "salary_min", "salary_max",
    "salary_currency", "experience_level", "date_posted", "application_deadline",
    "source", "job_url", "description_excerpt", "first_seen",
]


def write_csv(jobs: list[Job], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for job in jobs:
            row = job.model_dump(mode="json")
            writer.writerow([safe_cell(row.get(col)) for col in CSV_COLUMNS])


def format_report(
    results: list[SourceResult],
    started: datetime,
    duration_s: float,
    excluded_by_reason: Counter[str] | None = None,
) -> str:
    minutes, seconds = divmod(int(duration_s), 60)
    lines = [f"RUN {started:%Y-%m-%d %H:%M} UTC  ({minutes}m {seconds:02d}s)"]
    for r in results:
        if r.status is SourceStatus.SKIPPED:
            lines.append(f"{r.source}: skipped ({r.error})")
            continue
        detail = f"{r.found} found, {r.new} new" if r.new is not None else f"{r.found} found, {r.kept} kept"
        extras = []
        if r.dropped:
            extras.append(f"{r.dropped} dropped")
        if r.duplicates:
            extras.append(f"{r.duplicates} duplicate")
        if extras:
            detail += " (" + ", ".join(extras) + ")"
        line = f"{r.source}: {r.status.value}, {detail}"
        if r.error:
            line += f" [{r.error}]"
        lines.append(line)
    if excluded_by_reason:
        total = sum(excluded_by_reason.values())
        detail = ", ".join(f"{n} {reason.replace('_', '-')}" for reason, n in excluded_by_reason.most_common())
        lines.append(f"Excluded: {total} ({detail})")
    return "\n".join(lines)
