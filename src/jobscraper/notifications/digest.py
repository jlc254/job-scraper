"""Build the Telegram digest and follow-up reminders from stored rows (doc 04, doc 06).

Pure functions over row dictionaries, so the same code serves real runs (rows read back from
storage, which is how a failed send is retried on the next run) and dry runs.
Everything is plain text. Scraped fields are sanitised, never trusted.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from jobscraper.models import SourceResult, SourceStatus
from jobscraper.utils.dates import EAT, parse_timestamp, parse_user_date

TIER_ORDER = {"top": 0, "strong": 1, "potential": 2}
TIER_LABEL = {"top": "Top match", "strong": "Strong match", "potential": "Potential"}
ELIGIBILITY_TEXT = {
    "worldwide": "open worldwide",
    "africa": "open to Africa",
    "east_africa": "open to East Africa",
    "kenya": "open to Kenya",
    "timezone_limited": "timezone-limited",
    "unclear": "region not stated",
    "restricted": "restricted",
}
ACRONYMS = {"crm", "sql", "api", "pos", "sla", "erp", "kpi", "bpo"}
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class DigestConfig:
    max_potential: int = 5
    potential_lookback_days: int = 2
    max_jobs: int = 30
    jobs_per_message: int = 10
    follow_up_days: int = 7
    max_follow_ups: int = 15
    body_limit: int = 3800  # Telegram allows 4096. The rest is room for headers and page markers.
    empty_digest_before_hour_eat: int = 12


@dataclass
class Batch:
    """One message and the rows it covers, so only delivered rows are marked as sent."""

    body: str
    job_ids: list[str] = field(default_factory=list)
    follow_up_ids: list[str] = field(default_factory=list)
    text: str = ""


@dataclass
class Digest:
    batches: list[Batch]
    unreadable_dates: int = 0

    @property
    def messages(self) -> list[str]:
        return [b.text for b in self.batches]


# -- text helpers -------------------------------------------------------------


def clean(value: object, max_len: int = 120) -> str:
    """One safe line: no control or bidi characters, collapsed whitespace, length-capped."""
    text = _SPACES.sub(" ", _CONTROL.sub(" ", str(value or ""))).strip()
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "\u2026"


def safe_url(value: object) -> str | None:
    text = _CONTROL.sub("", str(value or "")).strip()
    if " " in text or not text.lower().startswith(("http://", "https://")) or len(text) > 300:
        return None
    return text


def _skill_label(name: str) -> str:
    return name.upper() if name.lower() in ACRONYMS else name[:1].upper() + name[1:]


def _skills(value: str, limit: int = 5) -> str:
    items = [clean(s, 40) for s in value.split(";") if s.strip()]
    return ", ".join(_skill_label(s) for s in items[:limit])


def _score(row: dict[str, str]) -> float:
    try:
        return float(row.get("match_score") or 0)
    except ValueError:
        return 0.0


def _posted(row: dict[str, str], today: date) -> str:
    posted = parse_user_date(row.get("date_posted"))
    if posted is None:
        return "date unknown"
    days = (today - posted).days
    if days <= 0:
        return "today"
    return "1 day ago" if days == 1 else f"{days} days ago"


def _where(row: dict[str, str]) -> str:
    if (row.get("work_type") or "") == "remote":
        elig = ELIGIBILITY_TEXT.get(row.get("remote_eligibility") or "unclear", "region not stated")
        return f"Remote: {elig}"
    return f"Location: {clean(row.get('location') or 'not stated', 50)}"


# -- selection ----------------------------------------------------------------


def select_jobs(
    rows: Sequence[dict[str, str]], today: date, now: datetime, cfg: DigestConfig
) -> list[dict[str, str]]:
    """Unnotified Top and Strong jobs, plus up to `max_potential` recent Potential ones.

    Skips jobs the owner already handled (status other than New), inactive and expired ones.
    Weak jobs are never notified. Anything not shown stays unmarked and is retried next run.
    """
    lookback = timedelta(days=cfg.potential_lookback_days)
    strong: list[dict[str, str]] = []
    potential: list[dict[str, str]] = []
    for row in rows:
        tier = (row.get("match_tier") or "").strip().lower()
        if tier not in TIER_ORDER or (row.get("notified_at") or "").strip():
            continue
        if (row.get("application_status") or "New").strip().lower() not in ("new", ""):
            continue
        if (row.get("is_active") or "TRUE").strip().upper() == "FALSE":
            continue
        deadline = parse_user_date(row.get("application_deadline"))
        if deadline is not None and deadline < today:
            continue
        if tier == "potential":
            seen = parse_timestamp(row.get("first_seen"))
            if seen is not None and now - seen > lookback:
                continue
            potential.append(row)
        else:
            strong.append(row)
    strong.sort(key=lambda r: (TIER_ORDER[(r.get("match_tier") or "").lower()], -_score(r)))
    potential.sort(key=lambda r: -_score(r))
    return (strong + potential[: cfg.max_potential])[: cfg.max_jobs]


def due_follow_ups(
    rows: Sequence[dict[str, str]], today: date, cfg: DigestConfig
) -> tuple[list[tuple[dict[str, str], date | None]], int]:
    """Applied jobs whose follow-up date has arrived and has not been reminded yet.

    The date is the owner's follow_up_date, else applied_on plus 7 days. It is computed here,
    never written into the owner's columns. Returns (rows with applied_on, unreadable count).
    """
    due: list[tuple[dict[str, str], date | None]] = []
    unreadable = 0
    for row in rows:
        if (row.get("application_status") or "").strip().lower() != "applied":
            continue
        applied_text = (row.get("applied_on") or "").strip()
        follow_text = (row.get("follow_up_date") or "").strip()
        applied = parse_user_date(applied_text)
        follow = parse_user_date(follow_text)
        if follow_text and follow is None or applied_text and applied is None and follow is None:
            unreadable += 1
            continue
        due_date = follow or (applied + timedelta(days=cfg.follow_up_days) if applied else None)
        if due_date is None or due_date > today:
            continue
        reminded = parse_user_date(row.get("follow_up_reminded_on"))
        if reminded is not None and reminded >= due_date:
            continue  # already reminded for this due date
        due.append((row, applied))
    due.sort(key=lambda item: item[0].get("title", ""))
    return due, unreadable


# -- formatting ---------------------------------------------------------------


def format_job(number: int, row: dict[str, str], today: date, source_names: dict[str, str]) -> str:
    tier = (row.get("match_tier") or "").lower()
    score = int(_score(row) + 0.5)
    repost = " (repost)" if (row.get("is_repost") or "").upper() == "TRUE" else ""
    lines = [
        f"{number}. {clean(row.get('title'))}  [{TIER_LABEL.get(tier, tier)} {score}]{repost}",
        f"   Company: {clean(row.get('company'), 60)} | {_where(row)} | Posted: {_posted(row, today)}",
    ]
    have, missing = _skills(row.get("skills_matched", "")), _skills(row.get("skills_missing", ""))
    if have or missing:
        lines.append(f"   You have: {have or '-'} | Missing: {missing or '-'}")
    source = source_names.get(row.get("source") or "", row.get("source") or "unknown")
    tail = [
        f"Salary: {clean(row.get('salary') or 'not listed', 40)}",
        f"Source: {clean(source, 40)}",
    ]
    deadline = parse_user_date(row.get("application_deadline"))
    if deadline is not None:
        tail.append(f"Deadline: {deadline.isoformat()}")
    lines.append("   " + " | ".join(tail))
    action = clean(row.get("recommended_action"), 300)
    if action:
        lines.append(f"   Next: {action}")
    lines.append(f"   Apply: {safe_url(row.get('job_url')) or 'link unavailable'}")
    return "\n".join(lines)


def format_follow_ups(
    due: list[tuple[dict[str, str], date | None]], today: date, cfg: DigestConfig
) -> str:
    lines = ["FOLLOW-UPS DUE TODAY"]
    for row, applied in due[: cfg.max_follow_ups]:
        if applied is None:
            note = "follow-up date reached"
        else:
            days = (today - applied).days
            note = f"applied {days} day{'s' if days != 1 else ''} ago"
        lines.append(f"- {clean(row.get('company'), 60)}, {clean(row.get('title'))} ({note})")
    if len(due) > cfg.max_follow_ups:
        lines.append(f"...and {len(due) - cfg.max_follow_ups} more")
    return "\n".join(lines)


def has_problems(results: Sequence[SourceResult]) -> bool:
    return any(r.status not in (SourceStatus.OK, SourceStatus.SKIPPED) for r in results)


def run_summary(results: Sequence[SourceResult], source_names: dict[str, str]) -> str:
    """The RUN line from doc 04, for example: 4 sources ok, 1 degraded (Jobicy: 0 results)."""
    ran = [r for r in results if r.status is not SourceStatus.SKIPPED]
    parts = [f"{sum(1 for r in ran if r.status is SourceStatus.OK)} sources ok"]
    for status in (
        SourceStatus.PARTIAL,
        SourceStatus.DEGRADED,
        SourceStatus.RATE_LIMITED,
        SourceStatus.BLOCKED,
        SourceStatus.FAILED,
    ):
        hit = [r for r in ran if r.status is status]
        if not hit:
            continue
        names = []
        for r in hit:
            name = source_names.get(r.source, r.source)
            names.append(
                f"{name}: 0 results" if r.status is SourceStatus.DEGRADED and r.found == 0 else name
            )
        parts.append(f"{len(hit)} {status.value.replace('_', ' ')} ({', '.join(names)})")
    parts.append(f"{sum(r.found for r in ran)} found")
    parts.append(f"{sum(r.new or 0 for r in ran)} new")
    excluded = sum(r.excluded for r in ran)
    if excluded:
        parts.append(f"{excluded} excluded")
    return "RUN: " + ", ".join(parts)


# -- assembly -----------------------------------------------------------------


def build_digest(
    rows: Sequence[dict[str, str]],
    results: Sequence[SourceResult],
    *,
    now: datetime,
    source_names: dict[str, str],
    config: DigestConfig | None = None,
    report_text: str | None = None,
    notify_problems: bool | None = None,
    title: str = "NEW CUSTOMER SUPPORT JOBS",
) -> Digest:
    """Plan the messages. An empty digest is only worth sending in the morning, or when a
    source has a problem, so quiet afternoon runs stay silent."""
    cfg = config or DigestConfig()
    local = now.astimezone(EAT)
    today = local.date()
    jobs = select_jobs(rows, today, now, cfg)
    due, unreadable = due_follow_ups(rows, today, cfg)
    # The caller can pass health findings, so a source that stays broken does not force a
    # message every run. The RUN line still shows it whenever a digest is sent.
    problems = has_problems(results) if notify_problems is None else notify_problems

    if (
        not jobs
        and not due
        and not problems
        and unreadable == 0
        and local.hour >= cfg.empty_digest_before_hour_eat
    ):
        return Digest([], 0)

    sections: list[tuple[str, list[str], list[str]]] = []  # (text, job_ids, follow_up_ids)
    for number, row in enumerate(jobs, start=1):
        sections.append((format_job(number, row, today, source_names), [row.get("job_id", "")], []))
    if due:
        ids = [r.get("job_id", "") for r, _ in due[: cfg.max_follow_ups]]
        sections.append((format_follow_ups(due, today, cfg), [], ids))
    if unreadable:
        sections.append(
            (
                f"NOTE: {unreadable} applied job(s) have a date I could not read. "
                "Use a format like 2026-10-01 or 01/10/2026.",
                [],
                [],
            )
        )
    sections.append((run_summary(results, source_names), [], []))

    batches: list[Batch] = []
    current = Batch(body="")
    job_count = 0
    for text, job_ids, follow_ids in sections:
        is_job = bool(job_ids)
        too_long = current.body and len(current.body) + 2 + len(text) > cfg.body_limit
        too_many = is_job and job_count >= cfg.jobs_per_message
        if current.body and (too_long or too_many):
            batches.append(current)
            current, job_count = Batch(body=""), 0
        current.body = f"{current.body}\n\n{text}" if current.body else text
        current.job_ids += [j for j in job_ids if j]
        current.follow_up_ids += [f for f in follow_ids if f]
        job_count += 1 if is_job else 0
    batches.append(current)

    heading = (
        f"{title} ({today.isoformat()}, EAT)"
        if jobs
        else f"NO NEW MATCHING JOBS ({today.isoformat()}, EAT)"
    )
    total = len(batches)
    for index, batch in enumerate(batches, start=1):
        marker = f" [{index}/{total}]" if total > 1 else ""
        head = heading + marker if index == 1 else f"{heading.split(' (')[0]} (continued){marker}"
        batch.text = f"{head}\n\n{batch.body}"
    if report_text and problems:  # detail for a broken source, kept out of the page numbering
        batches.append(Batch(body="", text=f"RUN REPORT\n{report_text}"[: cfg.body_limit]))
    return Digest(batches, unreadable)
