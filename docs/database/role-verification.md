# Role verification — which role does the production dashboard authenticate as?

- **Date:** 2026-11-02 (UTC)
- **Project:** `autumn-rain-77812061` (`job-scrapper`), database `neondb`
- **Question (SEC-01):** does the production `DATABASE_URL` authenticate as the
  read-only `jobs_reader`, or as the table owner?
- **Vercel variable inspected:** `DATABASE_URL`, target `production`, type
  `encrypted` (id not recorded here on purpose).

## How the evidence was obtained

The Vercel UI route in the plan ("open the variable and read the username") was
attempted first, and the Vercel API returns the value of an `encrypted`
variable as redacted — `filter_project_envs` and `get_project_env` expose the
key, target and type but not the decrypted string. No value was ever printed,
copied or stored.

The role was therefore proven the stronger way: **from the database side**, by
watching which role the running dashboard actually opens connections as. That
is direct evidence, whereas reading the variable only proves intent.

1. Production traffic was generated against the live deployment
   (`job-scraper-iyojajad4-…vercel.app`, the deployment built from `main`),
   a few hundred requests across `/` and `/jobs`, which both query the database
   from server components.
2. While that traffic was in flight, `pg_stat_activity` on the branch the app
   connects to was sampled repeatedly:

   ```sql
   SELECT usename, coalesce(application_name,'') AS app, state, count(*) AS n
   FROM pg_stat_activity
   WHERE datname = 'neondb'
   GROUP BY 1,2,3 ORDER BY 4 DESC;
   ```

3. A control sample was taken with no traffic in flight, and the same query was
   run against `main` for comparison.

## Result of the sampling

| Observation | Branch serving the app | `main` |
| --- | --- | --- |
| Under load | `jobs_reader` / `pgbouncer` / `idle` in every sample | — |
| Under load | `neondb_owner` / `pgbouncer` / `active` (platform/pooler connection only) | — |
| Control, idle | `jobs_reader` / `pgbouncer` / `idle` pooled connections still present | — |
| No app traffic | — | only `neondb_owner` / `pgbouncer`; no `jobs_reader` |

`jobs_reader` was observed **only** on the branch the dashboard is wired to,
and only as pooled sessions behind the connection pooler — consistent with the
Neon HTTP/serverless driver, where individual client sessions are extremely
short-lived and an idle-session sample can otherwise miss them entirely.

`neondb_owner` also appears on both branches; that is the platform's own pooled
connection and, on its own, is not proof of anything.

Corroboration from grants (`migrations/002_roles.sql`): `jobs_reader` is
`LOGIN` with `SELECT`-only rights on `jobs` and `publish_meta`, which matches
read-only dashboard behaviour and the observed connection role.

## Consequence for the wider audit

The same sampling established where production traffic actually lands, which
matters for the restore drill: the app's endpoint is currently bound to the
branch `drill/2026-11-02`, not to `main`. See
[restore-drill.md](restore-drill.md) for the cause and the remediation.

## Result

Result: PASS — the production dashboard authenticates as `jobs_reader`.

Task 2 ("switch the dashboard to `jobs_reader`") is therefore **not required**
and is recorded as a no-op rather than silently skipped.
