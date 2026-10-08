"""Source health: zero-result and drift alarms, three-strikes alerts, debug samples (doc 07).

Pure functions over run history. A broken source is never silent, and a source that stays
broken does not nag every run: the alert comes at the third bad run in a row, then as a
reminder every six runs after that, and once more when the source recovers.
"""

from __future__ import annotations

import json
import re
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jobscraper.models import SourceResult, SourceRun, SourceStatus
from jobscraper.utils.pii import scrub_pii

NON_OK = frozenset(
    {
        SourceStatus.DEGRADED,
        SourceStatus.PARTIAL,
        SourceStatus.RATE_LIMITED,
        SourceStatus.BLOCKED,
        SourceStatus.FAILED,
    }
)
# Counted as a normal response when judging result volume.
RESPONDED = frozenset({SourceStatus.OK, SourceStatus.PARTIAL})
# Finding kinds that deserve attention in the digest or as a separate alert.
ATTENTION = frozenset({"new_problem", "three_strikes", "reminder"})
ALERT_KINDS = frozenset({"three_strikes", "reminder", "recovered"})
UNREACHABLE = frozenset({SourceStatus.FAILED, SourceStatus.BLOCKED, SourceStatus.RATE_LIMITED})
ALERT_MAX_CHARS = 950  # Telegram alerts are capped at 1000 characters

ADVICE = {
    SourceStatus.BLOCKED: "Do not work around it. Disable the source, note it in the verification log, "
    "and use the site's email alerts.",
    SourceStatus.DEGRADED: "Run `python main.py sources check` and compare with the site in your browser. "
    "If the format changed, update the adapter and its fixture.",
    SourceStatus.RATE_LIMITED: "Lower the frequency in sources.yaml and check the source's terms.",
    SourceStatus.FAILED: "Check the Actions log, then run `python main.py sources check`.",
    SourceStatus.PARTIAL: "Part of the source is failing (see the run report). Check its board tokens or feeds.",
}


@dataclass(frozen=True)
class HealthSettings:
    window: int = 7  # how many recent runs form the baseline
    min_history: int = 3  # runs needed before volume alarms can fire
    zero_min_median: float = (
        3  # a sudden zero only matters if the source normally returns this many
    )
    drop_ratio: float = 0.2  # drift: fewer than 20% of the usual count...
    drop_min_median: float = 10  # ...when the usual count is at least this
    strikes: int = 3  # consecutive bad runs before the prominent alert
    reminder_every: int = 6  # further reminders while it stays broken


@dataclass(frozen=True)
class Finding:
    source: str
    kind: str  # zero_results, drift, new_problem, three_strikes, reminder, recovered
    message: str


def _by_source(history: Sequence[SourceRun]) -> dict[str, list[SourceRun]]:
    grouped: dict[str, list[SourceRun]] = {}
    for run in sorted(history, key=lambda r: r.started_utc, reverse=True):
        if run.status is not SourceStatus.SKIPPED:
            grouped.setdefault(run.source, []).append(run)
    return grouped


def non_ok_streak(statuses_newest_first: Sequence[SourceStatus]) -> int:
    count = 0
    for status in statuses_newest_first:
        if status not in NON_OK:
            break
        count += 1
    return count


def evaluate_health(
    results: Sequence[SourceResult],
    history: Sequence[SourceRun],
    *,
    names: Mapping[str, str],
    settings: HealthSettings | None = None,
) -> list[Finding]:
    """Judge this run against history. May downgrade an `ok` result to `degraded` in place."""
    cfg = settings or HealthSettings()
    past = _by_source(history)
    findings: list[Finding] = []
    for result in results:
        if result.status is SourceStatus.SKIPPED:
            continue
        name = names.get(result.source, result.source)
        previous = past.get(result.source, [])

        if result.status is SourceStatus.OK:
            counts = [r.found for r in previous[: cfg.window] if r.status in RESPONDED]
            if len(counts) >= cfg.min_history:
                usual = statistics.median(counts)
                if result.found == 0 and usual >= cfg.zero_min_median:
                    result.status = SourceStatus.DEGRADED
                    result.error = f"0 results (usually about {usual:g})"
                    findings.append(
                        Finding(
                            result.source,
                            "zero_results",
                            f"{name}: 0 results, usually about {usual:g}",
                        )
                    )
                elif usual >= cfg.drop_min_median and result.found < cfg.drop_ratio * usual:
                    result.status = SourceStatus.DEGRADED
                    result.error = f"{result.found} results (usually about {usual:g})"
                    findings.append(
                        Finding(
                            result.source,
                            "drift",
                            f"{name}: {result.found} results, usually about {usual:g}",
                        )
                    )

        history_statuses = [r.status for r in previous]
        if result.status in NON_OK:
            streak = 1 + non_ok_streak(history_statuses)
            detail = f"{result.status.value}" + (f": {result.error}" if result.error else "")
            if streak == 1:
                findings.append(Finding(result.source, "new_problem", f"{name} is {detail}"))
            elif streak >= cfg.strikes and (streak - cfg.strikes) % cfg.reminder_every == 0:
                kind = "three_strikes" if streak == cfg.strikes else "reminder"
                advice = ADVICE.get(result.status, "")
                findings.append(
                    Finding(
                        result.source,
                        kind,
                        f"{name} has not been healthy for {streak} runs in a row (now {detail}). {advice}".strip(),
                    )
                )
        else:
            earlier = non_ok_streak(history_statuses)
            if earlier >= cfg.strikes:
                findings.append(
                    Finding(
                        result.source,
                        "recovered",
                        f"{name} is healthy again after {earlier} bad runs.",
                    )
                )
    return findings


