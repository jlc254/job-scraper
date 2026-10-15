"""Postgres backend for local development. Same column rules as the Sheet.

Connection string: postgresql://postgres:postgres@localhost:5433/jobs
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg import sql

from jobscraper.models import (
    ExcludedRecord,
    Job,
    JobUpdate,
    SourceRun,
    StoredJob,
)
from jobscraper.models.dashboard import DashboardTable, sheet_value
from jobscraper.storage.base import Storage
from jobscraper.storage.rows import (
    JOBS_HEADERS,
    USER_COLUMNS,
    excluded_to_row,
    job_to_row,
    row_to_stored,
    source_run_to_row,
    validate_update,
)
from jobscraper.utils.errors import StorageError

log = None  # placeholder, set below


def _log_once(msg: str) -> None:
    global log
    if log is None:
        import logging

        log = logging.getLogger(__name__)
    log.warning(msg)


def _connect(dsn: str) -> psycopg.Connection[Any]:
    """Connect to Postgres, creating the configured database on first run."""
    database = conninfo_to_dict(dsn).get("dbname") or "postgres"
    template_dsn = make_conninfo(dsn, dbname="template1")
    admin_conn = psycopg.connect(template_dsn, connect_timeout=10, autocommit=True)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    admin_conn.close()

    # Now connect to the jobs database and create tables
    conn = psycopg.connect(dsn, connect_timeout=10, autocommit=True)
    with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    fingerprint       TEXT NOT NULL,                    job_id            TEXT PRIMARY KEY,
                    title             TEXT NOT NULL,
                    company           TEXT NOT NULL,
                    location          TEXT,
                    work_type         TEXT NOT NULL,
                    employment_type   TEXT NOT NULL,
                    remote_eligibility TEXT NOT NULL,
                    salary            TEXT,
                    skills_matched    TEXT[],
                    skills_missing    TEXT[],
                    match_score       DOUBLE PRECISION,
                    match_tier        TEXT,
                    scoring_version   INTEGER,
                    match_breakdown   JSONB,
                    recommended_action TEXT,
                    source            TEXT NOT NULL,
                    job_url           TEXT NOT NULL,
                    date_posted       DATE,
                    application_deadline DATE,
                    first_seen        TIMESTAMPTZ,
                    last_seen         TIMESTAMPTZ,
                    is_active         BOOLEAN NOT NULL,
                    is_repost         BOOLEAN NOT NULL,
                    description_excerpt TEXT,
                    checklist         TEXT,
                    source_job_id     TEXT,
                    all_urls          TEXT,
                    notified_at       TIMESTAMPTZ,
                    follow_up_reminded_on TIMESTAMPTZ,
                    application_status TEXT NOT NULL,
                    applied_on        DATE,
                    follow_up_date    DATE,
                    notes             TEXT,
                    priority          TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS excluded (
                    job_id      TEXT PRIMARY KEY,
                    row_json    TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id          SERIAL PRIMARY KEY,
                    row_json    TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS health (
                    id          SERIAL PRIMARY KEY,
                    row_json    TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboard (
                    name        TEXT PRIMARY KEY,
                    payload     TEXT NOT NULL
                )
                """
            )
    return conn


