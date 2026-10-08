"""We Work Remotely RSS adapter (customer-support category feed).

Feed items (VERIFY against tests/fixtures/weworkremotely.xml): title is
"Company: Job Title", plus link, guid, pubDate, description and a custom
<region> element. feedparser exposes unknown tags as entry["region"].
"""

from __future__ import annotations

from typing import Any

import feedparser

from jobscraper.models import Job, RawJob, RemoteEligibility, WorkType, make_job_id
from jobscraper.parsers.names import geo_eligibility
from jobscraper.parsers.text import clean_str, html_to_text, parse_date, safe_http_url, truncate
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import register
from jobscraper.utils.errors import SchemaError
from jobscraper.utils.http import HttpClient
from jobscraper.utils.pii import scrub_pii

DEFAULT_FEED = "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"
SOURCE_URL = "https://weworkremotely.com/"
MAX_TEXT_CHARS = 20_000
_KEEP = ("title", "link", "id", "published", "summary", "region", "category", "type")


def split_title(value: str) -> tuple[str | None, str]:
    """'Acme: Support Agent' -> ('Acme', 'Support Agent'). No colon means no company."""
    company, sep, title = value.partition(": ")
    if sep and company.strip() and title.strip():
        return company.strip(), title.strip()
    return None, value.strip()


@register
class WeWorkRemotelyAdapter(Adapter):
    id = "weworkremotely"
    display_name = "We Work Remotely"
    allowed_hosts = frozenset({"weworkremotely.com"})

    def fetch(self, client: HttpClient) -> list[RawJob]:
        raws: list[RawJob] = []
        for feed_url in self.config.feeds or [DEFAULT_FEED]:
            body = client.get(feed_url).content
            parsed: Any = feedparser.parse(body)
            entries = list(parsed.entries)
            if not entries and parsed.bozo:
                raise SchemaError("feed could not be parsed")
            for entry in entries:
                raws.append(
                    RawJob(
                        source=self.id,
                        data={k: entry.get(k) for k in _KEEP if entry.get(k) is not None},
                    )
                )
        return raws

    def to_job(self, raw: RawJob) -> Job | None:
        data = raw.data
        full_title = clean_str(data.get("title"))
        job_url = safe_http_url(data.get("link"))
        if full_title is None or job_url is None:
            return None
        company, title = split_title(full_title)
        if company is None:
            return None  # company is required (doc 05)
        source_job_id = clean_str(data.get("id")) or job_url
        region = clean_str(data.get("region"))
        text = scrub_pii(html_to_text(clean_str(data.get("summary")) or ""))[:MAX_TEXT_CHARS]
        eligibility = geo_eligibility(region)
        return Job(
            job_id=make_job_id(self.id, source_job_id),
            title=title,
            company=company,
            job_url=job_url,
            source=self.id,
            source_url=SOURCE_URL,
            source_job_id=source_job_id,
            location=region,
            work_type=WorkType.REMOTE,
            remote_eligibility=RemoteEligibility(eligibility),
            posting_country_restrictions=[region] if eligibility == "restricted" and region else [],
            description_excerpt=truncate(text, self.config.excerpt_max_chars),
            date_posted=parse_date(data.get("published")),
            first_seen=self.now,
            scoring_text=text,
        )
