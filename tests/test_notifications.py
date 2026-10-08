from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
import pytest
import respx

from jobscraper.models import MatchTier, SourceResult, SourceStatus
from jobscraper.notifications.base import Notifier, SendResult
from jobscraper.notifications.digest import (
    DigestConfig,
    build_digest,
    clean,
    due_follow_ups,
    format_job,
    run_summary,
    safe_url,
    select_jobs,
)
from jobscraper.notifications.telegram import TelegramNotifier
from jobscraper.notify import deliver_digest
from jobscraper.storage.google_sheets import GoogleSheetsStorage
from jobscraper.storage.sqlite import SQLiteStorage
from jobscraper.utils.dates import parse_user_date
from jobscraper.utils.errors import NotificationError, StorageError
from tests.helpers import make_job
from tests.test_storage import FakeWorksheet

NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)  # 06:00 EAT
AFTERNOON = datetime(2026, 10, 1, 13, 0, tzinfo=UTC)  # 16:00 EAT
TODAY = date(2026, 10, 1)
NAMES = {"himalayas": "Himalayas", "jobicy": "Jobicy"}
TOKEN = "123456789:" + "A" * 35
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
OK_RESULTS = [SourceResult(source="himalayas", status=SourceStatus.OK, found=10, new=3)]


def row(i: int = 1, **kw: str) -> dict[str, str]:
    base = {
        "job_id": f"j{i}",
        "title": f"Customer Support Specialist {i}",
        "company": "XYZ",
        "work_type": "remote",
        "remote_eligibility": "africa",
        "location": "Remote - Africa",
        "match_tier": "top",
        "match_score": "85.5",
        "skills_matched": "zendesk; ticketing; crm",
        "skills_missing": "freshdesk; live chat",
        "salary": "USD 800-1,200",
        "source": "himalayas",
        "job_url": f"https://example.com/jobs/{i}",
        "date_posted": "2026-09-29",
        "first_seen": NOW.isoformat(),
        "notified_at": "",
        "application_status": "New",
        "is_active": "TRUE",
        "recommended_action": "",
        "application_deadline": "",
    }
    base.update(kw)
    return base


class FakeNotifier(Notifier):
    def __init__(self, fail_on: int | None = None) -> None:
        self.messages: list[str] = []
        self.alerts: list[str] = []
        self.fail_on = fail_on

    def send(self, messages):
        sent = 0
        for text in messages:
            if self.fail_on is not None and len(self.messages) + 1 == self.fail_on:
                return SendResult(sent, "boom")
            self.messages.append(text)
            sent += 1
        return SendResult(sent)

    def send_alert(self, text):
        self.alerts.append(text)
        return True


# ---- formatting ----------------------------------------------------------------------------


def test_job_block_follows_the_doc_04_layout() -> None:
    block = format_job(1, row(recommended_action="Tailor CV, apply within 3 days."), TODAY, NAMES)
    assert block.splitlines() == [
        "1. Customer Support Specialist 1  [Top match 86]",
        "   Company: XYZ | Remote: open to Africa | Posted: 2 days ago",
        "   You have: Zendesk, Ticketing, CRM | Missing: Freshdesk, Live chat",
        "   Salary: USD 800-1,200 | Source: Himalayas",
        "   Next: Tailor CV, apply within 3 days.",
        "   Apply: https://example.com/jobs/1",
    ]


def test_job_block_variants() -> None:
    onsite = format_job(
        2,
        row(
            work_type="unknown",
            location="Nairobi, Kenya",
            salary="",
            skills_matched="",
            skills_missing="",
            is_repost="TRUE",
            application_deadline="2026-10-05",
        ),
        TODAY,
        NAMES,
    )
    assert (
        "Location: Nairobi, Kenya" in onsite
        and "(repost)" in onsite
        and "Salary: not listed" in onsite
    )
    assert "Deadline: 2026-10-05" in onsite and "You have" not in onsite


@pytest.mark.parametrize(
    ("posted", "text"), [("2026-10-01", "today"), ("2026-09-30", "1 day ago"), ("", "date unknown")]
)
def test_posted_text(posted: Any, text: Any) -> None:
    assert f"Posted: {text}" in format_job(1, row(date_posted=posted), TODAY, NAMES)


