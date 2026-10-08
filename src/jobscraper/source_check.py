"""`sources check` (FR-14): reachability, robots.txt and parse success, without saving jobs.

Run by the owner from a normal shell, low volume (one page per source). It is also the tool for
the verification procedure in doc 02: it can save a sanitized real response as a test fixture.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from jobscraper.config import SourceConfig
from jobscraper.runner import ClientFactory, default_client_factory
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import get_adapter_class
from jobscraper.utils.errors import FetchError
from jobscraper.utils.http import FetchedResponse, HttpClient
from jobscraper.utils.pii import scrub_pii

# Sources whose status says "do not contact" are refused even when named explicitly.
CHECKABLE_STATUSES = frozenset({"verified", "pending"})
MAX_FIXTURE_ITEMS = 5
MAX_FIXTURE_BYTES = 200_000
_ITEM = re.compile(r"<item\b.*?</item>", re.DOTALL | re.IGNORECASE)


@dataclass
class CheckResult:
    source: str
    ok: bool = False
    detail: str = ""
    seconds: float = 0.0
    robots: str = "n/a (API source)"
    found: int = 0
    mapped: int = 0
    samples: list[str] = field(default_factory=list)
    captured: list[FetchedResponse] = field(default_factory=list)


def refusal_reason(cfg: SourceConfig) -> str | None:
    if cfg.status not in CHECKABLE_STATUSES:
        return f"status is '{cfg.status}': not contacted"
    return None


def check_source(
    source_id: str, cfg: SourceConfig, now: datetime, client_factory: ClientFactory = default_client_factory
) -> CheckResult:
    result = CheckResult(source=source_id)
    adapter_cls = get_adapter_class(source_id)
    if adapter_cls is None:
        result.detail = "no adapter registered for this id"
        return result
    refused = refusal_reason(cfg)
    if refused:
        result.detail = refused
        return result

    adapter: Adapter = adapter_cls(cfg.model_copy(update={"max_pages": 1}), now)
    client: HttpClient = client_factory(adapter)
    client.capture = result.captured
    started = time.monotonic()
    try:
        raws = adapter.fetch(client)
    except FetchError as exc:
        result.seconds = round(time.monotonic() - started, 1)
        result.detail = f"not reachable or unusable: {type(exc).__name__}: {exc}"
        return result
    finally:
        result.seconds = round(time.monotonic() - started, 1)

    if adapter.kind == "html":
        verdicts = []
        for response in result.captured:
            allowed = client.robots_allowed(response.url)
            verdicts.append("allowed" if allowed else "DISALLOWED or unreadable")
        result.robots = ", ".join(sorted(set(verdicts))) or "no page fetched"
    client.close()

    result.found = len(raws)
    for raw in raws:
        try:
            job = adapter.to_job(raw)
        except (ValidationError, ValueError, TypeError, KeyError, AttributeError):
            job = None
        if job is not None:
            result.mapped += 1
            if len(result.samples) < 3:
                result.samples.append(f"{job.title} ({job.company})")
    ratio = result.mapped / result.found if result.found else 0.0
    result.ok = result.found > 0 and ratio >= 0.7 and not result.robots.startswith("DISALLOWED")
    result.detail = f"{result.found} records, {result.mapped} mapped" + (
        "" if result.found else " (empty response: check the site in a browser)"
    )
    if result.found and ratio < 0.7:
        result.detail += " (many records failed to map: the format may have changed)"
    return result


def format_check(results: list[CheckResult]) -> str:
    lines = []
    for r in results:
        mark = "OK  " if r.ok else "FAIL"
        lines.append(f"{mark} {r.source:<16} {r.detail}  [{r.seconds}s] robots: {r.robots}")
        for sample in r.samples:
            lines.append(f"       e.g. {sample}")
    return "\n".join(lines)


# -- fixtures ------------------------------------------------------------------------------------

def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        return scrub_pii(value)[:4000]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        trimmed = value[:MAX_FIXTURE_ITEMS] if value and all(isinstance(v, dict) for v in value) else value[:50]
        return [_scrub(v) for v in trimmed]
    return value


def sanitize_fixture(content: bytes) -> tuple[str, str]:
    """(extension, text) for a captured response: personal data removed, a few items only.

    JSON keeps its full structure with long lists cut to five records. Feeds keep their
    header and the first five <item> elements.
    """
    text = content.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except ValueError:
        items = list(_ITEM.finditer(text))
        if len(items) > MAX_FIXTURE_ITEMS:
            text = text[: items[MAX_FIXTURE_ITEMS].start()] + text[items[-1].end():]
        return "xml", scrub_pii(text)[:MAX_FIXTURE_BYTES]
    return "json", json.dumps(_scrub(data), ensure_ascii=False, indent=2)[:MAX_FIXTURE_BYTES]


def save_fixture(result: CheckResult, directory: Path) -> Path | None:
    """Save the first captured response. Review the file before committing it."""
    if not result.captured:
        return None
    extension, text = sanitize_fixture(result.captured[0].content)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{result.source}.{extension}"
    path.write_text(text, encoding="utf-8")
    return path


def select_sources(
    sources: dict[str, SourceConfig], requested: list[str] | None
) -> list[str]:
    """Default: enabled and verified. Named sources may also be pending (to verify them)."""
    if requested:
        return requested
    return [sid for sid, cfg in sources.items() if cfg.enabled and cfg.status == "verified"]


Checker = Callable[[str, SourceConfig, datetime], CheckResult]
