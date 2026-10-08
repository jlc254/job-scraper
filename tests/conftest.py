from __future__ import annotations

import json
import random
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from jobscraper.config import SourceConfig
from jobscraper.utils.http import HttpClient

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 1, 3, 0, tzinfo=timezone.utc)
PUBLIC_IP = "93.184.216.34"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Sleeper:
    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleeper() -> Sleeper:
    return Sleeper()


@pytest.fixture
def make_client(sleeper: Sleeper) -> Callable[..., HttpClient]:
    def factory(hosts: set[str], resolver: Callable[[str], list[str]] | None = None) -> HttpClient:
        return HttpClient(
            hosts,
            resolver=resolver or (lambda host: [PUBLIC_IP]),
            sleep=sleeper,
            rng=random.Random(0),
            min_interval_s=0.0,
        )

    return factory


@pytest.fixture
def now() -> datetime:
    return NOW


@pytest.fixture
def source_config() -> Callable[..., SourceConfig]:
    def factory(**overrides: Any) -> SourceConfig:
        base: dict[str, Any] = {"enabled": True, "status": "verified"}
        base.update(overrides)
        return SourceConfig.model_validate(base)

    return factory