def test_scraped_text_is_sanitised() -> None:
    dirty = row(
        title="Agent\nSecond line\u202e\x07 " + "x" * 300,
        company="Evil\u200bCo\ttab",
        job_url="javascript:alert(1)",
    )
    block = format_job(1, dirty, TODAY, NAMES)
    assert "\u202e" not in block and "\x07" not in block and "\u200b" not in block
    assert block.count("\n") == 4 and "link unavailable" in block
    assert len(block.splitlines()[0]) < 180 and "\u2026" in block.splitlines()[0]
    assert clean("a  \n b") == "a b" and safe_url("https://x.com/a b") is None
    assert safe_url("https://x.com/a") == "https://x.com/a"


# ---- selection -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"match_tier": "weak"},
        {"match_tier": ""},
        {"notified_at": "2026-09-30T06:00:00+00:00"},
        {"application_status": "Applied"},
        {"application_status": "Ignored"},
        {"is_active": "FALSE"},
        {"application_deadline": "2026-09-30"},
        {"match_tier": "potential", "first_seen": (NOW - timedelta(days=3)).isoformat()},
    ],
)
def test_rows_that_are_not_notified(overrides: Any) -> None:
    assert select_jobs([row(**overrides)], TODAY, NOW, DigestConfig()) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"application_status": ""},
        {"match_tier": "strong"},
        {"application_deadline": "2026-10-01"},
        {
            "first_seen": (NOW - timedelta(days=10)).isoformat()
        },  # old Top is still unsent, so still sent
        {"match_tier": "potential", "first_seen": ""},
    ],
)
def test_rows_that_are_notified(overrides: Any) -> None:
    assert len(select_jobs([row(**overrides)], TODAY, NOW, DigestConfig())) == 1


def test_order_and_potential_cap() -> None:
    rows = [
        row(1, match_tier="strong", match_score="80"),
        row(2, match_score="86"),
        row(3, match_score="90"),
    ]
    rows += [row(10 + i, match_tier="potential", match_score=str(50 + i)) for i in range(7)]
    picked = [r["job_id"] for r in select_jobs(rows, TODAY, NOW, DigestConfig())]
    assert picked[:3] == ["j3", "j2", "j1"]
    assert picked[3:] == ["j16", "j15", "j14", "j13", "j12"]  # the five best Potential only


# ---- splitting -----------------------------------------------------------------------------


def test_many_jobs_split_into_messages_of_ten_without_repeats() -> None:
    rows = [row(i, match_score=str(90 - i * 0.1)) for i in range(25)]
    digest = build_digest(rows, OK_RESULTS, now=NOW, source_names=NAMES)
    assert [len(b.job_ids) for b in digest.batches] == [10, 10, 5]
    assert all(len(m) <= 4096 for m in digest.messages)
    assert digest.messages[0].splitlines()[0] == "NEW CUSTOMER SUPPORT JOBS (2026-10-01, EAT) [1/3]"
    assert digest.messages[1].splitlines()[0] == "NEW CUSTOMER SUPPORT JOBS (continued) [2/3]"
    ids = [j for b in digest.batches for j in b.job_ids]
    assert ids == [f"j{i}" for i in range(25)] and len(set(ids)) == 25
    text = "\n".join(digest.messages)
    assert [f"\n{n}. " in "\n" + text for n in (1, 10, 11, 25)] == [True] * 4
    assert "RUN:" in digest.messages[-1] and all("RUN:" not in m for m in digest.messages[:-1])


def test_long_messages_split_by_size() -> None:
    rows = [row(i, recommended_action="Tailor the CV carefully. " * 20) for i in range(12)]
    cfg = DigestConfig(body_limit=900, jobs_per_message=100)
    digest = build_digest(rows, OK_RESULTS, now=NOW, source_names=NAMES, config=cfg)
    assert len(digest.batches) > 3 and all(len(m) <= 1000 for m in digest.messages)
    assert sorted(j for b in digest.batches for j in b.job_ids) == sorted(
        f"j{i}" for i in range(12)
    )


# ---- follow-ups ----------------------------------------------------------------------------


def applied(i: int, **kw: str) -> dict[str, str]:
    return row(i, application_status="Applied", notified_at="x", **kw)


def due_ids(rows):
    return [r["job_id"] for r, _ in due_follow_ups(rows, TODAY, DigestConfig())[0]]


