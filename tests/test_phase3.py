from __future__ import annotations

from typing import Any

import pytest
import respx

import jobscraper.scrapers  # noqa: F401
from jobscraper.models import RemoteEligibility, WorkType
from jobscraper.parsers.normalize import normalize_job
from jobscraper.pipeline import dedupe_jobs, persist
from jobscraper.runner import run_sources
from jobscraper.scrapers.jobicy import JobicyAdapter
from jobscraper.scrapers.registry import get_adapter_class
from jobscraper.scrapers.weworkremotely import (
    DEFAULT_FEED,
    WeWorkRemotelyAdapter,
    WeWorkRemotelyCategoriesAdapter,
    split_title,
)
from jobscraper.storage.sqlite import SQLiteStorage
from jobscraper.utils.errors import FetchError
from tests.conftest import FIXTURES, load_fixture
from tests.helpers import make_job

JOBICY = "https://jobicy.com/api/v2/remote-jobs"
HIMALAYAS = "https://himalayas.app/jobs/api"
SITE_WIDE_FEED = "https://weworkremotely.com/remote-jobs.rss"


def test_normalize_job_reads_location_text() -> None:
    job = make_job(location="Remote - Africa", work_type="unknown", remote_eligibility="unclear")
    assert job.work_type is WorkType.REMOTE and job.remote_eligibility is RemoteEligibility.AFRICA
    nairobi = make_job(location="Nairobi, Kenya", work_type="unknown")
    assert nairobi.country == "KE" and nairobi.work_type is WorkType.UNKNOWN


def test_normalize_job_is_idempotent() -> None:
    once = make_job()
    assert normalize_job(once) == once


def test_company_domain_only_for_employer_sites() -> None:
    assert make_job().company_domain is None
    assert make_job(job_url="https://www.acme.com/jobs/1").company_domain == "acme.com"


@respx.mock
def test_jobicy_fetch_and_map(make_client: Any, source_config: Any, now: Any) -> None:
    route = respx.get(JOBICY).respond(200, json=load_fixture("jobicy.json"))
    adapter = JobicyAdapter(source_config(), now)
    raws = adapter.fetch(make_client({"jobicy.com"}))
    assert route.calls.last.request.url.params["count"] == "50"
    jobs = [j for j in (adapter.to_job(r) for r in raws) if j]
    assert len(raws) == 3 and len(jobs) == 2
    first, second = jobs
    assert first.remote_eligibility is RemoteEligibility.WORLDWIDE
    assert first.salary_min == 20000 and first.salary_period == "year"
    assert "careers@acme.example" not in first.scoring_text
    assert second.remote_eligibility is RemoteEligibility.RESTRICTED
    assert second.posting_country_restrictions == ["USA"]


def test_split_title() -> None:
    assert split_title("Acme: Support Agent") == ("Acme", "Support Agent")
    assert split_title("Acme: Support: Tier 2") == ("Acme", "Support: Tier 2")
    assert split_title("No company here") == (None, "No company here")


@respx.mock
def test_weworkremotely_fetch_and_map(make_client: Any, source_config: Any, now: Any) -> None:
    xml = (FIXTURES / "weworkremotely.xml").read_text(encoding="utf-8")
    respx.get(DEFAULT_FEED).respond(200, text=xml)
    adapter = WeWorkRemotelyAdapter(source_config(), now)
    raws = adapter.fetch(make_client({"weworkremotely.com"}))
    jobs = [j for j in (adapter.to_job(r) for r in raws) if j]
    assert len(raws) == 3 and len(jobs) == 2
    assert jobs[0].company == "Acme Cloud" and jobs[0].title == "Customer Support Agent"
    assert jobs[0].remote_eligibility is RemoteEligibility.WORLDWIDE
    assert str(jobs[0].date_posted) == "2026-09-28"
    assert jobs[1].remote_eligibility is RemoteEligibility.RESTRICTED


@respx.mock
def test_weworkremotely_categories_reads_every_configured_feed(
    make_client: Any, source_config: Any, now: Any
) -> None:
    """The second id is the same parser over a wider feed list; one request per feed."""
    xml = (FIXTURES / "weworkremotely.xml").read_text(encoding="utf-8")
    respx.get(DEFAULT_FEED).respond(200, text=xml)
    respx.get(SITE_WIDE_FEED).respond(200, text=xml)
    config = source_config(feeds=[DEFAULT_FEED, SITE_WIDE_FEED])
    assert get_adapter_class("weworkremotely_categories") is WeWorkRemotelyCategoriesAdapter
    adapter = WeWorkRemotelyCategoriesAdapter(config, now)
    raws = adapter.fetch(make_client({"weworkremotely.com"}))
    assert len(raws) == 6  # 3 items per feed, including the company-less one
    assert {raw.source for raw in raws} == {"weworkremotely_categories"}
    jobs = [j for j in (adapter.to_job(r) for r in raws) if j]
    assert len(jobs) == 4


@respx.mock
def test_weworkremotely_one_dead_feed_is_partial_not_failed(
    make_client: Any, source_config: Any, now: Any
) -> None:
    """One dead feed is a partial error; the live feeds still deliver their jobs."""
    xml = (FIXTURES / "weworkremotely.xml").read_text(encoding="utf-8")
    respx.get(DEFAULT_FEED).respond(200, text=xml)
    respx.get(SITE_WIDE_FEED).respond(500)
    adapter = WeWorkRemotelyCategoriesAdapter(
        source_config(feeds=[SITE_WIDE_FEED, DEFAULT_FEED]), now
    )
    raws = adapter.fetch(make_client({"weworkremotely.com"}))
    assert len(raws) == 3
    assert adapter.partial_errors == [f"HTTP 500 from {SITE_WIDE_FEED}"]


@respx.mock
def test_weworkremotely_every_feed_failed_is_a_failed_source(
    make_client: Any, source_config: Any, now: Any
) -> None:
    respx.get(DEFAULT_FEED).respond(500)
    adapter = WeWorkRemotelyAdapter(source_config(), now)
    with pytest.raises(FetchError):
        adapter.fetch(make_client({"weworkremotely.com"}))


@respx.mock
def test_three_sources_merge_across_boards_and_second_run_adds_nothing(
    source_config, now, make_client, tmp_path
) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    respx.get(JOBICY).respond(200, json=load_fixture("jobicy.json"))
    respx.get(DEFAULT_FEED).respond(
        200, text=(FIXTURES / "weworkremotely.xml").read_text(encoding="utf-8")
    )
    sources = {
        "himalayas": source_config(),
        "jobicy": source_config(),
        "weworkremotely": source_config(),
    }
    factory = lambda adapter: make_client(set(adapter.allowed_hosts))  # noqa: E731
    storage = SQLiteStorage()

    outcome = run_sources(sources, now=now, client_factory=factory, environ={})
    deduped = dedupe_jobs(outcome.jobs, storage, now, outcome.results)
    persist(storage, deduped, tmp_path)
    by = {r.source: r for r in outcome.results}
    assert (by["himalayas"].new, by["jobicy"].new, by["weworkremotely"].new) == (3, 2, 1)
    assert by["weworkremotely"].duplicates == 1  # Acme "Customer Support Agent" is also on Jobicy
    assert len(storage.load_index()) == 6

    outcome2 = run_sources(sources, now=now, client_factory=factory, environ={})
    deduped2 = dedupe_jobs(outcome2.jobs, storage, now, outcome2.results)
    persist(storage, deduped2, tmp_path)
    assert sum(r.new or 0 for r in outcome2.results) == 0
    assert len(storage.load_index()) == 6
