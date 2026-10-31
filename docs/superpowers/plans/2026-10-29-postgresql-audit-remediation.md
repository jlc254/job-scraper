# PostgreSQL Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the High and Medium findings in `docs/database/postgresql-audit-report.md` without taking the dashboard or the twice-daily publish offline.

**Architecture:** Five waves ordered by risk reduction per hour. Wave 0 is pure verification and operations (no code, no schema). Wave 1 adds repository guardrails. Wave 2 changes the publish path (advisory lock, post-publish state assertion, health checks) with tests first. Wave 3 builds the migration runner and a real database CI job, because every later schema change depends on it. Wave 4 applies the schema hardening through that runner. Wave 5 records the decisions and closes the loop. Waves 3–5 are independent of Wave 2 and can run in parallel worktrees; tasks within a wave share files and must run in order.

**Tech Stack:** PostgreSQL 18 (Neon Free), Python 3.12, psycopg 3, pytest, GitHub Actions, Next.js 15 dashboard (read-only consumer), `pg_dump`/`pg_restore` 18.

**Spec:** `docs/database/postgresql-audit-report.md`

## Global Constraints

- Python 3.12; `ruff` line length 100; `mypy src` must pass; tests run from the repo root with `pythonpath = ["src"]`.
- Every GitHub Action is pinned to a full commit SHA. After editing a workflow run `python scripts/pin_actions.py` and commit the pinned refs.
- Workflows declare `permissions: contents: read` unless a task explicitly needs more.
- Never print, echo, or pass a DSN/password on a command line. Read it from an environment variable; pass secrets to `curl` through `--config -` as `daily.yml` already does.
- DDL and `pg_dump` use the **direct** (non-pooled) connection string. The pooled host contains `-pooler` and must be rejected.
- Neon Free limits: 1 GB storage, 100 CU-hours/month, 10 branches, 1 manual snapshot, 6-hour PITR. A restore branch must be deleted after the drill.
- No schema write happens outside `migrations/*.sql` applied by `scripts/migrate.py`.
- `python main.py publish` keeps its exit codes: 0 ok, 2 config, 3 Sheet, 6 Neon/guard.
- Every database statement added to the app path must be parameterized; identifiers composed with `psycopg.sql` only.

## Review Focus

1. **Two publishes for the same profile at once** — the second must wait, then succeed, leaving exactly one generation of rows (`Task 9`).
2. **Two publishes for different profiles at once** — they must not block each other; a global lock would serialize Juliet behind Jumalaw98 (`Task 9`).
3. **Migration runner against the existing database**, where `001`–`004` are recorded with no checksums — it must backfill, not fail (`Task 12`).
4. **`pg_dump` given the pooled DSN** — it must refuse loudly rather than write a partial or hanging dump (`Task 8`).
5. **Restore drill pointed at a branch** — it must use read-only credentials and leave the branch's row counts unchanged, proving the drill itself did not mutate evidence (`Task 4`).

---

## Wave 0 — Verify and de-risk (≈4 hours, no code, no schema)

### Task 1: Confirm which role the dashboard authenticates as

**Files:**
- Create: `docs/database/role-verification.md`

**Interfaces:**
- Produces: a recorded yes/no that `DATABASE_URL` (production) uses `jobs_reader`; consumed by Task 2 and by the final report update in Task 19.

- [ ] **Step 1: Read the username, never the value**

In Vercel → Project → Settings → Environment Variables, open `DATABASE_URL` for **Production** and note only the username portion (text before the first `:`). Do not copy the value into a terminal, file, or chat.

- [ ] **Step 2: Corroborate against live sessions**

With the dashboard open and recently loaded, run as owner:

```sql
SELECT usename, count(*) FROM pg_stat_activity
WHERE backend_type = 'client backend' GROUP BY 1 ORDER BY 2 DESC;
```

Expected: `jobs_reader` present. `neondb_owner` may also appear (Neon MCP, platform tooling) — that alone is not proof.

- [ ] **Step 3: Write the record**

Create `docs/database/role-verification.md` with: date, Vercel variable name, username observed, `pg_stat_activity` output summary, and one line: `Result: PASS` or `Result: FAIL — dashboard uses <role>`.

- [ ] **Step 4: Commit**

```bash
git add docs/database/role-verification.md
git commit -m "docs(db): record which role the dashboard connects as"
```

### Task 2: Switch the dashboard to `jobs_reader` (only if Task 1 failed)

**Files:**
- Modify: `docs/database/role-verification.md`

**Interfaces:**
- Consumes: Task 1's result. Skip entirely when Task 1 passed.

- [ ] **Step 1: Keep the current value recoverable**

In Vercel, copy the current production `DATABASE_URL` into the project's encrypted notes (or leave the variable version history intact) so rollback is one click. Do not write it to disk.

- [ ] **Step 2: Build a `jobs_reader` connection string**

In the Neon console → Connect, choose role `jobs_reader`, database `neondb`, **pooled** connection for the serverless dashboard. Set it as production `DATABASE_URL` (and preview `DATABASE_URL` if it also points at `main`). If the password is unknown, reset it in the console; do not set it via a shell command that lands in history.

- [ ] **Step 3: Verify**

