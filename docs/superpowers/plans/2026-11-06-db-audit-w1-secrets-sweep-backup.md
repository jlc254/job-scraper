# DB Audit W1 — Secret Scanning, Preview Sweep, Weekly Verified Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the three "documented but not real" DB-audit controls real: a secret
scan that fails CI, a sweep that keeps the Neon Free branch cap from filling, and a
weekly verified dump that lives outside Neon's six-hour PITR window.

**Architecture:** Three independent additions to the repository's guardrails, no
application-code path changes. A `secrets` job in `ci.yml` runs gitleaks on every push
and PR. A bash sweep, scheduled weekly in `cleanup-neon-preview.yml`, lists all Neon
branches, validates the whole listing, then deletes only non-default `preview/*`
branches older than `MAX_AGE_DAYS`. A bash dump script, scheduled weekly in a new
`db-backup.yml`, refuses a pooled DSN, writes into a dot-prefixed temp file inside
`postgres:18`, verifies with `pg_restore --list`, and only then renames the artifact for
upload.

**Tech Stack:** Bash 5, `curl`, Python 3 standard library (JSON/date parsing in the
scripts), pytest, GitHub Actions (`actions/checkout@v7.0.1`,
`actions/upload-artifact@v7.0.2`, `gitleaks/gitleaks-action@v3.0.0`), PostgreSQL 18
client inside the `postgres:18` image, Neon REST API v2.

**Spec:** `docs/database/issues/wave-1.md` (tasks 6–8 and their acceptance criteria),
arguing from `docs/database/postgresql-audit-report.md` §SEC-06, BAK-01, BAK-04.

**State at time of writing:** tasks 1–6 below are already implemented on
`feat/db-audit-w1-secrets-sweep-backup` as `cea193c`, `a6b6e10`, `c74ef62`, `335aed7`,
`c4ac679`. Their steps remain the reproduction and review recipe — run the tests and
the commands rather than re-creating files. Task 7 is the unfinished acceptance work
and is **not** implemented; do not tick it without producing the evidence it names.

## Global Constraints

- Python 3.12; `ruff` line length 100; `pytest` runs from the repo root with
  `pythonpath = ["src"]`.
- Every GitHub Action is pinned to a 40-character commit SHA, never a tag.
- Workflow-level `permissions` is exactly `{"contents": "read"}`. A job may widen it
  only through `JOB_PERMISSION_EXCEPTIONS` in `tests/test_workflows.py`.
- `ci.yml` must never contain the text `secrets.`; it may use `${{ github.token }}`.
- No `${{ }}` expression inside a `run:` body. Pass values through the step's `env:`.
- Every checkout sets `persist-credentials: false`; every job timeout is `> 0` and
  `<= 20` minutes.
- Never print, echo, or pass a DSN, password, or API key on a command line. Pass the
  DSN as an environment variable into the container (`--env PGURL`, no value); pass the
  Neon key to `curl` through `--config`.
- `pg_dump` uses the **direct** (non-pooled) host. Any DSN whose host contains
  `-pooler.` is refused with exit 2 and no artifact.
- `pg_dump`/`pg_restore` run inside `postgres:18`: Ubuntu 24.04 runners ship client 16,
  which refuses a PG 18 server.
- Neon Free limits that shape the design: 6-hour PITR, 10 branches, 1 manual snapshot.
- `MAX_AGE_DAYS` defaults to `7` and must be a positive integer; an explicitly empty
  value is a usage error, not a request for the default.
- Sweep schedule `23 4 * * 1` (Monday 04:23 UTC). Backup schedule `17 4 * * 0`
  (Sunday 04:17 UTC). Both are off the hour and clear of `daily.yml` at 03:07.
- Backup artifact name `db-backup`, path `backups/backup-*.dump`,
  `if-no-files-found: error`, `retention-days: 56`.
- Backup `concurrency` is `{group: db-backup, cancel-in-progress: false}`.
- Docs state only what the evidence proves. Where an acceptance bullet is unmet, the
  doc says so and names the blocker.

## Review Focus

These are the inputs a reasonable person would expect to be safe and that the spec
does not spell out. Each is pinned by a test in the task that owns the code.

1. **A branch marked `default` whose name matches `preview/*`** — the sweep must abort
   before deleting anything, including the harmless old preview listed beside it. A
   wrong branch here is production. (Task 2)
2. **An `updated_at` with no timezone, no value, or no parseable date** — age is the
   only guard against deleting a live branch, so the sweep must abort rather than
   guess old or new. (Task 2)
