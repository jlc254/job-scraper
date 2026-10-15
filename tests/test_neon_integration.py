"""Integration tests for the Neon writer.

Skipped unless TEST_DATABASE_URL points at a THROWAWAY Postgres (for example a local container
in CI). Never point it at your Neon dev or production branch: the tests drop and recreate tables.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from jobscraper.publish import COLUMNS, PublishSettings, build_rows  # noqa: E402
from jobscraper.storage.neon import NeonError, NeonPublisher  # noqa: E402
from tests.test_publish import make_row  # noqa: E402

DSN = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL not set")

MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "001_init.sql"
SETTINGS = PublishSettings()
RUN1 = datetime.now(UTC).replace(microsecond=0)


@pytest.fixture(autouse=True)
def fresh_schema():
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS jobs, publish_meta, schema_migrations CASCADE")
        conn.execute(MIGRATION.read_text())
    yield


def rows(*ids: str, now: datetime):
    sheet = [
        make_row(job_id=i, job_url=f"https://example.com/{i}", first_seen=now.isoformat())
        for i in ids
    ]
    return build_rows(sheet, SETTINGS, now)


def count() -> int:
    with psycopg.connect(DSN) as conn:
        return conn.execute("SELECT count(*) FROM jobs").fetchone()[0]


def test_publish_twice_is_idempotent():
    plan = rows("a", "b", "c", now=RUN1)
    with NeonPublisher(DSN) as pub:
        pub.replace_jobs(COLUMNS, plan.rows, run_start=RUN1, sheet_rows=3)
    run2 = RUN1 + timedelta(hours=10)
    plan2 = rows("a", "b", "c", now=run2)
    with NeonPublisher(DSN) as pub:
        deleted = pub.replace_jobs(COLUMNS, plan2.rows, run_start=run2, sheet_rows=3)
    assert count() == 3 and deleted == 0


def test_removed_row_is_deleted_on_next_publish():
    with NeonPublisher(DSN) as pub:
        pub.replace_jobs(COLUMNS, rows("a", "b", now=RUN1).rows, run_start=RUN1, sheet_rows=2)
    run2 = RUN1 + timedelta(hours=10)
    with NeonPublisher(DSN) as pub:
        deleted = pub.replace_jobs(COLUMNS, rows("a", now=run2).rows, run_start=run2, sheet_rows=2)
    assert deleted == 1 and count() == 1


def test_failure_rolls_back_and_keeps_previous_rows():
    with NeonPublisher(DSN) as pub:
        pub.replace_jobs(COLUMNS, rows("a", "b", now=RUN1).rows, run_start=RUN1, sheet_rows=2)
    run2 = RUN1 + timedelta(hours=10)
    bad = rows("c", now=run2).rows
    bad[0]["job_url"] = "not-a-url"  # violates the CHECK constraint mid-transaction
    with NeonPublisher(DSN) as pub, pytest.raises(NeonError):
        pub.replace_jobs(COLUMNS, bad, run_start=run2, sheet_rows=1)
    with psycopg.connect(DSN) as conn:
        ids = sorted(r[0] for r in conn.execute("SELECT job_id FROM jobs"))
    assert ids == ["a", "b"]


def test_types_round_trip():
    with NeonPublisher(DSN) as pub:
        pub.replace_jobs(COLUMNS, rows("a", now=RUN1).rows, run_start=RUN1, sheet_rows=1)
    with psycopg.connect(DSN) as conn:
        skills, score, version, hit = conn.execute(
            "SELECT skills_matched, match_score, scoring_version, "
            "search @@ plainto_tsquery('english','customer') FROM jobs"
        ).fetchone()
    assert skills == ["excel", "english"] and float(score) == 68.0 and version == 2 and hit
