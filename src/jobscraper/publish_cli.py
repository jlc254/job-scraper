"""`python main.py publish` logic. The CLI/runner is the only place that wires pieces together.

One publish covers every enabled profile (doc 15). Each profile has its own Sheet loader, its own
row-count guard and its own transaction, so a problem in one profile never blocks or damages another.

Exit codes: 0 ok, 2 configuration problem, 3 could not read a Sheet, 6 Neon write failed or the
row-count guard refused. With several profiles the worst code wins, and every profile is still tried.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from jobscraper.publish import (
    COLUMNS,
    GuardError,
    PublishPlan,
    PublishSettings,
    build_rows,
    check_guard,
)

EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_SHEET = 3
EXIT_NEON = 6

RowLoader = Callable[[], Iterable[Mapping[str, Any]]]


def run_publish(
    *,
    loaders: Mapping[str, RowLoader],
    dsn: str | None,
    settings: PublishSettings,
    dry_run: bool = False,
    force: bool = False,
    prune_keep: Sequence[str] | None = None,
    now: datetime | None = None,
    out: Callable[[str], None] = print,
) -> int:
    """Read each profile's Sheet, apply the rules, and refresh that profile's slice of Neon.

    `loaders` maps profile id to a function returning that profile's Jobs tab as header-keyed
    dicts of strings, for example `{"support": lambda: storage.load_table("jobs")}`. Its keys are
    the profiles to publish. `prune_keep` is the full list of enabled profiles; when given, rows of
    any other profile still in Neon are pruned after the loop, but only when every profile
    published cleanly, so a failed Sheet read never deletes data. Leave it None for a partial
    publish (`--only`), which must never prune.
    """
    now = now or datetime.now(UTC)

    if not loaders:
        out("No enabled profiles to publish.")
        return EXIT_CONFIG
    if not dry_run and not dsn:
        out("NEON_DATABASE_URL_PUBLISHER is not set.")
        return EXIT_CONFIG

    plans: dict[str, PublishPlan] = {}
    worst = EXIT_OK
    for profile, load_rows in loaders.items():
        try:
            sheet_rows = list(load_rows())
        except Exception as exc:  # boundary: any Sheet failure maps to one exit code
            out(f"[{profile}] Could not read the Sheet: {type(exc).__name__}")
            worst = max(worst, EXIT_SHEET)
            continue
        plan = build_rows(sheet_rows, settings, now, profile)
        out(f"[{profile}] {plan.summary()}")
        plans[profile] = plan

    if dry_run:
        for profile, plan in plans.items():
            for row in plan.rows[:3]:
                out(
                    f"  [{profile}] {row['job_id']}  {row['match_tier']:<9} {row['match_score']}  "
                    f"{row['title'][:50]} | {row['company'][:30]}"
                )
        out("Dry run: nothing was written.")
        return worst

    if dsn is None:
        return EXIT_CONFIG

    # Imported here so dry runs and unit tests do not need psycopg installed.
    from jobscraper.storage.neon import NeonError, NeonPublisher

    try:
        with NeonPublisher(dsn) as publisher:
            for profile, plan in plans.items():
                try:
                    check_guard(
                        len(plan.rows), publisher.count_jobs(profile), settings, force=force
                    )
                    deleted = publisher.replace_jobs(
                        COLUMNS,
                        plan.rows,
                        profile=profile,
                        run_start=now,
                        sheet_rows=plan.sheet_rows,
                    )
                except GuardError as exc:
                    out(f"[{profile}] Guard: {exc}")
                    worst = max(worst, EXIT_NEON)
                    continue
                except NeonError as exc:
                    out(f"[{profile}] Neon: {exc}")
                    worst = max(worst, EXIT_NEON)
                    continue
                out(
                    f"[{profile}] Neon updated: {len(plan.rows)} jobs live, "
                    f"{deleted} stale rows removed."
                )
            if worst == EXIT_OK and prune_keep:
                removed = publisher.prune_profiles(list(prune_keep))
                if removed:
                    out(f"Removed {removed} rows of profiles that are no longer enabled.")
    except NeonError as exc:  # connection failure or prune failure
        out(f"Neon: {exc}")
        return EXIT_NEON

    return worst