def test_follow_up_is_seven_days_after_applied_unless_overridden() -> None:
    rows = [
        applied(1, applied_on="2026-09-24"),  # exactly 7 days
        applied(
            2, applied_on="2026-09-28", follow_up_date="2026-10-01"
        ),  # the owner's own date wins
        applied(3, applied_on="2026-09-30"),  # due 7 Oct
        applied(4, applied_on="2026-09-20", follow_up_date="2026-10-09"),  # own date is later
        applied(5, applied_on="24/09/2026"),  # day-first dates
        applied(6, applied_on="2026-09-20"),  # overdue
        applied(7),  # no date at all
        row(8, application_status="Interview", applied_on="2026-09-01"),
    ]
    assert due_ids(rows) == ["j1", "j2", "j5", "j6"]


def test_follow_up_reminded_once_per_due_date() -> None:
    rows = [
        applied(1, applied_on="2026-09-24", follow_up_reminded_on="2026-10-01"),
        applied(2, applied_on="2026-09-24", follow_up_reminded_on="2026-09-25"),  # date moved later
        applied(3, applied_on="2026-09-10", follow_up_reminded_on="2026-09-17"),
    ]
    assert due_ids(rows) == ["j2"]


def test_unreadable_dates_are_reported_not_ignored() -> None:
    rows = [
        applied(1, applied_on="soon"),
        applied(2, applied_on="2026-09-24", follow_up_date="whenever"),
    ]
    assert due_follow_ups(rows, TODAY, DigestConfig())[1] == 2
    text = build_digest(rows, OK_RESULTS, now=NOW, source_names=NAMES).messages[0]
    assert "NOTE: 2 applied job(s)" in text


