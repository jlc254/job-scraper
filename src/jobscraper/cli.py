"""Command line entry point: run, brief, calibrate, publish and the other tools.

Multi-profile (doc 15): `run` fetches once, then filters, scores, stores and notifies once per
enabled profile, each with its own Sheet and Telegram chat. A failure in one profile never stops
another. Commands that work on one profile take `--for <id>` (default: the first enabled one).
"""

from __future__ import annotations

import argparse
import copy
import logging
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
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
from jobscraper.matching.settings import ProfileConfig, ScoringConfig, load_profile, load_scoring
from jobscraper.models import Job, SourceResult
from jobscraper.notifications.digest import build_digest
from jobscraper.notifications.telegram import TelegramNotifier
from jobscraper.notify import deliver_digest
from jobscraper.output import format_report, write_csv
from jobscraper.pipeline import persist, process_jobs, recover_unsaved
from jobscraper.profiles import (
    ProfileEntry,
    enabled_profiles,
    load_profiles,
    pick_profile,
    resolve_chat_ids,
    resolve_sheet_ids,
    validate_profile_sources,
)
from jobscraper.publish_cli import run_publish
from jobscraper.retention import run_retention
from jobscraper.runner import default_client_factory, run_sources
from jobscraper.runtime_settings import RuntimeSettings, load_runtime_settings
from jobscraper.scrapers.registry import get_adapter_class, registered_ids
from jobscraper.source_check import (
    check_source,
    format_check,
    save_fixture,
    select_sources,
)
from jobscraper.storage.base import Storage
from jobscraper.storage.google_sheets import GoogleSheetsStorage
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

EXIT_UNEXPECTED = 1  # a profile stage raised something we did not plan for (contained)
# Which exit code wins when several profiles disagree. Storage trouble outranks delivery trouble.
_EXIT_RANK = {0: 0, 4: 1, 3: 2, EXIT_UNEXPECTED: 3}


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


def _add_profile_args(parser: argparse.ArgumentParser, *, single: bool = True) -> None:
    """`--profiles` is the profiles.yaml path. `--for` picks one profile for single-profile tools."""
    parser.add_argument(
        "--profiles",
        default=Path("config/profiles.yaml"),
        type=Path,
        help="profiles file; if it does not exist the single legacy profile is used",
    )
    if single:
        parser.add_argument(
            "--for",
            dest="for_profile",
            help="profile id (default: the first enabled profile)",
        )


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
    # --profile and --scoring are the legacy single-profile files, used only when there is no
    # profiles.yaml. With profiles.yaml, each profile names its own files.
    run.add_argument("--profile", default="config/profile.yaml", type=Path)
    run.add_argument("--scoring", default="config/scoring.yaml", type=Path)
    _add_profile_args(run, single=False)
    run.add_argument("--only", help="comma-separated profile ids to run (default: all enabled)")
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
    _add_profile_args(clean)

    dash = sub.add_parser(
        "dashboard", help="rebuild the Dash_* tabs that feed the Looker Studio dashboard"
    )
    dash.add_argument(
        "--export", type=Path, help="write the tables as CSV files to this folder instead"
    )
    _add_settings_arg(dash)
    _add_storage_args(dash)
    _add_profile_args(dash)

    hlth = sub.add_parser("health", help="per-source status and result counts from recent runs")
    _add_settings_arg(hlth)
    _add_storage_args(hlth)
    _add_profile_args(hlth)

    rec = sub.add_parser(
        "recover", help="re-add jobs from output/unsaved-*.json after a storage failure"
    )
    rec.add_argument(
        "files", nargs="*", type=Path, help="default: this profile's output/unsaved-*.json"
    )
    _add_storage_args(rec)
    _add_profile_args(rec)

    brief = sub.add_parser("brief", help="Markdown brief for one stored job")
    brief.add_argument("job_id", help="job_id or a unique prefix")
    _add_storage_args(brief)
    _add_profile_args(brief)

    cal = sub.add_parser("calibrate", help="label real jobs and compare with the tiers")
    cal.add_argument("--export", type=Path, help="write a CSV of jobs to label")
    cal.add_argument("--labels", type=Path, help="read your filled-in CSV and report agreement")
    cal.add_argument("--limit", type=int, default=30)
    _add_storage_args(cal)
    _add_profile_args(cal)

    pub = sub.add_parser("publish", help="refresh Neon database from the Google Sheets")
    pub.add_argument("--dry-run", action="store_true", help="preview changes without writing")
    pub.add_argument("--force", action="store_true", help="ignore row-count guard")
    pub.add_argument("--only", help="comma-separated profile ids to publish (default: all enabled)")
    _add_settings_arg(pub)
    _add_profile_args(pub, single=False)

    return parser