3. **`MAX_AGE_DAYS=""`** — the shape a missing repository variable takes when
   interpolated into `env:` — must exit 2, not silently delete every preview branch.
   (Task 2)
4. **An old preview branch on page 2** — the list is `updated_at`-descending, so a
   backlog of recent branches hides exactly the orphans the sweep exists to remove.
   (Task 2)
5. **A dump that connects and writes only a header** — `pg_restore --list` accepts
   that file, so the 10 KB size floor is the only thing that stops an empty backup
   from becoming the artifact everyone trusts. (Task 4)

## File Structure

| Path | Responsibility |
| --- | --- |
| `.github/workflows/ci.yml` | Adds the `secrets` job; no other job changes |
| `.github/workflows/cleanup-neon-preview.yml` | Adds `schedule:` and the `sweep` job beside the existing close-event job |
| `.github/workflows/db-backup.yml` | New workflow: schedule, dispatch, concurrency, one job (checkout → dump → upload) |
| `scripts/neon_branch_sweep.sh` | List → validate → delete; owns the `MAX_AGE_DAYS`/`DRY_RUN`/credential contract |
| `scripts/db_dump.sh` | Dump → size floor → `pg_restore --list` → rename; owns the DSN/`DUMP_DIR`/`DOCKER` contract |
| `tests/test_neon_branch_sweep.py` | Fake Neon API plus the 13 sweep tests |
| `tests/test_db_dump.py` | Docker shim plus the 8 dump tests |
| `tests/test_workflows.py` | Static workflow rules; registers the new workflow and job exception |
| `docs/08-security.md` | Corrects the secret-scanning claim and prints working commands |
| `docs/09-scheduling-and-setup.md` | Records both schedules, the backup workflow spec, and the secrets |
| `docs/database/recovery-baseline.md` | Records the dump/restore evidence and what it does not prove |
| `docs/database/issues/wave-1.md` | Authoritative task ticks and per-bullet status |

---

## Dependency gate: Wave 0 is only partially complete

Wave 1 declares `depends_on: wave-0`. Before treating any acceptance bullet as
closable, confirm all four facts:

```bash
# 1. The Wave 0 drill branch is gone.
curl -sS -H @<(printf 'header = "Authorization: Bearer %s"\n' "$NEON_API_KEY") \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID/branches?limit=100" |
  python3 -c 'import json,sys; print([b["name"] for b in json.load(sys.stdin)["branches"]])'

# 2. Production is back on main, not the drill branch.
#    Neon Console -> Project -> Branches, or the Vercel Neon integration settings.

# 3. Branch headroom exists below the Free-tier cap of 10.
#    Count the branch names printed by step 1.

# 4. The manual snapshot from the drill is cleaned up (cap: 1).
```

Known state on 2026-11-06: **the gate is partly met.** The snapshot/restore drill ran,
but cleanup steps 2–7 of `docs/database/restore-drill.md` did not. Three specific
blockers stand between the branch and full acceptance:

1. `drill/2026-11-02` (`br-muddy-water-b5yy3rz4`) still exists and carries
   `restricted_actions: delete "vercel production branch"`. Lifting that is a human
   step in Neon Console → Vercel integration settings; no API exposes it.
2. The project is at **10/10 branches**, so `create_branch` fails until the sweep runs
   or a stale `preview/dependabot/*` branch is deleted by hand.
3. `db-backup.yml` is not on `main`, so `workflow_dispatch` is not offered and no
   artifact exists to download.

Do not mark Task 7 complete while any of the three is true.

---

### Task 1: Enforce secret scanning in CI (issue task 6)

**Files:**
- Modify: `.github/workflows/ci.yml` (append the `secrets` job)
- Modify: `tests/test_workflows.py` (`JOB_PERMISSION_EXCEPTIONS`, two new tests)
- Modify: `docs/08-security.md` §Secret scanning
- Test: `tests/test_workflows.py`

**Interfaces:**
- Consumes: `load(name)`, `triggers(doc)`, `steps(doc)`, `WORKFLOWS`,
  `JOB_PERMISSION_EXCEPTIONS` from `tests/test_workflows.py`.
- Produces: job id `secrets` in `ci.yml`; the allowlist entry
  `("ci.yml", "secrets"): {"contents": "read", "pull-requests": "read"}` that
  `test_least_privilege_and_no_dangerous_triggers` and
  `test_only_the_secret_scan_may_read_pull_requests` both read.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_secret_scan_runs_on_every_pull_request() -> None:
    # A paths: filter (or an `if:`) would let a secret-bearing commit reach main without
    # the gate ever running, which is the exact failure SEC-06 describes.
    doc = load("ci.yml")
    job = doc["jobs"]["secrets"]
    assert "if" not in job
    assert "needs" not in job
    pull_request = triggers(doc).get("pull_request")
    if isinstance(pull_request, dict):
        assert "paths" not in pull_request
        assert "paths-ignore" not in pull_request


