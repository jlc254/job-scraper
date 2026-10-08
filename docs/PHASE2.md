# Phase 2 notes

Run on your machine (Python 3.12+):

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.txt          # locked, hashed versions (run scripts/lock.sh first)
    pytest
    ruff check . && ruff format --check . && mypy src
    cp config/sources.example.yaml config/sources.yaml   # or merge into your existing file
    python main.py run --dry-run --no-notify

Before relying on it:
1. Replace tests/fixtures/himalayas.json and greenhouse.json with your saved REAL responses
   (personal data removed), fix any field names the tests expose, and set one real board
   token under `greenhouse.boards`.
2. Check Himalayas pagination (doc 02 says cursor, the adapter assumes offset/limit).
3. Reconcile config/sources.example.yaml with your real sources.yaml. The schema accepts extra keys.
4. Replace the example terms_url values with the pages you actually reviewed.

Not in Phase 2 (by plan): dedupe across sources (Phase 3), storage (Phase 3), scoring and
hard filters (Phase 4), Telegram (Phase 5), sources check / retention (Phase 7).
`prefilter.py` is a temporary off-topic filter that Phase 4 replaces.
