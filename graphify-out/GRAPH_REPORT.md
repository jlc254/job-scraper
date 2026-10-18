# Graph Report - job-scraper  (2026-10-18)

## Corpus Check
- 191 files · ~128,323 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 5, .example 2, .in 2)

## Summary
- 2105 nodes · 4640 edges · 148 communities (117 shown, 21 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 285 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4b1c20a2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- test_matching.py
- settings.py
- SourceResult
- load_fixture
- errors.py
- check_source
- SQLiteStorage
- test_health.py
- build_digest
- greenhouse.py
- Deduper
- test_dashboard.py
- Part B. Other job boards
- digest.py
- package.json
- What You Must Do When Invoked
- Installation & Setup Guide
- pipeline.py
- Job
- test_workflows.py
- normalize.py
- test_verify_vercel_project.py
- DashboardTable
- Neon
- GoogleSheetsStorage
- weworkremotely.py
- google_sheets.py
- build_parser
- Storage
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
- TelegramNotifier
- 07. Reliability and Monitoring
- 13. Neon Database, Migration and Publish Command
- graphify reference: query, path, explain
- 05. Data Model
- 7. How one run works, and what is stored where
- text.py
- 8. Running it day to day
- HttpClient
- models/__init__.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 5. The websites it reads
- [id]/page.tsx
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 12. Quiz and FAQ
- test_retention.py
- AGENTS.md
- extraction-spec.md
- PHASE2.md
- PHASE3.md
- PHASE4.md
- PHASE5.md
- ci_run.sh
- lock.sh
- jobscraper
- test_phase3.py
- 14. Frontend Dashboard
- Lakebase Postgres
- NeonError
- Semantic Vector Search
- PostgresStorage
- compilerOptions
- run_publish
- test_http.py
- build_rows
- queries.ts
- load_runtime_settings
- scrub_pii
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
- db.ts
- make_job
- brief.py
- FetchedResponse
- breakdown.ts
- hybrid-search.md
- SkillChips.tsx
- rows.py
- Managing Lakebase Search with Drizzle
- Claimable Neon
- ConfigError
- app/page.tsx
- FakeNotifier
- conftest.py
- Full-Text Search with BM25 Ranking
- Setup Flow
- Troubleshooting and Neon-Specific Performance
- sqlite.py
- save_sample
- Logs: CLI, Loki, and SDK pagination
- RobotsChecker
- .eslintrc.json
- function-triggers.md
- parse-env.md
- sdk.md
- check_guard
- urls.py
- verify_vercel_project.sh
- test_captured_fixtures.py
- Clock
- .to_job
- clear_registry_for_tests

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
10. `SourceResult` - 27 edges

## Surprising Connections (you probably didn't know these)
- `test_default_settings_match_the_plan()` --uses--> `HealthSettings`  [INFERRED]
  tests/test_health.py → src/jobscraper/utils/health.py
- `test_redaction_filter()` --uses--> `RedactionFilter`  [INFERRED]
  tests/test_helpers.py → src/jobscraper/utils/logging.py
- `_load_entries()` --indirect_call--> `profile()`  [INFERRED]
  src/jobscraper/cli.py → tests/test_matching.py
- `_load_entries()` --indirect_call--> `scoring()`  [INFERRED]
  src/jobscraper/cli.py → tests/test_matching.py
- `test_settings_defaults_and_errors()` --uses--> `ConfigError`  [INFERRED]
  tests/test_matching.py → src/jobscraper/config.py

## Import Cycles
- None detected.

## Communities (148 total, 21 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.09
Nodes (44): CLI entry point: python main.py run --dry-run --no-notify, Namespace, build_storage(), cmd_brief(), cmd_calibrate(), cmd_cleanup(), cmd_dashboard(), cmd_health() (+36 more)

### Community 1 - "test_matching.py"
Cohesion: 0.09
Nodes (54): Pattern, _compile(), Exclusion, JobFilters, _keyword_regex(), Job, Match, Hard filters (doc 06, step 1). A job that fails is excluded, logged and never… (+46 more)

### Community 2 - "settings.py"
Cohesion: 0.06
Nodes (57): field_validator, build_checklist(), build_explanation(), Explanation, Job, Gaps and recommendations (doc 06): transferable strengths, action, checklist., One primary action by rule, then advisories that must not be hidden by it., FR-9: for Top and Strong matches only. (+49 more)

### Community 3 - "SourceResult"
Cohesion: 0.21
Nodes (12): datetime, Exception, Job, Filter, score, store, notify and refresh the dashboard for ONE profile. Returns…, _run_profile(), run_row(), _warn(), Per-source outcome recorded by the runner (doc 04). (+4 more)

### Community 4 - "load_fixture"
Cohesion: 0.19
Nodes (27): Run every enabled, verified source. One source failing never stops the rest., run_sources(), RunOutcome, load_fixture(), Any, factory(), Any, mock (+19 more)

### Community 5 - "errors.py"
Cohesion: 0.11
Nodes (24): BlockedError, FetchError, NotFoundError, RateLimitedError, Exception types. Each maps to one source status in the runner., HTTP 401/403. Never retried, never worked around., HTTP 429. The source is marked rate_limited for this run., Response exceeded the size cap. (+16 more)

### Community 6 - "check_source"
Cohesion: 0.18
Nodes (23): check_source(), CheckResult, format_check(), Any, ClientFactory, Path, (extension, text) for a captured response: personal data removed, a few items…, Save the first captured response. Review the file before committing it. (+15 more)

### Community 7 - "SQLiteStorage"
Cohesion: 0.10
Nodes (25): Job scraper: finds customer-care jobs from permitted sources., Any, Job, Path, Validate table name against the whitelist and return the safe name., Simulate the owner editing a user column in the Sheet., SQLiteStorage, env() (+17 more)

### Community 8 - "test_health.py"
Cohesion: 0.16
Nodes (32): How a source ended a run (doc 07)., SourceStatus, alert_text(), _by_source(), evaluate_health(), Finding, format_health_table(), needs_attention() (+24 more)

### Community 9 - "build_digest"
Cohesion: 0.13
Nodes (21): Batch, build_digest(), has_problems(), The RUN line from doc 04, for example: 4 sources ok, 1 degraded (Jobicy: 0…, Plan the messages. An empty digest is only worth sending in the morning, or…, One message and the rows it covers, so only delivered rows are marked as sent., run_summary(), applied() (+13 more)

### Community 10 - "greenhouse.py"
Cohesion: 0.16
Nodes (26): One unmapped record exactly as the source returned it., RawJob, _board_entries(), GreenhouseAdapter, Greenhouse public job board adapter (one adapter for every company board).…, Return (token, company name) pairs, skipping invalid tokens., HimalayasAdapter, JobicyAdapter (+18 more)

### Community 11 - "Deduper"
Cohesion: 0.22
Nodes (11): Deduper, _Entry, format_salary(), datetime, Job, Add one candidate. Returns True if it became a new job, False if merged., Merge policy: union URLs, prefer the employer's domain, keep richest values.…, Human-readable salary for the Sheet. Never converts currency (doc 05). (+3 more)

### Community 12 - "test_dashboard.py"
Cohesion: 0.10
Nodes (45): _breakdown(), build_dashboard(), build_from_storage(), _float(), _int(), _job_row(), _local_date(), _local_dt() (+37 more)

### Community 13 - "Part B. Other job boards"
Cohesion: 0.07
Nodes (28): 0. Quick answers, A1. How filtering works, A2. Change filters with config only, A3. Soft preferences (no code), A4. Add a new kind of hard filter (recipe), A5. Other filter ideas, A6. After you change a filter, A7. Searching a different type of job entirely (+20 more)

### Community 14 - "digest.py"
Cohesion: 0.15
Nodes (26): clean(), DigestConfig, due_follow_ups(), format_follow_ups(), format_job(), _posted(), datetime, Build the Telegram digest and follow-up reminders from stored rows (doc 04, doc… (+18 more)

### Community 15 - "package.json"
Cohesion: 0.04
Nodes (46): font, metadata, viewport, dependencies, @neondatabase/serverless, next, pg, react (+38 more)

### Community 16 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 17 - "Installation & Setup Guide"
Cohesion: 0.08
Nodes (22): 1. Find your Source IDs, 1. Using a Virtual Environment (Highly Recommended), 2. Installing Dependencies, 2. Run a Single Source, 3. Configuration, 3. How to Verify the Data, 🛠 Detailed Setup Steps, Installation & Setup Guide (+14 more)

### Community 18 - "pipeline.py"
Cohesion: 0.21
Nodes (16): Counter, dedupe_jobs(), persist(), process_jobs(), datetime, Job, Path, Normalize, filter, dedupe, score and persist. The runner fetches; this decides… (+8 more)

### Community 19 - "Job"
Cohesion: 0.21
Nodes (10): Job, BaseModel, What the dedupe step needs to know about a job already in storage., Common job schema (subset of doc 05 that Phase 2 can fill). Fingerprint,…, StoredJob, normalize_company(), Lowercase, remove punctuation and trailing legal suffixes., Everything dedupe needs about jobs already stored. (+2 more)

### Community 20 - "test_workflows.py"
Cohesion: 0.15
Nodes (22): load(), Any, parametrize, Path, Static checks that keep the workflows inside the rules in docs 08, 09 and 11.…, _requirement_blocks(), steps(), test_checkout_does_not_persist_credentials() (+14 more)

### Community 21 - "normalize.py"
Cohesion: 0.17
Nodes (14): classify_location(), _is_location_segment(), LocationInfo, normalize_title(), Pure normalization helpers for titles, companies and locations (doc 05). No…, Lowercase, drop bracketed text, location suffixes, punctuation and level noise., Read free-text location. Conservative: unknown stays unknown., fingerprint() (+6 more)

### Community 22 - "test_verify_vercel_project.py"
Cohesion: 0.22
Nodes (24): CompletedProcess, MakeApp, make_app(), project(), Any, fixture, parametrize, Path (+16 more)

### Community 23 - "DashboardTable"
Cohesion: 0.10
Nodes (22): csv_value(), DashboardTable, Any, datetime, Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data…, Days since 1899-12-30, the day-count Google Sheets uses for dates and times., A cell value for a RAW Sheets write: blanks as "", dates as serials, text made…, A cell value for a CSV export: ISO dates, true/false, formula-safe text. (+14 more)

### Community 24 - "Neon"
Cohesion: 0.05
Nodes (36): Auth, 1. Install the Neon CLI, 2. Install the Neon MCP Server, 3. Install Neon Agent Skills, 4. Link Your Project and Get Started, Architecture: How to Use Neon, Backend Primitives, Bootstrap a New Project (+28 more)

### Community 25 - "GoogleSheetsStorage"
Cohesion: 0.16
Nodes (7): col_letter(), GoogleSheetsStorage, Job, Add any missing columns at the end of the header row. Never reorders., One batched request, highest rows first so earlier row numbers stay valid., 1-based column index to A1 letters., test_col_letter()

### Community 26 - "weworkremotely.py"
Cohesion: 0.12
Nodes (22): geo_eligibility(), Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).…, clean_str(), parse_date(), Cut at max_chars, preferring a word boundary. 0 returns an empty string., Return a stripped non-empty string, else None., Accept only absolute http(s) URLs. Anything else is dropped., Parse unix seconds/milliseconds or ISO-8601 strings to a UTC date. (+14 more)

### Community 27 - "google_sheets.py"
Cohesion: 0.29
Nodes (5): ExcludedRecord, A job removed by a hard filter, kept in the Excluded tab as an audit trail., Record jobs removed by hard filters (audit trail, kept 30 days)., Google Sheets backend (D3). Columns are addressed by header name, never…, excluded_to_row()

### Community 28 - "build_parser"
Cohesion: 0.53
Nodes (6): ArgumentParser, _add_profile_args(), _add_settings_arg(), _add_storage_args(), build_parser(), `--profiles` is the profiles.yaml path. `--for` picks one profile for single-…

### Community 29 - "Storage"
Cohesion: 0.09
Nodes (14): ABC, Job, Storage interface (doc 04). Backends never score, filter or notify., Append new rows. Never overwrites existing rows., Update system-owned columns of existing rows. User columns are never written., Record one row in the Runs tab., job_ids already in the Excluded log, so they are not logged again., Every Jobs row as a header-name dictionary, for `brief` and `calibrate`. (+6 more)

### Community 30 - "test_security_checklist.py"
Cohesion: 0.12
Nodes (13): LogRecord, JsonFormatter, Strips query strings, tokens and registered secret values from messages., One JSON object per line. Extra context goes in `ctx`., RedactionFilter, capture_logs(), stop(), Any (+5 more)

### Community 31 - "4. Step-by-step installation"
Cohesion: 0.15
Nodes (13): 4.0 What you need first, 4.10 Put it on GitHub (this is what makes it automatic), 4.11 Build the dashboard, 4.1 Get the code, 4.2 Local environment, 4.3 Telegram bot, 4.4 Google Sheet and service account, 4.5 Configure (+5 more)

### Community 32 - "filters.ts"
Cohesion: 0.19
Nodes (18): pageWindow(), Pagination(), activeFilterCount(), clamp(), clampLimit(), DEFAULT_TIERS, first(), int() (+10 more)

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

### Community 53 - "TelegramNotifier"
Cohesion: 0.14
Nodes (12): Client, _describe(), _Permanent, Exception, Response, Telegram's own error text and retry_after, if the body is the expected JSON., Do not retry: bad token, blocked bot, unknown chat, rejected message., TelegramNotifier (+4 more)

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

### Community 59 - "text.py"
Cohesion: 0.18
Nodes (9): HTMLParser, html_to_text(), HTML to plain text, truncation and small value helpers. Pure functions., Strip tags and return plain text. Scraped content is data, never markup., For feeds that deliver HTML entity-escaped HTML (Greenhouse `content`)., _TextExtractor, unescape_then_text(), test_html_to_text_strips_tags_and_scripts() (+1 more)

### Community 60 - "8. Running it day to day"
Cohesion: 0.40
Nodes (5): 8. Running it day to day, Common jobs, Daily (about 5 minutes), Weekly (about 15 minutes), What an alert means and what to do

### Community 61 - "HttpClient"
Cohesion: 0.10
Nodes (30): gate_reason(), BaseModel, Config loading and the source gate (doc 03)., One entry under `sources:` in sources.yaml., Return why a source may not run, or None when it passes the gate., SourceConfig, SourcesFile, default_client_factory() (+22 more)

### Community 62 - "models/__init__.py"
Cohesion: 0.23
Nodes (15): EmploymentType, ExperienceLevel, make_job_id(), Pydantic models shared by adapters, runner and (later) storage., Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)., RemoteEligibility, WorkType, _as_str_list() (+7 more)

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
Nodes (28): dynamic, JobPage(), FilterPanel(), JobCard(), OverviewStrip(), ScoreBadge(), fmt(), ScoreBreakdown() (+20 more)

### Community 70 - "12. Quiz and FAQ"
Cohesion: 0.67
Nodes (3): 12. Quiz and FAQ, Question 1 (your question), Self-check quiz (click an answer line to reveal it)

### Community 71 - "test_retention.py"
Cohesion: 0.17
Nodes (21): _older_than(), plan_retention(), datetime, Retention (FR-13, doc 03): remove what has aged out, never touch what the owner…, Plan from the stored tables and, unless dry_run, apply. Raises StorageError on…, Unreadable or empty timestamps are never treated as old, so nothing is deleted…, RetentionPlan, run_retention() (+13 more)

### Community 84 - "test_phase3.py"
Cohesion: 0.27
Nodes (8): Importing this package registers every built-in adapter., Any, mock, test_company_domain_only_for_employer_sites(), test_jobicy_fetch_and_map(), test_normalize_job_reads_location_text(), test_three_sources_merge_across_boards_and_second_run_adds_nothing(), test_weworkremotely_fetch_and_map()

### Community 87 - "14. Frontend Dashboard"
Cohesion: 0.08
Nodes (25): 14. Frontend Dashboard, Apply button, Data access, Decisions (add to the log in doc 00), Display rules, End-to-end checklist (manual, before deploy), Environment variables, Filters and sorting (+17 more)

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
Cohesion: 0.15
Nodes (5): _connect(), PostgresStorage, Any, Connection, Connect to Postgres, creating the configured database on first run.

### Community 92 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 93 - "run_publish"
Cohesion: 0.16
Nodes (19): RowLoader, datetime, `python main.py publish` logic. The CLI/runner is the only place that wires…, Read each profile's Sheet, apply the rules, and refresh that profile's slice of…, run_publish(), PublishSettings, BaseModel, The `publish:` block of config/settings.yaml. Every value has a safe default. (+11 more)

### Community 94 - "test_http.py"
Cohesion: 0.20
Nodes (23): URL failed the SSRF rules (doc 08)., UnsafeUrlError, default_resolver(), Resolve a hostname to its IP addresses., Any, mock, parametrize, test_429_not_retried_and_retry_after_capped() (+15 more)

### Community 95 - "build_rows"
Cohesion: 0.21
Nodes (16): _breakdown(), build_rows(), _names(), _or_none(), PublishPlan, Any, datetime, Turn Sheet rows into publishable Neon rows (doc 13). Pure functions, no I/O.… (+8 more)

### Community 96 - "queries.ts"
Cohesion: 0.17
Nodes (13): ORDER, Filters, PAGE_SIZE, buildListQuery(), JOB_COLUMNS, ListQuery, ORDER_BY, FilterOptions (+5 more)

### Community 97 - "load_runtime_settings"
Cohesion: 0.21
Nodes (17): RetentionSettings, _build(), load_runtime_settings(), Any, Path, Optional config/settings.yaml: thresholds for health alarms, retention and the…, Defaults, overridden by the file if it exists. `default_max_potential` comes…, RuntimeSettings (+9 more)

### Community 98 - "scrub_pii"
Cohesion: 0.24
Nodes (11): _phone_sub(), Match, Remove emails and phone numbers from text before it is stored (D8)., Return text with emails and phone numbers replaced by placeholders., scrub_pii(), Any, parametrize, test_csv_formula_prefix() (+3 more)

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
Cohesion: 0.20
Nodes (6): FilterDisclosure(), Opt, FOUND_OPTIONS, TIERS, WORK_TYPES, react

### Community 103 - "test_notifications.py"
Cohesion: 0.28
Nodes (17): Any, mock, parametrize, test_parse_user_date(), test_posted_text(), test_rows_that_are_not_notified(), test_rows_that_are_notified(), test_telegram_alert_is_prefixed_and_capped() (+9 more)

### Community 104 - "15. Multi-profile"
Cohesion: 0.14
Nodes (13): 15. Multi-profile, Dashboard without a login, Database migration, Decisions (add to the log in doc 00), Deferred, Edits to the pages (not seen, so described), Files in this drop, How a run works now (+5 more)

### Community 105 - "notify.py"
Cohesion: 0.17
Nodes (12): Notifier, ABC, Notifier interface (D17). A second channel is a new file that implements this., Deliver one short alert. Returns whether it was delivered., Digest, Telegram Bot API notifier. Plain text only, sent to one configured chat (doc…, deliver_digest(), Delivery (+4 more)

### Community 106 - "Job dashboard (frontend)"
Cohesion: 0.33
Nodes (5): Before you trust it (O10), Job dashboard (frontend), Notes and decisions, Run locally (against local PostgreSQL), Structure

### Community 108 - "neon"
Cohesion: 0.22
Nodes (3): neon(), fixture, A fake storage.neon so these tests need neither psycopg nor a database.

### Community 109 - "test_storage.py"
Cohesion: 0.13
Nodes (16): test_writing_dashboard_tabs_needs_the_spreadsheet_handle(), FakeSpreadsheet, FakeWorksheet, Any, fixture, Applies deleteDimension requests in order, like the real batchUpdate., In-memory stand-in for gspread.Worksheet., read_cell() (+8 more)

### Community 115 - "db.ts"
Cohesion: 0.27
Nodes (10): DatabaseConfigurationError, errorProperties(), getDatabaseUrl(), isRetryable(), NeonSql, query(), runQuery(), sleep() (+2 more)

### Community 117 - "make_job"
Cohesion: 0.19
Nodes (21): later(), make_job(), Any, datetime, Job, A normalized Job with sensible defaults. Override any field., Any, parametrize (+13 more)

### Community 118 - "brief.py"
Cohesion: 0.47
Nodes (5): _breakdown(), _bullets(), Any, Markdown job brief for CV and cover-letter help (FR-10). Built from the stored…, render_brief()

### Community 119 - "FetchedResponse"
Cohesion: 0.40
Nodes (3): FetchedResponse, Any, Minimal response object returned to adapters.

### Community 120 - "breakdown.ts"
Cohesion: 0.27
Nodes (10): ScoreBar(), Factor, FACTOR_ORDER, factorFrom(), isObj(), LABELS, num(), parseBreakdown() (+2 more)

### Community 121 - "hybrid-search.md"
Cohesion: 0.43
Nodes (3): Adapt the Hybrid Search, Hybrid Search, RRF Example

### Community 123 - "rows.py"
Cohesion: 0.20
Nodes (12): One source's outcome in one run. The Health tab keeps these to spot trends (doc…, SourceRun, _int(), _parse_dt(), datetime, Column ownership and row conversion shared by every storage backend (doc 05).…, Rebuild what dedupe needs from a stored row. Rows without a job_id are skipped., Rebuild a history record. Rows that cannot be read are skipped, not guessed. (+4 more)

### Community 124 - "Managing Lakebase Search with Drizzle"
Cohesion: 0.25
Nodes (8): BM25 Index, Config, Extensions, Generate and Store Embeddings, Managing Lakebase Search with Drizzle, Query, Schema, Tune Per Query

### Community 125 - "Claimable Neon"
Cohesion: 0.29
Nodes (6): Claim, Claimable Neon, If neon claim is missing, Path, With REST, With the CLI

### Community 126 - "ConfigError"
Cohesion: 0.11
Nodes (36): cmd_run(), ProfileContext, Everything one profile needs for its stage of a run., ConfigError, load_sources(), Exception, Path, Config file missing or invalid. Fail fast with a clear message. (+28 more)

### Community 127 - "app/page.tsx"
Cohesion: 0.24
Nodes (12): dynamic, Home(), ProfileSwitcher(), RawParams, labelMap(), listProfiles, loadProfiles(), ProfileInfo (+4 more)

### Community 128 - "FakeNotifier"
Cohesion: 0.19
Nodes (11): `sent` counts messages delivered in order. Sending stops at the first failure., Deliver plain-text messages in order. Never raises for delivery problems., SendResult, FakeNotifier, run_once(), stored(), test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part(), test_follow_up_reminders_are_marked_and_not_repeated() (+3 more)

### Community 129 - "conftest.py"
Cohesion: 0.22
Nodes (9): Random, Resolver, make_client(), factory(), now(), datetime, fixture, Sleeper (+1 more)

### Community 130 - "Full-Text Search with BM25 Ranking"
Cohesion: 0.33
Nodes (6): Full-Text Search with BM25 Ranking, Prepare and Index Text, Query and Interpret Scores, Set Parameters at Build Time or Per Query, Set the Candidate Limit, Use Prefilter Selectively

### Community 131 - "Setup Flow"
Cohesion: 0.33
Nodes (6): 1. Select the organization and project, 2. Get the connection string, 3. Pick the connection method and driver, 4. Set up the schema, Setup Flow, When to use pooled vs direct connections

### Community 132 - "Troubleshooting and Neon-Specific Performance"
Cohesion: 0.33
Nodes (6): Choose CLI or MCP, Inspect Neon Cache Behavior Per Query, Interpret Results Safely, Performance Workflow, Pick the Diagnostic, Troubleshooting and Neon-Specific Performance

### Community 133 - "sqlite.py"
Cohesion: 0.15
Nodes (10): JobUpdate, Changes to system-owned columns of an existing row. Never user columns., Job, Postgres backend for local development. Same column rules as the Sheet.…, job_to_row(), Job, Refuse any write to a user-owned or unknown column., System columns for a new job, plus the initial application_status. (+2 more)

### Community 134 - "save_sample"
Cohesion: 0.22
Nodes (11): Any, datetime, Path, Make a scraped record safe to keep: no emails or phones, no URL queries,…, Write up to three sanitized records that failed parsing, for debugging a layout…, sanitize_value(), save_sample(), to_source_runs() (+3 more)

### Community 136 - "RobotsChecker"
Cohesion: 0.25
Nodes (4): RobotFileParser, Whether robots.txt allows this URL. Unreadable robots.txt means no (doc 03)., Caches one parsed robots.txt per host for the lifetime of a run. `fetch_text`…, RobotsChecker

### Community 141 - "check_guard"
Cohesion: 0.32
Nodes (8): check_guard(), GuardError, RuntimeError, Refuse to replace a healthy copy with an empty or collapsed one. Zero rows is…, Publishing would wipe or collapse the existing copy., test_guard_allows_exactly_half(), test_guard_collapse_blocked_unless_forced(), test_guard_zero_rows_blocked_even_with_force()

### Community 142 - "urls.py"
Cohesion: 0.39
Nodes (7): employer_domain(), _host_in(), host_of(), URL canonicalization and host classification for dedupe (doc 05)., Host of the URL if it looks like the employer's own site, else None., 3 = employer domain, 2 = ATS board, 1 = aggregator or unknown., url_rank()

### Community 143 - "verify_vercel_project.sh"
Cohesion: 0.70
Nodes (4): check_build(), check_link(), resolve_app_root(), verify_vercel_project.sh script

### Community 144 - "test_captured_fixtures.py"
Cohesion: 0.40
Nodes (4): Any, parametrize, Contract tests against REAL saved responses (doc 11). Create the fixtures with…, test_adapter_still_understands_the_real_response()

### Community 145 - "Clock"
Cohesion: 0.40
Nodes (3): Clock, fixture, tg()

## Knowledge Gaps
- **463 isolated node(s):** `extends`, `next/core-web-vitals`, `dynamic`, `font`, `metadata` (+458 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 888 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLiteStorage` connect `SQLiteStorage` to `cli.py`, `test_matching.py`, `FakeNotifier`, `load_fixture`, `sqlite.py`, `test_retention.py`, `test_health.py`, `rows.py`, `test_dashboard.py`, `test_storage.py`, `test_phase3.py`, `DashboardTable`, `google_sheets.py`, `Storage`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `StorageError` connect `cli.py` to `FakeNotifier`, `SourceResult`, `sqlite.py`, `errors.py`, `SQLiteStorage`, `notify.py`, `PostgresStorage`, `rows.py`, `test_storage.py`, `pipeline.py`, `TelegramNotifier`, `DashboardTable`, `GoogleSheetsStorage`, `google_sheets.py`, `ConfigError`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `Worksheet` connect `Worksheet` to `GoogleSheetsStorage`, `google_sheets.py`, `DashboardTable`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SQLiteStorage` (e.g. with `DashboardTable` and `StorageError`) actually correct?**
  _`SQLiteStorage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `HttpClient` (e.g. with `Adapter` and `GreenhouseAdapter`) actually correct?**
  _`HttpClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `StorageError` (e.g. with `cmd_brief()` and `cmd_calibrate()`) actually correct?**
  _`StorageError` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Storage` (e.g. with `build_storage()` and `cmd_run()`) actually correct?**
  _`Storage` has 13 INFERRED edges - model-reasoned connections that need verification._