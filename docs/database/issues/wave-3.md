---
title: "DB audit W3 — Migration runner with checksums, real DB CI, schema drift gate"
labels: db-audit, wave-3, priority:medium
milestone: PostgreSQL audit remediation
size: ~1.5d
depends_on:
blocks: wave-4, wave-5
---

## Goal

Today migrations are pasted by hand, nothing records a checksum, and no test
ever applies them. That means a hand-edited live schema is undetectable and a
broken migration is found in production. This wave makes the migration set
executable, versioned, and diffable — and puts it under CI on the same Postgres
major version Neon runs.

## Spec

- Report: `docs/database/postgresql-audit-report.md` → MIG-01, MIG-02, MIG-04
- Plan: `docs/superpowers/plans/2026-10-29-postgresql-audit-remediation.md` → §Wave 3 (Tasks 12–14)

## Tasks

- [ ] **12.** Write `scripts/migrate.py` test-first: `load()`, `pending()`,
      `main()` with distinct exit codes, SHA-256 checksums, `--dry-run`,
      `--to`, and `--accept-checksums`. Each file runs in one transaction
      together with its `schema_migrations` row.
- [ ] **13.** Add a `db` CI job that applies migrations from zero and runs the
      integration tests, and bump `docker-compose.yml` from `postgres:17` to
      `postgres:18` so local and CI match Neon.
- [ ] **14.** Add `scripts/schema_dump.sh` plus a committed `docs/database/schema.sql`
      and a CI diff gate, so hand-edited live schema shows up as a failed job.

## Acceptance criteria

- Adopting the runner on an existing database **backfills** NULL checksums for
  `001_init` … `004_persona_rename` instead of failing. A recorded checksum that
  later differs is a hard error unless `--accept-checksums` is passed.
- Exit codes are distinct and documented: `0` ok, `2` config, `3` checksum
  mismatch, `4` SQL failure.
- Versions sort numerically: `009` applies before `010`.
- A second `migrate.py` run on an already-migrated database is a no-op.
- Editing an applied migration exits 3; `--accept-checksums` then exits 0 and
  prints every version it changed.
- The `db` job creates `jobs_publisher` and `jobs_reader` **before** running the
  chain. `migrations/002_roles.sql` raises if they are missing, so without this
  step the chain aborts on its second file on every run.
- The `db` job's `pytest` invocation does not reference test files created by
  other waves, so this wave stands alone.
- A PR adding a migration containing `SELECT 1/0;` fails at `migrate.py`.
- `schema_dump.sh` runs `pg_dump` inside the `postgres:18` image and strips the
  per-run `\restrict` / `\unrestrict` tokens, so a clean tree yields an empty diff.
- Changing a column default in a migration produces a non-empty diff and a red
  job.
- `docker compose down -v` is documented as required for the 17 → 18 image bump.

## Human in the loop

None required to implement. The `postgres:18` image is public and the job runs
entirely inside CI.

## Dependencies

<!-- deps:start -->
<!-- deps:end -->

## Notes

- Wave 4 requires this wave: new DDL must go through the runner.
- Task 13 and Task 14 both edit `ci.yml`, as does Wave 1's Task 6. Do not run
  them in parallel worktrees.
- Do not "fix" the runner by making checksum mismatch a warning. The mismatch is
  the only signal that production and the repository disagree.
