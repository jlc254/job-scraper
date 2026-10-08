from typing import Any
from __future__ import annotations

import httpx
import pytest
import respx

from jobscraper.utils.errors import (
    BlockedError,
    FetchError,
    NotFoundError,
    RateLimitedError,
    ResponseTooLargeError,
    RobotsDisallowedError,
    UnsafeUrlError,
)
from jobscraper.utils.http import redact_url

HOST = "api.example.com"
URL = f"https://{HOST}/jobs"


@respx.mock
def test_success_returns_json(make_client: Any) -> None:
    respx.get(URL).respond(200, json={"jobs": []})
    assert make_client({HOST}).get(URL).json() == {"jobs": []}


@respx.mock
def test_retries_5xx_with_backoff_then_succeeds(make_client: Any, sleeper: Any) -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(500), httpx.Response(200, json={})]
    )
    make_client({HOST}).get(URL)
    assert route.call_count == 3
    assert 2.0 <= sleeper.calls[0] < 3.0
    assert 4.0 <= sleeper.calls[1] < 5.0


@respx.mock
def test_gives_up_after_three_attempts(make_client: Any) -> None:
    route = respx.get(URL).respond(500)
    with pytest.raises(FetchError):
        make_client({HOST}).get(URL)
    assert route.call_count == 3


@respx.mock
def test_timeout_is_retried(make_client: Any) -> None:
    route = respx.get(URL).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(FetchError):
        make_client({HOST}).get(URL)
    assert route.call_count == 3


@pytest.mark.parametrize(
    ("status", "exc"),
    [(401, BlockedError), (403, BlockedError), (404, NotFoundError), (410, NotFoundError)],
)
@respx.mock
def test_no_retry_statuses(make_client: Any, status: Any, exc: Any) -> None:
    route = respx.get(URL).respond(status)
    with pytest.raises(exc):
        make_client({HOST}).get(URL)
    assert route.call_count == 1


@respx.mock
def test_429_not_retried_and_retry_after_capped(make_client: Any) -> None:
    route = respx.get(URL).respond(429, headers={"Retry-After": "9999"})
    with pytest.raises(RateLimitedError) as info:
        make_client({HOST}).get(URL)
    assert route.call_count == 1
    assert info.value.retry_after == 300.0


@respx.mock
def test_non_https_rejected(make_client: Any) -> None:
    with pytest.raises(UnsafeUrlError):
        make_client({HOST}).get(f"http://{HOST}/jobs")


def test_host_outside_allowlist_rejected(make_client: Any) -> None:
    with pytest.raises(UnsafeUrlError):
        make_client({HOST}).get("https://evil.example.org/x")


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "169.254.169.254", "192.168.1.1", "::1"])
def test_private_addresses_rejected(make_client: Any, ip: Any) -> None:
    client = make_client({HOST}, resolver=lambda host: [ip])
    with pytest.raises(UnsafeUrlError):
        client.get(URL)


@respx.mock
def test_redirect_to_unlisted_host_rejected(make_client: Any) -> None:
    respx.get(URL).respond(302, headers={"Location": "https://evil.example.org/x"})
    with pytest.raises(UnsafeUrlError):
        make_client({HOST}).get(URL)


@respx.mock
def test_redirect_within_allowlist_followed(make_client: Any) -> None:
    respx.get(URL).respond(302, headers={"Location": f"https://{HOST}/v2/jobs"})
    respx.get(f"https://{HOST}/v2/jobs").respond(200, json={"ok": True})
    assert make_client({HOST}).get(URL).json() == {"ok": True}


@respx.mock
def test_redirect_loop_stops_after_limit(make_client: Any) -> None:
    respx.get(URL).respond(302, headers={"Location": URL})
    with pytest.raises(FetchError):
        make_client({HOST}).get(URL)


@respx.mock
def test_oversize_response_rejected(make_client: Any) -> None:
    respx.get(URL).respond(200, content=b"x" * 2000)
    client = make_client({HOST})
    client._max_bytes = 1000  # noqa: SLF001
    with pytest.raises(ResponseTooLargeError):
        client.get(URL)


@respx.mock
def test_robots_disallow_blocks_fetch(make_client: Any) -> None:
    respx.get(f"https://{HOST}/robots.txt").respond(200, text="User-agent: *\nDisallow: /jobs\n")
    page = respx.get(URL).respond(200, text="hi")
    with pytest.raises(RobotsDisallowedError):
        make_client({HOST}).get(URL, respect_robots=True)
    assert page.call_count == 0


@respx.mock
def test_robots_allowed_path_fetches(make_client: Any) -> None:
    respx.get(f"https://{HOST}/robots.txt").respond(200, text="User-agent: *\nDisallow: /private\n")
    respx.get(URL).respond(200, text="hi")
    assert make_client({HOST}).get(URL, respect_robots=True).text == "hi"


@respx.mock
def test_unreadable_robots_means_disallowed(make_client: Any) -> None:
    respx.get(f"https://{HOST}/robots.txt").respond(404)
    respx.get(URL).respond(200, text="hi")
    with pytest.raises(RobotsDisallowedError):
        make_client({HOST}).get(URL, respect_robots=True)


def test_redact_url_drops_query() -> None:
    assert redact_url("https://a.com/p?app_key=SECRET#x") == "https://a.com/p"