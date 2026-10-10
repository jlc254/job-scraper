# Graph Report - job-scraper  (2026-10-10)

## Corpus Check
- 119 files · ~83,293 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .in 2, .example 1)

## Summary
- 1428 nodes · 3390 edges · 96 communities (77 shown, 13 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 230 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `050964ac`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- test_matching.py
- scorer.py
- .to_job
- load_fixture
- HttpClient
- jobscraper/dashboard.py
- test_retention.py
- test_health.py
- test_cli_run.py
- models/__init__.py
- test_notifications.py
- make_job
- Part B. Other job boards
- digest.py
- Job
- What You Must Do When Invoked
- Installation & Setup Guide
- test_security_checklist.py
- RawJob
- test_workflows.py
- dedupe.py
- notify.py
- safe_cell
- source_check.py
- StorageError
- test_http.py
- google_sheets.py
- FakeNotifier
- Storage
- TelegramNotifier
- 4. Step-by-step installation
- runner.py
- Deduper
- test_pin_actions.py
- 02. Source Catalog
- 03. Legal and Responsible Use
- 04. Architecture
- 10. Development Plan
- 11. What each phase handled
- Worksheet
- docs/README.md
- Phase 7 notes: monitoring and reliability hardening
- graphify reference: extra exports and benchmark
- 00. Product Requirements Document (PRD)
- 1. Functional Requirements
- 06. Matching and Scoring
- 09. Scheduling and Setup
- Phase 6 notes: scheduling on GitHub Actions
- pin_actions.py
- Job Scraper: Complete Guide
- Looker Studio dashboard
- Phase 8 notes: Looker Studio dashboard
- test_phase3.py
- 07. Reliability and Monitoring
- test_captured_fixtures.py
- graphify reference: query, path, explain
- 05. Data Model
- 7. How one run works, and what is stored where
- _TextExtractor
- 8. Running it day to day
- SQLiteStorage
- Clock
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 5. The websites it reads
- settings.py
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 12. Quiz and FAQ
- test_adapters.py
- AGENTS.md
- extraction-spec.md
- PHASE2.md
- PHASE3.md
- PHASE4.md
- PHASE5.md
- ci_run.sh
- lock.sh
- jobscraper
- himalayas.py
- format_job
- skills.py
- DashboardTable
- brief.py
- applied
- build_parser
- logging.py
- clear_registry_for_tests

## God Nodes (most connected - your core abstractions)
1. `Job` - 55 edges
2. `SQLiteStorage` - 43 edges
3. `HttpClient` - 42 edges
4. `make_job()` - 40 edges
5. `StorageError` - 36 edges
6. `cmd_run()` - 35 edges
7. `Storage` - 34 edges
8. `GoogleSheetsStorage` - 34 edges
9. `load_fixture()` - 28 edges
10. `FetchError` - 27 edges

## Surprising Connections (you probably didn't know these)
- `test_default_settings_match_the_plan()` --uses--> `HealthSettings`  [INFERRED]
  tests/test_health.py → src/jobscraper/utils/health.py
- `test_redaction_filter()` --uses--> `RedactionFilter`  [INFERRED]
  tests/test_helpers.py → src/jobscraper/utils/logging.py
- `test_settings_defaults_and_errors()` --uses--> `ConfigError`  [INFERRED]
  tests/test_matching.py → src/jobscraper/config.py
- `test_bad_settings_fail_fast_with_a_clear_message()` --uses--> `ConfigError`  [INFERRED]
  tests/test_runtime_settings.py → src/jobscraper/config.py
- `source_config()` --uses--> `SourceConfig`  [INFERRED]
  tests/conftest.py → src/jobscraper/config.py

## Import Cycles
- None detected.

## Communities (96 total, 13 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.10
Nodes (43): CLI entry point: python main.py run --dry-run --no-notify, Namespace, build_storage(), cmd_brief(), cmd_calibrate(), cmd_cleanup(), cmd_dashboard(), cmd_health() (+35 more)

### Community 1 - "test_matching.py"
Cohesion: 0.07
Nodes (66): Pattern, _compile(), Exclusion, JobFilters, _keyword_regex(), date, Match, Hard filters (doc 06, step 1). A job that fails is excluded, logged and never… (+58 more)

### Community 2 - "scorer.py"
Cohesion: 0.17
Nodes (18): field_validator, build_checklist(), build_explanation(), Explanation, date, Gaps and recommendations (doc 06): transferable strengths, action, checklist., One primary action by rule, then advisories that must not be hidden by it., FR-9: for Top and Strong matches only. (+10 more)

### Community 3 - ".to_job"
Cohesion: 0.10
Nodes (29): geo_eligibility(), Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).…, clean_str(), html_to_text(), parse_date(), date, HTML to plain text, truncation and small value helpers. Pure functions., Strip tags and return plain text. Scraped content is data, never markup. (+21 more)

