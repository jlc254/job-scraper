"""Optional config/settings.yaml: thresholds for health alarms, retention and the digest (doc 11).

Every value has a default in code, so the file may be missing or list only what you change.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jobscraper.config import ConfigError
from jobscraper.notifications.digest import DigestConfig
from jobscraper.publish import PublishSettings
from jobscraper.retention import RetentionSettings
from jobscraper.utils.health import HealthSettings


@dataclass(frozen=True)
class RuntimeSettings:
    health: HealthSettings
    retention: RetentionSettings
    digest: DigestConfig
    publish: PublishSettings = dataclasses.field(default_factory=PublishSettings)


def _build(section: str, cls: type[Any], values: Any, base: Any) -> Any:
    if values is None:
        return base
    if not isinstance(values, dict):
        raise ConfigError(f"settings.{section} must be a mapping")
    known = {f.name for f in dataclasses.fields(cls)}
    changes: dict[str, Any] = {}
    for key, value in values.items():
        if key not in known:
            raise ConfigError(
                f"settings.{section}.{key} is not a setting (known: {', '.join(sorted(known))})"
            )
        expected = type(getattr(base, key))
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ConfigError(f"settings.{section}.{key} must be a number, got {value!r}")
        if value < 0:
            raise ConfigError(f"settings.{section}.{key} must not be negative")
        changes[key] = expected(value)
    return dataclasses.replace(base, **changes)


def load_runtime_settings(path: Path | None, *, default_max_potential: int = 5) -> RuntimeSettings:
    """Defaults, overridden by the file if it exists. `default_max_potential` comes from scoring.yaml."""
    raw: dict[str, Any] = {}
    if path is not None and path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid settings file {path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ConfigError(f"invalid settings file {path}: expected a mapping")
        unknown = set(loaded) - {"health", "retention", "digest", "publish"}
        if unknown:
            raise ConfigError(f"unknown section(s) in {path}: {', '.join(sorted(unknown))}")
        raw = loaded

    publish_raw = raw.get("publish")
    if publish_raw is not None and not isinstance(publish_raw, dict):
        raise ConfigError("settings.publish must be a mapping")
    try:
        publish_settings = PublishSettings.model_validate(publish_raw or {})
    except Exception as exc:
        raise ConfigError(f"invalid settings.publish in {path}: {exc}") from exc

    return RuntimeSettings(
        health=_build("health", HealthSettings, raw.get("health"), HealthSettings()),
        retention=_build("retention", RetentionSettings, raw.get("retention"), RetentionSettings()),
        digest=_build(
            "digest",
            DigestConfig,
            raw.get("digest"),
            DigestConfig(max_potential=default_max_potential),
        ),
        publish=publish_settings,
    )
