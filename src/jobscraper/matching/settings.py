"""Validated profile and scoring configuration (doc 06, doc 11).

Every point value defaults to the number in doc 06 and can be overridden in
config/scoring.yaml. Bump `scoring_version` whenever a value changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from jobscraper.config import DEFAULT_KEYWORDS, ConfigError
from jobscraper.parsers.names import normalize_title

DEFAULT_REGION_PATTERNS = [
    # Abbreviations are case-sensitive so "email us only" is not read as "US only".
    r"\b(?-i:US|U\.S\.)\s+(?:residents?|citizens?)\s+only\b",
    r"\b(?:(?-i:US|U\.S\.|UK|U\.K\.|EU)|usa|united states|canada|europe)\s+(?:only|residents? only)\b",
    r"\bmust (?:be )?(?:legally )?(?:authori[sz]ed|eligible) to work in (?:the )?"
    r"(?:us|u\.s\.|usa|united states|uk|u\.k\.|united kingdom|eu|european union|canada|australia)\b",
    r"\bmust (?:reside|live|be (?:located|based)) in (?:the )?"
    r"(?:us|u\.s\.|usa|united states|uk|united kingdom|eu|europe|canada|australia)\b",
    r"\bright to work in (?:the )?(?:uk|united kingdom|eu|us|usa|ireland)\b",
]
DEFAULT_SCAM_PATTERNS = [
    r"registration fee",
    r"processing fee",
    r"training fee",
    r"refundable deposit",
    r"\bpay (?:a |an )?(?:fee )?to apply\b",
    r"commission[- ]only",
    r"\bmlm\b",
    r"multi[- ]level marketing",
    r"(?:apply|contact|reach us|message us)\s+(?:only\s+)?(?:via|on|through)\s+(?:whatsapp|telegram)",
    r"whatsapp (?:only|number) to apply",
]
DEFAULT_EXCLUDED_TITLES = [
    r"\btelemarketer\b",
    r"\btelesales\b",
    r"\bsales (?:representative|executive|associate|agent)\b",
    r"\bbusiness development\b",
]
DEFAULT_SUPPORT_KEYWORDS = sorted(
    {*DEFAULT_KEYWORDS, "support", "customer", "helpdesk", "client", "complaint", "chat agent"}
)


class TitlePoints(BaseModel):
    strong_exact: float = 25
    strong_fuzzy: float = 22
    potential_exact: float = 18
    potential_fuzzy: float = 15
    stretch_exact: float = 10
    stretch_fuzzy: float = 8
    other_keyword: float = 5
    fuzzy_threshold: float = 85


class SkillsPoints(BaseModel):
    max: float = 25
    unlisted: float = 12
    required_weight: float = 2
    preferred_weight: float = 1
    partial_credit: float = 0.5


class LocationPoints(BaseModel):
    open_remote: float = 20
    nairobi_onsite: float = 20
    other_kenyan_city: float = 16
    remote_timezone: float = 16
    remote_unstated: float = 10
    east_africa_onsite: float = 8
    other_international: float = 4
    unknown: float = 10


class ExperiencePoints(BaseModel):
    years_3_to_8: float = 10
    years_1_to_3: float = 8
    not_stated: float = 7
    senior_lead: float = 6
    manager_director: float = 2
    over_8_years: float = 6
    manager_patterns: list[str] = Field(
        default_factory=lambda: [
            r"\b(?:head of|director|vp|vice president|general manager)\b",
            r"\bmanager\b",
        ]
    )
    manager_exceptions: list[str] = Field(default_factory=lambda: ["customer success manager"])


class SalaryPoints(BaseModel):
    at_or_above_floor: float = 10
    below_floor: float = 2
    neutral: float = 5


class FreshnessPoints(BaseModel):
    # (max age in days, points), checked in order. Older than the last row scores 0.
    steps: list[tuple[int, float]] = Field(
        default_factory=lambda: [(3, 5.0), (7, 4.0), (14, 3.0), (30, 1.0)]
    )


class IndustryPoints(BaseModel):
    preferred: float = 5
    neutral: float = 3
    avoided: float = 0


class TierCutoffs(BaseModel):
    top: float = 85
    strong: float = 75
    potential: float = 50


class FilterSettings(BaseModel):
    region_restricted_patterns: list[str] = Field(
        default_factory=lambda: list(DEFAULT_REGION_PATTERNS)
    )
    scam_patterns: list[str] = Field(default_factory=lambda: list(DEFAULT_SCAM_PATTERNS))
    excluded_title_patterns: list[str] = Field(
        default_factory=lambda: list(DEFAULT_EXCLUDED_TITLES)
    )
    support_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_SUPPORT_KEYWORDS))
    max_age_days: int = 30
    offtopic_chars: int = 300


class ScoringConfig(BaseModel):
    scoring_version: int = 1
    title: TitlePoints = Field(default_factory=TitlePoints)
    skills: SkillsPoints = Field(default_factory=SkillsPoints)
    location: LocationPoints = Field(default_factory=LocationPoints)
    experience: ExperiencePoints = Field(default_factory=ExperiencePoints)
    salary: SalaryPoints = Field(default_factory=SalaryPoints)
    freshness: FreshnessPoints = Field(default_factory=FreshnessPoints)
    industry: IndustryPoints = Field(default_factory=IndustryPoints)
    tiers: TierCutoffs = Field(default_factory=TierCutoffs)
    filters: FilterSettings = Field(default_factory=FilterSettings)
    skill_dictionary: dict[str, list[str]] = Field(default_factory=dict)
    industry_keywords: dict[str, list[str]] = Field(default_factory=dict)
    common_tools: list[str] = Field(default_factory=lambda: ["freshdesk", "intercom", "salesforce"])
    digest_max_potential: int = 5

    @field_validator("skill_dictionary")
    @classmethod
    def _lower(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        return {k.lower(): [s.lower() for s in v] for k, v in value.items()}


class SalaryFloor(BaseModel):
    amount: float
    currency: str
    period: str = "month"  # month or year


class Transferable(BaseModel):
    strength: str
    relevant_to: list[str]


class ProfileTitles(BaseModel):
    strong: list[str] = Field(default_factory=list)
    potential: list[str] = Field(default_factory=list)
    stretch: list[str] = Field(default_factory=list)


class ProfileConfig(BaseModel):
    titles: ProfileTitles = Field(default_factory=ProfileTitles)
    skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    avoided_industries: list[str] = Field(default_factory=list)
    salary_floor: SalaryFloor | None = None
    transferable: list[Transferable] = Field(default_factory=list)

    @field_validator("skills", "partial_skills", "preferred_industries", "avoided_industries")
    @classmethod
    def _lower_list(cls, value: list[str]) -> list[str]:
        return [v.lower() for v in value]

    def normalized_titles(self) -> dict[str, list[str]]:
        return {
            "strong": [normalize_title(t) for t in self.titles.strong],
            "potential": [normalize_title(t) for t in self.titles.potential],
            "stretch": [normalize_title(t) for t in self.titles.stretch],
        }


def _load(path: Path, model: type[BaseModel], hint: str) -> Any:
    if not path.is_file():
        raise ConfigError(f"{path} not found. {hint}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return model.model_validate(raw)
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"invalid config {path}: {exc}") from exc


def load_scoring(path: Path) -> ScoringConfig:
    result: ScoringConfig = _load(path, ScoringConfig, "Copy config/scoring.example.yaml to start.")
    return result


def load_profile(path: Path) -> ProfileConfig:
    result: ProfileConfig = _load(
        path, ProfileConfig, "Copy config/profile.example.yaml and edit it."
    )
    return result
