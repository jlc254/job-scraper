# PostgreSQL Audit — job-scraper (Neon Free Tier)

**Audit date:** 2026-10-29
**Database:** Neon project `autumn-rain-77812061` ("job-scrapper"), org `Jumalaw98` (Free plan), region `aws-us-east-2`
**Engine:** PostgreSQL 18.6, database `neondb`, owner `neondb_owner`
**Audit mode:** Read-only. No schema, role, configuration, application code, or data changes were made.
**Report path:** `docs/database/postgresql-audit-report.md`

---

## A. Executive summary

The database layer is in good shape for a small, single-writer workload. The design is deliberate: a profile-scoped primary key, a generated `search` tsvector with a GIN index, two narrowly granted login roles, a transactional publish path with a stale-row sweep, and retention rules with destructive-operation guards. Live metadata matches the migrations that are checked into the repository. Resource usage is far below Free-tier ceilings (≈1.7 MB of a 1 GB database, ≈4.3 CU-hours of 100 per month, ≈11 MB of 5 GB egress).

The material risks are not in the schema; they are in **operational assurance**:

1. **Recovery is untested and partly unmanaged.** Free tier has no backup schedule, only a 6-hour PITR window. The documented recovery story ("rebuild from the Google Sheet") has no written, rehearsed procedure, and no restore has been performed.
2. **The dashboard's database role cannot be confirmed as the read-only `jobs_reader`.** A `jobs_reader` role with `SELECT`-only grants exists and is documented, but whether the production `DATABASE_URL` actually uses it cannot be determined without decrypting a Vercel secret. If the dashboard uses `neondb_owner`, the read-only separation is decorative.
3. **Migrations are applied by hand.** There is no runner, no checksum, no rollback path, and no CI drift check. Schema correctness currently depends on operator discipline.
4. **No query-level performance visibility.** `pg_stat_statements` is preloaded but not installed, and Free tier offers no metrics export.
5. **Security hardening gaps:** no RLS (acceptable here), no statement/lock timeouts, no `gitleaks` in CI (the pre-commit config exists but hooks are not installed), and the database accepts public connections (IP Allow is Scale-plan-only).

**Overall rating by pillar**

| Pillar | Rating | One-line verdict |
|---|---|---|
| Performance | Good | Right indexes for the workload; blind without query stats |
| Security | Fair | Strong role split on paper; unverified in production, no timeouts |
| Integrity | Good | Strong publish transaction and guards; weak cross-table constraints |
| Backups / recovery | Poor | No schedule, no tested restore, 6-hour window only |
| Monitoring | Fair | Pipeline alerting exists; no database-capacity alerting |
| Migrations | Fair | Versioned and applied, but fully manual and unverified in CI |

**Do these first (this week):** confirm the dashboard role (SEC-01), run one restore drill into a branch (BAK-02), install `pg_stat_statements` (PERF-04), set statement/lock timeouts (SEC-05), and delete the four stale preview branches (OPS-01). All are Free-tier compatible and low risk.

---

## B. Application and database context

**What the database serves**

- A scraper publishes job postings twice a day (`daily.yml`, 03:07 and 13:07 UTC) from GitHub Actions.
- A Next.js dashboard reads the postings with search, filters, sorting, and pagination.
- Two personas share one table, distinguished by `profile` (`juliet`, `jumalaw98`).

**Schema (verified live)**

| Object | Definition highlights |
|---|---|
| `public.jobs` | PK `(profile, job_id)`; generated `search` tsvector over title/company/excerpt; `match_score numeric NULL`; `match_tier` with CHECK; `job_url` http(s) CHECK; `profile` regex CHECK; `application_status` default `'New'`; no foreign keys |
| `public.publish_meta` | PK `profile`; tracks `job_count`, `published_at`, `last_run_id` |
| `public.schema_migrations` | PK `version`; owner-only; records `001_init` … `004_persona_rename` |

**Indexes (verified live)**

`jobs_pkey` (PK), `jobs_profile_tier_score_idx`, `jobs_profile_score_idx`, `jobs_profile_first_seen_idx`, `jobs_deadline_idx`, `jobs_source_idx`, `jobs_search_idx` (GIN, 456 kB), `jobs_skills_idx` (GIN).

**Roles and grants (verified live)**

| Role | Attributes | Grants |
|---|---|---|
| `jobs_publisher` | LOGIN, no superuser/BYPASSRLS/CREATEDB/CREATEROLE, no role-level config | Full DML on `jobs` and `publish_meta`; `USAGE` on `public` |
| `jobs_reader` | LOGIN, same restrictions | `SELECT` only on `jobs`, `publish_meta`; `USAGE` on `public` |
| `neondb_owner` | Owner of the database and tables | Full |
| `cloud_admin`, `neon_superuser`, `neon_service` | Platform-managed | Not used by the application |

Password encryption is `scram-sha-256`. Row-level security is **not** enabled on any table. The `public` schema grants `USAGE` to `PUBLIC` but not `CREATE`.

**Data profile (verified)**

- 131 rows total: `juliet` 106, `jumalaw98` 25; all active; 0 reposts.
- No duplicate `job_url` within a profile; no null `match_score`, no null `search`; 102 null deadlines; 28 empty `skills_matched`; 4 distinct sources.
- `publish_meta.job_count` reconciles exactly with live row counts (106 + 25 = 131); last publish `2026-10-29T09:49:08.807Z`.

**Sizes and activity (verified)**

- `jobs`: heap 408 kB, indexes 664 kB, total 1704 kB. Database 9632 kB.
- Cumulative since stats reset (never reset): 482 sequential scans vs 1522 index scans.
- Zero-scan indexes: `jobs_search_idx`, `jobs_skills_idx`, `jobs_deadline_idx`. `jobs_source_idx` has 22 scans.
- `publish_meta`: 32 dead tuples, never manually vacuumed or analyzed (autovacuum handles `jobs`; last autovacuum/autoanalyze 2026-10-29).

**Configuration relevant to the audit (verified)**

`ssl=off` on the compute node (TLS terminates at the Neon proxy — expected), `statement_timeout=0`, `lock_timeout=0` (default), `idle_in_transaction_session_timeout=5min`, `work_mem=4MB`, `max_connections=901`, `autovacuum=on`, `wal_level=replica`, `pg_stat_statements` in `shared_preload_libraries` but **not installed as an extension**.

**Connection topology**

