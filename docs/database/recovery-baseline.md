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

## 2026-11-26 — GitHub Actions artifact restored into a fresh Neon branch

This is the acceptance run the 2026-11-06 note said was still owed: a dump
produced **by CI on the default branch**, downloaded as a workflow artifact,
and restored into a **new** branch rather than a local container database.

### Where the artifact came from

| Step | Evidence |
| --- | --- |
| Workflow run | `db-backup` run `45720131358` on `main` (success) |
| Artifact | `db-backup`, `size_in_bytes` 83,156, `expired: false` |
| Downloaded file | `backup-20261125.dump`, 88,096 bytes |
| SHA-256 | `02ae37712b039eb122ce3c53b41791736d57f62b25335286f3528ec51d84840d` |
| TOC | 16 entries, `Dump Version 1.16-0`, `Dumped from database version 18.7` |

**The dump is of `drill/2026-11-02`, not `main`.** The repository secret
`NEON_DATABASE_URL_PUBLISHER` points at the drill branch: a `pg_stat_activity`
sample taken while run `45719346699` was dumping showed
`usename = jobs_publisher`, `application_name = pg_dump`, `datname = neondb` on
branch `br-muddy-water-b5yy3rz4`. The artifact's contents match that branch
exactly (below), which is independent confirmation. Until production is moved
back to `main` this is the branch the weekly copy protects; `main` has been
frozen at its `2026-11-02 10:54:14Z` publish since.

### The restore target was genuinely empty

Neon copies the parent's data into a new branch, so `verify/db-backup-20261126`
(`br-solitary-sky-b5kwqzri`, created from `main`) arrived with `main`'s rows.
Restoring over that would have made parity meaningless. Instead the run created
a **new, empty database** `restore_proof` on the new branch and restored into
that.

| Step | Command | Result |
| --- | --- | --- |
| Target identity | `select current_database(), current_setting('neon.branch_id', true)` | `restore_proof`, `br-solitary-sky-b5kwqzri` |
| Restore | `pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error` in `postgres:18` | exit 0 |
| Tables created | `pg_class` where `relkind = 'r'` in `public` | `jobs`, `publish_meta`, `schema_migrations` |

The DSN was a **direct** (non-`-pooler`) URL held in a `0600` file and passed to
the container as an environment variable, never as an argument; the file was
deleted with the dump afterwards.

### Parity: restored branch vs live `drill/2026-11-02`

`jobs` has primary key `(profile, job_id)`, and the same `job_id` appears once
per profile. A fingerprint keyed on `job_id` alone collapses those rows and
compares unrelated pairs — the first pass did exactly that and produced six
false differences. Keyed correctly:

| Measure | Restored | Live `drill` |
| --- | --- | --- |
| `jobs` rows | 127 | 127 |
| distinct `(profile, job_id)` | 127 | 127 |
| content MD5 over `profile, job_id, title, company, match_score, match_tier, is_active, published_at` | `2420693a03e150bb8722e34cf9f6e521` | `2420693a03e150bb8722e34cf9f6e521` |
| `publish_meta` `juliet` | 95 jobs / 173 sheet rows | 95 / 173 |
| `publish_meta` `jumalaw98` | 32 / 32 | 32 / 32 |
| newest `published_at` | `2026-11-02 22:18:47.628717+00` | same |
| `schema_migrations` | `001_init`, `002_roles`, `003_profile`, `004_persona_rename` | same |

Acceptance query, per profile (`live = recorded`):

| profile | live | recorded |
| --- | --- | --- |
| `juliet` | 95 | 95 |
| `jumalaw98` | 32 | 32 |

`127 = 95 + 32`, so the per-table row count and the per-profile split agree
rather than being two independent coincidences.

### Cleanup

`restore_proof` was dropped and branch `br-solitary-sky-b5kwqzri` deleted after
the run; the branch list returned to its previous seven entries. No other branch
was created or deleted.

## What this does not prove

The 2026-11-26 run closes the artifact half of the Wave 1 acceptance bullet: a
downloaded CI artifact restored cleanly into a genuinely empty target and
satisfied `live = recorded` for every profile. It does not close these:

1. **The Wave 0 drill branch still exists.** The bullet also requires that the
   branch created for the check be fresh *and* that `drill/2026-11-02` no longer
   exist. The drill branch is still Vercel's pinned production branch
   (`restricted_actions`: delete, delete-rw-endpoint,
   move-rw-endpoint-using-api), and lifting that pin is a Neon Console → Vercel
   step no API exposes. See [restore-drill.md](restore-drill.md).
2. **The artifact covers `drill`, not `main`.** As above, the secret resolves to
   the drill branch. That is the correct branch to protect while it is the one
   publishing writes to, but it means a copy of `main` is still not being taken.
   Repoint production first, then re-run `db-backup` and this check.
3. **Repeatability on Neon was not re-tested.** The local 2026-11-06 run
   restored twice into the same database and exited 0 both times. The 2026-11-26
   run restored once, because its target was a dedicated empty database on a
   branch that was deleted immediately afterwards. The flags are identical, but
   the second restore is inference from the local run, not observation.
4. **Nothing here exercises `pg_dump` under concurrent writes.** The dump ran
   against an idle branch (`daily-run` is `disabled_manually`), so no
   snapshot-isolation behaviour was tested.
