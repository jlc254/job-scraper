"""Lenient date reading for cells the owner types into the Sheet (applied_on, follow_up_date)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3), "EAT")  # Kenya has no daylight saving
_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d-%b-%Y",
)


def parse_user_date(value: str | None) -> date | None:
    """Parse a typed date. Day-first wins for ambiguous numeric dates (Kenya).

    Also accepts ISO timestamps and Google Sheets serial numbers.
    """
    text = (value or "").strip()
    if not text:
        return None
    if text.isdigit() and 30_000 <= int(text) <= 80_000:  # Sheets serial day count
        return date(1899, 12, 30) + timedelta(days=int(text))
    for fmt in _FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO timestamp written by this tool. Naive values are taken as UTC."""
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