Redeploy, load the dashboard, then re-run the `pg_stat_activity` query. Expected: `jobs_reader` sessions. Check list, search, filters, and a job detail page.

- [ ] **Step 4: Roll back if anything breaks**

Restore the previous variable value and redeploy. Record the outcome in `role-verification.md`.

- [ ] **Step 5: Commit**

```bash
git add docs/database/role-verification.md
git commit -m "docs(db): switch dashboard to the read-only role"
```

### Task 3: Take the one permitted manual snapshot

**Files:**
- Create: `docs/database/recovery-baseline.md`

- [ ] **Step 1: Create the snapshot**

Neon console → Project → Backups/Snapshots → Create snapshot, name `baseline-2026-10-29`. Free allows one; if an older snapshot exists, confirm it is not needed before replacing it.

- [ ] **Step 2: Record it**

In `recovery-baseline.md` write: snapshot name, creation timestamp, branch it captures (`main`), current PITR window (6 h), current branch count, and the open question "RPO/RTO to be set in Task 18".

- [ ] **Step 3: Commit**

```bash
git add docs/database/recovery-baseline.md
git commit -m "docs(db): record baseline snapshot and recovery facts"
```

### Task 4: Run the first restore drill

**Files:**
- Create: `docs/database/restore-drill.md`

**Interfaces:**
- Produces: a measured restore duration, used as the RTO input in Task 18.

- [ ] **Step 1: Create a drill branch inside the PITR window**

Do not hardcode a timestamp: Neon Free keeps only a 6-hour window, so any literal written into this plan is stale before the first run. Compute it at run time:

```bash
TS=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
neonctl branches create --name "drill/$(date -u +%Y%m%d)" --parent main --timestamp "$TS"
```

The timestamp must fall inside the 6-hour window. A restore point one hour back may or may not include the most recent publish — that is expected, and it is why Step 2 checks self-consistency rather than today's counts.

- [ ] **Step 2: Verify the restored data read-only**

Connect with a read-only role (the branch clones roles). Run:

```sql
SELECT j.profile, count(*) AS live, m.job_count AS recorded
FROM jobs j JOIN publish_meta m USING (profile)
GROUP BY j.profile, m.job_count ORDER BY 1;
SELECT max(published_at) FROM publish_meta;
```

Expected: for every profile, `live = recorded`. The branch restores a *coherent* moment, which is not necessarily today's numbers — do not compare against a literal such as 106/25, because the counts move with every publish (they were 112/26 at 2026-10-29T18:57Z). `max(published_at)` must be at or before the restore point. Record the numbers.

- [ ] **Step 3: Prove the drill did not mutate the branch**

Re-run the same two queries. Expected: identical output. If counts changed, the drill used a write-capable role — stop and fix the drill, not the branch.

- [ ] **Step 4: Write the runbook**

`docs/database/restore-drill.md` must contain: exact commands used, start/end timestamps, total duration, row counts before/after, and the teardown command. Add a "repeat quarterly" line with the next due date.

- [ ] **Step 5: Delete the drill branch**

`neonctl branches delete "drill/$(date -u +%Y%m%d)"` (the name from Step 1). Confirm `neonctl branches list` no longer shows it, and that the branch count is below the cap.

- [ ] **Step 6: Commit**

```bash
git add docs/database/restore-drill.md
git commit -m "docs(db): record first successful restore drill"
```

### Task 5: Delete the stale branches

**Files:**
- Modify: `docs/database/recovery-baseline.md`

- [ ] **Step 1: Inventory**

`neonctl branches list` — record name, id, `created_at`, `updated_at` for every branch.

- [ ] **Step 2: Confirm nothing points at them**

For each `preview/dependabot/*` branch, confirm no open PR/preview deployment references it. `vercel-dev` is archived; confirm no Vercel project still targets it.

- [ ] **Step 3: Delete**

Delete the four `preview/dependabot/*` branches and `vercel-dev`. Re-list. Expected: `main`, `devtest`, and any live preview only — at most 3.

- [ ] **Step 4: Commit**

```bash
git add docs/database/recovery-baseline.md
git commit -m "docs(db): record branch cleanup and current inventory"
```

---

## Wave 1 — Repository guardrails (≈4 hours)

### Task 6: Enforce secret scanning in CI

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/08-security.md`

**Interfaces:**
- Produces: a `secrets` CI job that blocks merges containing credentials.

- [ ] **Step 1: Add the job**

Append to `ci.yml`:

```yaml
  secrets:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - name: Check out
        uses: actions/checkout@f548e57e544e1ff5a4c46bf1e1b8685f8e4a348a # v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - name: Scan for secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: Pin the new action**

Run `python scripts/pin_actions.py`, confirm `gitleaks/gitleaks-action` is now a 40-character SHA, and commit the rewritten workflow.

- [ ] **Step 3: Prove it fails**

On a scratch branch add a file containing a generated fake AWS key — `AKIA` followed by 16 random uppercase letters. Do not use AWS's documented `AKIAIOSFODNN7EXAMPLE`; it is allowlisted by some rulesets and would make a passing scan look like a working gate. Push and open a PR. Expected: the `secrets` job fails. Delete the branch.

