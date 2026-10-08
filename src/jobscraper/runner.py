"""Runner: the only place that wires config, adapters and the HTTP client together."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from jobscraper.config import SourceConfig, gate_reason
from jobscraper.models import Job, SourceResult, SourceStatus
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import get_adapter_class
from jobscraper.utils.errors import BlockedError, FetchError, RateLimitedError
from jobscraper.utils.health import save_sample
from jobscraper.utils.http import HttpClient

log = logging.getLogger(__name__)

DEGRADED_DROP_RATIO = 0.30  # doc 07: more than 30% parse failures means degraded

ClientFactory = Callable[[Adapter], HttpClient]


@dataclass
class RunOutcome:
    jobs: list[Job] = field(default_factory=list)
    results: list[SourceResult] = field(default_factory=list)


def default_client_factory(adapter: Adapter) -> HttpClient:
    min_interval = 3.0 if adapter.kind == "html" else adapter.min_interval_s
    return HttpClient(adapter.allowed_hosts, min_interval_s=min_interval)


def run_sources(
    sources: dict[str, SourceConfig],
    *,
    selected: Iterable[str] | None = None,
    now: datetime,
    client_factory: ClientFactory = default_client_factory,
    environ: dict[str, str] | None = None,
    sample_dir: Path | None = None,
) -> RunOutcome:
    """Run every enabled, verified source. One source failing never stops the rest."""
    env = dict(os.environ) if environ is None else environ
    wanted = list(selected) if selected is not None else list(sources)
    outcome = RunOutcome()
    seen_ids: set[str] = set()
    for source_id in wanted:
        cfg = sources[source_id]
        result, jobs = _run_one(source_id, cfg, now, client_factory, env, seen_ids, sample_dir)
        outcome.results.append(result)
        outcome.jobs.extend(jobs)
    return outcome


def _run_one(
    source_id: str,
    cfg: SourceConfig,
    now: datetime,
    client_factory: ClientFactory,
    env: dict[str, str],
    seen_ids: set[str],
    sample_dir: Path | None = None,
) -> tuple[SourceResult, list[Job]]:
    started = time.monotonic()

    def finish(status: SourceStatus, **fields: object) -> SourceResult:
        return SourceResult(
            source=source_id,
            status=status,
            duration_s=round(time.monotonic() - started, 2),
            **fields,
        )

    reason = gate_reason(source_id, cfg)
    if reason is not None:
        return finish(SourceStatus.SKIPPED, error=reason), []
    adapter_cls = get_adapter_class(source_id)
    if adapter_cls is None:
        return finish(SourceStatus.FAILED, error="no adapter registered for this id"), []
    if adapter_cls.requires_key and not env.get(adapter_cls.requires_key):
        return finish(SourceStatus.SKIPPED, error=f"missing {adapter_cls.requires_key}"), []

    adapter = adapter_cls(cfg, now)
    client = client_factory(adapter)
    try:
        raws = adapter.fetch(client)
    except BlockedError as exc:
        log.error("source blocked", extra={"ctx": {"source": source_id}})
        return finish(SourceStatus.BLOCKED, error=str(exc)), []
    except RateLimitedError as exc:
        log.warning("source rate limited", extra={"ctx": {"source": source_id}})
        return finish(SourceStatus.RATE_LIMITED, error=str(exc)), []
    except FetchError as exc:
        log.error(
            "source failed", extra={"ctx": {"source": source_id, "error": type(exc).__name__}}
        )
        return finish(SourceStatus.FAILED, error=str(exc)), []
    finally:
        client.close()

    kept: list[Job] = []
    dropped = duplicates = 0
    unparsed: list[dict[str, object]] = []
    for index, raw in enumerate(raws):
        try:
            job = adapter.to_job(raw)
        except (ValidationError, ValueError, TypeError, KeyError, AttributeError):
            log.warning("record dropped", extra={"ctx": {"source": source_id, "index": index}})
            job = None
        if job is None:
            dropped += 1
            if len(unparsed) < 3:
                unparsed.append(raw.data)
        elif job.job_id in seen_ids:
            duplicates += 1
        else:
            seen_ids.add(job.job_id)
            kept.append(job)

    status = SourceStatus.OK
    if raws and dropped / len(raws) > DEGRADED_DROP_RATIO:
        status = SourceStatus.DEGRADED
        if sample_dir is not None and unparsed:
            path = save_sample(
                source_id, unparsed, "more than 30% of records failed to parse", sample_dir, now
            )
            log.warning(
                "saved debug sample", extra={"ctx": {"source": source_id, "file": path.name}}
            )
    elif adapter.partial_errors:
        status = SourceStatus.PARTIAL
    note = "; ".join(adapter.partial_errors) or None
    if status is SourceStatus.DEGRADED and note is None:
        note = f"{dropped} of {len(raws)} records failed to parse"
    result = finish(
        status,
        found=len(raws),
        kept=len(kept),
        dropped=dropped,
        duplicates=duplicates,
        error=note,
    )
    return result, kept