def test_only_the_secret_scan_may_read_pull_requests() -> None:
    # A per-job permission is the one place a workflow can widen its own grant, so the
    # exception list is the complete allowlist and nothing may widen it silently.
    for path in WORKFLOWS:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_id, job in doc["jobs"].items():
            granted = job.get("permissions", doc["permissions"])
            if "pull-requests" in granted:
                assert (path.name, job_id) in JOB_PERMISSION_EXCEPTIONS, f"{path.name}:{job_id}"
                assert granted["pull-requests"] == "read", f"{path.name}:{job_id}"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_workflows.py -q -k "secret_scan or only_the_secret_scan"`
Expected: FAIL — `KeyError: 'secrets'`.

- [ ] **Step 3: Add the allowlist entry**

```python
JOB_PERMISSION_EXCEPTIONS = {
    ("ci.yml", "secrets"): {"contents": "read", "pull-requests": "read"},
}
```

- [ ] **Step 4: Add the job to `ci.yml`**

Job id `secrets`, `runs-on: ubuntu-24.04`, `timeout-minutes: 10`, a job-level
`permissions` equal to the allowlist entry above, and exactly two steps:

1. `Check out` — `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
   with `fetch-depth: 0` (a shallow clone hides the commit that introduced the
   secret) and `persist-credentials: false`.
2. `Scan for secrets` — `gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e # v3.0.0`
   with `env: {GITHUB_TOKEN: ${{ github.token }}, GITLEAKS_ENABLE_COMMENTS: "false"}`.
   v2 is retired; do not use it. `github.token`, not the `GITHUB_TOKEN` secret — the
   test below forbids `secrets.` anywhere in this file.

- [ ] **Step 5: Confirm the pin and the file-level rules**

Run: `python scripts/pin_actions.py --check && pytest tests/test_workflows.py -q`
Expected: pin check clean; all workflow tests pass.

- [ ] **Step 6: Prove the gate fires on a generated fake key**

Generate at run time — never commit a literal key, and do not reuse the example key
printed in AWS's own documentation, which some rulesets allowlist:

```bash
key="$(python3 -c "import secrets,string; a=string.ascii_uppercase+string.digits; print('AKIA'+''.join(secrets.choice(a) for _ in range(16)))")"
scratch="$(mktemp -d)"
git switch -c probe/gitleaks-gate
printf 'aws_access_key_id = %s\n' "$key" > "$scratch/probe.txt"
git add -f "$scratch/probe.txt" && git commit -m "probe: fake credential"
git push -u origin probe/gitleaks-gate
```

Open a PR, wait for `secrets` to finish, record `secrets: failure` and the run id,
then delete the probe branch and PR. The probe file must never reach `main`.

- [ ] **Step 7: Correct `docs/08-security.md`**

The `Secret scanning` section must say the gate is the `secrets` job in `ci.yml` on
every push and PR, and that `pre-commit install` is a local convenience that does
nothing until installed. The printed commands must be the ones that work:
`pip install pre-commit && pre-commit install`, then
`pre-commit run gitleaks --all-files`.

- [ ] **Step 8: Commit**

```bash
git add .github/workflows/ci.yml tests/test_workflows.py docs/08-security.md
git commit -m "ci: enforce gitleaks on every push and pull request"
```

---

### Task 2: Write the preview-branch sweep (issue task 7, script half)

**Files:**
- Create: `scripts/neon_branch_sweep.sh` (executable)
- Test: `tests/test_neon_branch_sweep.py`

**Interfaces:**
- Consumes: the pagination shape and credential handling of
  `scripts/neon_preview_branch.sh` — cursor in `pagination.next`, `limit=100`,
  `Authorization: Bearer` supplied via `curl --config <(...)`.
- Produces: a script with this env contract —
  `NEON_API_KEY` (required), `NEON_PROJECT_ID` (required), `MAX_AGE_DAYS`
  (default `7`, positive integer), `DRY_RUN` (default `0`), `NEON_API_BASE`
  (default `https://console.neon.tech/api/v2`). Exit 0 on success, 1 on API/parse
  error, 2 on usage error. stdout ends with `deleted=<n> kept=<n>`.

- [ ] **Step 1: Write the test harness**