def alert_text(findings: Sequence[Finding]) -> str | None:
    """One combined alert for everything that crossed a threshold this run, or None."""
    lines = [f"- {f.message}" for f in findings if f.kind in ALERT_KINDS]
    if not lines:
        return None
    text = "SOURCE HEALTH\n" + "\n".join(lines)
    return text if len(text) <= ALERT_MAX_CHARS else text[: ALERT_MAX_CHARS - 1] + "\u2026"


def no_source_succeeded(results: Sequence[SourceResult]) -> bool:
    """True when nothing was attempted, or every attempted source was unreachable.

    Contained source failures keep a run green, but a run with no data at all is a failed run:
    otherwise a network outage or a wrong config would look like a quiet day.
    """
    attempted = [r for r in results if r.status is not SourceStatus.SKIPPED]
    return not attempted or all(r.status in UNREACHABLE for r in attempted)


def needs_attention(findings: Sequence[Finding]) -> bool:
    return any(f.kind in ATTENTION for f in findings)


def to_source_runs(
    results: Sequence[SourceResult], run_id: str, started: datetime
) -> list[SourceRun]:
    return [
        SourceRun(
            run_id=run_id,
            started_utc=started,
            source=r.source,
            status=r.status,
            found=r.found,
            new=r.new or 0,
            dropped=r.dropped,
            excluded=r.excluded,
            error=(r.error or "")[:200],
        )
        for r in results
        if r.status is not SourceStatus.SKIPPED
    ]


def format_health_table(
    history: Sequence[SourceRun], names: Mapping[str, str], settings: HealthSettings | None = None
) -> str:
    cfg = settings or HealthSettings()
    past = _by_source(history)
    if not past:
        return "No run history yet."
    lines = [
        f"{'source':<18} {'last':<13} {'bad streak':<11} {'usual':<7} last counts (newest first)"
    ]
    for source in sorted(past):
        runs = past[source]
        counts = [r.found for r in runs[: cfg.window] if r.status in RESPONDED]
        usual = f"{statistics.median(counts):g}" if counts else "-"
        streak = non_ok_streak([r.status for r in runs])
        recent = ", ".join(str(r.found) for r in runs[: cfg.window])
        lines.append(
            f"{names.get(source, source):<18} {runs[0].status.value:<13} {streak:<11} {usual:<7} {recent}"
        )
    return "\n".join(lines)


# -- sanitized debug samples ----------------------------------------------------------------

_URL = re.compile(r"^(https?://[^?#\s]+)[?#]\S*$")


def sanitize_value(value: Any, depth: int = 0) -> Any:
    """Make a scraped record safe to keep: no emails or phones, no URL queries, bounded size."""
    if depth > 4:
        return "..."
    if isinstance(value, str):
        text = _URL.sub(r"\1", value.strip())
        text = scrub_pii(text)
        return text if len(text) <= 200 else text[:200] + "\u2026"
    if isinstance(value, dict):
        return {str(k)[:60]: sanitize_value(v, depth + 1) for k, v in list(value.items())[:40]}
    if isinstance(value, list | tuple):
        return [sanitize_value(v, depth + 1) for v in value[:5]]
    if isinstance(value, bool | int | float) or value is None:
        return value
    return str(type(value).__name__)


def save_sample(
    source: str, records: Sequence[Mapping[str, Any]], reason: str, directory: Path, now: datetime
) -> Path:
    """Write up to three sanitized records that failed parsing, for debugging a layout change."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{source}-{now:%Y%m%d-%H%M%S}.json"
    payload = {
        "source": source,
        "reason": reason,
        "records": [sanitize_value(dict(r)) for r in records[:3]],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