### Community 4 - "load_fixture"
Cohesion: 0.10
Nodes (38): Random, ClientFactory, Path, Run every enabled, verified source. One source failing never stops the rest., run_sources(), RunOutcome, Resolver, load_fixture() (+30 more)

### Community 5 - "HttpClient"
Cohesion: 0.08
Nodes (34): RobotFileParser, BlockedError, FetchError, NotFoundError, RateLimitedError, Exception types. Each maps to one source status in the runner., HTTP 401/403. Never retried, never worked around., HTTP 429. The source is marked rate_limited for this run. (+26 more)

### Community 6 - "jobscraper/dashboard.py"
Cohesion: 0.19
Nodes (23): _breakdown(), build_dashboard(), build_from_storage(), _float(), _int(), _job_row(), _local_date(), _local_dt() (+15 more)

### Community 7 - "test_retention.py"
Cohesion: 0.10
Nodes (37): _older_than(), plan_retention(), datetime, Retention (FR-13, doc 03): remove what has aged out, never touch what the owner…, Plan from the stored tables and, unless dry_run, apply. Raises StorageError on…, Unreadable or empty timestamps are never treated as old, so nothing is deleted…, RetentionPlan, RetentionSettings (+29 more)

### Community 8 - "test_health.py"
Cohesion: 0.09
Nodes (46): How a source ended a run (doc 07)., One source's outcome in one run. The Health tab keeps these to spot trends (doc…, SourceRun, SourceStatus, Record one row per source for this run (the Health tab)., alert_text(), _by_source(), evaluate_health() (+38 more)

### Community 9 - "test_cli_run.py"
Cohesion: 0.24
Nodes (19): Job scraper: finds customer-care jobs from permitted sources., env(), mock_sources(), Any, fixture, mock, Path, The whole `run` command against SQLite, with HTTP mocked. No network, no… (+11 more)

### Community 10 - "models/__init__.py"
Cohesion: 0.16
Nodes (20): EmploymentType, ExperienceLevel, make_job_id(), Pydantic models shared by adapters, runner and (later) storage., Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)., RemoteEligibility, WorkType, Adapter (+12 more)

### Community 11 - "test_notifications.py"
Cohesion: 0.29
Nodes (16): Any, mock, parametrize, test_parse_user_date(), test_rows_that_are_not_notified(), test_rows_that_are_notified(), test_telegram_alert_is_prefixed_and_capped(), test_telegram_fails_after_three_server_errors() (+8 more)

### Community 12 - "make_job"
Cohesion: 0.06
Nodes (64): dedupe_jobs(), Phase 3 behaviour: no filters, no scoring., later(), make_job(), Any, datetime, A normalized Job with sensible defaults. Override any field., build() (+56 more)

