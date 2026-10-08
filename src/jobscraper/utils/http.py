"""Shared HTTP client: timeouts, retries, politeness, SSRF rules (docs 03, 07, 08)."""

from __future__ import annotations

import ipaddress
import json
import logging
import random
import socket
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from jobscraper.utils.errors import (
    BlockedError,
    FetchError,
    NotFoundError,
    RateLimitedError,
    ResponseTooLargeError,
    RobotsDisallowedError,
    SchemaError,
    UnsafeUrlError,
)
from jobscraper.utils.robots import RobotsChecker

log = logging.getLogger(__name__)

USER_AGENT = "JobScraper/0.1 (personal job-search tool)"
CONNECT_TIMEOUT_S = 5.0
READ_TIMEOUT_S = 20.0
MAX_ATTEMPTS = 3
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
RETRY_AFTER_CAP_S = 300.0
_RETRYABLE_STATUS = {408, 500, 502, 503, 504}

Resolver = Callable[[str], list[str]]


def default_resolver(host: str) -> list[str]:
    """Resolve a hostname to its IP addresses."""
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"cannot resolve host {host}") from exc
    return sorted({str(info[4][0]) for info in infos})


def redact_url(url: str) -> str:
    """URL without query string or fragment, safe to log."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"


@dataclass(frozen=True)
class FetchedResponse:
    """Minimal response object returned to adapters."""

    url: str
    status_code: int
    content: bytes
    headers: Mapping[str, str]

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        try:
            return json.loads(self.content)
        except (ValueError, UnicodeDecodeError) as exc:
            raise SchemaError("response was not valid JSON") from exc


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return min(max(float(value), 0.0), RETRY_AFTER_CAP_S)
    except ValueError:
        return None


class HttpClient:
    """GET-only client restricted to an allowlist of hosts."""

    def __init__(
        self,
        allowed_hosts: frozenset[str] | set[str],
        *,
        user_agent: str = USER_AGENT,
        min_interval_s: float = 1.0,
        resolver: Resolver = default_resolver,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
    ) -> None:
        self._allowed_hosts = {h.lower() for h in allowed_hosts}
        self._user_agent = user_agent
        self._min_interval_s = min_interval_s
        self._resolver = resolver
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()
        self._max_bytes = max_response_bytes
        self._last_request: dict[str, float] = {}
        self._robots: RobotsChecker | None = None
        # When a list, every successful response is appended (used by `sources check`).
        self.capture: list[FetchedResponse] | None = None
        self._client = httpx.Client(
            timeout=httpx.Timeout(READ_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
            follow_redirects=False,
            headers={"User-Agent": user_agent, "Accept": "application/json, text/*;q=0.8"},
        )

    def close(self) -> None:
        self._client.close()

    # -- public API ---------------------------------------------------------

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        respect_robots: bool = False,
    ) -> FetchedResponse:
        """GET with retries. Raises a FetchError subclass on failure."""
        self.validate_url(url)
        if respect_robots and not self._robots_checker().allowed(url):
            raise RobotsDisallowedError(f"robots.txt disallows {redact_url(url)}")
        last_error: FetchError | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._get_once(url, params)
                if self.capture is not None:
                    self.capture.append(response)
                return response
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = FetchError(f"{type(exc).__name__} fetching {redact_url(url)}")
            except _RetryableStatusError as exc:
                last_error = FetchError(f"HTTP {exc.status} from {redact_url(url)}")
            if attempt < MAX_ATTEMPTS:
                delay = 2.0 * 2 ** (attempt - 1) + self._rng.uniform(0.0, 1.0)
                log.warning(
                    "retrying %s (attempt %d failed)", redact_url(url), attempt,
                    extra={"ctx": {"delay_s": round(delay, 2)}},
                )
                self._sleep(delay)
        assert last_error is not None
        raise last_error

    def robots_allowed(self, url: str) -> bool:
        """Whether robots.txt allows this URL. Unreadable robots.txt means no (doc 03)."""
        return self._robots_checker().allowed(url)

    def validate_url(self, url: str) -> None:
        """SSRF rules (doc 08): HTTPS only, allowlisted host, public IPs only."""
        parts = urlsplit(url)
        if parts.scheme != "https":
            raise UnsafeUrlError(f"non-HTTPS URL rejected: {redact_url(url)}")
        host = (parts.hostname or "").lower()
        if not host or parts.username or parts.password:
            raise UnsafeUrlError("URL with missing host or credentials rejected")
        if parts.port not in (None, 443):
            raise UnsafeUrlError(f"non-standard port rejected for {host}")
        if host not in self._allowed_hosts:
            raise UnsafeUrlError(f"host not in allowlist: {host}")
        for ip in self._resolver(host):
            try:
                address = ipaddress.ip_address(ip.split("%")[0])
            except ValueError as exc:
                raise UnsafeUrlError(f"unparseable address for {host}") from exc
            if not address.is_global:
                raise UnsafeUrlError(f"{host} resolves to a non-public address")

    # -- internals ----------------------------------------------------------

    def _robots_checker(self) -> RobotsChecker:
        if self._robots is None:
            self._robots = RobotsChecker(self._fetch_robots_text, self._user_agent)
        return self._robots

    def _fetch_robots_text(self, robots_url: str) -> str:
        try:
            return self._get_once(robots_url, None).text
        except httpx.HTTPError as exc:
            raise FetchError(f"{type(exc).__name__} fetching robots.txt") from exc

    def _pace(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            wait = self._min_interval_s - (self._clock() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_request[host] = self._clock()

    def _get_once(self, url: str, params: Mapping[str, str | int] | None) -> FetchedResponse:
        current = url
        current_params = params
        for _ in range(MAX_REDIRECTS + 1):
            self.validate_url(current)
            self._pace(urlsplit(current).netloc.lower())
            with self._client.stream("GET", current, params=current_params) as response:
                status = response.status_code
                if status in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        raise FetchError(f"redirect without Location from {redact_url(current)}")
                    current = urljoin(current, location)
                    current_params = None
                    continue
                if status == 429:
                    retry_after = _parse_retry_after(response.headers.get("retry-after"))
                    raise RateLimitedError(f"HTTP 429 from {redact_url(current)}", retry_after)
                if status in (401, 403):
                    raise BlockedError(f"HTTP {status} from {redact_url(current)}")
                if status in (404, 410):
                    raise NotFoundError(f"HTTP {status} from {redact_url(current)}")
                if status in _RETRYABLE_STATUS:
                    raise _RetryableStatusError(status)
                if status >= 400:
                    raise FetchError(f"HTTP {status} from {redact_url(current)}")
                content = self._read_capped(response)
                return FetchedResponse(
                    url=current,
                    status_code=status,
                    content=content,
                    headers=dict(response.headers),
                )
        raise FetchError(f"too many redirects from {redact_url(url)}")

    def _read_capped(self, response: httpx.Response) -> bytes:
        declared = response.headers.get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > self._max_bytes:
            raise ResponseTooLargeError("declared response size over limit")
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_bytes():
            total += len(chunk)
            if total > self._max_bytes:
                raise ResponseTooLargeError("response over size limit")
            chunks.append(chunk)
        return b"".join(chunks)


class _RetryableStatusError(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"retryable status {status}")
        self.status = status
