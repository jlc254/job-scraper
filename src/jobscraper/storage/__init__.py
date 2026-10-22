"""Storage backends (doc 04). Backends never score, filter or notify.

This package intentionally does NOT import backends eagerly: ``neon`` and
``postgres`` need ``psycopg`` which is only installed in the project venv /
CI. Importing them here would break ``pytest`` collection for SQLite-only
tests on any interpreter without that extra. Import backends directly
(``from jobscraper.storage.sqlite import SQLiteStorage``) or via this
package's lazy ``__getattr__``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # for type-checkers only; resolved lazily at runtime below
    from jobscraper.storage.google_sheets import GoogleSheetsStorage
    from jobscraper.storage.neon import NeonError, NeonPublisher
    from jobscraper.storage.postgres import PostgresStorage
    from jobscraper.storage.sqlite import SQLiteStorage

__all__ = [
    "GoogleSheetsStorage",
    "NeonPublisher",
    "NeonError",
    "PostgresStorage",
    "SQLiteStorage",
]

_LAZY: dict[str, str] = {
    "GoogleSheetsStorage": "jobscraper.storage.google_sheets",
    "NeonPublisher": "jobscraper.storage.neon",
    "NeonError": "jobscraper.storage.neon",
    "PostgresStorage": "jobscraper.storage.postgres",
    "SQLiteStorage": "jobscraper.storage.sqlite",
}


def __getattr__(name: str) -> object:
    """Lazily import backends so ``import jobscraper.storage`` stays light."""
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    module = importlib.import_module(_LAZY[name])
    value = getattr(module, name)
    globals()[name] = value  # cache for next access
    return value
