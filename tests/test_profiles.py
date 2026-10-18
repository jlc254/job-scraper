"""Profiles loader and per-profile config checks (doc 15)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jobscraper.config import ConfigError
from jobscraper.profiles import (
    LEGACY_DIGEST_TITLE,
    enabled_profiles,
    load_profiles,
    pick_profile,
    resolve_sheet_ids,
)


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "profiles.yaml"
    path.write_text(text, encoding="utf-8")
    return path


TWO = """
profiles:
  - {id: support, label: Support, profile: a.yaml, scoring: b.yaml}
  - {id: community, label: Community, profile: c.yaml, scoring: d.yaml,
     sheet_id_env: SHEET_2, chat_id_env: CHAT_2}
"""


def test_no_file_means_the_single_legacy_profile_with_todays_title(tmp_path):
    (entry,) = load_profiles(tmp_path / "missing.yaml")
    assert entry.id == "support" and entry.digest_title == LEGACY_DIGEST_TITLE
    assert entry.sheet_id_env == "GOOGLE_SHEET_ID" and entry.chat_id_env == "TELEGRAM_CHAT_ID"


def test_two_profiles_load_and_default_title_comes_from_label(tmp_path):
    entries = load_profiles(write(tmp_path, TWO))
    assert [e.id for e in entries] == ["support", "community"]
    assert entries[1].digest_title == "NEW COMMUNITY JOBS"


@pytest.mark.parametrize(
    "text",
    [
        "profiles:\n  - {id: A1, label: A, profile: p, scoring: s}\n",  # bad id
        "profiles:\n  - {id: a, label: A, profile: p, scoring: s, typo: 1}\n",  # unknown key
        "profiles:\n  - {id: a, label: A, profile: p, scoring: s, enabled: false}\n",  # none enabled
        # two people on the same secrets would mix their data
        "profiles:\n  - {id: a, label: A, profile: p, scoring: s}\n"
        "  - {id: b, label: B, profile: p, scoring: s}\n",
        "profiles: []\n",
        "other: 1\n",
    ],
)
def test_bad_configs_are_refused(tmp_path, text):
    with pytest.raises(ConfigError):
        load_profiles(write(tmp_path, text))


def test_disabled_profiles_are_skipped_and_unknown_ids_refused(tmp_path):
    text = TWO.replace("scoring: d.yaml,", "scoring: d.yaml, enabled: false,")
    entries = load_profiles(write(tmp_path, text))
    assert [e.id for e in enabled_profiles(entries)] == ["support"]
    with pytest.raises(ConfigError):
        enabled_profiles(entries, ["community"])
    assert pick_profile(entries, None).id == "support"


def test_two_profiles_resolving_to_one_sheet_is_refused(tmp_path):
    entries = load_profiles(write(tmp_path, TWO))
    ok = resolve_sheet_ids(entries, {"GOOGLE_SHEET_ID": "x", "SHEET_2": "y"})
    assert ok == {"support": "x", "community": "y"}
    with pytest.raises(ConfigError):
        resolve_sheet_ids(entries, {"GOOGLE_SHEET_ID": "x", "SHEET_2": "x"})
    with pytest.raises(ConfigError):
        resolve_sheet_ids(entries, {"GOOGLE_SHEET_ID": "x"})  # second secret missing


def test_every_shipped_profile_loads_and_sets_its_own_filter_lists():
    """Catches a profile that silently inherits the customer-support defaults.

    The first entry in config/profiles.yaml is the customer-support profile, which intentionally
    relies on the code defaults for `support_keywords`. Every profile after it must set its own.
    """
    from jobscraper.matching.settings import load_profile, load_scoring

    entries = load_profiles(Path("config/profiles.yaml"))
    assert [e.id for e in entries] == ["support", "community"]
    for index, entry in enumerate(entries):
        load_profile(entry.profile_path)
        scoring = load_scoring(entry.scoring_path)
        if index > 0:
            assert "support_keywords" in scoring.filters.model_fields_set, entry.id
        assert scoring.skill_dictionary, entry.id


def test_every_profile_skill_exists_in_its_dictionary():
    from jobscraper.matching.settings import load_profile, load_scoring

    _entries = load_profiles(Path("config/profiles.yaml"))
    assert [e.id for e in _entries] == ["support", "community"]
    for entry in _entries:
        profile, scoring = load_profile(entry.profile_path), load_scoring(entry.scoring_path)
        known = set(scoring.skill_dictionary) | {
            s for v in scoring.skill_dictionary.values() for s in v
        }
        missing = [s for s in [*profile.skills, *profile.partial_skills] if s not in known]
        assert not missing, f"{entry.id}: not in skill_dictionary: {missing}"
        assert all(t in scoring.skill_dictionary for t in scoring.common_tools), entry.id
