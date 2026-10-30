---
title: "DB audit W1 — Secret scanning, branch sweep, weekly verified backup"
labels: db-audit, wave-1, priority:high, needs-console
milestone: PostgreSQL audit remediation
size: ~4h
depends_on: wave-0
blocks: wave-5
---

## Goal

Close the two "documented but not real" gaps and give the project a backup
schedule Neon Free will never provide. Secret scanning is described as
configured but does not run in CI; preview branches accumulate until they hit
the Free-tier cap; and there is no dump anywhere outside Neon's 6-hour PITR
window.

## Spec

- Report: `docs/database/postgresql-audit-report.md` → SEC-06, BAK-01, BAK-04
- Plan: `docs/superpowers/plans/2026-10-29-postgresql-audit-remediation.md` → §Wave 1 (Tasks 6–8)

## Tasks

- [ ] **6.** Add a `secrets` job to `ci.yml` using `gitleaks-action`, pin it to a
      commit SHA via `scripts/pin_actions.py`, correct the false claim in
      `docs/08-security.md`, and prove the gate fires on a generated fake AWS key.
- [ ] **7.** Write `scripts/neon_branch_sweep.sh` test-first, reusing the
      pagination and `curl --config -` credential handling already in
      `scripts/neon_preview_branch.sh`; delete only non-default `preview/*`
      branches older than `MAX_AGE_DAYS`; schedule it weekly.
- [ ] **8.** Write `scripts/db_dump.sh` producing a custom-format dump from a
      **direct, non-pooled** DSN inside the `postgres:18` image, verify the
      artifact with `pg_restore --list`, upload it with 56-day retention, and
      restore one artifact into a fresh branch to prove it is readable.

## Acceptance criteria

- The `secrets` job is required on PRs and demonstrably fails on a committed
  fake credential. Use a generated `AKIA` + 16 random uppercase characters —
  AWS's documented example key is allowlisted by some rulesets and would make
  a passing scan look like a working gate.
- `gitleaks-action` is referenced by a 40-character SHA, not a mutable tag.
- `docs/08-security.md` no longer claims gitleaks runs unless it does, and the
  commands it prints actually work.
- `pytest tests/test_neon_branch_sweep.py -q` passes, including the refusal
  case where a branch marked `default` matches the preview pattern.
- `DRY_RUN=1` prints what it would delete and deletes nothing.
- `NEON_DATABASE_URL_PUBLISHER=<pooled>` exits 2 with one line on stderr and
  writes no dump.
- A downloaded artifact restores cleanly into a throwaway branch and satisfies
  the per-profile `live = recorded` check. The branch created for this is fresh
  — the Wave 0 drill branch no longer exists.
- `.github/workflows/db-backup.yml` has a weekly `schedule` and a
  `workflow_dispatch` trigger, and `concurrency` prevents overlapping runs.

## Human in the loop

The `NEON_DATABASE_URL_PUBLISHER` repository secret must exist, and step 8's
manual verification needs a Neon console / `neonctl` session. Deleting the
verification branch after the check also needs console access.

## Dependencies

<!-- deps:start -->
<!-- deps:end -->

## Notes

- Step 8 consumes branch headroom. Running it before Wave 0's cleanup can push
  the project over the 10-branch cap.
- `pg_dump` must run in the `postgres:18` container: Ubuntu 24.04 runners ship
  client 16 and abort against a PG 18 server.
- Do not let this workflow run against `main` only — the point is a copy that
  survives a mistake on `main`.
