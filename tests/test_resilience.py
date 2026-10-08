from typing import Any
"""Resilience suite (doc 07): break one source on purpose and check the others still run."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import jobscraper.scrapers  # noqa: F401
from jobscraper.models import SourceStatus
from jobscraper.pipeline import persist, process_jobs
from jobscraper.runner import run_sources
from jobscraper.storage.sqlite import SQLiteStorage
from tests.conftest import load_fixture

HIMALAYAS = "https://himalayas.app/jobs/api"
JOBICY = "https://jobicy.com/api/v2/remote-jobs"
WWR = "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"
GH = "https://boards-api.greenhouse.io/v1/boards/exampleco/jobs"
S = SourceStatus

FAILURES = {
    "timeout": (lambda: httpx.ReadTimeout("slow"), S.FAILED),
    "server error": (lambda: httpx.Response(500), S.FAILED),
    "rate limited": (lambda: httpx.Response(429, headers={"Retry-After": "30"}), S.RATE_LIMITED),
    "blocked": (lambda: httpx.Response(403), S.BLOCKED),
    "malformed json": (lambda: httpx.Response(200, text="<html>maintenance</html>"), S.FAILED),
    "unexpected shape": (lambda: httpx.Response(200, json={"error": "gone"}), S.FAILED),
}


def factory(make_client):
    return lambda adapter: make_client(set(adapter.allowed_hosts))


@pytest.mark.parametrize("mode", sorted(FAILURES))
@respx.mock
def test_one_broken_source_never_stops_the_others(mode: Any, make_client: Any, source_config: Any, now: Any, tmp_path: Any) -> None:
    make_failure, expected = FAILURES[mode]
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    failure = make_failure()
    route = respx.get(JOBICY)
    route.mock(side_effect=failure) if isinstance(failure, Exception) else route.mock(return_value=failure)

    sources = {"jobicy": source_config(), "himalayas": source_config()}  # the broken one runs first
    outcome = run_sources(sources, now=now, client_factory=factory(make_client), environ={})
    by = {r.source: r for r in outcome.results}
    assert by["jobicy"].status is expected and by["jobicy"].error
    assert by["himalayas"].status is S.OK and by["himalayas"].kept == 3

    storage = SQLiteStorage()
    deduped = process_jobs(outcome.jobs, storage, now, outcome.results)
    persist(storage, deduped, tmp_path)
    assert len(storage.load_index()) == 3  # the healthy source's jobs were still saved


@respx.mock
def test_every_failure_mode_at_once(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    respx.get(JOBICY).respond(429)
    respx.get(WWR).respond(200, text='<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>')
    respx.get(GH).mock(side_effect=httpx.ReadTimeout("slow"))
    sources = {
        "himalayas": source_config(), "jobicy": source_config(), "weworkremotely": source_config(),
        "greenhouse": source_config(boards=["exampleco"]),
    }
    outcome = run_sources(sources, now=now, client_factory=factory(make_client), environ={})
    assert {r.source: r.status for r in outcome.results} == {
        "himalayas": S.OK, "jobicy": S.RATE_LIMITED, "weworkremotely": S.OK, "greenhouse": S.FAILED}
    by = {r.source: r for r in outcome.results}
    assert by["weworkremotely"].found == 0  # an empty feed is not an error by itself: health history judges it


@respx.mock
def test_unparseable_records_degrade_the_source_and_leave_a_clean_sample(make_client: Any, source_config: Any, now: Any, tmp_path: Any) -> None:
    good = load_fixture("himalayas.json")["jobs"][0]
    broken = [{"title": "no company", "contact": "hr@evil.example", "applicationLink": "https://x.com/a?token=secret"}] * 4
    respx.get(HIMALAYAS).respond(200, json={"jobs": [good, *broken]})
    outcome = run_sources({"himalayas": source_config()}, now=now, client_factory=factory(make_client),
                          environ={}, sample_dir=tmp_path / "samples")
    result = outcome.results[0]
    assert result.status is S.DEGRADED and result.error == "4 of 5 records failed to parse" and result.kept == 1
    (sample,) = list((tmp_path / "samples").glob("himalayas-*.json"))
    data = json.loads(sample.read_text(encoding="utf-8"))
    assert len(data["records"]) == 3 and "hr@evil.example" not in sample.read_text(encoding="utf-8")
    assert "token=secret" not in sample.read_text(encoding="utf-8")


@respx.mock
def test_healthy_runs_leave_no_samples(make_client: Any, source_config: Any, now: Any, tmp_path: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    run_sources({"himalayas": source_config()}, now=now, client_factory=factory(make_client),
                environ={}, sample_dir=tmp_path / "samples")
    assert not (tmp_path / "samples").exists()


@respx.mock
def test_a_missing_key_skips_the_source_without_failing_the_run(make_client: Any, source_config: Any, now: Any, monkeypatch: Any) -> None:
    from jobscraper.scrapers.jobicy import JobicyAdapter

    monkeypatch.setattr(JobicyAdapter, "requires_key", "JOBICY_KEY")
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    outcome = run_sources({"jobicy": source_config(), "himalayas": source_config()}, now=now,
                          client_factory=factory(make_client), environ={})
    by = {r.source: r for r in outcome.results}
    assert by["jobicy"].status is S.SKIPPED and "JOBICY_KEY" in by["jobicy"].error and by["himalayas"].status is S.OK