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
        for (raw,) in self._db.execute("SELECT row_json FROM jobs"):
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

    def load_excluded_ids(self) -> set[str]:
        return {r[0] for r in self._db.execute("SELECT job_id FROM excluded")}

    def load_rows(self) -> list[dict[str, str]]:
        return self.load_table("jobs")

    @staticmethod
    def _table(name: str) -> str:
        if name not in TABLES:  # table names come from this whitelist, never from input
            raise StorageError(f"unknown table: {name}")
        return name

    def load_table(self, table: str) -> list[dict[str, str]]:
        name = self._table(table)
        return [json.loads(r[0]) for r in self._db.execute(f"SELECT row_json FROM {name}")]  # noqa: S608

    def append_source_runs(self, runs: list[SourceRun]) -> None:
        with self._db:
            for run in runs:
                self._db.execute(
                    "INSERT INTO health (row_json) VALUES (?)", (json.dumps(source_run_to_row(run)),)
                )

    def delete_rows(self, table: str, key_column: str, keys: set[str]) -> int:
        name = self._table(table)
        doomed = [
            rowid
            for rowid, raw in self._db.execute(f"SELECT rowid, row_json FROM {name}")  # noqa: S608
            if json.loads(raw).get(key_column) in keys
        ]
        with self._db:
            for rowid in doomed:
                self._db.execute(f"DELETE FROM {name} WHERE rowid = ?", (rowid,))  # noqa: S608
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