- [ ] **Step 4: Document local use**

In `docs/08-security.md`, replace any "gitleaks is configured" claim with the exact commands:

```bash
pip install pre-commit && pre-commit install
pre-commit run gitleaks --all-files
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml docs/08-security.md
git commit -m "ci: block commits containing secrets with gitleaks"
```

### Task 7: Sweep orphaned preview branches weekly

**Files:**
- Create: `scripts/neon_branch_sweep.sh`
- Create: `tests/test_neon_branch_sweep.py`
- Modify: `.github/workflows/cleanup-neon-preview.yml`

**Interfaces:**
- Consumes: the Neon API helpers and pagination pattern in `scripts/neon_preview_branch.sh`.
- Produces: `scripts/neon_branch_sweep.sh` with env contract `NEON_API_KEY`, `NEON_PROJECT_ID`, `MAX_AGE_DAYS` (default 7), `DRY_RUN` (default 0); prints `deleted=<n> kept=<n>`; exit 0 on success, 1 on any API/parse error.

- [ ] **Step 1: Write the failing test**

`tests/test_neon_branch_sweep.py`, following the stub-server style already used in `tests/test_neon_preview_branch.py`:

```python
def test_deletes_only_old_previews(api_stub):
    api_stub.branches = [
        {"id": "b1", "name": "preview/old", "default": False, "updated_at": OLD},
        {"id": "b2", "name": "preview/new", "default": False, "updated_at": NEW},
        {"id": "b3", "name": "main", "default": True, "updated_at": OLD},
        {"id": "b4", "name": "devtest", "default": False, "updated_at": OLD},
    ]
    result = run_script(api_stub.url)
    assert result.returncode == 0
    assert api_stub.deleted == ["b1"]
    assert "deleted=1 kept=3" in result.stdout


def test_refuses_when_default_branch_is_listed_as_preview(api_stub):
    api_stub.branches = [{"id": "b1", "name": "preview/x", "default": True, "updated_at": OLD}]
    result = run_script(api_stub.url)
    assert result.returncode == 1
    assert api_stub.deleted == []
```

- [ ] **Step 2: Run it and confirm it fails**

`pytest tests/test_neon_branch_sweep.py -q` → FAIL (script missing).

- [ ] **Step 3: Implement the script**

Copy the `find_branch` pagination and `--config -` credential handling from `scripts/neon_preview_branch.sh`. Delete only when **all** hold: name starts with `preview/`, `default` is false, `updated_at` is older than `now - MAX_AGE_DAYS`. `DRY_RUN=1` prints what would be deleted and exits 0. Delete via `DELETE /projects/{id}/branches/{branch_id}`; treat 404 as success.

- [ ] **Step 4: Run the tests**

`pytest tests/test_neon_branch_sweep.py -q` → PASS.

- [ ] **Step 5: Schedule it**

In `cleanup-neon-preview.yml` add a `schedule: cron: "23 4 * * 1"` trigger and a `sweep` job (same `NEON_API_KEY`/`NEON_PROJECT_ID` secrets, `permissions: contents: read`). Keep the existing per-PR cleanup job intact.

- [ ] **Step 6: Commit**

```bash
git add scripts/neon_branch_sweep.sh tests/test_neon_branch_sweep.py .github/workflows/cleanup-neon-preview.yml
git commit -m "ci: sweep preview branches older than seven days"
```

### Task 8: Weekly logical backup outside Neon

**Files:**
- Create: `scripts/db_dump.sh`
- Create: `.github/workflows/db-backup.yml`
- Modify: `docs/database/recovery-baseline.md`

**Interfaces:**
- Consumes: `NEON_DATABASE_URL_PUBLISHER` (direct, non-pooled).
- Produces: `backup-YYYYMMDD.dump` (custom format), uploaded as an artifact with 56-day retention; exit 2 for a pooled or missing DSN, exit 1 for a dump that fails verification.

- [ ] **Step 1: Write the guard and the dump**

`scripts/db_dump.sh`:

```bash
# refuse pooled hosts: pgbouncer breaks pg_dump's session assumptions
case "${NEON_DATABASE_URL_PUBLISHER:-}" in
  *-pooler.*) echo "refusing pooled DSN for pg_dump" >&2; exit 2 ;;
  "") echo "NEON_DATABASE_URL_PUBLISHER is required" >&2; exit 2 ;;
esac
```

Then run the dump inside the matching client image so the version is not the runner's:

```bash
docker run --rm -e PGURL -v "$PWD:/out" postgres:18 \
  sh -c 'pg_dump "$PGURL" --format=custom --no-owner --no-privileges -f /out/backup.dump'
```

- [ ] **Step 2: Verify the artifact**

Fail unless `backup.dump` is at least 10 KB and `pg_restore --list backup.dump` succeeds (run it in the same container image).

- [ ] **Step 3: Test the refusal path**

`NEON_DATABASE_URL_PUBLISHER='postgresql://u:p@ep-x-pooler.us-east-2.aws.neon.tech/db' bash scripts/db_dump.sh` → exit 2 and a one-line error, no dump file.

- [ ] **Step 4: Add the workflow**

