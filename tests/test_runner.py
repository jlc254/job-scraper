from __future__ import annotations

import csv
from typing import Any

import httpx
import pytest
import respx

import jobscraper.scrapers  # noqa: F401
from jobscraper.models import SourceStatus
from jobscraper.output import format_report, write_csv
from jobscraper.runner import run_sources
from tests.conftest import load_fixture

HIMALAYAS = "https://himalayas.app/jobs/api"
GH = "https://boards-api.greenhouse.io/v1/boards/exampleco/jobs"


@pytest.fixture
def factory(make_client):
    return lambda adapter: make_client(set(adapter.allowed_hosts))


def by_source(outcome):
    return {r.source: r for r in outcome.results}


def test_gate_skips_unverified_and_disabled_without_contacting(
    source_config: Any, now: Any, factory: Any
) -> None:
    sources = {
        "himalayas": source_config(status="pending"),
        "greenhouse": source_config(enabled=False),
    }
    with respx.mock(assert_all_called=False) as router:
        any_call = router.route().respond(200)
        outcome = run_sources(sources, now=now, client_factory=factory, environ={})
    assert any_call.call_count == 0
    results = by_source(outcome)
    assert results["himalayas"].status is SourceStatus.SKIPPED
    assert "not 'verified'" in (results["himalayas"].error or "")
    assert results["greenhouse"].error == "disabled"


@respx.mock
def test_full_run_isolates_failures(source_config: Any, now: Any, factory: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    respx.get(GH).mock(side_effect=httpx.ReadTimeout("slow"))
    sources = {
        "himalayas": source_config(),
        "greenhouse": source_config(boards=["exampleco"]),
    }
    outcome = run_sources(sources, now=now, client_factory=factory, environ={})
    results = by_source(outcome)
    h = results["himalayas"]
    assert (h.found, h.kept, h.dropped) == (4, 3, 1)
    assert h.status is SourceStatus.OK  # 1 of 4 dropped is 25%, under the 30% threshold
    assert results["greenhouse"].status is SourceStatus.FAILED
    assert {j.title for j in outcome.jobs} == {
        "Customer Support Specialist",
        "Customer Care Agent",
        "Backend Engineer",
    }


@respx.mock
def test_blocked_and_rate_limited_statuses(source_config: Any, now: Any, factory: Any) -> None:
    respx.get(HIMALAYAS).respond(403)
    respx.get(GH).respond(429)
    sources = {"himalayas": source_config(), "greenhouse": source_config(boards=["exampleco"])}
    results = by_source(run_sources(sources, now=now, client_factory=factory, environ={}))
    assert results["himalayas"].status is SourceStatus.BLOCKED
    assert results["greenhouse"].status is SourceStatus.RATE_LIMITED


@respx.mock
def test_mostly_unparseable_source_is_degraded(source_config: Any, now: Any, factory: Any) -> None:
    bad = {"jobs": [{"title": "only title"}] * 4 + [load_fixture("himalayas.json")["jobs"][0]]}
    respx.get(HIMALAYAS).respond(200, json=bad)
    outcome = run_sources(
        {"himalayas": source_config()}, now=now, client_factory=factory, environ={}
    )
    assert by_source(outcome)["himalayas"].status is SourceStatus.DEGRADED


@respx.mock
def test_partial_status_when_one_board_fails(source_config: Any, now: Any, factory: Any) -> None:
    respx.get(GH).respond(
        200,
        json={
            "jobs": [
                {
                    "id": 1,
                    "title": "T1",
                    "location": {"name": "L1"},
                    "absolute_url": "https://ex.com/1",
                    "content": "C1",
                },
                {
                    "id": 2,
                    "title": "T2",
                    "location": {"name": "L2"},
                    "absolute_url": "https://ex.com/2",
                    "content": "C2",
                },
                {
                    "id": 3,
                    "title": "T3",
                    "location": {"name": "L3"},
                    "absolute_url": "https://ex.com/3",
                    "content": "C3",
                },
                {
                    "id": 4,
                    "title": "T4",
                    "location": {"name": "L4"},
                    "absolute_url": "https://ex.com/4",
                    "content": "C4",
                },
            ]
        },
    )
    respx.get("https://boards-api.greenhouse.io/v1/boards/gone/jobs").respond(404)
    sources = {"greenhouse": source_config(boards=["exampleco", "gone"])}
    results = by_source(run_sources(sources, now=now, client_factory=factory, environ={}))
    assert results["greenhouse"].status is SourceStatus.PARTIAL


@respx.mock
def test_rerun_is_deterministic(source_config: Any, now: Any, factory: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    sources = {"himalayas": source_config()}
    ids = [
        sorted(
            j.job_id for j in run_sources(sources, now=now, client_factory=factory, environ={}).jobs
        )
        for _ in range(2)
    ]
    assert ids[0] == ids[1]


@respx.mock
def test_csv_and_report(source_config: Any, now: Any, factory: Any, tmp_path: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    outcome = run_sources(
        {"himalayas": source_config()}, now=now, client_factory=factory, environ={}
    )
    path = tmp_path / "out.csv"
    write_csv(outcome.jobs, path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 3 and rows[0]["source"] == "himalayas"
    report = format_report(outcome.results, now, 161)
    assert "RUN 2026-10-01 03:00 UTC  (2m 41s)" in report
    assert "himalayas: ok, 4 found, 3 kept" in report