The fixture is the part an implementer cannot guess, so it is fixed here: a
`HTTPServer` on `127.0.0.1:0` serving `/api/v2`. `GET
/api/v2/projects/prj_1/branches?limit=100[&cursor=…]` returns
`{"branches": [...], "pagination": {"next": "cN"}}`, rejecting (500) a missing
`Authorization: Bearer k`, a missing `Accept: application/json`, or a `limit` other
than `100`. `DELETE /api/v2/projects/prj_1/branches/<id>` records the id and returns a
configurable status. `run(base, **overrides)` executes `bash scripts/neon_branch_sweep.sh`
with `NEON_API_BASE`, `NEON_API_KEY=k`, `NEON_PROJECT_ID=prj_1` plus overrides, and
`None` values removed so a missing variable can be exercised.

Then the tests, each a name plus the assertion that must hold:

| Test | Assertion |
| --- | --- |
| `test_deletes_only_old_preview_branches` | with old `preview/old`, new `preview/new`, default `main`, non-preview `devtest`: deletes `["b1"]` only; stdout `deleted=1 kept=3`; exit 0 |
| `test_refuses_when_the_default_branch_matches_the_preview_pattern` | default `preview/x` plus old `preview/old`: exit 1, **no DELETE**, stderr names `preview/x` and `default` |
| `test_dry_run_reports_what_it_would_delete_and_deletes_nothing` | `DRY_RUN=1`: no DELETE, stdout has `Would delete 'preview/old'` and `deleted=0 kept=2` |
| `test_finds_an_old_preview_listed_on_a_later_page` | two pages, orphan on page 2: deletes `br-7`; requests are `?limit=100` then `?limit=100&cursor=c1`; exactly 2 GETs |
| `test_unusable_updated_at_aborts_without_deleting` | parametrized `None`, `"not-a-date"`, `"2020-01-01T00:00:00"` (naive): exit 1, no DELETE, stderr contains `updated_at` |
| `test_a_future_timestamp_is_kept_not_treated_as_ancient` | `days_old=-30`: no DELETE, `deleted=0 kept=1` |
| `test_max_age_days_overrides_the_default` | 3-day-old preview survives the default, is deleted with `MAX_AGE_DAYS=2` |
| `test_delete_treats_404_as_success` | DELETE returns 404: exit 0, `deleted=1` |
| `test_delete_fails_loudly_on_any_other_error` | DELETE returns 401: exit 1, stderr contains `HTTP 401` |
| `test_the_api_key_never_reaches_curl_s_argv` | `curl` shim records argv: some item is `--config`; no item equals `k`; no item contains `Bearer` |
| `test_max_age_days_must_be_a_positive_integer` | parametrized `"0"`, `"-1"`, `"seven"`, `"7.5"`, `""`: exit 2, one stderr line, contains `MAX_AGE_DAYS` |
| `test_missing_credentials_are_a_usage_failure` | `NEON_API_KEY=None`: non-zero exit, stderr `NEON_API_KEY is required` |
| `test_an_unparseable_branch_list_aborts_without_deleting` | body `<html>not json</html>`: exit 1, no DELETE, stderr `could not be parsed` |

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_neon_branch_sweep.py -q`
Expected: FAIL — script not found.

- [ ] **Step 3: Implement the script**

Order is the safety property: `collect_branches` appends every page to a temp file;
`classify` (Python, reading stdin) emits `TOTAL`, `REFUSE`, and `DELETE` records and
exits 2 on any shape violation; the caller scans all records for `REFUSE` and aborts
**before** the first DELETE. Age is `now - updated_at > timedelta(days=max_age)`;
a naive timestamp is exit 2, so a future timestamp yields a negative age and is kept.
Deletes read the HTTP status with `--write-out '%{http_code}'`; `2??` and `404` count
as deleted, everything else is `::error::` + exit 1. `DRY_RUN=1` prints and counts
nothing. The key travels only through `curl --config <(neon_curl_config)`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_neon_branch_sweep.py -q && bash -n scripts/neon_branch_sweep.sh`
Expected: 19 tests pass (the parametrized ones expand), syntax clean.

- [ ] **Step 5: Commit**

```bash
git add scripts/neon_branch_sweep.sh tests/test_neon_branch_sweep.py
git commit -m "feat(ci): add the stale preview-branch sweep"
```

---

### Task 3: Schedule the sweep weekly (issue task 7, workflow half)

**Files:**
- Modify: `.github/workflows/cleanup-neon-preview.yml` (add `schedule:` and `sweep`)
- Modify: `tests/test_workflows.py`
- Modify: `docs/09-scheduling-and-setup.md`

**Interfaces:**
- Consumes: Task 2's script and env contract.
- Produces: job id `sweep`, cron `23 4 * * 1`, sharing the workflow-level
  `contents: read` grant.

