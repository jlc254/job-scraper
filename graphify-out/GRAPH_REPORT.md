# Graph Report - job-scraper  (2026-10-24)

## Corpus Check
- 216 files · ~181,502 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 5, .example 2, .in 2)

## Summary
- 2475 nodes · 5129 edges · 177 communities (144 shown, 20 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 285 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d93fb560`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- test_matching.py
- Scorer
- cmd_run
- load_fixture
- HttpClient
- jobscraper/dashboard.py
- test_cli_run.py
- SourceResult
- build_digest
- source_check.py
- TelegramNotifier
- models/__init__.py
- Part B. Other job boards
- digest.py
- package.json
- What You Must Do When Invoked
- Installation & Setup Guide
- Storage
- servers
- test_workflows.py
- dedupe.py
- test_verify_vercel_project.py
- google_sheets.py
- Neon
- StorageError
- jobicy.py
- job_to_row
- calibrate.py
- build_parser
- test_security_checklist.py
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
- test_captured_fixtures.py
- 07. Reliability and Monitoring
- 13. Neon Database, Migration and Publish Command
- graphify reference: query, path, explain
- 05. Data Model
- 7. How one run works, and what is stored where
- Managed Better Auth: implement login
- 8. Running it day to day
- Adapter
- scorer.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 5. The websites it reads
- [id]/page.tsx
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 12. Quiz and FAQ
- Lakebase Postgres Branching
- AGENTS.md
- extraction-spec.md
- PHASE2.md
- PHASE3.md
- PHASE4.md
- PHASE5.md
- ci_run.sh
- lock.sh
- jobscraper
- test_dashboard.py
- 14. Frontend Dashboard
- Lakebase Postgres
- NeonError
- Semantic Vector Search
- PostgresStorage
- compilerOptions
- run_publish
- test_http.py
- build_rows
- test_retention.py
- load_runtime_settings
- Neon Functions
- 11. Coding Standards
- NeonPublisher
- Neon publish: wiring it into the repo
- FilterPanel.tsx
- test_notifications.py
- 15. Multi-profile
- notify.py
- Job dashboard (frontend)
- next.config.mjs
- neon
- test_storage.py
- next-env.d.ts
- queries.ts
- _NeonHandler
- brief.py
- make_job
- breakdown.ts
- Neon AI Gateway
- sqlite.py
- Managing Lakebase Search with Drizzle
- Claimable Neon
- ConfigError
- app/page.tsx
- FakeNotifier
- Postgres Egress Optimizer
- Full-Text Search with BM25 Ranking
- Setup Flow
- Troubleshooting and Neon-Specific Performance
- postgres.py
- SQLiteStorage
- Logs: CLI, Loki, and SDK pagination
- Neon Object Storage
- .eslintrc.json
- function-triggers.md
- parse-env.md
- sdk.md
- check_guard
- Client-side reactivity
- verify_vercel_project.sh
- Server-side rendering
- Clock
- Function Triggers
- Optimistic mutations
- Subscribing to queries
- Defining queries
- filters.py
- Sentry (errors, logs, and traces)
- Neon Realtime
- load_scoring
- Production hardening for Neon Functions
- Mastra agents with Mastra Studio observability
- Shipping native binaries with a Function
- Server-sent events (SSE) on Neon Functions
- AI SDK agents on Neon Functions
- MCP servers on Neon Functions
- Defining live queries
- neon_preview_branch.sh
- WebSocket Servers
- Hybrid Search
- test_normalize_company
- pipeline.py
- skills.py
- settings.py
- test_helpers.py
- retention.py
- JobUpdate
- _TextExtractor
- FetchedResponse
- .from_env
- fixture

## God Nodes (most connected - your core abstractions)
1. `SQLiteStorage` - 44 edges
2. `HttpClient` - 42 edges
3. `StorageError` - 41 edges
4. `make_job()` - 40 edges
5. `Storage` - 38 edges
6. `ConfigError` - 36 edges
7. `GoogleSheetsStorage` - 36 edges
8. `cmd_run()` - 34 edges
9. `load_fixture()` - 28 edges
10. `make_app()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `test_redaction_filter()` --uses--> `RedactionFilter`  [INFERRED]
  tests/test_helpers.py → src/jobscraper/utils/logging.py
- `_load_entries()` --indirect_call--> `profile()`  [INFERRED]
  src/jobscraper/cli.py → tests/test_matching.py
- `_load_entries()` --indirect_call--> `scoring()`  [INFERRED]
  src/jobscraper/cli.py → tests/test_matching.py
- `test_settings_defaults_and_errors()` --uses--> `ConfigError`  [INFERRED]
  tests/test_matching.py → src/jobscraper/config.py
- `test_bad_settings_fail_fast_with_a_clear_message()` --uses--> `ConfigError`  [INFERRED]
  tests/test_runtime_settings.py → src/jobscraper/config.py

## Import Cycles
- None detected.

## Communities (177 total, 20 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.15
Nodes (28): CLI entry point: python main.py run --dry-run --no-notify, Namespace, build_storage(), cmd_brief(), cmd_calibrate(), cmd_cleanup(), cmd_dashboard(), cmd_health() (+20 more)

### Community 1 - "test_matching.py"
Cohesion: 0.17
Nodes (33): factor(), job(), Any, parametrize, test_action_apply_now_when_deadline_close(), test_bonus_in_a_sentence_is_not_a_heading(), test_breakdown_is_json_serialisable_and_versioned(), test_experience_points() (+25 more)

### Community 2 - "Scorer"
Cohesion: 0.24
Nodes (7): Factor, Any, Job, First 'N years' phrase that sits next to the word 'experience'., Scorer, years_asked(), JobSkills

### Community 3 - "cmd_run"
Cohesion: 0.15
Nodes (16): cmd_run(), ProfileContext, datetime, Exception, Job, Everything one profile needs for its stage of a run., Filter, score, store, notify and refresh the dashboard for ONE profile. Returns…, _run_profile() (+8 more)

### Community 4 - "load_fixture"
Cohesion: 0.08
Nodes (52): Run every enabled, verified source. One source failing never stops the rest., run_sources(), RunOutcome, load_fixture(), make_client(), factory(), now(), Any (+44 more)

### Community 5 - "HttpClient"
Cohesion: 0.06
Nodes (44): Random, RobotFileParser, default_client_factory(), ClientFactory, datetime, Job, Path, Runner: the only place that wires config, adapters and the HTTP client together. (+36 more)

### Community 6 - "jobscraper/dashboard.py"
Cohesion: 0.26
Nodes (19): _breakdown(), build_dashboard(), build_from_storage(), _float(), _int(), _job_row(), _local_date(), _local_dt() (+11 more)

### Community 7 - "test_cli_run.py"
Cohesion: 0.24
Nodes (19): Job scraper: finds customer-care jobs from permitted sources., env(), mock_sources(), Any, fixture, mock, Path, The whole `run` command against SQLite, with HTTP mocked. No network, no… (+11 more)

### Community 8 - "SourceResult"
Cohesion: 0.09
Nodes (51): Per-source outcome recorded by the runner (doc 04)., How a source ended a run (doc 07)., SourceResult, SourceStatus, format_report(), datetime, CSV export and the plain-text run report (doc 07 format)., alert_text() (+43 more)

### Community 9 - "build_digest"
Cohesion: 0.17
Nodes (18): Batch, build_digest(), DigestConfig, due_follow_ups(), format_follow_ups(), Applied jobs whose follow-up date has arrived and has not been reminded yet.…, The RUN line from doc 04, for example: 4 sources ok, 1 degraded (Jobicy: 0…, Plan the messages. An empty digest is only worth sending in the morning, or… (+10 more)

### Community 10 - "source_check.py"
Cohesion: 0.11
Nodes (36): gate_reason(), BaseModel, Config loading and the source gate (doc 03)., One entry under `sources:` in sources.yaml., Return why a source may not run, or None when it passes the gate., SourceConfig, SourcesFile, get_adapter_class() (+28 more)

### Community 11 - "TelegramNotifier"
Cohesion: 0.14
Nodes (13): Client, cmd_notify_test(), _describe(), _Permanent, Exception, Response, Telegram's own error text and retry_after, if the body is the expected JSON., Do not retry: bad token, blocked bot, unknown chat, rejected message. (+5 more)

### Community 12 - "models/__init__.py"
Cohesion: 0.11
Nodes (27): EmploymentType, ExperienceLevel, Job, Pydantic models shared by adapters, runner and (later) storage., Common job schema (subset of doc 05 that Phase 2 can fill). Fingerprint,…, RemoteEligibility, WorkType, classify_location() (+19 more)

### Community 13 - "Part B. Other job boards"
Cohesion: 0.07
Nodes (28): 0. Quick answers, A1. How filtering works, A2. Change filters with config only, A3. Soft preferences (no code), A4. Add a new kind of hard filter (recipe), A5. Other filter ideas, A6. After you change a filter, A7. Searching a different type of job entirely (+20 more)

### Community 14 - "digest.py"
Cohesion: 0.17
Nodes (22): clean(), format_job(), has_problems(), _posted(), datetime, Build the Telegram digest and follow-up reminders from stored rows (doc 04, doc…, Unnotified Top and Strong jobs, plus up to `max_potential` recent Potential…, One safe line: no control or bidi characters, collapsed whitespace, length-… (+14 more)

### Community 15 - "package.json"
Cohesion: 0.04
Nodes (44): font, metadata, viewport, dependencies, @neondatabase/serverless, next, pg, react (+36 more)

### Community 16 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 17 - "Installation & Setup Guide"
Cohesion: 0.08
Nodes (22): 1. Find your Source IDs, 1. Using a Virtual Environment (Highly Recommended), 2. Installing Dependencies, 2. Run a Single Source, 3. Configuration, 3. How to Verify the Data, 🛠 Detailed Setup Steps, Installation & Setup Guide (+14 more)

### Community 18 - "Storage"
Cohesion: 0.09
Nodes (14): ABC, Job, Storage interface (doc 04). Backends never score, filter or notify., Everything dedupe needs about jobs already stored., Append new rows. Never overwrites existing rows., Record one row in the Runs tab., job_ids already in the Excluded log, so they are not logged again., Every Jobs row as a header-name dictionary, for `brief` and `calibrate`. (+6 more)

### Community 19 - "servers"
Cohesion: 0.20
Nodes (9): mcp, servers, type, url, $schema, neon, vercel, type (+1 more)

### Community 20 - "test_workflows.py"
Cohesion: 0.14
Nodes (26): load(), Any, parametrize, Path, Static checks that keep the workflows inside the rules in docs 08, 09 and 11.…, _requirement_blocks(), steps(), test_checkout_does_not_persist_credentials() (+18 more)

### Community 21 - "dedupe.py"
Cohesion: 0.12
Nodes (23): Counter, normalize_company(), Lowercase, remove punctuation and trailing legal suffixes., Deduper, _Entry, format_salary(), datetime, Job (+15 more)

### Community 22 - "test_verify_vercel_project.py"
Cohesion: 0.14
Nodes (45): MakeApp, _EnvHandler, make_app(), preview_env_vars(), preview_secrets_env(), project(), Any, BaseHTTPRequestHandler (+37 more)

### Community 23 - "google_sheets.py"
Cohesion: 0.18
Nodes (15): csv_value(), Any, datetime, Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data…, Days since 1899-12-30, the day-count Google Sheets uses for dates and times., A cell value for a RAW Sheets write: blanks as "", dates as serials, text made…, A cell value for a CSV export: ISO dates, true/false, formula-safe text., sheet_serial() (+7 more)

### Community 24 - "Neon"
Cohesion: 0.05
Nodes (36): Auth, 1. Install the Neon CLI, 2. Install the Neon MCP Server, 3. Install Neon Agent Skills, 4. Link Your Project and Get Started, Architecture: How to Use Neon, Backend Primitives, Bootstrap a New Project (+28 more)

### Community 25 - "StorageError"
Cohesion: 0.14
Nodes (11): DashboardTable, col_letter(), GoogleSheetsStorage, Job, Add any missing columns at the end of the header row. Never reorders., One batched request, highest rows first so earlier row numbers stay valid., Rewrite each Dash_* tab completely. Looker Studio reads one worksheet per data…, 1-based column index to A1 letters. (+3 more)

### Community 26 - "jobicy.py"
Cohesion: 0.10
Nodes (37): make_job_id(), Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)., One unmapped record exactly as the source returned it., RawJob, geo_eligibility(), Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).…, clean_str(), html_to_text() (+29 more)

### Community 27 - "job_to_row"
Cohesion: 0.29
Nodes (5): Job, job_to_row(), Job, System columns for a new job, plus the initial application_status., Job

### Community 28 - "calibrate.py"
Cohesion: 0.33
Nodes (8): agreement_report(), Path, Calibration helpers (doc 06): label about 30 real jobs, then compare with the…, Newest first, spread across tiers so every tier gets looked at., read_labels(), select_for_labeling(), write_label_sheet(), test_calibration_export_and_report()

### Community 29 - "build_parser"
Cohesion: 0.53
Nodes (6): ArgumentParser, _add_profile_args(), _add_settings_arg(), _add_storage_args(), build_parser(), `--profiles` is the profiles.yaml path. `--for` picks one profile for single-…

### Community 30 - "test_security_checklist.py"
Cohesion: 0.11
Nodes (15): LogRecord, JsonFormatter, Strips query strings, tokens and registered secret values from messages., One JSON object per line. Extra context goes in `ctx`., Configure the root logger once. Logs go to stderr so stdout stays clean., RedactionFilter, setup_logging(), capture_logs() (+7 more)

### Community 31 - "4. Step-by-step installation"
Cohesion: 0.15
Nodes (13): 4.0 What you need first, 4.10 Put it on GitHub (this is what makes it automatic), 4.11 Build the dashboard, 4.1 Get the code, 4.2 Local environment, 4.3 Telegram bot, 4.4 Google Sheet and service account, 4.5 Configure (+5 more)

### Community 32 - "filters.ts"
Cohesion: 0.14
Nodes (23): activeFilterCount(), clamp(), clampLimit(), DEFAULT_TIERS, Filters, first(), int(), MAX_LIMIT (+15 more)

### Community 33 - "test_publish.py"
Cohesion: 0.15
Nodes (27): dropped(), make_row(), one(), parametrize, Unit tests for publish.py and publish_cli.py (no network, no psycopg)., test_age_rule_and_keep_statuses(), test_bad_first_seen_dropped(), test_bad_urls_dropped() (+19 more)

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
Cohesion: 0.20
Nodes (9): 09. Scheduling and Setup, Account status (1 Oct 2026), Cost, Deploy secrets (Vercel and Neon), Options compared, Schedule, Secrets, Setup guide (+1 more)

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

### Community 53 - "test_captured_fixtures.py"
Cohesion: 0.40
Nodes (4): Any, parametrize, Contract tests against REAL saved responses (doc 11). Create the fixtures with…, test_adapter_still_understands_the_real_response()

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

### Community 59 - "Managed Better Auth: implement login"
Cohesion: 0.08
Nodes (23): Auth emails, Cross-subdomain vs bearer JWT, Data API identity, Environment, Managed Better Auth: implement login, Next.js, Organization invitations, Packages (+15 more)

### Community 60 - "8. Running it day to day"
Cohesion: 0.40
Nodes (5): 8. Running it day to day, Common jobs, Daily (about 5 minutes), Weekly (about 15 minutes), What an alert means and what to do

### Community 61 - "Adapter"
Cohesion: 0.10
Nodes (21): Adapter, ABC, datetime, Job, Adapter contract (doc 04). Adapters return data. They never write or notify., One adapter per source (one per ATS platform)., Return raw records. May raise a FetchError subclass., Map one raw record to the common schema, or None if unusable. (+13 more)

### Community 62 - "scorer.py"
Cohesion: 0.22
Nodes (15): field_validator, build_checklist(), build_explanation(), Explanation, Job, Gaps and recommendations (doc 06): transferable strengths, action, checklist., One primary action by rule, then advisories that must not be hidden by it., FR-9: for Top and Strong matches only. (+7 more)

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
Cohesion: 0.15
Nodes (28): dynamic, JobPage(), FilterPanel(), JobCard(), ScoreBadge(), ScoreBar(), fmt(), ScoreBreakdown() (+20 more)

### Community 70 - "12. Quiz and FAQ"
Cohesion: 0.67
Nodes (3): 12. Quiz and FAQ, Question 1 (your question), Self-check quiz (click an answer line to reveal it)

### Community 71 - "Lakebase Postgres Branching"
Cohesion: 0.08
Nodes (25): Beta Support Guidance (Mandatory), Branch Type Decision, Branching in CI/CD, CLI usage, Console and API usage, Create a Normal Branch (Preferred for Real-Data Migration Testing), Create a Schema-Only Branch (Beta, Sensitive Data), Example 1: Migration testing with realistic data (+17 more)

### Community 84 - "test_dashboard.py"
Cohesion: 0.24
Nodes (23): build(), job_row(), Any, record(), sheets(), tab(), test_a_changed_layout_is_reformatted(), test_a_refresh_replaces_everything_and_does_not_reformat_an_unchanged_layout() (+15 more)

### Community 87 - "14. Frontend Dashboard"
Cohesion: 0.07
Nodes (26): 14. Frontend Dashboard, Apply button, Data access, Decisions (add to the log in doc 00), Display rules, End-to-end checklist (manual, before deploy), Environment variables, Filters and sorting (+18 more)

### Community 88 - "Lakebase Postgres"
Cohesion: 0.15
Nodes (13): Autoscaling, Branching, Connection Pooling, Gotchas, Instant Restore, IP Allow Lists, Lakebase Postgres, Lakebase Search (+5 more)

### Community 89 - "NeonError"
Cohesion: 0.16
Nodes (14): _adapt(), NeonError, Any, Connection, datetime, Exception, RuntimeError, Write-only Neon copy (doc 13, doc 15). Not a full Storage implementation. What:… (+6 more)

### Community 90 - "Semantic Vector Search"
Cohesion: 0.18
Nodes (11): AI SDK (Recommended), Build the Index, Contents, Create the Extension, OpenAI SDK Alternative, Prepare Embeddings, Query, Semantic Vector Search (+3 more)

### Community 91 - "PostgresStorage"
Cohesion: 0.11
Nodes (9): What the dedupe step needs to know about a job already in storage., StoredJob, _connect(), PostgresStorage, Any, Connection, Connect to Postgres, creating the configured database on first run., Rebuild what dedupe needs from a stored row. Rows without a job_id are skipped. (+1 more)

### Community 92 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 93 - "run_publish"
Cohesion: 0.16
Nodes (19): RowLoader, datetime, `python main.py publish` logic. The CLI/runner is the only place that wires…, Read each profile's Sheet, apply the rules, and refresh that profile's slice of…, run_publish(), PublishSettings, BaseModel, The `publish:` block of config/settings.yaml. Every value has a safe default. (+11 more)

### Community 94 - "test_http.py"
Cohesion: 0.25
Nodes (19): Any, mock, parametrize, test_429_not_retried_and_retry_after_capped(), test_gives_up_after_three_attempts(), test_host_outside_allowlist_rejected(), test_no_retry_statuses(), test_non_https_rejected() (+11 more)

### Community 95 - "build_rows"
Cohesion: 0.21
Nodes (16): _breakdown(), build_rows(), _names(), _or_none(), PublishPlan, Any, datetime, Turn Sheet rows into publishable Neon rows (doc 13). Pure functions, no I/O.… (+8 more)

### Community 96 - "test_retention.py"
Cohesion: 0.29
Nodes (13): ago(), job_row(), plan(), stored(), test_a_plan_that_deletes_most_of_the_sheet_is_blocked(), test_dry_run_and_blocked_plans_change_nothing(), test_jobs_not_seen_for_a_week_become_inactive_once(), test_logs_and_audit_rows_use_their_own_ages() (+5 more)

### Community 97 - "load_runtime_settings"
Cohesion: 0.19
Nodes (15): _build(), load_runtime_settings(), Any, Path, Optional config/settings.yaml: thresholds for health alarms, retention and the…, Defaults, overridden by the file if it exists. `default_max_potential` comes…, RuntimeSettings, Any (+7 more)

### Community 98 - "Neon Functions"
Cohesion: 0.09
Nodes (22): Application instrumentation, Architecture: Where Functions Fit, Availability, Built-in branch logs, Connecting to Postgres, Develop Locally and Deploy, Environment Variables, Function Triggers (+14 more)

### Community 99 - "11. Coding Standards"
Cohesion: 0.18
Nodes (11): 11. Coding Standards, Configuration, Definition of done (per task), Error handling, Git workflow, Language and tooling, Logging, Naming and style (+3 more)

### Community 100 - "NeonPublisher"
Cohesion: 0.22
Nodes (13): BaseException, NeonPublisher, count(), fresh_schema(), datetime, fixture, Integration tests for the Neon writer. Skipped unless TEST_DATABASE_URL points…, rows() (+5 more)

### Community 101 - "Neon publish: wiring it into the repo"
Cohesion: 0.22
Nodes (8): 1. Dependencies and config, 2. CLI glue (adapt names to your `cli.py`), 3. Workflow (`.github/workflows/daily.yml`), 4. Order of work, 5. Doc updates, Behavior notes, Neon publish: wiring it into the repo, What I could not see (please check)

### Community 102 - "FilterPanel.tsx"
Cohesion: 0.25
Nodes (6): FilterDisclosure(), Opt, FOUND_OPTIONS, TIERS, WORK_TYPES, react

### Community 103 - "test_notifications.py"
Cohesion: 0.20
Nodes (24): Any, mock, parametrize, row(), test_detailed_report_only_when_a_source_has_problems(), test_follow_up_is_seven_days_after_applied_unless_overridden(), test_job_block_follows_the_doc_04_layout(), test_job_block_variants() (+16 more)

### Community 104 - "15. Multi-profile"
Cohesion: 0.14
Nodes (13): 15. Multi-profile, Dashboard without a login, Database migration, Decisions (add to the log in doc 00), Deferred, Edits to the pages (not seen, so described), Files in this drop, How a run works now (+5 more)

### Community 105 - "notify.py"
Cohesion: 0.14
Nodes (14): Notifier, ABC, Notifier interface (D17). A second channel is a new file that implements this., `sent` counts messages delivered in order. Sending stops at the first failure., Deliver plain-text messages in order. Never raises for delivery problems., Deliver one short alert. Returns whether it was delivered., SendResult, Digest (+6 more)

### Community 106 - "Job dashboard (frontend)"
Cohesion: 0.33
Nodes (5): Before you trust it (O10), Job dashboard (frontend), Notes and decisions, Run locally (against local PostgreSQL), Structure

### Community 108 - "neon"
Cohesion: 0.22
Nodes (3): neon(), fixture, A fake storage.neon so these tests need neither psycopg nor a database.

### Community 109 - "test_storage.py"
Cohesion: 0.11
Nodes (17): FakeBook, FakeSpreadsheet, FakeWorksheet, Any, fixture, Applies deleteDimension requests in order, like the real batchUpdate., In-memory stand-in for gspread.Worksheet., Stand-in for a gspread Spreadsheet: lists tabs and can add new ones. (+9 more)

### Community 115 - "queries.ts"
Cohesion: 0.15
Nodes (21): Home(), DatabaseConfigurationError, errorProperties(), getDatabaseUrl(), isRetryable(), NeonSql, query(), runQuery() (+13 more)

### Community 117 - "_NeonHandler"
Cohesion: 0.20
Nodes (20): branch(), neon_api(), _NeonHandler, Any, BaseHTTPRequestHandler, CompletedProcess, fixture, parametrize (+12 more)

### Community 118 - "brief.py"
Cohesion: 0.32
Nodes (7): _breakdown(), _bullets(), find_row(), Any, Markdown job brief for CV and cover-letter help (FR-10). Built from the stored…, Exact job_id, or a unique prefix., render_brief()

### Community 119 - "make_job"
Cohesion: 0.20
Nodes (19): later(), make_job(), Any, datetime, Job, A normalized Job with sensible defaults. Override any field., run(), test_canonical_url_ignores_tracking_fragment_slash_case() (+11 more)

### Community 120 - "breakdown.ts"
Cohesion: 0.30
Nodes (9): Factor, FACTOR_ORDER, factorFrom(), isObj(), LABELS, num(), parseBreakdown(), ParsedBreakdown (+1 more)

### Community 122 - "Neon AI Gateway"
Cohesion: 0.12
Nodes (16): Availability, Build Agents with Mastra (Recommended), Build Agents with the Vercel AI SDK (Recommended), Enabling the gateway: plan and model access, Environment Variables, Further Reading, Generate Embeddings with the AI SDK, List Available Models at Runtime (`/v1/models`) (+8 more)

### Community 123 - "sqlite.py"
Cohesion: 0.21
Nodes (11): One source's outcome in one run. The Health tab keeps these to spot trends (doc…, SourceRun, _int(), _parse_dt(), datetime, Column ownership and row conversion shared by every storage backend (doc 05).…, Rebuild a history record. Rows that cannot be read are skipped, not guessed., row_to_source_run() (+3 more)

### Community 124 - "Managing Lakebase Search with Drizzle"
Cohesion: 0.25
Nodes (8): BM25 Index, Config, Extensions, Generate and Store Embeddings, Managing Lakebase Search with Drizzle, Query, Schema, Tune Per Query

### Community 125 - "Claimable Neon"
Cohesion: 0.29
Nodes (6): Claim, Claimable Neon, If neon claim is missing, Path, With REST, With the CLI

### Community 126 - "ConfigError"
Cohesion: 0.13
Nodes (30): ConfigError, Exception, Config file missing or invalid. Fail fast with a clear message., _check_unique(), enabled_profiles(), _entry(), legacy_profile(), load_profiles() (+22 more)

### Community 127 - "app/page.tsx"
Cohesion: 0.19
Nodes (13): dynamic, ORDER, OverviewStrip(), pageWindow(), Pagination(), ProfileSwitcher(), RawParams, withProfile() (+5 more)

### Community 128 - "FakeNotifier"
Cohesion: 0.27
Nodes (9): FakeNotifier, run_once(), stored(), test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part(), test_follow_up_reminders_are_marked_and_not_repeated(), test_marking_failure_is_reported(), update_jobs(), test_nothing_is_ever_sent_twice() (+1 more)

### Community 129 - "Postgres Egress Optimizer"
Cohesion: 0.12
Nodes (16): Application-side aggregation, Check if pg_stat_statements is available, Diagnostic queries, Further Reading, Handle empty stats, High-frequency queries on static data, Interpret the results, JOIN duplication (+8 more)

### Community 130 - "Full-Text Search with BM25 Ranking"
Cohesion: 0.33
Nodes (6): Full-Text Search with BM25 Ranking, Prepare and Index Text, Query and Interpret Scores, Set Parameters at Build Time or Per Query, Set the Candidate Limit, Use Prefilter Selectively

### Community 131 - "Setup Flow"
Cohesion: 0.33
Nodes (6): 1. Select the organization and project, 2. Get the connection string, 3. Pick the connection method and driver, 4. Set up the schema, Setup Flow, When to use pooled vs direct connections

### Community 132 - "Troubleshooting and Neon-Specific Performance"
Cohesion: 0.33
Nodes (6): Choose CLI or MCP, Inspect Neon Cache Behavior Per Query, Interpret Results Safely, Performance Workflow, Pick the Diagnostic, Troubleshooting and Neon-Specific Performance

### Community 133 - "postgres.py"
Cohesion: 0.17
Nodes (8): ExcludedRecord, A job removed by a hard filter, kept in the Excluded tab as an audit trail., Record jobs removed by hard filters (audit trail, kept 30 days)., __getattr__(), Storage backends (doc 04). Backends never score, filter or notify. This package…, Lazily import backends so ``import jobscraper.storage`` stays light., Postgres backend for local development. Same column rules as the Sheet.…, excluded_to_row()

### Community 134 - "SQLiteStorage"
Cohesion: 0.16
Nodes (6): Any, Path, Validate table name against the whitelist and return the safe name., Stored as JSON with the same cell values the Sheet gets (dates as serial…, Simulate the owner editing a user column in the Sheet., SQLiteStorage

### Community 136 - "Neon Object Storage"
Cohesion: 0.12
Nodes (15): Architecture: Where Object Storage Fits, Availability, Built-in Branch Logs, CLI Bucket and Object Commands, Environment Variables, Further Reading, Neon Documentation, Neon Infrastructure as Code (`neon.ts`) (+7 more)

### Community 141 - "check_guard"
Cohesion: 0.32
Nodes (8): check_guard(), GuardError, RuntimeError, Refuse to replace a healthy copy with an empty or collapsed one. Zero rows is…, Publishing would wipe or collapse the existing copy., test_guard_allows_exactly_half(), test_guard_collapse_blocked_unless_forced(), test_guard_zero_rows_blocked_even_with_force()

### Community 142 - "Client-side reactivity"
Cohesion: 0.12
Nodes (16): Changing query parameters, Client-side reactivity, Contents, Create the collection, Handling errors, initialData, Manage optimistic state, Other frameworks (+8 more)

### Community 143 - "verify_vercel_project.sh"
Cohesion: 0.46
Nodes (7): check_build(), check_link(), check_preview_env(), check_preview_secrets(), check_secrets(), resolve_app_root(), verify_vercel_project.sh script

### Community 144 - "Server-side rendering"
Cohesion: 0.13
Nodes (15): Contents, Create a `DbClient` per router, Define the collection, Examples, Keep row shapes identical, Keep secrets on the server, Open the connection in the browser, Render the initial rows straight away (+7 more)

### Community 145 - "Clock"
Cohesion: 0.40
Nodes (3): Clock, fixture, tg()

### Community 146 - "Function Triggers"
Cohesion: 0.15
Nodes (13): CLI, Delivery payload, Fields, Function Triggers, Inheritance, Local `neon dev`, Logs, MCP backup (+5 more)

### Community 147 - "Optimistic mutations"
Cohesion: 0.15
Nodes (13): Automatic management of optimistic state, Calling the routes from the frontend, Contents, How optimistic mutations work, Optimistic mutations, Render the app, Returning the `txid` from your backend, Running example (+5 more)

### Community 148 - "Subscribing to queries"
Cohesion: 0.15
Nodes (13): Contents, Debug subscriptions, Fetch from a server function, Fetch from an API endpoint, Getting the query to subscribe to, Handle errors, Listen for changes, Log client diagnostics (+5 more)

### Community 149 - "Defining queries"
Cohesion: 0.17
Nodes (12): Authorization, Contents, Defining queries, Exposing an endpoint, Exposing queries, Live authorization, Renewing sealed queries, Sealing authorized queries (+4 more)

### Community 150 - "filters.py"
Cohesion: 0.21
Nodes (12): Pattern, _compile(), Exclusion, JobFilters, _keyword_regex(), Job, Match, Hard filters (doc 06, step 1). A job that fails is excluded, logged and never… (+4 more)

### Community 151 - "Sentry (errors, logs, and traces)"
Cohesion: 0.20
Nodes (10): 1. Initialize before anything else, 2. Provide the DSN as a deploy-time secret, 3. Create the request span and catch route errors, 4. Errors are for failures; logs are for the story, 5. Trace the agent itself, Environment variables, Other Node integrations, Sentry error monitoring on Neon Functions (+2 more)

### Community 152 - "Neon Realtime"
Cohesion: 0.20
Nodes (10): Choose the Stack, Core Pattern, Define and Seal Queries, How It Works, More Docs, Neon Realtime, Optimistic Writes, Server-Side Rendering (+2 more)

### Community 153 - "load_scoring"
Cohesion: 0.27
Nodes (11): _load(), load_profile(), load_scoring(), Any, Path, profile(), scoring(), Path (+3 more)

### Community 154 - "Production hardening for Neon Functions"
Cohesion: 0.22
Nodes (9): Choose the caller shape, Function Triggers only, Limit authenticated application work, Native URL, Preserve existing clients, Production hardening for Neon Functions, Public consumers through a Worker, Reject these (+1 more)

### Community 155 - "Mastra agents with Mastra Studio observability"
Cohesion: 0.25
Nodes (8): 1. Define the agent against the Neon AI Gateway, 2. Wire observability to Mastra Studio, 3. Structured output through the gateway, 4. Create the Mastra project + token with the CLI, 5. Pass the creds via `neon.ts` (third-party env), 6. Verify, Further reading, Mastra agents with Mastra Studio observability

### Community 156 - "Shipping native binaries with a Function"
Cohesion: 0.25
Nodes (7): `bundler: "none"`: ship a prebuilt directory, Custom `bundler`: return the file map, `externalPackages`: npm packages with a Node addon, Shipping native binaries with a Function, Size limits, Standalone executables, The runtime a binary lands on

### Community 157 - "Server-sent events (SSE) on Neon Functions"
Cohesion: 0.25
Nodes (7): Caveats, Client, Minimal SSE endpoint (no framework), Push to every client, across isolates, Server-sent events (SSE) on Neon Functions, Wire format (just text), With Hono

### Community 159 - "AI SDK agents on Neon Functions"
Cohesion: 0.29
Nodes (7): 1. Declare the gateway and the function, 2. The handler: stream a tool-calling agent, 3. Generate images and persist them, 4. Call it directly from the client (don't proxy the stream), 5. Run and deploy, AI SDK agents on Neon Functions, Further reading

### Community 160 - "MCP servers on Neon Functions"
Cohesion: 0.33
Nodes (6): Authenticating the server, MCP servers on Neon Functions, Option 1 — OAuth via the Better Auth MCP plugin (best for third-party clients), Option 2 — API key or session JWT via self-hosted Better Auth (simplest), Testing, The server

### Community 162 - "Defining live queries"
Cohesion: 0.33
Nodes (6): Defining live queries, Parameter types, Query parameters, Table requirements, Using a query builder or ORM, Using raw SQL

### Community 163 - "neon_preview_branch.sh"
Cohesion: 0.80
Nodes (4): delete(), find_branch(), neon_preview_branch.sh script, verify()

### Community 164 - "WebSocket Servers"
Cohesion: 0.50
Nodes (4): Client must reconnect, Fan-out across isolates (do not skip this), Heartbeat (keep the socket alive), WebSocket Servers

### Community 165 - "Hybrid Search"
Cohesion: 0.50
Nodes (4): Adapt the Hybrid Search, Hybrid Search, Rerank with Jev, RRF Example

### Community 166 - "test_normalize_company"
Cohesion: 0.67
Nodes (4): Any, parametrize, test_normalize_company(), test_normalize_title()

### Community 167 - "pipeline.py"
Cohesion: 0.20
Nodes (18): dedupe_jobs(), persist(), process_jobs(), datetime, Job, Path, Normalize, filter, dedupe, score and persist. The runner fetches; this decides…, Re-add jobs from output/unsaved-*.json after a storage failure (doc 07). Jobs… (+10 more)

### Community 168 - "skills.py"
Cohesion: 0.17
Nodes (12): _kind_at(), _markers(), Skills extraction, version 1: a dictionary with synonyms, no machine learning…, (start, end, kind) for each heading that opens a required or preferred section., Section of a mention. No headings, or before the first one, means required., _requirement_lines(), SkillExtractor, found() (+4 more)

### Community 169 - "settings.py"
Cohesion: 0.24
Nodes (14): ExperiencePoints, FreshnessPoints, IndustryPoints, LocationPoints, ProfileTitles, BaseModel, Validated profile and scoring configuration (doc 06, doc 11). Every point value…, SalaryFloor (+6 more)

### Community 170 - "test_helpers.py"
Cohesion: 0.23
Nodes (11): Any, parametrize, test_csv_formula_prefix(), test_html_to_text_strips_tags_and_scripts(), test_parse_date_variants(), test_pii_keeps_salaries(), test_pii_removed(), test_redaction_filter() (+3 more)

### Community 171 - "retention.py"
Cohesion: 0.35
Nodes (9): _older_than(), plan_retention(), datetime, Retention (FR-13, doc 03): remove what has aged out, never touch what the owner…, Plan from the stored tables and, unless dry_run, apply. Raises StorageError on…, Unreadable or empty timestamps are never treated as old, so nothing is deleted…, RetentionPlan, RetentionSettings (+1 more)

### Community 172 - "JobUpdate"
Cohesion: 0.22
Nodes (7): JobUpdate, BaseModel, Changes to system-owned columns of an existing row. Never user columns., Update system-owned columns of existing rows. User columns are never written., Refuse any write to a user-owned or unknown column., validate_update(), test_update_of_protected_column_is_refused()

### Community 174 - "FetchedResponse"
Cohesion: 0.40
Nodes (3): FetchedResponse, Any, Minimal response object returned to adapters.

### Community 176 - "fixture"
Cohesion: 0.50
Nodes (4): extractor(), filters(), fixture, scorer()

## Knowledge Gaps
- **692 isolated node(s):** `extends`, `next/core-web-vitals`, `dynamic`, `font`, `metadata` (+687 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1131 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLiteStorage` connect `SQLiteStorage` to `cli.py`, `FakeNotifier`, `test_retention.py`, `load_fixture`, `postgres.py`, `test_cli_run.py`, `job_to_row`, `SourceResult`, `PostgresStorage`, `pipeline.py`, `JobUpdate`, `test_storage.py`, `Storage`, `test_dashboard.py`, `StorageError`, `sqlite.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `FakeWorksheet` connect `test_storage.py` to `FakeNotifier`, `test_retention.py`, `test_notifications.py`, `test_dashboard.py`, `StorageError`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `Storage` connect `Storage` to `cli.py`, `cmd_run`, `postgres.py`, `jobscraper/dashboard.py`, `pipeline.py`, `SQLiteStorage`, `notify.py`, `retention.py`, `JobUpdate`, `sqlite.py`, `google_sheets.py`, `StorageError`, `PostgresStorage`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SQLiteStorage` (e.g. with `DashboardTable` and `StorageError`) actually correct?**
  _`SQLiteStorage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `HttpClient` (e.g. with `Adapter` and `GreenhouseAdapter`) actually correct?**
  _`HttpClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `StorageError` (e.g. with `cmd_brief()` and `cmd_calibrate()`) actually correct?**
  _`StorageError` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Storage` (e.g. with `build_storage()` and `cmd_run()`) actually correct?**
  _`Storage` has 13 INFERRED edges - model-reasoned connections that need verification._