### Community 13 - "Part B. Other job boards"
Cohesion: 0.07
Nodes (28): 0. Quick answers, A1. How filtering works, A2. Change filters with config only, A3. Soft preferences (no code), A4. Add a new kind of hard filter (recipe), A5. Other filter ideas, A6. After you change a filter, A7. Searching a different type of job entirely (+20 more)

### Community 14 - "digest.py"
Cohesion: 0.11
Nodes (31): Batch, build_digest(), DigestConfig, due_follow_ups(), format_follow_ups(), has_problems(), _posted(), date (+23 more)

### Community 15 - "Job"
Cohesion: 0.22
Nodes (7): Factor, Any, Scorer, JobSkills, Job, Common job schema (subset of doc 05 that Phase 2 can fill). Fingerprint,…, Append new rows. Never overwrites existing rows.

### Community 16 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 17 - "Installation & Setup Guide"
Cohesion: 0.08
Nodes (22): 1. Find your Source IDs, 1. Using a Virtual Environment (Highly Recommended), 2. Installing Dependencies, 2. Run a Single Source, 3. Configuration, 3. How to Verify the Data, 🛠 Detailed Setup Steps, Installation & Setup Guide (+14 more)

### Community 18 - "test_security_checklist.py"
Cohesion: 0.13
Nodes (11): LogRecord, Strips query strings, tokens and registered secret values from messages., RedactionFilter, capture_logs(), stop(), Any, mock, Machine-checkable items from the doc 08 pre-deployment checklist. Items that… (+3 more)

### Community 19 - "RawJob"
Cohesion: 0.14
Nodes (11): One unmapped record exactly as the source returned it., RawJob, Return raw records. May raise a FetchError subclass., Map one raw record to the common schema, or None if unusable., _board_entries(), Return (token, company name) pairs, skipping invalid tokens., JobicyAdapter, WeWorkRemotelyAdapter (+3 more)

### Community 20 - "test_workflows.py"
Cohesion: 0.16
Nodes (20): load(), Any, parametrize, Path, Static checks that keep the workflows inside the rules in docs 08, 09 and 11.…, _requirement_blocks(), steps(), test_checkout_does_not_persist_credentials() (+12 more)

### Community 21 - "dedupe.py"
Cohesion: 0.12
Nodes (24): classify_location(), _is_location_segment(), LocationInfo, normalize_company(), normalize_title(), Pure normalization helpers for titles, companies and locations (doc 05). No…, Lowercase, drop bracketed text, location suffixes, punctuation and level noise., Lowercase, remove punctuation and trailing legal suffixes. (+16 more)

### Community 22 - "notify.py"
Cohesion: 0.19
Nodes (11): Notifier, ABC, Notifier interface (D17). A second channel is a new file that implements this., Deliver one short alert. Returns whether it was delivered., Digest, deliver_digest(), Delivery, date (+3 more)

### Community 23 - "safe_cell"
Cohesion: 0.17
Nodes (15): csv_value(), Any, date, datetime, Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data…, Days since 1899-12-30, the day-count Google Sheets uses for dates and times., A cell value for a RAW Sheets write: blanks as "", dates as serials, text made…, A cell value for a CSV export: ISO dates, true/false, formula-safe text. (+7 more)

### Community 24 - "source_check.py"
Cohesion: 0.11
Nodes (35): gate_reason(), BaseModel, Config loading and the source gate (doc 03)., One entry under `sources:` in sources.yaml., Return why a source may not run, or None when it passes the gate., SourceConfig, SourcesFile, check_source() (+27 more)

### Community 25 - "StorageError"
Cohesion: 0.14
Nodes (10): col_letter(), GoogleSheetsStorage, Add any missing columns at the end of the header row. Never reorders., One batched request, highest rows first so earlier row numbers stay valid., 1-based column index to A1 letters., Storage unreachable, over quota, or asked to break an ownership rule., StorageError, test_marking_failure_is_reported() (+2 more)

