"""Deduplication and merge policy (doc 05).

Checks run in order and the first match wins:
1. canonical URL  2. source + source_job_id  3. fingerprint  4. near-duplicate.
Reposts: the same fingerprint returning after more than 30 days is a new posting.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from rapidfuzz import fuzz

from jobscraper.models import ExcludedRecord, Job, JobUpdate, StoredJob
from jobscraper.utils.urls import canonical_url, url_rank

REPOST_GAP = timedelta(days=30)
NEAR_WINDOW = timedelta(days=30)
TITLE_SIMILARITY = 90
DESCRIPTION_SIMILARITY = 85


def format_salary(job: Job) -> str:
    """Human-readable salary for the Sheet. Never converts currency (doc 05)."""
    if job.salary_min is None and job.salary_max is None:
        return ""
    low, high = job.salary_min, job.salary_max

    def fmt(value: float | None) -> str:
        return "" if value is None else f"{value:,.0f}"

    amount = fmt(low) if high is None or low == high else (fmt(high) if low is None else f"{fmt(low)}-{fmt(high)}")
    parts = [job.salary_currency or "", amount]
    if job.salary_period:
        parts.append(f"/{job.salary_period}")
    return " ".join(p for p in parts if p).replace(" /", "/")


@dataclass
class _Entry:
    job_id: str
    fingerprint: str
    company_norm: str
    title_norm: str
    source: str
    source_job_id: str | None
    job_url: str
    all_urls: list[str]
    excerpt: str
    last_seen: datetime | None
    has_salary: bool
    has_deadline: bool
    orig_job_url: str = ""
    new_job: Job | None = None  # set for entries created in this run
    changes: dict[str, str] = field(default_factory=dict)  # for stored entries


@dataclass
class DedupeOutcome:
    new_jobs: list[Job]
    updates: list[JobUpdate]
    duplicates: int
    new_by_source: Counter[str]
    duplicates_by_source: Counter[str]
    # Filled by the pipeline (Phase 4): jobs removed by hard filters, and why.
    excluded: list[ExcludedRecord] = field(default_factory=list)
    excluded_by_reason: Counter[str] = field(default_factory=Counter)


def _stored_norm(stored: StoredJob) -> tuple[str, str]:
    from jobscraper.parsers.names import normalize_company, normalize_title

    return normalize_company(stored.company), normalize_title(stored.title)


class Deduper:
    """Index of stored jobs plus jobs added during this run."""

    def __init__(self, stored: list[StoredJob], now: datetime) -> None:
        self._now = now
        self._by_url: dict[str, _Entry] = {}
        self._by_source_id: dict[tuple[str, str], _Entry] = {}
        self._by_fp: dict[str, list[_Entry]] = defaultdict(list)
        self._by_company: dict[str, list[_Entry]] = defaultdict(list)
        self._entries: list[_Entry] = []
        self._dupes: Counter[str] = Counter()
        for item in stored:
            company_norm, title_norm = _stored_norm(item)
            urls = list(dict.fromkeys([u for u in [item.job_url, *item.all_urls] if u]))
            self._register(
                _Entry(
                    job_id=item.job_id,
                    fingerprint=item.fingerprint,
                    company_norm=company_norm,
                    title_norm=title_norm,
                    source=item.source,
                    source_job_id=item.source_job_id,
                    job_url=item.job_url,
                    all_urls=urls,
                    excerpt=item.description_excerpt,
                    last_seen=item.last_seen or item.first_seen,
                    has_salary=bool(item.salary),
                    has_deadline=bool(item.application_deadline),
                )
            )

    # -- public ---------------------------------------------------------------

    def add(self, job: Job) -> bool:
        """Add one candidate. Returns True if it became a new job, False if merged."""
        entry = self._find(job)
        if entry is not None:
            self._merge(entry, job)
            self._dupes[job.source] += 1
            return False
        repost = self._is_repost(job)
        new_job = job.model_copy(
            update={"is_repost": repost, "last_seen": self._now, "all_urls": self._urls_of(job)}
        )
        self._register(
            _Entry(
                job_id=new_job.job_id,
                fingerprint=new_job.fingerprint,
                company_norm=new_job.company_normalized,
                title_norm=new_job.title_normalized,
                source=new_job.source,
                source_job_id=new_job.source_job_id,
                job_url=new_job.job_url,
                all_urls=new_job.all_urls,
                excerpt=new_job.description_excerpt,
                last_seen=self._now,
                has_salary=bool(format_salary(new_job)),
                has_deadline=new_job.application_deadline is not None,
                new_job=new_job,
            )
        )
        return True

    def finish(self) -> DedupeOutcome:
        new_jobs = [e.new_job for e in self._entries if e.new_job is not None]
        updates = [
            JobUpdate(job_id=e.job_id, fields=dict(e.changes))
            for e in self._entries
            if e.new_job is None and e.changes
        ]
        return DedupeOutcome(
            new_jobs=new_jobs,
            updates=updates,
            duplicates=sum(self._dupes.values()),
            new_by_source=Counter(j.source for j in new_jobs),
            duplicates_by_source=Counter(self._dupes),
        )

    # -- matching -------------------------------------------------------------

    @staticmethod
    def _urls_of(job: Job) -> list[str]:
        return list(dict.fromkeys([job.job_url, *job.all_urls]))

    def _find(self, job: Job) -> _Entry | None:
        for url in self._urls_of(job):  # 1. canonical URL
            hit = self._by_url.get(canonical_url(url))
            if hit is not None:
                return hit
        if job.source_job_id:  # 2. source + source_job_id
            hit = self._by_source_id.get((job.source, job.source_job_id))
            if hit is not None:
                return hit
        same_fp = self._by_fp.get(job.fingerprint)  # 3. fingerprint
        if job.fingerprint and same_fp:
            latest = max(same_fp, key=lambda e: e.last_seen or datetime.min.replace(tzinfo=self._now.tzinfo))
            if latest.last_seen is None or self._now - latest.last_seen <= REPOST_GAP:
                return latest
            return None  # returned after a long gap: a repost, handled by add()
        return self._near_duplicate(job)  # 4. near-duplicate

    def _is_repost(self, job: Job) -> bool:
        same_fp = self._by_fp.get(job.fingerprint) if job.fingerprint else None
        return bool(same_fp)

    def _near_duplicate(self, job: Job) -> _Entry | None:
        if not job.description_excerpt:
            return None
        for entry in self._by_company.get(job.company_normalized, []):
            if not entry.excerpt:
                continue
            if entry.last_seen is not None and abs(self._now - entry.last_seen) > NEAR_WINDOW:
                continue
            if fuzz.token_set_ratio(job.title_normalized, entry.title_norm) < TITLE_SIMILARITY:
                continue
            if fuzz.token_set_ratio(job.description_excerpt, entry.excerpt) >= DESCRIPTION_SIMILARITY:
                return entry
        return None

    # -- merge ----------------------------------------------------------------

    def _register(self, entry: _Entry) -> None:
        entry.orig_job_url = entry.job_url
        self._entries.append(entry)
        self._index(entry)

    def _index(self, entry: _Entry) -> None:
        for url in entry.all_urls:
            self._by_url.setdefault(canonical_url(url), entry)
        if entry.source_job_id:
            self._by_source_id.setdefault((entry.source, entry.source_job_id), entry)
        if entry.fingerprint and entry not in self._by_fp[entry.fingerprint]:
            self._by_fp[entry.fingerprint].append(entry)
        if entry.company_norm and entry not in self._by_company[entry.company_norm]:
            self._by_company[entry.company_norm].append(entry)

    def _merge(self, entry: _Entry, job: Job) -> None:
        """Merge policy: union URLs, prefer the employer's domain, keep richest values.

        `first_seen` is never touched: stored rows keep theirs, and a job created in
        this run has the same timestamp as any later duplicate.
        """
        known = {canonical_url(u) for u in entry.all_urls}
        added = [u for u in self._urls_of(job) if canonical_url(u) not in known]
        entry.all_urls = [*entry.all_urls, *added]
        best_url = max(entry.all_urls, key=url_rank)
        if url_rank(best_url) > url_rank(entry.job_url):
            entry.job_url = best_url
        if job.source_job_id:
            entry.source_job_id = entry.source_job_id or job.source_job_id
        entry.last_seen = self._now
        salary = format_salary(job)
        take_salary = bool(salary) and not entry.has_salary
        take_deadline = job.application_deadline is not None and not entry.has_deadline

        if entry.new_job is not None:
            updates: dict[str, object] = {"all_urls": entry.all_urls, "job_url": entry.job_url}
            if take_salary:
                updates.update(
                    salary_min=job.salary_min, salary_max=job.salary_max,
                    salary_currency=job.salary_currency, salary_period=job.salary_period,
                )
            if take_deadline:
                updates["application_deadline"] = job.application_deadline
            entry.new_job = entry.new_job.model_copy(update=updates)
        else:
            entry.changes["last_seen"] = self._now.isoformat()
            entry.changes["is_active"] = "TRUE"
            if added:
                entry.changes["all_urls"] = "\n".join(entry.all_urls)
            if entry.job_url != entry.orig_job_url:
                entry.changes["job_url"] = entry.job_url
            if take_salary:
                entry.changes["salary"] = salary
            if take_deadline and job.application_deadline is not None:
                entry.changes["application_deadline"] = job.application_deadline.isoformat()
        entry.has_salary = entry.has_salary or take_salary
        entry.has_deadline = entry.has_deadline or take_deadline
        self._index(entry)
