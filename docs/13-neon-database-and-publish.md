# 13. Neon Database, Migration and Publish Command
 
Specification for the read-only Neon copy that feeds the dashboard (doc 14). Written before any code, to be reviewed and signed off first. Status: **design, nothing built**.
 
## Purpose
The Google Sheet stays the working store and the tracker. Neon holds a disposable, read-only copy of only what the dashboard shows, filters or sorts on. A new `publish` command rebuilds that copy from the Sheet. The dashboard never writes to Neon and never touches the Sheet.
 
## Decisions (add to the log in doc 00)
| ID | Decision | Reason |
|---|---|---|
| D19 | Sheet remains the source of truth. Neon is a one-way, rebuildable copy | No two-way sync, no conflicting edits. Losing Neon loses nothing |
| D20 | Only dashboard columns are pushed. Notes, fingerprint, URLs list, Telegram bookkeeping and personal dates never leave the Sheet | Keeps the promise in `dashboard.py`: private notes never leave the Jobs tab |
| D21 | Sync is a full refresh inside one transaction, with a row-count guard | Safe to rerun. A bad Sheet read cannot wipe the database |
| D22 | Retention is applied at publish time. Neon keeps jobs from the last 30 days that are still open | Free tier stays small. The Sheet keeps the full history |
| D23 | Two Postgres roles: a publisher (writes) and a reader (dashboard, `SELECT` only) | A dashboard bug or leaked read URL cannot modify data |
| D26 | `publish` is a separate workflow step after `run` and after the dead-man's-switch ping | A publish failure turns the workflow red and alerts you, but never hides a successful fetch |
 
## What is verified from the real data
Checked on 10 Oct 2026 against the uploaded `Job-scraping.xlsx` (32 jobs: 31 We Work Remotely, 1 Himalayas) and `dashboard.py`.
 
| Topic | Finding |
|---|---|
| Skill lists | `skills_matched` and `skills_missing` are **semicolon-separated** (`excel; english`). Same rule as `_names()` in `dashboard.py` |
| `match_breakdown` | Valid JSON. Keys: `version`, `total`, `tier`, `factors` (each with `points`, `max`, `reason`), `flags`, `skills` (`required`, `preferred`, `matched`, `partial`, `missing`), `requirements` |
| Booleans | Strings `TRUE` / `FALSE` |
| Blank cells | Empty strings, never null |
| Numbers | Stored as text (`'68.0'`). Parse to numeric |
| Dates | `date_posted`, `application_deadline`: `YYYY-MM-DD`. `first_seen`, `last_seen`, `notified_at`: ISO UTC with `+00:00` |
| Text sizes | Excerpt up to about 1,001 characters with newlines and a trailing ellipsis. Titles up to 62 characters in this sample |
| Tiers present | 1 top, 20 potential, 11 weak. **Weak jobs are stored in the Sheet**, so `publish` must decide whether to send them |
| Mostly unknown fields | `employment_type` is `unknown` for 31 of 32. `salary` is blank for 31 of 32 |
| No experience column | The Jobs tab has **no `experience_level` column**. Experience appears only as points and a reason inside `match_breakdown`. It is therefore not a dashboard filter |
| Other tabs | `Excluded`, `Runs`, `Health`, six `Dash_*` tabs, and an unrelated `Sheet2` content planner. `publish` ignores all of them |
 
Existing helpers to reuse from `dashboard.py` (not modified in v1): `_breakdown`, `_names`, `_tier`, `_status`, `_float`, and from `jobscraper.utils.dates`: `EAT`, `parse_timestamp`, `parse_user_date`. A later, separate commit may promote these to a shared module. `dashboard.py` is covered by its own tests, so that refactor is safe, but it is not part of this work.
 
## Column mapping (34 Sheet columns)
 
