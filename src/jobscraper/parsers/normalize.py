"""Fill the normalized fields of a Job. Runs on every job before dedupe."""

from __future__ import annotations

import hashlib

from jobscraper.models import Job, RemoteEligibility, WorkType
from jobscraper.parsers.names import classify_location, normalize_company, normalize_title
from jobscraper.utils.urls import employer_domain


def fingerprint(company_norm: str, title_norm: str, scope: str) -> str:
    """sha1 of company + title + location scope (country, or 'remote')."""
    raw = f"{company_norm}|{title_norm}|{scope}"
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()


def normalize_job(job: Job) -> Job:
    """Return a copy with normalized names, country, scope-based fingerprint and URLs."""
    info = classify_location(job.location)
    title_norm = normalize_title(job.title)
    company_norm = normalize_company(job.company)
    work_type = job.work_type
    if work_type is WorkType.UNKNOWN and info.is_remote:
        work_type = WorkType.REMOTE
    eligibility = job.remote_eligibility
    if eligibility is RemoteEligibility.UNCLEAR and info.eligibility:
        eligibility = RemoteEligibility(info.eligibility)
    country = job.country or info.country
    scope = "remote" if work_type is WorkType.REMOTE else (country or "unknown")
    urls = list(dict.fromkeys([job.job_url, *job.all_urls]))
    return job.model_copy(
        update={
            "title_normalized": title_norm,
            "company_normalized": company_norm,
            "country": country,
            "work_type": work_type,
            "remote_eligibility": eligibility,
            "fingerprint": fingerprint(company_norm, title_norm, scope),
            "company_domain": job.company_domain or employer_domain(job.job_url),
            "all_urls": urls,
            "last_seen": job.last_seen or job.first_seen,
        }
    )