- [ ] **Step 1: Write the failing test**

```python
def test_the_preview_sweep_runs_weekly() -> None:
    # The close event is the only cleanup path for a preview branch, so an orphan from a
    # failed or skipped run is never revisited without this schedule.
    doc = load("cleanup-neon-preview.yml")
    assert triggers(doc)["schedule"] == [{"cron": "23 4 * * 1"}]
    job = doc["jobs"]["sweep"]
    assert job.get("permissions", doc["permissions"]) == {"contents": "read"}
    assert 0 < job["timeout-minutes"] <= 20
    checkout = next(s for s in job["steps"] if s.get("uses", "").startswith("actions/checkout"))
    assert checkout["with"]["persist-credentials"] is False
    sweep = next(s for s in job["steps"] if "neon_branch_sweep.sh" in str(s.get("run", "")))
    assert sweep["run"] == "bash scripts/neon_branch_sweep.sh"
    assert sweep["env"]["NEON_API_KEY"] == "${{ secrets.NEON_API_KEY }}"
    assert sweep["env"]["NEON_PROJECT_ID"] == "${{ secrets.NEON_PROJECT_ID }}"
    assert sweep["env"].get("DRY_RUN", "0") == "0"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest tests/test_workflows.py -q -k preview_sweep`
Expected: FAIL — `KeyError: 'sweep'`.

- [ ] **Step 3: Add the schedule and job**

Add `schedule: [{cron: "23 4 * * 1"}]` to the existing `on:` and a `sweep` job with
`runs-on: ubuntu-24.04`, `timeout-minutes: 10`, and two steps: the pinned checkout
(`persist-credentials: false`) and
`bash scripts/neon_branch_sweep.sh` with only `NEON_API_KEY` and `NEON_PROJECT_ID`
in `env`. Do not set `MAX_AGE_DAYS` (the seven-day default is what production runs)
and do not set `DRY_RUN` (a report would let the cap fill while staying green).

- [ ] **Step 4: Run it to verify it passes**

Run: `pytest tests/test_workflows.py -q`
Expected: PASS, including the existing close-event test that requires `delete-branch`
to contain only its checkout and delete steps.

- [ ] **Step 5: Document the schedule**

In `docs/09-scheduling-and-setup.md`, add one line beside the existing schedules:
"Mondays 04:23 UTC (`cleanup-neon-preview.yml`) deletes `preview/*` branches unchanged
for seven days", and note in the cleanup/preview paragraph that the sweep covers
branches whose close event was missed and never touches the default branch.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/cleanup-neon-preview.yml tests/test_workflows.py docs/09-scheduling-and-setup.md
git commit -m "ci: sweep preview branches older than seven days"
```

---

### Task 4: Write the verified dump script (issue task 8, script half)

**Files:**
- Create: `scripts/db_dump.sh` (executable)
- Test: `tests/test_db_dump.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a script with this env contract —
  `NEON_DATABASE_URL_PUBLISHER` (required, direct), `DUMP_DIR` (default `.`),
  `DOCKER` (default `docker`, overridable for the test shim). Exit 0 with
  `backup-YYYYMMDD.dump` in `DUMP_DIR`; 2 for a missing or pooled DSN; 1 when the
  dump or verification fails, with no artifact left behind. stdout on success contains
  `verified`.

- [ ] **Step 1: Write the test harness**

`SHIM` is a bash script standing in for docker: it appends each argv item
NUL-separated to `$DOCKER_ARGV_LOG`, finds the `--volume`/`-v` source as the output
directory, then for `*pg_dump*` either exits `$FAKE_DUMP_STATUS` or writes
`$FAKE_DUMP_BYTES` zero bytes to `$out_dir/$DUMP_NAME`, and for `*pg_restore*` exits
`$FAKE_RESTORE_STATUS`. The `stub` fixture writes it to `tmp_path/bin/docker` mode
`0755`; `run()` invokes `bash scripts/db_dump.sh` with `DOCKER`, `DOCKER_ARGV_LOG`,
`DUMP_DIR`, and a direct DSN; `dumps()` lists `backup-*`.

