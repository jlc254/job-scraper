"""Command line entry point: run, brief, calibrate."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import jobscraper.scrapers  # noqa: F401  (registers adapters)
from jobscraper.config import ConfigError, load_sources
from jobscraper.dashboard import build_from_storage, refresh_dashboard, write_csv_dir
from jobscraper.matching.brief import find_row, render_brief
from jobscraper.matching.calibrate import (
    agreement_report,
    read_labels,
    select_for_labeling,
    write_label_sheet,
)
from jobscraper.matching.filters import JobFilters
from jobscraper.matching.scorer import Scorer
from jobscraper.matching.settings import load_profile, load_scoring
from jobscraper.models import SourceResult
from jobscraper.notifications.digest import build_digest
from jobscraper.notifications.telegram import TelegramNotifier
from jobscraper.notify import deliver_digest
from jobscraper.output import format_report, write_csv
from jobscraper.pipeline import persist, process_jobs, recover_unsaved
from jobscraper.publish_cli import run_publish
from jobscraper.retention import run_retention
from jobscraper.runner import default_client_factory, run_sources
from jobscraper.runtime_settings import load_runtime_settings
from jobscraper.scrapers.registry import get_adapter_class, registered_ids
from jobscraper.source_check import (
    check_source,
    format_check,
    save_fixture,
    select_sources,
)
from jobscraper.storage.base import Storage
from jobscraper.storage.google_sheets import GoogleSheetsStorage
from jobscraper.storage.postgres import PostgresStorage
from jobscraper.storage.rows import job_to_row
from jobscraper.storage.sqlite import SQLiteStorage
from jobscraper.utils.dates import EAT
from jobscraper.utils.errors import NotificationError, StorageError
from jobscraper.utils.health import (
    alert_text,
    evaluate_health,
    format_health_table,
    needs_attention,
    no_source_succeeded,
    to_source_runs,
)
from jobscraper.utils.logging import setup_logging

# Tests replace these: no real DNS or sleeping, and a frozen clock so fixture dates never age out.
CLIENT_FACTORY = default_client_factory


def _now() -> datetime:
    return datetime.now(UTC)


def _add_settings_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--settings",
        default=Path("config/settings.yaml"),
        type=Path,
        help="optional thresholds file (see config/settings.example.yaml)",
    )


def _add_storage_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--storage", choices=["sheets", "sqlite", "postgres"], default="sheets")
    parser.add_argument("--db", type=Path, default=Path("output/jobs.db"), help="SQLite path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="main.py", description="Job scraper")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="fetch, filter, score and store jobs")
    run.add_argument("--dry-run", action="store_true", help="no storage reads or writes")
    run.add_argument(
        "--no-notify", action="store_true", help="print the digest instead of sending it"
    )
    run.add_argument("--sources", help="comma-separated source ids")
    run.add_argument("--config", default="config/sources.yaml", type=Path)
    run.add_argument("--profile", default="config/profile.yaml", type=Path)
    run.add_argument("--scoring", default="config/scoring.yaml", type=Path)
    run.add_argument("--csv", type=Path, help="CSV path (default output/jobs-<timestamp>.csv)")
    run.add_argument("--no-csv", action="store_true")
    run.add_argument("--no-cleanup", action="store_true", help="skip the daily retention pass")
    run.add_argument("--no-dashboard", action="store_true", help="skip refreshing the Dash_* tabs")
    _add_settings_arg(run)
    run.add_argument("--limit", type=int, default=20, help="rows to print")
    _add_storage_args(run)

    sub.add_parser("notify-test", help="send one test message to your Telegram chat")

    src = sub.add_parser("sources", help="source tools")
    src_sub = src.add_subparsers(dest="sources_command", required=True)
    chk = src_sub.add_parser(
        "check", help="live check: reachability, robots.txt, parsing. Saves nothing"
    )
    chk.add_argument("--config", default="config/sources.yaml", type=Path)
    chk.add_argument("--sources", help="comma-separated ids (may include pending sources)")
    chk.add_argument(
        "--save-fixtures", type=Path, help="save a sanitized real response per source, for tests"
    )

    clean = sub.add_parser("cleanup", help="apply retention (old jobs, logs and audit rows)")
    clean.add_argument("--dry-run", action="store_true", help="show what would be removed")
    _add_settings_arg(clean)
    _add_storage_args(clean)

    dash = sub.add_parser(
        "dashboard", help="rebuild the Dash_* tabs that feed the Looker Studio dashboard"
    )
    dash.add_argument(
        "--export", type=Path, help="write the tables as CSV files to this folder instead"
    )
    _add_settings_arg(dash)
    _add_storage_args(dash)

    hlth = sub.add_parser("health", help="per-source status and result counts from recent runs")
    _add_settings_arg(hlth)
    _add_storage_args(hlth)

    rec = sub.add_parser(
        "recover", help="re-add jobs from output/unsaved-*.json after a storage failure"
    )
    rec.add_argument("files", nargs="*", type=Path, help="default: output/unsaved-*.json")
    _add_storage_args(rec)

    brief = sub.add_parser("brief", help="Markdown brief for one stored job")
    brief.add_argument("job_id", help="job_id or a unique prefix")
    _add_storage_args(brief)

    cal = sub.add_parser("calibrate", help="label real jobs and compare with the tiers")
    cal.add_argument("--export", type=Path, help="write a CSV of jobs to label")
    cal.add_argument("--labels", type=Path, help="read your filled-in CSV and report agreement")
    cal.add_argument("--limit", type=int, default=30)
    _add_storage_args(cal)

    pub = sub.add_parser("publish", help="refresh Neon database from Google Sheet")
    pub.add_argument("--dry-run", action="store_true", help="preview changes without writing")
    pub.add_argument("--force", action="store_true", help="ignore row-count guard")
    _add_settings_arg(pub)

    return parser


def build_storage(args: argparse.Namespace, environ: dict[str, str]) -> Storage:
    if args.storage == "sqlite":
        args.db.parent.mkdir(parents=True, exist_ok=True)
        return SQLiteStorage(args.db)
    if args.storage == "postgres":
        return PostgresStorage()
    if args.storage == "sheets":
        return GoogleSheetsStorage.from_env(environ)
    raise StorageError(f"unknown storage backend: {args.storage}")


def run_row(
    started: datetime, elapsed: float, results: list[SourceResult], report: str
) -> dict[str, str]:
    return {
        "run_id": f"{started:%Y%m%d-%H%M%S}",
        "started_utc": started.isoformat(),
        "duration_s": f"{elapsed:.1f}",
        "found": str(sum(r.found for r in results)),
        "new": str(sum(r.new or 0 for r in results)),
        "duplicates": str(sum(r.duplicates for r in results)),
        "report": report,
    }


def _source_names() -> dict[str, str]:
    return {sid: cls.display_name for sid in registered_ids() if (cls := get_adapter_class(sid))}


def _warn(action: str, exc: Exception) -> None:
    print(f"warning: could not {action}: {exc}", file=sys.stderr)


def cmd_run(args: argparse.Namespace) -> int:
    try:
        sources = load_sources(args.config)
        profile = load_profile(args.profile)
        scoring = load_scoring(args.scoring)
        settings = load_runtime_settings(
            args.settings, default_max_potential=scoring.digest_max_potential
        )
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    selected = None
    if args.sources:
        selected = [s.strip() for s in args.sources.split(",") if s.strip()]
        unknown = [s for s in selected if s not in sources]
        if unknown:
            print(f"unknown source id(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
    # Fail fast, before any fetching: a missing secret should not cost a whole run.
    notifier: TelegramNotifier | None = None
    if not args.dry_run and not args.no_notify:
        try:
            notifier = TelegramNotifier.from_env(dict(os.environ))
        except NotificationError as exc:
            print(f"notification error: {exc}. Use --no-notify to skip sending.", file=sys.stderr)
            return 2
    storage: Storage | None = None
    if not args.dry_run:
        try:
            storage = build_storage(args, dict(os.environ))
        except StorageError as exc:
            print(f"storage error: {exc}", file=sys.stderr)
            return 2

    names = _source_names()
    history = []
    if storage is not None:
        try:
            history = storage.load_source_runs()
        except StorageError as exc:  # no history just means no trend alarms this run
            _warn("read the health history", exc)

    started = _now()
    run_id = f"{started:%Y%m%d-%H%M%S}"
    t0 = time.monotonic()
    outcome = run_sources(
        sources,
        selected=selected,
        now=started,
        client_factory=CLIENT_FACTORY,
        sample_dir=Path("output") / "samples",
    )
    findings = evaluate_health(outcome.results, history, names=names, settings=settings.health)

    today = started.date()
    try:
        deduped = process_jobs(
            outcome.jobs,
            storage,
            started,
            outcome.results,
            filters=JobFilters(scoring.filters, today),
            scorer=Scorer(profile, scoring, today),
        )
    except StorageError as exc:
        print(f"storage error while reading existing jobs: {exc}", file=sys.stderr)
        return 3
    exit_code = 0
    if storage is not None:
        try:
            persist(storage, deduped, Path("output"))
        except StorageError as exc:
            print(f"storage error: {exc}", file=sys.stderr)
            exit_code = 3
    elapsed = time.monotonic() - t0
    report = format_report(outcome.results, started, elapsed, deduped.excluded_by_reason)

    if storage is not None and exit_code == 0:
        tasks: list[tuple[str, Callable[[], None]]] = [
            (
                "write the Runs row",
                lambda: storage.append_run(run_row(started, elapsed, outcome.results, report)),
            ),
            (
                "write the Health rows",
                lambda: storage.append_source_runs(
                    to_source_runs(outcome.results, run_id, started)
                ),
            ),
        ]
        for action, write in tasks:
            try:
                write()
            except StorageError as exc:
                _warn(action, exc)
        if (
            not args.no_cleanup and started.astimezone(EAT).hour < 12
        ):  # once a day, on the morning run
            try:
                plan = run_retention(storage, started, settings.retention)
                summary = ", ".join(f"{n} {label}" for label, n in plan.counts().items() if n)
                print(
                    f"Cleanup: {summary or 'nothing to remove'}"
                    + (f" [{plan.blocked}]" if plan.blocked else "")
                )
            except StorageError as exc:
                _warn("run cleanup", exc)

    # Digest: built from stored rows, so jobs from an earlier failed send are included.
    rows: list[dict[str, str]] = []
    if storage is not None and exit_code == 0:
        try:
            rows = storage.load_rows()
        except StorageError as exc:
            _warn("read rows for the digest", exc)
    elif storage is None:
        rows = [job_to_row(j) for j in deduped.new_jobs]  # dry run: preview only
    attention = needs_attention(findings)
    digest = build_digest(
        rows,
        outcome.results,
        now=started,
        source_names=names,
        config=settings.digest,
        report_text=report if attention else None,
        notify_problems=attention,
    )
    health_alert = alert_text(findings)
    delivery_failed = False
    if notifier is not None and storage is not None and exit_code == 0:
        delivery = deliver_digest(digest, notifier, storage, _now(), started.astimezone(EAT).date())
        print(
            f"Digest: {delivery.sent}/{delivery.total} messages sent, "
            f"{delivery.jobs_marked} jobs and {delivery.follow_ups_marked} follow-ups marked"
        )
        if delivery.error:
            print(f"notification error: {delivery.error}", file=sys.stderr)
            delivery_failed = True
        if delivery.mark_error:
            print(
                f"WARNING: could not mark jobs as sent ({delivery.mark_error}); "
                "they may be sent again next run",
                file=sys.stderr,
            )
        if health_alert and not notifier.send_alert(health_alert):
            print("warning: the source health alert could not be sent", file=sys.stderr)
    elif notifier is not None and exit_code != 0:
        notifier.send_alert(
            "Run failed while saving jobs. New jobs were saved to output/ on the runner."
        )
    else:
        print("\n--- digest preview (not sent) ---")
        print("\n\n----\n\n".join(digest.messages) if digest.messages else "(nothing to send)")
        print("--- end preview ---")
        if health_alert:
            print(f"\n--- source health alert (not sent) ---\n{health_alert}")

    if storage is not None and exit_code == 0 and not args.no_dashboard:
        try:  # last, so statuses and notified_at written above are included
            tables = refresh_dashboard(storage, started, settings.digest.follow_up_days)
            print(f"Dashboard: {len(tables)} tabs refreshed")
        except StorageError as exc:
            _warn("refresh the dashboard", exc)

    print(report)
    print(f"\nMerged duplicates: {deduped.duplicates}, updated rows: {len(deduped.updates)}\n")
    ranked = sorted(deduped.new_jobs, key=lambda j: j.match_score or 0, reverse=True)
    for job in ranked[: args.limit]:
        tier = job.match_tier.value if job.match_tier else "?"
        flag = " [repost]" if job.is_repost else ""
        print(
            f"- [{tier} {job.match_score}] {job.title} | {job.company} | {job.location or '?'} | {job.source}{flag}"
        )
        if job.recommended_action:
            print(f"  Action: {job.recommended_action}")
        print(f"  {job.job_url}")
    if len(ranked) > args.limit:
        print(f"... and {len(ranked) - args.limit} more")
    if not args.no_csv:
        path = args.csv or Path("output") / f"jobs-{started:%Y%m%d-%H%M%S}.csv"
        write_csv(ranked, path)
        print(f"\nCSV written to {path}")

    # A run where no source gave any data is a failed run, even though every source failure
    # was contained: otherwise a network outage or a wrong config would look like a quiet day.
    if exit_code == 0 and no_source_succeeded(outcome.results):
        print("error: no source returned data this run", file=sys.stderr)
        return 5
    if exit_code == 0 and delivery_failed:
        return 4
    return exit_code


def cmd_sources_check(args: argparse.Namespace) -> int:
    try:
        sources = load_sources(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    requested = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
    unknown = [s for s in requested or [] if s not in sources]
    if unknown:
        print(f"unknown source id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    ids = select_sources(sources, requested)
    if not ids:
        print(
            "no enabled, verified sources to check. Name sources with --sources.", file=sys.stderr
        )
        return 2
    now = _now()
    results = [check_source(sid, sources[sid], now) for sid in ids]
    print(format_check(results))
    if args.save_fixtures:
        for result in results:
            saved = save_fixture(result, args.save_fixtures)
            if saved:
                print(
                    f"saved {saved}. Read it before committing: personal data is removed, nothing else."
                )
    return 0 if all(r.ok for r in results) else 1


def cmd_cleanup(args: argparse.Namespace) -> int:
    try:
        settings = load_runtime_settings(args.settings)
        storage = build_storage(args, dict(os.environ))
        plan = run_retention(storage, _now(), settings.retention, dry_run=args.dry_run)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 3
    label = "Would remove" if args.dry_run else "Removed"
    print(
        f"{label}: " + (", ".join(f"{n} {k}" for k, n in plan.counts().items() if n) or "nothing")
    )
    if plan.blocked:
        print(f"BLOCKED: {plan.blocked}", file=sys.stderr)
        return 1
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    try:
        settings = load_runtime_settings(args.settings)
        storage = build_storage(args, dict(os.environ))
        if args.export:
            tables = build_from_storage(storage, _now(), settings.digest.follow_up_days)
            paths = write_csv_dir(tables, args.export)
            print(f"Wrote {len(paths)} CSV files to {args.export}")
        else:
            tables = refresh_dashboard(storage, _now(), settings.digest.follow_up_days)
            print("Refreshed: " + ", ".join(f"{t.name} ({len(t.rows)} rows)" for t in tables))
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 3
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    try:
        settings = load_runtime_settings(args.settings)
        history = build_storage(args, dict(os.environ)).load_source_runs()
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 3
    print(format_health_table(history, _source_names(), settings.health))
    return 0


def cmd_recover(args: argparse.Namespace) -> int:
    paths = list(args.files) or sorted(Path("output").glob("unsaved-*.json"))
    if not paths:
        print("no unsaved-*.json files found")
        return 0
    try:
        result = recover_unsaved(paths, build_storage(args, dict(os.environ)), _now())
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 3
    print(
        f"Recovered {result.appended} new jobs from {result.files} file(s); "
        f"{result.already_stored} were already stored."
    )
    for problem in result.problems:
        print(f"could not read {problem}", file=sys.stderr)
    return 1 if result.problems else 0


def cmd_notify_test() -> int:
    try:
        notifier = TelegramNotifier.from_env(dict(os.environ))
    except NotificationError as exc:
        print(f"notification error: {exc}", file=sys.stderr)
        return 2
    sent = notifier.send_alert(
        "Test message from the job scraper. If you can read this, Telegram is set up."
    )
    print(
        "Test message sent."
        if sent
        else "Sending failed. Check the token and chat ID, and that you messaged the bot first."
    )
    return 0 if sent else 4


def cmd_brief(args: argparse.Namespace) -> int:
    try:
        rows = build_storage(args, dict(os.environ)).load_rows()
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 2
    row = find_row(rows, args.job_id)
    if row is None:
        print(f"no single job matches '{args.job_id}'", file=sys.stderr)
        return 1
    print(render_brief(row))
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    if not args.export and not args.labels:
        print(
            "give --export PATH to create a label sheet, or --labels PATH to compare",
            file=sys.stderr,
        )
        return 2
    try:
        rows = build_storage(args, dict(os.environ)).load_rows()
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 2
    if args.export:
        picked = select_for_labeling(rows, args.limit)
        write_label_sheet(picked, args.export)
        print(
            f"Wrote {len(picked)} jobs to {args.export}. Fill the label column (apply/maybe/skip)."
        )
    if args.labels:
        print(agreement_report(rows, read_labels(args.labels)))
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    """Google Sheet to Neon, one way. Exit codes: 0 ok, 2 config, 3 Sheet read, 6 Neon or guard."""
    try:
        settings = load_runtime_settings(args.settings)
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    from jobscraper.storage.google_sheets import GoogleSheetsStorage

    try:
        storage = GoogleSheetsStorage.from_env(dict(os.environ))
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 2

    return run_publish(
        load_rows=lambda: storage.load_table("jobs"),
        dsn=os.environ.get("NEON_DATABASE_URL_PUBLISHER"),
        settings=settings.publish,
        dry_run=args.dry_run,
        force=args.force,
    )


def main(argv: list[str] | None = None) -> int:
    setup_logging(level=logging.INFO)
    args = build_parser().parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "sources":
        return cmd_sources_check(args)
    if args.command == "cleanup":
        return cmd_cleanup(args)
    if args.command == "dashboard":
        return cmd_dashboard(args)
    if args.command == "health":
        return cmd_health(args)
    if args.command == "recover":
        return cmd_recover(args)
    if args.command == "notify-test":
        return cmd_notify_test()
    if args.command == "brief":
        return cmd_brief(args)
    if args.command == "calibrate":
        return cmd_calibrate(args)
    if args.command == "publish":
        return cmd_publish(args)
    return 2
