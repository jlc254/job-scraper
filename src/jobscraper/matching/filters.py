"""Hard filters (doc 06, step 1). A job that fails is excluded, logged and never notified."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from jobscraper.matching.settings import FilterSettings
from jobscraper.models import Job, RemoteEligibility


@dataclass(frozen=True)
class Exclusion:
    reason: str
    detail: str = ""


def _compile(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _keyword_regex(keywords: list[str]) -> re.Pattern[str]:
    parts = [r"\b" + re.escape(k.lower()) for k in keywords if k.strip()]
    return re.compile("|".join(parts) if parts else r"(?!x)x", re.IGNORECASE)


def _snippet(match: re.Match[str]) -> str:
    return match.group(0).strip()[:80]


class JobFilters:
    """Order follows doc 06. Region restriction runs first because it is the most common waste."""

    def __init__(self, cfg: FilterSettings, today: date) -> None:
        self._cfg = cfg
        self._today = today
        self._region = _compile(cfg.region_restricted_patterns)
        self._scam = _compile(cfg.scam_patterns)
        self._titles = _compile(cfg.excluded_title_patterns)
        self._support = _keyword_regex(cfg.support_keywords)

    def check(self, job: Job) -> Exclusion | None:
        text = f"{job.title}\n{job.scoring_text}"
        if job.remote_eligibility is RemoteEligibility.RESTRICTED:
            where = ", ".join(job.posting_country_restrictions) or "unspecified"
            return Exclusion("region_restricted", f"source lists: {where}")
        for pattern in self._region:
            hit = pattern.search(text)
            if hit:
                return Exclusion("region_restricted", _snippet(hit))
        if job.application_deadline is not None and job.application_deadline < self._today:
            return Exclusion("expired", job.application_deadline.isoformat())
        for pattern in self._scam:
            hit = pattern.search(text)
            if hit:
                return Exclusion("scam_pattern", _snippet(hit))
        for pattern in self._titles:
            hit = pattern.search(job.title)
            if hit:
                return Exclusion("excluded_title", _snippet(hit))
        opening = job.scoring_text[: self._cfg.offtopic_chars]
        if not (self._support.search(job.title) or self._support.search(opening)):
            return Exclusion("off_topic", "no support keyword in title or opening text")
        if job.date_posted is not None:
            cutoff = self._today - timedelta(days=self._cfg.max_age_days)
            deadline_ahead = (
                job.application_deadline is not None and job.application_deadline >= self._today
            )
            if job.date_posted < cutoff and not deadline_ahead:
                return Exclusion("too_old", job.date_posted.isoformat())
        return None
