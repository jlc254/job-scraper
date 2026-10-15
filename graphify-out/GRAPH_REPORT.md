# Graph Report - job-scraper  (2026-10-15)

## Corpus Check
- 178 files · ~115,628 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 5, .example 2, .in 2)

## Summary
- 1957 nodes · 4260 edges · 141 communities (111 shown, 20 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 251 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e5197191`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- test_matching.py
- scorer.py
- models/__init__.py
- load_fixture
- HttpClient
- jobscraper/dashboard.py
- load_runtime_settings
- test_health.py
- SQLiteStorage
- runner.py
- test_notifications.py
- make_job
- Part B. Other job boards
- digest.py
- package.json
- What You Must Do When Invoked
- Installation & Setup Guide
- test_security_checklist.py
- Scorer
- test_workflows.py
- Deduper
- notify.py
- safe_cell
- Neon
- GoogleSheetsStorage
- jobicy.py
- google_sheets.py
- FakeNotifier
- Storage
- TelegramNotifier
- 4. Step-by-step installation
- normalize.py
- test_publish.py
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
- register
- 07. Reliability and Monitoring
- 13. Neon Database, Migration and Publish Command
- graphify reference: query, path, explain
- 05. Data Model
- 7. How one run works, and what is stored where
- html_to_text
- 8. Running it day to day
- SourceResult
- Clock
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 5. The websites it reads
- filters.ts
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 12. Quiz and FAQ
- filters.py
- AGENTS.md
- extraction-spec.md
- PHASE2.md
- PHASE3.md
- PHASE4.md
- PHASE5.md
- ci_run.sh
- lock.sh
- jobscraper
- pipeline.py
- 14. Frontend Dashboard
- Lakebase Postgres
- NeonPublisher
- Semantic Vector Search
- PostgresStorage
- compilerOptions
- run_publish
- build_parser
- publish.py
- settings.py
- test_retention.py
- scrub_pii
- 11. Coding Standards
- test_neon_integration.py
- Neon publish: wiring it into the repo
- devDependencies
- calibrate.py
- himalayas.py
- load_scoring
- Job dashboard (frontend)
- next.config.mjs
- skills.py
- job_to_row
- next-env.d.ts
- db.ts
- urls.py
- brief.py
- years_asked
- .to_job
- hybrid-search.md
- .to_job
- check_source
- Managing Lakebase Search with Drizzle
- Claimable Neon
- dependencies
- scripts
- output.py
- dedupe.py
- Full-Text Search with BM25 Ranking
- Setup Flow
- Troubleshooting and Neon-Specific Performance
- layout.tsx
- logging.py
- Logs: CLI, Loki, and SDK pagination
- .__exit__
- .eslintrc.json
- function-triggers.md
- parse-env.md
- sdk.md

## God Nodes (most connected - your core abstractions)
1. `SQLiteStorage` - 44 edges
2. `HttpClient` - 42 edges
3. `StorageError` - 41 edges
4. `make_job()` - 40 edges
5. `Storage` - 36 edges
6. `GoogleSheetsStorage` - 36 edges
7. `cmd_run()` - 35 edges
8. `load_fixture()` - 28 edges
9. `FetchError` - 27 edges
10. `SourceResult` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_default_settings_match_the_plan()` --uses--> `HealthSettings`  [INFERRED]
  tests/test_health.py → src/jobscraper/utils/health.py
- `test_redaction_filter()` --uses--> `RedactionFilter`  [INFERRED]
  tests/test_helpers.py → src/jobscraper/utils/logging.py
- `test_settings_defaults_and_errors()` --uses--> `ConfigError`  [INFERRED]
  tests/test_matching.py → src/jobscraper/config.py
- `source_config()` --uses--> `SourceConfig`  [INFERRED]
  tests/conftest.py → src/jobscraper/config.py
- `filters()` --uses--> `JobFilters`  [INFERRED]
  tests/test_matching.py → src/jobscraper/matching/filters.py

## Import Cycles
- None detected.

## Communities (141 total, 20 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.16
Nodes (29): CLI entry point: python main.py run --dry-run --no-notify, Namespace, build_storage(), cmd_brief(), cmd_calibrate(), cmd_cleanup(), cmd_dashboard(), cmd_health() (+21 more)

### Community 1 - "test_matching.py"
Cohesion: 0.17
Nodes (34): factor(), job(), Any, parametrize, test_action_apply_now_when_deadline_close(), test_bonus_in_a_sentence_is_not_a_heading(), test_breakdown_is_json_serialisable_and_versioned(), test_brief_renders_from_stored_row() (+26 more)

### Community 2 - "scorer.py"
Cohesion: 0.22
Nodes (15): field_validator, build_checklist(), build_explanation(), Explanation, Job, Gaps and recommendations (doc 06): transferable strengths, action, checklist., One primary action by rule, then advisories that must not be hidden by it., FR-9: for Top and Strong matches only. (+7 more)

### Community 3 - "models/__init__.py"
Cohesion: 0.21
Nodes (15): EmploymentType, Job, make_job_id(), BaseModel, Pydantic models shared by adapters, runner and (later) storage., Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)., One unmapped record exactly as the source returned it., Common job schema (subset of doc 05 that Phase 2 can fill). Fingerprint,… (+7 more)

