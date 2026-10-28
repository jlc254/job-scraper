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


# A language hit is only a hard requirement if its own sentence carries no optional marker
# (or carries a requirement word that is not negated, which wins). Sentences are split on the
# same separators described in doc 06: . ; ! ? and newlines.
_SEGMENTS = re.compile(r"[^.;!?\n]+")
_OPTIONAL_LANGUAGE = re.compile(
    r"\b(?:preferred|nice[- ]to[- ]have|a plus|an advantage|advantageous|desirable|bonus)\b",
    re.IGNORECASE,
)
# Positive requirement words — but NOT when preceded by "not" (e.g. "not required").
_REQUIRED_LANGUAGE = re.compile(
    r"(?<!\bnot )\b(?:required|mandatory|essential|must)\b",
    re.IGNORECASE,
)


def _build_segment_index(text: str) -> list[tuple[int, int, str]]:
    """Return a list of (start, end, segment_text) for all sentence segments in *text*.

    Pre-computing this index lets the caller look up segments in O(n) per pass instead of
    rescanning from the beginning for each language-pattern match.
    """
    return [(m.start(), m.end(), m.group(0)) for m in _SEGMENTS.finditer(text)]


def _segment_for_pos(index: list[tuple[int, int, str]], pos: int) -> str:
    """Return the segment text that contains *pos*, or an empty string."""
    for start, end, text in index:
        if start <= pos < end:
            return text
    return ""


class JobFilters:
    """Order follows doc 06. Region restriction runs first because it is the most common waste."""

    def __init__(self, cfg: FilterSettings, today: date) -> None:
        self._cfg = cfg
        self._today = today
        self._region = _compile(cfg.region_restricted_patterns)
        self._scam = _compile(cfg.scam_patterns)
        self._titles = _compile(cfg.excluded_title_patterns)
        self._languages = _compile(cfg.language_required_patterns)
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
        seg_index = _build_segment_index(text)
        for pattern in self._languages:
            for hit in pattern.finditer(text):
                segment = _segment_for_pos(seg_index, hit.start())
                if _OPTIONAL_LANGUAGE.search(segment) and not _REQUIRED_LANGUAGE.search(segment):
                    continue  # optional preference ("a plus"), not a hard requirement
                return Exclusion("language_required", _snippet(hit))
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
