"""`python main.py publish` logic. The CLI/runner is the only place that wires pieces together.

Exit codes: 0 ok, 2 configuration problem, 3 could not read the Sheet, 6 Neon write failed
or the row-count guard refused.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from jobscraper.publish import (
    COLUMNS,
    GuardError,
    PublishSettings,
    build_rows,
    check_guard,
)

EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_SHEET = 3
EXIT_NEON = 6


def run_publish(
    *,
    load_rows: Callable[[], Iterable[Mapping[str, Any]]],
    dsn: str | None,
    settings: PublishSettings,
    dry_run: bool = False,
    force: bool = False,
    now: datetime | None = None,
    out: Callable[[str], None] = print,
) -> int:
    """Read the Sheet, apply the rules, and refresh Neon (unless dry-run).

    `load_rows` returns the Jobs tab as a list of header-keyed dicts of strings
    (for example `lambda: storage.load_table("jobs")`).
    """
    now = now or datetime.now(UTC)

    if not dry_run and not dsn:
        out("NEON_DATABASE_URL_PUBLISHER is not set.")
        return EXIT_CONFIG

    try:
        sheet_rows = list(load_rows())
    except Exception as exc:  # boundary: any Sheet failure maps to one exit code
        out(f"Could not read the Sheet: {type(exc).__name__}")
        return EXIT_SHEET

    plan = build_rows(sheet_rows, settings, now)
    out(plan.summary())

    if dry_run:
        for row in plan.rows[:3]:
            out(
                f"  {row['job_id']}  {row['match_tier']:<9} {row['match_score']}  "
                f"{row['title'][:50]} | {row['company'][:30]}"
            )
        out("Dry run: nothing was written.")
        return EXIT_OK

    # Imported here so dry runs and unit tests do not need psycopg installed.
    from jobscraper.storage.neon import NeonError, NeonPublisher

    try:
        with NeonPublisher(dsn) as publisher:
            check_guard(len(plan.rows), publisher.count_jobs(), settings, force=force)
            deleted = publisher.replace_jobs(
                COLUMNS, plan.rows, run_start=now, sheet_rows=plan.sheet_rows
            )
    except GuardError as exc:
        out(f"Guard: {exc}")
        return EXIT_NEON
    except NeonError as exc:
        out(f"Neon: {exc}")
        return EXIT_NEON

    out(f"Neon updated: {len(plan.rows)} jobs live, {deleted} stale rows removed.")
    return EXIT_OK
