---
title: "DB audit W2 — Publish advisory lock, post-publish assertion, health checks"
labels: db-audit, wave-2, priority:high
milestone: PostgreSQL audit remediation
size: ~1.5d
depends_on:
blocks: wave-5
---

## Goal

Make the publish path tell the truth. Two concurrent publishes for the same
profile can interleave their stale-row sweep and leave a mixed result, and a
publish can report success while the dashboard shows something else. Both are
silent failures today; neither is visible without querying the database by hand.

## Spec

- Report: `docs/database/postgresql-audit-report.md` → INT-01, MON-01, MON-02, PERF-02
- Plan: `docs/superpowers/plans/2026-10-29-postgresql-audit-remediation.md` → §Wave 2 (Tasks 9–11)

## Tasks

- [ ] **9.** Take a transaction-scoped advisory lock keyed on `hashtext(profile)`
      as the first statement inside `replace_jobs`' transaction, test-first.
      Same-profile publishes serialize; different profiles must not block.
- [ ] **10.** Add `publish_state(profile) -> PublishState(live, recorded)` and
      call it at the end of `run_publish`, emitting one sorted-JSON summary line
      per profile and exiting non-zero when `live != recorded`.
- [ ] **11.** Add `scripts/db_health.py` with a pure `check()` plus a thin
      `main()`, wired into `daily.yml`, covering stale publish, storage growth,
      and branch-cap pressure.

## Acceptance criteria

- `tests/test_neon_integration.py` proves serialization: a second publish for
  the same profile waits, while a publish for a different profile does not.
- A publish whose `publish_meta.job_count` disagrees with the live row count
  exits non-zero and prints `"ok": false` with both numbers and the profile name.
- The summary line is valid JSON, key-sorted, one line per profile, and does not
  break the existing log parsing or the Telegram failure alert.
- `check()` is pure: tests construct the inputs and assert on the returned list
  without a database. Its signature accepts injected `ages`, so freshness is not
  read from the clock inside the function.
- `daily.yml` runs the health check after a successful install even when an
  earlier step failed — the check is most valuable on a bad day, not a good one.
- The health check skips the branch-count assertion with a printed notice when
  `NEON_API_KEY` / `NEON_PROJECT_ID` are absent, instead of failing the run.

## Human in the loop

None required to implement. The first real scheduled run should be watched to
confirm the alert path actually delivers.

## Dependencies

<!-- deps:start -->
<!-- deps:end -->

## Notes

- Tasks 9 and 10 both edit `src/jobscraper/storage/neon.py`. Run them in
  sequence, not in parallel worktrees.
- Do not take a global lock. A global lock makes one persona's publish block the
  other's, which is a regression, not a fix.
- `tests/test_db_health.py` is created here. Wave 3 must not depend on it.