### Community 26 - "test_http.py"
Cohesion: 0.23
Nodes (20): Any, mock, parametrize, test_429_not_retried_and_retry_after_capped(), test_gives_up_after_three_attempts(), test_host_outside_allowlist_rejected(), test_no_retry_statuses(), test_non_https_rejected() (+12 more)

### Community 27 - "google_sheets.py"
Cohesion: 0.11
Nodes (25): ExcludedRecord, JobUpdate, BaseModel, What the dedupe step needs to know about a job already in storage., Changes to system-owned columns of an existing row. Never user columns., A job removed by a hard filter, kept in the Excluded tab as an audit trail., StoredJob, Update system-owned columns of existing rows. User columns are never written. (+17 more)

### Community 28 - "FakeNotifier"
Cohesion: 0.20
Nodes (10): `sent` counts messages delivered in order. Sending stops at the first failure., Deliver plain-text messages in order. Never raises for delivery problems., SendResult, FakeNotifier, run_once(), stored(), test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part(), test_follow_up_reminders_are_marked_and_not_repeated() (+2 more)

### Community 29 - "Storage"
Cohesion: 0.11
Nodes (11): ABC, Storage interface (doc 04). Backends never score, filter or notify., Everything dedupe needs about jobs already stored., Record one row in the Runs tab., Record jobs removed by hard filters (audit trail, kept 30 days)., job_ids already in the Excluded log, so they are not logged again., Every Jobs row as a header-name dictionary, for `brief` and `calibrate`., All rows of 'jobs', 'excluded', 'runs' or 'health' as header-name dictionaries. (+3 more)

