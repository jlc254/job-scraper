"""Greenhouse public job board adapter (one adapter for every company board).

Endpoint: https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
Shape (VERIFY against tests/fixtures/greenhouse.json):
{"jobs": [{"id", "title", "updated_at", "absolute_url", "location": {"name"},
           "content": "<entity-escaped HTML>", ...}], "meta": {...}}
Companies are listed under `boards` in sources.yaml, either as a token string
or as {token: ..., name: ...}. The jobs endpoint does not return the company
name, so a plain token is used as the name unless one is given.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from jobscraper.models import Job, RawJob, RemoteEligibility, WorkType, make_job_id
from jobscraper.parsers.text import (
    clean_str,
    parse_date,
    safe_http_url,
    truncate,
    unescape_then_text,
)
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import register
from jobscraper.utils.errors import (
    BlockedError,
    FetchError,
    RateLimitedError,
    SchemaError,
)
from jobscraper.utils.http import HttpClient
from jobscraper.utils.pii import scrub_pii

log = logging.getLogger(__name__)

BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
SOURCE_URL = "https://boards.greenhouse.io/{token}"
_TOKEN = re.compile(r"[A-Za-z0-9_-]{1,64}")
MAX_TEXT_CHARS = 20_000


def _board_entries(boards: list[str | dict[str, str]]) -> list[tuple[str, str]]:
    """Return (token, company name) pairs, skipping invalid tokens."""
    entries: list[tuple[str, str]] = []
    for item in boards:
        token = item if isinstance(item, str) else item.get("token", "")
        name = token if isinstance(item, str) else item.get("name", token)
        if _TOKEN.fullmatch(token):
            entries.append((token, name or token))
        else:
            log.warning("ignoring invalid Greenhouse board token")
    return entries


@register
class GreenhouseAdapter(Adapter):
    id = "greenhouse"
    display_name = "Greenhouse boards"
    allowed_hosts = frozenset({"boards-api.greenhouse.io"})

    def fetch(self, client: HttpClient) -> list[RawJob]:
        entries = _board_entries(self.config.boards)
        if not entries:
            raise SchemaError("no valid Greenhouse boards configured")
        raws: list[RawJob] = []
        failures = 0
        last_error: FetchError | None = None
        for token, name in entries:
            try:
                payload: Any = client.get(
                    BOARD_URL.format(token=token), params={"content": "true"}
                ).json()
                jobs = payload.get("jobs") if isinstance(payload, dict) else None
                if not isinstance(jobs, list):
                    raise SchemaError("Greenhouse response has no 'jobs' list")
            except (BlockedError, RateLimitedError):
                raise  # Source-level problems stop the whole source.
            except FetchError as exc:
                failures += 1
                last_error = exc
                self.partial_errors.append(f"{token}: {type(exc).__name__}")
                continue
            for job in jobs:
                if isinstance(job, dict):
                    record = dict(job)
                    record["_board"] = token
                    record["_company"] = name
                    raws.append(RawJob(source=self.id, data=record))
        if failures == len(entries) and last_error is not None:
            raise last_error
        return raws

    def to_job(self, raw: RawJob) -> Job | None:
        data = raw.data
        title = clean_str(data.get("title"))
        company = clean_str(data.get("_company"))
        token = clean_str(data.get("_board"))
        job_url = safe_http_url(data.get("absolute_url"))
        job_number = data.get("id")
        if title is None or company is None or token is None or job_url is None:
            return None
        if isinstance(job_number, bool) or not isinstance(job_number, int | str):
            return None
        source_job_id = f"{token}:{job_number}"
        location_obj = data.get("location")
        location = clean_str(location_obj.get("name")) if isinstance(location_obj, dict) else None
        content = clean_str(data.get("content")) or ""
        text = scrub_pii(unescape_then_text(content))[:MAX_TEXT_CHARS]
        is_remote = location is not None and "remote" in location.lower()
        return Job(
            job_id=make_job_id(self.id, source_job_id),
            title=title,
            company=company,
            job_url=job_url,
            source=self.id,
            source_url=SOURCE_URL.format(token=token),
            source_job_id=source_job_id,
            location=location,
            work_type=WorkType.REMOTE if is_remote else WorkType.UNKNOWN,
            remote_eligibility=RemoteEligibility.UNCLEAR,
            description_excerpt=truncate(text, self.config.excerpt_max_chars),
            # Greenhouse exposes first_published on some boards, else updated_at.
            date_posted=parse_date(data.get("first_published") or data.get("updated_at")),
            first_seen=self.now,
            scoring_text=text,
        )
