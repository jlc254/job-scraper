"""Write-only Neon copy (doc 13, doc 15). Not a full Storage implementation.

What: opens one connection with the publisher role and replaces ONE PROFILE's slice of the
jobs copy in one transaction. Every read, upsert, delete and meta row is scoped by profile,
so publishing one person's jobs can never remove or change another person's rows.
Inputs: the DIRECT connection string (never logged), column names, typed row dicts.
Outputs: count of stale rows deleted.
Failure behavior: any database error becomes NeonError with no connection string or SQL text.
The transaction rolls back, so the dashboard keeps showing the previous data.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from datetime import datetime
from types import TracebackType
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

# Explicit casts keep empty lists and NULLs unambiguous for Postgres.
_CASTS: dict[str, str] = {
    "skills_matched": "text[]",
    "skills_missing": "text[]",
    "match_breakdown": "jsonb",
}


class NeonError(RuntimeError):
    """A Neon connection or write failed. The message never contains secrets."""


def _safe(exc: Exception) -> str:
    code = getattr(exc, "sqlstate", None)
    return f"{type(exc).__name__}" + (f" (SQLSTATE {code})" if code else "")


def _adapt(value: Any) -> Any:
    return Jsonb(value) if isinstance(value, dict) else value


class NeonPublisher:
    def __init__(self, dsn: str, *, retries: int = 1, backoff_seconds: float = 3.0) -> None:
        self._dsn = dsn
        self._retries = retries
        self._backoff = backoff_seconds
        self._conn: psycopg.Connection[Any] | None = None

    def __enter__(self) -> NeonPublisher:
        self._conn = self._connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _connect(self) -> psycopg.Connection[Any]:
        """Connect with one retry: compute may be waking from scale-to-zero."""
        last: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                return psycopg.connect(self._dsn, connect_timeout=15, autocommit=True)
            except psycopg.Error as exc:
                last = exc
                if attempt < self._retries:
                    time.sleep(self._backoff)
        raise NeonError(f"could not connect to Neon: {_safe(last or RuntimeError())}") from None

    def _require(self) -> psycopg.Connection[Any]:
        if self._conn is None:
            raise NeonError("publisher used outside a with-block")
        return self._conn

    def count_jobs(self, profile: str) -> int:
        """Rows currently held for this profile only (used by the collapse guard)."""
        try:
            row = (
                self._require()
                .execute("SELECT count(*) FROM jobs WHERE profile = %s", (profile,))
                .fetchone()
            )
        except psycopg.Error as exc:
            raise NeonError(f"count failed: {_safe(exc)}") from None
        return int(row[0]) if row else 0

    def prune_profiles(self, keep: Sequence[str]) -> int:
        """Delete rows and meta of profiles that are no longer enabled (doc 15, D33).

        Refuses an empty `keep`, so a config mistake can never wipe the whole table.
        """
        if not keep:
            raise NeonError("refusing to prune with no enabled profiles")
        conn = self._require()
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM jobs WHERE profile <> ALL(%s)", (list(keep),))
                    removed = cur.rowcount
                    cur.execute("DELETE FROM publish_meta WHERE profile <> ALL(%s)", (list(keep),))
        except psycopg.Error as exc:
            raise NeonError(f"prune failed and was rolled back: {_safe(exc)}") from None
        return max(removed, 0)

    def replace_jobs(
        self,
        columns: Sequence[str],
        rows: Sequence[Mapping[str, Any]],
        *,
        profile: str,
        run_start: datetime,
        sheet_rows: int,
        batch_size: int = 200,
    ) -> int:
        """Upsert this profile's rows, delete its rows not refreshed this run, update its meta.

        Everything happens in one transaction. Every row must carry the same `profile`.
        Every value is a bound parameter and column names are composed as identifiers.
        `run_start` must equal `published_at` on the rows.
        """
        cols = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
        values = sql.SQL(", ").join(
            sql.SQL("%s::" + _CASTS[c]) if c in _CASTS else sql.SQL("%s") for c in columns
        )
        updates = sql.SQL(", ").join(
            sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c))
            for c in columns
            if c not in ("profile", "job_id")
        )
        upsert = sql.SQL(
            "INSERT INTO jobs ({cols}) VALUES ({values}) "
            "ON CONFLICT (profile, job_id) DO UPDATE SET {updates}"
        ).format(cols=cols, values=values, updates=updates)

        if "profile" not in columns or any(r["profile"] != profile for r in rows):
            raise NeonError("every row must carry the profile being published")
        conn = self._require()
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    for start in range(0, len(rows), batch_size):
                        batch = rows[start : start + batch_size]
                        cur.executemany(
                            upsert, [tuple(_adapt(r[c]) for c in columns) for r in batch]
                        )
                    cur.execute(
                        "DELETE FROM jobs WHERE profile = %s AND published_at < %s",
                        (profile, run_start),
                    )
                    deleted = cur.rowcount
                    cur.execute(
                        "INSERT INTO publish_meta (profile, published_at, job_count, sheet_rows) "
                        "VALUES (%s, %s, %s, %s) "
                        "ON CONFLICT (profile) DO UPDATE SET published_at = EXCLUDED.published_at, "
                        "job_count = EXCLUDED.job_count, sheet_rows = EXCLUDED.sheet_rows",
                        (profile, run_start, len(rows), sheet_rows),
                    )
        except psycopg.Error as exc:
            raise NeonError(f"publish failed and was rolled back: {_safe(exc)}") from None
        return max(deleted, 0)