| Test | Assertion |
| --- | --- |
| `test_refuses_a_pooled_dsn` | exit 2, one stderr line containing `pooled`, no dump, **docker never invoked** |
| `test_a_missing_dsn_is_a_usage_error` | exit 2, one stderr line naming `NEON_DATABASE_URL_PUBLISHER`, no dump, no docker |
| `test_writes_and_verifies_a_custom_format_dump` | exit 0, exactly `backup-\d{8}\.dump`, 20480 bytes, no dot-file left, stdout `verified`, container argv has `--format=custom`, `--no-owner`, `--no-privileges`, `postgres:18` |
| `test_a_dump_below_the_size_floor_is_discarded` | `FAKE_DUMP_BYTES=100`: exit 1, stderr `too small`, directory empty |
| `test_a_dump_pg_restore_cannot_list_is_discarded` | `FAKE_RESTORE_STATUS=1`: exit 1, stderr `pg_restore`, directory empty |
| `test_a_failed_pg_dump_is_discarded` | `FAKE_DUMP_STATUS=1`: exit 1, stderr `pg_dump failed`, directory empty |
| `test_the_password_never_reaches_docker_s_argv` | argv has no `s3cret`, no full DSN, has `--env` and `PGURL`, no `PGURL=` |
| `test_the_dump_directory_is_created_when_missing` | missing `DUMP_DIR` is created; one dump |

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_db_dump.py -q`
Expected: FAIL — script not found.

- [ ] **Step 3: Implement the script**

Validate the DSN first: empty → exit 2; host matching `*-pooler.*` → exit 2 with one
stderr line. Resolve `DUMP_DIR` to an absolute path (docker resolves a relative
bind-mount source against the daemon's cwd, not the runner's). Write to
`.backup-YYYYMMDD.dump.tmp`, `export PGURL` and `export DUMP_NAME`, and run
`docker run --rm --user "$(id -u):$(id -g)" --env PGURL --env DUMP_NAME --volume
"$dump_dir:/out" postgres:18 sh -c 'exec pg_dump "$PGURL" --format=custom --no-owner
--no-privileges --file "/out/$DUMP_NAME"'`. On failure or below 10240 bytes or a
failing `pg_restore --list`, delete the temp file and exit 1. Only then `mv` to the
final name.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_db_dump.py -q && bash -n scripts/db_dump.sh`
Expected: 8 tests pass; syntax clean.

- [ ] **Step 5: Commit**

```bash
git add scripts/db_dump.sh tests/test_db_dump.py
git commit -m "feat(db): verify a logical dump before publishing it"
```

---

### Task 5: Add the weekly backup workflow (issue task 8, workflow half)

**Files:**
- Create: `.github/workflows/db-backup.yml`
- Modify: `tests/test_workflows.py` (`REVIEWED_WORKFLOWS`, new test)
- Modify: `docs/09-scheduling-and-setup.md`

**Interfaces:**
- Consumes: Task 4's script and env contract; the `NEON_DATABASE_URL_PUBLISHER`
  repository secret.
- Produces: a reviewed workflow named `db-backup.yml` with a job `backup` and an
  artifact `db-backup`.

- [ ] **Step 1: Write the failing test**

```python
def test_db_backup_is_weekly_and_never_overlaps() -> None:
    doc = load("db-backup.yml")
    assert set(triggers(doc)) == {"schedule", "workflow_dispatch"}
    assert triggers(doc)["schedule"] == [{"cron": "17 4 * * 0"}]
    assert doc["concurrency"] == {"group": "db-backup", "cancel-in-progress": False}

    job = doc["jobs"]["backup"]
    assert 0 < job["timeout-minutes"] <= 20
    by_name = {s["name"]: s for s in job["steps"]}
    dump = by_name["Dump and verify"]
    assert dump["run"] == "bash scripts/db_dump.sh"
    assert dump["env"]["NEON_DATABASE_URL_PUBLISHER"] == (
        "${{ secrets.NEON_DATABASE_URL_PUBLISHER }}"
    )
    assert dump["env"]["DUMP_DIR"] == "backups"

    upload = by_name["Upload the dump"]
    assert upload["with"]["name"] == "db-backup"
    assert upload["with"]["path"].strip() == "backups/backup-*.dump"
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["retention-days"] == 56
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest tests/test_workflows.py -q -k db_backup`
Expected: FAIL — `FileNotFoundError` for the workflow.

- [ ] **Step 3: Create the workflow**

`name: db-backup`; `on: {schedule: [{cron: "17 4 * * 0"}], workflow_dispatch: {}}`;
`permissions: {contents: read}`; `concurrency: {group: db-backup,
cancel-in-progress: false}` (not cancelling: a half-cancelled dump is the unverified
artifact this workflow prevents). One job `backup`, `runs-on: ubuntu-24.04`,
`timeout-minutes: 15`, three steps: pinned checkout with `persist-credentials: false`;
`Dump and verify` running `bash scripts/db_dump.sh` with the secret and
`DUMP_DIR: backups`; `Upload the dump` using
`actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2` with the
four values the test asserts.

- [ ] **Step 4: Register the workflow and run the suite**

Add `"db-backup.yml"` to `REVIEWED_WORKFLOWS`. Run:
`pytest tests/test_workflows.py -q && python scripts/pin_actions.py --check`
Expected: PASS; the new workflow is reviewed, its actions pinned, its job within the
timeout and permission rules.

- [ ] **Step 5: Document the workflow**

In `docs/09-scheduling-and-setup.md`, add the Sunday 04:17 line, a
`Workflow specification (.github/workflows/db-backup.yml)` section listing the
triggers, concurrency, timeout, the three steps and the 56-day artifact, and note in
`Secrets` that `NEON_DATABASE_URL_PUBLISHER` feeds both `main.py publish` and this
dump.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/db-backup.yml tests/test_workflows.py docs/09-scheduling-and-setup.md
git commit -m "ci: back up the database weekly and keep the artifact"
```

