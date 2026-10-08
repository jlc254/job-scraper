"""Google Sheets backend (D3). Columns are addressed by header name, never position.

The worksheets are injected so tests can use a fake. `from_env` builds the real
ones from a service account that has Editor access to the one Sheet and no
project roles (doc 08).
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Protocol, cast

from jobscraper.models import ExcludedRecord, Job, JobUpdate, SourceRun, StoredJob
from jobscraper.models.dashboard import DashboardTable, sheet_value
from jobscraper.storage.base import Storage
from jobscraper.storage.rows import (
    EXCLUDED_HEADERS,
    HEALTH_HEADERS,
    JOBS_HEADERS,
    RUNS_HEADERS,
    excluded_to_row,
    job_to_row,
    row_to_stored,
    source_run_to_row,
    validate_update,
)
from jobscraper.utils.cells import safe_cell
from jobscraper.utils.errors import StorageError

log = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class Worksheet(Protocol):
    """The slice of gspread.Worksheet this module uses."""

    def get_all_values(self) -> list[list[str]]: ...
    def update(self, *, range_name: str, values: list[list[Any]], **kwargs: Any) -> Any: ...
    def append_rows(self, values: list[list[Any]], **kwargs: Any) -> Any: ...
    def batch_update(self, data: list[dict[str, Any]], **kwargs: Any) -> Any: ...

    @property
    def id(self) -> int: ...

    @property
    def spreadsheet(self) -> Any: ...


def col_letter(index: int) -> str:
    """1-based column index to A1 letters."""
    letters = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


class GoogleSheetsStorage(Storage):
    def __init__(
        self,
        jobs_ws: Worksheet,
        runs_ws: Worksheet | None = None,
        excluded_ws: Worksheet | None = None,
        health_ws: Worksheet | None = None,
        book: Any | None = None,
    ) -> None:
        self._jobs = jobs_ws
        self._runs = runs_ws
        self._excluded = excluded_ws
        self._health = health_ws
        self._book = book  # the spreadsheet itself, needed to create the Dash_* tabs
        self._row_numbers: dict[str, int] = {}

    @classmethod
    def from_env(cls, environ: dict[str, str]) -> GoogleSheetsStorage:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:  # pragma: no cover
            raise StorageError("gspread and google-auth are required for Sheets storage") from exc
        encoded = environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "")
        sheet_id = environ.get("GOOGLE_SHEET_ID", "")
        if not encoded or not sheet_id:
            raise StorageError("GOOGLE_SERVICE_ACCOUNT_JSON_B64 and GOOGLE_SHEET_ID are required")
        try:
            info = json.loads(base64.b64decode(encoded))
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)  # type: ignore[no-untyped-call]
            book = gspread.authorize(creds).open_by_key(sheet_id)

            def tab(title: str) -> Worksheet:  # helper tabs are created if missing; Jobs must exist
                try:
                    return cast(Worksheet, book.worksheet(title))
                except gspread.WorksheetNotFound:
                    return cast(Worksheet, book.add_worksheet(title=title, rows=1000, cols=20))

            return cls(
                cast(Worksheet, book.worksheet("Jobs")),
                tab("Runs"),
                tab("Excluded"),
                tab("Health"),
                book=book,
            )
        except Exception as exc:  # noqa: BLE001 - third-party errors vary; message stays generic
            raise StorageError(f"could not open the Sheet ({type(exc).__name__})") from exc

    # -- reading ------------------------------------------------------------

    def _read(self) -> tuple[list[str], list[list[str]]]:
        values = self._jobs.get_all_values()
        if not values:
            return [], []
        return [h.strip() for h in values[0]], values[1:]

    def _ensure_headers(self, headers: list[str], wanted: list[str], ws: Worksheet) -> list[str]:
        """Add any missing columns at the end of the header row. Never reorders."""
        missing = [h for h in wanted if h not in headers]
        if not missing:
            return headers
        merged = [*headers, *missing]
        # Keyword arguments: gspread 5 and 6 order the positional ones differently.
        ws.update(
            range_name=f"A1:{col_letter(len(merged))}1", values=[merged], value_input_option="RAW"
        )
        log.info("added missing sheet columns", extra={"ctx": {"count": len(missing)}})
        return merged

    def load_index(self) -> list[StoredJob]:
        headers, rows = self._read()
        self._row_numbers = {}
        stored: list[StoredJob] = []
        for offset, cells in enumerate(rows):
            record = {h: (cells[i] if i < len(cells) else "") for i, h in enumerate(headers) if h}
            item = row_to_stored(record)
            if item is None:
                continue
            stored.append(item)
            self._row_numbers[item.job_id] = offset + 2  # header is row 1
        return stored

    # -- writing ------------------------------------------------------------

    def append_jobs(self, jobs: list[Job]) -> None:
        if not jobs:
            return
        headers, _ = self._read()
        headers = self._ensure_headers(headers, JOBS_HEADERS, self._jobs)
        values = []
        for job in jobs:
            row = job_to_row(job)
            values.append([row.get(h, "") for h in headers])
        try:
            self._jobs.append_rows(values, value_input_option="RAW")
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"append failed ({type(exc).__name__})") from exc

    def update_jobs(self, updates: list[JobUpdate]) -> None:
        if not updates:
            return
        headers, rows = self._read()
        # Row numbers are read fresh: rows appended earlier in this run have none cached.
        id_col = headers.index("job_id") if "job_id" in headers else -1
        row_numbers = {
            cells[id_col]: offset + 2
            for offset, cells in enumerate(rows)
            if id_col >= 0 and len(cells) > id_col and cells[id_col]
        }
        data: list[dict[str, Any]] = []
        for update in updates:
            validate_update(update.fields)
            row_number = row_numbers.get(update.job_id)
            if row_number is None:
                continue
            for column, value in update.fields.items():
                if column not in headers:
                    continue
                cell = f"{col_letter(headers.index(column) + 1)}{row_number}"
                data.append({"range": cell, "values": [[safe_cell(value)]]})
        if not data:
            return
        try:
            self._jobs.batch_update(data, value_input_option="RAW")
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"update failed ({type(exc).__name__})") from exc

    def _append_dicts(
        self, ws: Worksheet, wanted: list[str], rows: list[dict[str, str]], what: str
    ) -> None:
        if not rows:
            return
        values = ws.get_all_values()
        headers = [h.strip() for h in values[0]] if values else []
        headers = self._ensure_headers(headers, wanted, ws)
        try:
            ws.append_rows(
                [[safe_cell(r.get(h, "")) for h in headers] for r in rows], value_input_option="RAW"
            )
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"{what} append failed ({type(exc).__name__})") from exc

    def append_run(self, row: dict[str, str]) -> None:
        if self._runs is not None:
            self._append_dicts(self._runs, RUNS_HEADERS, [row], "run log")

    def append_excluded(self, records: list[ExcludedRecord]) -> None:
        if self._excluded is not None:
            self._append_dicts(
                self._excluded,
                EXCLUDED_HEADERS,
                [excluded_to_row(r) for r in records],
                "excluded log",
            )

    def load_excluded_ids(self) -> set[str]:
        if self._excluded is None:
            return set()
        values = self._excluded.get_all_values()
        if not values or "job_id" not in values[0]:
            return set()
        col = [h.strip() for h in values[0]].index("job_id")
        return {row[col] for row in values[1:] if len(row) > col and row[col]}

    def load_rows(self) -> list[dict[str, str]]:
        headers, rows = self._read()
        return [
            {h: (cells[i] if i < len(cells) else "") for i, h in enumerate(headers) if h}
            for cells in rows
        ]

    # -- Phase 7: health history, generic tables, deletion ------------------------

    def append_source_runs(self, runs: list[SourceRun]) -> None:
        if self._health is not None:
            self._append_dicts(
                self._health, HEALTH_HEADERS, [source_run_to_row(r) for r in runs], "health log"
            )

    def _worksheet(self, table: str) -> Worksheet:
        sheet = {
            "jobs": self._jobs,
            "excluded": self._excluded,
            "runs": self._runs,
            "health": self._health,
        }.get(table)
        if sheet is None:
            raise StorageError(f"the {table} tab is not configured")
        return sheet

    @staticmethod
    def _values(ws: Worksheet) -> tuple[list[str], list[list[str]]]:
        values = ws.get_all_values()
        return ([h.strip() for h in values[0]], values[1:]) if values else ([], [])

    def load_table(self, table: str) -> list[dict[str, str]]:
        headers, rows = self._values(self._worksheet(table))
        return [
            {h: (cells[i] if i < len(cells) else "") for i, h in enumerate(headers) if h}
            for cells in rows
        ]

    def delete_rows(self, table: str, key_column: str, keys: set[str]) -> int:
        """One batched request, highest rows first so earlier row numbers stay valid."""
        ws = self._worksheet(table)
        headers, rows = self._values(ws)
        if key_column not in headers or not keys:
            return 0
        col = headers.index(key_column)
        numbers = [
            offset + 2
            for offset, cells in enumerate(rows)
            if len(cells) > col and cells[col] in keys
        ]
        if not numbers:
            return 0
        ranges: list[list[int]] = []
        for number in sorted(numbers, reverse=True):
            if ranges and ranges[-1][0] == number + 1:
                ranges[-1][0] = number
            else:
                ranges.append([number, number])
        requests = [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": ws.id,
                        "dimension": "ROWS",
                        "startIndex": first - 1,
                        "endIndex": last,
                    }
                }
            }
            for first, last in ranges
        ]
        try:
            ws.spreadsheet.batch_update({"requests": requests})
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"delete failed ({type(exc).__name__})") from exc
        self._row_numbers = {}
        return len(numbers)

    # -- Phase 8: dashboard tabs --------------------------------------------------

    def write_dashboard(self, tables: list[DashboardTable]) -> None:
        """Rewrite each Dash_* tab completely. Looker Studio reads one worksheet per data source.

        Dates are written as Sheets serial numbers and the date columns get a date number format,
        because Looker only reads a column as a date if the cells are real Sheets dates. Blank
        values are written as "" so a shrinking table never leaves stale cells behind.
        """
        if self._book is None:
            raise StorageError("the spreadsheet handle is needed to write dashboard tabs")
        try:
            existing = {ws.title: ws for ws in self._book.worksheets()}
            for table in tables:
                ws = existing.get(table.name)
                created = ws is None
                if ws is None:
                    ws = self._book.add_worksheet(
                        title=table.name, rows=max(len(table.rows) + 1, 2), cols=len(table.headers)
                    )
                matrix = [list(table.headers)] + [
                    [sheet_value(cell) for cell in row] for row in table.rows
                ]
                previous_header = [] if created else [h.strip() for h in ws.row_values(1)]
                ws.resize(
                    rows=max(len(matrix), 2), cols=len(table.headers)
                )  # also drops leftover rows
                ws.update(range_name="A1", values=matrix, value_input_option="RAW")
                if (
                    created or previous_header != table.headers
                ):  # formats persist, so only on a new layout
                    self._format_dashboard_tab(ws, table)
        except StorageError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"dashboard write failed ({type(exc).__name__})") from exc

    @staticmethod
    def _format_dashboard_tab(ws: Worksheet, table: DashboardTable) -> None:
        patterns = {"date": "yyyy-mm-dd", "datetime": "yyyy-mm-dd hh:mm"}
        requests: list[dict[str, Any]] = [
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": ws.id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }
            }
        ]
        for header, kind in table.formats.items():
            if header not in table.headers or kind not in patterns:
                continue
            column = table.headers.index(header)
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": ws.id,
                            "startRowIndex": 1,
                            "startColumnIndex": column,
                            "endColumnIndex": column + 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "DATE_TIME" if kind == "datetime" else "DATE",
                                    "pattern": patterns[kind],
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat",
                    }
                }
            )
        ws.spreadsheet.batch_update({"requests": requests})
