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
SELECT coalesce(j.profile, m.profile) AS profile,
       count(j.job_id) AS live,
       coalesce(m.job_count, 0) AS recorded
FROM jobs j
FULL OUTER JOIN publish_meta m USING (profile)
GROUP BY coalesce(j.profile, m.profile), m.job_count
ORDER BY 1;
```

`count(j.job_id)` (not `count(*)`) keeps a profile that exists only in
`publish_meta` visible as `live = 0`, and `coalesce` on the join key keeps a
profile that exists only in `jobs` visible as `recorded = 0`. An inner join
would silently drop both mismatches and still report parity.

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
3. **Branch headroom.** The project is at the 10-branch Free-tier cap —
   `main`, archived `vercel-dev`, `drill/2026-11-02`,
   `preview/feat/db-audit-w1-secrets-sweep-backup`, four `preview/dependabot/*`
   from the original audit, and two newer `preview/dependabot/*` created on
   2026-11-05 (10 total). Creating the verification branch requires deleting
   stale `preview/*` branches first — which the weekly sweep in
   [`.github/workflows/cleanup-neon-preview.yml`](../../.github/workflows/cleanup-neon-preview.yml)
   will do once it runs on a schedule.

Re-run this file's table after the first scheduled `db-backup` run, using the
downloaded artifact and a fresh branch named for that run.
