"""HTML to plain text, truncation and small value helpers. Pure functions."""

from __future__ import annotations

import html
import re
from email.utils import parsedate_to_datetime
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit

_BLOCK_TAGS = {"p", "br", "li", "ul", "ol", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}
_SKIP_TAGS = {"script", "style"}
_WS = re.compile(r"[ \t\r\f\v]+")
_BLANKS = re.compile(r"\n\s*\n+")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    """Strip tags and return plain text. Scraped content is data, never markup."""
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    text = "".join(parser.parts)
    text = _WS.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANKS.sub("\n\n", text).strip()


def unescape_then_text(value: str) -> str:
    """For feeds that deliver HTML entity-escaped HTML (Greenhouse `content`)."""
    return html_to_text(html.unescape(value))


def truncate(text: str, max_chars: int) -> str:
    """Cut at max_chars, preferring a word boundary. 0 returns an empty string."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    space = cut.rfind(" ")
    if space > max_chars * 0.8:
        cut = cut[:space]
    return cut.rstrip() + "\u2026"


def clean_str(value: object) -> str | None:
    """Return a stripped non-empty string, else None."""
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def safe_http_url(value: object) -> str | None:
    """Accept only absolute http(s) URLs. Anything else is dropped."""
    text = clean_str(value)
    if text is None:
        return None
    parts = urlsplit(text)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    return text


def parse_date(value: object) -> date | None:
    """Parse unix seconds/milliseconds or ISO-8601 strings to a UTC date."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        seconds = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            pass
        try:  # RFC 822, as used by RSS pubDate
            return parsedate_to_datetime(value.strip()).date()
        except (TypeError, ValueError, IndexError):
            return None
    return None
