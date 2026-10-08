# Job Scraper: Development Documents

Personal tool that finds recent customer-care and related jobs from permitted sources, scores them against one candidate profile, stores them in a Google Sheet and sends a daily Telegram digest.

**Status:** Phase 1 documents updated 1 Oct 2026 with the settled design decisions. Source verification is in progress, and Phase 1 closes when the exit criteria in doc 10 are met. No application code has been written.

| # | Document | Purpose |
|---|---|---|
| 00 | [PRD](00-prd.md) | Purpose, goals, non-goals, success criteria, decisions log, open items |
| 01 | [Requirements](01-requirements.md) | Functional and non-functional requirements, acceptance criteria |
| 02 | [Source catalog](02-source-catalog.md) | Every source, access method, key needs, verification status |
| 03 | [Legal and responsible use](03-legal-and-responsible-use.md) | Source gate, robots/ToS policy, privacy, retention |
| 04 | [Architecture](04-architecture.md) | Components, data flow, technology choices, repo layout, CLI |
| 05 | [Data model](05-data-model.md) | Job schema, Google Sheet layout, deduplication |
| 06 | [Matching and scoring](06-matching-and-scoring.md) | 100-point methodology, hard filters, worked examples |
| 07 | [Reliability and monitoring](07-reliability-and-monitoring.md) | Failure handling, retries, logging, tests |
| 08 | [Security](08-security.md) | Threat model and controls |
| 09 | [Scheduling and setup](09-scheduling-and-setup.md) | GitHub Actions, secrets, Telegram/Sheets/Adzuna setup |
| 10 | [Development plan](10-development-plan.md) | Phases 1 to 8 with tests and exit criteria |
| 11 | [Coding standards](11-coding-standards.md) | Style, typing, testing, git and review rules |
| 12 | [Runbook](12-runbook.md) | Day-to-day operation, alerts, troubleshooting, adding or disabling sources |

Config templates are in `../config/` (`profile.yaml`, `scoring.yaml`, `sources.yaml`). Environment variables are listed in `../.env.example`.

**Conventions**
- **(verify)** marks a fact taken from memory or a third-party page that must be confirmed against the official source before code depends on it.
- Dates are recorded when a source is verified, because terms and endpoints change.
- Not legal advice. Re-check terms before relying on any source.