### Pushed to Neon (22 Sheet columns plus 3 derived or added)
| Sheet column | Neon column | Type | Conversion |
|---|---|---|---|
| job_id | job_id | text, primary key | as is |
| title | title | text | strip a leading `'` (formula-injection escape) |
| company | company | text | strip leading `'` |
| location | location | text | blank to NULL |
| work_type | work_type | text | blank to `unknown` |
| employment_type | employment_type | text | blank to `unknown` |
| remote_eligibility | remote_eligibility | text | blank to `unclear` |
| salary | salary | text | blank to NULL |
| skills_matched | skills_matched | text[] | split on `;`, trim, drop empties |
| skills_missing | skills_missing | text[] | same |
| match_score | match_score | numeric(4,1) | parse float, invalid to NULL |
| match_tier | match_tier | text | lowercase, blank to `unscored` |
| match_breakdown | match_breakdown | jsonb | `json.loads`, invalid to NULL |
| recommended_action | recommended_action | text | blank to NULL |
| source | source | text | as is |
| job_url | job_url | text | must start with `http://` or `https://`, else the row is dropped and counted |
| date_posted | date_posted | date | `parse_user_date`, blank to NULL |
| application_deadline | application_deadline | date | same |
| first_seen | first_seen | timestamptz | `parse_timestamp`, stored in UTC |
| last_seen | last_seen | timestamptz | same |
| is_active | is_active | boolean | `FALSE` means false, anything else true (same rule as `dashboard.py`) |
| is_repost | is_repost | boolean | `TRUE` means true |
| description_excerpt | description_excerpt | text | as is, blank to empty string |
| checklist | checklist | text | blank to NULL |
| application_status | application_status | text | trim, blank to `New` |
| (from match_breakdown) | scoring_version | integer | `breakdown.version`, else NULL |
| (added by publish) | published_at | timestamptz | run start time, used by the refresh and delete |
| (generated by Postgres) | search | tsvector | title, company and excerpt |
 
### Not pushed (10 Sheet columns)
| Column | Reason |
|---|---|
| fingerprint, source_job_id | Python-side dedupe only |
| all_urls | The Apply button uses `job_url`, already the preferred link |
| notified_at, follow_up_reminded_on | Telegram bookkeeping |
| notes | Private free text. Never leaves the Sheet |
| applied_on, follow_up_date, priority | Optional. Left out to keep personal data in one place. Revisit if a "follow-ups due" panel is wanted |
 
## Schema
 
