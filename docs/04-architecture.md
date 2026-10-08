# 04. Architecture

## Overview
A small batch pipeline. Each run pulls from every enabled source, normalizes, deduplicates, filters, scores, saves and notifies. Nothing runs between runs.

```mermaid
flowchart LR
  CFG[config: sources, profile, scoring] --> RUN[Runner]
  RUN --> A1[Adapter: Himalayas]
  RUN --> A2[Adapter: Greenhouse boards]
  RUN --> A3[Adapter: Kenyan board (if verified)]
  RUN --> A4[Adapter: Inbox tab (email alerts)]
  A1 & A2 & A3 & A4 --> N[Normalizer + PII scrubber]
  N --> D[Deduplicator]
  D --> F[Hard filters]
  F --> S[Scorer]
  S --> ST[(Storage: Google Sheet)]
  ST --> NT[Telegram digest]
  RUN --> RP[Run report + logs]
```

## Technology choices
| Choice | Why | Rejected |
|---|---|---|
| Python 3.12 | Owner is comfortable, best ecosystem for this | Node (no advantage here) |
| httpx | Timeouts, retries via tenacity, easy mocking with respx | requests (no async or fine timeouts) |
| feedparser | Robust RSS/Atom parsing | Hand-rolled XML |
| BeautifulSoup or selectolax | HTML only where permitted | Scrapy for v1 (too heavy for a few sources) |
| Scrapling (optional) | Adaptive selectors help when layouts change. Parser only, evaluated in Phase 2 | Its stealth fetchers and Camoufox (bypass tooling, out of scope) |
| Playwright (standard mode) | Only if a permitted site needs JS rendering | Selenium, stealth browsers |
| pydantic | Validates every job object | Plain dicts |
| rapidfuzz | Fuzzy title and description matching | Custom string distance |
| gspread + google-auth | Sheets access with a service account | Full Google API client (heavier) |
| Telegram Bot API over httpx | One POST call, no extra dependency | python-telegram-bot |
| GitHub Actions | Free, secrets, logs | VPS (cost, upkeep), Docker (not needed at first) |
| pytest, respx, ruff, mypy, pip-audit | Tests, mocking, style, types, dependency audit | none |

Not used: Redis, PostgreSQL, Supabase, Docker, Selenium. Add later only if a real need appears.

## Repo layout
```text
job-scraper/
├── src/jobscraper/
│   ├── scrapers/        # one adapter per source (one per ATS platform), base.py, registry.py, inbox.py
│   ├── parsers/         # feed/JSON/HTML helpers, PII scrubber
│   ├── models/          # pydantic Job, RawJob, SourceResult
│   ├── matching/        # filters, skills extraction, scorer, explainer
│   ├── notifications/   # base.py (interface), telegram digest
│   ├── storage/         # base interface, google_sheets, sqlite (tests)
│   └── utils/           # http client, robots, rate limiter, logging, dedupe
├── tests/               # unit tests + fixtures/
├── config/              # sources.yaml, profile.yaml, scoring.yaml
├── docs/
├── .github/workflows/daily.yml
├── .env.example
├── requirements.txt
├── README.md
└── main.py              # CLI entry
```

## Adapter contract
Each adapter exposes:
- `id`, `display_name`, `requires_key` (env var name or none)
- `fetch(context) -> list[RawJob]`, which uses the shared HTTP client (robots check, rate limiter, retries) and returns raw records
- `to_job(raw) -> Job | None`, which maps to the common schema, returning `None` for unusable records

**Registry.** Adapters register under their `id` in `scrapers/registry.py`, and the `id` matches the key in `sources.yaml`. The runner builds its source list from config and looks each one up in the registry. Adding a source means a new adapter file and a config entry, with no edit to the runner.

**ATS platforms.** Greenhouse, Lever, Ashby and similar each get one adapter. Companies are board tokens listed under that platform in `sources.yaml`, so 30 companies do not mean 30 files.

**Inbox adapter.** Email-alert jobs (LinkedIn, Indeed, Glassdoor, any board that fails the source gate) reach the pipeline through the `Inbox` tab (doc 05). A Google Apps Script in the owner's own account writes only to that tab. The Inbox adapter reads unprocessed rows and returns them as `RawJob`s, so they go through the same normalization, dedupe, filters and scoring. After a successful run the runner marks those rows processed through the storage interface.

**Notifier interface.** `notifications/base.py` defines `send(messages)` and `send_alert(text)`. Telegram implements it, and a future channel is a new file.

Adapters never write to storage, never send notifications and never raise past their own boundary. The runner wraps each one and records a `SourceResult` (status, counts, error, duration).

## Run flow
1. Load config, validate, read secrets from environment.
2. Storage: read existing job IDs, fingerprints and user-owned columns.
3. For each enabled and verified source: fetch, map, scrub personal data, validate.
4. Deduplicate against this run and against stored jobs.
5. Apply hard filters. Excluded jobs go to the audit log with a reason.
6. Score and build explanations.
7. Append new jobs, update `last_seen` on known ones (user columns untouched).
8. Send digest for jobs with `notified_at` empty and tier Strong or Potential. Set `notified_at`.
9. Send run report. Run cleanup if due.

**Idempotent:** running twice in a row adds no duplicates and sends no repeat digest.

## Digest format
```text
NEW CUSTOMER SUPPORT JOBS (2026-10-01, EAT)

1. Customer Support Specialist  [Top match 86]
   Company: XYZ | Remote: open to Africa | Posted: 2 days ago
   You have: Zendesk, ticketing, CRM | Missing: Freshdesk, live chat
   Salary: $800-1,200 | Source: Himalayas
   Apply: <url>

FOLLOW-UPS DUE TODAY
- ABC Bank, Customer Care Rep (applied 7 days ago)

RUN: 4 sources ok, 1 degraded (Jobicy: 0 results), 23 found, 9 new
```
Plain text with escaped content, split into messages under 4096 characters, top 10 per message.

## CLI
| Command | Purpose |
|---|---|
| `python main.py run` | Full run |
| `python main.py run --dry-run --no-notify` | Fetch, score, print. No writes, no messages |
| `python main.py run --sources himalayas,greenhouse` | Subset |
| `python main.py sources check` | Health, robots and parse check per source |
| `python main.py brief <job_id>` | Markdown brief for CV or cover-letter help |
| `python main.py cleanup` | Apply retention |

## Configuration precedence
Defaults in code, then YAML in `config/`, then environment variables for secrets and overrides. Secrets are never in YAML.

## Time handling
Store UTC ISO-8601. Display Africa/Nairobi (EAT, UTC+3). GitHub cron uses UTC. Runs are at 03:00 and 13:00 UTC (06:00 and 16:00 EAT). The second run only digests jobs with `notified_at` empty, so nothing repeats.
