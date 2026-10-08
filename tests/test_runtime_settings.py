from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jobscraper.config import ConfigError
from jobscraper.notifications.digest import DigestConfig
from jobscraper.retention import RetentionSettings
from jobscraper.runtime_settings import load_runtime_settings
from jobscraper.utils.health import HealthSettings

EXAMPLE = Path(__file__).parent.parent / "config" / "settings.example.yaml"


def write(tmp_path, text: str) -> Path:
    path = tmp_path / "settings.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_missing_file_means_defaults_and_scoring_supplies_max_potential(tmp_path: Any) -> None:
    s = load_runtime_settings(tmp_path / "nope.yaml", default_max_potential=7)
    assert s.health == HealthSettings() and s.retention == RetentionSettings()
    assert (
        s.digest == DigestConfig(max_potential=7)
        and load_runtime_settings(None).digest.max_potential == 5
    )


def test_the_example_file_documents_exactly_the_defaults() -> None:
    s = load_runtime_settings(EXAMPLE)
    assert (s.health, s.retention, s.digest) == (
        HealthSettings(),
        RetentionSettings(),
        DigestConfig(),
    )


def test_overrides_keep_the_types_of_the_defaults(tmp_path: Any) -> None:
    s = load_runtime_settings(
        write(
            tmp_path,
            "health: {strikes: 5, drop_ratio: 0.1}\nretention: {job_days: 90}\ndigest: {max_potential: 2}\n",
        )
    )
    assert (
        s.health.strikes == 5 and isinstance(s.health.strikes, int) and s.health.drop_ratio == 0.1
    )
    assert s.retention.job_days == 90 and s.digest.max_potential == 2 and s.health.window == 7


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("health: {stikes: 5}", "not a setting"),
        ("helth: {}", "unknown section"),
        ("health: {strikes: many}", "must be a number"),
        ("retention: {job_days: -1}", "negative"),
        ("health: [1, 2]", "must be a mapping"),
        ("- just a list", "expected a mapping"),
        ("health: {strikes: true}", "must be a number"),
    ],
)
def test_bad_settings_fail_fast_with_a_clear_message(
    tmp_path: Any, text: Any, message: Any
) -> None:
    with pytest.raises(ConfigError, match=message):
        load_runtime_settings(write(tmp_path, text))
