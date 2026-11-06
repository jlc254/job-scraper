# Recovery baseline — dump and restore evidence

The audit report (BAK-01, BAK-04) asks for a backup that lives outside Neon's
six-hour point-in-time-recovery window, and for proof that the backup can
actually be read back. This file records what was verified and, just as
importantly, what was **not** verified.

## 2026-11-06 — local dump/restore round trip

Source: Neon `main` (`br-green-butterfly-b5opvq53`), project
`autumn-rain-77812061`, PostgreSQL 18.6. The dump used a **direct, non-pooled**
connection, obtained from the Neon API and stripped of the `-pooler` host label.
The credential was held in a `0600` file for the duration and deleted afterwards.

| Step | Command | Result |
| --- | --- | --- |
| Dump | `scripts/db_dump.sh` (image `postgres:18`) | `backup-20261106.dump`, 105,367 bytes, exit 0 |
| Artifact check | `pg_restore --list` | 20 TOC entries, `Dump Version 1.16-0`, `Dumped from database version 18.6` |
| Restore A | `pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error` into an **empty** local PG 18.6 database | exit 0, 3 tables created |
| Restore B | same command into the now **non-empty** target | exit 0 (repeatable without manual cleanup) |

Row-count parity between live and restored (Restore A, before Restore B):

| Table | Live | Restored |
| --- | --- | --- |
| `jobs` | 169 | 169 |
| `publish_meta` | 2 | 2 |
| `schema_migrations` | 4 | 4 |

Acceptance query, per profile:

```sql
SELECT j.profile, count(*) AS live, m.job_count AS recorded
FROM jobs j JOIN publish_meta m USING (profile)
GROUP BY j.profile, m.job_count
ORDER BY j.profile;
```

| profile | live | recorded |
| --- | --- | --- |
| `juliet` | 137 | 137 |
| `jumalaw98` | 32 | 32 |

Identical on the live branch and on the restored copy, so the dump is complete
for every published profile rather than merely readable.

The throwaway database, the local dump, and the credential files were removed
after the run. No Neon branch was created or deleted.

## What this does not prove

This was a **local** round trip. It proves the artifact `scripts/db_dump.sh`
produces is restorable and data-complete, but it does **not** satisfy the
Wave 1 acceptance bullet, which requires a **downloaded GitHub Actions
artifact** restored into a **fresh Neon branch** with the Wave 0 drill branch
already deleted.

Three things are still outstanding before that bullet can be closed:

1. **The workflow is not on `main` yet.** `workflow_dispatch` only appears for
   workflows present on the default branch, so `db-backup.yml` cannot be
   triggered and no downloadable artifact exists until this branch merges.
2. **The Wave 0 drill branch still exists.** `drill/2026-11-02`
   (`br-muddy-water-b5yy3rz4`) carries
   `restricted_actions: delete "vercel production branch"`. Lifting that is a
   human step in the Neon Console → Vercel integration settings; it is not
   exposed by an API. See [restore-drill.md](restore-drill.md) cleanup step 2.
3. **Branch headroom.** The project is at the 10-branch Free-tier cap
   (`main`, `drill/2026-11-02`, `preview/feat/db-audit-w1-secrets-sweep-backup`,
   four `preview/dependabot/*`, and two newer `preview/dependabot/*` created on
   2026-11-05). Creating the verification branch requires deleting stale
   `preview/*` branches first — which the weekly sweep in
   [`.github/workflows/cleanup-neon-preview.yml`](../../.github/workflows/cleanup-neon-preview.yml)
   will do once it runs on a schedule.

Re-run this file's table after the first scheduled `db-backup` run, using the
downloaded artifact and a fresh branch named for that run.
