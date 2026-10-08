from __future__ import annotations

import logging
from typing import Any

import pytest

from jobscraper.output import safe_cell
from jobscraper.parsers.text import (
    html_to_text,
    parse_date,
    safe_http_url,
    truncate,
    unescape_then_text,
)
from jobscraper.utils.logging import RedactionFilter
from jobscraper.utils.pii import scrub_pii


@pytest.mark.parametrize(
    ("raw", "expected_absent"),
    [
        ("mail jane@example.com now", "jane@example.com"),
        ("call +254 712 345 678 today", "712"),
        ("call 0712345678 today", "0712345678"),
        ("call (415) 555-1234", "555-1234"),
    ],
)
def test_pii_removed(raw: Any, expected_absent: Any) -> None:
    assert expected_absent not in scrub_pii(raw)


@pytest.mark.parametrize(
    "text", ["Salary 20000-30000 per month", "KES 80,000 - 120,000", "3 to 5 years"]
)
def test_pii_keeps_salaries(text: Any) -> None:
    assert scrub_pii(text) == text


def test_html_to_text_strips_tags_and_scripts() -> None:
    assert (
        html_to_text("<p>Hello <b>you</b></p><script>alert(1)</script><p>Bye</p>")
        == "Hello you\n\nBye"
    )


def test_unescape_then_text() -> None:
    assert unescape_then_text("&lt;p&gt;Hi &amp;amp; bye&lt;/p&gt;") == "Hi & bye"


def test_truncate() -> None:
    assert truncate("abc", 0) == ""
    assert truncate("short", 100) == "short"
    assert len(truncate("word " * 100, 50)) <= 51


def test_safe_http_url() -> None:
    assert safe_http_url("https://a.com/x") == "https://a.com/x"
    assert safe_http_url("javascript:alert(1)") is None
    assert safe_http_url("//a.com") is None
    assert safe_http_url(None) is None


def test_parse_date_variants() -> None:
    assert str(parse_date(1790000000)) == "2026-09-21"
    assert str(parse_date(1790000000000)) == "2026-09-21"
    assert str(parse_date("2026-09-28T10:00:00Z")) == "2026-09-28"
    assert parse_date("garbage") is None
    assert parse_date(True) is None


@pytest.mark.parametrize("value", ["=SUM(A1)", "+1", "-2", "@cmd"])
def test_csv_formula_prefix(value: Any) -> None:
    assert safe_cell(value).startswith("'")


def test_redaction_filter() -> None:
    flt = RedactionFilter(secrets=["supersecretvalue"])
    record = logging.LogRecord(
        "x", logging.INFO, "f", 1, "GET https://a.com/p?app_key=abc123 supersecretvalue", None, None
    )
    flt.filter(record)
    assert "abc123" not in record.msg
    assert "supersecretvalue" not in record.msg
