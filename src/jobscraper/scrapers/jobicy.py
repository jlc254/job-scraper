"""Jobicy public JSON API adapter. Rate limit: at most one request per hour (doc 02).

Shape (from memory, VERIFY against tests/fixtures/jobicy.json):
{"jobs": [{"id", "url", "jobTitle", "companyName", "jobType": [...], "jobGeo",
           "jobLevel", "jobExcerpt", "jobDescription", "pubDate",
           "annualSalaryMin", "annualSalaryMax", "salaryCurrency"}]}
Default query is count=50. Add `query_params` (for example industry or geo) in
sources.yaml after checking the API's documented values.
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
from jobscraper.parsers.names import geo_eligibility
from jobscraper.parsers.text import clean_str, html_to_text, parse_date, safe_http_url, truncate
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import register
from jobscraper.utils.errors import SchemaError
from jobscraper.utils.http import HttpClient
from jobscraper.utils.pii import scrub_pii

API_URL = "https://jobicy.com/api/v2/remote-jobs"
SOURCE_URL = "https://jobicy.com/"
MAX_TEXT_CHARS = 20_000

_EMPLOYMENT = {
    "full-time": EmploymentType.FULL_TIME,
    "part-time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "internship": EmploymentType.INTERNSHIP,
}
_LEVEL = {
    "junior": ExperienceLevel.ENTRY,
    "midweight": ExperienceLevel.MID,
    "mid": ExperienceLevel.MID,
    "senior": ExperienceLevel.SENIOR,
}


def _num(value: object) -> float | None:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _first_str(value: object) -> str | None:
    if isinstance(value, list):
        value = next((v for v in value if isinstance(v, str) and v.strip()), None)
    return clean_str(value)


@register
class JobicyAdapter(Adapter):
    id = "jobicy"
    display_name = "Jobicy"
    allowed_hosts = frozenset({"jobicy.com"})

    def fetch(self, client: HttpClient) -> list[RawJob]:
        params: dict[str, str | int] = {"count": 50}
        params.update(self.config.query_params)
        payload: Any = client.get(API_URL, params=params).json()
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            raise SchemaError("Jobicy response has no 'jobs' list")
        return [RawJob(source=self.id, data=j) for j in jobs if isinstance(j, dict)]

    def to_job(self, raw: RawJob) -> Job | None:
        data = raw.data
        title = clean_str(data.get("jobTitle"))
        company = clean_str(data.get("companyName"))
        job_url = safe_http_url(data.get("url"))
        if title is None or company is None or job_url is None:
            return None
        raw_id = data.get("id")
        source_job_id = str(raw_id) if isinstance(raw_id, int | str) and str(raw_id) else job_url
        geo = clean_str(data.get("jobGeo"))
        description = (
            clean_str(data.get("jobDescription")) or clean_str(data.get("jobExcerpt")) or ""
        )
        text = scrub_pii(html_to_text(description))[:MAX_TEXT_CHARS]
        job_type = (_first_str(data.get("jobType")) or "").lower()
        level = (clean_str(data.get("jobLevel")) or "").lower()
        eligibility = geo_eligibility(geo)
        return Job(
            job_id=make_job_id(self.id, source_job_id),
            title=title,
            company=company,
            job_url=job_url,
            source=self.id,
            source_url=SOURCE_URL,
            source_job_id=source_job_id,
            location=geo,
            work_type=WorkType.REMOTE,
            employment_type=_EMPLOYMENT.get(job_type, EmploymentType.UNKNOWN),
            remote_eligibility=RemoteEligibility(eligibility),
            posting_country_restrictions=[geo] if eligibility == "restricted" and geo else [],
            salary_min=_num(data.get("annualSalaryMin")),
            salary_max=_num(data.get("annualSalaryMax")),
            salary_currency=clean_str(data.get("salaryCurrency")),
            salary_period="year" if _num(data.get("annualSalaryMin")) else None,
            experience_level=_LEVEL.get(level, ExperienceLevel.UNKNOWN),
            description_excerpt=truncate(text, self.config.excerpt_max_chars),
            date_posted=parse_date(data.get("pubDate")),
            first_seen=self.now,
            scoring_text=text,
        )
