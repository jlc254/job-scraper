"""Pydantic models shared by adapters, runner and (later) storage."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SourceStatus(StrEnum):
    """How a source ended a run (doc 07)."""

    OK = "ok"
    DEGRADED = "degraded"
    PARTIAL = "partial"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkType(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    UNKNOWN = "unknown"


class RemoteEligibility(StrEnum):
    WORLDWIDE = "worldwide"
    AFRICA = "africa"
    EAST_AFRICA = "east_africa"
    KENYA = "kenya"
    TIMEZONE_LIMITED = "timezone_limited"
    RESTRICTED = "restricted"
    UNCLEAR = "unclear"


class ExperienceLevel(StrEnum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    UNKNOWN = "unknown"


class MatchTier(StrEnum):
    TOP = "top"
    STRONG = "strong"
    POTENTIAL = "potential"
    WEAK = "weak"


class RawJob(BaseModel):
    """One unmapped record exactly as the source returned it."""

    source: str
    data: dict[str, Any]


class Job(BaseModel):
    """Common job schema (subset of doc 05 that Phase 2 can fill).

    Fingerprint, scoring and tracking fields arrive in Phases 3 and 4.
    """

    job_id: str
    title: str
    company: str
    job_url: str
    source: str
    source_url: str
    source_job_id: str | None = None
    location: str | None = None
    work_type: WorkType = WorkType.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    remote_eligibility: RemoteEligibility = RemoteEligibility.UNCLEAR
    posting_country_restrictions: list[str] = Field(default_factory=list)
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN
    description_excerpt: str = ""
    date_posted: date | None = None
    application_deadline: date | None = None
    first_seen: datetime
    # Phase 3: normalization, dedupe and tracking fields (doc 05).
    last_seen: datetime | None = None
    is_active: bool = True
    is_repost: bool = False
    fingerprint: str = ""
    title_normalized: str = ""
    company_normalized: str = ""
    company_domain: str | None = None
    country: str | None = None
    all_urls: list[str] = Field(default_factory=list)
    # Phase 4: scoring output (doc 05, doc 06).
    match_score: float | None = None
    match_tier: MatchTier | None = None
    match_breakdown: dict[str, Any] | None = None
    skills_required: list[str] = Field(default_factory=list)
    skills_preferred: list[str] = Field(default_factory=list)
    skills_matched: list[str] = Field(default_factory=list)
    skills_missing: list[str] = Field(default_factory=list)
    transferable: list[str] = Field(default_factory=list)
    recommended_action: str = ""
    checklist: str = ""
    # Full scrubbed text kept in memory only, for filtering and scoring (doc 03).
    scoring_text: str = Field(default="", exclude=True, repr=False)


class SourceResult(BaseModel):
    """Per-source outcome recorded by the runner (doc 04)."""

    source: str
    status: SourceStatus
    found: int = 0
    kept: int = 0
    dropped: int = 0
    filtered: int = 0
    duplicates: int = 0
    excluded: int = 0
    new: int | None = None  # set once dedupe has run (Phase 3)
    error: str | None = None
    duration_s: float = 0.0


def make_job_id(source: str, source_job_id: str) -> str:
    """Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)."""
    digest = hashlib.sha1(f"{source}{source_job_id}".encode(), usedforsecurity=False)
    return digest.hexdigest()[:12]


class StoredJob(BaseModel):
    """What the dedupe step needs to know about a job already in storage."""

    job_id: str
    fingerprint: str = ""
    title: str = ""
    company: str = ""
    job_url: str = ""
    all_urls: list[str] = Field(default_factory=list)
    source: str = ""
    source_job_id: str | None = None
    description_excerpt: str = ""
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    salary: str = ""
    application_deadline: str = ""


class JobUpdate(BaseModel):
    """Changes to system-owned columns of an existing row. Never user columns."""

    job_id: str
    fields: dict[str, str]


class ExcludedRecord(BaseModel):
    """A job removed by a hard filter, kept in the Excluded tab as an audit trail."""

    job_id: str
    title: str
    company: str
    source: str
    job_url: str
    reason: str
    detail: str = ""
    excluded_at: datetime


class SourceRun(BaseModel):
    """One source's outcome in one run. The Health tab keeps these to spot trends (doc 07)."""

    run_id: str
    started_utc: datetime
    source: str
    status: SourceStatus
    found: int = 0
    new: int = 0
    dropped: int = 0
    excluded: int = 0
    error: str = ""

    @property
    def key(self) -> str:
        return f"{self.run_id}:{self.source}"