# -- profiles and storage -----------------------------------------------------------------------


def _split(value: str | None) -> list[str] | None:
    items = [s.strip() for s in (value or "").split(",") if s.strip()]
    return items or None


def _load_entries(args: argparse.Namespace) -> list[ProfileEntry]:
    """Every profile in profiles.yaml, or the one legacy profile. The first is the primary."""
    return load_profiles(
        args.profiles,
        legacy_profile_path=getattr(args, "profile", Path("config/profile.yaml")),
        legacy_scoring_path=getattr(args, "scoring", Path("config/scoring.yaml")),
    )


def build_storage(
    args: argparse.Namespace,
    environ: dict[str, str],
    entry: ProfileEntry | None = None,
    *,
    primary: bool = True,
) -> Storage:
    """Storage for one profile. `primary` is the first profile in the file (the operator's)."""
    if args.storage == "sqlite":
        path: Path = args.db
        if entry is not None and not primary:
            path = path.with_name(f"{path.stem}-{entry.id}{path.suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        return SQLiteStorage(path)
    if args.storage == "postgres":
        if not primary:
            raise StorageError("the postgres backend supports one profile only")
        # Imported here so `import jobscraper.cli` (and SQLite-only tests)
        # does not require `psycopg` to be installed.
        from jobscraper.storage.postgres import PostgresStorage

        return PostgresStorage()
    if args.storage == "sheets":
        sheet_id = entry.sheet_id(environ) if entry is not None else None
        return GoogleSheetsStorage.from_env(environ, sheet_id=sheet_id)
    raise StorageError(f"unknown storage backend: {args.storage}")


def _storage_for(args: argparse.Namespace, environ: dict[str, str]) -> Storage:
    """Storage for the profile a single-profile command works on (`--for`)."""
    entries = _load_entries(args)
    entry = pick_profile(entries, getattr(args, "for_profile", None))
    return build_storage(args, environ, entry, primary=entry.id == entries[0].id)


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


# -- run ----------------------------------------------------------------------------------------


@dataclass
class ProfileContext:
    """Everything one profile needs for its stage of a run."""

    entry: ProfileEntry
    profile: ProfileConfig
    scoring: ScoringConfig
    settings: RuntimeSettings
    storage: Storage | None
    notifier: TelegramNotifier | None
    primary: bool  # the operator's profile: owns source-health alerts and the run report


def _run_profile(
    args: argparse.Namespace,
    ctx: ProfileContext,
    *,
    all_jobs: list[Job],
    shared_results: list[SourceResult],
    started: datetime,
    run_id: str,
    t0: float,
    names: dict[str, str],
    attention: bool,
    multi: bool,
) -> int:
    """Filter, score, store, notify and refresh the dashboard for ONE profile.

    Returns 0 ok, 3 storage problem, 4 digest delivery failed. Shared `SourceResult`s are copied
    first, because `process_jobs` writes new/excluded/duplicate counts onto them.
    """
    entry, storage, notifier, settings = ctx.entry, ctx.storage, ctx.notifier, ctx.settings
    tag = f"[{entry.id}] " if multi else ""
    results = copy.deepcopy(shared_results)
    jobs = [j for j in all_jobs if entry.sources is None or j.source in entry.sources]

    today = started.date()
    try:
        deduped = process_jobs(
            jobs,
            storage,
            started,
            results,
            filters=JobFilters(ctx.scoring.filters, today),
            scorer=Scorer(ctx.profile, ctx.scoring, today),
        )
    except StorageError as exc:
        print(f"{tag}storage error while reading existing jobs: {exc}", file=sys.stderr)
        return 3
    exit_code = 0
    if storage is not None:
        try:
            persist(storage, deduped, Path("output"), profile=entry.id)
        except StorageError as exc:
            print(f"{tag}storage error: {exc}", file=sys.stderr)
            exit_code = 3
    elapsed = time.monotonic() - t0
    report = format_report(results, started, elapsed, deduped.excluded_by_reason)

    if storage is not None and exit_code == 0:
        tasks: list[tuple[str, Callable[[], None]]] = [
            (
                "write the Runs row",
                lambda: storage.append_run(run_row(started, elapsed, results, report)),
            ),
        ]
        for action, write in tasks:
            try:
                write()
            except StorageError as exc:
                _warn(f"{tag}{action}", exc)
        if not args.no_cleanup and started.astimezone(EAT).hour < 12:  # once a day, morning run
            try:
                plan = run_retention(storage, started, settings.retention)
                summary = ", ".join(f"{n} {label}" for label, n in plan.counts().items() if n)
                print(
                    f"{tag}Cleanup: {summary or 'nothing to remove'}"
                    + (f" [{plan.blocked}]" if plan.blocked else "")
                )
            except StorageError as exc:
                _warn(f"{tag}run cleanup", exc)

    # Digest: built from stored rows, so jobs from an earlier failed send are included.
    rows: list[dict[str, str]] = []
    if storage is not None and exit_code == 0:
        try:
            rows = storage.load_rows()
        except StorageError as exc:
            _warn(f"{tag}read rows for the digest", exc)
    elif storage is None:
        rows = [job_to_row(j) for j in deduped.new_jobs]  # dry run: preview only
    # Source problems are the operator's concern. Other people still see the RUN line.
    show_problems = attention and ctx.primary
    digest = build_digest(
        rows,
        results,
        now=started,
        source_names=names,
        config=settings.digest,
        report_text=report if show_problems else None,
        notify_problems=show_problems,
        title=entry.digest_title,
    )
    delivery_failed = False
    if notifier is not None and storage is not None and exit_code == 0:
        delivery = deliver_digest(digest, notifier, storage, _now(), started.astimezone(EAT).date())
        print(
            f"{tag}Digest: {delivery.sent}/{delivery.total} messages sent, "
            f"{delivery.jobs_marked} jobs and {delivery.follow_ups_marked} follow-ups marked"
        )
        if delivery.error:
            print(f"{tag}notification error: {delivery.error}", file=sys.stderr)
            delivery_failed = True
        if delivery.mark_error:
            print(
                f"WARNING: {tag}could not mark jobs as sent ({delivery.mark_error}); "
                "they may be sent again next run",
                file=sys.stderr,
            )
    elif notifier is not None and exit_code != 0:
        notifier.send_alert(
            f"Run failed while saving jobs for '{entry.label}'. "
            "New jobs were saved to output/ on the runner."
        )
    else:
        print(f"\n--- {tag}digest preview (not sent) ---")
        print("\n\n----\n\n".join(digest.messages) if digest.messages else "(nothing to send)")
        print("--- end preview ---")

    if storage is not None and exit_code == 0 and not args.no_dashboard:
        try:  # last, so statuses and notified_at written above are included
            tables = refresh_dashboard(storage, started, settings.digest.follow_up_days)
            print(f"{tag}Dashboard: {len(tables)} tabs refreshed")
        except StorageError as exc:
            _warn(f"{tag}refresh the dashboard", exc)

    print(f"\n{tag}{report}")
    print(f"\n{tag}Merged duplicates: {deduped.duplicates}, updated rows: {len(deduped.updates)}\n")
    ranked = sorted(deduped.new_jobs, key=lambda j: j.match_score or 0, reverse=True)
    for job in ranked[: args.limit]:
        tier = job.match_tier.value if job.match_tier else "?"
        flag = " [repost]" if job.is_repost else ""
        print(
            f"- [{tier} {job.match_score}] {job.title} | {job.company} | "
            f"{job.location or '?'} | {job.source}{flag}"
        )
        if job.recommended_action:
            print(f"  Action: {job.recommended_action}")
        print(f"  {job.job_url}")
    if len(ranked) > args.limit:
        print(f"... and {len(ranked) - args.limit} more")
    if not args.no_csv:
        if args.csv and (ctx.primary or not multi):
            path = args.csv
        else:
            prefix = "" if ctx.primary else f"{entry.id}-"
            path = Path("output") / f"jobs-{prefix}{started:%Y%m%d-%H%M%S}.csv"
        write_csv(ranked, path)
        print(f"\n{tag}CSV written to {path}")

    if exit_code == 0 and delivery_failed:
        return 4
    return exit_code


def cmd_run(args: argparse.Namespace) -> int:
    environ = dict(os.environ)
    try:
        sources = load_sources(args.config)
        entries = _load_entries(args)
        validate_profile_sources(entries, sources)
        active = enabled_profiles(entries, _split(args.only))
        loaded: list[tuple[ProfileEntry, ProfileConfig, ScoringConfig, RuntimeSettings]] = []
        for entry in active:
            profile = load_profile(entry.profile_path)
            scoring = load_scoring(entry.scoring_path)
            settings = load_runtime_settings(
                args.settings, default_max_potential=scoring.digest_max_potential
            )
            loaded.append((entry, profile, scoring, settings))
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
    elif all(entry.sources is not None for entry, *_ in loaded):
        # No explicit --sources: fetch the union of the active profiles' allowlists, so a
        # configured source no profile references cannot cost requests (doc 15). A profile
        # without an allowlist sees every source, so the union collapses back to all.
        selected = sorted(
            {
                sid
                for entry, *_ in loaded
                for sid in entry.sources  # type: ignore[union-attr]  # guarded by the `all` above
            }
        )
    primary_id = entries[0].id
    operator_entry = entries[0]

    # Fail fast, before any fetching: a missing secret should not cost a whole run.
    notifiers: dict[str, TelegramNotifier] = {}
    if not args.dry_run and not args.no_notify:
        try:
            token = environ.get("TELEGRAM_BOT_TOKEN", "")
            health_entries = [operator_entry] + [e for e, *_ in loaded if e.id != operator_entry.id]
            chat_ids = resolve_chat_ids(health_entries, environ)
            for entry, *_ in loaded:
                notifiers[entry.id] = TelegramNotifier(token, chat_ids[entry.id])
            if operator_entry.id not in notifiers:
                notifiers[operator_entry.id] = TelegramNotifier(token, chat_ids[operator_entry.id])
        except (NotificationError, ConfigError) as exc:
            print(f"notification error: {exc}. Use --no-notify to skip sending.", file=sys.stderr)
            return 2
    storages: dict[str, Storage] = {}
    failed_storage: set[str] = set()
    if not args.dry_run:
        if args.storage == "sheets":
            try:
                resolve_sheet_ids(
                    [e for e, *_ in loaded]
                    + (
                        [operator_entry]
                        if operator_entry.id not in {e.id for e, *_ in loaded}
                        else []
                    ),
                    environ,
                )
            except ConfigError as exc:
                print(f"storage error: {exc}", file=sys.stderr)
                return 2
        for entry, *_ in loaded:
            try:
                storages[entry.id] = build_storage(
                    args, environ, entry, primary=entry.id == primary_id
                )
            except (StorageError, ConfigError) as exc:
                print(f"[{entry.id}] storage error: {exc}", file=sys.stderr)
                failed_storage.add(entry.id)
        # operator storage for health, even on a partial run
        if operator_entry.id not in storages and operator_entry.id not in failed_storage:
            try:
                storages[operator_entry.id] = build_storage(
                    args, environ, operator_entry, primary=True
                )
            except (StorageError, ConfigError) as exc:
                print(f"[{operator_entry.id}] storage error: {exc}", file=sys.stderr)
                failed_storage.add(operator_entry.id)

    # Source health is shared. The operator is the FIRST profile in profiles.yaml, even when
    # `--only` narrows the run: its Sheet holds the health history and it alone gets alerts.
    operator_loaded = next((t for t in loaded if t[0].id == operator_entry.id), None)
    if operator_loaded is None:
        try:
            _op_profile = load_profile(operator_entry.profile_path)
            _op_scoring = load_scoring(operator_entry.scoring_path)
            _op_settings = load_runtime_settings(
                args.settings, default_max_potential=_op_scoring.digest_max_potential
            )
            operator_loaded = (operator_entry, _op_profile, _op_scoring, _op_settings)
        except ConfigError as exc:
            print(f"config error: {exc}", file=sys.stderr)
            return 2
    health_settings = operator_loaded[3].health
    names = _source_names()
    history = []
    operator_storage = storages.get(operator_entry.id)
    if operator_storage is not None:
        try:
            history = operator_storage.load_source_runs()
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
    # Judge health once, on the shared results. It may downgrade a result to `degraded`, and
    # every profile then gets a copy that already carries that verdict.
    findings = evaluate_health(outcome.results, history, names=names, settings=health_settings)
    attention = needs_attention(findings)

    multi = len(loaded) > 1
    codes: list[int] = []
    for entry, profile, scoring, settings in loaded:
        if entry.id in failed_storage:
            codes.append(3)
            continue
        ctx = ProfileContext(
            entry=entry,
            profile=profile,
            scoring=scoring,
            settings=settings,
            storage=storages.get(entry.id),
            notifier=notifiers.get(entry.id),
            primary=entry.id == operator_entry.id,
        )
        try:
            codes.append(
                _run_profile(
                    args,
                    ctx,
                    all_jobs=outcome.jobs,
                    shared_results=outcome.results,
                    started=started,
                    run_id=run_id,
                    t0=t0,
                    names=names,
                    attention=attention,
                    multi=multi,
                )
            )
        except Exception as exc:  # noqa: BLE001 - boundary: one profile must not stop the others
            print(f"[{entry.id}] unexpected error: {type(exc).__name__}", file=sys.stderr)
            logging.getLogger(__name__).exception(
                "profile stage failed", extra={"ctx": {"profile": entry.id}}
            )
            codes.append(EXIT_UNEXPECTED)

    # Source-run history is the operator's (D30): write it once, to the operator's Sheet.
    if not args.dry_run and operator_storage is not None:
        try:
            operator_storage.append_source_runs(to_source_runs(outcome.results, run_id, started))
        except StorageError as exc:
            _warn("write the source-run history", exc)

    # Source-health alert: once, to the operator only.
    health_alert = alert_text(findings)
    if health_alert:
        operator_notifier = notifiers.get(operator_entry.id)
        if operator_notifier is not None:
            if not operator_notifier.send_alert(health_alert):
                print("warning: the source health alert could not be sent", file=sys.stderr)
        else:
            print(f"\n--- source health alert (not sent) ---\n{health_alert}")

    worst = max(codes, key=lambda c: _EXIT_RANK.get(c, 3), default=0)
    # A run where no source gave any data is a failed run, even though every source failure
    # was contained: otherwise a network outage or a wrong config would look like a quiet day.
    if worst in (0, 4) and no_source_succeeded(outcome.results):
        print("error: no source returned data this run", file=sys.stderr)
        return 5
    return worst


# -- other commands -----------------------------------------------------------------------------


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
        storage = _storage_for(args, dict(os.environ))
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
        storage = _storage_for(args, dict(os.environ))
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
        history = _storage_for(args, dict(os.environ)).load_source_runs()
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 3
    print(format_health_table(history, _source_names(), settings.health))
    return 0


def cmd_recover(args: argparse.Namespace) -> int:
    try:
        entries = _load_entries(args)
        entry = pick_profile(entries, args.for_profile)
        storage = build_storage(args, dict(os.environ), entry, primary=entry.id == entries[0].id)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except StorageError as exc:
        print(f"storage error: {exc}", file=sys.stderr)
        return 3
    paths = list(args.files)
    if not paths:
        paths = sorted(Path("output").glob(f"unsaved-{entry.id}-*.json"))
        if (
            entry.id == entries[0].id
        ):  # files written before profiles existed: unsaved-<date>-<time>
            paths += sorted(Path("output").glob("unsaved-[0-9]*.json"))
    if not paths:
        print(f"no unsaved files found for profile '{entry.id}'")
        return 0
    try:
        result = recover_unsaved(paths, storage, _now(), profile=entry.id)
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
        rows = _storage_for(args, dict(os.environ)).load_rows()
    except (StorageError, ConfigError) as exc:
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
        rows = _storage_for(args, dict(os.environ)).load_rows()
    except (StorageError, ConfigError) as exc:
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
    """Google Sheets to Neon, one way, per profile.

    Exit codes: 0 ok, 2 config, 3 Sheet read, 6 Neon or guard. The worst code across profiles wins.
    """
    environ = dict(os.environ)
    try:
        settings = load_runtime_settings(args.settings)
        active = enabled_profiles(_load_entries(args), _split(args.only))
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    def loader(profile_id: str) -> Callable[[], list[dict[str, str]]]:
        # Opened lazily, so one unreachable Sheet is reported for that profile only.
        def _load() -> list[dict[str, str]]:
            entry = next(e for e in active if e.id == profile_id)
            return GoogleSheetsStorage.from_env(
                environ, sheet_id=entry.sheet_id(environ)
            ).load_table("jobs")

        return _load

    # Pruning removes rows of profiles that are no longer enabled. Only a full publish (no
    # `--only`) knows the complete enabled list, so a partial one must never prune.
    prune_keep = None if args.only else [e.id for e in active]
    return run_publish(
        loaders={e.id: loader(e.id) for e in active},
        dsn=environ.get("NEON_DATABASE_URL_PUBLISHER"),
        settings=settings.publish,
        dry_run=args.dry_run,
        force=args.force,
        prune_keep=prune_keep,
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