`.github/workflows/db-backup.yml`: `schedule: cron: "17 4 * * 0"`, `workflow_dispatch`, `permissions: contents: read`, `concurrency` group `db-backup`, step env `NEON_DATABASE_URL_PUBLISHER`, then `actions/upload-artifact` with `retention-days: 56`.

- [ ] **Step 5: Run it once by hand**

Trigger `workflow_dispatch`. Download the artifact. Create a **fresh** branch for this check (`drill/backup-verify`, parent `main`) — Task 4 already deleted its own branch. Restore the dump into it with `pg_restore --no-owner --no-privileges`, then run the per-profile self-consistency query from Task 4 Step 2: expect `live = recorded` for every profile, not a fixed count. Delete the branch.

- [ ] **Step 6: Commit**

```bash
git add scripts/db_dump.sh .github/workflows/db-backup.yml docs/database/recovery-baseline.md
git commit -m "feat(db): weekly verified logical backup"
```

---

## Wave 2 — Publish path hardening (≈1.5 days, TDD)

### Task 9: Serialize publishes per profile with an advisory lock

**Files:**
- Modify: `src/jobscraper/storage/neon.py` (`replace_jobs`)
- Test: `tests/test_neon_integration.py`

**Interfaces:**
- Consumes: `NeonPublisher.replace_jobs(columns, rows, *, profile, run_start, sheet_rows, batch_size=200) -> int` (unchanged signature).
- Produces: the same signature; guaranteed serialization per profile. The lock key is `hashtext(profile)` and is transaction-scoped.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_neon_integration.py` (skipped without `TEST_DATABASE_URL`):

```python
def test_concurrent_publishes_same_profile_serialize():
    # A holds the profile lock for ~0.6s inside replace_jobs' transaction;
    # B must wait for A rather than interleave its stale sweep.
    ...  # thread A: open publisher, begin transaction, SELECT pg_advisory_xact_lock(hashtext('support'))
    ...  # thread B: publisher.replace_jobs(...) and time it
    assert elapsed_b >= 0.3
    assert count("support") == len(plan_b.rows)


def test_publishes_for_different_profiles_do_not_block():
    ...  # A holds the lock for 'support'
    assert elapsed_other < 0.2
```

- [ ] **Step 2: Run them and confirm they fail**

`TEST_DATABASE_URL=... pytest tests/test_neon_integration.py -k concurrent -q` → FAIL (B returns immediately).

- [ ] **Step 3: Add the lock**

In `replace_jobs`, as the first statement inside `with conn.transaction():`, before the upsert loop:

```python
cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (profile,))
```

Add a docstring line: "Two publishes for the same profile serialize; different profiles do not block. The lock releases on commit or rollback."

- [ ] **Step 4: Run the tests**

Both pass. Then run the full file to confirm idempotency and stale-delete tests still pass.

- [ ] **Step 5: Commit**

```bash
git add src/jobscraper/storage/neon.py tests/test_neon_integration.py
git commit -m "fix(publish): serialize concurrent publishes per profile"
```

### Task 10: Assert post-publish consistency and emit a machine-readable summary

**Files:**
- Modify: `src/jobscraper/storage/neon.py`
- Modify: `src/jobscraper/publish_cli.py`
- Test: `tests/test_publish_profiles.py`
- Test: `tests/test_neon_integration.py`

**Interfaces:**
- Produces:

```python
class PublishState(NamedTuple):
    live: int
    recorded: int | None

def publish_state(self, profile: str) -> PublishState
```

- Consumes: `publish_state` inside `run_publish` after each `replace_jobs`.
- Log contract: one line per profile, `summary: {"event":"publish","profile":...,"live":N,"recorded":N,"ok":true}`, JSON with sorted keys.

- [ ] **Step 1: Write the failing unit test**

In `tests/test_publish_profiles.py`, extend the fake publisher with `publish_state` returning `(3, 2)` for one profile and assert:

```python
assert code == EXIT_NEON
assert '"ok": false' in output
assert '"recorded": 2' in output
```

- [ ] **Step 2: Run it and confirm it fails**

`pytest tests/test_publish_profiles.py -q` → FAIL (`publish_state` missing).

- [ ] **Step 3: Implement `publish_state`**

One round trip:

```sql
SELECT (SELECT count(*) FROM jobs WHERE profile = %s),
       (SELECT job_count FROM publish_meta WHERE profile = %s)
```

Return `PublishState(live, recorded)`. Wrap `psycopg.Error` in `NeonError` using `_safe`, like the other methods.

- [ ] **Step 4: Wire it into `run_publish`**

After the successful `replace_jobs`, call `publish_state`, print the summary line with `json.dumps(..., sort_keys=True)`, and set `worst = max(worst, EXIT_NEON)` when `state.recorded != state.live` or `state.recorded is None`, printing a one-line reason that names the profile and both counts.

- [ ] **Step 5: Add the integration assertion**

`tests/test_neon_integration.py`: after a successful `replace_jobs`, `publish_state("support").live == publish_state("support").recorded == len(plan.rows)`.

- [ ] **Step 6: Run the tests**

`pytest tests/test_publish_profiles.py tests/test_publish.py -q` and the integration file both pass.

- [ ] **Step 7: Commit**

```bash
git add src/jobscraper/storage/neon.py src/jobscraper/publish_cli.py tests/test_publish_profiles.py tests/test_neon_integration.py
git commit -m "feat(publish): assert live rows match publish_meta and log a summary"
```

### Task 11: Freshness, size, and branch-cap health checks

**Files:**
- Create: `scripts/db_health.py`
- Create: `tests/test_db_health.py`
- Modify: `.github/workflows/daily.yml`

**Interfaces:**
- Produces:

```python
def check(now: datetime, *, max_age_hours: int, storage_bytes: int,
          max_storage_mb: int, branch_count: int | None,
          max_branches: int,
          ages: Mapping[str, timedelta]) -> list[str]
