"""Config loading and the source gate (doc 03)."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

log = logging.getLogger(__name__)

# From the query set in doc 02. Interim relevance prefilter until Phase 4 filters.
DEFAULT_KEYWORDS: tuple[str, ...] = (
    "customer support", "customer service", "customer care", "customer success",
    "customer experience", "help desk", "helpdesk", "service desk", "technical support",
    "contact centre", "contact center", "call centre", "call center", "client services",
    "account support", "order support", "billing support", "collections", "onboarding",
    "complaints", "retention", "support administrator", "chat support", "email support",
    "support specialist", "support agent", "support representative", "support engineer",
)


class ConfigError(Exception):
    """Config file missing or invalid. Fail fast with a clear message."""


class SourceConfig(BaseModel):
    """One entry under `sources:` in sources.yaml."""

    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    status: str = "pending"
    verified_on: date | None = None
    terms_url: str | None = None
    excerpt_max_chars: int = Field(default=1000, ge=0)
    keywords: list[str] | None = None
    max_pages: int = Field(default=3, ge=1, le=20)
    page_size: int = Field(default=20, ge=1, le=100)
    # ATS sources: tokens, or {token: ..., name: ...} mappings.
    boards: list[str | dict[str, str]] = Field(default_factory=list)
    # Feed sources (We Work Remotely): feed URLs. API sources: extra query parameters.
    feeds: list[str] = Field(default_factory=list)
    query_params: dict[str, str | int] = Field(default_factory=dict)


class SourcesFile(BaseModel):
    sources: dict[str, SourceConfig]


def load_sources(path: Path) -> dict[str, SourceConfig]:
    """Read and validate sources.yaml."""
    if not path.is_file():
        raise ConfigError(f"sources config not found: {path}")
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        return SourcesFile.model_validate(raw).sources
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"invalid sources config {path}: {exc}") from exc


def gate_reason(source_id: str, cfg: SourceConfig) -> str | None:
    """Return why a source may not run, or None when it passes the gate."""
    if not cfg.enabled:
        return "disabled"
    if cfg.status != "verified":
        return f"status is '{cfg.status}', not 'verified'"
    if cfg.verified_on is None or not cfg.terms_url:
        log.warning("source %s is verified but missing verified_on or terms_url", source_id)
    return None
