"""Markdown job brief for CV and cover-letter help (FR-10). Built from the stored row."""

from __future__ import annotations

import json
from typing import Any


def _breakdown(row: dict[str, str]) -> dict[str, Any]:
    try:
        data = json.loads(row.get("match_breakdown", "") or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "- none"


def render_brief(row: dict[str, str]) -> str:
    data = _breakdown(row)
    skills = data.get("skills", {}) if isinstance(data.get("skills"), dict) else {}
    urls = [u for u in row.get("all_urls", "").splitlines() if u.strip()] or [row.get("job_url", "")]
    lines = [
        f"# {row.get('title', '')} at {row.get('company', '')}",
        "",
        f"- Location: {row.get('location') or 'not stated'} "
        f"({row.get('work_type', 'unknown')}, eligibility: {row.get('remote_eligibility', 'unclear')})",
        f"- Score: {row.get('match_score') or 'n/a'} ({row.get('match_tier') or 'unscored'}), "
        f"scoring version {data.get('version', 'n/a')}",
        f"- Salary: {row.get('salary') or 'not listed'}",
        f"- Deadline: {row.get('application_deadline') or 'none listed'}",
        f"- Source: {row.get('source', '')}",
        "- Links:",
        *[f"  - {u}" for u in urls],
        "",
        "## Recommended action",
        row.get("recommended_action") or "None (weak match).",
        "",
        "## Why it scored this way",
    ]
    for name, factor in (data.get("factors") or {}).items():
        lines.append(f"- {name}: {factor.get('points')}/{factor.get('max')}, {factor.get('reason')}")
    if data.get("flags"):
        lines += ["", "Flags: " + "; ".join(data["flags"])]
    lines += [
        "", "## Requirements from the posting", _bullets(data.get("requirements", [])),
        "", "## Skills you match", _bullets(skills.get("matched", []) + [f"{s} (partial)" for s in skills.get("partial", [])]),
        "", "## Skills to address", _bullets(skills.get("missing", [])),
        "", "## Excerpt", row.get("description_excerpt") or "(not stored)",
    ]
    if row.get("checklist"):
        lines += ["", "## Checklist", row["checklist"]]
    return "\n".join(lines) + "\n"


def find_row(rows: list[dict[str, str]], job_id: str) -> dict[str, str] | None:
    """Exact job_id, or a unique prefix."""
    exact = [r for r in rows if r.get("job_id") == job_id]
    if exact:
        return exact[0]
    prefix = [r for r in rows if job_id and r.get("job_id", "").startswith(job_id)]
    return prefix[0] if len(prefix) == 1 else None
