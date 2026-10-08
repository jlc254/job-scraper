# 10. Development Plan

Rule: no phase starts until the previous phase's exit criteria are met and the owner confirms.

## Phase 1. Requirements and source research (current)
- **Objective:** Fix scope, sources and rules.
- **Files:** docs 00 to 10, config templates.
- **Work:** Owner reviews documents. Verify sources in the batch order in doc 02 and fill the verification log. Resolve O1 and O2. O3 and O5 are closed. Finish account setup (O6).
- **Testing:** Manual verification only.
- **Exit criteria (minimum bar):** at least 4 sources with `status: verified`, each with a dated log entry, a terms link and a saved fixture. Every other source is `pending`, `alerts-only` or `retired`. O2 answered. Sheet created and shared with the service account.
- **Status 1 Oct 2026:** Owner reports Batches 1 to 3 verified. Still needed to meet the bar: terms links and a saved fixture for each, and the Kenyan boards' status.
- **Expected result:** A signed-off source list with status per source.
- **Problems:** Kenyan boards may prohibit automated access, so email alerts become the route there.
- **Next:** Phase 2.

## Phase 2. Prototype with 1 to 2 permitted sources
- **Objective:** Prove the end-to-end shape on the safest sources.
- **Files:** `main.py`, `utils/http.py`, `utils/robots.py`, `scrapers/base.py`, `scrapers/himalayas.py`, `scrapers/greenhouse.py`, `models/job.py`, tests and fixtures.
- **Work:** Shared HTTP client (timeouts, retries, rate limiter, redaction). Two adapters. CLI `run --dry-run` printing to the terminal and CSV. Evaluate Scrapling as an optional parser.
- **Testing:** Contract tests on saved fixtures. Failure injection.
- **Expected result:** Real jobs from two sources printed and saved to CSV.
- **Problems:** Endpoint shapes differing from docs, so verify before coding.
- **Next:** Phase 3.

## Phase 3. Normalization, deduplication, more sources
- **Objective:** One clean schema and no duplicates across sources.
- **Files:** `parsers/`, `utils/dedupe.py`, `utils/pii.py`, `storage/base.py`, `storage/google_sheets.py`, `storage/sqlite.py`, more adapters (We Work Remotely, Jobicy, verified Kenyan sources, Adzuna if it covers Kenya).
- **Work:** Normalizer, PII scrubber, canonical URLs, fingerprints, merge policy. Google Sheet writer that preserves user columns.
- **Testing:** Dedupe table tests, formula-injection test, Sheet integration test with a scratch Sheet.
- **Expected result:** Jobs appear in the Sheet with no duplicates and user columns intact after reruns.
- **Problems:** Sheets API quotas (batch writes), messy location and salary text.
- **Next:** Phase 4.

## Phase 4. Matching and scoring
- **Objective:** Transparent scores and gaps.
- **Files:** `matching/filters.py`, `skills.py`, `scorer.py`, `explain.py`, tests, calibration notebook or script.
- **Work:** Hard filters, skills dictionary, scoring per doc 06, breakdown storage, `brief` command, checklist generation.
- **Testing:** Golden tests reproduce doc 06 examples. Owner labels about 30 jobs, and agreement is at least 80%.
- **Expected result:** Tiers you agree with, with reasons.
- **Problems:** Synonym gaps and ambiguous eligibility text. Tune `scoring.yaml`.
- **Next:** Phase 5.

## Phase 5. Notifications
- **Objective:** Daily Telegram digest and run report.
- **Files:** `notifications/telegram.py`, digest formatter, tests.
- **Work:** Plain-text digest, splitting under 4096 characters, `notified_at`, follow-up reminders.
- **Testing:** Fake Telegram in tests. Manual send to your chat.
- **Expected result:** A readable digest that never repeats jobs.
- **Problems:** Telegram rate limits, special characters.
- **Next:** Phase 6.

## Phase 6. Scheduling
- **Objective:** Unattended daily runs.
- **Files:** `.github/workflows/daily.yml`, `ci.yml`, `requirements.txt` with hashes, README setup.
- **Work:** Workflow per doc 09, secrets, failure alert, concurrency.
- **Testing:** Manual `workflow_dispatch`, then three consecutive scheduled runs.
- **Expected result:** Digests arrive at about 06:00 and 16:00 EAT with no laptop.
- **Problems:** Delayed cron, secret misconfiguration.
- **Next:** Phase 7.

## Phase 7. Monitoring and reliability hardening
- **Objective:** Failures are visible and contained.
- **Files:** `utils/health.py`, source status tracking, `sources check` command, retention job.
- **Work:** Zero-result and drift alarms, three-strikes alerts, dead-man's-switch, cleanup, security checklist (doc 08).
- **Testing:** Resilience suite. Deliberately break one source and confirm the others still run.
- **Expected result:** Alerts for breakage, no silent failures.
- **Problems:** Alert fatigue, so tune thresholds.
- **Next:** Phase 8 or stop here.

## Phase 8. Optional extras
- Looker Studio dashboard on the Sheet (no code).
- Alert-email ingestion for LinkedIn, Indeed and Glassdoor through an Apps Script in your own Google account (decision O4).
- Optional LLM-assisted extraction or CV tailoring, off by default.
- Streamlit or Next.js dashboard only if the Sheet stops being enough.

## Definition of done (v1)
Phases 1 to 7 complete, success criteria in doc 00 met over one week of real runs, security checklist passed, verification log current.

## Risk register
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Kenyan boards disallow automated access | High | Medium | Email alerts, employer endpoints, other boards |
| Source layout or API change | Medium | Medium | Contract tests, drift alarms, adapters isolated |
| Region-restricted remote jobs slip through | Medium | Medium | Hard filters, "eligibility unconfirmed" flag, calibration |
| Sheets quota limits | Low | Low | Batch writes, small data volume |
| GitHub schedule delays or disabling | Low | Low | Private repo with regular activity, dead-man's switch |
