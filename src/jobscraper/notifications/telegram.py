"""Telegram Bot API notifier. Plain text only, sent to one configured chat (doc 08).

The bot token sits in the request URL, so this module never logs or raises a URL.
Error messages carry only a status code and Telegram's own short description.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from jobscraper.notifications.base import Notifier, SendResult
from jobscraper.utils.errors import NotificationError

log = logging.getLogger(__name__)

API_HOST = "https://api.telegram.org"
MAX_ATTEMPTS = 3
MIN_GAP_S = 1.1  # Telegram allows about one message per second to the same chat
MAX_RETRY_AFTER_S = 30.0
ALERT_MAX_CHARS = 1000


class _Permanent(Exception):
    """Do not retry: bad token, blocked bot, unknown chat, rejected message."""


class TelegramNotifier(Notifier):
    def __init__(
        self,
        token: str,
        chat_id: str,
        *,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not token or not chat_id:
            raise NotificationError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")
        self._token = token
        self._chat_id = chat_id
        self._client = client or httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0))
        self._sleep = sleep
        self._clock = clock
        self._last_sent: float | None = None

    @classmethod
    def from_env(cls, environ: dict[str, str]) -> TelegramNotifier:
        return cls(environ.get("TELEGRAM_BOT_TOKEN", ""), environ.get("TELEGRAM_CHAT_ID", ""))

    def __repr__(self) -> str:  # keeps the token out of tracebacks and logs
        return "TelegramNotifier(token=***, chat_id=***)"

    # -- Notifier ------------------------------------------------------------

    def send(self, messages: Sequence[str]) -> SendResult:
        sent = 0
        for text in messages:
            try:
                self._pace()
                self._post(text)
            except (NotificationError, _Permanent) as exc:
                log.error("telegram send failed", extra={"ctx": {"sent": sent, "of": len(messages)}})
                return SendResult(sent, str(exc))
            sent += 1
        return SendResult(sent)

    def send_alert(self, text: str) -> bool:
        return self.send([f"ALERT: {text[:ALERT_MAX_CHARS]}"]).sent == 1

    # -- internals -------------------------------------------------------------

    def _pace(self) -> None:
        if self._last_sent is not None:
            wait = MIN_GAP_S - (self._clock() - self._last_sent)
            if wait > 0:
                self._sleep(wait)

    def _post(self, text: str) -> None:
        url = f"{API_HOST}/bot{self._token}/sendMessage"
        body: dict[str, Any] = {
            "chat_id": self._chat_id,
            "text": text,
            "link_preview_options": {"is_disabled": True},  # no parse_mode: always plain text
        }
        failure = "unknown error"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._client.post(url, json=body)
            except httpx.HTTPError as exc:
                failure = f"network error ({type(exc).__name__})"
                self._backoff(attempt)
                continue
            self._last_sent = self._clock()
            if response.status_code == 200:
                return
            description, retry_after = _describe(response)
            if response.status_code == 429:
                if retry_after is None or retry_after > MAX_RETRY_AFTER_S:
                    raise NotificationError(f"Telegram rate limited (retry after {retry_after}s)")
                failure = "Telegram rate limited"
                self._sleep(retry_after)
                continue
            if response.status_code >= 500:
                failure = f"Telegram server error {response.status_code}"
                self._backoff(attempt)
                continue
            raise _Permanent(f"Telegram rejected the message ({response.status_code}: {description})")
        raise NotificationError(f"Telegram unavailable after {MAX_ATTEMPTS} attempts: {failure}")

    def _backoff(self, attempt: int) -> None:
        if attempt < MAX_ATTEMPTS:
            self._sleep(2.0 * 2 ** (attempt - 1))


def _describe(response: httpx.Response) -> tuple[str, float | None]:
    """Telegram's own error text and retry_after, if the body is the expected JSON."""
    try:
        data = response.json()
    except ValueError:
        return "no details", None
    if not isinstance(data, dict):
        return "no details", None
    description = str(data.get("description", "no details"))[:120]
    params = data.get("parameters")
    retry = params.get("retry_after") if isinstance(params, dict) else None
    return description, float(retry) if isinstance(retry, int | float) else None
