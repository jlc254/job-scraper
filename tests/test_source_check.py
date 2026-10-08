from typing import Any
from __future__ import annotations

import json

import httpx
import respx

import jobscraper.scrapers  # noqa: F401
from jobscraper.source_check import (
    check_source,
    format_check,
    sanitize_fixture,
    save_fixture,
    select_sources,
)
from tests.conftest import load_fixture

HIMALAYAS = "https://himalayas.app/jobs/api"


def factory(make_client):
    return lambda adapter: make_client(set(adapter.allowed_hosts))


@respx.mock
def test_healthy_source_reports_counts_and_samples(make_client: Any, source_config: Any, now: Any) -> None:
    route = respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    result = check_source("himalayas", source_config(max_pages=5), now, factory(make_client))
    assert result.ok and (result.found, result.mapped) == (4, 3)
    assert (
        route.call_count == 1
    )  # one page only, whatever max_pages says: this is a low-volume check
    assert result.robots == "n/a (API source)" and len(result.captured) == 1
    text = format_check([result])
    assert (
        text.startswith("OK   himalayas")
        and "e.g. Customer Support Specialist (Acme Cloud)" in text
    )


@respx.mock
def test_unreachable_source_fails_with_a_reason(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(HIMALAYAS).respond(403)
    result = check_source("himalayas", source_config(), now, factory(make_client))
    assert (
        not result.ok
        and "BlockedError" in result.detail
        and format_check([result]).startswith("FAIL")
    )


@respx.mock
def test_empty_and_unparseable_responses_are_failures(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(HIMALAYAS).mock(
        side_effect=[
            httpx.Response(200, json={"jobs": []}),
            httpx.Response(200, json={"jobs": [{"title": "only a title"}] * 5}),
        ]
    )
    empty = check_source("himalayas", source_config(), now, factory(make_client))
    assert not empty.ok and "empty response" in empty.detail

    broken = check_source("himalayas", source_config(), now, factory(make_client))
    assert not broken.ok and "format may have changed" in broken.detail


@respx.mock
def test_sources_that_must_not_be_contacted_are_refused(make_client: Any, source_config: Any, now: Any) -> None:
    route = respx.get(HIMALAYAS).respond(200, json={"jobs": []})
    for status in ("alerts-only", "retired", "blocked"):
        result = check_source("himalayas", source_config(status=status), now, factory(make_client))
        assert not result.ok and "not contacted" in result.detail
    assert route.call_count == 0
    assert "no adapter" in check_source("nope", source_config(), now, factory(make_client)).detail


@respx.mock
def test_pending_sources_can_be_checked_before_they_are_enabled(make_client: Any, source_config: Any, now: Any) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    result = check_source(
        "himalayas", source_config(status="pending", enabled=False), now, factory(make_client)
    )
    assert result.ok


def test_select_sources(source_config: Any) -> None:
    sources = {
        "a": source_config(),
        "b": source_config(enabled=False),
        "c": source_config(status="pending"),
    }
    assert select_sources(sources, None) == ["a"]
    assert select_sources(sources, ["c", "b"]) == ["c", "b"]


# ---- fixtures: personal data out, a few records in -----------------------------------------------


def test_json_fixture_is_scrubbed_and_trimmed() -> None:
    body = json.dumps(
        {
            "jobs": [
                {"title": f"Job {i}", "contact": "hr@acme.com", "tel": "+254 712 345 678"}
                for i in range(12)
            ],
            "meta": {"total": 12},
        }
    ).encode()
    ext, text = sanitize_fixture(body)
    data = json.loads(text)
    assert ext == "json" and len(data["jobs"]) == 5 and data["meta"] == {"total": 12}
    assert "hr@acme.com" not in text and "712 345" not in text


def test_feed_fixture_keeps_header_and_five_items() -> None:
    items = "".join(
        f"<item><title>Co: Job {i}</title><description>mail me@x.org</description></item>"
        for i in range(9)
    )
    ext, text = sanitize_fixture(f"<rss><channel><title>T</title>{items}</channel></rss>".encode())
    assert (
        ext == "xml"
        and text.count("<item>") == 5
        and "<title>T</title>" in text
        and text.endswith("</channel></rss>")
    )
    assert "me@x.org" not in text


@respx.mock
def test_save_fixture_writes_a_file_named_after_the_source(
    make_client, source_config, now, tmp_path
) -> None:
    respx.get(HIMALAYAS).respond(200, json=load_fixture("himalayas.json"))
    result = check_source("himalayas", source_config(), now, factory(make_client))
    path = save_fixture(result, tmp_path / "captured")
    assert path is not None and path.name == "himalayas.json"
    assert "jane.doe@example.com" not in path.read_text(encoding="utf-8")
    assert (
        save_fixture(check_source("nope", source_config(), now, factory(make_client)), tmp_path)
        is None
    )