class PostgresStorage(Storage):
    def __init__(self, dsn: str = "postgresql://postgres:postgres@localhost:5433/jobs") -> None:
        self._dsn = dsn
        self._conn = _connect(dsn)

    def _load_jobs(self) -> list[dict[str, str]]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT job_id, fingerprint, title, company, location, work_type,
                       employment_type, remote_eligibility, salary, skills_matched,
                       skills_missing, match_score, match_tier, match_breakdown,
                       recommended_action, source, job_url, date_posted,
                       application_deadline, first_seen, last_seen, is_active,
                       notified_at, checklist, source_job_id, all_urls,
                       description_excerpt, is_repost, follow_up_reminded_on,
                       application_status, applied_on, follow_up_date, notes, priority
                FROM jobs
                """
            )
            return [dict(zip(JOBS_HEADERS, r)) for r in cur]

    def load_index(self) -> list[StoredJob]:
        stored: list[StoredJob] = []
        for row in self._load_jobs():
            item = row_to_stored(row)
            if item is not None:
                stored.append(item)
        return stored

    def append_jobs(self, jobs: list[Job]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                for job in jobs:
                    row = job_to_row(job)
                    cols = sql.SQL(", ").join(sql.Identifier(c) for c in row.keys())
                    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in row)
                    cur.execute(
                        sql.SQL("INSERT INTO jobs ({cols}) VALUES ({placeholders})").format(
                            cols=cols, placeholders=placeholders
                        ),
                        list(row.values()),
                    )

    def update_jobs(self, updates: list[JobUpdate]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                for update in updates:
                    validate_update(update.fields)
                    if not update.fields:
                        continue
                    found = cur.execute(
                        "SELECT " + ", ".join(JOBS_HEADERS) + " FROM jobs WHERE job_id = %s",
                        (update.job_id,),
                    ).fetchone()
                    if found is None:
                        continue
                    row = dict(zip(JOBS_HEADERS, found))
                    row.update(update.fields)
                    fields = list(update.fields)
                    assignments = sql.SQL(", ").join(
                        sql.SQL("{} = %s").format(sql.Identifier(field)) for field in fields
                    )
                    cur.execute(
                        sql.SQL("UPDATE jobs SET {assignments} WHERE job_id = %s").format(
                            assignments=assignments
                        ),
                        [row[field] for field in fields] + [update.job_id],
                    )

    def append_run(self, row: dict[str, str]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                cur.execute("INSERT INTO runs (row_json) VALUES (%s)", (json.dumps(row),))

    def append_excluded(self, records: list[ExcludedRecord]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                for record in records:
                    cur.execute(
                        "INSERT INTO excluded (job_id, row_json) VALUES (%s, %s) ON CONFLICT (job_id) DO NOTHING",
                        (record.job_id, json.dumps(excluded_to_row(record))),
                    )

    def load_excluded_ids(self) -> set[str]:
        with self._conn.cursor() as cur:
            cur.execute("SELECT job_id FROM excluded")
            return {r[0] for r in cur}

    def load_rows(self) -> list[dict[str, str]]:
        return self._load_jobs()

    def append_source_runs(self, runs: list[SourceRun]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                for run in runs:
                    cur.execute(
                        "INSERT INTO health (row_json) VALUES (%s)",
                        (json.dumps(source_run_to_row(run)),),
                    )

    def load_table(self, table: str) -> list[dict[str, str]]:
        if table == "jobs":
            return self._load_jobs()
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT row_json FROM {table}")
            return [json.loads(r[0]) for r in cur]

    def delete_rows(self, table: str, key_column: str, keys: set[str]) -> int:
        key_columns = {"jobs": "job_id", "excluded": "job_id", "runs": "run_id", "health": "key"}
        id_columns = {"jobs": "job_id", "excluded": "job_id", "runs": "id", "health": "id"}
        if table not in key_columns or key_column != key_columns[table] or not keys:
            return 0
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                if table in {"jobs", "excluded"}:
                    cur.execute(
                        sql.SQL("DELETE FROM {} WHERE {} = ANY(%s)").format(
                            sql.Identifier(table), sql.Identifier(key_columns[table])
                        ),
                        (list(keys),),
                    )
                    return cur.rowcount
                cur.execute(sql.SQL("SELECT id, row_json FROM {}").format(sql.Identifier(table)))
                doomed = [
                    row_id for row_id, row_json in cur
                    if json.loads(row_json).get(key_column) in keys
                ]
                if doomed:
                    cur.execute(
                        sql.SQL("DELETE FROM {} WHERE {} = ANY(%s)").format(
                            sql.Identifier(table), sql.Identifier(id_columns[table])
                        ),
                        (doomed,),
                    )
                return len(doomed)

    def write_dashboard(self, tables: list[DashboardTable]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                for table in tables:
                    payload = {
                        "headers": table.headers,
                        "rows": [[sheet_value(c) for c in row] for row in table.rows],
                    }
                    try:
                        cur.execute(
                            "INSERT INTO dashboard (name, payload) VALUES (%s, %s)",
                            (table.name, json.dumps(payload)),
                        )
                    except psycopg.Error:
                        cur.execute(
                            "UPDATE dashboard SET payload = %s WHERE name = %s",
                            (json.dumps(payload), table.name),
                        )

    def load_dashboard(self, name: str) -> dict[str, Any] | None:
        with self._conn.cursor() as cur:
            cur.execute("SELECT payload FROM dashboard WHERE name = %s", (name,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None

    def get_row(self, job_id: str) -> dict[str, str] | None:
        with self._conn.cursor() as cur:
            cur.execute("SELECT " + ", ".join(JOBS_HEADERS) + " FROM jobs WHERE job_id = %s", (job_id,))
            row = cur.fetchone()
            return dict(zip(JOBS_HEADERS, row)) if row else None

    def set_user_cell(self, job_id: str, column: str, value: str) -> None:
        if column not in USER_COLUMNS:
            raise StorageError(f"refusing to update unknown user column: {column}")
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                cur.execute(
                    sql.SQL("UPDATE jobs SET {} = %s WHERE job_id = %s").format(
                        sql.Identifier(column)
                    ),
                    (value, job_id),
                )

    def close(self) -> None:
        self._conn.close()