def main(argv: list[str] | None = None) -> int
```

- `ages` is injected rather than read inside `check`, so the function stays pure and testable without a database; `main` supplies it from the query in Step 3.

- Env: `NEON_DATABASE_URL_PUBLISHER` (required), `NEON_API_KEY`/`NEON_PROJECT_ID` (optional; branch check skipped with a notice when absent).
- Output: `{"event":"db_health","problems":[...]}`; exit 1 when the list is non-empty.

- [ ] **Step 1: Write the failing tests**

`tests/test_db_health.py` — pure function, no database:

```python
def test_stale_profile_is_reported():
    problems = check(NOW, max_age_hours=26, storage_bytes=1, max_storage_mb=700,
                     branch_count=3, max_branches=8,
                     ages={"juliet": timedelta(hours=30), "jumalaw98": timedelta(hours=2)})
    assert any("juliet" in p and "stale" in p for p in problems)


def test_fresh_small_and_under_cap_is_clean():
    assert check(...) == []
```

- [ ] **Step 2: Run and confirm failure**

`pytest tests/test_db_health.py -q` → FAIL (module missing).

- [ ] **Step 3: Implement**

`check` takes a mapping of profile → age rather than opening a connection, so it stays pure; `main` reads the ages with

```sql
SELECT profile, now() - published_at FROM publish_meta
```

and reads `pg_database_size(current_database())`. Branch count comes from `GET /projects/{id}/branches` (reuse the pagination approach). Every threshold flag is a CLI argument with the defaults above.

- [ ] **Step 4: Run the tests**

`pytest tests/test_db_health.py -q` → PASS.

- [ ] **Step 5: Wire into `daily.yml`**

Add after the Publish step:

```yaml
      - name: Database health
        if: ${{ always() && steps.install.outcome == 'success' }}
        timeout-minutes: 3
        env:
          NEON_DATABASE_URL_PUBLISHER: ${{ secrets.NEON_DATABASE_URL_PUBLISHER }}
          NEON_API_KEY: ${{ secrets.NEON_API_KEY }}
          NEON_PROJECT_ID: ${{ secrets.NEON_PROJECT_ID }}
        run: python scripts/db_health.py --max-age-hours 26 --max-branches 8 --max-storage-mb 700
```

- [ ] **Step 6: Prove it alerts**

On `devtest`, backdate one `publish_meta.published_at` by 40 hours, run the script, confirm exit 1 and the profile named. Restore the timestamp.

- [ ] **Step 7: Commit**

```bash
git add scripts/db_health.py tests/test_db_health.py .github/workflows/daily.yml
git commit -m "feat(ops): alert on stale publishes, storage, and branch cap"
```

---

## Wave 3 — Migration safety (≈1.5 days)

### Task 12: A migration runner that records checksums

**Files:**
- Create: `scripts/migrate.py`
- Create: `tests/test_migrate.py`
- Test: `tests/test_neon_integration.py` (shared fixture reuse)

**Interfaces:**
- Produces:

```python
def load(folder: Path) -> list[Migration]          # sorted by filename; Migration(version, path, checksum)
def pending(applied: dict[str, str | None], migrations: list[Migration]) -> list[Migration]
def main(argv: list[str] | None = None) -> int     # 0 ok, 2 config, 3 checksum mismatch, 4 SQL failure
```

- Env: `NEON_DATABASE_URL` (owner, direct).
- Flags: `--dry-run`, `--to VERSION`, `--accept-checksums`.
- Guarantee: each file runs in its own transaction together with its `schema_migrations` row.

- [ ] **Step 1: Write the failing unit tests**

`tests/test_migrate.py`:

```python
def test_pending_ignores_applied_versions(tmp_path):
    ...  # two files, one applied -> only the other is pending

def test_checksum_mismatch_is_reported(tmp_path):
    ...  # applied checksum differs -> pending() raises ChecksumMismatch

def test_versions_sort_numerically_not_lexically(tmp_path):
    ...  # 009 before 010
```

- [ ] **Step 2: Run and confirm failure**

`pytest tests/test_migrate.py -q` → FAIL.

- [ ] **Step 3: Implement the runner**

Bootstrap first, as owner:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum text;
```

For versions already recorded with `checksum IS NULL`, compute the file's SHA-256 and backfill (this is the one-time adoption path for `001`–`004`). A recorded checksum that differs is a hard error unless `--accept-checksums` is passed; with the flag, update the row and print each changed version.

