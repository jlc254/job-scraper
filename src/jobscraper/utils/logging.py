"""JSON logging with a redaction filter (doc 07, doc 11)."""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Iterable
from typing import Any

_URL_QUERY = re.compile(r"(https?://[^\s?#]+)\?[^\s]*")
# No leading \b: in a URL the token follows the letters "bot", with no word boundary between them.
_BOT_TOKEN = re.compile(r"(?<!\d)\d{6,}:[A-Za-z0-9_-]{30,}")
_BEARER = re.compile(r"(?i)\b(bearer|token|api[_-]?key|app[_-]?key)\b\s*[=:]\s*\S+")


class RedactionFilter(logging.Filter):
    """Strips query strings, tokens and registered secret values from messages."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        super().__init__()
        self._secrets = [s for s in secrets if s and len(s) >= 4]

    def redact(self, text: str) -> str:
        text = _URL_QUERY.sub(r"\1?[redacted]", text)
        text = _BOT_TOKEN.sub("[redacted]", text)
        text = _BEARER.sub(r"\1=[redacted]", text)
        for secret in self._secrets:
            text = text.replace(secret, "[redacted]")
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.redact(record.getMessage())
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line. Extra context goes in `ctx`."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        ctx = getattr(record, "ctx", None)
        if isinstance(ctx, dict):
            payload["ctx"] = ctx
        if record.exc_info and record.exc_info[0] is not None:
            # Exception type only: messages can echo scraped data.
            payload["exc_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(secrets: Iterable[str] = (), level: int = logging.INFO) -> None:
    """Configure the root logger once. Logs go to stderr so stdout stays clean."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactionFilter(secrets))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
