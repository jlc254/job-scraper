"""We Work Remotely RSS adapter, shared by two source ids.

`weworkremotely` polls the feeds in `sources.yaml` (the support category by default).
`weworkremotely_categories` is the same parser under a second id so a profile can be given
every category feed without widening the support profile's fetch set.

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
from jobscraper.utils.errors import FetchError
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
        feed_urls = self.config.feeds or [DEFAULT_FEED]
        for feed_url in feed_urls:
            try:
                body = client.get(feed_url).content
            except FetchError as exc:
                # One dead feed must not fail the other category feeds: record it and keep
                # the rest (the runner reports the source as `partial`). str(exc) already
                # names the feed URL.
                self.partial_errors.append(str(exc))
                continue
            parsed: Any = feedparser.parse(body)
            entries = list(parsed.entries)
            if not entries and parsed.bozo:
                self.partial_errors.append(f"{feed_url}: feed could not be parsed")
                continue
            for entry in entries:
                raws.append(
                    RawJob(
                        source=self.id,
                        data={k: entry.get(k) for k in _KEEP if entry.get(k) is not None},
                    )
                )
        if not raws and self.partial_errors:
            raise FetchError(f"every feed failed: {'; '.join(self.partial_errors)}")
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


@register
class WeWorkRemotelyCategoriesAdapter(WeWorkRemotelyAdapter):
    """The same feed parser under a second id, for profiles that want every category.

    Feed URLs live in `sources.yaml` (`feeds:`). A separate id lets `profiles.yaml` give the
    wider set to one profile while the support profile keeps the single support feed.
    Adverts that appear in two feeds share a guid, so they merge within a run.
    """

    id = "weworkremotely_categories"
    display_name = "We Work Remotely (all categories)"