- [ ] **Step 4: Write the integration test**

Gated on `TEST_DATABASE_URL`, against a dropped-and-recreated schema: applying from empty creates `jobs`; a second run is a no-op; editing a migration after apply exits 3; `--accept-checksums` then exits 0.

- [ ] **Step 5: Run everything**

`pytest tests/test_migrate.py tests/test_neon_integration.py -q` → PASS.

- [ ] **Step 6: Adopt it on `devtest`**

Point `NEON_DATABASE_URL` at `devtest`, run `python scripts/migrate.py --dry-run`, then for real. Expected: `001`–`004` backfilled, nothing applied. Then run it against `main` and confirm the same before any new migration exists.

- [ ] **Step 7: Commit**

```bash
git add scripts/migrate.py tests/test_migrate.py
git commit -m "feat(migrations): add checksum-recording runner"
```

### Task 13: Run migrations and integration tests in CI

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `docker-compose.yml`

**Interfaces:**
- Produces: a `db` job that proves migrations apply from zero on every push.

- [ ] **Step 1: Match the production major version**

`docker-compose.yml`: change `image: postgres:17` to `postgres:18` and update the comment to say it mirrors Neon. Note in the README that an existing volume must be recreated (`docker compose down -v`).

- [ ] **Step 2: Add the job**

```yaml
  db:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: jobs_dashboard
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres -d jobs_dashboard"
          --health-interval 5s --health-timeout 3s --health-retries 10
    env:
      TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/jobs_dashboard
      NEON_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/jobs_dashboard
    steps:
      - uses: actions/checkout@f548e57e544e1ff5a4c46bf1e1b8685f8e4a348a # v4
        with: { persist-credentials: false }
      - uses: ./.github/actions/setup-python-env
      # 002_roles.sql raises unless both roles already exist
      # (migrations/002_roles.sql:8-13). Create them first or the chain
      # aborts on the second file, every run.
      - name: Create application roles
        run: |
          psql "$TEST_DATABASE_URL" -v ON_ERROR_STOP=1 \
            -c "CREATE ROLE jobs_publisher LOGIN;" \
            -c "CREATE ROLE jobs_reader LOGIN;"
      - run: python scripts/migrate.py
      - run: pytest -q tests/test_migrate.py tests/test_neon_integration.py
```

`tests/test_db_health.py` is deliberately absent from that `pytest` call: it is created by Task 11 in Wave 2, and Wave 3 has to stay runnable on its own. Add it to the list only once Task 11 has landed.

- [ ] **Step 3: Prove the gate works**

Open a PR with a migration containing `SELECT 1/0;`. Expected: `db` job fails at `migrate.py`. Revert.

- [ ] **Step 4: Confirm the existing jobs still pass**

`pytest -q` locally must stay green; the integration file skips when `TEST_DATABASE_URL` is absent, so no behaviour change outside CI.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml docker-compose.yml
git commit -m "ci: apply migrations and run database tests on postgres 18"
```

### Task 14: Detect schema drift

**Files:**
- Create: `scripts/schema_dump.sh`
- Create: `docs/database/schema.sql`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: a normalized, committed schema snapshot; CI fails when a freshly migrated database differs.

- [ ] **Step 1: Write the dump/normalize script**

Run the dump inside the `postgres:18` image. The runner's own `pg_dump` is version 16 on `ubuntu-24.04` and aborts with "server version mismatch" against a PG 18 server, and PG 18 dumps contain a per-run random token that makes any naive diff non-empty.

```bash
#!/usr/bin/env bash
set -euo pipefail
DSN="${1:?usage: schema_dump.sh <direct-dsn>}"
case "$DSN" in
  *-pooler.*) echo "refusing pooled DSN" >&2; exit 2 ;;
esac

docker run --rm -e PGURL="$DSN" postgres:18 \
  sh -c 'pg_dump "$PGURL" --schema-only --no-owner --no-privileges' \
