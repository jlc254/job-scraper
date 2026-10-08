"""Transparent 100-point scorer (doc 06, step 2). Every point has a reason in the breakdown."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from rapidfuzz import fuzz

from jobscraper.matching.explain import build_explanation
from jobscraper.matching.settings import ProfileConfig, ScoringConfig
from jobscraper.matching.skills import JobSkills, SkillExtractor
from jobscraper.models import ExperienceLevel, Job, MatchTier, RemoteEligibility, WorkType
from jobscraper.utils.dedupe import format_salary

EAST_AFRICA = {"UG", "TZ", "RW", "ET", "BI", "SS", "SO", "DJ", "ER"}
_OPEN_REMOTE = {
    RemoteEligibility.KENYA, RemoteEligibility.AFRICA,
    RemoteEligibility.EAST_AFRICA, RemoteEligibility.WORLDWIDE,
}
_YEARS = re.compile(
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|\u2013|to)\s*(\d{1,2})\s*\+?)?\s*(?:years?|yrs?)\b", re.IGNORECASE
)
_SENIOR = re.compile(r"\b(?:senior|sr|lead|principal|staff)\b", re.IGNORECASE)
_ENTRY = re.compile(r"\b(?:junior|jr|entry[- ]level|graduate|intern|trainee)\b", re.IGNORECASE)


@dataclass
class Factor:
    points: float
    max: float
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"points": round(self.points, 2), "max": self.max, "reason": self.reason}


@dataclass
class SkillsMatch:
    matched: list[str] = field(default_factory=list)
    partial: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


def years_asked(text: str) -> tuple[int, int | None] | None:
    """First 'N years' phrase that sits next to the word 'experience'."""
    for match in _YEARS.finditer(text):
        window = text[max(0, match.start() - 80) : match.end() + 80].lower()
        if "experience" in window:
            low = int(match.group(1))
            high = int(match.group(2)) if match.group(2) else None
            return low, high
    return None


class Scorer:
    def __init__(self, profile: ProfileConfig, scoring: ScoringConfig, today: date) -> None:
        self._profile = profile
        self._cfg = scoring
        self._today = today
        self._extractor = SkillExtractor(scoring.skill_dictionary)
        self._titles = profile.normalized_titles()
        self._manager = [re.compile(p, re.IGNORECASE) for p in scoring.experience.manager_patterns]
        self._support_words = [k.lower() for k in scoring.filters.support_keywords]

    # -- public ----------------------------------------------------------------

    def score(self, job: Job) -> Job:
        flags: list[str] = []
        text = job.scoring_text or job.description_excerpt
        skills = self._extractor.extract(text)
        match = self._match_skills(skills)
        factors = {
            "title": self._title(job),
            "skills": self._skills(skills, match, flags),
            "location": self._location(job, flags),
            "experience": self._experience(job, text),
            "salary": self._salary(job),
            "freshness": self._freshness(job),
            "industry": self._industry(job, text),
        }
        total = round(sum(f.points for f in factors.values()), 1)
        tier = self._tier(total)
        explanation = build_explanation(
            job=job, tier=tier, skills=skills, match=match, flags=flags,
            profile=self._profile, scoring=self._cfg, today=self._today, text=text,
        )
        breakdown: dict[str, Any] = {
            "version": self._cfg.scoring_version,
            "total": total,
            "tier": tier.value,
            "factors": {name: f.as_dict() for name, f in factors.items()},
            "flags": flags,
            "skills": {
                "required": skills.required, "preferred": skills.preferred,
                "matched": match.matched, "partial": match.partial, "missing": match.missing,
            },
            "requirements": skills.requirements,
        }
        return job.model_copy(
            update={
                "match_score": total,
                "match_tier": tier,
                "match_breakdown": breakdown,
                "skills_required": skills.required,
                "skills_preferred": skills.preferred,
                "skills_matched": [*match.matched, *match.partial],
                "skills_missing": match.missing,
                "transferable": explanation.transferable,
                "recommended_action": explanation.action,
                "checklist": explanation.checklist,
            }
        )

    # -- factors ---------------------------------------------------------------

    def _title(self, job: Job) -> Factor:
        p = self._cfg.title
        title = job.title_normalized
        table = [
            ("strong", p.strong_exact, p.strong_fuzzy),
            ("potential", p.potential_exact, p.potential_fuzzy),
            ("stretch", p.stretch_exact, p.stretch_fuzzy),
        ]
        for name, exact_pts, fuzzy_pts in table:
            items = self._titles[name]
            if title in items:
                return Factor(exact_pts, 25, f"{name}-list exact match: {title}")
            best = max((fuzz.token_sort_ratio(title, item) for item in items), default=0)
            if best >= p.fuzzy_threshold:
                return Factor(fuzzy_pts, 25, f"{name}-list fuzzy match ({best:.0f})")
        if any(re.search(r"\b" + re.escape(k), title) for k in self._support_words):
            return Factor(p.other_keyword, 25, "support keyword in title")
        return Factor(0, 25, "no support keyword in title")

    def _match_skills(self, skills: JobSkills) -> SkillsMatch:
        full = set(self._profile.skills)
        partial = set(self._profile.partial_skills)
        result = SkillsMatch()
        for skill in dict.fromkeys([*skills.required, *skills.preferred]):
            if skill in full:
                result.matched.append(skill)
            elif skill in partial:
                result.partial.append(skill)
            else:
                result.missing.append(skill)
        return result

    def _skills(self, skills: JobSkills, match: SkillsMatch, flags: list[str]) -> Factor:
        p = self._cfg.skills
        if not skills.listed:
            flags.append("skills not listed")
            return Factor(p.unlisted, p.max, "skills not listed, neutral points")
        weights = {s: p.required_weight for s in skills.required}
        weights.update({s: p.preferred_weight for s in skills.preferred if s not in weights})
        total = sum(weights.values())
        got = sum(
            weights[s] * (1.0 if s in match.matched else p.partial_credit if s in match.partial else 0.0)
            for s in weights
        )
        return Factor(p.max * got / total, p.max, f"{got:g} of {total:g} skill weight matched")

    def _location(self, job: Job, flags: list[str]) -> Factor:
        p = self._cfg.location
        elig, country = job.remote_eligibility, job.country
        remote = job.work_type is WorkType.REMOTE
        if elig is RemoteEligibility.RESTRICTED:
            return Factor(0, 20, "restricted region (the hard filter excludes these)")
        if remote and elig in _OPEN_REMOTE:
            return Factor(p.open_remote, 20, f"remote, open to {elig.value}")
        if remote and elig is RemoteEligibility.TIMEZONE_LIMITED:
            return Factor(p.remote_timezone, 20, "remote, timezone-limited")
        if country == "KE":
            if "nairobi" in (job.location or "").lower():
                return Factor(p.nairobi_onsite, 20, "Nairobi")
            return Factor(p.other_kenyan_city, 20, "Kenya, not Nairobi or city unstated")
        if remote:
            flags.append("eligibility unconfirmed")
            return Factor(p.remote_unstated, 20, "remote, region unstated")
        if country in EAST_AFRICA:
            return Factor(p.east_africa_onsite, 20, "East Africa on-site (relocation)")
        if country:
            return Factor(p.other_international, 20, f"on-site in {country}")
        flags.append("eligibility unconfirmed")
        return Factor(p.unknown, 20, "location not stated")

    def _experience(self, job: Job, text: str) -> Factor:
        p = self._cfg.experience
        title = job.title.lower()
        exempt = any(e in title for e in p.manager_exceptions)
        if not exempt and any(rx.search(title) for rx in self._manager):
            return Factor(p.manager_director, 10, "manager or director role")
        if _SENIOR.search(title):
            return Factor(p.senior_lead, 10, "senior or lead role")
        asked = years_asked(text)
        if asked is not None:
            low, high = asked
            if high is not None and high <= 3:
                return Factor(p.years_1_to_3, 10, f"asks {low}-{high} years")
            if low <= 2:
                return Factor(p.years_1_to_3, 10, f"asks {low} years")
            if low <= 8:
                return Factor(p.years_3_to_8, 10, f"asks {low}+ years")
            return Factor(p.over_8_years, 10, f"asks {low}+ years")
        if _ENTRY.search(title) or job.experience_level is ExperienceLevel.ENTRY:
            return Factor(p.years_1_to_3, 10, "entry level")
        if job.experience_level is ExperienceLevel.MID:
            return Factor(p.years_3_to_8, 10, "mid level")
        if job.experience_level in (ExperienceLevel.SENIOR, ExperienceLevel.LEAD):
            return Factor(p.senior_lead, 10, "senior level")
        if job.experience_level is ExperienceLevel.MANAGER:
            return Factor(p.manager_director, 10, "manager level")
        return Factor(p.not_stated, 10, "experience not stated")

    def _salary(self, job: Job) -> Factor:
        p = self._cfg.salary
        floor = self._profile.salary_floor
        listed = format_salary(job)
        if not listed:
            return Factor(p.neutral, 10, "salary not listed")
        if floor is None:
            return Factor(p.neutral, 10, f"listed ({listed}), no floor set")
        amount = job.salary_max if job.salary_max is not None else job.salary_min
        period = job.salary_period
        if amount is None or job.salary_currency != floor.currency or period not in {"month", "year"}:
            return Factor(p.neutral, 10, f"listed ({listed}), not comparable to the floor")
        monthly = amount / 12 if period == "year" else amount
        floor_monthly = floor.amount / 12 if floor.period == "year" else floor.amount
        if monthly >= floor_monthly:
            return Factor(p.at_or_above_floor, 10, f"listed ({listed}), at or above floor")
        return Factor(p.below_floor, 10, f"listed ({listed}), below floor")

    def _freshness(self, job: Job) -> Factor:
        posted = job.date_posted
        note = ""
        if posted is None:
            posted = job.first_seen.date()
            note = " (posting date unknown, using discovery date)"
        age = max((self._today - posted).days, 0)
        for max_days, points in self._cfg.freshness.steps:
            if age <= max_days:
                return Factor(points, 5, f"{age} days old{note}")
        return Factor(0, 5, f"{age} days old{note}")

    def _industry(self, job: Job, text: str) -> Factor:
        p = self._cfg.industry
        haystack = f"{job.company} {job.title} {text[:500]}".lower()
        found = [
            name
            for name, words in self._cfg.industry_keywords.items()
            if any(re.search(r"\b" + re.escape(w.lower()) + r"\b", haystack) for w in words)
        ]
        if any(n in self._profile.avoided_industries for n in found):
            return Factor(p.avoided, 5, "avoided industry")
        if any(n in self._profile.preferred_industries for n in found):
            return Factor(p.preferred, 5, "preferred industry")
        return Factor(p.neutral, 5, "neutral or unknown industry")

    def _tier(self, total: float) -> MatchTier:
        t = self._cfg.tiers
        if total >= t.top:
            return MatchTier.TOP
        if total >= t.strong:
            return MatchTier.STRONG
        if total >= t.potential:
            return MatchTier.POTENTIAL
        return MatchTier.WEAK
