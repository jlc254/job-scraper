"""Contract tests against REAL saved responses (doc 11).

Create the fixtures with `python main.py sources check --save-fixtures tests/fixtures/captured`.
Each file is named after its source id. With no files this module does nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import respx

import jobscraper.scrapers  # noqa: F401
from jobscraper.scrapers.registry import get_adapter_class

CAPTURED = sorted((Path(__file__).parent / "fixtures" / "captured").glob("*.*"))


@pytest.mark.parametrize("path", CAPTURED or [None])
def test_adapter_still_understands_the_real_response(path, make_client, source_config, now):
    if path is None:
        pytest.skip("no captured fixtures yet: run `sources check --save-fixtures tests/fixtures/captured`")
    adapter_cls = get_adapter_class(path.stem)
    assert adapter_cls is not None, f"no adapter registered for {path.stem}"
    config = source_config(max_pages=1, boards=[{"token": "captured", "name": "Captured Co"}])
    adapter = adapter_cls(config, now)
    body = path.read_bytes()
    with respx.mock:
        for host in adapter.allowed_hosts:
            respx.route(host=host).respond(200, content=body)
        raws = adapter.fetch(make_client(set(adapter.allowed_hosts)))
    mapped = [j for j in (adapter.to_job(r) for r in raws) if j is not None]
    assert raws, "the real response contained no records"
    assert len(mapped) / len(raws) >= 0.7, f"only {len(mapped)} of {len(raws)} records mapped: the format changed"
