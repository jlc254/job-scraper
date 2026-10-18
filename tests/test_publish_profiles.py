"""Publish is scoped per profile: one profile can never delete or block another (doc 15)."""

from __future__ import annotations

import sys
import types
from datetime import UTC, datetime

import pytest

from jobscraper.publish import COLUMNS, PublishSettings, build_rows
from jobscraper.publish_cli import run_publish

NOW = datetime(2026, 10, 16, 9, tzinfo=UTC)


def row(i: int) -> dict[str, str]:
    return {
        "job_id": f"j{i}",
        "title": "T",
        "company": "C",
        "job_url": f"https://x/{i}",
        "first_seen": "2026-10-15T08:00:00+00:00",
        "match_tier": "top",
        "match_score": "90",
    }


class FakeNeonError(RuntimeError):
    pass


@pytest.fixture
def neon(monkeypatch):
    """A fake storage.neon so these tests need neither psycopg nor a database."""
    state: dict = {"rows": {}, "pruned": None}

    class Publisher:
        def __init__(self, dsn): ...
        def __enter__(self):
            return self

        def __exit__(self, *a): ...
        def count_jobs(self, profile):
            return len(state["rows"].get(profile, []))

        def replace_jobs(self, columns, rows, *, profile, run_start, sheet_rows):
            assert all(r["profile"] == profile for r in rows)
            state["rows"][profile] = [r["job_id"] for r in rows]
            return 0

        def prune_profiles(self, keep):
            state["pruned"] = list(keep)
            return 0

    module = types.ModuleType("jobscraper.storage.neon")
    module.NeonError, module.NeonPublisher = FakeNeonError, Publisher
    monkeypatch.setitem(sys.modules, "jobscraper.storage.neon", module)
    return state


def test_profile_is_first_column_and_written_on_every_row():
    plan = build_rows([row(1), row(2)], PublishSettings(), NOW, "community")
    assert COLUMNS[0] == "profile"
    assert {r["profile"] for r in plan.rows} == {"community"}


def test_same_job_id_in_two_profiles_stays_separate(neon):
    loaders = {"support": lambda: [row(1)], "community": lambda: [row(1)]}
    assert (
        run_publish(
            loaders=loaders, dsn="x", settings=PublishSettings(), now=NOW, out=lambda _: None
        )
        == 0
    )
    assert neon["rows"] == {"support": ["j1"], "community": ["j1"]}


def test_a_collapsed_profile_is_blocked_but_the_other_still_publishes(neon):
    neon["rows"]["community"] = [f"j{i}" for i in range(20)]
    loaders = {"support": lambda: [row(i) for i in range(12)], "community": lambda: []}
    code = run_publish(
        loaders=loaders, dsn="x", settings=PublishSettings(), now=NOW, out=lambda _: None
    )
    assert code == 6
    assert len(neon["rows"]["community"]) == 20  # untouched
    assert len(neon["rows"]["support"]) == 12


def test_unreadable_sheet_never_prunes(neon):
    def broken():
        raise RuntimeError("down")

    code = run_publish(
        loaders={"support": lambda: [row(1)], "community": broken},
        dsn="x",
        settings=PublishSettings(),
        now=NOW,
        out=lambda _: None,
        prune_keep=["support", "community"],
    )
    assert code == 3 and neon["pruned"] is None


def test_partial_publish_never_prunes_but_full_publish_does(neon):
    run_publish(
        loaders={"community": lambda: [row(1)]},
        dsn="x",
        settings=PublishSettings(),
        now=NOW,
        out=lambda _: None,
    )
    assert neon["pruned"] is None
    run_publish(
        loaders={"support": lambda: [row(1)]},
        dsn="x",
        settings=PublishSettings(),
        now=NOW,
        out=lambda _: None,
        prune_keep=["support"],
    )
    assert neon["pruned"] == ["support"]
