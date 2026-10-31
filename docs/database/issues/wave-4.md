---
title: "DB audit W4 — pg_stat_statements, role timeouts, integrity constraints"
labels: db-audit, wave-4, priority:medium, needs-console
milestone: PostgreSQL audit remediation
size: ~2h
depends_on: wave-3
blocks: wave-5
---

## Goal

Three small DDL changes, each closing a finding, all applied through the runner
from Wave 3. Enable the query visibility that is already preloaded but never
installed, bound runaway statements per role, and constrain two value domains
that are currently only convention.

## Spec

- Report: `docs/database/postgresql-audit-report.md` → PERF-02, SEC-05, INT-03
- Plan: `docs/superpowers/plans/2026-10-29-postgresql-audit-remediation.md` → §Wave 4 (Tasks 15–17)

## Tasks

- [ ] **15.** Add `005_pg_stat_statements.sql` and verify the extension installs
      as `neondb_owner` without superuser.
- [ ] **16.** Add `006_role_timeouts.sql` — but measure first: read
      `pg_stat_statements` for the slowest dashboard query and time one real
      publish, then choose ceilings that clear the observed p99 with margin.
- [ ] **17.** Add `007_integrity_constraints.sql`: `match_score` between 0 and
      100 (NULL allowed), `application_status` restricted to an allowlist —
      after re-reading the live distinct values.

## Acceptance criteria

- `SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements'`
  returns a row and `pg_stat_statements` row count grows after real traffic.
- `pg_roles.rolconfig` shows the intended settings for both `jobs_%` roles.
- `SELECT pg_sleep(...)` as `jobs_reader` and as `jobs_publisher` is cancelled
  at each role's own ceiling, proving the settings are actually enforced rather
  than merely recorded.
- The reader ceiling is justified by a measured query, recorded in
  `docs/database/timeout-baseline.md` with the query and the number. A 15 s
  ceiling that cuts off a healthy dashboard query is a defect, not a fix.
- Constraints are added with zero cleanup: the live data already satisfies both
  (`application_status` observed as `New`; `match_score` observed 25–93, no
  nulls, nothing out of range). If a value outside the allowlist appears,
  extend the list before writing the migration.
- Integration tests assert that a score of 101 and an unknown status both raise
  `CheckViolation`.
- The migration files apply cleanly from an empty database in the Wave 3 `db` job.

## Human in the loop

If the extension does not install as `neondb_owner`, confirming the role and
retrying needs console access. Role settings apply at login, so existing pooled
connections keep the old values until the compute recycles — restarting or
waiting for scale-to-zero is a console action.

## Dependencies

<!-- deps:start -->
<!-- deps:end -->

## Notes

- Rollback for all three is documented in the plan's rollback table; none of them
  touches data.
- Prefer the Free-tier compromise: in-memory extension stats reset on
  scale-to-zero. That is acceptable, not a reason to skip the finding.
- Do not grant superuser to an application role to make the extension install.
