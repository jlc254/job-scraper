"""Normalize, filter, dedupe, score and persist. The runner fetches; this decides what is kept."""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from jobscraper.matching.filters import JobFilters
from jobscraper.matching.scorer import Scorer
from jobscraper.models import ExcludedRecord, Job, SourceResult
from jobscraper.parsers.normalize import normalize_job
from jobscraper.storage.base import Storage
from jobscraper.utils.dedupe import DedupeOutcome, Deduper
from jobscraper.utils.errors import StorageError

log = logging.getLogger(__name__)


def process_jobs(
    jobs: list[Job],
    storage: Storage | None,
    now: datetime,
    results: list[SourceResult],
    *,
    filters: JobFilters | None = None,
    scorer: Scorer | None = None,
) -> DedupeOutcome:
    """Run the Phase 3 and 4 steps in the order doc 04 gives:
    normalize, hard filters, dedupe against storage and this run, then score new jobs.

    A filtered job already stored, or already in the Excluded log, is skipped silently so
    reruns neither re-log it nor change an existing row.
    """
    stored = storage.load_index() if storage is not None else []
    stored_ids = {s.job_id for s in stored}
    excluded_ids = storage.load_excluded_ids() if storage is not None else set()
    deduper = Deduper(stored, now)
    excluded: list[ExcludedRecord] = []
    excluded_by_source: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    seen_excluded: set[str] = set()

    for job in jobs:
        candidate = normalize_job(job)
        verdict = filters.check(candidate) if filters is not None else None
        if verdict is None:
            deduper.add(candidate)
            continue
        if candidate.job_id in stored_ids or candidate.job_id in excluded_ids | seen_excluded:
            continue
        seen_excluded.add(candidate.job_id)
        reasons[verdict.reason] += 1
        excluded_by_source[candidate.source] += 1
        excluded.append(
            ExcludedRecord(
                job_id=candidate.job_id,
                title=candidate.title,
                company=candidate.company,
                source=candidate.source,
                job_url=candidate.job_url,
                reason=verdict.reason,
                detail=verdict.detail,
                excluded_at=now,
            )
        )

    outcome = deduper.finish()
    if scorer is not None:
        outcome.new_jobs = [scorer.score(j) for j in outcome.new_jobs]
    outcome.excluded = excluded
    outcome.excluded_by_reason = reasons
    for result in results:
        result.new = outcome.new_by_source.get(result.source, 0)
        result.duplicates += outcome.duplicates_by_source.get(result.source, 0)
        result.excluded = excluded_by_source.get(result.source, 0)
    return outcome


def dedupe_jobs(
    jobs: list[Job], storage: Storage | None, now: datetime, results: list[SourceResult]
) -> DedupeOutcome:
    """Phase 3 behaviour: no filters, no scoring."""
    return process_jobs(jobs, storage, now, results)


def persist(storage: Storage, outcome: DedupeOutcome, unsaved_dir: Path) -> None:
    """Write new rows, updates and excluded records. Retry once, then save locally (doc 07)."""
    last: StorageError | None = None
    for attempt in (1, 2):
        try:
            storage.append_jobs(outcome.new_jobs)
            storage.update_jobs(outcome.updates)
            storage.append_excluded(outcome.excluded)
            return
        except StorageError as exc:
            last = exc
            log.warning("storage write failed", extra={"ctx": {"attempt": attempt}})
            if attempt == 1:
                # Rows may be partly written. Drop what is already stored before retrying.
                try:
                    stored_ids = {s.job_id for s in storage.load_index()}
                    known_excluded = storage.load_excluded_ids()
                except StorageError:
                    stored_ids, known_excluded = set(), set()
                outcome.new_jobs = [j for j in outcome.new_jobs if j.job_id not in stored_ids]
                outcome.excluded = [e for e in outcome.excluded if e.job_id not in known_excluded]
    path = save_unsaved(outcome.new_jobs, unsaved_dir)
    raise StorageError(
        f"storage failed twice; {len(outcome.new_jobs)} new jobs saved to {path}"
    ) from last


def save_unsaved(jobs: list[Job], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"unsaved-{stamp}.json"
    path.write_text(
        json.dumps([j.model_dump(mode="json") for j in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


@dataclass
class RecoverResult:
    files: int = 0
    appended: int = 0
    already_stored: int = 0
    problems: list[str] = field(default_factory=list)


def recover_unsaved(paths: list[Path], storage: Storage, now: datetime) -> RecoverResult:
    """Re-add jobs from output/unsaved-*.json after a storage failure (doc 07).

    Jobs were already filtered and scored, so they only go through dedupe. A file is renamed
    to .recovered once its jobs are safely stored, so running this twice is harmless.
    """
    result = RecoverResult()
    deduper = Deduper(storage.load_index(), now)
    pending: list[tuple[Path, int]] = []
    for path in paths:
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
            jobs = [Job.model_validate(r) for r in records]
        except (OSError, ValueError, TypeError) as exc:
            result.problems.append(f"{path.name}: {type(exc).__name__}")
            continue
        for job in jobs:
            if not deduper.add(job):
                result.already_stored += 1
        pending.append((path, len(jobs)))
    outcome = deduper.finish()
    persist(storage, outcome, paths[0].parent if paths else Path("output"))
    for path, _count in pending:
        path.rename(path.with_suffix(".recovered"))
        result.files += 1
    result.appended = len(outcome.new_jobs)
    return result