### `migrations/001_init.sql`
```sql
CREATE TABLE IF NOT EXISTS jobs (
  job_id               text PRIMARY KEY,
  title                text NOT NULL,
  company              text NOT NULL,
  location             text,
  work_type            text NOT NULL DEFAULT 'unknown',
  employment_type      text NOT NULL DEFAULT 'unknown',
  remote_eligibility   text NOT NULL DEFAULT 'unclear',
  salary               text,
  skills_matched       text[] NOT NULL DEFAULT '{}',
  skills_missing       text[] NOT NULL DEFAULT '{}',
  match_score          numeric(4,1),
  match_tier           text NOT NULL DEFAULT 'unscored'
                         CHECK (match_tier IN ('top','strong','potential','weak','unscored')),
  scoring_version      integer,
  match_breakdown      jsonb,
  recommended_action   text,
  source               text NOT NULL,
  job_url              text NOT NULL CHECK (job_url ~* '^https?://'),
  date_posted          date,
  application_deadline date,
  first_seen           timestamptz NOT NULL,
  last_seen            timestamptz NOT NULL,
  is_active            boolean NOT NULL DEFAULT true,
  is_repost            boolean NOT NULL DEFAULT false,
  description_excerpt  text NOT NULL DEFAULT '',
  checklist            text,
  application_status   text NOT NULL DEFAULT 'New',
  published_at         timestamptz NOT NULL,
  search tsvector GENERATED ALWAYS AS (
    to_tsvector('english', title || ' ' || company || ' ' || description_excerpt)
  ) STORED
);
 
CREATE INDEX IF NOT EXISTS jobs_score_idx      ON jobs (match_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS jobs_tier_score_idx ON jobs (match_tier, match_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS jobs_first_seen_idx ON jobs (first_seen DESC);
CREATE INDEX IF NOT EXISTS jobs_deadline_idx   ON jobs (application_deadline);
CREATE INDEX IF NOT EXISTS jobs_source_idx     ON jobs (source);
CREATE INDEX IF NOT EXISTS jobs_search_idx     ON jobs USING gin (search);
CREATE INDEX IF NOT EXISTS jobs_skills_idx     ON jobs USING gin (skills_matched);
 
-- One row, so the dashboard can show "data as of ..." and publish can run its guard.
CREATE TABLE IF NOT EXISTS publish_meta (
  id            integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  published_at  timestamptz NOT NULL,
  job_count     integer NOT NULL,
  sheet_rows    integer NOT NULL
);
 
CREATE TABLE IF NOT EXISTS schema_migrations (
  version     text PRIMARY KEY,
  applied_at  timestamptz NOT NULL DEFAULT now()
);
INSERT INTO schema_migrations (version) VALUES ('001_init') ON CONFLICT DO NOTHING;
```
Notes:
- The generated column contains only immutable expressions, so Postgres accepts it. Skills are deliberately excluded from it, because `array_to_string` is not immutable. Skill filters use `skills_matched && ARRAY[...]` against the GIN index.
- `application_status` has no CHECK constraint, because the Sheet dropdown can be bypassed. Unknown values are shown as written.
- There is no foreign key and no tracking table. Neon holds nothing the user edits.
### `migrations/002_roles.sql`
Create the two roles in the Neon console or CLI first (Neon issues their passwords), then run:
```sql
-- publisher: used only by the GitHub Actions publish step
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs, publish_meta TO jobs_publisher;
 
-- reader: used only by the dashboard on Vercel
GRANT SELECT ON jobs, publish_meta TO jobs_reader;
 
INSERT INTO schema_migrations (version) VALUES ('002_roles') ON CONFLICT DO NOTHING;
```
Neither role can create or drop tables. Migrations are run by you, as the project owner role, from your own shell.
 
