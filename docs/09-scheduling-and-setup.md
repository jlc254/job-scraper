# 09. Scheduling and Setup

## Options compared
| Option | Cost | Pros | Cons | Verdict |
|---|---|---|---|---|
| GitHub Actions (private repo) | Free tier (verify current minutes) | No server, secrets built in, logs, failure alerts | Cron can be delayed by minutes. Stateless, so state lives in the Sheet | **Recommended** |
| Laptop (cron or Task Scheduler) | Free | Simple, easy debugging | Misses runs when off | Manual runs and testing |
| Docker | Free | Reproducible | Not needed at this scale | Skip for now |
| Small VPS | Paid | Always on, persistent | Maintenance, security upkeep | Only if free options fail |
| Cloud functions | Free tier | Serverless | More setup, more moving parts | Skip |

Public repositories can have scheduled workflows disabled after a long period without activity (verify), one more reason to keep the repo private.

## Schedule
- **Daily run:** 03:00 UTC = 06:00 EAT, so the digest is ready before the working day.
- **Second run (confirmed):** 13:00 UTC = 16:00 EAT, for boards that post during the day.
- GitHub cron is UTC only. A typical run uses a few minutes, well inside free limits.

## Workflow specification (`.github/workflows/daily.yml`)
- Trigger: `schedule` (crons `0 3 * * *` and `0 13 * * *`) and `workflow_dispatch` for manual runs.
- `permissions: contents: read`.
- `concurrency` group so two runs never overlap.
- `timeout-minutes: 15`.
- Steps: checkout (pinned SHA), setup Python 3.12 with pip cache, install from hashed requirements, run `python main.py run`.
- Secrets passed as environment variables only to the run step.
- On failure: a step that sends a Telegram alert and, if configured, pings the dead-man's-switch URL on success.

## Secrets
| Name | Purpose |
|---|---|
| TELEGRAM_BOT_TOKEN | Bot API |
| TELEGRAM_CHAT_ID | Destination chat |
| GOOGLE_SERVICE_ACCOUNT_JSON_B64 | Service account key, base64-encoded |
| GOOGLE_SHEET_ID | Target spreadsheet |
| ADZUNA_APP_ID, ADZUNA_APP_KEY | Only if Adzuna is enabled |
| JOOBLE_API_KEY | Only if Jooble is enabled (name proposed) |
| CAREERJET_AFFID | Only if Careerjet is enabled (name proposed) |
| RELIEFWEB_APPNAME | Only if ReliefWeb is enabled (name proposed) |
| HEALTHCHECK_URL | Optional dead-man's switch |

## Deploy secrets (Vercel and Neon)
| Name | Kind | Purpose |
|---|---|---|
| VERCEL_TOKEN | Secret | Authenticates the Vercel CLI in `preview.yml` and `deploy.yml` |
| VERCEL_ORG_ID | Secret | Team that owns the Vercel project |
| VERCEL_PROJECT_ID | Secret | The `job-scraper` Vercel project |
| DATABASE_URL | Secret | Production pooled reader URL. Used by `deploy.yml` only |
| NEON_API_KEY | Secret | Lets CI verify and delete preview branches |
| NEON_PROJECT_ID | Secret | Neon project that the Vercel integration branches |

Previews do not take a static database URL. Vercel's Neon integration creates a branch named `preview/<git-branch>` for each preview deployment and injects that branch's connection string, and `cleanup-neon-preview.yml` deletes it when the PR closes. `NEON_API_KEY` and `NEON_PROJECT_ID` must belong to the Vercel-managed Neon organization (`Vercel: <team>`); otherwise the branch check and cleanup fail with 401/404. Preview Branching must be enabled under Vercel > Project > Settings > Integrations > Neon.

## Setup guide

**1. Telegram bot**
1. In Telegram, open @BotFather, send `/newbot`, and follow the prompts. Copy the token.
2. Send any message to your new bot.
3. Get your chat ID from the bot's `getUpdates` result (do this privately, because the URL contains your token).
4. Store both as secrets.

**2. Google Sheet and service account**
1. Create a Google Cloud project and enable the Google Sheets API.
2. Create a service account (no roles) and download a JSON key.
3. Create the Sheet with tabs Jobs, Excluded and Runs. Copy the Sheet ID from its URL.
4. Share the Sheet with the service account's email as Editor.
5. Base64-encode the JSON key and store it as `GOOGLE_SERVICE_ACCOUNT_JSON_B64`. Delete the local key file.
6. If your account blocks service-account keys, tell me and we will use another route.

**3. Adzuna (optional, free)**
Register at developer.adzuna.com, create an application, and copy the App ID and App Key. Kenya coverage is unconfirmed (O2), so check the country list first.

**4. Local run**
Copy `.env.example` to `.env`, fill in values, create a virtual environment, install requirements, then run `python main.py run --dry-run --no-notify`.

## Account status (1 Oct 2026)
| Item | Status |
|---|---|
| Telegram bot | Created. Token and chat ID go into secrets |
| Google service account | Created. Key must be base64-encoded and the local file deleted |
| Google Sheet | To create: tabs Jobs, Excluded, Runs, Inbox. Share with the service account as Editor |
| GitHub private repo and secrets | To do in Phase 2 and 6 |
| Adzuna keys | Only after O2 confirms Kenya coverage |

Checks and local runs use a Linux shell, so use `curl` and `base64 -w0 key.json`.

## Cost
Target 0 USD: GitHub free tier, Google Sheets, Telegram, free APIs. The only possible cost is a paid API tier, which we will not use without your approval.
