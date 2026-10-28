"""Profiles: one entry per person the pipeline runs for (doc 15).

Fetching is shared. Everything a person owns is per profile: the candidate profile and scoring
files, the Google Sheet, the Telegram chat and the digest title. A profile never reads another
profile's Sheet, and the loader refuses a config where two profiles would share one.

With no config/profiles.yaml the legacy single-profile setup runs unchanged, so existing
installs keep working. Plain dataclasses and manual checks, like runtime_settings.py.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jobscraper.config import ConfigError

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,23}$")
KNOWN_KEYS = frozenset(
    {
        "id",
        "label",
        "enabled",
        "profile",
        "scoring",
        "sheet_id_env",
        "chat_id_env",
        "digest_title",
        "sources",
    }
)
LEGACY_ID = "juliet"
LEGACY_DIGEST_TITLE = "NEW JULIET JOBS"

# Old profile ids renamed to persona ids. Resolved transparently so legacy
# commands/links (e.g. --for support, ?profile=support) still reach the right profile.
PROFILE_ALIASES: dict[str, str] = {"support": "juliet", "community": "jumalaw98"}


@dataclass(frozen=True)
class ProfileEntry:
    id: str
    label: str
    profile_path: Path
    scoring_path: Path
    sheet_id_env: str = "GOOGLE_SHEET_ID_JULIET"
    chat_id_env: str = "TELEGRAM_CHAT_ID_JULIET"
    digest_title: str = "NEW JOBS"
    sources: tuple[str, ...] | None = None  # None means every enabled source
    enabled: bool = True

    def sheet_id(self, environ: Mapping[str, str]) -> str:
        value = environ.get(self.sheet_id_env, "").strip()
        if not value:
            raise ConfigError(f"profile '{self.id}': {self.sheet_id_env} is not set")
        return value

    def chat_id(self, environ: Mapping[str, str]) -> str:
        value = environ.get(self.chat_id_env, "").strip()
        if not value:
            raise ConfigError(f"profile '{self.id}': {self.chat_id_env} is not set")
        return value


def legacy_profile(profile: Path, scoring: Path) -> ProfileEntry:
    """The pre-multi-profile setup: same files, same secrets, same digest title."""
    return ProfileEntry(
        id=LEGACY_ID,
        label="Juliet",
        profile_path=profile,
        scoring_path=scoring,
        digest_title=LEGACY_DIGEST_TITLE,
    )


def _text(raw: Mapping[str, Any], key: str, where: str, default: str | None = None) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{where}.{key} must be a non-empty string")
    return value.strip()


def _entry(raw: Any, index: int) -> ProfileEntry:
    where = f"profiles[{index}]"
    if not isinstance(raw, dict):
        raise ConfigError(f"{where} must be a mapping")
    unknown = set(raw) - KNOWN_KEYS
    if unknown:
        raise ConfigError(
            f"{where} has unknown key(s): {', '.join(sorted(map(str, unknown)))} "
            f"(known: {', '.join(sorted(KNOWN_KEYS))})"
        )
    profile_id = _text(raw, "id", where)
    if not ID_PATTERN.fullmatch(profile_id):
        raise ConfigError(
            f"{where}.id '{profile_id}' must be lowercase letters, digits or underscores, "
            "start with a letter, and be at most 24 characters"
        )
    label = _text(raw, "label", where)
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ConfigError(f"{where}.enabled must be true or false")
    sources = raw.get("sources")
    if sources is not None and (
        not isinstance(sources, list) or not all(isinstance(s, str) for s in sources)
    ):
        raise ConfigError(f"{where}.sources must be a list of source ids")
    return ProfileEntry(
        id=profile_id,
        label=label,
        profile_path=Path(_text(raw, "profile", where)),
        scoring_path=Path(_text(raw, "scoring", where)),
        sheet_id_env=_text(raw, "sheet_id_env", where, "GOOGLE_SHEET_ID_JULIET"),
        chat_id_env=_text(raw, "chat_id_env", where, "TELEGRAM_CHAT_ID_JULIET"),
        digest_title=_text(raw, "digest_title", where, f"NEW {label.upper()} JOBS"),
        sources=tuple(sources) if sources is not None else None,
        enabled=enabled,
    )


def load_profiles(
    path: Path | None,
    *,
    legacy_profile_path: Path = Path("config/profile.yaml"),
    legacy_scoring_path: Path = Path("config/scoring.yaml"),
) -> list[ProfileEntry]:
    """Every profile in the file (enabled or not), or the single legacy profile if no file."""
    if path is None or not path.is_file():
        return [legacy_profile(legacy_profile_path, legacy_scoring_path)]
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid profiles file {path}: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) - {"profiles"}:
        raise ConfigError(f"{path} must contain only a 'profiles' list")
    items = raw.get("profiles")
    if not isinstance(items, list) or not items:
        raise ConfigError(f"{path}: 'profiles' must be a non-empty list")
    entries = [_entry(item, i) for i, item in enumerate(items)]
    _check_unique(entries)
    return entries


def _check_unique(entries: list[ProfileEntry]) -> None:
    enabled = [e for e in entries if e.enabled]
    if not enabled:
        raise ConfigError("at least one profile must be enabled")
    # The first profile is the operator: it owns health history and alerts, so it must be enabled.
    if not entries[0].enabled:
        raise ConfigError(
            f"the first profile '{entries[0].id}' is the operator and must be enabled"
        )
    for field_name in ("id", "sheet_id_env", "chat_id_env"):
        seen: dict[str, str] = {}
        for e in enabled if field_name != "id" else entries:
            value = getattr(e, field_name)
            if value in seen:
                raise ConfigError(
                    f"profiles '{seen[value]}' and '{e.id}' share the same {field_name} "
                    f"'{value}'. Each person needs their own, or their data would mix."
                )
            seen[value] = e.id


def _resolve_alias(profile_id: str) -> str:
    return PROFILE_ALIASES.get(profile_id, profile_id)


def enabled_profiles(
    entries: list[ProfileEntry], only: list[str] | None = None
) -> list[ProfileEntry]:
    """Enabled profiles, optionally narrowed by `--only`. Unknown or disabled ids are an error."""
    by_id = {e.id: e for e in entries}
    if only:
        resolved = [p if p in by_id else _resolve_alias(p) for p in only]
        bad = [p for p in resolved if p not in by_id or not by_id[p].enabled]
        if bad:
            raise ConfigError(f"unknown or disabled profile id(s): {', '.join(bad)}")
        return [by_id[p] for p in dict.fromkeys(resolved)]
    return [e for e in entries if e.enabled]


def resolve_sheet_ids(entries: list[ProfileEntry], environ: Mapping[str, str]) -> dict[str, str]:
    """Sheet id per profile. Two profiles resolving to the same Sheet is refused."""
    resolved: dict[str, str] = {}
    owner: dict[str, str] = {}
    for e in entries:
        sheet = e.sheet_id(environ)
        if sheet in owner:
            raise ConfigError(
                f"profiles '{owner[sheet]}' and '{e.id}' point at the same Google Sheet"
            )
        owner[sheet] = e.id
        resolved[e.id] = sheet
    return resolved


def resolve_chat_ids(entries: list[ProfileEntry], environ: Mapping[str, str]) -> dict[str, str]:
    """Chat id per profile. Two profiles resolving to the same chat is refused."""
    resolved: dict[str, str] = {}
    owner: dict[str, str] = {}
    for e in entries:
        chat = e.chat_id(environ)
        if chat in owner:
            raise ConfigError(
                f"profiles '{owner[chat]}' and '{e.id}' point at the same Telegram chat"
            )
        owner[chat] = e.id
        resolved[e.id] = chat
    return resolved


def validate_profile_sources(entries: list[ProfileEntry], known: Iterable[str]) -> None:
    """Every profile's `sources` list must name configured sources, or its jobs vanish silently."""
    known_set = set(known)
    for e in entries:
        if not e.sources:
            continue
        unknown = [s for s in e.sources if s not in known_set]
        if unknown:
            raise ConfigError(f"profile '{e.id}' names unknown source id(s): {', '.join(unknown)}")


def pick_profile(entries: list[ProfileEntry], requested: str | None) -> ProfileEntry:
    """The profile a single-profile command (brief, calibrate, health...) works on.

    `requested` comes from `--for`. Without it, the first enabled profile is used, which is the
    operator's own profile and the legacy one when there is no profiles.yaml.
    """
    return enabled_profiles(entries, [requested] if requested else None)[0]
