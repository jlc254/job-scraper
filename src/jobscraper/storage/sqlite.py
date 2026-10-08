"""SQLite backend for tests and local runs. Same column rules as the Sheet."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from jobscraper.models import ExcludedRecord, Job, JobUpdate, SourceRun, StoredJob
from jobscraper.models.dashboard import DashboardTable, sheet_value
from jobscraper.storage.base import Storage
from jobscraper.storage.rows import (
    TABLES,
    excluded_to_row,
    job_to_row,
    row_to_stored,
    source_run_to_row,
    validate_update,
)
from jobscraper.utils.errors import StorageError

_LOAD_TEMPLATES: dict[str, str] = {
    "jobs": "SELECT row_json FROM {name}",
    "excluded": "SELECT row_json, job_id FROM {name}",
    "runs": "SELECT row_json FROM {name}",
    "health": "SELECT row_json FROM {name}",
    "dashboard": "SELECT rowid, payload FROM {name}",
}
_DELETE_TEMPLATES: dict[str, str] = {
    "jobs": "SELECT rowid, row_json FROM {name}",
    "excluded": "SELECT rowid, row_json FROM {name}",
    "runs": "SELECT rowid, row_json FROM {name}",
    "health": "SELECT rowid, row_json FROM {name}",
    "dashboard": "SELECT rowid, payload FROM {name}",
}


class SQLiteStorage(Storage):
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._db = sqlite3.connect(str(path))
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, row_json TEXT NOT NULL)"
        )
        self._db.execute("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, row_json TEXT)")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS dashboard (name TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self._db.execute("CREATE TABLE IF NOT EXISTS health (id INTEGER PRIMARY KEY, row_json TEXT)")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS excluded (job_id TEXT PRIMARY KEY, row_json TEXT NOT NULL)"
        )
        self._db.commit()

    def load_index(self) -> list[StoredJob]:
        stored: list[StoredJob] = []
        name = self._resolve_table("jobs")
        for (raw,) in self._db.execute(_LOAD_TEMPLATES[name].format(name=name)):
            item = row_to_stored(json.loads(raw))
            if item is not None:
                stored.append(item)
        return stored

    def append_jobs(self, jobs: list[Job]) -> None:
        try:
            with self._db:
                for job in jobs:
                    self._db.execute(
                        "INSERT INTO jobs (job_id, row_json) VALUES (?, ?)",
                        (job.job_id, json.dumps(job_to_row(job))),
                    )
        except sqlite3.IntegrityError as exc:
            raise StorageError("duplicate job_id on append") from exc

    def update_jobs(self, updates: list[JobUpdate]) -> None:
        with self._db:
            for update in updates:
                validate_update(update.fields)
                found = self._db.execute(
                    "SELECT row_json FROM jobs WHERE job_id = ?", (update.job_id,)
                ).fetchone()
                if found is None:
                    continue
                row = json.loads(found[0])
                row.update(update.fields)
                self._db.execute(
                    "UPDATE jobs SET row_json = ? WHERE job_id = ?", (json.dumps(row), update.job_id)
                )

    def append_run(self, row: dict[str, str]) -> None:
        with self._db:
            self._db.execute("INSERT INTO runs (row_json) VALUES (?)", (json.dumps(row),))

    def append_excluded(self, records: list[ExcludedRecord]) -> None:
        with self._db:
            for record in records:
                self._db.execute(
                    "INSERT OR IGNORE INTO excluded (job_id, row_json) VALUES (?, ?)",
                    (record.job_id, json.dumps(excluded_to_row(record))),
                )

    def append_source_runs(self, runs: list[SourceRun]) -> None:
        with self._db:
            for run in runs:
                self._db.execute(
                    "INSERT INTO health (row_json) VALUES (?)", (json.dumps(source_run_to_row(run)),)
                )

    def load_excluded_ids(self) -> set[str]:
        name = self._resolve_table("excluded")
        return {r[1] for r in self._db.execute(_LOAD_TEMPLATES[name].format(name=name))}

    def load_rows(self) -> list[dict[str, str]]:
        return self.load_table("jobs")

    @staticmethod
    def _table(name: str) -> str:
        if name not in TABLES:  # table names come from this whitelist, never from input
            raise StorageError(f"unknown table: {name}")
        return name

    def _resolve_table(self, name: str) -> str:
        """Validate table name against the whitelist and return the safe name."""
        safe = self._table(name)  # raises StorageError if name not in TABLES
        if safe not in TABLES:
            raise StorageError(f"unknown table: {name}")
        return safe

    def _load_table(self, name: str) -> list[dict[str, str]]:
        safe = self._resolve_table(name)
        return [
            json.loads(r[0])
            for r in self._db.execute(_LOAD_TEMPLATES[safe].format(name=safe))  # noqa: S608 - safe name from whitelist
        ]

    def load_table(self, table: str) -> list[dict[str, str]]:  # noqa: N802 - required by Storage ABC
        name = self._resolve_table(table)
        return self._load_table(name)

    def load_rows(self) -> list[dict[str, str]]:
        name = self._resolve_table("jobs")
        return self._load_table(name)

    def delete_rows(self, table: str, key_column: str, keys: set[str]) -> int:
        name = self._resolve_table(table)
        doomed = [
            rowid
            for rowid, raw in self._db.execute(
                _DELETE_TEMPLATES[name].format(name=name)  # noqa: S608 - name is whitelisted via _resolve_table
            )
            if json.loads(raw).get(key_column) in keys
        ]
        with self._db:
            for rowid in doomed:
                self._db.execute(f"DELETE FROM {name} WHERE rowid = ?", (rowid,))  # noqa: S608 - name is whitelisted via _resolve_table
        return len(doomed)

    def write_dashboard(self, tables: list[DashboardTable]) -> None:
        """Stored as JSON with the same cell values the Sheet gets (dates as serial numbers)."""
        with self._db:
            for table in tables:
                payload = {"headers": table.headers, "rows": [[sheet_value(c) for c in row] for row in table.rows]}
                self._db.execute(
                    "INSERT OR REPLACE INTO dashboard (name, payload) VALUES (?, ?)", (table.name, json.dumps(payload))
                )

    def load_dashboard(self, name: str) -> dict[str, list[list[object]]] | None:
        found = self._db.execute("SELECT payload FROM dashboard WHERE name = ?", (name,)).fetchone()
        return json.loads(found[0]) if found else None  # type: ignore[no-any-return]

    # Test helpers -----------------------------------------------------------

    def get_row(self, job_id: str) -> dict[str, str] | None:
        found = self._db.execute("SELECT row_json FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return json.loads(found[0]) if found else None

    def set_user_cell(self, job_id: str, column: str, value: str) -> None:
        """Simulate the owner editing a user column in the Sheet."""
        row = self.get_row(job_id)
        assert row is not None
        row[column] = value
        with self._db:
            self._db.execute("UPDATE jobs SET row_json = ? WHERE job_id = ?", (json.dumps(row), job_id))