### Migration procedure
1. Run each file in order against the **dev** branch first, then production, with `psql "$DATABASE_URL_OWNER" -f migrations/00N_name.sql` using the direct (non-pooled) connection string.
2. Files are idempotent (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`), so a rerun is harmless.
3. Never edit an applied migration. Add a new numbered file.
4. Rollback for a copy-only database is simple: drop the tables and rerun publish. No data is lost because the Sheet is the source.
## The `publish` command
 
### Where the code goes
| File | Role |
|---|---|
| `src/jobscraper/publish.py` | Pure functions: Sheet rows to publishable rows, retention rules, guard check. Same style as `dashboard.py` |
| `src/jobscraper/storage/neon.py` | `NeonPublisher`: connects, writes the refresh in one transaction. Write-only copy. It does **not** implement the full `Storage` interface |
| `main.py` / `cli.py` | New `publish` subcommand |
 
Dependency direction follows doc 11: `publish.py` depends on models and utils, `storage/neon.py` depends on models and utils, and only the runner or CLI wires them together. Reading the Sheet reuses the existing `storage.load_table("jobs")`.
 
### CLI
| Command | Behavior |
|---|---|
| `python main.py publish --dry-run` | Reads the Sheet, applies rules, prints counts and a few sample rows. Connects to nothing, writes nothing |
| `python main.py publish` | Full refresh into Neon |
| `python main.py publish --force` | Skips the row-count guard (used after a deliberate big clean-up) |
 
Exit codes: `0` ok, `2` configuration problem (including a missing secret), `3` could not read the Sheet, `6` Neon write failed.
 
### Secret
`NEON_DATABASE_URL_PUBLISHER` (the **direct** string, `sslmode=require`, publisher role). GitHub secret only. Added to doc 09's table and to `.env.example` as an empty line. Added to the log-redaction list, because the URL contains a password.
 
### Rules for what gets published (in order)
A Sheet row is published only if all hold. Thresholds live in `config/settings.yaml` under a new `publish:` block, never in code.
 
| Rule | Default |
|---|---|
| Has a `job_id`, a title, a company and a valid `http(s)` `job_url` | required. Others are dropped and counted |
| `is_active` is not `FALSE` | required |
| `application_deadline` is empty or today or later (today in Africa/Nairobi) | required |
| Status is not one of `Ignored`, `Rejected` | `hide_statuses: [Ignored, Rejected]` |
| `first_seen` within the last N days, **or** status in `keep_statuses` | `max_age_days: 30`, `keep_statuses: [Applied, Interview, Offer]` |
| Weak tier | **Published**, so the dashboard can show it on request. The dashboard hides weak by default (doc 14) |
 
Dropped rows are counted by reason and printed, for example `Published 21, dropped 11 (8 too old, 2 expired, 1 no url)`.
 
### Refresh transaction
```sql
-- all inside one transaction (psycopg 3 `with conn.transaction():`)
INSERT INTO jobs (job_id, title, ..., published_at)
VALUES (...)
ON CONFLICT (job_id) DO UPDATE SET
  title = EXCLUDED.title, company = EXCLUDED.company, location = EXCLUDED.location,
  work_type = EXCLUDED.work_type, employment_type = EXCLUDED.employment_type,
  remote_eligibility = EXCLUDED.remote_eligibility, salary = EXCLUDED.salary,
  skills_matched = EXCLUDED.skills_matched, skills_missing = EXCLUDED.skills_missing,
  match_score = EXCLUDED.match_score, match_tier = EXCLUDED.match_tier,
  scoring_version = EXCLUDED.scoring_version, match_breakdown = EXCLUDED.match_breakdown,
  recommended_action = EXCLUDED.recommended_action, source = EXCLUDED.source,
  job_url = EXCLUDED.job_url, date_posted = EXCLUDED.date_posted,
  application_deadline = EXCLUDED.application_deadline,
  first_seen = EXCLUDED.first_seen, last_seen = EXCLUDED.last_seen,
  is_active = EXCLUDED.is_active, is_repost = EXCLUDED.is_repost,
  description_excerpt = EXCLUDED.description_excerpt, checklist = EXCLUDED.checklist,
  application_status = EXCLUDED.application_status, published_at = EXCLUDED.published_at;
 
DELETE FROM jobs WHERE published_at < :run_start;
 
INSERT INTO publish_meta (id, published_at, job_count, sheet_rows)
VALUES (1, :run_start, :published, :sheet_rows)
ON CONFLICT (id) DO UPDATE SET published_at = EXCLUDED.published_at,
  job_count = EXCLUDED.job_count, sheet_rows = EXCLUDED.sheet_rows;
```
- Parameters are always bound, never formatted into the SQL string.
- Rows are sent in batches inside the same transaction. If anything fails, the transaction rolls back and the dashboard keeps showing the previous data.
- `ON CONFLICT` refreshes every pushed column, because the Sheet is authoritative (a status change in the Sheet must reach Neon). This is safe because Neon holds no user-owned data.
- Rerunning with unchanged Sheet data leaves the same rows (only `published_at` moves), so it is idempotent.
### Guards
1. Zero publishable rows while Neon currently holds 10 or more: abort, exit `6`, change nothing.
2. Publishable rows below 50% of the current Neon count (when Neon holds 10 or more): abort unless `--force`.
3. A Sheet read error (exit `3`) happens before any connection to Neon is opened.
4. First connect retries once with a short backoff, because compute may be waking from scale-to-zero. The connection string is never logged, and errors never include it.
### Workflow changes (`.github/workflows/daily.yml`)
- New step `python main.py publish` **after** the `run` step and after the dead-man's-switch ping.
- `NEON_DATABASE_URL_PUBLISHER` is exposed to that step only. The Phase 6 security tests that restrict which steps see secrets must be updated deliberately to allow exactly this one.
- A new manual mode `publish` for `workflow_dispatch`, which runs only that step.
- If publish fails, the workflow goes red and the existing failure alert fires. The Sheet already holds the new jobs, so nothing is lost.
- Dependency: `psycopg[binary]` is added to `requirements.in`, then `scripts/lock.sh` regenerates the hashed lock files.
## Free-tier assessment (verified 10 Oct 2026)
Source: [neon.com/pricing](https://neon.com/pricing).
 
| Item | Neon Free | This design |
|---|---|---|
| Storage | 1 GB per project | A few MB. Roughly 2 KB per job plus indexes, capped by 30-day retention |
| Compute | 100 CU-hours per project, scale-to-zero after 5 minutes | Two short publishes a day plus dashboard reads. Far below the cap |
| Egress | 5 GB per project | Small pages, paginated, well below |
| Restore window | 6 hours | Irrelevant: the Sheet is the backup, and publish rebuilds Neon |
| Branches | 10 per project | `main` plus `dev` |
 
What happens at the limits (per Neon): out of CU-hours or egress suspends compute until the next period. Over 1 GB blocks writes. Data is not deleted. Neon plans and terms can change, so recheck before relying on them.
 
## Testing
 
### Unit tests (pytest, no network)
Build fixtures from the real sheet shape (a handful of rows, excerpts shortened, no personal data):
| Case | Expectation |
|---|---|
| `'68.0'` and `'43.3'` | numeric 68.0 and 43.3 |
| `excel; english` and empty string | `['excel','english']` and `[]` |
| Valid breakdown JSON | parsed, `scoring_version` read from `version` |
| Invalid or empty breakdown | NULL, row still published |
| `TRUE` and `FALSE` strings | correct booleans, blank `is_active` treated as true |
| Title starting with `'=` | leading apostrophe stripped |
| Blank `application_status` | `New` |
| `job_url` without scheme or relative | row dropped and counted |
| Deadline yesterday, today, tomorrow (in EAT) | dropped, kept, kept |
| 29-day, 31-day and 31-day-Applied rows | kept, dropped, kept |
| `Ignored` and `Rejected` | dropped |
| Guard cases | zero rows and a collapse abort. `--force` bypasses the collapse guard |
 
### Integration tests
Run against a throwaway Neon branch (or a local Postgres in CI, which is the cleaner option since CI must not use live services):
- Publish twice: row count unchanged, second run reports no change in content.
- Remove a row from the input: it is deleted on the next publish.
- Inject a failure halfway through the batch: the transaction rolls back and the previous rows remain.
- The reader role can `SELECT` but an `INSERT`, `UPDATE`, `DELETE` and `DROP` all fail.
- The publisher role cannot create or drop tables.
### Manual verification
1. `python main.py publish --dry-run`: counts match a manual count in the Sheet.
2. `python main.py publish` against dev, then compare 3 jobs row by row with the Sheet.
3. Search `select count(*) from jobs where search @@ plainto_tsquery('english','customer')`: plausible result.
4. Open the Neon console and confirm storage usage is tiny.
## Local-first order of work
1. Create the Neon project, a `dev` branch, and the two roles.
2. Write and run `001_init.sql` and `002_roles.sql` on dev.
3. Write `publish.py` and its unit tests. Run `publish --dry-run` against the real Sheet.
4. Write `storage/neon.py` and the integration tests. Run `publish` against dev twice.
5. Build the frontend (doc 14) against dev.
6. Only after the frontend passes locally: create the production branch and migrate it, add the secret, add the workflow step, and watch three scheduled runs.
## Open items
| ID | Item | Needed for |
|---|---|---|
| O7 | Confirm the `Storage.load_table("jobs")` return shape is `list[dict[str, str]]` (inferred from `dashboard.py`) | Writing `publish.py` |
| O8 | Confirm whether `follow_up_due` or `applied_on` should appear on the dashboard (currently excluded) | Schema, if added later |
| O9 | Eligibility is only as good as the source's own region field. Example: a Netlify role is labeled worldwide but asks for a Denver-based candidate in its requirements. The dashboard shows what the pipeline scored, so the posting must still be read | Dashboard wording, optional future filter |
