"""Adapter contract (doc 04). Adapters return data. They never write or notify."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar

from jobscraper.config import SourceConfig
from jobscraper.models import Job, RawJob
from jobscraper.utils.http import HttpClient


class Adapter(ABC):
    """One adapter per source (one per ATS platform)."""

    id: ClassVar[str]
    display_name: ClassVar[str]
    requires_key: ClassVar[str | None] = None
    allowed_hosts: ClassVar[frozenset[str]]
    kind: ClassVar[str] = "api"  # "api" or "html". HTML sources are checked against robots.txt.
    min_interval_s: ClassVar[float] = 1.0

    def __init__(self, config: SourceConfig, now: datetime) -> None:
        self.config = config
        self.now = now
        # Non-fatal problems (for example one ATS board failing) so the runner can report `partial`.
        self.partial_errors: list[str] = []

    @abstractmethod
    def fetch(self, client: HttpClient) -> list[RawJob]:
        """Return raw records. May raise a FetchError subclass."""

    @abstractmethod
    def to_job(self, raw: RawJob) -> Job | None:
        """Map one raw record to the common schema, or None if unusable."""
