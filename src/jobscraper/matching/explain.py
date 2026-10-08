"""Gaps and recommendations (doc 06): transferable strengths, action, checklist."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from jobscraper.matching.settings import ProfileConfig, ScoringConfig
from jobscraper.models import Job, MatchTier

if TYPE_CHECKING:
    from jobscraper.matching.scorer import SkillsMatch
    from jobscraper.matching.skills import JobSkills


@dataclass
class Explanation:
    transferable: list[str]
    action: str
    checklist: str


def transferable_strengths(profile: ProfileConfig, title: str, text: str) -> list[str]:
    haystack = f"{title}\n{text[:3000]}".lower()
    found: list[str] = []
    for item in profile.transferable:
        hits = [k for k in item.relevant_to if k.lower() in haystack]
        if hits:
            found.append(f"{item.strength} (relevant to {hits[0]})")
    return found


def recommended_action(
    *, job: Job, tier: MatchTier, match: SkillsMatch, flags: list[str],
    scoring: ScoringConfig, today: date,
) -> str:
    """One primary action by rule, then advisories that must not be hidden by it."""
    days_left = (job.application_deadline - today).days if job.application_deadline else None
    strong_or_top = tier in (MatchTier.TOP, MatchTier.STRONG)
    parts: list[str] = []
    if tier is MatchTier.WEAK:
        return ""  # stored, not notified
    if strong_or_top and days_left is not None and 0 <= days_left <= 3:
        parts.append("Apply now")
    elif strong_or_top:
        shown = ", ".join(match.matched[:4])
        parts.append(
            f"Tailor CV to matched skills ({shown}), apply within 3 days"
            if shown else "Tailor CV, apply within 3 days"
        )
    else:
        parts.append("Review gaps, apply if the role appeals")
    if "eligibility unconfirmed" in flags:
        parts.append("Check country eligibility before applying")
    common = {t.lower() for t in scoring.common_tools}
    missing_tools = [s for s in match.missing if s in common]
    if missing_tools:
        parts.append(
            f"Add a line on similar tool experience ({', '.join(missing_tools)}); consider a free course"
        )
    return ". ".join(parts) + "."


def build_checklist(job: Job, tier: MatchTier, match: SkillsMatch) -> str:
    """FR-9: for Top and Strong matches only."""
    if tier not in (MatchTier.TOP, MatchTier.STRONG):
        return ""
    deadline = job.application_deadline.isoformat() if job.application_deadline else "none listed"
    keywords = ", ".join([*match.matched, *match.partial][:8]) or "none extracted"
    return "\n".join(
        [
            f"Deadline: {deadline}",
            "Documents: tailored CV, cover letter if requested",
            f"Keywords to mirror: {keywords}",
            "Follow-up: applied date + 7 days",
        ]
    )


def build_explanation(
    *, job: Job, tier: MatchTier, skills: JobSkills, match: SkillsMatch, flags: list[str],
    profile: ProfileConfig, scoring: ScoringConfig, today: date, text: str,
) -> Explanation:
    del skills  # kept in the signature so callers pass everything the rules may need
    return Explanation(
        transferable=transferable_strengths(profile, job.title, text),
        action=recommended_action(
            job=job, tier=tier, match=match, flags=flags, scoring=scoring, today=today
        ),
        checklist=build_checklist(job, tier, match),
    )
