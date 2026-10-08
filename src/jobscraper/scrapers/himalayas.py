"""Himalayas public JSON API adapter.

Response shape (from memory, VERIFY against tests/fixtures/himalayas.json):
{"jobs": [{"title", "companyName", "employmentType", "minSalary", "maxSalary",
           "currency", "seniority": [...], "locationRestrictions": [...],
           "description", "pubDate", "expiryDate", "applicationLink", "guid"}], ...}
Pagination is offset/limit here. Doc 02 says "cursor (verify)", so confirm
against the real response and adjust `fetch` if needed.
"""

from __future__ import annotations

from typing import Any

from jobscraper.models import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RawJob,
    RemoteEligibility,
    WorkType,
    make_job_id,
)
from jobscraper.parsers.text import (
    clean_str,
    html_to_text,
    parse_date,
    safe_http_url,
    truncate,
)
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import register
from jobscraper.utils.errors import SchemaError
from jobscraper.utils.http import HttpClient
from jobscraper.utils.pii import scrub_pii

API_URL = "https://himalayas.app/jobs/api"
SOURCE_URL = "https://himalayas.app/jobs"
MAX_TEXT_CHARS = 20_000

_EMPLOYMENT = {
    "full time": EmploymentType.FULL_TIME,
    "full-time": EmploymentType.FULL_TIME,
    "part time": EmploymentType.PART_TIME,
    "part-time": EmploymentType.PART_TIME,
    "contractor": EmploymentType.CONTRACT,
    "contract": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "intern": EmploymentType.INTERNSHIP,
    "internship": EmploymentType.INTERNSHIP,
}
_SENIORITY = (
    ("entry", ExperienceLevel.ENTRY),
    ("junior", ExperienceLevel.ENTRY),
    ("mid", ExperienceLevel.MID),
    ("senior", ExperienceLevel.SENIOR),
    ("lead", ExperienceLevel.LEAD),
    ("manager", ExperienceLevel.MANAGER),
    ("director", ExperienceLevel.MANAGER),
)


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if value > 0 else None


def _eligibility(restrictions: list[str]) -> RemoteEligibility:
    if not restrictions:
        return RemoteEligibility.WORLDWIDE
    lowered = {r.lower() for r in restrictions}
    if "kenya" in lowered:
        return RemoteEligibility.KENYA
    if lowered & {"africa", "east africa"}:
        return RemoteEligibility.AFRICA
    if lowered & {"worldwide", "anywhere", "global"}:
        return RemoteEligibility.WORLDWIDE
    # Named countries that do not include Kenya. Phase 4 filters decide what to do.
    return RemoteEligibility.RESTRICTED


def _experience(seniority: list[str]) -> ExperienceLevel:
    for item in seniority:
        lowered = item.lower()
        for needle, level in _SENIORITY:
            if needle in lowered:
                return level
    return ExperienceLevel.UNKNOWN


@register
class HimalayasAdapter(Adapter):
    id = "himalayas"
    display_name = "Himalayas"
    allowed_hosts = frozenset({"himalayas.app"})

    def fetch(self, client: HttpClient) -> list[RawJob]:
        raws: list[RawJob] = []
        page_size = self.config.page_size
        for page in range(self.config.max_pages):
            payload: Any = client.get(
                API_URL, params={"limit": page_size, "offset": page * page_size}
            ).json()
            jobs = payload.get("jobs") if isinstance(payload, dict) else None
            if not isinstance(jobs, list):
                raise SchemaError("Himalayas response has no 'jobs' list")
            if not jobs:
                break
            raws.extend(RawJob(source=self.id, data=j) for j in jobs if isinstance(j, dict))
            if len(jobs) < page_size:
                break
        return raws

    def to_job(self, raw: RawJob) -> Job | None:
        data = raw.data
        title = clean_str(data.get("title"))
        company = clean_str(data.get("companyName"))
        job_url = safe_http_url(data.get("applicationLink"))
        if title is None or company is None or job_url is None:
            return None
        source_job_id = clean_str(data.get("guid")) or job_url
        restrictions = _as_str_list(data.get("locationRestrictions"))
        description = clean_str(data.get("description")) or clean_str(data.get("excerpt")) or ""
        text = scrub_pii(html_to_text(description))[:MAX_TEXT_CHARS]
        employment = clean_str(data.get("employmentType")) or ""
        currency = clean_str(data.get("currency"))
        return Job(
            job_id=make_job_id(self.id, source_job_id),
            title=title,
            company=company,
            job_url=job_url,
            source=self.id,
            source_url=SOURCE_URL,
            source_job_id=source_job_id,
            location=", ".join(restrictions) if restrictions else "Worldwide",
            work_type=WorkType.REMOTE,
            employment_type=_EMPLOYMENT.get(employment.lower(), EmploymentType.UNKNOWN),
            remote_eligibility=_eligibility(restrictions),
            posting_country_restrictions=restrictions,
            salary_min=_number(data.get("minSalary")),
            salary_max=_number(data.get("maxSalary")),
            salary_currency=currency,
            # salary_period left empty: unconfirmed in the API docs (verify).
            experience_level=_experience(_as_str_list(data.get("seniority"))),
            description_excerpt=truncate(text, self.config.excerpt_max_chars),
            date_posted=parse_date(data.get("pubDate")),
            application_deadline=parse_date(data.get("expiryDate")),
            first_seen=self.now,
            scoring_text=text,
        )
