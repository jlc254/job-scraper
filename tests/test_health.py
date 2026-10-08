from typing import Any
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jobscraper.models import SourceResult, SourceRun, SourceStatus
from jobscraper.storage.rows import row_to_source_run, source_run_to_row
from jobscraper.storage.sqlite import SQLiteStorage
from jobscraper.utils.health import (
    HealthSettings,
    alert_text,
    evaluate_health,
    format_health_table,
    needs_attention,
    no_source_succeeded,
    sanitize_value,
    save_sample,
    to_source_runs,
)

NOW = datetime(2026, 10, 1, 3, 0, tzinfo=timezone.utc)
NAMES = {"jobicy": "Jobicy", "himalayas": "Himalayas"}
S = SourceStatus


def history(source: str, *entries: tuple[SourceStatus, int]) -> list[SourceRun]:
    """entries are oldest first, one run per 12 hours before NOW."""
    runs = []
    for i, (status, found) in enumerate(reversed(entries), start=1):
        runs.append(
            SourceRun(
                run_id=f"r{i}",
                started_utc=NOW - timedelta(hours=12 * i),
                source=source,
                status=status,
                found=found,
            )
        )
    return runs


def result(
    source: str = "jobicy", status: SourceStatus = S.OK, found: int = 10, **kw
) -> SourceResult:
    return SourceResult(source=source, status=status, found=found, **kw)


def kinds(findings):
    return [f.kind for f in findings]


# ---- volume alarms ----------------------------------------------------------------------------


def test_sudden_zero_is_degraded() -> None:
    res = result(found=0)
    findings = evaluate_health([res], history("jobicy", *[(S.OK, 20)] * 5), names=NAMES)
    assert res.status is S.DEGRADED and "0 results" in res.error
    assert kinds(findings) == ["zero_results", "new_problem"]


def test_no_volume_alarm_without_enough_history_or_a_busy_baseline() -> None:
    assert (
        evaluate_health(
            [r := result(found=0)], history("jobicy", (S.OK, 20), (S.OK, 20)), names=NAMES
        )
        == []
    )
    assert r.status is S.OK
    quiet = history("jobicy", *[(S.OK, 1)] * 6)  # a source that normally returns almost nothing
    assert evaluate_health([r2 := result(found=0)], quiet, names=NAMES) == [] and r2.status is S.OK


def test_collapse_in_volume_is_drift_but_a_dip_is_not() -> None:
    base = history("jobicy", *[(S.OK, 20)] * 6)
    dip, collapse = result(found=5), result(found=3)
    assert evaluate_health([dip], base, names=NAMES) == [] and dip.status is S.OK
    findings = evaluate_health([collapse], base, names=NAMES)
    assert collapse.status is S.DEGRADED and kinds(findings)[0] == "drift"


def test_baseline_ignores_failed_runs() -> None:
    runs = history("jobicy", *[(S.OK, 20)] * 4, (S.FAILED, 0), (S.FAILED, 0))
    res = result(found=0)
    evaluate_health([res], runs, names=NAMES)
    assert res.status is S.DEGRADED  # the two failed zeros did not drag the baseline down


# ---- three strikes, fatigue control, recovery -----------------------------------------------------


def run_streak(previous_bad: int, status: SourceStatus = S.FAILED):
    runs = (
        history("jobicy", (S.OK, 20), *[(S.FAILED, 0)] * previous_bad)
        if previous_bad
        else history("jobicy", (S.OK, 20))
    )
    res = result(status=status, found=0, error="boom")
    return kinds(evaluate_health([res], runs, names=NAMES))


def test_alerts_follow_the_streak_without_nagging() -> None:
    assert run_streak(0) == ["new_problem"]
    assert run_streak(1) == []  # second bad run: only the digest RUN line
    assert run_streak(2) == ["three_strikes"]  # third bad run in a row
    assert [run_streak(n) for n in (3, 4, 5, 6, 7)] == [[], [], [], [], []]
    assert run_streak(8) == ["reminder"]  # streak 9: one reminder, then quiet again
    assert run_streak(14) == ["reminder"]


def test_three_strikes_message_has_advice_per_status() -> None:
    for status, hint in (
        (S.BLOCKED, "Do not work around"),
        (S.DEGRADED, "sources check"),
        (S.RATE_LIMITED, "frequency"),
        (S.FAILED, "Actions log"),
    ):
        res = result(status=status, found=0)
        findings = evaluate_health(
            [res], history("jobicy", (S.FAILED, 0), (S.FAILED, 0)), names=NAMES
        )
        text = alert_text(findings)
        assert text and "3 runs in a row" in text and hint in text and "Jobicy" in text


def test_recovery_is_announced_once() -> None:
    findings = evaluate_health(
        [result(found=12)], history("jobicy", (S.OK, 12), *[(S.BLOCKED, 0)] * 4), names=NAMES
    )
    assert kinds(findings) == ["recovered"] and "healthy again after 4 bad runs" in alert_text(
        findings
    )
    assert (
        evaluate_health(
            [result(found=12)],
            history("jobicy", (S.OK, 12), (S.BLOCKED, 0), (S.OK, 12)),
            names=NAMES,
        )
        == []
    )