- Publisher: direct connection as `jobs_publisher`, one transaction per profile, `executemany` batches of 200, upsert plus stale-row delete, with a connect-retry for scale-to-zero.
- Dashboard: Neon HTTP driver for `*.neon.tech` hosts, otherwise a `pg` pool capped at 5; one retry on transient/connection errors; all list/count queries filtered by `profile`; `LIMIT/OFFSET` pagination (25/page, max 50, page ≤ 10,000); 60-second `unstable_cache` on overview and filter options.
- Branching: `main` (default), `devtest`, archived `vercel-dev`, and four `preview/dependabot/*` branches — 7 of the 10 allowed on Free.

**Usage against Free-tier limits (verified)**

| Limit | Allowance | Observed | Headroom |
|---|---|---|---|
| Storage | 1 GB / project | ≈1.7 MB | ~99.8% |
| Compute | 100 CU-h / project / month | ≈4.3 CU-h since 2026-10-10 | large |
| Egress | 5 GB / month | ≈11 MB | ~99.8% |
| Branches | 10 | 7 | 3 |
| PITR history | 6 h, capped at 1 GB | 21 600 s configured | — |
| Manual snapshots | 1 | 0 used | 1 |
| Monitoring retention | 1 day | — | — |

**Scope of inspection**

Repository: `migrations/*.sql`, `src/jobscraper/storage/neon.py`, `src/jobscraper/publish.py`, `src/jobscraper/retention.py`, `frontend/lib/{db,sql,queries,filters}.ts`, `frontend/components/Pagination.tsx`, `.github/workflows/*.yml`, `scripts/neon_preview_branch.sh`, `docs/08-security.md`, `docs/09-scheduling-and-setup.md`, `docs/13-neon-database-and-publish.md`, `docs/PUBLISH-INTEGRATION.md`, `.gitignore`, `.env.example`, `frontend/.env.example`, `.pre-commit-config.yaml`.
Live database: catalog, roles, grants, settings, statistics, sizes, replication/history metadata, branch inventory, usage metrics.
Vercel: environment variable **names and targets only**; no secret values were decrypted or printed.

---

## C. Six-pillar matrix

| Pillar | Verified implemented | Partially implemented | Missing | Needs verification | Overall |
|---|---|---|---|---|---|
| **Performance** | Profile-leading composite indexes; GIN search and skills indexes; 60 s dashboard cache; batched publish; pool cap 5 | Index usage hygiene (three zero-scan indexes, correct for 131 rows) | Query-level statistics, slow-query baseline, timeout policy | Whether the planner stays off the GIN indexes as data grows | Good |
| **Security** | Separate `jobs_publisher` / `jobs_reader` logins; least-privilege grants; SCRAM-SHA-256; secrets scoped per workflow step; TLS to the proxy | Role separation (unverified in production); secret scanning (config present, hooks and CI absent) | RLS, statement/lock timeouts, network restriction (paid feature), audit logging | Which role the dashboard actually authenticates as | Fair |
| **Integrity** | `(profile, job_id)` PK; single transaction per profile; upsert + stale sweep; zero/collapse guard; profile-scoped deletes; `prune_profiles` refuses empty keep; retention guards | Cross-table consistency (`publish_meta` ↔ `jobs`); value-domain checks | Advisory lock for concurrent publishes; `match_score` range check; constrained `application_status` | Behavior under two simultaneous publishes | Good |
| **Backups / recovery** | 6-hour PITR window; branch-based recovery available; Google Sheet as external source of truth | Snapshot usage (1 allowed, 0 used); documented rebuild story | Backup schedule, restore drill, documented RPO/RTO, retention of exported data | Whether a restore has ever been executed successfully | Poor |
| **Monitoring** | Workflow failure notifications; optional Healthchecks ping; `publish_meta` freshness fields | Capacity/branch/usage monitoring (manual only) | DB size, CU-hour, branch-cap, connection, and staleness alerts; query stats; log export (paid) | Alert delivery path actually reaching a human | Fair |
| **Migrations** | Four versioned, idempotent migrations applied and recorded; constraints and grants encoded in SQL | Runner (manual `psql` steps); documentation of apply order | Checksums, down migrations, CI drift check, migration test on a branch | Whether `main` matches migrations exactly (spot-checked only) | Fair |

---

## D. Detailed findings

Priority scale: **Critical** (act now), **High** (this sprint), **Medium** (this quarter), **Low** (backlog).
Effort: **S** ≤ 1 h, **M** ≤ 1 day, **L** > 1 day.

### Performance

#### PERF-01 — Three indexes have never been used
- **Status:** Needs verification
- **Evidence:** `pg_stat_user_indexes.idx_scan = 0` for `jobs_search_idx`, `jobs_skills_idx`, `jobs_deadline_idx`; `jobs_source_idx` = 22. Table has 131 rows, where sequential scans are legitimately cheaper; 482 seq scans recorded.
- **Description:** The GIN and deadline indexes are unread. At this size the planner is correct to ignore them, so this is not evidence of a design error — but it is also not evidence that they work.
- **Risk / impact:** Low today. If the table grows and the planner still avoids them, search latency degrades silently. Dropping them now would be premature and would slow a future growth path.
- **Recommended action:** Keep all indexes. Record a baseline `EXPLAIN (ANALYZE, BUFFERS)` for the dashboard's list, count, and search queries; re-check `idx_scan` after the table passes ~50 k rows or after any latency complaint.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes — read-only inspection.
- **Dependencies / verification:** Compare `idx_scan` before/after a month of dashboard use; confirm GIN is chosen for `websearch_to_tsquery('english', ...)` once row counts justify it.
- **Remediation risk:** Dropping indexes is irreversible without a rebuild (a write-locking operation on large tables). Do not drop based on zero counters alone.

#### PERF-02 — No query-level performance visibility
- **Status:** Missing
- **Evidence:** `pg_stat_statements` appears in `shared_preload_libraries` but `SELECT * FROM pg_extension` does not list it; Neon MCP query-analysis tools are unusable as a result.
- **Description:** There is no per-statement latency, call-count, or rows-examined data. Performance work is currently guesswork.
- **Risk / impact:** Medium. Regressions from a query change or a data-shape change would be discovered by users, not by the team.
- **Recommended action:** `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;` (a schema change, so schedule it explicitly), then review the top statements by `total_exec_time` weekly. If extension creation is undesirable, capture `EXPLAIN (ANALYZE, BUFFERS)` output for the five dashboard query shapes into `docs/database/` instead.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes — extension is preloaded; no paid feature required.
- **Dependencies / verification:** Requires a write to the database (extension creation) and therefore explicit approval; verify with `SELECT count(*) FROM pg_stat_statements;`.
- **Remediation risk:** Minimal. The extension adds a small shared-memory overhead and resets on compute restart (scale-to-zero), so trends are per-compute-session unless exported.

