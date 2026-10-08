"""Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data Studio).

Looker's Google Sheets connector reads ONE worksheet per data source, wants one value type per
column and a single header row, and reads dates only if the cells are real Sheets dates. So each
table here becomes its own `Dash_*` tab, rebuilt on every run, with dates written as Sheets date
serial numbers and a date number format applied to those columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from jobscraper.utils.cells import safe_cell

_SHEETS_EPOCH = date(1899, 12, 30)


@dataclass
class DashboardTable:
    name: str  # the tab name, for example Dash_Jobs
    headers: list[str]
    rows: list[list[Any]]  # str, int, float, bool, date, naive datetime (Africa/Nairobi) or None
    formats: dict[str, str] = field(default_factory=dict)  # header -> "date" or "datetime"


def sheet_serial(value: date | datetime) -> int | float:
    """Days since 1899-12-30, the day-count Google Sheets uses for dates and times."""
    if isinstance(value, datetime):
        delta = value - datetime(_SHEETS_EPOCH.year, _SHEETS_EPOCH.month, _SHEETS_EPOCH.day)
        return round(delta.total_seconds() / 86400, 6)
    return (value - _SHEETS_EPOCH).days


def sheet_value(value: Any) -> Any:
    """A cell value for a RAW Sheets write: blanks as "", dates as serials, text made formula-safe."""
    if value is None:
        return ""
    if isinstance(value, bool):  # before int: bool is an int subclass
        return value
    if isinstance(value, date):  # datetime is a date subclass, handled by sheet_serial
        return sheet_serial(value)
    if isinstance(value, int | float):
        return value
    return safe_cell(value)


def csv_value(value: Any) -> Any:
    """A cell value for a CSV export: ISO dates, true/false, formula-safe text."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, int | float):
        return value
    return safe_cell(value)