def test_partial_runs_count_as_bad_and_skipped_runs_are_ignored() -> None:
    runs = history("jobicy", (S.OK, 5), (S.PARTIAL, 5), (S.SKIPPED, 0), (S.PARTIAL, 5))
    assert kinds(evaluate_health([result(status=S.PARTIAL)], runs, names=NAMES)) == [
        "three_strikes"
    ]
    assert evaluate_health([result(status=S.SKIPPED, found=0)], runs, names=NAMES) == []


def test_sources_are_judged_independently() -> None:
    runs = history("jobicy", (S.FAILED, 0), (S.FAILED, 0)) + history("himalayas", *[(S.OK, 20)] * 3)
    out = evaluate_health(
        [result("jobicy", S.FAILED, 0), result("himalayas", found=20)], runs, names=NAMES
    )
    assert [(f.source, f.kind) for f in out] == [("jobicy", "three_strikes")]


def test_alert_text_combines_and_is_capped() -> None:
    assert alert_text([]) is None and not needs_attention([])
    many = [
        type("F", (), {"kind": "reminder", "message": "x" * 200, "source": "s"})()
        for _ in range(10)
    ]
    assert len(alert_text(many)) <= 950
    only_new = evaluate_health([result(status=S.FAILED, found=0)], [], names=NAMES)
    assert alert_text(only_new) is None and needs_attention(only_new)


def test_no_source_succeeded() -> None:
    assert no_source_succeeded([]) and no_source_succeeded([result(status=S.SKIPPED)])
    assert no_source_succeeded(
        [result(status=S.FAILED), result("b", S.BLOCKED), result("c", S.RATE_LIMITED)]
    )
    assert not no_source_succeeded([result(status=S.FAILED), result("b", S.DEGRADED)])
    assert not no_source_succeeded([result(status=S.OK), result("b", S.FAILED)])


# ---- recording and reading history -----------------------------------------------------------------


def test_to_source_runs_skips_skipped_and_caps_errors() -> None:
    runs = to_source_runs(
        [result(error="e" * 500, new=3, excluded=1), result("x", S.SKIPPED)], "r1", NOW
    )
    assert (
        len(runs) == 1 and len(runs[0].error) == 200 and runs[0].new == 3 and runs[0].excluded == 1
    )


def test_source_run_rows_round_trip_and_bad_rows_are_skipped() -> None:
    run = SourceRun(
        run_id="r1", started_utc=NOW, source="jobicy", status=S.DEGRADED, found=4, error="=evil"
    )
    row = source_run_to_row(run)
    assert row["key"] == "r1:jobicy" and row["error"].startswith("'=")
    back = row_to_source_run(row)
    assert back is not None and (back.status, back.found, back.started_utc) == (S.DEGRADED, 4, NOW)
    assert row_to_source_run({**row, "status": "nonsense"}) is None
    assert row_to_source_run({**row, "started_utc": "never"}) is None


def test_storage_keeps_history_newest_first_and_deletes_by_key() -> None:
    storage = SQLiteStorage()
    storage.append_source_runs(history("jobicy", (S.OK, 1), (S.FAILED, 0), (S.OK, 3)))
    assert [r.found for r in storage.load_source_runs()] == [3, 0, 1]
    assert storage.delete_rows("health", "key", {"r2:jobicy"}) == 1
    assert [r.found for r in storage.load_source_runs()] == [3, 1]


def test_health_table() -> None:
    text = format_health_table(history("jobicy", (S.OK, 20), (S.FAILED, 0), (S.FAILED, 0)), NAMES)
    row = text.splitlines()[1].split()
    assert row[0] == "Jobicy" and row[1] == "failed" and row[2] == "2"
    assert format_health_table([], NAMES) == "No run history yet."


# ---- sanitized samples ---------------------------------------------------------------------------


def test_sample_values_are_sanitised() -> None:
    dirty = {
        "email": "jane@example.com",
        "phone": "+254 712 345 678",
        "url": "https://x.com/j/1?token=abc#frag",
        "long": "y" * 500,
        "items": list(range(20)),
        "nested": {"a": {"b": {"c": {"d": {"e": "deep"}}}}},
        "ok": 7,
        "obj": object(),
    }
    out = sanitize_value(dirty)
    assert "jane@example.com" not in str(out) and "712" not in out["phone"]
    assert out["url"] == "https://x.com/j/1" and len(out["long"]) <= 201
    assert out["items"] == [0, 1, 2, 3, 4] and out["ok"] == 7 and out["obj"] == "object"
    assert out["nested"]["a"]["b"]["c"]["d"] == "..."


def test_save_sample_writes_at_most_three_records(tmp_path: Any) -> None:
    path = save_sample(
        "jobicy",
        [{"n": i, "mail": "a@b.co"} for i in range(6)],
        "parse failures",
        tmp_path / "samples",
        NOW,
    )
    text = path.read_text(encoding="utf-8")
    assert (
        path.name == "jobicy-20261001-030000.json"
        and "a@b.co" not in text
        and text.count('"n"') == 3
    )


def test_default_settings_match_the_plan() -> None:
    cfg = HealthSettings()
    assert (cfg.strikes, cfg.reminder_every, cfg.min_history) == (3, 6, 3)