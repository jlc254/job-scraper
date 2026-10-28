# Neon publish: wiring it into the repo

Files in this drop and where they go (same paths as in the repo):

| File | Purpose |
|---|---|
| `migrations/001_init.sql` | Tables, indexes, generated search column |
| `migrations/002_roles.sql` | Grants for `jobs_publisher` and `jobs_reader` |
| `src/jobscraper/publish.py` | Pure rules: Sheet rows to typed rows, retention, guard |
| `src/jobscraper/publish_cli.py` | `run_publish()`, exit codes, dry run |
| `src/jobscraper/storage/neon.py` | Write-only Neon refresh in one transaction |
| `tests/test_publish.py` | Unit tests (no network, no psycopg) |
| `tests/test_neon_integration.py` | Needs `TEST_DATABASE_URL` (throwaway Postgres only) |

## What I could not see (please check)
- `cli.py` and the `Storage` code were not in the documents, so the CLI glue below is a template, and `load_rows` must return the Jobs tab as `list[dict[str, str]]` (open item O7).
- `dashboard.py` helpers are not imported. `publish.py` has its own small converters with the same rules (semicolon lists, `FALSE` means inactive, text numbers). Swap them in later if you promote the originals to a shared module.
- Tests for `publish.py` were smoke-checked here with a stand-in for pydantic, but **pytest, pydantic and psycopg could not be installed in my sandbox**, so run `pytest` yourself. The Neon writer and integration tests have **not been executed**.

## 1. Dependencies and config
`requirements.in`: add `psycopg[binary]` (pin an exact version at least two weeks old), then `scripts/lock.sh` and commit both lock files.

`.env.example`: add an empty line `NEON_DATABASE_URL_PUBLISHER=`

`config/settings.yaml` (optional, all defaults shown):
```yaml
publish:
  max_age_days: 30
  hide_statuses: [Ignored, Rejected]
  keep_statuses: [Applied, Interview, Offer]
  guard_min_existing: 10
  guard_min_ratio: 0.5
```
Hook `PublishSettings.model_validate(raw.get("publish", {}))` into your existing settings loader, so the block is validated at startup.

## 2. CLI glue (adapt names to your `cli.py`)
```python
# subparser
p = sub.add_parser("publish", help="Refresh the Neon copy from the Sheet")
p.add_argument("--dry-run", action="store_true")
p.add_argument("--force", action="store_true", help="Skip the row-count collapse guard")


# handler
def cmd_publish(args) -> int:
    settings = load_settings(args.settings)  # your existing loader
    storage = open_google_sheets_storage()  # your existing constructor
    return run_publish(
        load_rows=lambda: storage.load_table("jobs"),
        dsn=os.environ.get("NEON_DATABASE_URL_PUBLISHER"),
        settings=settings.publish,
        dry_run=args.dry_run,
        force=args.force,
    )
```
Add the new variable to the log redaction list: the URL contains a password.

## 3. Workflow (`.github/workflows/daily.yml`)
After the `run` step and the dead-man's-switch ping:
```yaml
      - name: Publish to Neon
        if: ${{ !cancelled() && (github.event_name == 'schedule' || inputs.mode == 'normal' || inputs.mode == 'publish') }}
        env:
          GOOGLE_SERVICE_ACCOUNT_JSON_B64: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON_B64 }}
          GOOGLE_SHEET_ID_JULIET: ${{ secrets.GOOGLE_SHEET_ID_JULIET }}
          GOOGLE_SHEET_ID_JUMALAW98: ${{ secrets.GOOGLE_SHEET_ID_JUMALAW98 }}
          NEON_DATABASE_URL_PUBLISHER: ${{ secrets.NEON_DATABASE_URL_PUBLISHER }}
        run: python main.py publish
```
- Add `publish` to the `mode` options of `workflow_dispatch`, and make the `run` step skip when `inputs.mode == 'publish'`.
- `!cancelled()` lets publish run even when `run` exited 4 (Telegram failed) because the Sheet is still up to date. Remove it if you prefer publish to be skipped after any failure.
- Update the Phase 6 security test that lists which steps may see secrets, so it allows exactly this one step and nothing more.
- Do this **last** (doc 13, order of work step 6).

## 4. Order of work
1. Neon project, `dev` branch, create roles `jobs_publisher` and `jobs_reader` in the console.
2. `psql "$DATABASE_URL_OWNER" -f migrations/001_init.sql` then `002_roles.sql` on **dev** (direct, non-pooled string).
3. `pytest tests/test_publish.py`, then `python main.py publish --dry-run` against the real Sheet. Compare the counts with the Sheet by hand.
4. Run the integration tests against a local Postgres: `TEST_DATABASE_URL=postgresql://... pytest tests/test_neon_integration.py`.
5. `python main.py publish` against dev with the publisher URL, twice. Compare 3 jobs row by row.
6. Role checks in `psql`: as `jobs_reader`, `INSERT`, `UPDATE`, `DELETE`, `DROP TABLE` must all fail. As `jobs_publisher`, `CREATE TABLE` and `DROP TABLE` must fail.
7. Point the dashboard's `DATABASE_URL` (reader, pooled) at dev and check the list loads.
8. Production branch, migrate it, add the GitHub secret, add the workflow step, watch three scheduled runs.

## 5. Doc updates
- Doc 00 decisions log: add D19 to D27 from docs 13 and 14.
- `README.md` index: add rows for docs 13 and 14.
- Doc 09 secrets table: add `NEON_DATABASE_URL_PUBLISHER`.
- Doc 12 runbook: add "Publish failed (exit 6): read the guard message, check the Sheet, rerun `workflow_dispatch` mode `publish`".

## Behavior notes
- Weak jobs are published (the dashboard hides them by default).
- Unknown `match_tier` values become `unscored`, so a stray value can never trip the CHECK constraint and roll back the whole run.
- Zero publishable rows is refused even with `--force` when Neon already holds 10 or more. `--force` only skips the "below 50%" collapse check.
- Duplicate `job_id`s in the Sheet keep the later row and are counted as `duplicate id`.
- Exit codes: `0` ok, `2` missing secret, `3` Sheet read failed, `6` Neon failed or the guard refused.
