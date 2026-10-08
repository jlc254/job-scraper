"""robots.txt checker (doc 03). Unreadable robots.txt means disallowed."""

from __future__ import annotations

import logging
from collections.abc import Callable
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from jobscraper.utils.errors import FetchError

log = logging.getLogger(__name__)


class RobotsChecker:
    """Caches one parsed robots.txt per host for the lifetime of a run.

    `fetch_text` returns the robots.txt body for a URL, or raises FetchError.
    Doc 03 says a robots.txt that cannot be fetched or parsed is treated as
    disallowed, which is stricter than the usual convention for a 404.
    """

    def __init__(self, fetch_text: Callable[[str], str], user_agent: str) -> None:
        self._fetch_text = fetch_text
        self._user_agent = user_agent
        self._cache: dict[str, RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if host not in self._cache:
            self._cache[host] = self._load(parts.scheme, host)
        parser = self._cache[host]
        if parser is None:
            return False
        return parser.can_fetch(self._user_agent, url)

    def _load(self, scheme: str, host: str) -> RobotFileParser | None:
        robots_url = f"{scheme}://{host}/robots.txt"
        try:
            body = self._fetch_text(robots_url)
            parser = RobotFileParser()
            parser.parse(body.splitlines())
        except (FetchError, ValueError, UnicodeDecodeError) as exc:
            log.warning("robots.txt unreadable for %s (%s); treating as disallowed", host, type(exc).__name__)
            return None
        return parser
