# Graph Report - job-scraper  (2026-10-26)

## Corpus Check
- 218 files · ~187,390 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 5, .example 2, .in 2)

## Summary
- 2515 nodes · 5264 edges · 167 communities (132 shown, 22 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 291 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5b75647b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_notifications.py
- test_matching.py
- models/__init__.py
- ConfigError
- jobicy.py
- HttpClient
- google_sheets.py
- SQLiteStorage
- test_health.py
- Managed Better Auth: implement login
- runner.py
- test_security_checklist.py
- Lakebase Postgres Branching
- Part B. Other job boards
- digest.py
- package.json
- What You Must Do When Invoked
- Installation & Setup Guide
- make_job
- servers
- test_workflows.py
- dedupe.py
- test_verify_vercel_project.py
- notify.py
- Neon
- GoogleSheetsStorage
- himalayas.py
- pipeline.py
- test_phase3.py
- TelegramNotifier
- Neon Functions
- 4. Step-by-step installation
- filters.ts
- test_publish.py
- test_pin_actions.py
- 02. Source Catalog
- 03. Legal and Responsible Use
- 04. Architecture
- 10. Development Plan
- 11. What each phase handled
- load_scoring
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
- Deduper
- 07. Reliability and Monitoring
- 13. Neon Database, Migration and Publish Command
- graphify reference: query, path, explain
- 05. Data Model
- 7. How one run works, and what is stored where
- Scorer
- 8. Running it day to day
- source_check.py
- Storage
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 5. The websites it reads
- [id]/page.tsx
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 12. Quiz and FAQ
- test_dashboard.py
- AGENTS.md
- extraction-spec.md
- PHASE2.md
- PHASE3.md
- PHASE4.md
- PHASE5.md
- ci_run.sh
- lock.sh
- jobscraper
- Neon AI Gateway
- 14. Frontend Dashboard
- Lakebase Postgres
- NeonPublisher
- Semantic Vector Search
- PostgresStorage
- compilerOptions
- run_publish
- test_http.py
- build_rows
- skills.py
- jobscraper/dashboard.py
- Postgres Egress Optimizer
- 11. Coding Standards
- .__exit__
- Neon publish: wiring it into the repo
- Worksheet
- Neon Object Storage
- 15. Multi-profile
- Client-side reactivity
- Job dashboard (frontend)
- next.config.mjs
- neon
- test_storage.py
- next-env.d.ts
- queries.ts
- _NeonHandler
- Server-side rendering
- settings.py
- breakdown.ts
- JobFilters
- app/page.tsx
- Managing Lakebase Search with Drizzle
- Claimable Neon
- FilterPanel.tsx
- db.ts
- _TextExtractor
- test_adapters.py
- Full-Text Search with BM25 Ranking
- Setup Flow
- Troubleshooting and Neon-Specific Performance
- SkillChips.tsx
- Function Triggers
- Logs: CLI, Loki, and SDK pagination
- Optimistic mutations
- .eslintrc.json
- function-triggers.md
- parse-env.md
- sdk.md
- Subscribing to queries
- cli.py
- verify_vercel_project.sh
- Defining queries
- test_language_filter.py
- conftest.py
- Sentry (errors, logs, and traces)
- Neon Realtime
- FakeNotifier
- logging.py
- Production hardening for Neon Functions
- Clock
- Mastra agents with Mastra Studio observability
- Shipping native binaries with a Function
- Server-sent events (SSE) on Neon Functions
- AI SDK agents on Neon Functions
- test_normalize_company
- MCP servers on Neon Functions
- Defining live queries
- WebSocket Servers
- neon_preview_branch.sh
- Hybrid Search
- test_refresh_dashboard_from_a_real_store
- 2026-10-26-widen-community-profile.md

## God Nodes (most connected - your core abstractions)
1. `SQLiteStorage` - 44 edges
2. `HttpClient` - 42 edges
3. `make_job()` - 42 edges
4. `StorageError` - 41 edges
5. `Storage` - 38 edges
6. `ConfigError` - 36 edges
7. `GoogleSheetsStorage` - 36 edges
8. `make_app()` - 36 edges
9. `cmd_run()` - 34 edges
10. `load_fixture()` - 28 edges

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

## Communities (167 total, 22 thin omitted)

### Community 0 - "test_notifications.py"
Cohesion: 0.18
Nodes (26): due_ids(), Any, mock, parametrize, row(), test_detailed_report_only_when_a_source_has_problems(), test_follow_up_is_seven_days_after_applied_unless_overridden(), test_follow_up_reminded_once_per_due_date() (+18 more)

### Community 1 - "test_matching.py"
Cohesion: 0.10
Nodes (48): _breakdown(), _bullets(), Any, Markdown job brief for CV and cover-letter help (FR-10). Built from the stored…, render_brief(), extractor(), factor(), filters() (+40 more)

### Community 2 - "models/__init__.py"
Cohesion: 0.17
Nodes (20): field_validator, build_checklist(), build_explanation(), Explanation, Job, Gaps and recommendations (doc 06): transferable strengths, action, checklist., One primary action by rule, then advisories that must not be hidden by it., FR-9: for Top and Strong matches only. (+12 more)

### Community 3 - "ConfigError"
Cohesion: 0.10
Nodes (41): cmd_run(), ProfileContext, Everything one profile needs for its stage of a run., ConfigError, load_sources(), Exception, Path, Config loading and the source gate (doc 03). (+33 more)

### Community 4 - "jobicy.py"
Cohesion: 0.07
Nodes (34): One unmapped record exactly as the source returned it., RawJob, classify_location(), geo_eligibility(), LocationInfo, Pure normalization helpers for titles, companies and locations (doc 05). No…, Read free-text location. Conservative: unknown stays unknown., Eligibility for sources that only list remote jobs (Jobicy, We Work Remotely).… (+26 more)

### Community 5 - "HttpClient"
Cohesion: 0.08
Nodes (34): RobotFileParser, _board_entries(), GreenhouseAdapter, Greenhouse public job board adapter (one adapter for every company board).…, Return (token, company name) pairs, skipping invalid tokens., BlockedError, FetchError, NotFoundError (+26 more)

### Community 6 - "google_sheets.py"
Cohesion: 0.06
Nodes (49): csv_value(), DashboardTable, Any, datetime, Dashboard tables: tidy, typed copies of the Sheet data for Looker Studio (Data…, Days since 1899-12-30, the day-count Google Sheets uses for dates and times., A cell value for a RAW Sheets write: blanks as "", dates as serials, text made…, A cell value for a CSV export: ISO dates, true/false, formula-safe text. (+41 more)

### Community 7 - "SQLiteStorage"
Cohesion: 0.11
Nodes (24): Job scraper: finds customer-care jobs from permitted sources., Any, Path, Validate table name against the whitelist and return the safe name., Simulate the owner editing a user column in the Sheet., SQLiteStorage, env(), mock_sources() (+16 more)

### Community 8 - "test_health.py"
Cohesion: 0.05
Nodes (80): How a source ended a run (doc 07)., SourceStatus, _older_than(), plan_retention(), datetime, Retention (FR-13, doc 03): remove what has aged out, never touch what the owner…, Plan from the stored tables and, unless dry_run, apply. Raises StorageError on…, Unreadable or empty timestamps are never treated as old, so nothing is deleted… (+72 more)

### Community 9 - "Managed Better Auth: implement login"
Cohesion: 0.08
Nodes (23): Auth emails, Cross-subdomain vs bearer JWT, Data API identity, Environment, Managed Better Auth: implement login, Next.js, Organization invitations, Packages (+15 more)

### Community 10 - "runner.py"
Cohesion: 0.12
Nodes (37): gate_reason(), Return why a source may not run, or None when it passes the gate., default_client_factory(), ClientFactory, datetime, Job, Path, Runner: the only place that wires config, adapters and the HTTP client together. (+29 more)

### Community 11 - "test_security_checklist.py"
Cohesion: 0.13
Nodes (11): LogRecord, Strips query strings, tokens and registered secret values from messages., RedactionFilter, capture_logs(), stop(), Any, mock, Machine-checkable items from the doc 08 pre-deployment checklist. Items that… (+3 more)

### Community 12 - "Lakebase Postgres Branching"
Cohesion: 0.08
Nodes (25): Beta Support Guidance (Mandatory), Branch Type Decision, Branching in CI/CD, CLI usage, Console and API usage, Create a Normal Branch (Preferred for Real-Data Migration Testing), Create a Schema-Only Branch (Beta, Sensitive Data), Example 1: Migration testing with realistic data (+17 more)

### Community 13 - "Part B. Other job boards"
Cohesion: 0.07
Nodes (28): 0. Quick answers, A1. How filtering works, A2. Change filters with config only, A3. Soft preferences (no code), A4. Add a new kind of hard filter (recipe), A5. Other filter ideas, A6. After you change a filter, A7. Searching a different type of job entirely (+20 more)

### Community 14 - "digest.py"
Cohesion: 0.12
Nodes (34): Batch, build_digest(), clean(), DigestConfig, due_follow_ups(), format_follow_ups(), format_job(), has_problems() (+26 more)

### Community 15 - "package.json"
Cohesion: 0.04
Nodes (46): font, metadata, viewport, dependencies, @neondatabase/serverless, next, pg, react (+38 more)

### Community 16 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 17 - "Installation & Setup Guide"
Cohesion: 0.08
Nodes (22): 1. Find your Source IDs, 1. Using a Virtual Environment (Highly Recommended), 2. Installing Dependencies, 2. Run a Single Source, 3. Configuration, 3. How to Verify the Data, 🛠 Detailed Setup Steps, Installation & Setup Guide (+14 more)

### Community 18 - "make_job"
Cohesion: 0.20
Nodes (19): later(), make_job(), Any, datetime, Job, A normalized Job with sensible defaults. Override any field., run(), test_canonical_url_ignores_tracking_fragment_slash_case() (+11 more)

### Community 19 - "servers"
Cohesion: 0.20
Nodes (9): mcp, servers, type, url, $schema, neon, vercel, type (+1 more)

### Community 20 - "test_workflows.py"
Cohesion: 0.14
Nodes (27): load(), Any, parametrize, Path, Static checks that keep the workflows inside the rules in docs 08, 09 and 11.…, _requirement_blocks(), steps(), test_checkout_does_not_persist_credentials() (+19 more)

### Community 21 - "dedupe.py"
Cohesion: 0.12
Nodes (22): _is_location_segment(), normalize_company(), normalize_title(), Lowercase, drop bracketed text, location suffixes, punctuation and level noise., Lowercase, remove punctuation and trailing legal suffixes., fingerprint(), normalize_job(), Job (+14 more)

### Community 22 - "test_verify_vercel_project.py"
Cohesion: 0.13
Nodes (56): list, MakeApp, _EnvHandler, FlatEnvList, make_app(), preview_env_vars(), preview_secrets_env(), project() (+48 more)

### Community 23 - "notify.py"
Cohesion: 0.14
Nodes (14): Notifier, ABC, Notifier interface (D17). A second channel is a new file that implements this., `sent` counts messages delivered in order. Sending stops at the first failure., Deliver plain-text messages in order. Never raises for delivery problems., Deliver one short alert. Returns whether it was delivered., SendResult, Digest (+6 more)

### Community 24 - "Neon"
Cohesion: 0.05
Nodes (36): Auth, 1. Install the Neon CLI, 2. Install the Neon MCP Server, 3. Install Neon Agent Skills, 4. Link Your Project and Get Started, Architecture: How to Use Neon, Backend Primitives, Bootstrap a New Project (+28 more)

### Community 25 - "GoogleSheetsStorage"
Cohesion: 0.13
Nodes (8): col_letter(), GoogleSheetsStorage, Job, Add any missing columns at the end of the header row. Never reorders., One batched request, highest rows first so earlier row numbers stay valid., Rewrite each Dash_* tab completely. Looker Studio reads one worksheet per data…, 1-based column index to A1 letters., test_writing_dashboard_tabs_needs_the_spreadsheet_handle()

### Community 26 - "himalayas.py"
Cohesion: 0.08
Nodes (43): make_job_id(), Stable ID: first 12 hex of sha1(source + source_job_id) (doc 05)., RemoteEligibility, clean_str(), html_to_text(), parse_date(), HTML to plain text, truncation and small value helpers. Pure functions., Strip tags and return plain text. Scraped content is data, never markup. (+35 more)

### Community 27 - "pipeline.py"
Cohesion: 0.09
Nodes (35): Counter, datetime, Exception, Job, Filter, score, store, notify and refresh the dashboard for ONE profile. Returns…, _run_profile(), run_row(), _warn() (+27 more)

### Community 28 - "test_phase3.py"
Cohesion: 0.31
Nodes (8): Acme: Support Agent' -> ('Acme', 'Support Agent'). No colon means no company., split_title(), Any, mock, test_jobicy_fetch_and_map(), test_split_title(), test_three_sources_merge_across_boards_and_second_run_adds_nothing(), test_weworkremotely_fetch_and_map()

### Community 29 - "TelegramNotifier"
Cohesion: 0.14
Nodes (12): Client, _describe(), _Permanent, Exception, Response, Telegram's own error text and retry_after, if the body is the expected JSON., Do not retry: bad token, blocked bot, unknown chat, rejected message., TelegramNotifier (+4 more)

### Community 30 - "Neon Functions"
Cohesion: 0.09
Nodes (22): Application instrumentation, Architecture: Where Functions Fit, Availability, Built-in branch logs, Connecting to Postgres, Develop Locally and Deploy, Environment Variables, Function Triggers (+14 more)

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

### Community 40 - "load_scoring"
Cohesion: 0.27
Nodes (12): _load(), load_profile(), load_scoring(), Any, BaseModel, Path, Path, New tools (26 Oct 2026) must be in BOTH the dictionary and partial_skills. A… (+4 more)

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

### Community 53 - "Deduper"
Cohesion: 0.24
Nodes (10): Deduper, _Entry, format_salary(), Job, Add one candidate. Returns True if it became a new job, False if merged., Merge policy: union URLs, prefer the employer's domain, keep richest values.…, Human-readable salary for the Sheet. Never converts currency (doc 05)., Index of stored jobs plus jobs added during this run. (+2 more)

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

### Community 59 - "Scorer"
Cohesion: 0.24
Nodes (7): Factor, Any, Job, First 'N years' phrase that sits next to the word 'experience'., Scorer, years_asked(), JobSkills

### Community 60 - "8. Running it day to day"
Cohesion: 0.40
Nodes (5): 8. Running it day to day, Common jobs, Daily (about 5 minutes), Weekly (about 15 minutes), What an alert means and what to do

### Community 61 - "source_check.py"
Cohesion: 0.14
Nodes (30): BaseModel, One entry under `sources:` in sources.yaml., SourceConfig, SourcesFile, check_source(), CheckResult, format_check(), Any (+22 more)

### Community 62 - "Storage"
Cohesion: 0.07
Nodes (17): build_from_storage(), Rebuild every Dash_* table from the stored data and write them. Raises…, refresh_dashboard(), ABC, Job, Everything dedupe needs about jobs already stored., Append new rows. Never overwrites existing rows., Update system-owned columns of existing rows. User columns are never written. (+9 more)

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

### Community 71 - "test_dashboard.py"
Cohesion: 0.30
Nodes (20): build(), job_row(), record(), sheets(), tab(), test_a_changed_layout_is_reformatted(), test_a_refresh_replaces_everything_and_does_not_reformat_an_unchanged_layout(), test_blank_values_overwrite_old_values() (+12 more)

### Community 84 - "Neon AI Gateway"
Cohesion: 0.12
Nodes (16): Availability, Build Agents with Mastra (Recommended), Build Agents with the Vercel AI SDK (Recommended), Enabling the gateway: plan and model access, Environment Variables, Further Reading, Generate Embeddings with the AI SDK, List Available Models at Runtime (`/v1/models`) (+8 more)

### Community 87 - "14. Frontend Dashboard"
Cohesion: 0.07
Nodes (26): 14. Frontend Dashboard, Apply button, Data access, Decisions (add to the log in doc 00), Display rules, End-to-end checklist (manual, before deploy), Environment variables, Filters and sorting (+18 more)

### Community 88 - "Lakebase Postgres"
Cohesion: 0.15
Nodes (13): Autoscaling, Branching, Connection Pooling, Gotchas, Instant Restore, IP Allow Lists, Lakebase Postgres, Lakebase Search (+5 more)

### Community 89 - "NeonPublisher"
Cohesion: 0.10
Nodes (28): __getattr__(), Storage backends (doc 04). Backends never score, filter or notify. This package…, Lazily import backends so ``import jobscraper.storage`` stays light., _adapt(), NeonError, NeonPublisher, Any, Connection (+20 more)

### Community 90 - "Semantic Vector Search"
Cohesion: 0.18
Nodes (11): AI SDK (Recommended), Build the Index, Contents, Create the Extension, OpenAI SDK Alternative, Prepare Embeddings, Query, Semantic Vector Search (+3 more)

### Community 91 - "PostgresStorage"
Cohesion: 0.13
Nodes (6): _connect(), PostgresStorage, Any, Connection, Job, Connect to Postgres, creating the configured database on first run.

### Community 92 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 93 - "run_publish"
Cohesion: 0.12
Nodes (27): RowLoader, check_guard(), datetime, `python main.py publish` logic. The CLI/runner is the only place that wires…, Read each profile's Sheet, apply the rules, and refresh that profile's slice of…, run_publish(), GuardError, PublishSettings (+19 more)

### Community 94 - "test_http.py"
Cohesion: 0.19
Nodes (24): URL failed the SSRF rules (doc 08)., UnsafeUrlError, default_resolver(), Resolve a hostname to its IP addresses., Any, mock, parametrize, test_429_not_retried_and_retry_after_capped() (+16 more)

### Community 95 - "build_rows"
Cohesion: 0.21
Nodes (16): _breakdown(), build_rows(), _names(), _or_none(), PublishPlan, Any, datetime, Turn Sheet rows into publishable Neon rows (doc 13). Pure functions, no I/O.… (+8 more)

### Community 96 - "skills.py"
Cohesion: 0.18
Nodes (13): _kind_at(), _markers(), Skills extraction, version 1: a dictionary with synonyms, no machine learning…, (start, end, kind) for each heading that opens a required or preferred section., Section of a mention. No headings, or before the first one, means required., _requirement_lines(), SkillExtractor, found() (+5 more)

### Community 97 - "jobscraper/dashboard.py"
Cohesion: 0.22
Nodes (20): _breakdown(), build_dashboard(), _float(), _int(), _job_row(), _local_date(), _local_dt(), _names() (+12 more)

### Community 98 - "Postgres Egress Optimizer"
Cohesion: 0.12
Nodes (16): Application-side aggregation, Check if pg_stat_statements is available, Diagnostic queries, Further Reading, Handle empty stats, High-frequency queries on static data, Interpret the results, JOIN duplication (+8 more)

### Community 99 - "11. Coding Standards"
Cohesion: 0.18
Nodes (11): 11. Coding Standards, Configuration, Definition of done (per task), Error handling, Git workflow, Language and tooling, Logging, Naming and style (+3 more)

### Community 101 - "Neon publish: wiring it into the repo"
Cohesion: 0.22
Nodes (8): 1. Dependencies and config, 2. CLI glue (adapt names to your `cli.py`), 3. Workflow (`.github/workflows/daily.yml`), 4. Order of work, 5. Doc updates, Behavior notes, Neon publish: wiring it into the repo, What I could not see (please check)

### Community 102 - "Worksheet"
Cohesion: 0.16
Nodes (4): Protocol, Any, The slice of gspread.Worksheet this module uses., Worksheet

### Community 103 - "Neon Object Storage"
Cohesion: 0.12
Nodes (15): Architecture: Where Object Storage Fits, Availability, Built-in Branch Logs, CLI Bucket and Object Commands, Environment Variables, Further Reading, Neon Documentation, Neon Infrastructure as Code (`neon.ts`) (+7 more)

### Community 104 - "15. Multi-profile"
Cohesion: 0.14
Nodes (13): 15. Multi-profile, Dashboard without a login, Database migration, Decisions (add to the log in doc 00), Deferred, Edits to the pages (not seen, so described), Files in this drop, How a run works now (+5 more)

### Community 105 - "Client-side reactivity"
Cohesion: 0.12
Nodes (16): Changing query parameters, Client-side reactivity, Contents, Create the collection, Handling errors, initialData, Manage optimistic state, Other frameworks (+8 more)

### Community 106 - "Job dashboard (frontend)"
Cohesion: 0.33
Nodes (5): Before you trust it (O10), Job dashboard (frontend), Notes and decisions, Run locally (against local PostgreSQL), Structure

### Community 108 - "neon"
Cohesion: 0.22
Nodes (3): neon(), fixture, A fake storage.neon so these tests need neither psycopg nor a database.

### Community 109 - "test_storage.py"
Cohesion: 0.11
Nodes (16): FakeBook, FakeSpreadsheet, FakeWorksheet, Any, fixture, Applies deleteDimension requests in order, like the real batchUpdate., In-memory stand-in for gspread.Worksheet., Stand-in for a gspread Spreadsheet: lists tabs and can add new ones. (+8 more)

### Community 115 - "queries.ts"
Cohesion: 0.17
Nodes (13): ORDER, Filters, PAGE_SIZE, buildListQuery(), JOB_COLUMNS, ListQuery, ORDER_BY, FilterOptions (+5 more)

### Community 117 - "_NeonHandler"
Cohesion: 0.17
Nodes (24): branch(), neon_api(), _NeonHandler, Any, BaseHTTPRequestHandler, CompletedProcess, fixture, parametrize (+16 more)

### Community 118 - "Server-side rendering"
Cohesion: 0.13
Nodes (15): Contents, Create a `DbClient` per router, Define the collection, Examples, Keep row shapes identical, Keep secrets on the server, Open the connection in the browser, Render the initial rows straight away (+7 more)

### Community 119 - "settings.py"
Cohesion: 0.25
Nodes (14): ExperiencePoints, FilterSettings, FreshnessPoints, IndustryPoints, LocationPoints, ProfileTitles, Validated profile and scoring configuration (doc 06, doc 11). Every point value…, SalaryFloor (+6 more)

### Community 120 - "breakdown.ts"
Cohesion: 0.27
Nodes (10): ScoreBar(), Factor, FACTOR_ORDER, factorFrom(), isObj(), LABELS, num(), parseBreakdown() (+2 more)

### Community 122 - "JobFilters"
Cohesion: 0.22
Nodes (10): Pattern, _compile(), Exclusion, JobFilters, _keyword_regex(), Job, Match, Hard filters (doc 06, step 1). A job that fails is excluded, logged and never… (+2 more)

### Community 123 - "app/page.tsx"
Cohesion: 0.24
Nodes (12): dynamic, Home(), ProfileSwitcher(), RawParams, labelMap(), listProfiles, loadProfiles(), ProfileInfo (+4 more)

### Community 124 - "Managing Lakebase Search with Drizzle"
Cohesion: 0.25
Nodes (8): BM25 Index, Config, Extensions, Generate and Store Embeddings, Managing Lakebase Search with Drizzle, Query, Schema, Tune Per Query

### Community 125 - "Claimable Neon"
Cohesion: 0.29
Nodes (6): Claim, Claimable Neon, If neon claim is missing, Path, With REST, With the CLI

### Community 126 - "FilterPanel.tsx"
Cohesion: 0.20
Nodes (6): FilterDisclosure(), Opt, FOUND_OPTIONS, TIERS, WORK_TYPES, react

### Community 127 - "db.ts"
Cohesion: 0.27
Nodes (10): DatabaseConfigurationError, errorProperties(), getDatabaseUrl(), isRetryable(), NeonSql, query(), runQuery(), sleep() (+2 more)

### Community 129 - "test_adapters.py"
Cohesion: 0.34
Nodes (14): HimalayasAdapter, map_all(), Any, mock, test_excerpt_zero_stores_nothing_but_keeps_scoring_text(), test_greenhouse_blocked_stops_source(), test_greenhouse_fetch_and_map(), test_greenhouse_invalid_token_ignored() (+6 more)

### Community 130 - "Full-Text Search with BM25 Ranking"
Cohesion: 0.33
Nodes (6): Full-Text Search with BM25 Ranking, Prepare and Index Text, Query and Interpret Scores, Set Parameters at Build Time or Per Query, Set the Candidate Limit, Use Prefilter Selectively

### Community 131 - "Setup Flow"
Cohesion: 0.33
Nodes (6): 1. Select the organization and project, 2. Get the connection string, 3. Pick the connection method and driver, 4. Set up the schema, Setup Flow, When to use pooled vs direct connections

### Community 132 - "Troubleshooting and Neon-Specific Performance"
Cohesion: 0.33
Nodes (6): Choose CLI or MCP, Inspect Neon Cache Behavior Per Query, Interpret Results Safely, Performance Workflow, Pick the Diagnostic, Troubleshooting and Neon-Specific Performance

### Community 134 - "Function Triggers"
Cohesion: 0.15
Nodes (13): CLI, Delivery payload, Fields, Function Triggers, Inheritance, Local `neon dev`, Logs, MCP backup (+5 more)

### Community 136 - "Optimistic mutations"
Cohesion: 0.15
Nodes (13): Automatic management of optimistic state, Calling the routes from the frontend, Contents, How optimistic mutations work, Optimistic mutations, Render the app, Returning the `txid` from your backend, Running example (+5 more)

### Community 141 - "Subscribing to queries"
Cohesion: 0.15
Nodes (13): Contents, Debug subscriptions, Fetch from a server function, Fetch from an API endpoint, Getting the query to subscribe to, Handle errors, Listen for changes, Log client diagnostics (+5 more)

### Community 142 - "cli.py"
Cohesion: 0.08
Nodes (50): ArgumentParser, CLI entry point: python main.py run --dry-run --no-notify, Namespace, _add_profile_args(), _add_settings_arg(), _add_storage_args(), build_parser(), build_storage() (+42 more)

### Community 143 - "verify_vercel_project.sh"
Cohesion: 0.42
Nodes (8): check_build(), check_link(), check_preview_env(), check_preview_secrets(), check_secrets(), parse_error(), resolve_app_root(), verify_vercel_project.sh script

### Community 144 - "Defining queries"
Cohesion: 0.17
Nodes (12): Authorization, Contents, Defining queries, Exposing an endpoint, Exposing queries, Live authorization, Renewing sealed queries, Sealing authorized queries (+4 more)

### Community 145 - "test_language_filter.py"
Cohesion: 0.24
Nodes (12): community(), job(), Any, fixture, parametrize, Language and region filters for the community profile (added 2026-10-26). The…, test_a_company_headquarters_is_not_a_role_restriction(), test_a_required_other_language_is_excluded() (+4 more)

### Community 146 - "conftest.py"
Cohesion: 0.22
Nodes (9): Random, Resolver, make_client(), factory(), now(), datetime, fixture, Sleeper (+1 more)

### Community 147 - "Sentry (errors, logs, and traces)"
Cohesion: 0.20
Nodes (10): 1. Initialize before anything else, 2. Provide the DSN as a deploy-time secret, 3. Create the request span and catch route errors, 4. Errors are for failures; logs are for the story, 5. Trace the agent itself, Environment variables, Other Node integrations, Sentry error monitoring on Neon Functions (+2 more)

### Community 148 - "Neon Realtime"
Cohesion: 0.20
Nodes (10): Choose the Stack, Core Pattern, Define and Seal Queries, How It Works, More Docs, Neon Realtime, Optimistic Writes, Server-Side Rendering (+2 more)

### Community 149 - "FakeNotifier"
Cohesion: 0.27
Nodes (9): FakeNotifier, run_once(), stored(), test_a_failed_send_is_retried_next_run_without_repeating_the_delivered_part(), test_follow_up_reminders_are_marked_and_not_repeated(), test_marking_failure_is_reported(), update_jobs(), test_nothing_is_ever_sent_twice() (+1 more)

### Community 150 - "logging.py"
Cohesion: 0.40
Nodes (5): JsonFormatter, JSON logging with a redaction filter (doc 07, doc 11)., One JSON object per line. Extra context goes in `ctx`., Configure the root logger once. Logs go to stderr so stdout stays clean., setup_logging()

### Community 151 - "Production hardening for Neon Functions"
Cohesion: 0.22
Nodes (9): Choose the caller shape, Function Triggers only, Limit authenticated application work, Native URL, Preserve existing clients, Production hardening for Neon Functions, Public consumers through a Worker, Reject these (+1 more)

### Community 152 - "Clock"
Cohesion: 0.40
Nodes (3): Clock, fixture, tg()

### Community 153 - "Mastra agents with Mastra Studio observability"
Cohesion: 0.25
Nodes (8): 1. Define the agent against the Neon AI Gateway, 2. Wire observability to Mastra Studio, 3. Structured output through the gateway, 4. Create the Mastra project + token with the CLI, 5. Pass the creds via `neon.ts` (third-party env), 6. Verify, Further reading, Mastra agents with Mastra Studio observability

### Community 154 - "Shipping native binaries with a Function"
Cohesion: 0.25
Nodes (7): `bundler: "none"`: ship a prebuilt directory, Custom `bundler`: return the file map, `externalPackages`: npm packages with a Node addon, Shipping native binaries with a Function, Size limits, Standalone executables, The runtime a binary lands on

### Community 155 - "Server-sent events (SSE) on Neon Functions"
Cohesion: 0.25
Nodes (7): Caveats, Client, Minimal SSE endpoint (no framework), Push to every client, across isolates, Server-sent events (SSE) on Neon Functions, Wire format (just text), With Hono

### Community 157 - "AI SDK agents on Neon Functions"
Cohesion: 0.29
Nodes (7): 1. Declare the gateway and the function, 2. The handler: stream a tool-calling agent, 3. Generate images and persist them, 4. Call it directly from the client (don't proxy the stream), 5. Run and deploy, AI SDK agents on Neon Functions, Further reading

### Community 158 - "test_normalize_company"
Cohesion: 0.67
Nodes (4): Any, parametrize, test_normalize_company(), test_normalize_title()

### Community 159 - "MCP servers on Neon Functions"
Cohesion: 0.33
Nodes (6): Authenticating the server, MCP servers on Neon Functions, Option 1 — OAuth via the Better Auth MCP plugin (best for third-party clients), Option 2 — API key or session JWT via self-hosted Better Auth (simplest), Testing, The server

### Community 161 - "Defining live queries"
Cohesion: 0.33
Nodes (6): Defining live queries, Parameter types, Query parameters, Table requirements, Using a query builder or ORM, Using raw SQL

### Community 162 - "WebSocket Servers"
Cohesion: 0.50
Nodes (4): Client must reconnect, Fan-out across isolates (do not skip this), Heartbeat (keep the socket alive), WebSocket Servers

### Community 163 - "neon_preview_branch.sh"
Cohesion: 0.60
Nodes (4): delete(), find_branch(), neon_preview_branch.sh script, verify()

### Community 164 - "Hybrid Search"
Cohesion: 0.50
Nodes (4): Adapt the Hybrid Search, Hybrid Search, Rerank with Jev, RRF Example

### Community 165 - "test_refresh_dashboard_from_a_real_store"
Cohesion: 0.67
Nodes (3): Any, test_dashboard_command_exports_csv_and_refreshes(), test_refresh_dashboard_from_a_real_store()

## Knowledge Gaps
- **693 isolated node(s):** `extends`, `next/core-web-vitals`, `dynamic`, `font`, `metadata` (+688 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1138 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_publish()` connect `run_publish` to `NeonPublisher`, `test_publish.py`, `cli.py`, `build_rows`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `SQLiteStorage` connect `SQLiteStorage` to `test_matching.py`, `test_refresh_dashboard_from_a_real_store`, `google_sheets.py`, `test_health.py`, `runner.py`, `test_storage.py`, `cli.py`, `FakeNotifier`, `NeonPublisher`, `test_phase3.py`, `Storage`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `Storage` connect `Storage` to `jobscraper/dashboard.py`, `ConfigError`, `google_sheets.py`, `SQLiteStorage`, `test_health.py`, `PostgresStorage`, `cli.py`, `notify.py`, `GoogleSheetsStorage`, `pipeline.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SQLiteStorage` (e.g. with `DashboardTable` and `StorageError`) actually correct?**
  _`SQLiteStorage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `HttpClient` (e.g. with `Adapter` and `GreenhouseAdapter`) actually correct?**
  _`HttpClient` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `StorageError` (e.g. with `cmd_brief()` and `cmd_calibrate()`) actually correct?**
  _`StorageError` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Storage` (e.g. with `build_storage()` and `cmd_run()`) actually correct?**
  _`Storage` has 13 INFERRED edges - model-reasoned connections that need verification._