### Community 4 - "load_fixture"
Cohesion: 0.07
Nodes (60): ClientFactory, datetime, Job, Path, Run every enabled, verified source. One source failing never stops the rest., _run_one(), finish(), run_sources() (+52 more)

### Community 5 - "HttpClient"
Cohesion: 0.06
Nodes (57): Random, RobotFileParser, Return raw records. May raise a FetchError subclass., BlockedError, FetchError, NotFoundError, RateLimitedError, Exception types. Each maps to one source status in the runner. (+49 more)

### Community 6 - "jobscraper/dashboard.py"
Cohesion: 0.21
Nodes (23): _breakdown(), build_dashboard(), build_from_storage(), _float(), _int(), _job_row(), _local_date(), _local_dt() (+15 more)

### Community 7 - "load_runtime_settings"
Cohesion: 0.18
Nodes (19): ConfigError, Exception, Config file missing or invalid. Fail fast with a clear message., _build(), load_runtime_settings(), Any, Path, Optional config/settings.yaml: thresholds for health alarms, retention and the… (+11 more)

### Community 8 - "test_health.py"
Cohesion: 0.11
Nodes (42): How a source ended a run (doc 07)., SourceStatus, alert_text(), _by_source(), evaluate_health(), Finding, format_health_table(), needs_attention() (+34 more)

### Community 9 - "SQLiteStorage"
Cohesion: 0.11
Nodes (24): Any, Job, Path, Validate table name against the whitelist and return the safe name., Simulate the owner editing a user column in the Sheet., SQLiteStorage, env(), mock_sources() (+16 more)

### Community 10 - "runner.py"
Cohesion: 0.09
Nodes (29): gate_reason(), load_sources(), BaseModel, Path, Config loading and the source gate (doc 03)., One entry under `sources:` in sources.yaml., Read and validate sources.yaml., Return why a source may not run, or None when it passes the gate. (+21 more)

### Community 11 - "test_notifications.py"
Cohesion: 0.28
Nodes (17): Any, mock, parametrize, test_parse_user_date(), test_posted_text(), test_rows_that_are_not_notified(), test_rows_that_are_notified(), test_telegram_alert_is_prefixed_and_capped() (+9 more)

### Community 12 - "make_job"
Cohesion: 0.05
Nodes (67): Job scraper: finds customer-care jobs from permitted sources., later(), make_job(), Any, datetime, Job, A normalized Job with sensible defaults. Override any field., build() (+59 more)

### Community 13 - "Part B. Other job boards"
Cohesion: 0.07
Nodes (28): 0. Quick answers, A1. How filtering works, A2. Change filters with config only, A3. Soft preferences (no code), A4. Add a new kind of hard filter (recipe), A5. Other filter ideas, A6. After you change a filter, A7. Searching a different type of job entirely (+20 more)

