from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from jobscraper.models import RawJob, RemoteEligibility, WorkType
from jobscraper.scrapers.greenhouse import GreenhouseAdapter
from jobscraper.scrapers.himalayas import HimalayasAdapter
from jobscraper.utils.errors import BlockedError, SchemaError
from tests.conftest import load_fixture

HIMALAYAS = "https://himalayas.app/jobs/api"
GH = "https://boards-api.greenhouse.io/v1/boards/exampleco/jobs"


def map_all(adapter, raws):
    return [j for j in (adapter.to_job(r) for r in raws) if j is not None]


@respx.mock
def test_himalayas_fetch_and_map(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    adapter = HimalayasAdapter(source_config(page_size=20), now)
    raws = adapter.fetch(make_client(set(adapter.allowed_hosts)))
    assert len(raws) == 4
    jobs = map_all(adapter, raws)
    assert len(jobs) == 3  # the record with no title is dropped

    first = jobs[0]
    assert first.title == "Customer Support Specialist"
    assert first.work_type is WorkType.REMOTE
    assert first.remote_eligibility is RemoteEligibility.WORLDWIDE
    assert first.salary_min == 800 and first.salary_currency == "USD"
    assert "jane.doe@example.com" not in first.scoring_text
    assert "712" not in first.description_excerpt
    assert jobs[1].remote_eligibility is RemoteEligibility.RESTRICTED
    assert jobs[1].posting_country_restrictions == ["United States", "Canada"]


@respx.mock
def test_himalayas_paginates_until_short_page(
    make_client: Any, source_config: Any, now: Any
) -> None:
    page = {
        "jobs": [{"title": "t", "companyName": "c", "applicationLink": "https://himalayas.app/x"}]
        * 2
    }
    route = respx.get(HIMALAYAS).mock(
        side_effect=[
            httpx.Response(200, json=page),
            httpx.Response(200, json={"jobs": []}),
        ]
    )
    adapter = HimalayasAdapter(source_config(page_size=2, max_pages=5), now)
    assert len(adapter.fetch(make_client({"himalayas.app"}))) == 2
    assert route.call_count == 2


@respx.mock
def test_himalayas_bad_shape_raises_schema_error(
    make_client: Any, source_config: Any, now: Any
) -> None:
    respx.get(HIMALAYAS).respond(200, json={"unexpected": True})
    adapter = HimalayasAdapter(source_config(), now)
    with pytest.raises(SchemaError):
        adapter.fetch(make_client({"himalayas.app"}))


@respx.mock
def test_himalayas_malformed_json_raises_schema_error(
    make_client: Any, source_config: Any, now: Any
) -> None:
    respx.get(HIMALAYAS).respond(200, text="<html>not json")
    adapter = HimalayasAdapter(source_config(), now)
    with pytest.raises(SchemaError):
        adapter.fetch(make_client({"himalayas.app"}))


@respx.mock
def test_greenhouse_fetch_and_map(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(GH).respond(200, json=load_fixture("greenhouse.json"))
    cfg = source_config(boards=[{"token": "exampleco", "name": "Example Co"}])
    adapter = GreenhouseAdapter(cfg, now)
    raws = adapter.fetch(make_client(set(adapter.allowed_hosts)))
    assert len(raws) == 3
    jobs = map_all(adapter, raws)
    assert len(jobs) == 2  # javascript: URL dropped
    first = jobs[0]
    assert first.company == "Example Co"
    assert first.work_type is WorkType.REMOTE
    assert first.source_job_id == "exampleco:4001"
    assert "<p>" not in first.scoring_text and "ticketing" in first.scoring_text
    assert "hr@exampleco.com" not in first.scoring_text


@respx.mock
def test_greenhouse_one_bad_board_is_partial(
    make_client: Any, source_config: Any, now: Any
) -> None:
    respx.get(GH).respond(200, json=load_fixture("greenhouse.json"))
    respx.get("https://boards-api.greenhouse.io/v1/boards/gone/jobs").respond(404)
    adapter = GreenhouseAdapter(source_config(boards=["exampleco", "gone"]), now)
    raws = adapter.fetch(make_client({"boards-api.greenhouse.io"}))
    assert len(raws) == 3
    assert adapter.partial_errors == ["gone: NotFoundError"]


@respx.mock
def test_greenhouse_blocked_stops_source(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(GH).respond(403)
    adapter = GreenhouseAdapter(source_config(boards=["exampleco"]), now)
    with pytest.raises(BlockedError):
        adapter.fetch(make_client({"boards-api.greenhouse.io"}))


def test_greenhouse_invalid_token_ignored(source_config: Any, now: Any) -> None:
    adapter = GreenhouseAdapter(source_config(boards=["../etc/passwd"]), now)
    with pytest.raises(SchemaError):
        adapter.fetch(None)  # type: ignore[arg-type]


def test_job_id_is_stable(source_config: Any, now: Any) -> None:
    adapter = HimalayasAdapter(source_config(), now)
    raw = RawJob(source="himalayas", data=load_fixture("himalayas.json")["jobs"][0])
    a, b = adapter.to_job(raw), adapter.to_job(raw)
    assert a is not None and b is not None and a.job_id == b.job_id and len(a.job_id) == 12


def test_excerpt_zero_stores_nothing_but_keeps_scoring_text(source_config: Any, now: Any) -> None:
    adapter = HimalayasAdapter(source_config(excerpt_max_chars=0), now)
    job = adapter.to_job(RawJob(source="himalayas", data=load_fixture("himalayas.json")["jobs"][0]))
    assert job is not None and job.description_excerpt == "" and job.scoring_text
