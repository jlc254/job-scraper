"""Pure normalization helpers for titles, companies and locations (doc 05).

No imports from models, so these stay trivially testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_BRACKETED = re.compile(r"\([^)]*\)|\[[^\]]*\]|\{[^}]*\}")
_SEGMENTS = re.compile(r"\s+[-\u2013\u2014|/]\s+|\s*\|\s*|,\s+")
_PUNCT = re.compile(r"[^\w\s]|_")
_LEVEL_NOISE = {"sr", "senior", "jr", "junior"}
_LEGAL_SUFFIXES = {
    "ltd",
    "limited",
    "inc",
    "incorporated",
    "llc",
    "plc",
    "gmbh",
    "corp",
    "corporation",
}
_LOCATION_WORDS = {
    "remote",
    "remotely",
    "hybrid",
    "onsite",
    "on",
    "site",
    "worldwide",
    "anywhere",
    "global",
    "kenya",
    "nairobi",
    "mombasa",
    "kisumu",
    "nakuru",
    "eldoret",
    "africa",
    "east",
    "west",
    "emea",
    "us",
    "usa",
    "uk",
    "eu",
    "europe",
    "apac",
    "latam",
    "america",
    "americas",
    "north",
    "south",
    "canada",
    "nigeria",
    "ghana",
    "lagos",
    "uganda",
    "kampala",
    "tanzania",
    "rwanda",
    "egypt",
    "india",
    "philippines",
    "wfh",
    "work",
    "from",
    "home",
    "flexible",
    "based",
    "only",
    "and",
    "or",
    "in",
    "the",
    "time",
    "zone",
    "gmt",
    "utc",
    "cet",
    "est",
    "pst",
}

_KENYAN_PLACES = ("nairobi", "mombasa", "kisumu", "nakuru", "eldoret", "thika", "kenya")
_COUNTRIES = (
    ("united states", "US"),
    ("usa", "US"),
    ("canada", "CA"),
    ("united kingdom", "GB"),
    ("south africa", "ZA"),
    ("nigeria", "NG"),
    ("ghana", "GH"),
    ("uganda", "UG"),
    ("tanzania", "TZ"),
    ("rwanda", "RW"),
    ("egypt", "EG"),
    ("india", "IN"),
    ("philippines", "PH"),
    ("germany", "DE"),
    ("ireland", "IE"),
)
_REMOTE_WORDS = ("remote", "work from home", "wfh", "anywhere", "worldwide", "global")
_WORLDWIDE_WORDS = ("anywhere", "worldwide", "global", "any location")


def _is_location_segment(segment: str) -> bool:
    words = re.findall(r"[a-z]+", segment)
    return bool(words) and all(w in _LOCATION_WORDS for w in words)


def normalize_title(title: str) -> str:
    """Lowercase, drop bracketed text, location suffixes, punctuation and level noise."""
    lowered = _BRACKETED.sub(" ", title.lower())
    parts = [p for p in _SEGMENTS.split(lowered) if p.strip()]
    while len(parts) > 1 and _is_location_segment(parts[-1]):
        parts.pop()
    text = _PUNCT.sub(" ", " ".join(parts))
    words = [w for w in text.split() if w not in _LEVEL_NOISE]
    if not words:  # a title made only of noise words: keep it rather than lose it
        words = _PUNCT.sub(" ", title.lower()).split()
    return " ".join(words)


def normalize_company(name: str) -> str:
    """Lowercase, remove punctuation and trailing legal suffixes."""
    words = _PUNCT.sub(" ", name.lower()).split()
    while len(words) > 1 and words[-1] in _LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


@dataclass(frozen=True)
class LocationInfo:
    country: str | None
    is_remote: bool
    eligibility: str | None  # values match RemoteEligibility; only set for remote text


def classify_location(text: str | None) -> LocationInfo:
    """Read free-text location. Conservative: unknown stays unknown."""
    if not text:
        return LocationInfo(None, False, None)
    low = text.lower()
    is_remote = any(w in low for w in _REMOTE_WORDS)
    country: str | None = "KE" if any(p in low for p in _KENYAN_PLACES) else None
    if country is None:
        for needle, code in _COUNTRIES:
            if needle in low:
                country = code
                break
    eligibility: str | None = None
    if is_remote:
        if "east africa" in low:
            eligibility = "east_africa"
        elif "kenya" in low:
            eligibility = "kenya"
        elif "africa" in low:
            eligibility = "africa"
        elif any(w in low for w in _WORLDWIDE_WORDS):
            eligibility = "worldwide"
    return LocationInfo(country, is_remote, eligibility)


def geo_eligibility(text: str | None, default: str = "restricted") -> str:
    """Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).

    A named region that does not include Africa or Kenya means restricted.
    EMEA is ambiguous and stays unclear (doc 06 flags these for review).
    """
    if not text or not text.strip():
        return "unclear"
    low = text.lower()
    if "east africa" in low:
        return "east_africa"
    if "kenya" in low:
        return "kenya"
    if "africa" in low:
        return "africa"
    if any(w in low for w in _WORLDWIDE_WORDS):
        return "worldwide"
    if "emea" in low:
        return "unclear"
    return default
