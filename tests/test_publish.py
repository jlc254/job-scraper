"""Unit tests for publish.py and publish_cli.py (no network, no psycopg)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from jobscraper.publish import (
    COLUMNS,
    GuardError,
    PublishSettings,
    build_rows,
    check_guard,
)
from jobscraper.publish_cli import EXIT_CONFIG, EXIT_OK, EXIT_SHEET, run_publish

NOW = datetime(2026, 10, 11, 6, 0, tzinfo=UTC)  # 09:00 EAT, 2026-10-11
SETTINGS = PublishSettings()


def make_row(**overrides: str) -> dict[str, str]:
    base = {
        "job_id": "abc123def456",
        "title": "Customer Support Specialist",
        "company": "Example Co",
        "location": "Remote",
        "work_type": "remote",
        "employment_type": "",
        "remote_eligibility": "africa",
        "salary": "",
        "skills_matched": "excel; english",
        "skills_missing": "",
        "match_score": "68.0",
        "match_tier": "potential",
        "match_breakdown": json.dumps({"version": 2, "total": 68.0, "factors": {}}),
        "recommended_action": "Review gaps",
        "source": "weworkremotely",
        "job_url": "https://example.com/jobs/1",
        "date_posted": "2026-10-09",
        "application_deadline": "",
        "first_seen": "2026-10-10T03:07:00+00:00",
        "last_seen": "2026-10-11T03:07:00+00:00",
        "is_active": "TRUE",
        "is_repost": "FALSE",
        "description_excerpt": "Line one\nLine two...",
        "checklist": "",
        "application_status": "",
    }
    base.update(overrides)
    return base


def one(**overrides: str) -> dict:
    plan = build_rows([make_row(**overrides)], SETTINGS, NOW)
    assert len(plan.rows) == 1, plan.dropped
    return plan.rows[0]


def dropped(**overrides: str) -> dict[str, int]:
    plan = build_rows([make_row(**overrides)], SETTINGS, NOW)
    assert plan.rows == []
    return dict(plan.dropped)


# ---------- conversions ----------


def test_columns_match_row_keys():
    assert set(one()) == set(COLUMNS)


@pytest.mark.parametrize(
    ("raw", "expected"), [("68.0", 68.0), ("43.3", 43.3), ("", None), ("x", None), ("250", None)]
)
def test_score_parsing(raw, expected):
    assert one(match_score=raw)["match_score"] == expected


def test_skill_lists():
    row = one(skills_matched="excel; english", skills_missing="")
    assert row["skills_matched"] == ["excel", "english"]
    assert row["skills_missing"] == []


def test_breakdown_valid_and_version():
    row = one()
    assert row["match_breakdown"]["total"] == 68.0
    assert row["scoring_version"] == 2


@pytest.mark.parametrize("bad", ["", "not json", "[1, 2]"])
def test_breakdown_invalid_still_publishes(bad):
    row = one(match_breakdown=bad)
    assert row["match_breakdown"] is None and row["scoring_version"] is None


def test_booleans():
    assert one(is_active="")["is_active"] is True  # blank counts as active
    assert one(is_repost="TRUE")["is_repost"] is True
    assert one(is_repost="")["is_repost"] is False
    assert dropped(is_active="FALSE") == {"inactive": 1}


def test_formula_escape_stripped():
    row = one(title="'=SUM(A1)", company="'+Acme")
    assert row["title"] == "=SUM(A1)" and row["company"] == "+Acme"


def test_defaults_for_blanks():
    row = one(
        application_status="", work_type="", remote_eligibility="", match_tier="", location=""
    )
    assert row["application_status"] == "New"
    assert row["work_type"] == "unknown"
    assert row["remote_eligibility"] == "unclear"
    assert row["match_tier"] == "unscored"
    assert row["location"] is None


def test_unknown_tier_becomes_unscored():
    assert one(match_tier="amazing")["match_tier"] == "unscored"


def test_timestamps_are_utc():
    row = one(first_seen="2026-10-10T06:00:00+03:00")
    assert row["first_seen"] == datetime(2026, 10, 10, 3, 0, tzinfo=UTC)
    assert row["published_at"] == NOW


def test_nul_characters_removed():
    assert "\x00" not in one(description_excerpt="a\x00b")["description_excerpt"]


# ---------- drop rules ----------


@pytest.mark.parametrize("url", ["", "/jobs/5", "javascript:alert(1)", "ftp://x.com/a"])
def test_bad_urls_dropped(url):
    assert dropped(job_url=url) == {"no_url": 1}


def test_missing_required_fields_dropped():
    assert dropped(job_id="") == {"missing_field": 1}
    assert dropped(title="") == {"missing_field": 1}
    assert dropped(company="") == {"missing_field": 1}


def test_deadline_rule_uses_nairobi_date():
    assert dropped(application_deadline="2026-10-10") == {"expired": 1}
    assert (
        one(application_deadline="2026-10-11")["application_deadline"].isoformat() == "2026-10-11"
    )
    assert one(application_deadline="2026-10-12")
    # 22:30 UTC on 10 Oct is already 11 Oct in Nairobi, so a 10 Oct deadline has passed.
    late = datetime(2026, 10, 10, 22, 30, tzinfo=UTC)
    plan = build_rows([make_row(application_deadline="2026-10-10")], SETTINGS, late)
    assert plan.rows == [] and plan.dropped["expired"] == 1


def test_age_rule_and_keep_statuses():
    def seen(days: int) -> str:
        return (NOW - timedelta(days=days)).isoformat()

    assert one(first_seen=seen(29))
    assert dropped(first_seen=seen(31)) == {"too_old": 1}
    assert one(first_seen=seen(31), application_status="Applied")["application_status"] == "Applied"


@pytest.mark.parametrize("status", ["Ignored", "Rejected", "ignored"])
def test_hidden_statuses_dropped(status):
    assert dropped(application_status=status) == {"hidden_status": 1}


def test_weak_jobs_are_published():
    assert one(match_tier="weak")["match_tier"] == "weak"


def test_bad_first_seen_dropped():
    assert dropped(first_seen="yesterday") == {"bad_timestamp": 1}


def test_duplicate_ids_keep_later_row():
    plan = build_rows([make_row(title="Old"), make_row(title="New")], SETTINGS, NOW)
    assert [r["title"] for r in plan.rows] == ["New"]
    assert plan.dropped["duplicate_id"] == 1


def test_summary_text():
    plan = build_rows([make_row(), make_row(job_id="x", job_url="")], SETTINGS, NOW)
    assert plan.summary() == "Published 1, dropped 1 (1 no url)"


# ---------- guard ----------


def test_guard_zero_rows_blocked_even_with_force():
    with pytest.raises(GuardError):
        check_guard(0, 25, SETTINGS)
    with pytest.raises(GuardError):
        check_guard(0, 25, SETTINGS, force=True)


def test_guard_collapse_blocked_unless_forced():
    with pytest.raises(GuardError):
        check_guard(10, 25, SETTINGS)
    check_guard(10, 25, SETTINGS, force=True)


def test_guard_allows_exactly_half():
    check_guard(13, 25, SETTINGS)  # 13 >= 12.5
    check_guard(12, 24, SETTINGS)  # exactly 50%


# ---------- CLI runner ----------


def test_dry_run_writes_nothing_and_needs_no_dsn():
    lines: list[str] = []
    code = run_publish(
        load_rows=lambda: [make_row()],
        dsn=None,
        settings=SETTINGS,
        dry_run=True,
        now=NOW,
        out=lines.append,
    )
    assert code == EXIT_OK
    assert lines[0].startswith("Published 1")
    assert lines[-1] == "Dry run: nothing was written."


def test_sheet_read_failure_exit_code():
    def boom():
        raise OSError("quota")

    lines: list[str] = []
    assert run_publish(load_rows=boom, dsn="x", settings=SETTINGS, out=lines.append) == EXIT_SHEET
    assert "quota" not in lines[0]  # only the exception type is reported


def test_missing_secret_is_config_error():
    code = run_publish(
        load_rows=lambda: [make_row()], dsn=None, settings=SETTINGS, now=NOW, out=lambda _: None
    )
    assert code == EXIT_CONFIG
