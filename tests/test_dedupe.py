from __future__ import annotations

from datetime import date

import pytest

from jobscraper.models import StoredJob
from jobscraper.parsers.names import normalize_company, normalize_title
from jobscraper.utils.dedupe import Deduper, format_salary
from jobscraper.utils.urls import canonical_url
from tests.helpers import T0, later, make_job


def run(jobs, stored=None, now=T0):
    d = Deduper(stored or [], now)
    flags = [d.add(j) for j in jobs]
    return flags, d.finish()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Customer Support Specialist - Remote", "customer support specialist"),
        ("Senior Customer Support Agent (Nairobi)", "customer support agent"),
        ("Support Agent | Worldwide", "support agent"),
        ("Customer Support, Tier 2", "customer support tier 2"),
        ("Sr. Help Desk Analyst / Hybrid Nairobi", "help desk analyst"),
    ],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Acme Cloud, Inc.", "acme cloud"), ("Safaricom PLC", "safaricom"), ("Wave Ltd.", "wave")],
)
def test_normalize_company(raw, expected):
    assert normalize_company(raw) == expected


def test_canonical_url_ignores_tracking_fragment_slash_case():
    a = canonical_url("http://Jobs.Example.com/x/?utm_source=a&b=2&a=1#frag")
    b = canonical_url("https://jobs.example.com/x?a=1&b=2&gclid=zzz")
    assert a == b


def test_same_url_with_tracking_is_duplicate():
    a = make_job(job_id="a", source_job_id="1", job_url="https://x.com/j/1")
    b = make_job(job_id="b", source="jobicy", source_job_id="9", job_url="https://x.com/j/1?utm_source=z",
                 title="Totally Different", company="Other")
    flags, out = run([a, b])
    assert flags == [True, False] and len(out.new_jobs) == 1 and out.duplicates == 1


def test_same_source_job_id_is_duplicate():
    a = make_job(job_id="a", job_url="https://x.com/1")
    b = make_job(job_id="b", job_url="https://x.com/2", title="Other Title", company="Other Co")
    flags, _ = run([a, b])
    assert flags == [True, False]


def test_cross_source_fingerprint_merges_and_prefers_employer_domain():
    himalayas = make_job(job_id="h", source_job_id="h-1")
    wwr = make_job(
        job_id="w", source="weworkremotely", source_job_id="w-1",
        job_url="https://acme.com/careers/support-agent", company="Acme Cloud",
        salary_min=800, salary_max=1200, salary_currency="USD",
        application_deadline=date(2026, 11, 1),
    )
    flags, out = run([himalayas, wwr])
    assert flags == [True, False]
    (job,) = out.new_jobs
    assert job.job_id == "h"  # the first one keeps its identity
    assert job.job_url == "https://acme.com/careers/support-agent"
    assert set(job.all_urls) == {"https://himalayas.app/jobs/acme-1", "https://acme.com/careers/support-agent"}
    assert job.salary_min == 800 and job.application_deadline == date(2026, 11, 1)
    assert job.first_seen == T0
    assert out.duplicates_by_source["weworkremotely"] == 1


def test_different_location_scope_is_not_a_duplicate():
    remote = make_job(job_id="r")
    nairobi = make_job(job_id="n", source="x", source_job_id="n-1", job_url="https://x.com/n",
                       location="Nairobi, Kenya", work_type="unknown", description_excerpt="")
    flags, _ = run([remote, nairobi])
    assert flags == [True, True]


def test_stored_job_seen_again_only_updates_system_columns():
    stored = StoredJob(job_id="s1", fingerprint=make_job().fingerprint, title="Customer Support Agent",
                       company="Acme Cloud Inc.", job_url="https://himalayas.app/jobs/acme-1",
                       all_urls=["https://himalayas.app/jobs/acme-1"], source="himalayas",
                       source_job_id="h-1", last_seen=later(-2), first_seen=later(-10))
    cand = make_job(job_id="new-id", source="jobicy", source_job_id="j-1", job_url="https://acme.com/c/1")
    flags, out = run([cand], [stored])
    assert flags == [False] and out.new_jobs == []
    (update,) = out.updates
    assert update.job_id == "s1"
    assert set(update.fields) <= {"last_seen", "is_active", "all_urls", "job_url"}
    assert update.fields["job_url"] == "https://acme.com/c/1"
    assert "https://acme.com/c/1" in update.fields["all_urls"]


def test_repost_after_gap_is_new_and_flagged():
    stored = StoredJob(job_id="old", fingerprint=make_job().fingerprint, title="Customer Support Agent",
                       company="Acme Cloud Inc.", job_url="https://himalayas.app/jobs/old",
                       all_urls=["https://himalayas.app/jobs/old"], source="himalayas",
                       source_job_id="h-old", last_seen=later(-45), first_seen=later(-60))
    cand = make_job(job_id="fresh", source_job_id="h-new", job_url="https://himalayas.app/jobs/new")
    flags, out = run([cand], [stored])
    assert flags == [True] and out.new_jobs[0].is_repost is True


def test_near_duplicate_needs_similar_title_and_description():
    a = make_job(job_id="a", job_url="https://x.com/a", source_job_id="a")
    b = make_job(job_id="b", source="jobicy", job_url="https://y.com/b", source_job_id="b",
                 title="Customer Support Agent II",
                 description_excerpt="Help customers with Zendesk and ticketing every day!")
    c = make_job(job_id="c", source="jobicy", job_url="https://y.com/c", source_job_id="c",
                 title="Customer Support Agent III",
                 description_excerpt="Completely unrelated text about warehouse forklift operation.")
    flags, _ = run([a, b, c])
    assert flags == [True, False, True]


def test_rerun_with_same_jobs_adds_nothing():
    first = make_job()
    _, out1 = run([first])
    stored = [StoredJob(job_id=j.job_id, fingerprint=j.fingerprint, title=j.title, company=j.company,
                        job_url=j.job_url, all_urls=j.all_urls, source=j.source,
                        source_job_id=j.source_job_id, description_excerpt=j.description_excerpt,
                        first_seen=j.first_seen, last_seen=j.last_seen) for j in out1.new_jobs]
    flags, out2 = run([make_job()], stored, now=later(0.5))
    assert flags == [False] and out2.new_jobs == []


def test_format_salary():
    assert format_salary(make_job()) == ""
    job = make_job(salary_min=800, salary_max=1200, salary_currency="USD", salary_period="month")
    assert format_salary(job) == "USD 800-1,200/month"
