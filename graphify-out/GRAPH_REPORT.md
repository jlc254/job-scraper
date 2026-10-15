# Graph Report - job-scraper  (2026-10-15)

## Corpus Check
- 178 files · ~115,659 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 5, .example 2, .in 2)

## Summary
- 1960 nodes · 4263 edges · 140 communities (108 shown, 22 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 250 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5f3f2959`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- StorageError
- test_matching.py
- scorer.py
- scrapers/__init__.py
- load_fixture
- HttpClient
- jobscraper/dashboard.py
- load_runtime_settings
- test_health.py
- SQLiteStorage
- runner.py
- test_notifications.py
- test_dashboard.py
- Part B. Other job boards
- digest.py
- package.json
- What You Must Do When Invoked
- Installation & Setup Guide
- test_security_checklist.py
- Scorer
- test_workflows.py
- dedupe.py
- notify.py
- google_sheets.py
- Neon
- GoogleSheetsStorage
- himalayas.py
- sqlite.py
- FakeNotifier
- Storage
- TelegramNotifier
- 4. Step-by-step installation
- filters.ts
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
- SchemaError
- 07. Reliability and Monitoring
- 13. Neon Database, Migration and Publish Command
- graphify reference: query, path, explain
- 05. Data Model
- 7. How one run works, and what is stored where
- _TextExtractor
- 8. Running it day to day
- SourceResult
- Clock
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 5. The websites it reads
- [id]/page.tsx
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 12. Quiz and FAQ
- models/__init__.py
- AGENTS.md
- extraction-spec.md
- PHASE2.md
- PHASE3.md
- PHASE4.md
- PHASE5.md
- ci_run.sh
- lock.sh
- jobscraper
- persist
- 14. Frontend Dashboard
- Lakebase Postgres
- NeonPublisher
- Semantic Vector Search
- PostgresStorage
- compilerOptions
- run_publish
- test_http.py
- build_rows
- settings.py
- test_retention.py
- greenhouse.py
- 11. Coding Standards
- test_neon_integration.py
- Neon publish: wiring it into the repo
- FilterPanel.tsx
- calibrate.py
- retention.py
- load_scoring
- Job dashboard (frontend)
- next.config.mjs
- skills.py
- test_storage.py
- next-env.d.ts
- queries.ts
- make_job
- brief.py
- years_asked
- breakdown.ts
- hybrid-search.md
- .to_job
- rows.py
- Managing Lakebase Search with Drizzle
- Claimable Neon
- ConfigError
- app/page.tsx
- cli.py
- ExcludedRecord
- Full-Text Search with BM25 Ranking
- Setup Flow
- Troubleshooting and Neon-Specific Performance
- FakeBook
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
- `test_redaction_filter()` --uses--> `RedactionFilter`  [INFERRED]
  tests/test_helpers.py → src/jobscraper/utils/logging.py
- `test_settings_defaults_and_errors()` --uses--> `ConfigError`  [INFERRED]
  tests/test_matching.py → src/jobscraper/config.py
- `test_bad_settings_fail_fast_with_a_clear_message()` --uses--> `ConfigError`  [INFERRED]
  tests/test_runtime_settings.py → src/jobscraper/config.py
- `source_config()` --uses--> `SourceConfig`  [INFERRED]
  tests/conftest.py → src/jobscraper/config.py
- `filters()` --uses--> `JobFilters`  [INFERRED]
  tests/test_matching.py → src/jobscraper/matching/filters.py

## Import Cycles
- None detected.

## Communities (140 total, 22 thin omitted)

### Community 0 - "StorageError"
Cohesion: 0.30
Nodes (15): Namespace, build_storage(), cmd_brief(), cmd_calibrate(), cmd_cleanup(), cmd_dashboard(), cmd_health(), cmd_publish() (+7 more)

### Community 1 - "test_matching.py"
Cohesion: 0.15
Nodes (37): process_jobs(), Run the Phase 3 and 4 steps in the order doc 04 gives: normalize, hard filters,…, factor(), job(), Any, parametrize, test_action_apply_now_when_deadline_close(), test_bonus_in_a_sentence_is_not_a_heading() (+29 more)

### Community 2 - "scorer.py"
Cohesion: 0.22
Nodes (15): field_validator, build_checklist(), build_explanation(), Explanation, Job, Gaps and recommendations (doc 06): transferable strengths, action, checklist., One primary action by rule, then advisories that must not be hidden by it., FR-9: for Top and Strong matches only. (+7 more)

### Community 3 - "scrapers/__init__.py"
Cohesion: 0.29
Nodes (5): Importing this package registers every built-in adapter., Any, parametrize, Contract tests against REAL saved responses (doc 11). Create the fixtures with…, test_adapter_still_understands_the_real_response()

### Community 4 - "load_fixture"
Cohesion: 0.06
Nodes (70): Run every enabled, verified source. One source failing never stops the rest., run_sources(), RunOutcome, check_source(), CheckResult, format_check(), ClientFactory, datetime (+62 more)

### Community 5 - "HttpClient"
Cohesion: 0.08
Nodes (30): Random, RobotFileParser, BlockedError, FetchError, NotFoundError, RateLimitedError, Exception types. Each maps to one source status in the runner., HTTP 401/403. Never retried, never worked around. (+22 more)

### Community 6 - "jobscraper/dashboard.py"
Cohesion: 0.26
Nodes (19): _breakdown(), build_dashboard(), build_from_storage(), _float(), _int(), _job_row(), _local_date(), _local_dt() (+11 more)

### Community 7 - "load_runtime_settings"
Cohesion: 0.27
Nodes (11): load_runtime_settings(), Path, Defaults, overridden by the file if it exists. `default_max_potential` comes…, Any, parametrize, Path, test_a_missing_file_means_defaults_and_scoring_supplies_max_potential(), test_bad_settings_fail_fast_with_a_clear_message() (+3 more)

### Community 8 - "test_health.py"
Cohesion: 0.11
Nodes (44): How a source ended a run (doc 07)., SourceStatus, alert_text(), _by_source(), evaluate_health(), Finding, format_health_table(), HealthSettings (+36 more)

### Community 9 - "SQLiteStorage"
Cohesion: 0.11
Nodes (24): Any, Job, Path, Validate table name against the whitelist and return the safe name., Simulate the owner editing a user column in the Sheet., SQLiteStorage, env(), mock_sources() (+16 more)

### Community 10 - "runner.py"
Cohesion: 0.10
Nodes (27): gate_reason(), One entry under `sources:` in sources.yaml., Return why a source may not run, or None when it passes the gate., SourceConfig, default_client_factory(), ClientFactory, datetime, Job (+19 more)

### Community 11 - "test_notifications.py"
Cohesion: 0.22
Nodes (22): Any, mock, parametrize, row(), test_job_block_follows_the_doc_04_layout(), test_job_block_variants(), test_long_messages_split_by_size(), test_many_jobs_split_into_messages_of_ten_without_repeats() (+14 more)

### Community 12 - "test_dashboard.py"
Cohesion: 0.21
Nodes (24): Job scraper: finds customer-care jobs from permitted sources., build(), job_row(), Any, record(), sheets(), tab(), test_a_changed_layout_is_reformatted() (+16 more)

### Community 13 - "Part B. Other job boards"
Cohesion: 0.07
Nodes (28): 0. Quick answers, A1. How filtering works, A2. Change filters with config only, A3. Soft preferences (no code), A4. Add a new kind of hard filter (recipe), A5. Other filter ideas, A6. After you change a filter, A7. Searching a different type of job entirely (+20 more)

### Community 14 - "digest.py"
Cohesion: 0.16
Nodes (23): clean(), format_follow_ups(), format_job(), _posted(), datetime, Build the Telegram digest and follow-up reminders from stored rows (doc 04, doc…, Unnotified Top and Strong jobs, plus up to `max_potential` recent Potential…, One safe line: no control or bidi characters, collapsed whitespace, length-… (+15 more)

### Community 15 - "package.json"
Cohesion: 0.04
Nodes (44): font, metadata, viewport, dependencies, @neondatabase/serverless, next, pg, react (+36 more)

### Community 16 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 17 - "Installation & Setup Guide"
Cohesion: 0.08
Nodes (22): 1. Find your Source IDs, 1. Using a Virtual Environment (Highly Recommended), 2. Installing Dependencies, 2. Run a Single Source, 3. Configuration, 3. How to Verify the Data, 🛠 Detailed Setup Steps, Installation & Setup Guide (+14 more)

### Community 18 - "test_security_checklist.py"
Cohesion: 0.12
Nodes (13): LogRecord, JsonFormatter, Strips query strings, tokens and registered secret values from messages., One JSON object per line. Extra context goes in `ctx`., RedactionFilter, capture_logs(), stop(), Any (+5 more)

### Community 19 - "Scorer"
Cohesion: 0.29
Nodes (5): Factor, Any, Job, Scorer, JobSkills

### Community 20 - "test_workflows.py"
Cohesion: 0.16
Nodes (20): load(), Any, parametrize, Path, Static checks that keep the workflows inside the rules in docs 08, 09 and 11.…, _requirement_blocks(), steps(), test_checkout_does_not_persist_credentials() (+12 more)

### Community 21 - "dedupe.py"
Cohesion: 0.07
Nodes (40): Counter, classify_location(), _is_location_segment(), LocationInfo, normalize_company(), normalize_title(), Pure normalization helpers for titles, companies and locations (doc 05). No…, Lowercase, drop bracketed text, location suffixes, punctuation and level noise. (+32 more)

### Community 22 - "notify.py"
Cohesion: 0.36
Nodes (6): Digest, deliver_digest(), Delivery, datetime, Send a planned digest and mark what was delivered, so nothing is sent twice…, Send one message at a time and mark its rows straight after it is delivered. If…

### Community 23 - "google_sheets.py"
Cohesion: 0.11
Nodes (22): Path, One CSV per table, for a quick look or for Looker Studio's file-upload…, write_csv_dir(), csv_value(), Any, datetime, Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data…, Days since 1899-12-30, the day-count Google Sheets uses for dates and times. (+14 more)

### Community 24 - "Neon"
Cohesion: 0.05
Nodes (36): Auth, 1. Install the Neon CLI, 2. Install the Neon MCP Server, 3. Install Neon Agent Skills, 4. Link Your Project and Get Started, Architecture: How to Use Neon, Backend Primitives, Bootstrap a New Project (+28 more)

### Community 25 - "GoogleSheetsStorage"
Cohesion: 0.12
Nodes (11): DashboardTable, col_letter(), GoogleSheetsStorage, Job, Add any missing columns at the end of the header row. Never reorders., One batched request, highest rows first so earlier row numbers stay valid., Rewrite each Dash_* tab completely. Looker Studio reads one worksheet per data…, 1-based column index to A1 letters. (+3 more)

### Community 26 - "himalayas.py"
Cohesion: 0.12
Nodes (31): make_job_id(), Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)., One unmapped record exactly as the source returned it., RawJob, geo_eligibility(), Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).…, clean_str(), html_to_text() (+23 more)

### Community 27 - "sqlite.py"
Cohesion: 0.13
Nodes (13): JobUpdate, BaseModel, What the dedupe step needs to know about a job already in storage., Changes to system-owned columns of an existing row. Never user columns., StoredJob, Everything dedupe needs about jobs already stored., Update system-owned columns of existing rows. User columns are never written., Postgres backend for local development. Same column rules as the Sheet.… (+5 more)

### Community 28 - "FakeNotifier"
Cohesion: 0.27
Nodes (9): FakeNotifier, run_once(), stored(), test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part(), test_follow_up_reminders_are_marked_and_not_repeated(), test_marking_failure_is_reported(), update_jobs(), test_nothing_is_ever_sent_twice() (+1 more)

### Community 29 - "Storage"
Cohesion: 0.09
Nodes (13): ABC, Job, Storage interface (doc 04). Backends never score, filter or notify., Append new rows. Never overwrites existing rows., Record one row in the Runs tab., job_ids already in the Excluded log, so they are not logged again., Every Jobs row as a header-name dictionary, for `brief` and `calibrate`., Record one row per source for this run (the Health tab). (+5 more)

### Community 30 - "TelegramNotifier"
Cohesion: 0.09
Nodes (21): Client, cmd_notify_test(), Notifier, ABC, Notifier interface (D17). A second channel is a new file that implements this., `sent` counts messages delivered in order. Sending stops at the first failure., Deliver plain-text messages in order. Never raises for delivery problems., Deliver one short alert. Returns whether it was delivered. (+13 more)

### Community 31 - "4. Step-by-step installation"
Cohesion: 0.15
Nodes (13): 4.0 What you need first, 4.10 Put it on GitHub (this is what makes it automatic), 4.11 Build the dashboard, 4.1 Get the code, 4.2 Local environment, 4.3 Telegram bot, 4.4 Google Sheet and service account, 4.5 Configure (+5 more)

### Community 32 - "filters.ts"
Cohesion: 0.14
Nodes (21): clamp(), clampLimit(), DEFAULT_TIERS, Filters, first(), int(), MAX_LIMIT, PAGE_SIZE (+13 more)

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

### Community 53 - "SchemaError"
Cohesion: 0.21
Nodes (7): HimalayasAdapter, JobicyAdapter, Response did not have the expected overall shape., SchemaError, FetchedResponse, Any, Minimal response object returned to adapters.

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

### Community 60 - "8. Running it day to day"
Cohesion: 0.40
Nodes (5): 8. Running it day to day, Common jobs, Daily (about 5 minutes), Weekly (about 15 minutes), What an alert means and what to do

### Community 61 - "SourceResult"
Cohesion: 0.16
Nodes (21): Per-source outcome recorded by the runner (doc 04)., SourceResult, Batch, build_digest(), DigestConfig, due_follow_ups(), has_problems(), Applied jobs whose follow-up date has arrived and has not been reminded yet.… (+13 more)

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

### Community 67 - "[id]/page.tsx"
Cohesion: 0.17
Nodes (22): dynamic, JobPage(), JobCard(), ScoreBadge(), SkillChips(), dayNumber(), daysBetween(), deadlineNote() (+14 more)

### Community 70 - "12. Quiz and FAQ"
Cohesion: 0.67
Nodes (3): 12. Quiz and FAQ, Question 1 (your question), Self-check quiz (click an answer line to reveal it)

### Community 71 - "models/__init__.py"
Cohesion: 0.10
Nodes (27): Pattern, _compile(), Exclusion, JobFilters, _keyword_regex(), Job, Match, Hard filters (doc 06, step 1). A job that fails is excluded, logged and never… (+19 more)

### Community 84 - "persist"
Cohesion: 0.22
Nodes (13): dedupe_jobs(), persist(), datetime, Job, Path, Re-add jobs from output/unsaved-*.json after a storage failure (doc 07). Jobs…, Phase 3 behaviour: no filters, no scoring., Write new rows, updates and excluded records. Retry once, then save locally… (+5 more)

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
Cohesion: 0.14
Nodes (5): _connect(), PostgresStorage, Any, Connection, Connect to Postgres, creating the configured database on first run.

### Community 92 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 93 - "run_publish"
Cohesion: 0.16
Nodes (15): check_guard(), Any, datetime, `python main.py publish` logic. The CLI/runner is the only place that wires…, Read the Sheet, apply the rules, and refresh Neon (unless dry-run). `load_rows`…, run_publish(), GuardError, RuntimeError (+7 more)

### Community 94 - "test_http.py"
Cohesion: 0.19
Nodes (24): URL failed the SSRF rules (doc 08)., UnsafeUrlError, default_resolver(), Resolve a hostname to its IP addresses., Any, mock, parametrize, test_429_not_retried_and_retry_after_capped() (+16 more)

### Community 95 - "build_rows"
Cohesion: 0.21
Nodes (16): _breakdown(), build_rows(), _names(), _or_none(), PublishPlan, Any, datetime, Turn Sheet rows into publishable Neon rows (doc 13). Pure functions, no I/O.… (+8 more)

### Community 96 - "settings.py"
Cohesion: 0.24
Nodes (14): ExperiencePoints, FilterSettings, FreshnessPoints, IndustryPoints, LocationPoints, ProfileTitles, BaseModel, Validated profile and scoring configuration (doc 06, doc 11). Every point value… (+6 more)

### Community 97 - "test_retention.py"
Cohesion: 0.29
Nodes (13): ago(), job_row(), plan(), stored(), test_a_plan_that_deletes_most_of_the_sheet_is_blocked(), test_dry_run_and_blocked_plans_change_nothing(), test_jobs_not_seen_for_a_week_become_inactive_once(), test_logs_and_audit_rows_use_their_own_ages() (+5 more)

### Community 98 - "greenhouse.py"
Cohesion: 0.10
Nodes (23): _board_entries(), GreenhouseAdapter, Greenhouse public job board adapter (one adapter for every company board).…, Return (token, company name) pairs, skipping invalid tokens., Any, _scrub(), JSON logging with a redaction filter (doc 07, doc 11)., _phone_sub() (+15 more)

### Community 99 - "11. Coding Standards"
Cohesion: 0.18
Nodes (11): 11. Coding Standards, Configuration, Definition of done (per task), Error handling, Git workflow, Language and tooling, Logging, Naming and style (+3 more)

### Community 100 - "test_neon_integration.py"
Cohesion: 0.31
Nodes (10): count(), fresh_schema(), datetime, fixture, Integration tests for the Neon writer. Skipped unless TEST_DATABASE_URL points…, rows(), test_failure_rolls_back_and_keeps_previous_rows(), test_publish_twice_is_idempotent() (+2 more)

### Community 101 - "Neon publish: wiring it into the repo"
Cohesion: 0.22
Nodes (8): 1. Dependencies and config, 2. CLI glue (adapt names to your `cli.py`), 3. Workflow (`.github/workflows/daily.yml`), 4. Order of work, 5. Doc updates, Behavior notes, Neon publish: wiring it into the repo, What I could not see (please check)

### Community 102 - "FilterPanel.tsx"
Cohesion: 0.17
Nodes (13): FilterDisclosure(), FilterPanel(), Opt, ORDER, OverviewStrip(), activeFilterCount(), FOUND_OPTIONS, sameTiers() (+5 more)

### Community 103 - "calibrate.py"
Cohesion: 0.33
Nodes (8): agreement_report(), Path, Calibration helpers (doc 06): label about 30 real jobs, then compare with the…, Newest first, spread across tiers so every tier gets looked at., read_labels(), select_for_labeling(), write_label_sheet(), test_calibration_export_and_report()

### Community 104 - "retention.py"
Cohesion: 0.21
Nodes (14): PublishSettings, BaseModel, The `publish:` block of config/settings.yaml. Every value has a safe default., _older_than(), plan_retention(), datetime, Retention (FR-13, doc 03): remove what has aged out, never touch what the owner…, Plan from the stored tables and, unless dry_run, apply. Raises StorageError on… (+6 more)

### Community 105 - "load_scoring"
Cohesion: 0.21
Nodes (12): _load(), load_profile(), load_scoring(), Any, Path, extractor(), filters(), profile() (+4 more)

### Community 106 - "Job dashboard (frontend)"
Cohesion: 0.33
Nodes (5): Before you trust it (O10), Job dashboard (frontend), Notes and decisions, Run locally (against local PostgreSQL), Structure

### Community 108 - "skills.py"
Cohesion: 0.27
Nodes (7): _kind_at(), _markers(), Skills extraction, version 1: a dictionary with synonyms, no machine learning…, (start, end, kind) for each heading that opens a required or preferred section., Section of a mention. No headings, or before the first one, means required., _requirement_lines(), SkillExtractor

### Community 109 - "test_storage.py"
Cohesion: 0.13
Nodes (15): FakeSpreadsheet, FakeWorksheet, Any, fixture, Applies deleteDimension requests in order, like the real batchUpdate., In-memory stand-in for gspread.Worksheet., read_cell(), storage() (+7 more)

### Community 115 - "queries.ts"
Cohesion: 0.20
Nodes (14): DatabaseConfigurationError, errorProperties(), getDatabaseUrl(), isRetryable(), NeonSql, query(), runQuery(), sleep() (+6 more)

### Community 117 - "make_job"
Cohesion: 0.20
Nodes (19): later(), make_job(), Any, datetime, Job, A normalized Job with sensible defaults. Override any field., run(), test_canonical_url_ignores_tracking_fragment_slash_case() (+11 more)

### Community 118 - "brief.py"
Cohesion: 0.32
Nodes (7): _breakdown(), _bullets(), find_row(), Any, Markdown job brief for CV and cover-letter help (FR-10). Built from the stored…, Exact job_id, or a unique prefix., render_brief()

### Community 119 - "years_asked"
Cohesion: 0.67
Nodes (3): First 'N years' phrase that sits next to the word 'experience'., years_asked(), test_years_asked()

### Community 120 - "breakdown.ts"
Cohesion: 0.22
Nodes (12): ScoreBar(), fmt(), ScoreBreakdown(), Factor, FACTOR_ORDER, factorFrom(), isObj(), LABELS (+4 more)

### Community 121 - "hybrid-search.md"
Cohesion: 0.43
Nodes (3): Adapt the Hybrid Search, Hybrid Search, RRF Example

### Community 123 - "rows.py"
Cohesion: 0.23
Nodes (10): One source's outcome in one run. The Health tab keeps these to spot trends (doc…, SourceRun, _int(), _parse_dt(), datetime, Column ownership and row conversion shared by every storage backend (doc 05).…, Rebuild a history record. Rows that cannot be read are skipped, not guessed., row_to_source_run() (+2 more)

### Community 124 - "Managing Lakebase Search with Drizzle"
Cohesion: 0.25
Nodes (8): BM25 Index, Config, Extensions, Generate and Store Embeddings, Managing Lakebase Search with Drizzle, Query, Schema, Tune Per Query

### Community 125 - "Claimable Neon"
Cohesion: 0.29
Nodes (6): Claim, Claimable Neon, If neon claim is missing, Path, With REST, With the CLI

### Community 126 - "ConfigError"
Cohesion: 0.18
Nodes (11): ConfigError, load_sources(), BaseModel, Exception, Path, Config loading and the source gate (doc 03)., Config file missing or invalid. Fail fast with a clear message., Read and validate sources.yaml. (+3 more)

### Community 127 - "app/page.tsx"
Cohesion: 0.38
Nodes (8): dynamic, Home(), pageWindow(), Pagination(), toQueryString(), filterOptions, listJobs(), overview

### Community 128 - "cli.py"
Cohesion: 0.11
Nodes (25): ArgumentParser, CLI entry point: python main.py run --dry-run --no-notify, _add_settings_arg(), _add_storage_args(), build_parser(), cmd_run(), datetime, Exception (+17 more)

### Community 129 - "ExcludedRecord"
Cohesion: 0.36
Nodes (4): ExcludedRecord, A job removed by a hard filter, kept in the Excluded tab as an audit trail., Record jobs removed by hard filters (audit trail, kept 30 days)., excluded_to_row()

### Community 130 - "Full-Text Search with BM25 Ranking"
Cohesion: 0.33
Nodes (6): Full-Text Search with BM25 Ranking, Prepare and Index Text, Query and Interpret Scores, Set Parameters at Build Time or Per Query, Set the Candidate Limit, Use Prefilter Selectively

### Community 131 - "Setup Flow"
Cohesion: 0.33
Nodes (6): 1. Select the organization and project, 2. Get the connection string, 3. Pick the connection method and driver, 4. Set up the schema, Setup Flow, When to use pooled vs direct connections

### Community 132 - "Troubleshooting and Neon-Specific Performance"
Cohesion: 0.33
Nodes (6): Choose CLI or MCP, Inspect Neon Cache Behavior Per Query, Interpret Results Safely, Performance Workflow, Pick the Diagnostic, Troubleshooting and Neon-Specific Performance

## Knowledge Gaps
- **450 isolated node(s):** `extends`, `next/core-web-vitals`, `dynamic`, `font`, `metadata` (+445 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 836 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Storage` connect `Storage` to `cli.py`, `StorageError`, `test_matching.py`, `ExcludedRecord`, `jobscraper/dashboard.py`, `models/__init__.py`, `retention.py`, `SQLiteStorage`, `PostgresStorage`, `persist`, `notify.py`, `google_sheets.py`, `GoogleSheetsStorage`, `sqlite.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `GoogleSheetsStorage` connect `GoogleSheetsStorage` to `cli.py`, `StorageError`, `ExcludedRecord`, `test_retention.py`, `Worksheet`, `sqlite.py`, `test_dashboard.py`, `test_storage.py`, `google_sheets.py`, `rows.py`, `FakeNotifier`, `Storage`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `StorageError` connect `StorageError` to `cli.py`, `HttpClient`, `models/__init__.py`, `SQLiteStorage`, `PostgresStorage`, `rows.py`, `test_storage.py`, `persist`, `notify.py`, `google_sheets.py`, `GoogleSheetsStorage`, `sqlite.py`, `FakeNotifier`, `TelegramNotifier`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SQLiteStorage` (e.g. with `DashboardTable` and `StorageError`) actually correct?**
  _`SQLiteStorage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `HttpClient` (e.g. with `Adapter` and `GreenhouseAdapter`) actually correct?**
  _`HttpClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `StorageError` (e.g. with `cmd_brief()` and `cmd_calibrate()`) actually correct?**
  _`StorageError` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Storage` (e.g. with `build_storage()` and `cmd_run()`) actually correct?**
  _`Storage` has 11 INFERRED edges - model-reasoned connections that need verification._