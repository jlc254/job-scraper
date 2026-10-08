"""Storage interface (doc 04). Backends never score, filter or notify."""

from __future__ import annotations

from abc import ABC, abstractmethod

from jobscraper.models import ExcludedRecord, Job, JobUpdate, SourceRun, StoredJob
from jobscraper.models.dashboard import DashboardTable
from jobscraper.storage.rows import row_to_source_run


class Storage(ABC):
    @abstractmethod
    def load_index(self) -> list[StoredJob]:
        """Everything dedupe needs about jobs already stored."""

    @abstractmethod
    def append_jobs(self, jobs: list[Job]) -> None:
        """Append new rows. Never overwrites existing rows."""

    @abstractmethod
    def update_jobs(self, updates: list[JobUpdate]) -> None:
        """Update system-owned columns of existing rows. User columns are never written."""

    @abstractmethod
    def append_run(self, row: dict[str, str]) -> None:
        """Record one row in the Runs tab."""

    @abstractmethod
    def append_excluded(self, records: list[ExcludedRecord]) -> None:
        """Record jobs removed by hard filters (audit trail, kept 30 days)."""

    @abstractmethod
    def load_excluded_ids(self) -> set[str]:
        """job_ids already in the Excluded log, so they are not logged again."""

    @abstractmethod
    def load_rows(self) -> list[dict[str, str]]:
        """Every Jobs row as a header-name dictionary, for `brief` and `calibrate`."""

    @abstractmethod
    def append_source_runs(self, runs: list[SourceRun]) -> None:
        """Record one row per source for this run (the Health tab)."""

    @abstractmethod
    def load_table(self, table: str) -> list[dict[str, str]]:
        """All rows of 'jobs', 'excluded', 'runs' or 'health' as header-name dictionaries."""

    @abstractmethod
    def delete_rows(self, table: str, key_column: str, keys: set[str]) -> int:
        """Delete rows whose `key_column` value is in `keys`. Rows are found by key at the
        moment of deletion, never by a position read earlier. Returns how many were removed."""

    @abstractmethod
    def write_dashboard(self, tables: list[DashboardTable]) -> None:
        """Replace the Dash_* tabs with these tables. They are derived data, rebuilt every time."""

    def load_source_runs(self) -> list[SourceRun]:
        """Health history, newest first."""
        runs = [r for row in self.load_table("health") if (r := row_to_source_run(row)) is not None]
        return sorted(runs, key=lambda r: r.started_utc, reverse=True)