### Community 14 - "digest.py"
Cohesion: 0.18
Nodes (20): clean(), format_follow_ups(), format_job(), _posted(), datetime, Build the Telegram digest and follow-up reminders from stored rows (doc 04, doc…, Unnotified Top and Strong jobs, plus up to `max_potential` recent Potential…, One safe line: no control or bidi characters, collapsed whitespace, length-… (+12 more)

### Community 15 - "package.json"
Cohesion: 0.13
Nodes (14): name, private, version, eslint, eslint-config-next, @neondatabase/serverless, pg, react-dom (+6 more)

### Community 16 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 17 - "Installation & Setup Guide"
Cohesion: 0.08
Nodes (22): 1. Find your Source IDs, 1. Using a Virtual Environment (Highly Recommended), 2. Installing Dependencies, 2. Run a Single Source, 3. Configuration, 3. How to Verify the Data, 🛠 Detailed Setup Steps, Installation & Setup Guide (+14 more)

### Community 18 - "test_security_checklist.py"
Cohesion: 0.13
Nodes (11): LogRecord, Strips query strings, tokens and registered secret values from messages., RedactionFilter, capture_logs(), stop(), Any, mock, Machine-checkable items from the doc 08 pre-deployment checklist. Items that… (+3 more)

### Community 19 - "Scorer"
Cohesion: 0.29
Nodes (5): Factor, Any, Job, Scorer, JobSkills

### Community 20 - "test_workflows.py"
Cohesion: 0.16
Nodes (20): load(), Any, parametrize, Path, Static checks that keep the workflows inside the rules in docs 08, 09 and 11.…, _requirement_blocks(), steps(), test_checkout_does_not_persist_credentials() (+12 more)

### Community 21 - "Deduper"
Cohesion: 0.28
Nodes (8): Deduper, _Entry, format_salary(), Job, Add one candidate. Returns True if it became a new job, False if merged., Merge policy: union URLs, prefer the employer's domain, keep richest values.…, Human-readable salary for the Sheet. Never converts currency (doc 05)., Index of stored jobs plus jobs added during this run.

### Community 22 - "notify.py"
Cohesion: 0.17
Nodes (11): Notifier, ABC, Notifier interface (D17). A second channel is a new file that implements this., Deliver plain-text messages in order. Never raises for delivery problems., Deliver one short alert. Returns whether it was delivered., Digest, deliver_digest(), Delivery (+3 more)

### Community 23 - "safe_cell"
Cohesion: 0.15
Nodes (15): csv_value(), Any, datetime, Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data…, Days since 1899-12-30, the day-count Google Sheets uses for dates and times., A cell value for a RAW Sheets write: blanks as "", dates as serials, text made…, A cell value for a CSV export: ISO dates, true/false, formula-safe text., sheet_serial() (+7 more)

### Community 24 - "Neon"
Cohesion: 0.05
Nodes (36): Auth, 1. Install the Neon CLI, 2. Install the Neon MCP Server, 3. Install Neon Agent Skills, 4. Link Your Project and Get Started, Architecture: How to Use Neon, Backend Primitives, Bootstrap a New Project (+28 more)

### Community 25 - "GoogleSheetsStorage"
Cohesion: 0.13
Nodes (9): col_letter(), GoogleSheetsStorage, Job, Add any missing columns at the end of the header row. Never reorders., One batched request, highest rows first so earlier row numbers stay valid., Rewrite each Dash_* tab completely. Looker Studio reads one worksheet per data…, 1-based column index to A1 letters., test_writing_dashboard_tabs_needs_the_spreadsheet_handle() (+1 more)

### Community 26 - "jobicy.py"
Cohesion: 0.17
Nodes (16): clean_str(), parse_date(), HTML to plain text, truncation and small value helpers. Pure functions., Cut at max_chars, preferring a word boundary. 0 returns an empty string., Return a stripped non-empty string, else None., Accept only absolute http(s) URLs. Anything else is dropped., Parse unix seconds/milliseconds or ISO-8601 strings to a UTC date., safe_http_url() (+8 more)

### Community 27 - "google_sheets.py"
Cohesion: 0.10
Nodes (26): ExcludedRecord, JobUpdate, What the dedupe step needs to know about a job already in storage., Changes to system-owned columns of an existing row. Never user columns., A job removed by a hard filter, kept in the Excluded tab as an audit trail., One source's outcome in one run. The Health tab keeps these to spot trends (doc…, SourceRun, StoredJob (+18 more)

### Community 28 - "FakeNotifier"
Cohesion: 0.21
Nodes (11): `sent` counts messages delivered in order. Sending stops at the first failure., SendResult, FakeNotifier, run_once(), stored(), test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part(), test_follow_up_reminders_are_marked_and_not_repeated(), test_marking_failure_is_reported() (+3 more)

### Community 29 - "Storage"
Cohesion: 0.08
Nodes (14): Job, Everything dedupe needs about jobs already stored., Append new rows. Never overwrites existing rows., Update system-owned columns of existing rows. User columns are never written., Record one row in the Runs tab., Record jobs removed by hard filters (audit trail, kept 30 days)., job_ids already in the Excluded log, so they are not logged again., Every Jobs row as a header-name dictionary, for `brief` and `calibrate`. (+6 more)

### Community 30 - "TelegramNotifier"
Cohesion: 0.14
Nodes (14): Client, cmd_notify_test(), _describe(), _Permanent, Exception, Response, Telegram Bot API notifier. Plain text only, sent to one configured chat (doc…, Telegram's own error text and retry_after, if the body is the expected JSON. (+6 more)

### Community 31 - "4. Step-by-step installation"
Cohesion: 0.15
Nodes (13): 4.0 What you need first, 4.10 Put it on GitHub (this is what makes it automatic), 4.11 Build the dashboard, 4.1 Get the code, 4.2 Local environment, 4.3 Telegram bot, 4.4 Google Sheet and service account, 4.5 Configure (+5 more)

### Community 32 - "normalize.py"
Cohesion: 0.18
Nodes (13): classify_location(), _is_location_segment(), LocationInfo, normalize_title(), Pure normalization helpers for titles, companies and locations (doc 05). No…, Lowercase, drop bracketed text, location suffixes, punctuation and level noise., Read free-text location. Conservative: unknown stays unknown., fingerprint() (+5 more)

### Community 33 - "test_publish.py"
Cohesion: 0.15
Nodes (26): dropped(), make_row(), one(), parametrize, Unit tests for publish.py and publish_cli.py (no network, no psycopg)., test_age_rule_and_keep_statuses(), test_bad_first_seen_dropped(), test_bad_urls_dropped() (+18 more)

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
Cohesion: 0.18
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

### Community 53 - "register"
Cohesion: 0.33
Nodes (4): JobicyAdapter, Class decorator that registers an adapter under its `id`., register(), WeWorkRemotelyAdapter

### Community 54 - "07. Reliability and Monitoring"
Cohesion: 0.29
Nodes (6): 07. Reliability and Monitoring, Failure handling, Logging, Per-source status, Run report (sent to Telegram and stored in the Runs tab), Testing strategy

### Community 55 - "13. Neon Database, Migration and Publish Command"
Cohesion: 0.07
Nodes (26): 13. Neon Database, Migration and Publish Command, CLI, Column mapping (34 Sheet columns), Decisions (add to the log in doc 00), Free-tier assessment (verified 10 Oct 2026), Guards, Integration tests, Local-first order of work (+18 more)

### Community 56 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 57 - "05. Data Model"
Cohesion: 0.33
Nodes (5): 05. Data Model, Deduplication, Google Sheet layout, Job record, Normalization notes

### Community 58 - "7. How one run works, and what is stored where"
Cohesion: 0.33
Nodes (6): 7.1 The steps of a run, 7.2 Your Google Sheet, 7.3 Hard filters (a job that fails is excluded and logged), 7.4 Scoring (100 points, every point has a reason), 7.5 What you receive, 7. How one run works, and what is stored where

### Community 59 - "html_to_text"
Cohesion: 0.18
Nodes (8): HTMLParser, html_to_text(), Strip tags and return plain text. Scraped content is data, never markup., For feeds that deliver HTML entity-escaped HTML (Greenhouse `content`)., _TextExtractor, unescape_then_text(), test_html_to_text_strips_tags_and_scripts(), test_unescape_then_text()

### Community 60 - "8. Running it day to day"
Cohesion: 0.40
Nodes (5): 8. Running it day to day, Common jobs, Daily (about 5 minutes), Weekly (about 15 minutes), What an alert means and what to do

### Community 61 - "SourceResult"
Cohesion: 0.15
Nodes (24): Per-source outcome recorded by the runner (doc 04)., SourceResult, Batch, build_digest(), DigestConfig, due_follow_ups(), has_problems(), Applied jobs whose follow-up date has arrived and has not been reminded yet.… (+16 more)

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

### Community 67 - "filters.ts"
Cohesion: 0.05
Nodes (80): dynamic, JobPage(), dynamic, Home(), FilterDisclosure(), FilterPanel(), Opt, JobCard() (+72 more)

### Community 70 - "12. Quiz and FAQ"
Cohesion: 0.67
Nodes (3): 12. Quiz and FAQ, Question 1 (your question), Self-check quiz (click an answer line to reveal it)

### Community 71 - "filters.py"
Cohesion: 0.21
Nodes (12): Pattern, _compile(), Exclusion, JobFilters, _keyword_regex(), Job, Match, Hard filters (doc 06, step 1). A job that fails is excluded, logged and never… (+4 more)

### Community 84 - "pipeline.py"
Cohesion: 0.20
Nodes (17): Counter, dedupe_jobs(), persist(), process_jobs(), datetime, Job, Path, Normalize, filter, dedupe, score and persist. The runner fetches; this decides… (+9 more)

### Community 87 - "14. Frontend Dashboard"
Cohesion: 0.08
Nodes (25): 14. Frontend Dashboard, Apply button, Data access, Decisions (add to the log in doc 00), Display rules, End-to-end checklist (manual, before deploy), Environment variables, Filters and sorting (+17 more)

### Community 88 - "Lakebase Postgres"
Cohesion: 0.15
Nodes (13): Autoscaling, Branching, Connection Pooling, Gotchas, Instant Restore, IP Allow Lists, Lakebase Postgres, Lakebase Search (+5 more)

### Community 89 - "NeonPublisher"
Cohesion: 0.19
Nodes (13): _adapt(), NeonError, NeonPublisher, Any, Connection, datetime, Exception, RuntimeError (+5 more)

### Community 90 - "Semantic Vector Search"
Cohesion: 0.18
Nodes (11): AI SDK (Recommended), Build the Index, Contents, Create the Extension, OpenAI SDK Alternative, Prepare Embeddings, Query, Semantic Vector Search (+3 more)

### Community 91 - "PostgresStorage"
Cohesion: 0.15
Nodes (5): _connect(), PostgresStorage, Any, Connection, Connect to Postgres, creating the configured database on first run.

### Community 92 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 93 - "run_publish"
Cohesion: 0.14
Nodes (18): check_guard(), Any, datetime, `python main.py publish` logic. The CLI/runner is the only place that wires…, Read the Sheet, apply the rules, and refresh Neon (unless dry-run). `load_rows`…, run_publish(), GuardError, PublishSettings (+10 more)

### Community 94 - "build_parser"
Cohesion: 0.83
Nodes (4): ArgumentParser, _add_settings_arg(), _add_storage_args(), build_parser()

### Community 95 - "publish.py"
Cohesion: 0.20
Nodes (17): _breakdown(), build_rows(), _date(), _names(), _or_none(), PublishPlan, Any, datetime (+9 more)

### Community 96 - "settings.py"
Cohesion: 0.25
Nodes (13): ExperiencePoints, FreshnessPoints, IndustryPoints, LocationPoints, ProfileTitles, BaseModel, Validated profile and scoring configuration (doc 06, doc 11). Every point value…, SalaryFloor (+5 more)

### Community 97 - "test_retention.py"
Cohesion: 0.14
Nodes (26): _older_than(), plan_retention(), datetime, Retention (FR-13, doc 03): remove what has aged out, never touch what the owner…, Plan from the stored tables and, unless dry_run, apply. Raises StorageError on…, Unreadable or empty timestamps are never treated as old, so nothing is deleted…, RetentionPlan, RetentionSettings (+18 more)

### Community 98 - "scrub_pii"
Cohesion: 0.22
Nodes (12): _phone_sub(), Match, Remove emails and phone numbers from text before it is stored (D8)., Return text with emails and phone numbers replaced by placeholders., scrub_pii(), Any, parametrize, test_csv_formula_prefix() (+4 more)

### Community 99 - "11. Coding Standards"
Cohesion: 0.18
Nodes (11): 11. Coding Standards, Configuration, Definition of done (per task), Error handling, Git workflow, Language and tooling, Logging, Naming and style (+3 more)

### Community 100 - "test_neon_integration.py"
Cohesion: 0.31
Nodes (10): count(), fresh_schema(), datetime, fixture, Integration tests for the Neon writer. Skipped unless TEST_DATABASE_URL points…, rows(), test_failure_rolls_back_and_keeps_previous_rows(), test_publish_twice_is_idempotent() (+2 more)

### Community 101 - "Neon publish: wiring it into the repo"
Cohesion: 0.22
Nodes (8): 1. Dependencies and config, 2. CLI glue (adapt names to your `cli.py`), 3. Workflow (`.github/workflows/daily.yml`), 4. Order of work, 5. Doc updates, Behavior notes, Neon publish: wiring it into the repo, What I could not see (please check)

### Community 102 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, eslint, eslint-config-next, @types/node, @types/pg, @types/react, @types/react-dom, typescript (+1 more)

### Community 103 - "calibrate.py"
Cohesion: 0.33
Nodes (8): agreement_report(), Path, Calibration helpers (doc 06): label about 30 real jobs, then compare with the…, Newest first, spread across tiers so every tier gets looked at., read_labels(), select_for_labeling(), write_label_sheet(), test_calibration_export_and_report()

### Community 104 - "himalayas.py"
Cohesion: 0.33
Nodes (7): ExperienceLevel, _as_str_list(), _eligibility(), _experience(), _number(), Job, Himalayas public JSON API adapter. Response shape (from memory, VERIFY against…

### Community 105 - "load_scoring"
Cohesion: 0.21
Nodes (12): _load(), load_profile(), load_scoring(), Any, Path, extractor(), filters(), profile() (+4 more)

### Community 106 - "Job dashboard (frontend)"
Cohesion: 0.33
Nodes (5): Before you trust it (O10), Job dashboard (frontend), Notes and decisions, Run locally (against local PostgreSQL), Structure

### Community 108 - "skills.py"
Cohesion: 0.27
Nodes (7): _kind_at(), _markers(), Skills extraction, version 1: a dictionary with synonyms, no machine learning…, (start, end, kind) for each heading that opens a required or preferred section., Section of a mention. No headings, or before the first one, means required., _requirement_lines(), SkillExtractor

### Community 109 - "job_to_row"
Cohesion: 0.33
Nodes (5): Job, job_to_row(), Job, System columns for a new job, plus the initial application_status., test_job_to_row_escapes_formulas_and_sets_status()

### Community 115 - "db.ts"
Cohesion: 0.27
Nodes (10): DatabaseConfigurationError, errorProperties(), getDatabaseUrl(), isRetryable(), NeonSql, query(), runQuery(), sleep() (+2 more)

### Community 117 - "urls.py"
Cohesion: 0.25
Nodes (10): canonical_url(), employer_domain(), _host_in(), host_of(), URL canonicalization and host classification for dedupe (doc 05)., Host of the URL if it looks like the employer's own site, else None., 3 = employer domain, 2 = ATS board, 1 = aggregator or unknown., Comparison key: lowercase host, https, no fragment, no tracking params, sorted… (+2 more)

### Community 118 - "brief.py"
Cohesion: 0.47
Nodes (5): _breakdown(), _bullets(), Any, Markdown job brief for CV and cover-letter help (FR-10). Built from the stored…, render_brief()

### Community 119 - "years_asked"
Cohesion: 0.67
Nodes (3): First 'N years' phrase that sits next to the word 'experience'., years_asked(), test_years_asked()

### Community 120 - ".to_job"
Cohesion: 0.29
Nodes (6): geo_eligibility(), Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).…, Job, Acme: Support Agent' -> ('Acme', 'Support Agent'). No colon means no company., split_title(), test_split_title()

### Community 121 - "hybrid-search.md"
Cohesion: 0.43
Nodes (3): Adapt the Hybrid Search, Hybrid Search, RRF Example

### Community 123 - "check_source"
Cohesion: 0.17
Nodes (24): check_source(), CheckResult, format_check(), Any, ClientFactory, datetime, Path, (extension, text) for a captured response: personal data removed, a few items… (+16 more)

### Community 124 - "Managing Lakebase Search with Drizzle"
Cohesion: 0.25
Nodes (8): BM25 Index, Config, Extensions, Generate and Store Embeddings, Managing Lakebase Search with Drizzle, Query, Schema, Tune Per Query

### Community 125 - "Claimable Neon"
Cohesion: 0.29
Nodes (6): Claim, Claimable Neon, If neon claim is missing, Path, With REST, With the CLI

### Community 126 - "dependencies"
Cohesion: 0.29
Nodes (7): dependencies, @neondatabase/serverless, next, pg, react, react-dom, server-only

### Community 127 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, start, test, typecheck

### Community 128 - "output.py"
Cohesion: 0.33
Nodes (6): format_report(), datetime, Job, Path, CSV export and the plain-text run report (doc 07 format)., write_csv()

### Community 129 - "dedupe.py"
Cohesion: 0.38
Nodes (5): normalize_company(), Lowercase, remove punctuation and trailing legal suffixes., datetime, Deduplication and merge policy (doc 05). Checks run in order and the first…, _stored_norm()

### Community 130 - "Full-Text Search with BM25 Ranking"
Cohesion: 0.33
Nodes (6): Full-Text Search with BM25 Ranking, Prepare and Index Text, Query and Interpret Scores, Set Parameters at Build Time or Per Query, Set the Candidate Limit, Use Prefilter Selectively

### Community 131 - "Setup Flow"
Cohesion: 0.33
Nodes (6): 1. Select the organization and project, 2. Get the connection string, 3. Pick the connection method and driver, 4. Set up the schema, Setup Flow, When to use pooled vs direct connections

### Community 132 - "Troubleshooting and Neon-Specific Performance"
Cohesion: 0.33
Nodes (6): Choose CLI or MCP, Inspect Neon Cache Behavior Per Query, Interpret Results Safely, Performance Workflow, Pick the Diagnostic, Troubleshooting and Neon-Specific Performance

### Community 133 - "layout.tsx"
Cohesion: 0.33
Nodes (4): font, metadata, viewport, next

### Community 134 - "logging.py"
Cohesion: 0.40
Nodes (5): JsonFormatter, JSON logging with a redaction filter (doc 07, doc 11)., One JSON object per line. Extra context goes in `ctx`., Configure the root logger once. Logs go to stderr so stdout stays clean., setup_logging()

## Knowledge Gaps
- **448 isolated node(s):** `extends`, `next/core-web-vitals`, `dynamic`, `font`, `metadata` (+443 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 834 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Storage` connect `Storage` to `cli.py`, `test_retention.py`, `jobscraper/dashboard.py`, `SQLiteStorage`, `PostgresStorage`, `pipeline.py`, `notify.py`, `GoogleSheetsStorage`, `google_sheets.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `GoogleSheetsStorage` connect `GoogleSheetsStorage` to `cli.py`, `test_retention.py`, `jobscraper/dashboard.py`, `Worksheet`, `make_job`, `NeonPublisher`, `google_sheets.py`, `FakeNotifier`, `Storage`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `StorageError` connect `cli.py` to `HttpClient`, `google_sheets.py`, `SQLiteStorage`, `make_job`, `pipeline.py`, `notify.py`, `GoogleSheetsStorage`, `PostgresStorage`, `FakeNotifier`, `TelegramNotifier`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SQLiteStorage` (e.g. with `DashboardTable` and `StorageError`) actually correct?**
  _`SQLiteStorage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `HttpClient` (e.g. with `Adapter` and `GreenhouseAdapter`) actually correct?**
  _`HttpClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `StorageError` (e.g. with `cmd_brief()` and `cmd_calibrate()`) actually correct?**
  _`StorageError` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Storage` (e.g. with `build_storage()` and `cmd_run()`) actually correct?**
  _`Storage` has 11 INFERRED edges - model-reasoned connections that need verification._