#### PERF-03 — `publish_meta` has never been vacuumed or analyzed
- **Status:** Partially implemented
- **Evidence:** 32 dead tuples; `last_vacuum` / `last_analyze` / `last_autovacuum` / `last_autoanalyze` are null.
- **Description:** The table is tiny and autovacuum thresholds are percentage-based, so it may never trigger. Statistics for the planner are absent.
- **Risk / impact:** Low. Query plans on a two-row table are irrelevant; dead tuples cost kilobytes.
- **Recommended action:** No emergency action. Optionally lower autovacuum thresholds for the table, or accept it — at this size the practical impact is nil.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables WHERE relname = 'publish_meta';`
- **Remediation risk:** Manual `VACUUM` is harmless but unnecessary; avoid tuning global autovacuum for a 32-tuple table.

#### PERF-04 — `OFFSET` pagination has a hard ceiling
- **Status:** Verified implemented (with a known limit)
- **Evidence:** `frontend/components/Pagination.tsx` and query builders cap page size at 50 and page number at 10,000; queries use `LIMIT/OFFSET` with a stable sort allowlist.
- **Description:** Deep offsets force the database to walk and discard rows. The 10,000-page cap bounds the worst case; at current data volume this is invisible.
- **Risk / impact:** Low now, Medium if the table grows into the hundreds of thousands while users page deep.
- **Recommended action:** Keep the cap. When rows exceed ~100 k, move to keyset pagination on `(match_score DESC, job_id)` or `(first_seen DESC, job_id)`, keeping the same sort allowlist.
- **Priority:** Low · **Effort:** M
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Measure `EXPLAIN (ANALYZE)` at the highest permitted offset after data growth; confirm plan is an index scan, not a full sort.
- **Remediation risk:** Keyset pagination changes URL semantics and breaks bookmarked page numbers; plan a redirect or accept the change.

#### PERF-05 — Dashboard connection reuse is bounded and appropriate
- **Status:** Verified implemented
- **Evidence:** `frontend/lib/db.ts` uses the Neon HTTP driver for `*.neon.tech` and a `pg` pool with `max: 5` otherwise; one retry on transient errors.
- **Description:** Pool sizing is conservative relative to `max_connections=901` and avoids exhausting connections during serverless bursts.
- **Risk / impact:** None observed.
- **Recommended action:** None. Revisit only if serverless concurrency rises enough to queue on 5 connections.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Watch for connection-acquisition latency in Vercel logs.
- **Remediation risk:** N/A.

### Security

#### SEC-01 — The dashboard's database role is unverified
- **Status:** Needs verification (highest-value unknown in this audit)
- **Evidence:** `jobs_reader` exists with `SELECT`-only grants and is documented as the dashboard role (`docs/09-scheduling-and-setup.md`, `docs/PUBLISH-INTEGRATION.md`). Vercel exposes `DATABASE_URL` and `DATABASE_URL_UNPOOLED` for production, preview, and development, plus per-branch preview entries, but values are encrypted. At sample time `pg_stat_activity` showed only `neondb_owner` sessions (8 via pgbouncer) — which may be the dashboard, the Neon MCP server used for this audit, or platform backends.
- **Description:** The read-only separation is only real if production actually authenticates as `jobs_reader`. If `DATABASE_URL` carries `neondb_owner`, a compromised frontend or an injection bug has full DML and DDL reach.
- **Risk / impact:** High. This is the difference between a contained read-path compromise and full database takeover.
- **Recommended action:** In the Vercel dashboard, open the production `DATABASE_URL` and confirm the username is `jobs_reader`. Do not paste the value anywhere. If it is not, rotate to a `jobs_reader` connection string (direct or pooled as appropriate) and redeploy.
- **Priority:** High · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `SELECT usename, count(*) FROM pg_stat_activity GROUP BY 1;` during active dashboard traffic should show `jobs_reader`. Corroborate by running `SELECT current_user;` from a diagnostic route once, then remove it.
- **Remediation risk:** A wrong connection string breaks the dashboard on deploy; stage the change on a preview deployment first.

#### SEC-02 — No row-level security
- **Status:** Missing (by design)
- **Evidence:** `pg_class.relrowsecurity = false` for `jobs` and `publish_meta`; no policies exist.
- **Description:** Isolation between the two personas is enforced only in application `WHERE profile = $1` clauses, which were verified as consistently applied in list, count, and detail queries.
- **Risk / impact:** Medium. A future query that forgets the filter leaks the other persona's rows. The blast radius is limited to two personas in one product, not multiple tenants.
- **Recommended action:** Either document "no RLS by design, single-tenant-per-deployment" as an accepted decision, or add policies keyed on a session variable (e.g. `current_setting('app.profile')`) and set it per connection. Do not add RLS without also auditing every query path — it will silently return zero rows where the setting is absent.
- **Priority:** Low · **Effort:** M
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Test with a `jobs_reader` session: `SET app.profile = 'juliet'; SELECT count(*) FROM jobs;` should return only Juliet's rows.
- **Remediation risk:** High operational risk if rolled out without full query coverage; the dashboard would appear empty rather than error.

#### SEC-03 — Database accepts public connections; no network restriction available on Free
- **Status:** Missing (plan-limited)
- **Evidence:** Project setting `block_public_connections = false`; Neon documentation confirms IP Allow is a Scale-plan feature; TLS is required for all connections and terminated at the proxy.
- **Description:** Anyone with valid credentials can connect from any IP. Protection rests entirely on credential strength and secrecy.
- **Risk / impact:** Medium. Credential leakage is the primary path to exploitation, and there is no network-layer mitigation.
- **Recommended action:** Treat database credentials as high-value secrets: keep them only in GitHub/Vercel secret stores, never in `.env` committed files, rotate on any suspicion, and consider upgrading to Scale if network allowlisting becomes a compliance requirement.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Partially — the control itself requires Scale. Compensating controls (rotation, scoping) are Free-compatible.
- **Dependencies / verification:** Confirm `ssl` is enforced by connecting with `sslmode=require`; confirm no credential appears in repository history (`gitleaks detect`).
- **Remediation risk:** Enabling IP Allow without including CI runner egress ranges would break publishing.

#### SEC-04 — `ssl=off` on the compute node is expected, not a finding
- **Status:** Verified implemented
- **Evidence:** `SHOW ssl` returns `off`; Neon documentation states TLS is mandatory and terminated at the proxy, with unencrypted connections rejected.
- **Description:** The compute node sees plaintext from the proxy, which is inside Neon's trust boundary. Client-to-proxy traffic is encrypted.
- **Risk / impact:** None, provided clients use `sslmode=require` (the default for Neon connection strings).
- **Recommended action:** None. Do not attempt to enable compute-level SSL.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `psql "…?sslmode=require" -c 'select 1'` must succeed; `sslmode=disable` must fail.
- **Remediation risk:** N/A.

#### SEC-05 — No statement, lock, or idle-in-transaction policy for application roles
- **Status:** Missing
- **Evidence:** `statement_timeout=0`, `lock_timeout=0` (default), `idle_in_transaction_session_timeout=5min`; `pg_roles.rolconfig` is null for both application roles.
- **Description:** A runaway dashboard query or a publisher blocked on a lock can hold resources until the client disconnects. On Free tier, compute hours are metered and shared.
- **Risk / impact:** Medium. A single pathological query can burn CU-hours and delay other work; a lock wait can stall the twice-daily publish.
- **Recommended action:** Set role-level defaults, which are Free-compatible and survive reconnects:
  `ALTER ROLE jobs_reader SET statement_timeout = '15s';`
  `ALTER ROLE jobs_reader SET lock_timeout = '3s';`
  `ALTER ROLE jobs_publisher SET statement_timeout = '120s';`
  `ALTER ROLE jobs_publisher SET lock_timeout = '10s';`
  Verify against real publish duration before committing (current publishes are small and fast).
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `SELECT rolname, rolconfig FROM pg_roles WHERE rolname LIKE 'jobs_%';` and a deliberate `SELECT pg_sleep(60)` as `jobs_reader` must fail at 15 s.
- **Remediation risk:** A timeout that is too tight will break the publish mid-transaction (it rolls back cleanly, but the run fails and alerts). Measure first; start generous.

#### SEC-06 — Secret scanning is configured but not enforced
- **Status:** Partially implemented
- **Evidence:** `.pre-commit-config.yaml` pins `gitleaks` v8.18.4, but hooks are not installed locally and `.github/workflows/ci.yml` has no `gitleaks` job. `.env` is git-ignored and untracked; `.env.example` contains placeholders only; `lock.log` is empty.
- **Description:** The control exists as configuration, not as a gate. A committed secret would reach the remote.
- **Risk / impact:** Medium. Given the database accepts public connections (SEC-03), a leaked connection string is directly exploitable.
- **Recommended action:** Add a `gitleaks` job to `ci.yml` on `pull_request` and `push`, and enable the pre-commit hook in the documented setup. Keep `permissions: contents: read`.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes (CI-side control).
- **Dependencies / verification:** Introduce a fake token in a throwaway branch and confirm CI fails; run `pre-commit run gitleaks --all-files` locally.
- **Remediation risk:** False positives on fixtures can block merges; maintain a narrowly scoped `.gitleaksignore` rather than disabling the rule.

#### SEC-07 — Publisher secret is correctly scoped
- **Status:** Verified implemented
- **Evidence:** `daily.yml` grants `permissions: contents: read` and exposes `NEON_DATABASE_URL_PUBLISHER` only on the publish step, not job-wide.
- **Description:** Least-privilege secret exposure is done well; the dashboard never receives publisher credentials.
- **Risk / impact:** None observed.
- **Recommended action:** Preserve this pattern when adding steps; do not promote the secret to workflow-level `env`.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Review workflow diffs for `env:` at job scope.
- **Remediation risk:** N/A.

#### SEC-08 — No credential rotation or inventory record
- **Status:** Missing
- **Evidence:** No rotation procedure in `docs/`; no record of when role passwords were last changed.
- **Description:** Rotating `jobs_publisher` or `jobs_reader` requires coordinated updates in GitHub and Vercel; without a written procedure it will be deferred during an incident.
- **Risk / impact:** Low to Medium, depending on exposure.
- **Recommended action:** Document a 3-step rotation runbook (create new password → update GitHub/Vercel secret → verify next publish and dashboard load → revoke old). Rotate at least annually and after any suspected exposure.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Dry-run the runbook on the `devtest` branch.
- **Remediation risk:** Rotation done out of order breaks publish or dashboard until both stores are updated.

### Integrity

#### INT-01 — Concurrent publishes can leave stale rows
- **Status:** Partially implemented
- **Evidence:** `storage/neon.py` performs upsert-then-delete (`published_at < run_start`) inside one transaction per profile, but takes no advisory lock. GitHub Actions uses a concurrency group, which protects scheduled runs only; a local or manual run can overlap a scheduled one.
- **Description:** Two overlapping publishes for the same profile can each sweep rows the other just wrote, or race on the same keys. The stale-delete predicate reduces the window but does not eliminate it.
- **Risk / impact:** Medium. Symptom is missing or duplicated postings until the next successful run; the `publish_meta.job_count` reconciliation would reveal it.
- **Recommended action:** Take a transaction-scoped advisory lock keyed on the profile at the start of each publish: `SELECT pg_advisory_xact_lock(hashtext($1));` and let the second run wait or abort. This requires a small code change and is Free-compatible.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Simulate two concurrent publishes against `devtest`; confirm one serializes and `job_count` still reconciles.
- **Remediation risk:** A lock held by a crashed session is released at transaction end, so the failure mode is a short wait, not a deadlock — provided the lock is transaction-scoped, not session-scoped.

#### INT-02 — No referential link between `publish_meta` and `jobs`
- **Status:** Missing
- **Evidence:** No foreign key; `publish_meta.profile` and `jobs.profile` are independent text columns with a regex CHECK.
- **Description:** A metadata row can exist with no jobs, or a profile can have jobs with no metadata row. Current data reconciles, so this is a guardrail gap, not a present defect.
- **Risk / impact:** Low. The dashboard's freshness display could mislead after a partial failure.
- **Recommended action:** Add a lightweight consistency check to the publish path or a periodic assertion: `SELECT p.profile FROM publish_meta p LEFT JOIN jobs j USING (profile) GROUP BY 1 HAVING count(j.*) <> max(p.job_count);` Feed a non-empty result into the existing alerting.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Run the query; it must return zero rows after every publish.
- **Remediation risk:** A true FK would require a profiles table and would complicate the delete-then-insert publish flow; prefer an assertion over a constraint here.

#### INT-03 — Value domains are only partly constrained
- **Status:** Partially implemented
- **Evidence:** `match_tier` has a CHECK; `profile` has a regex CHECK; `job_url` has an http(s) CHECK. `match_score` accepts any numeric; `application_status` is unconstrained text with default `'New'`.
- **Description:** A bug or manual edit can write `match_score = 999` or `application_status = 'new'` (case variant), fragmenting filters and sort order.
- **Risk / impact:** Low. The dashboard's status filter would silently miss mismatched values.
- **Recommended action:** Add `CHECK (match_score IS NULL OR match_score BETWEEN 0 AND 100)` and `CHECK (application_status IN ('New','Applied','Interview','Offer','Rejected','Archived'))` after confirming the exact value set used by the UI. Validate existing rows first.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `SELECT DISTINCT application_status FROM jobs;` before writing the constraint.
- **Remediation risk:** `ALTER TABLE … ADD CONSTRAINT` takes an ACCESS EXCLUSIVE lock and validates existing rows; on 131 rows this is instant, but confirm no publish is running.

#### INT-04 — Publish transaction and destructive guards are solid
- **Status:** Verified implemented
- **Evidence:** Single transaction per profile; `executemany` batches of 200; upsert with `ON CONFLICT (profile, job_id)`; stale sweep `published_at < run_start`; zero/collapse guard refuses to publish an empty or drastically shrunken result; all deletes are profile-scoped; `prune_profiles` refuses an empty keep-list; retention deletes only `New` rows older than 60 days, with a >50% guard above 20 rows.
- **Description:** This is the strongest part of the database design: every destructive path has a bound and a guard.
- **Risk / impact:** None observed; failures roll back cleanly.
- **Recommended action:** Add a regression test that asserts the guards fire (empty result, >50% shrink, empty keep-list), so refactors cannot quietly remove them.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `pytest` cases exercising each guard against a scratch schema.
- **Remediation risk:** N/A.

#### INT-05 — Retention boundaries are correct but data-dependent
- **Status:** Verified implemented
- **Evidence:** Jobs deleted after 60 days only while status is `New`; inactive after 7 days; excluded/runs/health after 30 days; guard blocks >50% deletion when more than 20 rows qualify.
- **Description:** Rules are sound. The 60-day boundary interacts with `application_status`; an `Applied` row is retained indefinitely, which is intended.
- **Risk / impact:** Low. Unbounded growth is possible only through applied rows, which are inherently few.
- **Recommended action:** None now; revisit if applied rows exceed a few thousand.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Log deletion counts per run and graph them; a sudden zero or a >50% block indicates a bug.
- **Remediation risk:** Tightening retention risks deleting rows a user still expects; always keep the guard.

### Backups and recovery

#### BAK-01 — No automated backup schedule on Free tier
- **Status:** Missing (plan-limited)
- **Evidence:** Neon Free provides a 6-hour PITR window (`history_retention_seconds = 21600`, capped at 1 GB) and one manual snapshot, but no scheduled backups. No snapshot has been created.
- **Description:** Recovery from anything older than 6 hours depends on rebuilding from the Google Sheet, which is a data source, not a database backup (no `application_status`, no `match_score` history, no `publish_meta`).
- **Risk / impact:** High. A logical corruption discovered a week later is unrecoverable to the exact prior state.
- **Recommended action:** (a) Create the one permitted manual snapshot now, as a known-good baseline. (b) Add a weekly logical export (`pg_dump --data-only --format=custom` or per-table CSV) to an external store, run from an existing workflow, with a retention of 8 weeks. (c) Document that 6 hours is the PITR bound and state the resulting RPO.
- **Priority:** High · **Effort:** M
- **Neon Free compatibility:** Yes — one snapshot plus external dumps; no paid feature.
- **Dependencies / verification:** Confirm the snapshot exists in the console; restore a dump into a scratch branch and compare row counts per profile.
- **Remediation risk:** `pg_dump` consumes compute and egress; at 1.7 MB this is negligible, but schedule it off-peak and keep it to one run per week.

#### BAK-02 — No restore has ever been tested
- **Status:** Missing
- **Evidence:** No restore procedure or drill record in `docs/`; `docs/13-neon-database-and-publish.md` describes the Sheet as the rebuild source but documents no execution.
- **Description:** An untested backup is a hypothesis. The team does not know whether a branch restore, a PITR restore, or a dump restore actually reconstitutes a working dashboard.
- **Risk / impact:** High. Discovery of a broken restore during an incident converts a recoverable outage into data loss.
- **Recommended action:** Run a drill on `devtest`: create a branch from `main` at a timestamp before the last publish, point a preview deployment at it, load the dashboard, and verify counts (106 / 25) and search behavior. Record duration and steps in `docs/database/restore-drill.md`. Repeat quarterly.
- **Priority:** High · **Effort:** M
- **Neon Free compatibility:** Yes — branch creation is within the 10-branch limit; delete the drill branch afterward.
- **Dependencies / verification:** Branch must be created from a timestamp inside the 6-hour window; a drill against an older point will fail by design.
- **Remediation risk:** Pointing a preview deployment at a restored branch can write to it if the app is not read-only; use a reader connection string for the drill.

#### BAK-03 — No documented RPO/RTO
- **Status:** Missing
- **Evidence:** No targets stated in `docs/`.
- **Description:** Without targets, "is the backup good enough" cannot be answered, and the 6-hour window is not connected to a business expectation.
- **Risk / impact:** Medium. Recovery decisions during an incident will be improvised.
- **Recommended action:** Record an explicit position, e.g. RPO 24 h (weekly dump) with a 6 h best-effort window, RTO 2 h (branch restore plus redeploy). State the accepted data loss for each persona.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes (documentation).
- **Dependencies / verification:** Review with the product owner; align BAK-01's dump frequency to the stated RPO.
- **Remediation risk:** N/A.

#### BAK-04 — Branch inventory is drifting toward the Free-tier cap
- **Status:** Partially implemented
- **Evidence:** 7 of 10 branches used: `main`, `devtest`, archived `vercel-dev`, and four `preview/dependabot/*`. `cleanup-neon-preview.yml` and `scripts/neon_preview_branch.sh` handle preview lifecycle but left these behind.
- **Description:** Lingering branches consume the cap and can hold data from old previews. Hitting the cap blocks CI preview creation and, worse, blocks a recovery branch during an incident.
- **Risk / impact:** Medium. The failure appears at the worst possible moment — when a new branch is needed urgently.
- **Recommended action:** Delete the four stale `preview/dependabot/*` branches and the archived `vercel-dev`; investigate why cleanup did not fire (likely runs that never reached the teardown job). Add a weekly sweep that deletes preview branches older than 7 days.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes — keeps usage inside the 10-branch limit.
- **Dependencies / verification:** `neonctl branches list` should show 3 or fewer; the next preview run should create and delete cleanly.
- **Remediation risk:** Deleting a branch is irreversible; confirm no preview deployment still points at it before deletion.

### Monitoring

#### MON-01 — No database-capacity or limit alerting
- **Status:** Missing
- **Evidence:** Alerting consists of GitHub Actions failure notifications and an optional Healthchecks ping. No alert covers database size, CU-hours, branch count, connection count, or egress.
- **Description:** Free-tier limits fail by throttling or suspending, not by a graceful error. The first signal would be a failed publish or an unavailable dashboard.
- **Risk / impact:** Medium. Storage and branches are the realistic risks (compute has large headroom).
- **Recommended action:** Add a scheduled job (daily, in an existing workflow) that reads `pg_database_size(current_database())`, counts branches via the Neon API, and warns at 70% of any limit; route to the same notification channel as workflow failures.
- **Priority:** Medium · **Effort:** M
- **Neon Free compatibility:** Yes — metadata queries and the Neon API are free.
- **Dependencies / verification:** Temporarily lower a threshold and confirm an alert fires.
- **Remediation risk:** Alert fatigue if thresholds are noisy; alert on 70% and 90%, not on every change.

#### MON-02 — No data-freshness alert
- **Status:** Partially implemented
- **Evidence:** `publish_meta` records `published_at` and `job_count`; the dashboard displays freshness; no alert fires when it goes stale.
- **Description:** A publish that runs but writes nothing (upstream breakage) is not the same as a publish that fails. Only the latter currently generates a signal.
- **Risk / impact:** Medium. Silent staleness is the most likely real-world failure of this system.
- **Recommended action:** Add an assertion after publish and a daily check: `SELECT profile, now() - published_at AS age FROM publish_meta WHERE now() - published_at > interval '26 hours';` Any row is an alert.
- **Priority:** Medium · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Backdate `published_at` on `devtest` and confirm the check alerts.
- **Remediation risk:** A legitimate pause (holiday, deliberate disable) will page; document how to silence it.

#### MON-03 — Monitoring retention is one day and not exportable
- **Status:** Missing (plan-limited)
- **Evidence:** Neon Free retains metrics for 1 day and provides no metrics/log export.
- **Description:** Post-incident analysis of a failure three days ago is impossible from the platform. Logs live only in GitHub Actions output.
- **Risk / impact:** Low to Medium. The application's own artifacts (`publish_meta`, run logs, Healthchecks) partly compensate.
- **Recommended action:** Persist what matters outside Neon: keep workflow logs at least 30 days, and have the publish step emit a one-line JSON summary (rows read, written, deleted, duration) that is easy to grep later.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Partially — export requires a paid plan; external logging is free.
- **Dependencies / verification:** Confirm the summary line appears in the last successful run's log.
- **Remediation risk:** N/A.

#### MON-04 — Pipeline alerting is implemented
- **Status:** Verified implemented
- **Evidence:** `daily.yml` fails visibly in GitHub, posts a Telegram alert on failure (token passed through curl's config on stdin, never argv), and optionally pings Healthchecks; `ci.yml` fails visibly; secrets are step-scoped.
- **Description:** The "did it run" signal exists and is reliable.
- **Risk / impact:** None observed.
- **Recommended action:** Verify that GitHub notifications actually reach a human (email filters and mute rules frequently swallow them).
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Trigger a deliberate failure on a scratch branch and confirm receipt.
- **Remediation risk:** N/A.

### Migrations

#### MIG-01 — Migrations are applied manually, without a runner
- **Status:** Partially implemented
- **Evidence:** `migrations/001_init.sql` … `004_persona_rename.sql` exist and are recorded in `schema_migrations`, but `docs/13-neon-database-and-publish.md` instructs manual `psql` execution. No runner is wired into CI or deploy.
- **Description:** Applying the wrong file, applying twice, or skipping one depends entirely on operator care. `003` and `004` are the kind of change (rename plus constraint rewrite) where a partial apply is damaging.
- **Risk / impact:** Medium. Drift between repository and production is currently undetectable.
- **Recommended action:** Add a minimal runner (a shell script that reads `schema_migrations`, applies pending files in order inside a transaction, and records the version) or adopt a lightweight tool. Keep it manual-trigger, not automatic-on-deploy, until it has proven itself on `devtest`.
- **Priority:** Medium · **Effort:** M
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Run it against a fresh branch; the resulting schema must match `main` (compare `\d+` output or an information_schema diff).
- **Remediation risk:** A runner that applies an untested migration to production is worse than manual steps; gate it behind review and a branch test.

#### MIG-02 — No checksums and no drift detection
- **Status:** Missing
- **Evidence:** `schema_migrations` stores `version` (PK) and `applied_at` only. No checksum column, and no CI job comparing the live schema to the migrations.
- **Description:** An edited-in-place migration, or a manual `ALTER` in the console, leaves no trace. The audit's live inspection matched the migrations, but that was a point-in-time manual comparison.
- **Risk / impact:** Medium. Silent drift is the classic cause of "works in dev, fails in prod".
- **Recommended action:** Add `checksum` and `applied_at` columns to `schema_migrations` (a new migration), record SHA-256 of each file, and add a CI step that dumps the live schema from a scratch branch and diffs it against a committed `schema.sql`.
- **Priority:** Medium · **Effort:** M
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Change one migration file and confirm CI fails the checksum comparison.
- **Remediation risk:** Retrofitting checksums requires trusting the current state as the baseline; do it immediately after a verified drift check.

#### MIG-03 — No down migrations or rollback plan
- **Status:** Missing
- **Evidence:** All four migrations are forward-only; no `down` files or documented reversal.
- **Description:** If `004_persona_rename` had gone wrong, the recovery path would have been a PITR restore, not a scripted rollback.
- **Risk / impact:** Medium. A failed forward migration blocks deploys until someone improvises.
- **Recommended action:** For each future migration, write the reversal in the PR description (even if not automated) and state whether it is PITR-only. Additive changes should be reversible by a companion migration; destructive changes should be two-phase (expand, then contract).
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** Rehearse the reversal for the next migration on `devtest`.
- **Remediation risk:** A hastily written down-migration can destroy data; prefer restore when in doubt.

#### MIG-04 — No migration test in CI
- **Status:** Missing
- **Evidence:** `ci.yml` runs `ruff`, `mypy`, `pytest`, `pip-audit`, and frontend checks; none of these touch a database or apply migrations.
- **Description:** A SQL syntax error or a constraint that fails on existing data is discovered at apply time, in production.
- **Risk / impact:** Medium.
- **Recommended action:** Add a CI job that creates an ephemeral Neon branch (or a local Postgres service container), applies all migrations from zero, and runs the schema assertions used in this audit. The preview-branch script already demonstrates the pattern.
- **Priority:** Medium · **Effort:** M
- **Neon Free compatibility:** Yes — ephemeral branch, deleted after the run; watch the 10-branch cap with concurrency limits.
- **Dependencies / verification:** Introduce a deliberately broken migration in a PR and confirm CI fails before merge.
- **Remediation risk:** CI-created branches that fail to delete will exhaust the branch cap; make teardown unconditional.

#### MIG-05 — Migration history and privileges are consistent
- **Status:** Verified implemented
- **Evidence:** Versions `001_init`–`004_persona_rename` recorded; `schema_migrations` is owner-only (application roles cannot tamper with it); grants for `jobs_publisher` and `jobs_reader` match the documented model.
- **Description:** The security-relevant part of migration handling is right: the ledger is not writable by application roles.
- **Risk / impact:** None observed.
- **Recommended action:** Preserve the owner-only grant when adding the checksum columns.
- **Priority:** Low · **Effort:** S
- **Neon Free compatibility:** Yes.
- **Dependencies / verification:** `has_table_privilege('jobs_publisher','schema_migrations','INSERT')` must be false.
- **Remediation risk:** N/A.

---

## E. Roadmap

### Immediate (next 7 days) — low risk, high value

| # | Action | Finding | Effort |
|---|---|---|---|
| 1 | Confirm production `DATABASE_URL` uses `jobs_reader`; fix if not | SEC-01 | S |
| 2 | Create the one permitted manual snapshot as a known-good baseline | BAK-01 | S |
| 3 | Run a restore drill on a branch and write `docs/database/restore-drill.md` | BAK-02 | M |
| 4 | Delete four stale preview branches and archived `vercel-dev` | BAK-04 | S |
| 5 | Install `pg_stat_statements` (requires approval — it is a write) | PERF-02 | S |
| 6 | Add `gitleaks` to CI | SEC-06 | S |
| 7 | Verify GitHub failure notifications reach a human | MON-04 | S |

### Short term (30 days)

| # | Action | Finding | Effort |
|---|---|---|---|
| 8 | Set role-level `statement_timeout` / `lock_timeout` after measuring real durations | SEC-05 | S |
| 9 | Add advisory lock to the publish path | INT-01 | S |
| 10 | Add data-freshness alert and publish-summary log line | MON-02, MON-03 | S |
| 11 | Add capacity/limit alerting (size, branches, CU-hours) | MON-01 | M |
| 12 | Write RPO/RTO and the credential-rotation runbook | BAK-03, SEC-08 | S |
| 13 | Add weekly external logical dump with 8-week retention | BAK-01 | M |
| 14 | Decide and document the RLS position (accept or implement) | SEC-02 | S |

### Medium term (quarter)

| # | Action | Finding | Effort |
|---|---|---|---|
| 15 | Add a minimal migration runner plus `checksum`/`applied_at` columns | MIG-01, MIG-02 | M |
| 16 | Add migration test on an ephemeral branch in CI | MIG-04 | M |
| 17 | Add schema-drift diff job | MIG-02 | M |
| 18 | Add `match_score` and `application_status` CHECK constraints | INT-03 | S |
| 19 | Add `publish_meta` ↔ `jobs` consistency assertion to the publish path | INT-02 | S |
| 20 | Record `EXPLAIN` baselines and re-check index usage after growth | PERF-01 | S |
| 21 | Make preview-branch teardown unconditional and add a weekly sweep | BAK-04 | S |

### Future / growth-triggered

| # | Action | Trigger |
|---|---|---|
| 22 | Keyset pagination | Table > ~100 k rows or deep-page latency |
| 23 | RLS implementation | Multi-tenant requirement or a second writer surface |
| 24 | IP Allow / protected branches | Compliance requirement, or upgrade to Scale |
| 25 | Metrics/log export, longer PITR | Incident analysis needs beyond 1 day / 6 hours |
| 26 | Re-evaluate zero-scan indexes | `idx_scan` still zero at > 50 k rows |

---

## F. Neon Free implementation plan

**What Free gives you (verified against current Neon documentation):** 1 GB storage per project (20 GB per account), 100 CU-hours per project per month, 10 branches, 5 GB egress, a 6-hour PITR window capped at 1 GB, one manual snapshot, 1-day metric retention, scale-to-zero after 5 minutes of inactivity, autoscaling up to 2 CU, and no IP Allow, protected branches, metrics export, backup schedules, or log export.

**How each recommendation fits**

| Recommendation | Free-compatible? | Mechanism |
|---|---|---|
| Role confirmation and rotation | Yes | Console + secret stores |
| `pg_stat_statements` | Yes | Preloaded; `CREATE EXTENSION` only |
| Role-level timeouts | Yes | `ALTER ROLE … SET` |
| Advisory lock in publish | Yes | Application SQL |
| Snapshot baseline | Yes | Exactly one snapshot allowed — use it deliberately |
| Restore drill | Yes | Branch from a timestamp inside the 6-hour window |
| Weekly logical dump | Yes | `pg_dump` to external storage (CI artifact or object store) |
| Freshness and capacity alerts | Yes | SQL + Neon API in an existing workflow |
| Branch cleanup | Yes | Keeps you under 10 |
| Migration runner + checksums | Yes | Script + SQL |
| Migration test in CI | Yes | Ephemeral branch; enforce teardown and concurrency limits |
| RLS | Yes | Policies + session variable |
| IP Allow | **No** | Scale plan; compensate with secret hygiene and rotation |
| Metrics/log export | **No** | Paid; persist summaries externally instead |
| Scheduled backups | **No** | Paid; use snapshot + external dumps |

**Budget guardrails**

- Compute is ~4.3 CU-hours used against 100/month, so the proposed changes (dumps, drills, CI branches) are affordable. A weekly `pg_dump` of 1.7 MB is noise.
- Each CI run that creates a branch must delete it in a `finally` block; four leaked branches already exist. Cap CI concurrency so no more than two ephemeral branches exist at once.
- Scale-to-zero means the first query after idle pays a cold start. Do not add high-frequency polling; daily and weekly checks are appropriate.
- The 6-hour PITR window is the binding constraint. The weekly dump exists precisely because 6 hours is too short to catch slow-burn corruption.

---

## G. Verification checklist

Run these after each remediation. All are read-only unless noted.

**Roles and security**

- [ ] `SELECT current_user;` from the dashboard runtime reports `jobs_reader` (add a temporary protected diagnostic route, then remove it).
- [ ] `SELECT usename, count(*) FROM pg_stat_activity GROUP BY 1;` during dashboard traffic shows `jobs_reader`.
- [ ] `SELECT rolname, rolconfig FROM pg_roles WHERE rolname LIKE 'jobs_%';` shows the configured timeouts.
- [ ] `SELECT pg_sleep(60);` as `jobs_reader` fails at the statement timeout.
- [ ] `psql "…?sslmode=require" -c 'select 1'` succeeds; `sslmode=disable` fails.
- [ ] `has_table_privilege('jobs_publisher','schema_migrations','INSERT')` is false; `has_table_privilege('jobs_reader','jobs','INSERT')` is false.
- [ ] `gitleaks detect --no-banner` on a full clone returns no findings; CI fails when a test secret is committed.

**Performance**

- [ ] `SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;` returns data after the extension is installed.
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` for list, count, and search queries is recorded in `docs/database/` and uses the expected index or a justified seq scan.
- [ ] `SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE relname = 'jobs';` is reviewed monthly; zero-scan indexes are explained, not deleted.

**Integrity**

- [ ] Two concurrent publishes against `devtest` serialize; `publish_meta.job_count` equals `count(*)` per profile afterward.
- [ ] `SELECT p.profile FROM publish_meta p LEFT JOIN jobs j USING (profile) GROUP BY 1 HAVING count(j.*) <> max(p.job_count);` returns zero rows.
- [ ] Guard tests pass: empty result, >50% collapse, empty keep-list, retention >50% block.
- [ ] `SELECT count(*) FROM jobs WHERE match_score NOT BETWEEN 0 AND 100;` returns zero after the CHECK is added.
- [ ] `SELECT DISTINCT application_status FROM jobs;` matches the allowed set exactly.

**Backups**

- [ ] A manual snapshot exists in the console and its creation time is recorded.
- [ ] The drill branch restored from a pre-publish timestamp shows 106 / 25 rows and working search.
- [ ] The most recent external dump restores into a scratch branch with matching row counts.
- [ ] Drill duration is recorded and compared to the stated RTO.

**Monitoring**

- [ ] A deliberately failed workflow produces a notification a human actually receives.
- [ ] A backdated `published_at` triggers the freshness alert.
- [ ] Thresholds for size, branches, and CU-hours fire when temporarily lowered.
- [ ] `neonctl branches list` shows ≤ 3 branches after cleanup, and CI preview runs leave none behind.

**Migrations**

- [ ] Applying all migrations to an empty branch reproduces `main`'s schema (information_schema diff is empty).
- [ ] A modified historical migration fails the checksum check in CI.
- [ ] The migration test job fails on a deliberately broken migration.
- [ ] `schema_migrations` still has no write grant for application roles after the checksum migration.

---

## H. Final recommendations

1. **Close the role question first.** Everything else in the security pillar is secondary to knowing whether the dashboard can write. It is a five-minute check with a large payoff.
2. **Treat recovery as a product feature, not an ops chore.** One snapshot plus a weekly dump plus one rehearsed drill moves this pillar from Poor to adequate, entirely within Free tier.
3. **Make the database observable from outside.** Free tier will not give you metrics or logs beyond a day, so persist a one-line publish summary and alert on staleness and capacity from your own workflows.
4. **Automate migrations before the schema gets more complex.** The current four migrations are simple enough that a minimal runner and a checksum column can be added safely; the same is not true after a rename-and-rewrite migration goes wrong.
5. **Do not over-engineer the schema.** At 131 rows, the zero-scan indexes, the 32 dead tuples, and the seq-scan preference are all correct behavior. The right response is a baseline and a revisit trigger, not immediate tuning.
6. **Keep the guards.** The publish transaction, the collapse guard, the profile-scoped deletes, and the retention threshold are the best-engineered parts of this system. Add regression tests so they survive future refactors.

**Accepted risks (documented, not defects):** no RLS given single-tenant-per-persona design; no IP allowlisting on Free; no compute-level SSL because TLS terminates at the proxy; no foreign key between `publish_meta` and `jobs` because the publish flow deletes and reinserts.

---

## I. Limitations and unverified items

| Item | Why it is unverified | How to close it |
|---|---|---|
| Dashboard's actual database role | Requires decrypting a Vercel secret; not permitted in this audit | Inspect the variable in the Vercel UI (username only, never the value) or add a temporary `current_user` diagnostic |
| TLS enforcement on real client connections | Client connection strings were not read | Connect with `sslmode=require` and `sslmode=disable` and compare |
| Whether a restore has ever succeeded | No drill record exists | Execute BAK-02 |
| Query-level latency and call counts | `pg_stat_statements` not installed | PERF-02 |
| Whether `main` matches migrations byte-for-byte | Only a live metadata spot-check was performed | MIG-02 drift job |
| Behavior under genuinely concurrent publishes | Not exercised (would write data) | INT-01 test on `devtest` |
| Actual alert delivery to a human | Notification preferences are outside the repository | MON-04 |
| Long-term planner behavior | Data volume is too small to be representative | PERF-01 revisit at > 50 k rows |
| Neon MCP connection identity | Audit tooling may itself connect as `neondb_owner`, confounding the `pg_stat_activity` observation | SEC-01 diagnostic from the app runtime, not from audit tooling |

**Audit integrity note:** No `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, or `CREATE` was executed. No application code, schema, role, or configuration was modified. No secret value, connection string, password, or real user data appears in this report.
