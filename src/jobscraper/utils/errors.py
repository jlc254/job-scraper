"""Exception types. Each maps to one source status in the runner."""

from __future__ import annotations


class FetchError(Exception):
    """Generic fetch failure (retries exhausted, bad status)."""


class BlockedError(FetchError):
    """HTTP 401/403. Never retried, never worked around."""


class RateLimitedError(FetchError):
    """HTTP 429. The source is marked rate_limited for this run."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(FetchError):
    """HTTP 404/410."""


class UnsafeUrlError(FetchError):
    """URL failed the SSRF rules (doc 08)."""


class ResponseTooLargeError(FetchError):
    """Response exceeded the size cap."""


class RobotsDisallowedError(FetchError):
    """robots.txt disallows the path, or could not be read (doc 03)."""


class SchemaError(FetchError):
    """Response did not have the expected overall shape."""


class StorageError(Exception):
    """Storage unreachable, over quota, or asked to break an ownership rule."""


class NotificationError(Exception):
    """A notification could not be delivered. Messages never include secrets or URLs."""