### Community 30 - "TelegramNotifier"
Cohesion: 0.14
Nodes (13): Client, _describe(), _Permanent, Exception, Response, Telegram Bot API notifier. Plain text only, sent to one configured chat (doc…, Telegram's own error text and retry_after, if the body is the expected JSON., Do not retry: bad token, blocked bot, unknown chat, rejected message. (+5 more)

### Community 31 - "4. Step-by-step installation"
Cohesion: 0.15
Nodes (13): 4.0 What you need first, 4.10 Put it on GitHub (this is what makes it automatic), 4.11 Build the dashboard, 4.1 Get the code, 4.2 Local environment, 4.3 Telegram bot, 4.4 Google Sheet and service account, 4.5 Configure (+5 more)

### Community 32 - "runner.py"
Cohesion: 0.23
Nodes (11): Per-source outcome recorded by the runner (doc 04)., SourceResult, format_report(), datetime, CSV export and the plain-text run report (doc 07 format)., default_client_factory(), datetime, Runner: the only place that wires config, adapters and the HTTP client together. (+3 more)

### Community 33 - "Deduper"
Cohesion: 0.18
Nodes (11): Counter, Deduper, _Entry, format_salary(), datetime, Add one candidate. Returns True if it became a new job, False if merged., Merge policy: union URLs, prefer the employer's domain, keep richest values.…, Human-readable salary for the Sheet. Never converts currency (doc 05). (+3 more)

### Community 34 - "test_pin_actions.py"
Cohesion: 0.26
Nodes (10): fake(), Any, test_already_pinned_lines_are_untouched_unless_update_is_requested(), test_idempotent(), test_local_actions_and_other_lines_are_ignored(), test_placeholder_without_a_version_comment_is_reported(), test_ref_without_a_comment_uses_the_ref_as_the_tag(), test_resolver_rejects_odd_input_and_prefers_the_peeled_commit() (+2 more)

### Community 35 - "02. Source Catalog"
Cohesion: 0.18
Nodes (11): 02. Source Catalog, Query set, Source gate, Sources that need a key, Tier A. Public APIs and feeds, no key, Tier B. Free key required, Tier C. Employer job endpoints (structured, public), Tier D. Kenyan job boards (permission-dependent) (+3 more)

### Community 36 - "03. Legal and Responsible Use"
Cohesion: 0.18
Nodes (11): 03. Legal and Responsible Use, Authentication and sessions, Copyright and attribution, If a source objects, Permission matrix, Personal data, Politeness, Pre-launch checklist (+3 more)

### Community 37 - "04. Architecture"
Cohesion: 0.18
Nodes (10): 04. Architecture, Adapter contract, CLI, Configuration precedence, Digest format, Overview, Repo layout, Run flow (+2 more)

### Community 38 - "10. Development Plan"
Cohesion: 0.18
Nodes (11): 10. Development Plan, Definition of done (v1), Phase 1. Requirements and source research (current), Phase 2. Prototype with 1 to 2 permitted sources, Phase 3. Normalization, deduplication, more sources, Phase 4. Matching and scoring, Phase 5. Notifications, Phase 6. Scheduling (+3 more)

### Community 39 - "11. What each phase handled"
Cohesion: 0.18
Nodes (11): 11. What each phase handled, Open items carried forward, Phase 1: Requirements and source research, Phase 2: Prototype with the safest sources, Phase 3: Normalization, duplicates, storage, more sources, Phase 4: Matching and scoring, Phase 5: Notifications, Phase 6: Scheduling on GitHub Actions (+3 more)

### Community 40 - "Worksheet"
Cohesion: 0.16
Nodes (4): Protocol, Any, The slice of gspread.Worksheet this module uses., Worksheet

### Community 41 - "docs/README.md"
Cohesion: 0.20
Nodes (5): 08. Security, Assets to protect, Pre-deployment checklist, Threats and controls, Job Scraper: Development Documents

### Community 42 - "Phase 7 notes: monitoring and reliability hardening"
Cohesion: 0.20
Nodes (9): Decisions to confirm, Doc 08 pre-deployment checklist, New commands, Phase 7 notes: monitoring and reliability hardening, Retention (runs once a day, on the morning run, or by hand), Suggested changes to the runbook (doc 12), Testing status, honestly, This replaces the synthetic fixtures (+1 more)

### Community 43 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 44 - "00. Product Requirements Document (PRD)"
Cohesion: 0.22
Nodes (8): 00. Product Requirements Document (PRD), Decisions log, Goals, Non-goals, Open items, Owner profile (summary, no personal identifiers), Purpose, Success criteria

### Community 45 - "1. Functional Requirements"
Cohesion: 0.22
Nodes (8): 01. Requirements & Acceptance Criteria, 1.1 Data Acquisition, 1.2 Processing Pipeline, 1.3 Matching & Scoring, 1.4 Storage & Notification, 1. Functional Requirements, 2. Non-Functional Requirements, 3. Acceptance Criteria (Definition of Done)

### Community 46 - "06. Matching and Scoring"
Cohesion: 0.22
Nodes (8): 06. Matching and Scoring, Calibration and versioning, Gaps and recommendations, Known limitations, Skills extraction (v1, no machine learning), Step 1. Hard filters (before scoring), Step 2. Score (100 points), Worked examples (using the current profile)

### Community 47 - "09. Scheduling and Setup"
Cohesion: 0.22
Nodes (8): 09. Scheduling and Setup, Account status (1 Oct 2026), Cost, Options compared, Schedule, Secrets, Setup guide, Workflow specification (`.github/workflows/daily.yml`)

### Community 48 - "Phase 6 notes: scheduling on GitHub Actions"
Cohesion: 0.22
Nodes (8): Decisions to confirm, Expect these on the first CI run, Healthchecks.io (dead-man's switch), Phase 6 notes: scheduling on GitHub Actions, Secrets (Settings, Secrets and variables, Actions), Two things you must do before the first run, Verification (doc 10), What the workflow does

### Community 49 - "pin_actions.py"
Cohesion: 0.28
Nodes (7): main(), pin_text(), Resolver, Pin every `uses:` line in .github/workflows to a full commit SHA (doc 08).…, Commit SHA behind a tag. Annotated tags are peeled to the commit., Return (new text, problems). Local actions and already-pinned lines are left…, resolve()

### Community 50 - "Job Scraper: Complete Guide"
Cohesion: 0.25
Nodes (7): 10. Troubleshooting, 1. What this is, and an honest status, 2. How the pieces connect, 3. Keys and secrets, 6. Tools and libraries used, 9. Command reference and exit codes, Job Scraper: Complete Guide

### Community 51 - "Looker Studio dashboard"
Cohesion: 0.25
Nodes (7): How the data gets there, Looker Studio dashboard, Step 1: create one data source per tab, Step 2: check the field types, Step 3: calculated fields (in the `Dash_Jobs` data source), Step 4: build the pages, Troubleshooting

### Community 52 - "Phase 8 notes: Looker Studio dashboard"
Cohesion: 0.25
Nodes (7): Decisions to confirm, Phase 8 notes: Looker Studio dashboard, Privacy, Setup (once), Still optional (not built), What I could and could not do, What was verified, and what was not

### Community 53 - "test_phase3.py"
Cohesion: 0.31
Nodes (8): Acme: Support Agent' -> ('Acme', 'Support Agent'). No colon means no company., split_title(), Any, mock, test_jobicy_fetch_and_map(), test_split_title(), test_three_sources_merge_across_boards_and_second_run_adds_nothing(), test_weworkremotely_fetch_and_map()

### Community 54 - "07. Reliability and Monitoring"
Cohesion: 0.29
Nodes (6): 07. Reliability and Monitoring, Failure handling, Logging, Per-source status, Run report (sent to Telegram and stored in the Runs tab), Testing strategy

### Community 55 - "test_captured_fixtures.py"
Cohesion: 0.40
Nodes (4): Any, parametrize, Contract tests against REAL saved responses (doc 11). Create the fixtures with…, test_adapter_still_understands_the_real_response()

### Community 56 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 57 - "05. Data Model"
Cohesion: 0.33
Nodes (5): 05. Data Model, Deduplication, Google Sheet layout, Job record, Normalization notes

### Community 58 - "7. How one run works, and what is stored where"
Cohesion: 0.33
Nodes (6): 7.1 The steps of a run, 7.2 Your Google Sheet, 7.3 Hard filters (a job that fails is excluded and logged), 7.4 Scoring (100 points, every point has a reason), 7.5 What you receive, 7. How one run works, and what is stored where

### Community 60 - "8. Running it day to day"
Cohesion: 0.40
Nodes (5): 8. Running it day to day, Common jobs, Daily (about 5 minutes), Weekly (about 15 minutes), What an alert means and what to do

### Community 61 - "SQLiteStorage"
Cohesion: 0.15
Nodes (7): Any, Path, Validate table name against the whitelist and return the safe name., Simulate the owner editing a user column in the Sheet., SQLiteStorage, fixture, storage()

### Community 62 - "Clock"
Cohesion: 0.40
Nodes (3): Clock, fixture, tg()

### Community 63 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 64 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 65 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 66 - "5. The websites it reads"
Cohesion: 0.50
Nodes (4): 5.1 Working readers, 5.2 How politely it behaves, 5.3 Sites reviewed but not read, 5. The websites it reads

### Community 67 - "settings.py"
Cohesion: 0.19
Nodes (18): ExperiencePoints, FreshnessPoints, IndustryPoints, _load(), load_profile(), load_scoring(), LocationPoints, ProfileTitles (+10 more)

### Community 70 - "12. Quiz and FAQ"
Cohesion: 0.67
Nodes (3): 12. Quiz and FAQ, Question 1 (your question), Self-check quiz (click an answer line to reveal it)

### Community 71 - "test_adapters.py"
Cohesion: 0.33
Nodes (15): GreenhouseAdapter, HimalayasAdapter, map_all(), Any, mock, test_excerpt_zero_stores_nothing_but_keeps_scoring_text(), test_greenhouse_blocked_stops_source(), test_greenhouse_fetch_and_map() (+7 more)

### Community 87 - "himalayas.py"
Cohesion: 0.23
Nodes (10): _as_str_list(), _eligibility(), _experience(), _number(), Himalayas public JSON API adapter. Response shape (from memory, VERIFY against…, _phone_sub(), Match, Remove emails and phone numbers from text before it is stored (D8). (+2 more)

### Community 88 - "format_job"
Cohesion: 0.27
Nodes (12): clean(), format_job(), One safe line: no control or bidi characters, collapsed whitespace, length-…, safe_url(), _skill_label(), _skills(), _where(), row() (+4 more)

### Community 89 - "skills.py"
Cohesion: 0.27
Nodes (7): _kind_at(), _markers(), Skills extraction, version 1: a dictionary with synonyms, no machine learning…, (start, end, kind) for each heading that opens a required or preferred section., Section of a mention. No headings, or before the first one, means required., _requirement_lines(), SkillExtractor

### Community 90 - "DashboardTable"
Cohesion: 0.29
Nodes (4): DashboardTable, Replace the Dash_* tabs with these tables. They are derived data, rebuilt every…, Rewrite each Dash_* tab completely. Looker Studio reads one worksheet per data…, Stored as JSON with the same cell values the Sheet gets (dates as serial…

### Community 91 - "brief.py"
Cohesion: 0.47
Nodes (5): _breakdown(), _bullets(), Any, Markdown job brief for CV and cover-letter help (FR-10). Built from the stored…, render_brief()

### Community 92 - "applied"
Cohesion: 0.40
Nodes (6): applied(), due_ids(), test_empty_digest_only_in_the_morning_or_when_something_is_wrong(), test_follow_up_is_seven_days_after_applied_unless_overridden(), test_follow_up_reminded_once_per_due_date(), test_follow_up_section_text()

### Community 93 - "build_parser"
Cohesion: 0.83
Nodes (4): ArgumentParser, _add_settings_arg(), _add_storage_args(), build_parser()

### Community 94 - "logging.py"
Cohesion: 0.50
Nodes (3): JsonFormatter, JSON logging with a redaction filter (doc 07, doc 11)., One JSON object per line. Extra context goes in `ctx`.

## Knowledge Gaps
- **235 isolated node(s):** `jobscraper`, `ci_run.sh script`, `lock.sh script`, `Usage`, `What graphify is for` (+230 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 550 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Storage` connect `Storage` to `cli.py`, `test_matching.py`, `jobscraper/dashboard.py`, `test_retention.py`, `test_health.py`, `make_job`, `Job`, `notify.py`, `StorageError`, `DashboardTable`, `google_sheets.py`, `SQLiteStorage`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `Job` connect `Job` to `runner.py`, `test_matching.py`, `scorer.py`, `cli.py`, `.to_job`, `Deduper`, `models/__init__.py`, `make_job`, `RawJob`, `dedupe.py`, `himalayas.py`, `StorageError`, `google_sheets.py`, `Storage`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `SQLiteStorage` connect `SQLiteStorage` to `cli.py`, `test_matching.py`, `load_fixture`, `test_retention.py`, `test_health.py`, `test_cli_run.py`, `make_job`, `test_phase3.py`, `StorageError`, `DashboardTable`, `google_sheets.py`, `FakeNotifier`, `Storage`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SQLiteStorage` (e.g. with `DashboardTable` and `StorageError`) actually correct?**
  _`SQLiteStorage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `HttpClient` (e.g. with `Adapter` and `GreenhouseAdapter`) actually correct?**
  _`HttpClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `StorageError` (e.g. with `cmd_brief()` and `cmd_calibrate()`) actually correct?**
  _`StorageError` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `jobscraper`, `ci_run.sh script`, `lock.sh script` to the rest of the system?**
  _235 weakly-connected nodes found - possible documentation gaps or missing edges._