---

### Task 6: Prove the dump restores (issue task 8, acceptance half — local)

**Files:**
- Create: `docs/database/recovery-baseline.md`
- Modify: `docs/database/issues/wave-1.md` (status table only)

**Interfaces:**
- Consumes: Task 4's script and Task 5's artifact contract.
- Produces: recorded evidence (byte count, TOC count, per-table and per-profile row
  parity) plus an explicit list of what the run does **not** prove.

- [ ] **Step 1: Dump against the live branch**

Run `scripts/db_dump.sh` with a DSN obtained for the `publisher` role, **direct**
host only, held in a `0600` file and deleted afterwards. Do not paste the DSN into a
terminal, a log, or the transcript.

- [ ] **Step 2: Restore into an empty local PG 18**

Start `postgres:18` locally, create an empty database, and run inside the container:
`pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error --dbname
"$PGURL" /out/backup-YYYYMMDD.dump`. Record the exit code and the table count.

- [ ] **Step 3: Run the acceptance query on both sides**

```sql
SELECT j.profile, count(*) AS live, m.job_count AS recorded
FROM jobs j JOIN publish_meta m USING (profile)
GROUP BY j.profile, m.job_count
ORDER BY j.profile;
```

Each profile must satisfy `live = recorded`, with identical values live and restored.
Also compare `jobs`, `publish_meta`, and `schema_migrations` row counts.

- [ ] **Step 4: Prove the restore is repeatable**

Restore a second time into the now non-empty database with the same flags. Expected:
exit 0, no manual cleanup. This is what makes the drill safe to re-run.

- [ ] **Step 5: Write `docs/database/recovery-baseline.md`**

Record the date, source branch, dump size, `pg_restore --list` entry count and dump
format version, both restore results, the row-count table, the per-profile table, and
a **What this does not prove** section stating that a local round trip does not
satisfy the "downloaded Actions artifact into a fresh Neon branch" bullet. Name the
three blockers from the dependency gate.

- [ ] **Step 6: Update the status table, not the checkboxes**

In `docs/database/issues/wave-1.md`, tick task 7 only. Leave 6 and 8 unticked while the
required-check and fresh-branch bullets are unmet, and record each bullet's state in
the status table.

- [ ] **Step 7: Commit**

```bash
git add docs/database/recovery-baseline.md docs/database/issues/wave-1.md
git commit -m "docs(db): record the dump/restore proof and what it does not cover"
```

---

### Task 7: Close the remaining acceptance bullets (issue tasks 6 and 8)

This task is the unfinished half. It is **not** complete as of 2026-11-06, and nothing
below may be ticked from inference.