| grep -v -E '^(--|SET |SELECT pg_catalog\.set_config|\\restrict|\\unrestrict|$)'
```

Each stripped pattern has to go:

| Stripped | Why |
|---|---|
| `--` comment lines | the dump header embeds the server version and the dump timestamp |
| `SET ` / `SELECT pg_catalog.set_config` | embeds the database name and role |
| `\restrict` / `\unrestrict` | random token, different on every run |
| blank lines | noise from the blocks above |

Print to stdout so CI can diff.

- [ ] **Step 2: Generate the baseline**

Run `scripts/schema_dump.sh "$TEST_DATABASE_URL" > docs/database/schema.sql` against a database migrated from zero.

- [ ] **Step 3: Add the CI step**

In the `db` job, after the tests: `scripts/schema_dump.sh "$TEST_DATABASE_URL" | diff -u docs/database/schema.sql -`.

- [ ] **Step 4: Prove it fails on drift**

Change a column default in a migration, run the job, confirm a non-empty diff. Revert.

- [ ] **Step 5: Commit**

```bash
git add scripts/schema_dump.sh docs/database/schema.sql .github/workflows/ci.yml
git commit -m "ci: detect schema drift against the migration set"
```

---

## Wave 4 — Schema hardening through the runner (≈2 hours)

### Task 15: Enable `pg_stat_statements`

**Files:**
- Create: `migrations/005_pg_stat_statements.sql`

- [ ] **Step 1: Write the migration**

```sql
-- 005_pg_stat_statements.sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
INSERT INTO schema_migrations (version) VALUES ('005_pg_stat_statements') ON CONFLICT DO NOTHING;
```

(The runner inserts the row itself; the explicit insert keeps the file runnable by hand, matching `001`.)

- [ ] **Step 2: Apply on `devtest`, then `main`**

`python scripts/migrate.py --to 005_pg_stat_statements`, then without `--to`.

- [ ] **Step 3: Verify**

```sql
SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements';
SELECT count(*) FROM pg_stat_statements;
```

Expected: one row, then a non-zero count only after some queries run. If creation fails for lack of privilege, confirm the runner connected as `neondb_owner` and retry; do not grant superuser to an application role.

- [ ] **Step 4: Commit**

```bash
git add migrations/005_pg_stat_statements.sql
git commit -m "feat(db): enable pg_stat_statements for query visibility"
```

### Task 16: Set role-level timeouts

**Files:**
- Create: `migrations/006_role_timeouts.sql`

**Interfaces:**
- Produces: `jobs_reader` statement 15 s (provisional — confirm against `pg_stat_statements` in Step 2) / lock 3 s / idle-in-transaction 60 s; `jobs_publisher` statement 120 s / lock 10 s.

- [ ] **Step 1: Write the migration**

```sql
ALTER ROLE jobs_reader SET statement_timeout = '15s';
ALTER ROLE jobs_reader SET lock_timeout = '3s';
ALTER ROLE jobs_reader SET idle_in_transaction_session_timeout = '60s';
ALTER ROLE jobs_publisher SET statement_timeout = '120s';
ALTER ROLE jobs_publisher SET lock_timeout = '10s';
INSERT INTO schema_migrations (version) VALUES ('006_role_timeouts') ON CONFLICT DO NOTHING;
```

- [ ] **Step 2: Measure before committing to either timeout**

Two measurements, in this order. Task 15 runs first, so `pg_stat_statements` is populated by now — use it instead of guessing.

**Reader ceiling.** The dashboard's real queries must fit comfortably under 15 s, and the ceiling must also be low enough to actually bound a runaway query. Measure the worst case rather than assuming:

```sql
SELECT calls,
       round(mean_exec_time::numeric, 1)  AS mean_ms,
       round(max_exec_time::numeric, 1)   AS max_ms,
       round(total_exec_time::numeric, 1) AS total_ms,
       left(query, 80) AS query
FROM pg_stat_statements
WHERE query ILIKE '%jobs%'
ORDER BY max_exec_time DESC
LIMIT 10;
```

`pg_stat_statements` is instance-wide, not per-role, so treat this as the upper bound for what the dashboard may issue. Set `statement_timeout` above the slowest *normal* dashboard query with margin — if `max_exec_time` is already near 15 s for a routine query, raise the ceiling instead of shipping a timeout that breaks the dashboard. If `pg_stat_statements` is empty (compute restarted since Task 15, or too little traffic), load the dashboard once and re-run before deciding.

**Publisher ceiling.** Time one real publish (`python main.py publish --only <profile>` on `devtest`). The 120 s ceiling must exceed it with margin; raise to 300 s if the publish takes over 60 s.

Record both numbers in `docs/database/restore-drill.md`'s sibling note, `docs/database/timeout-baseline.md`, with the query and the measured value that justified each ceiling.

- [ ] **Step 3: Apply and verify**

Run the runner. Then:

```sql
SELECT rolname, rolconfig FROM pg_roles WHERE rolname LIKE 'jobs_%';
```

Expected: both roles list their settings. Because these apply at login, pooled connections keep the old values until recycled — restart the compute or wait for scale-to-zero.

- [ ] **Step 4: Verify enforcement**

Connect as `jobs_reader` and run `SELECT pg_sleep(20);` → must fail at 15 s. Connect as `jobs_publisher`, run `SELECT pg_sleep(200);` → must fail at 120 s.

- [ ] **Step 5: Commit**

```bash
git add migrations/006_role_timeouts.sql
git commit -m "feat(db): bound statement and lock time per role"
```

### Task 17: Constrain `match_score` and `application_status`

**Files:**
- Create: `migrations/007_integrity_constraints.sql`
- Test: `tests/test_neon_integration.py`

- [ ] **Step 1: Verify the observed values first**

```sql
SELECT DISTINCT application_status FROM jobs ORDER BY 1;
SELECT count(*) FROM jobs WHERE match_score NOT BETWEEN 0 AND 100;
```

Expected: statuses are a subset of `New, Applied, Interview, Offer, Rejected, Ignored`, and zero out-of-range scores. If a status outside that set appears, add it to the list before writing the constraint.

- [ ] **Step 2: Write the migration**

```sql
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_match_score_range;
ALTER TABLE jobs ADD CONSTRAINT jobs_match_score_range
  CHECK (match_score IS NULL OR (match_score >= 0 AND match_score <= 100));

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_application_status_allowed;
ALTER TABLE jobs ADD CONSTRAINT jobs_application_status_allowed
  CHECK (application_status IN ('New','Applied','Interview','Offer','Rejected','Ignored'));

