"""Remove emails and phone numbers from text before it is stored (D8)."""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
_PHONE = re.compile(r"(?<![\w.])\+?\(?\d[\d\s().\-]{7,}\d(?!\w)")
_NUMERIC_RANGE = re.compile(r"\d[\d,]*\s*[-\u2013]\s*\d[\d,]*")


def _phone_sub(match: re.Match[str]) -> str:
    text = match.group(0)
    digits = sum(ch.isdigit() for ch in text)
    if not 9 <= digits <= 15:
        return text
    # Salary ranges such as "20000-30000" are not phone numbers.
    if _NUMERIC_RANGE.fullmatch(text.strip()):
        return text
    return "[phone removed]"


def scrub_pii(text: str) -> str:
    """Return text with emails and phone numbers replaced by placeholders."""
    text = _EMAIL.sub("[email removed]", text)
    return _PHONE.sub(_phone_sub, text)