**Files:**
- Modify: `docs/database/issues/wave-1.md` (tick tasks 6 and 8 when, and only when,
  each bullet's evidence exists)
- Modify: `docs/database/recovery-baseline.md` (replace the local-only note with the
  artifact run)

**Interfaces:**
- Consumes: the merged workflows from Tasks 1 and 5; the branch headroom produced by
  the Task 3 sweep or by manual deletion.
- Produces: a `secrets` check enforced by branch protection, and one recorded
  artifact-into-fresh-branch restore.

- [ ] **Step 1: Make `secrets` a required check**

In GitHub → Settings → Rules → the ruleset that currently requires `deploy-preview`,
add `secrets` to the required status checks. This needs repository admin; the current
account does not have it, so record the request rather than simulating the change.
Verify with `env -u GITHUB_TOKEN -u GH_TOKEN gh api repos/jlc254/job-scraper/rulesets`
and confirm `secrets` appears in `required_status_checks`.

- [ ] **Step 2: Clear the Wave 0 blockers**

Lift `restricted_actions` from `drill/2026-11-02` in Neon Console → Vercel integration
settings, delete the drill branch, and restore production to `main`. Confirm the
branch list no longer contains `drill/2026-11-02`. If the sweep has not run yet,
delete stale `preview/dependabot/*` branches by hand to get below 10/10.

- [ ] **Step 3: Produce an artifact from `main`**

Merge the branch so `db-backup.yml` exists on the default branch, then run it:
`env -u GITHUB_TOKEN -u GH_TOKEN gh workflow run db-backup.yml`. Wait for the run to
go green and download the artifact with `gh run download <run-id> -n db-backup`.
Expected: `backup-YYYYMMDD.dump`, and the run is red if no file was uploaded.

- [ ] **Step 4: Restore into a fresh branch**

Create a branch from `main` with a name for this run (for example
`verify/db-backup-<date>`), not the deleted drill branch. Restore inside `postgres:18`
with `--clean --if-exists --no-owner --no-privileges --exit-on-error`, then run the
acceptance query from Task 6 against the branch. Expected: exit 0 and `live = recorded`
for every profile.

- [ ] **Step 5: Record and clean up**

Add the artifact run id, dump size, TOC count, restore exit code and per-profile table
to `docs/database/recovery-baseline.md`; delete the verification branch (the Free tier
allows 10 and the drill must not consume one permanently). Only now tick task 8 and
the corresponding acceptance bullet; tick task 6 from Step 1's ruleset evidence.

- [ ] **Step 6: Commit**

```bash
git add docs/database/issues/wave-1.md docs/database/recovery-baseline.md
git commit -m "docs(db): close the W1 acceptance bullets with artifact evidence"
```

---

## Verification gate

Run before opening or updating the PR:

```bash
pytest -q
ruff check .
ruff format --check .
python scripts/pin_actions.py --check
bash -n scripts/db_dump.sh scripts/neon_branch_sweep.sh
git diff --check
```

Expected: 565 passed, 2 skipped; every command exits 0. Then confirm the workflow
tests specifically cover the new jobs:

```bash
pytest tests/test_workflows.py -q -k "secret or preview_sweep or db_backup"
pytest tests/test_neon_branch_sweep.py tests/test_db_dump.py -q
```

## Self-review

1. **Spec coverage.** Task 1 covers the `secrets` job, its pin, the doc correction and
   the fake-key proof. Tasks 2–3 cover the sweep, `DRY_RUN`, the default-branch
   refusal, `MAX_AGE_DAYS` and the weekly schedule. Tasks 4–5 cover the pooled-DSN
   refusal, `pg_restore --list`, upload with 56-day retention, weekly schedule,
   dispatch and concurrency. Task 6 covers restore and `live = recorded` locally;
   Task 7 covers the artifact-into-fresh-branch bullet and the required-check bullet.
   No acceptance bullet is unowned.
2. **Step scan.** Each step names the file, the exact test or the exact command and
   its expected result. The three tasks whose code is already committed say so, so an
   implementer verifies instead of guessing whether to recreate.
3. **Type consistency.** Env names are used identically in script, workflow and tests:
   `NEON_DATABASE_URL_PUBLISHER`, `DUMP_DIR`, `DOCKER`, `NEON_API_KEY`,
   `NEON_PROJECT_ID`, `MAX_AGE_DAYS`, `DRY_RUN`, `NEON_API_BASE`. Job ids are `secrets`,
   `sweep`, `backup` everywhere. Artifact name is `db-backup`, path
   `backups/backup-*.dump`.
4. **Review Focus.** All five items have a test in the owning task's Step 1 table or
   code block: default-branch refusal, unusable `updated_at`, empty `MAX_AGE_DAYS`,
   later-page orphan, header-only dump.
5. **Proportion.** The plan carries interfaces, test contracts and the dependency gate;
   it does not reproduce the 237-line sweep or the 101-line dump. Task 7 is explicit
   about being blocked rather than silently short.

## Execution handoff

Plan complete and saved to
`docs/superpowers/plans/2026-11-06-db-audit-w1-secrets-sweep-backup.md`. Please review
the plan. Which execution approach would you prefer?

- **Subagent-driven** — a fresh subagent implements each task and a fresh reviewer
  checks it before the next starts, then a whole-branch review. Best when the tasks
  share interfaces that a wrong guess would propagate.
- **Native** — I implement every task in this session, then one fresh reviewer on the
  most capable model checks the whole branch. Cheapest and fastest.

For this plan I recommend **Native**, because tasks 1–6 are already implemented and
green; the remaining work is one verification task with three human-gated steps, so
fresh contexts per task would mostly re-derive the same state.
