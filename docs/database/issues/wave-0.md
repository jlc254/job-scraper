---
title: "DB audit W0 — Verify dashboard role, snapshot, restore drill, branch cleanup"
labels: db-audit, wave-0, priority:high, needs-console
milestone: PostgreSQL audit remediation
size: ~4h
depends_on:
blocks: wave-1, wave-5
---

## Goal

Convert the two High-severity findings from "unverified" to either closed or
scheduled. Right now nobody knows whether the dashboard connects as
`jobs_reader` or as the table owner, no restore has ever been attempted, and
the project sits at 7 of 10 branches on the Free tier. This wave changes no
code and no schema — it buys certainty.

## Spec

- Report: `docs/database/postgresql-audit-report.md` → SEC-01, BAK-02, BAK-04
- Plan: `docs/superpowers/plans/2026-10-29-postgresql-audit-remediation.md` → §Wave 0 (Tasks 1–5)

## Tasks

- [ ] **1.** Confirm what role the production `DATABASE_URL` authenticates as.
      Read only the username portion in the Vercel UI; corroborate with
      `pg_stat_activity`. Never copy the value into a file, terminal, or chat.
- [ ] **2.** Switch the dashboard to `jobs_reader` — **only if step 1 failed**.
      Keep the old value recoverable before overwriting it.
- [ ] **3.** Take the single permitted Free-tier manual snapshot and record the
      current PITR window and branch count.
- [ ] **4.** Run the first restore drill on a throwaway branch: compute the
      restore timestamp at run time (the 6-hour window makes any literal stale),
      verify per-profile self-consistency, prove a second read is identical,
      record the measured duration, then delete the branch.
- [ ] **5.** Delete the four `preview/dependabot/*` branches and the archived
      `vercel-dev`, after confirming nothing still references them.

## Acceptance criteria

- `docs/database/role-verification.md` exists and ends with an explicit
  `Result: PASS` or `Result: FAIL — dashboard uses <role>`, plus the
  `pg_stat_activity` summary as evidence.
- `docs/database/recovery-baseline.md` records snapshot name, creation time,
  PITR window, branch count, and the open RPO/RTO question.
- `docs/database/restore-drill.md` records the exact commands, start/end
  timestamps, measured duration, and the per-profile `live = recorded` result.
  It makes no claim that restored counts equal today's counts — a restore point
  is a coherent earlier moment, not the current one.
- Re-running the verification queries on the drill branch returns identical
  output, proving the drill used a read-only role.
- `neonctl branches list` shows at most 3 branches.
- No file, commit, or issue comment contains a connection string, password, or
  decrypted environment value.

## Human in the loop

Steps 1, 3, and 5 require the Vercel UI and the Neon console / `neonctl` —
they are not automatable from a coding session. Step 4 also needs a Neon
credential the agent does not hold.

## Dependencies

<!-- deps:start -->
<!-- deps:end -->

## Notes

- Counts drift on every publish. Do not assert literals such as 106/25
  anywhere; they were already 112/26 within nine hours of the audit.
- If step 1 passes, step 2 is a no-op — close it as "not required" rather than
  skipping the checkbox silently.
- The snapshot from step 3 is the only rollback point before the DDL in Wave 4.
