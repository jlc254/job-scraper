# Phase 8 notes: Looker Studio dashboard

Scope chosen: the Looker Studio dashboard from doc 10's optional extras. Email-alert ingestion
(O4) and LLM-assisted extraction are NOT in this phase.

New: `dashboard.py`, `models/dashboard.py`, `docs/looker-studio.md`, CLI command `dashboard`, Sheet writing of six
`Dash_*` tabs, a `dashboard` mode for the workflow's manual run, `tests/test_dashboard.py`.
Changed: every `run` refreshes the Dash_* tabs at the end (skip with `--no-dashboard`).

## What I could and could not do
- I CANNOT create the Looker Studio report for you. Reports cannot be imported from a file, and creating one needs your
  Google login. `docs/looker-studio.md` is an exact build spec instead: six data sources, field types, seven calculated
  fields and six pages with the fields for each chart. Expect about 30 to 45 minutes of clicking.
- I CAN make the data fit Looker Studio, which is where dashboards on a raw Sheet usually go wrong. I checked Google's own
  guidance before designing this: a Sheets data source reads ONE worksheet, columns must hold one type, the header must be one
  row, dates must be real Sheets dates, and changed columns need a manual "Refresh fields". Hence the tab-per-source design.

## Setup (once)
1. Get the Dash_* tabs into the Sheet: Actions, daily-run, Run workflow, mode `dashboard` (or `python main.py dashboard`).
2. Follow `docs/looker-studio.md`, steps 1 to 4.
3. Keep the report private (see below).

## What was verified, and what was not
- From Google's documentation (read today): Sheets connector options, one worksheet per source, same-type columns, single
  header row, Owner's credentials, 15-minute default freshness with 1h/4h/12h options, manual refresh, "Refresh fields" after column changes.
- From Google's support page: date fields must be formatted with the Date data type in the Sheet.
- NOT verified: that every date column is auto-detected as a date in your account. The guide has the fix if one is not.
  The calculated-field formulas follow Google's function list but have not been run in a live report.
- Offline run across the whole project (stand-ins for pydantic and others): 267 passed, 1 failed (the deliberate "actions not
  pinned yet" check), 71 not executed because they need real httpx, respx or feedparser. That includes 20 new dashboard tests covering the table builders, typed Sheet writing, formatting, shrinking tables,
  blank handling, formula safety, CSV export and the CLI command. The real gspread calls (`resize`, `update`, `batch_update`) have
  not run against a real Sheet. First real run: check the Dash_Jobs tab by eye (dates formatted, header frozen).

## Privacy
The tabs contain job titles, companies, links, your scores and your application statuses and dates. They do not contain notes,
descriptions or alternate URLs. A Looker Studio report set to "anyone with the link" would expose your whole job search. Keep it
shared with your own account only.

## Decisions to confirm
1. The six Dash_* tabs are fully rebuilt each run (about 12 Sheets writes, well inside quota). Edits to them are lost.
2. All dashboard dates and times are Africa/Nairobi.
3. `follow_up_due` follows the same rule as the Telegram reminders and uses `digest.follow_up_days` from settings.yaml.
4. `dashboard --export DIR` writes CSVs. I do not recommend uploading those instead of using the Sheet: Looker Studio's CSV
   upload reportedly mis-reads dates, and the Sheet connector needs no re-upload.
5. Linking API / report templates: once your report exists you can make it copyable, but that needs a finished template first.

## Still optional (not built)
- Email-alert ingestion for LinkedIn, Indeed and Glassdoor through an Apps Script in your own Google account (decision O4).
- LLM-assisted extraction (off by default).
- A Streamlit or Next.js dashboard, only if Looker Studio stops being enough.
