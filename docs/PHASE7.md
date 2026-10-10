# Phase 7 notes: monitoring and reliability hardening

New: `utils/health.py`, `retention.py`, `source_check.py`, `runtime_settings.py`, a per-source Health tab,
CLI commands `sources check`, `cleanup`, `health`, `recover`, tests for all of it, `config/settings.example.yaml`.
Changed: `run` now judges every source against its history, alerts on trouble, cleans up once a day and
fails when no source returned data. The workflow keeps debugging files and pings the dead-man's switch on failure.

## What you will see, and when

| Situation | What happens |
|---|---|
| A source has a bad run (failed, blocked, rate limited, partial, degraded) | Recorded in Health. The digest RUN line names it and a RUN REPORT message follows. No separate alert |
| A source returns 0 results but normally returns 3+ (median of its last 7 good runs) | Marked `degraded` ("0 results (usually about N)"). Needs 3 earlier runs of history |
| A source returns under 20% of its usual count, when usual is 10+ | Marked `degraded` (drift: usually a layout or API change) |
| More than 30% of records fail to parse | `degraded`, and a sanitized sample of up to 3 bad records is saved |
| Third bad run in a row | ONE combined Telegram alert "SOURCE HEALTH" with the advice for that status |
| Still broken | A reminder at the 9th, 15th, 21st... bad run. Nothing in between, so you are not nagged every run |
| Source healthy again after 3+ bad runs | One "healthy again" message |
| No source returned data at all | The run FAILS (exit 5): Actions turns red, Telegram alert, Healthchecks `/fail` |
| Saving to the Sheet fails twice | Exit 3, new jobs saved to `output/unsaved-*.json` (kept as an Actions artifact for 7 days), Telegram alert |
| No successful run for about 27 hours | Healthchecks.io alarms (needs HEALTHCHECK_URL) |

Quiet afternoon runs stay silent while a source stays broken. The RUN line still shows it in the next digest.
Thresholds are in `config/settings.yaml` (optional, see the example). Tune there after a few weeks of real runs.

## New commands

    python main.py sources check                         # live check of enabled+verified sources, nothing saved
    python main.py sources check --sources adzuna        # also works for a PENDING source, to verify it
    python main.py sources check --save-fixtures tests/fixtures/captured
    python main.py health                                # per source: last status, bad streak, usual count
    python main.py cleanup --dry-run                     # then without --dry-run
    python main.py recover                               # re-add jobs from output/unsaved-*.json

`sources check` fetches ONE page per source, reports reachability, robots.txt (HTML sources) and how many
records parse. Sources marked blocked, alerts-only or retired are never contacted, even if you name them.

### This replaces the synthetic fixtures
Until now the fixtures were my guesses. Run from your own shell (it needs the network):

    python main.py sources check --save-fixtures tests/fixtures/captured

It saves one real response per source with emails and phone numbers removed and only the first 5 records.
READ each file before committing. `tests/test_captured_fixtures.py` then runs every adapter against its real
response, so a changed API shape fails a test instead of silently dropping jobs. Fix any adapter it reports.

## Retention (runs once a day, on the morning run, or by hand)
- Jobs: deleted 60 days after first_seen, but only while application_status is New. Anything you moved past
  New (Saved, Applied, Interview, Offer, Rejected, Ignored) is kept.
- Jobs not seen for 7 days are marked inactive (never notified again).
- Excluded rows, Runs rows and Health rows are kept 30 days.
- Safety net: a plan that would delete more than half the job rows (when over 20) is refused. A first_seen
  value that cannot be read is never treated as old.

## Suggested changes to the runbook (doc 12)
Add to the alerts table:
- "SOURCE HEALTH alert (third bad run)": follow the advice in the message. Blocked: disable, log, use email alerts.
- Source `degraded` with "0 results" or drift: run `sources check`, compare with the site in a browser, update the
  adapter and the captured fixture.
- Run exits red with "no source returned data": check the Actions log (network, expired config, every site down).
- Failed run with an `unsaved-jobs` artifact: download it into `output/` and run `python main.py recover`.
Add to the weekly routine: `python main.py health` (falling counts show up as a lower "usual" figure).

## Doc 08 pre-deployment checklist

| Item | Status |
|---|---|
| Repo private; `.gitignore` covers `.env`, credential JSON, `output/`, `logs/` | Ignore patterns tested. Private: YOU confirm in GitHub |
| gitleaks passes on full history | YOU run `gitleaks detect --source . --log-opts="--all"` before the first push |
| Redaction test: a fake key never appears in logs | Tested (API key in a query string, Telegram token in a URL). The token pattern had a bug I fixed: it missed a token inside `/bot<token>/`. |
| SSRF tests (private IP, redirect to internal host, non-HTTPS) | Tested in Phase 2 |
| Formula-injection test on Sheet writes | Tested |
| Sheet shared only with the service account and you | YOU confirm |
| Secrets set in GitHub, none in code | Names tested against the workflow. Values: YOU |
| `pip-audit` clean, Actions pinned | Runs in CI. Pinning: `scripts/pin_actions.py` |
| No `print`, bare `except`, `eval`, `shell=True` in source; every HTTP client has a timeout | Tested by scanning the code |

## Decisions to confirm
1. `Ignored` jobs are kept forever, because the runbook says "unless you moved them past New". Say so if you want Ignored purged at 60 days.
2. A live listing older than 60 days that you never touched is deleted and may come back as a new job. The `too_old` filter (posted over 30 days ago) stops most of these re-entering, for sources that give a posting date.
3. Exit code 5 (no source returned data) makes the run red. A run where sources respond but are `degraded` stays green, because the problem is contained and alerted.
4. The Jobs, Health, Runs and Excluded tabs are created automatically if missing; required headers are added without reordering existing columns.
5. Skipped sources (disabled, unverified, missing key) are not recorded in Health and never trigger alerts.

## Testing status, honestly
No sandbox here can reach PyPI, so I built throwaway stand-ins for pydantic, rapidfuzz, httpx, respx and feedparser
and ran every test that does not need real HTTP: 243 passed and 1 failed (the deliberate "actions not pinned yet" check).
65 tests were not executed because they need the real libraries, and 12 are skipped by design (lock files not generated, no captured fixtures yet). That run covered scoring, dedupe, digest, storage, retention, health, workflows and settings, and it
is what found the token-redaction bug. NOT executed: the HTTP client, Telegram client, adapters, runner, `sources check`,
resilience suite and the end-to-end CLI tests (they need real httpx and respx), and the stand-ins are more lenient than
real pydantic. Run `pytest` on your machine and send me the failures.
