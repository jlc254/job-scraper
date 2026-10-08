# Phase 3 notes

New: normalization (parsers/names.py, normalize.py), dedupe + merge (utils/dedupe.py),
storage (storage/base, sqlite, google_sheets, rows), pipeline.py, Jobicy and We Work Remotely adapters.

Run locally without Google (SQLite):

    pip install -r requirements-dev.txt && pytest
    python main.py run --storage sqlite --no-notify          # writes output/jobs.db, run it twice: second run adds 0
    python main.py run --dry-run --no-notify                 # no storage at all

Run against your Sheet (tabs Jobs, Runs; shared with the service account as Editor):

    export GOOGLE_SHEET_ID=... GOOGLE_SERVICE_ACCOUNT_JSON_B64=$(base64 -w0 key.json)
    python main.py run --no-notify

Decisions and deviations to confirm:
- Sheet gets 4 extra system columns beyond doc 05: source_job_id, all_urls, description_excerpt,
  is_repost. Dedupe needs them to read state back. Missing columns are appended to the header
  automatically; your column order and extra columns are respected.
- Existing rows only ever get: last_seen, is_active, all_urls, job_url, salary, application_deadline.
  Anything else raises StorageError (tested). New rows start with application_status = New.
- Doc 05's "level noise removal" means "Senior X" and "X" at one company and scope share a fingerprint.
  Same-company, same-scope distinct seniorities will merge (both URLs are kept). Say if you want
  seniority kept in the fingerprint.
- Storage failure: retry once, then the new jobs are saved to output/unsaved-<ts>.json and the run
  exits 3. Automatic resend of those files next run is not built yet (suggest Phase 7).
- Not added: Adzuna (Kenya coverage O2 still unrecorded), Kenyan boards (still pending).
- The Excluded tab and Inbox tab are Phase 4 / Phase 8. Create the Runs tab now; headers are added for you.
- Fixtures for jobicy.json and weworkremotely.xml are synthetic placeholders: replace with real saved responses.