def test_follow_up_section_text() -> None:
    text = build_digest(
        [applied(1, applied_on="2026-09-24", company="ABC Bank", title="Customer Care Rep")],
        OK_RESULTS,
        now=NOW,
        source_names=NAMES,
    ).messages[0]
    assert "FOLLOW-UPS DUE TODAY\n- ABC Bank, Customer Care Rep (applied 7 days ago)" in text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-09-24", date(2026, 9, 24)),
        ("24/09/2026", date(2026, 9, 24)),
        ("24 Sep 2026", date(2026, 9, 24)),
        ("Sep 24, 2026", date(2026, 9, 24)),
        ("46289", date(2026, 9, 24)),
        ("soon", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_user_date(text: Any, expected: Any) -> None:
    assert parse_user_date(text) == expected


# ---- run line, empty digests, reports -------------------------------------------------------


def test_run_summary_lines() -> None:
    results = [
        SourceResult(source="himalayas", status=SourceStatus.OK, found=20, new=5, excluded=3),
        SourceResult(source="greenhouse", status=SourceStatus.OK, found=3, new=1),
        SourceResult(source="jobicy", status=SourceStatus.DEGRADED, found=0, new=0),
        SourceResult(source="weworkremotely", status=SourceStatus.BLOCKED, found=0),
        SourceResult(source="adzuna", status=SourceStatus.SKIPPED, error="missing key"),
    ]
    assert run_summary(results, NAMES) == (
        "RUN: 2 sources ok, 1 degraded (Jobicy: 0 results), 1 blocked (weworkremotely), "
        "23 found, 6 new, 3 excluded"
    )


def test_empty_digest_only_in_the_morning_or_when_something_is_wrong() -> None:
    morning = build_digest([], OK_RESULTS, now=NOW, source_names=NAMES)
    assert len(morning.batches) == 1 and morning.messages[0].startswith(
        "NO NEW MATCHING JOBS (2026-10-01, EAT)"
    )
    assert build_digest([], OK_RESULTS, now=AFTERNOON, source_names=NAMES).batches == []
    bad = [SourceResult(source="jobicy", status=SourceStatus.FAILED)]
    assert len(build_digest([], bad, now=AFTERNOON, source_names=NAMES).batches) == 1
    assert (
        len(
            build_digest(
                [applied(1, applied_on="2026-09-24")], OK_RESULTS, now=AFTERNOON, source_names=NAMES
            ).batches
        )
        == 1
    )


def test_detailed_report_only_when_a_source_has_problems() -> None:
    bad = [SourceResult(source="jobicy", status=SourceStatus.BLOCKED)]
    with_report = build_digest(
        [row()], bad, now=NOW, source_names=NAMES, report_text="jobicy: blocked"
    )
    assert (
        with_report.messages[-1] == "RUN REPORT\njobicy: blocked"
        and with_report.batches[-1].job_ids == []
    )
    clean_run = build_digest(
        [row()], OK_RESULTS, now=NOW, source_names=NAMES, report_text="all fine"
    )
    assert all("RUN REPORT" not in m for m in clean_run.messages)


# ---- Telegram ------------------------------------------------------------------------------


class Clock:
    def __init__(self):
        self.sleeps: list[float] = []

    def sleep(self, s):
        self.sleeps.append(s)


@pytest.fixture
def tg():
    clock = Clock()
    return TelegramNotifier(TOKEN, "42", sleep=clock.sleep, clock=lambda: 0.0), clock


@respx.mock
def test_telegram_sends_plain_text_without_previews(tg: Any) -> None:
    notifier, _ = tg
    route = respx.post(URL).respond(200, json={"ok": True})
    assert notifier.send(["hello"]).sent == 1
    body = json.loads(route.calls.last.request.content)
    assert body == {"chat_id": "42", "text": "hello", "link_preview_options": {"is_disabled": True}}


@respx.mock
def test_telegram_waits_between_messages(tg: Any) -> None:
    notifier, clock = tg
    respx.post(URL).respond(200, json={"ok": True})
    assert notifier.send(["a", "b"]).sent == 2
    assert clock.sleeps == [pytest.approx(1.1)]


@respx.mock
def test_telegram_honours_retry_after_then_succeeds(tg: Any) -> None:
    notifier, clock = tg
    limited = httpx.Response(
        429,
        json={"ok": False, "description": "Too Many Requests", "parameters": {"retry_after": 3}},
    )
    route = respx.post(URL).mock(side_effect=[limited, httpx.Response(200, json={"ok": True})])
    assert notifier.send(["x"]).sent == 1 and route.call_count == 2 and 3.0 in clock.sleeps


@respx.mock
def test_telegram_gives_up_on_a_long_rate_limit(tg: Any) -> None:
    notifier, _ = tg
    route = respx.post(URL).respond(429, json={"ok": False, "parameters": {"retry_after": 120}})
    result = notifier.send(["x"])
    assert result.sent == 0 and "rate limited" in (result.error or "") and route.call_count == 1


@respx.mock
def test_telegram_retries_server_errors_with_backoff(tg: Any) -> None:
    notifier, clock = tg
    route = respx.post(URL).mock(
        side_effect=[httpx.Response(500), httpx.Response(502), httpx.Response(200, json={})]
    )
    assert notifier.send(["x"]).sent == 1 and route.call_count == 3
    assert clock.sleeps == [2.0, 4.0]


@respx.mock
def test_telegram_fails_after_three_server_errors(tg: Any) -> None:
    notifier, _ = tg
    route = respx.post(URL).respond(500)
    result = notifier.send(["x"])
    assert result.sent == 0 and "after 3 attempts" in (result.error or "") and route.call_count == 3


@pytest.mark.parametrize("status", [400, 401, 403, 404])
@respx.mock
def test_telegram_permanent_errors_are_not_retried_and_never_leak_the_token(
    tg: Any, status: Any
) -> None:
    notifier, _ = tg
    route = respx.post(URL).respond(status, json={"ok": False, "description": "Unauthorized"})
    result = notifier.send(["x"])
    assert route.call_count == 1 and str(status) in (result.error or "")
    assert TOKEN not in (result.error or "") and "bot123" not in (result.error or "")


@respx.mock
def test_telegram_network_errors_do_not_leak_the_token(tg: Any) -> None:
    notifier, _ = tg
    respx.post(URL).mock(side_effect=httpx.ReadTimeout(f"timeout for {URL}"))
    result = notifier.send(["x"])
    assert (
        result.sent == 0
        and "ReadTimeout" in (result.error or "")
        and TOKEN not in (result.error or "")
    )


@respx.mock
def test_telegram_stops_at_the_first_failure(tg: Any) -> None:
    notifier, _ = tg
    respx.post(URL).mock(
        side_effect=[httpx.Response(200, json={}), httpx.Response(400, json={"description": "bad"})]
    )
    result = notifier.send(["one", "two", "three"])
    assert result.sent == 1 and result.error


@respx.mock
def test_telegram_alert_is_prefixed_and_capped(tg: Any) -> None:
    notifier, _ = tg
    route = respx.post(URL).respond(200, json={})
    assert notifier.send_alert("x" * 5000) is True
    text = json.loads(route.calls.last.request.content)["text"]
    assert text.startswith("ALERT: ") and len(text) == len("ALERT: ") + 1000


def test_telegram_config_errors_and_repr() -> None:
    with pytest.raises(NotificationError):
        TelegramNotifier.from_env({"TELEGRAM_BOT_TOKEN": TOKEN})
    notifier = TelegramNotifier(TOKEN, "42")
    assert TOKEN not in repr(notifier) and TOKEN not in str(notifier)


# ---- delivery and marking ---------------------------------------------------------------------


def stored(n: int, **kw) -> SQLiteStorage:
    storage = SQLiteStorage()
    storage.append_jobs(
        [
            make_job(
                job_id=f"j{i}",
                source_job_id=str(i),
                job_url=f"https://x.com/{i}",
                match_tier=MatchTier.TOP,
                match_score=90 - i * 0.1,
                title=f"Support Agent {i}",
                **kw,
            )
            for i in range(n)
        ]
    )
    return storage


def run_once(storage, notifier, now=NOW):
    digest = build_digest(storage.load_rows(), OK_RESULTS, now=now, source_names=NAMES)
    return digest, deliver_digest(digest, notifier, storage, now, TODAY)


def test_nothing_is_ever_sent_twice() -> None:
    storage, notifier = stored(3), FakeNotifier()
    _, first = run_once(storage, notifier)
    assert first.sent == 1 and first.jobs_marked == 3
    assert all(r["notified_at"] for r in storage.load_rows())
    digest, second = run_once(storage, notifier, AFTERNOON)
    assert digest.batches == [] and second.sent == 0 and len(notifier.messages) == 1


def test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part() -> None:
    storage, notifier = stored(12), FakeNotifier(fail_on=2)
    _, first = run_once(storage, notifier)
    assert (first.sent, first.total, first.jobs_marked, first.error) == (1, 2, 10, "boom")
    assert sum(1 for r in storage.load_rows() if r["notified_at"]) == 10

    retry = FakeNotifier()
    digest, second = run_once(storage, retry, AFTERNOON)
    assert second.sent == 1 and second.jobs_marked == 2
    assert sorted(j for b in digest.batches for j in b.job_ids) == ["j10", "j11"]
    assert "1. Support Agent 10" in retry.messages[0]  # numbering restarts, titles are not repeated
    assert all(r["notified_at"] for r in storage.load_rows())


def test_follow_up_reminders_are_marked_and_not_repeated() -> None:
    storage = stored(1)
    storage.set_user_cell("j0", "application_status", "Applied")
    storage.set_user_cell("j0", "applied_on", "2026-09-24")
    notifier = FakeNotifier()
    digest, outcome = run_once(storage, notifier)
    assert outcome.follow_ups_marked == 1 and "FOLLOW-UPS DUE TODAY" in notifier.messages[0]
    assert storage.get_row("j0")["follow_up_reminded_on"] == "2026-10-01"
    assert (
        storage.get_row("j0")["application_status"] == "Applied"
    )  # the owner's columns are untouched
    again = build_digest(storage.load_rows(), OK_RESULTS, now=AFTERNOON, source_names=NAMES)
    assert again.batches == []


def test_marking_failure_is_reported() -> None:
    class BrokenStorage(SQLiteStorage):
        def update_jobs(self, updates):
            raise StorageError("sheet unreachable")

    storage = BrokenStorage()
    storage.append_jobs([make_job(match_tier=MatchTier.TOP, match_score=90)])
    _, outcome = run_once(storage, FakeNotifier())
    assert (
        outcome.sent == 1
        and outcome.jobs_marked == 0
        and "unreachable" in (outcome.mark_error or "")
    )


def test_sheet_marks_rows_appended_in_the_same_run() -> None:
    ws = FakeWorksheet()
    storage = GoogleSheetsStorage(ws)
    storage.append_jobs([make_job(match_tier=MatchTier.TOP, match_score=90)])
    digest = build_digest(storage.load_rows(), OK_RESULTS, now=NOW, source_names=NAMES)
    outcome = deliver_digest(
        digest, FakeNotifier(), storage, NOW, TODAY
    )  # no load_index call in between
    headers = ws.values[0]
    assert outcome.jobs_marked == 1 and ws.values[1][headers.index("notified_at")].startswith(
        "2026-10-01"
    )
    assert ws.values[1][headers.index("application_status")] == "New"
