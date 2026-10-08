from __future__ import annotations

import re
from typing import Any

import pytest

from jobscraper.models import JobUpdate
from jobscraper.pipeline import dedupe_jobs, persist
from jobscraper.storage.google_sheets import GoogleSheetsStorage, col_letter
from jobscraper.storage.rows import JOBS_HEADERS, job_to_row
from jobscraper.storage.sqlite import SQLiteStorage
from jobscraper.utils.errors import StorageError
from tests.helpers import T0, later, make_job


class FakeSpreadsheet:
    """Applies deleteDimension requests in order, like the real batchUpdate."""

    def __init__(self, sheet: FakeWorksheet) -> None:
        self.sheet = sheet
        self.calls = 0
        self.other_requests: list[dict[str, Any]] = []  # formatting and freezing

    def batch_update(self, body: dict[str, Any]) -> None:
        self.calls += 1
        for request in body["requests"]:
            if "deleteDimension" not in request:
                self.other_requests.append(request)
                continue
            rng = request["deleteDimension"]["range"]
            assert rng["dimension"] == "ROWS" and rng["sheetId"] == self.sheet.id
            del self.sheet.values[rng["startIndex"] : rng["endIndex"]]


class FakeWorksheet:
    """In-memory stand-in for gspread.Worksheet."""

    id = 0

    def __init__(self, values: list[list[str]] | None = None, title: str = "Sheet") -> None:
        self.values = values or []
        self.title = title
        self.fail_appends = 0
        self.spreadsheet = FakeSpreadsheet(self)

    def row_values(self, index: int) -> list[str]:
        return list(self.values[index - 1]) if len(self.values) >= index else []

    def resize(self, rows: int | None = None, cols: int | None = None) -> None:
        if rows is not None:
            del self.values[rows:]
            while len(self.values) < rows:
                self.values.append([])
        if cols is not None:
            self.values = [row[:cols] for row in self.values]

    def get_all_values(self) -> list[list[str]]:
        return [list(r) for r in self.values]

    def update(self, *, range_name: str, values: list[list[Any]], **kw: Any) -> None:
        if range_name == "A1":  # a full matrix from the top left corner
            while len(self.values) < len(values):
                self.values.append([])
            for index, row in enumerate(values):
                self.values[index] = list(row)
            return
        assert range_name.startswith("A1:")
        if not self.values:
            self.values = [[]]
        self.values[0] = list(values[0])

    def append_rows(self, values: list[list[Any]], **kw: Any) -> None:
        if self.fail_appends:
            self.fail_appends -= 1
            raise RuntimeError("quota")
        self.values.extend([list(map(str, r)) for r in values])

    def batch_update(self, data: list[dict[str, Any]], **kw: Any) -> None:
        for item in data:
            m = re.fullmatch(r"([A-Z]+)(\d+)", item["range"])
            assert m, item["range"]
            col = 0
            for ch in m.group(1):
                col = col * 26 + ord(ch) - 64
            row = int(m.group(2)) - 1
            self.values[row][col - 1] = item["values"][0][0]


class FakeBook:
    """Stand-in for a gspread Spreadsheet: lists tabs and can add new ones."""

    def __init__(self) -> None:
        self.sheets: list[FakeWorksheet] = []

    def worksheets(self) -> list[FakeWorksheet]:
        return list(self.sheets)

    def add_worksheet(self, title: str, rows: int, cols: int) -> FakeWorksheet:
        ws = FakeWorksheet(title=title)
        ws.id = len(self.sheets) + 1  # a distinct id per tab, so formatting requests can be checked
        self.sheets.append(ws)
        return ws


def test_col_letter():
    assert [col_letter(i) for i in (1, 26, 27, 52, 53)] == ["A", "Z", "AA", "AZ", "BA"]


def test_job_to_row_escapes_formulas_and_sets_status():
    row = job_to_row(make_job(title="=HYPERLINK(\"http://evil\")", company="@x"))
    assert row["title"].startswith("'=") and row["company"].startswith("'@")
    assert row["application_status"] == "New"
    assert set(JOBS_HEADERS) >= set(row)


