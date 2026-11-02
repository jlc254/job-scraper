---
title: "DB audit W5 — Recovery targets, rotation runbook, verification log"
labels: db-audit, wave-5, priority:low
milestone: PostgreSQL audit remediation
size: ~3h
depends_on: wave-0, wave-1, wave-2, wave-3, wave-4
blocks:
---

## Goal

Turn the audit from a document into a closed loop: state the recovery targets the
project actually accepts, write down the decisions that were made by default, and
record a pass/fail result for every checklist item so the next audit starts from
evidence instead of guesses.

## Spec

- Report: `docs/database/postgresql-audit-report.md` → BAK-03, SEC-02, SEC-03, SEC-08, plus §G checklist
- Plan: `docs/superpowers/plans/2026-10-29-postgresql-audit-remediation.md` → §Wave 5 (Tasks 18–19)

## Tasks

- [ ] **18.** Write `docs/database/recovery.md` (RPO/RTO from the measured drill),
      `docs/database/security-decisions.md` (why no RLS, why no network
      allowlisting, why `ssl=off` on the compute is correct, why no FK), and the
      four-step credential-rotation runbook. Update audit finding **statuses only**.
- [ ] **19.** Execute section G of the report, record every item as `PASS`,
      `FAIL`, or `BLOCKED (reason)` with date and command, list the accepted
      residual risks, and confirm one green scheduled run of `daily.yml`.

## Acceptance criteria

- `recovery.md` states an RPO and an RTO, where the RTO is derived from the
  duration measured in the Wave 0 drill — not an aspiration.
- The rotation runbook orders the steps so a failure can never leave both the
  publisher and the reader broken, and it never instructs anyone to paste a
  credential into shell history.
- `security-decisions.md` records each accepted risk with its compensating
  control. "Free tier does not offer it" is a constraint, not a control — pair it
  with something that does apply.
- `postgresql-audit-report.md` statuses are updated for closed findings only;
  no finding text is rewritten, and unverified items stay marked
  `Needs verification`.
- `docs/database/verification-log.md` contains one row per section-G item with a
  result and a date. No row contains query output that includes real data.
- One scheduled `daily.yml` run after all changes completes, the publish summary
  line shows `"ok": true`, and the health check reports no problems.

## Human in the loop

Confirming the scheduled run and any console-side residual risk needs your eyes.
The verification log documents what was observed, so it cannot be filled in from
the repository alone.

## Dependencies

<!-- deps:start -->
<!-- deps:end -->

## Notes

- This wave is a documentation wave only if the earlier waves actually landed.
  Writing a PASS for an unshipped change makes the whole report untrustworthy.
- Anything that could not be verified belongs in the residual-risk list with a
  reason, not quietly omitted.
