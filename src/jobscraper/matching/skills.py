"""Skills extraction, version 1: a dictionary with synonyms, no machine learning (doc 06)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_REQUIRED = "required"
_PREFERRED = "preferred"

_HEADING = re.compile(
    r"(?im)(?:^|(?<=[.!?]\s))\s*(?:key\s+|minimum\s+|basic\s+|essential\s+)?"
    r"(requirements?|must[- ]have|qualifications?|what you(?:'ll| will)?\s+(?:need|bring)|required"
    r"|nice[- ]to[- ]have|preferred|bonus(?: points)?|desirable)\b\s*(?:skills|qualifications)?\s*(?::|$)"
)
_PREFERRED_WORDS = ("nice", "preferred", "bonus", "desirable")
_BULLET = re.compile(r"^[\s\-\u2022*\u00b7]+")
MAX_REQUIREMENT_LINES = 10
MAX_REQUIREMENT_CHARS = 200


@dataclass
class JobSkills:
    required: list[str] = field(default_factory=list)
    preferred: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)

    @property
    def listed(self) -> bool:
        return bool(self.required or self.preferred)


def _markers(text: str) -> list[tuple[int, int, str]]:
    """(start, end, kind) for each heading that opens a required or preferred section."""
    found: list[tuple[int, int, str]] = []
    for match in _HEADING.finditer(text):
        word = match.group(1).lower()
        kind = _PREFERRED if word.startswith(_PREFERRED_WORDS) else _REQUIRED
        found.append((match.start(), match.end(), kind))
    return found


def _kind_at(position: int, markers: list[tuple[int, int, str]]) -> str:
    """Section of a mention. No headings, or before the first one, means required."""
    kind = _REQUIRED
    for start, _end, marker_kind in markers:
        if start <= position:
            kind = marker_kind
        else:
            break
    return kind


def _requirement_lines(text: str, markers: list[tuple[int, int, str]]) -> list[str]:
    lines: list[str] = []
    for index, (_start, end, kind) in enumerate(markers):
        if kind != _REQUIRED:
            continue
        stop = markers[index + 1][0] if index + 1 < len(markers) else len(text)
        for raw in text[end:stop].split("\n"):
            line = _BULLET.sub("", raw).strip()
            if line:
                lines.append(line[:MAX_REQUIREMENT_CHARS])
        if len(lines) >= MAX_REQUIREMENT_LINES:
            break
    return lines[:MAX_REQUIREMENT_LINES]


class SkillExtractor:
    def __init__(self, dictionary: dict[str, list[str]]) -> None:
        self._patterns: dict[str, re.Pattern[str]] = {}
        for canonical, synonyms in dictionary.items():
            names = sorted({canonical, *synonyms}, key=len, reverse=True)
            body = "|".join(re.escape(n) for n in names if n.strip())
            if body:
                self._patterns[canonical] = re.compile(
                    rf"(?<![\w])(?:{body})(?![\w])", re.IGNORECASE
                )

    def extract(self, text: str) -> JobSkills:
        markers = _markers(text)
        required: list[str] = []
        preferred: list[str] = []
        for canonical, pattern in self._patterns.items():
            kinds = {_kind_at(m.start(), markers) for m in pattern.finditer(text)}
            if _REQUIRED in kinds:
                required.append(canonical)
            elif _PREFERRED in kinds:
                preferred.append(canonical)
        return JobSkills(required, preferred, _requirement_lines(text, markers))