@pytest.fixture(params=["sqlite", "sheets"])
def storage(request):
    if request.param == "sqlite":
        return SQLiteStorage()
    return GoogleSheetsStorage(FakeWorksheet(), FakeWorksheet())


def user_cell_setter(storage):
    if isinstance(storage, SQLiteStorage):
        return lambda job_id, col, val: storage.set_user_cell(job_id, col, val)
    ws: FakeWorksheet = storage._jobs  # noqa: SLF001
    def setter(job_id, col, val):
        headers = ws.values[0]
        for row in ws.values[1:]:
            if row[headers.index("job_id")] == job_id:
                row[headers.index(col)] = val
    return setter


def read_cell(storage, job_id, col):
    if isinstance(storage, SQLiteStorage):
        return (storage.get_row(job_id) or {}).get(col)
    ws: FakeWorksheet = storage._jobs  # noqa: SLF001
    headers = ws.values[0]
    for row in ws.values[1:]:
        if row[headers.index("job_id")] == job_id:
            return row[headers.index(col)]
    return None


def test_rerun_is_idempotent_and_never_touches_user_columns(storage, tmp_path):
    job = make_job()
    out1 = dedupe_jobs([job], storage, T0, [])
    persist(storage, out1, tmp_path)
    assert len(out1.new_jobs) == 1

    user_cell_setter(storage)(job.job_id, "application_status", "Applied")
    user_cell_setter(storage)(job.job_id, "notes", "called them")

    other_source = make_job(job_id="zz", source="jobicy", source_job_id="j9", job_url="https://acme.com/c/9")
    out2 = dedupe_jobs([job, other_source], storage, later(1), [])
    persist(storage, out2, tmp_path)
    assert out2.new_jobs == [] and len(out2.updates) == 1

    assert read_cell(storage, job.job_id, "application_status") == "Applied"
    assert read_cell(storage, job.job_id, "notes") == "called them"
    assert read_cell(storage, job.job_id, "last_seen").startswith("2026-10-02")
    assert read_cell(storage, job.job_id, "job_url") == "https://acme.com/c/9"
    assert len(storage.load_index()) == 1


def test_update_of_protected_column_is_refused(storage):
    storage.append_jobs([make_job()])
    storage.load_index()
    for column in ("application_status", "notes", "title", "match_score"):
        with pytest.raises(StorageError):
            storage.update_jobs([JobUpdate(job_id="job-a", fields={column: "x"})])


def test_sheet_handles_reordered_and_extra_columns():
    ws = FakeWorksheet([["notes", "title", "my_custom", "job_id", "application_status"]])
    store = GoogleSheetsStorage(ws)
    store.append_jobs([make_job()])
    headers = ws.values[0]
    assert headers[:5] == ["notes", "title", "my_custom", "job_id", "application_status"]
    assert "match_score" in headers  # missing columns are appended, never reordered
    row = dict(zip(headers, ws.values[1], strict=False))
    assert row["title"] == "Customer Support Agent" and row["job_id"] == "job-a"
    assert row["notes"] == "" and row["my_custom"] == "" and row["application_status"] == "New"


def test_persist_retries_then_saves_locally(tmp_path):
    ws = FakeWorksheet()
    ws.fail_appends = 2
    store = GoogleSheetsStorage(ws)
    out = dedupe_jobs([make_job()], store, T0, [])
    with pytest.raises(StorageError, match="saved to"):
        persist(store, out, tmp_path)
    assert list(tmp_path.glob("unsaved-*.json"))


def test_persist_recovers_after_one_failure(tmp_path):
    ws = FakeWorksheet()
    ws.fail_appends = 1
    store = GoogleSheetsStorage(ws)
    out = dedupe_jobs([make_job()], store, T0, [])
    persist(store, out, tmp_path)
    assert len(ws.values) == 2 and not list(tmp_path.glob("unsaved-*.json"))