INSERT INTO schema_migrations (version) VALUES ('007_integrity_constraints') ON CONFLICT DO NOTHING;
```

- [ ] **Step 3: Write the failing tests**

In `tests/test_neon_integration.py`:

```python
def test_score_above_100_is_rejected():
    ...  # INSERT with match_score=101 raises psycopg.errors.CheckViolation

def test_unknown_status_is_rejected():
    ...  # INSERT with application_status='new' raises CheckViolation
```

Also assert the guard still runs first: `build_rows([])` → `check_guard(0, previous, ...)` raises `GuardError` before any insert, where `previous` is read from `publish_meta` at test time rather than hardcoded — the live counts move with every publish.

- [ ] **Step 4: Apply on `devtest`, run the tests, then apply on `main`**

The table has 131 rows, so the `ACCESS EXCLUSIVE` lock is momentary; still apply outside the 03:07/13:07 publish windows.

- [ ] **Step 5: Commit**

```bash
git add migrations/007_integrity_constraints.sql tests/test_neon_integration.py
git commit -m "feat(db): constrain score range and application status"
```

---

## Wave 5 — Decisions and closure (≈3 hours)

### Task 18: Record RPO/RTO, rotation, and the RLS decision

**Files:**
- Create: `docs/database/recovery.md`
- Create: `docs/database/security-decisions.md`
- Modify: `docs/database/postgresql-audit-report.md` (statuses only)

- [ ] **Step 1: Write recovery targets**

`recovery.md`: RPO 24 h (weekly dump) with a 6 h best-effort PITR window; RTO = the duration measured in Task 4 plus redeploy time. State the accepted loss per profile and the exact restore commands (branch + dump paths).

- [ ] **Step 2: Write the rotation runbook**

Four steps: reset the role password in the Neon console → update the GitHub secret → update the Vercel variable → verify one publish and one dashboard load → revoke the old credential. Note the order matters: publisher first, reader second, so a failure never leaves both surfaces broken.

- [ ] **Step 3: Write the security decision record**

`security-decisions.md`: RLS not enabled (single-tenant-per-persona, all queries profile-scoped, revisit on multi-tenant), network allowlisting unavailable on Free (compensate with secret hygiene and rotation), `ssl=off` on compute is correct (TLS at the proxy), no FK between `publish_meta` and `jobs` (replace-style publish), database role split.

- [ ] **Step 4: Update the audit report statuses only**

Change the status line of each closed finding; do not rewrite findings. Leave anything unverified marked `Needs verification`.

- [ ] **Step 5: Commit**

```bash
git add docs/database/recovery.md docs/database/security-decisions.md docs/database/postgresql-audit-report.md
git commit -m "docs(db): record recovery targets, rotation runbook, and security decisions"
```

### Task 19: Run the verification checklist and close the loop

**Files:**
- Create: `docs/database/verification-log.md`

- [ ] **Step 1: Execute every checklist item**

Work through section G of the audit report. Record each item as `PASS`, `FAIL`, or `BLOCKED (reason)` with the date and the command used — never the output containing data.

- [ ] **Step 2: Record the residual risks**

List what remains accepted: no IP allowlisting, no RLS, 1-day metric retention, 6-hour PITR, in-memory extension stats reset on scale-to-zero.

- [ ] **Step 3: Confirm the pipeline is green**

One scheduled run after all changes: `daily.yml` completes, the publish summary line shows `"ok": true`, and `db_health` reports no problems.

- [ ] **Step 4: Commit**

```bash
git add docs/database/verification-log.md
git commit -m "docs(db): record post-remediation verification results"
```

---

## Sequencing and independence

```
Wave 0 (ops)  ──► Wave 1 (CI/ops)  ──► Wave 2 (publish code)
                                   └─► Wave 3 (migrations/CI) ──► Wave 4 (schema) ──► Wave 5 (docs)
```

- Waves 0 and 1 touch no application code and can ship today.
- Wave 2 and Wave 3 are independent: the publish code does not need the runner, and the runner does not need the lock.
- Wave 4 **requires** Wave 3 (migrations must go through the runner).
- Wave 5 requires all prior waves to have a truthful status to record.
- Tasks 9 and 10 both edit `storage/neon.py`; 6, 13, and 14 all edit `ci.yml`. Do not run those pairs in parallel worktrees.

**Estimated total:** 4–5 focused days, dominated by Wave 2 and Wave 3.

## Rollback notes

| Change | Rollback |
|---|---|
| Dashboard role switch | Restore the previous Vercel variable value and redeploy |
| Advisory lock | Revert the commit; the lock is transaction-scoped and disappears with it |
| Role timeouts | `ALTER ROLE <role> RESET statement_timeout;` (etc.) |
| CHECK constraints | `ALTER TABLE jobs DROP CONSTRAINT <name>;` — no data change |
| `pg_stat_statements` | `DROP EXTENSION pg_stat_statements;` — loses history only |
| Migration runner | It only inserts/updates `schema_migrations`; application state is unaffected |
