# Role verification — which role does the production dashboard authenticate as?

- **Date:** 2026-11-02 (UTC); sampling repeated 2026-11-03 (UTC)
- **Project:** `autumn-rain-77812061` (`job-scrapper`), database `neondb`
- **Question (SEC-01):** does the production `DATABASE_URL` authenticate as the
  read-only `jobs_reader`, or as the table owner?
- **Vercel variable inspected:** `DATABASE_URL`, target `production`, type
  `encrypted` (id not recorded here on purpose).
- **Scope:** the deployed production build
  (`job-scraper-iyojajad4-…vercel.app`), sampled on whichever branch its
  read-write endpoint was bound to at the time — `drill/2026-11-02`, not `main`.
  See [Scope and re-sampling](#scope-and-re-sampling).

## How the evidence was obtained

The Vercel UI route in the plan ("open the variable and read the username") was
attempted first, and the Vercel API returns the value of an `encrypted`
variable as redacted — `filter_project_envs` and `get_project_env` expose the
key, target and type but not the decrypted string. No value was ever printed,
copied or stored.

The role was therefore proven the stronger way: **from the database side**, by
watching which role the running dashboard actually opens connections as. That
is direct evidence, whereas reading the variable only proves intent.

The first attempt was a passive sample taken at rest, and it observed only
`neondb_owner`. That is not evidence either way — the serverless driver's
sessions live for milliseconds, and the sampling query itself connects as
`neondb_owner`. So the check was rerun as a **before/after experiment**: sample,
generate traffic, sample again, with the sampler marking its own backend so it
cannot be mistaken for the application.

1. Sampling query. `bool_or(pid = pg_backend_pid())` marks the row that is this
   query's own connection:

   ```sql
   SELECT usename, coalesce(application_name,'') AS app, state, count(*) AS n,
          bool_or(pid = pg_backend_pid()) AS is_sampler
   FROM pg_stat_activity
   WHERE datname = 'neondb'
   GROUP BY 1,2,3 ORDER BY 1,3;
   ```

2. Sample with no application traffic in flight.
3. 20 requests to the live deployment, alternating `/` and `/jobs`. Only `/` is
   database-backed and returned `200` (10 of 10); `/jobs` has no index route and
   returned `404` (10 of 10). The 404s are a route-shape result, not a database
   error, and carry no role evidence.
4. Re-sample. Repeat with a second 20 requests and sample again — 40 requests in
   total, 20 × `200` and 20 × `404`.

## Result of the sampling

| Phase | App requests | `jobs_reader` sessions | `neondb_owner` sessions |
| --- | --- | --- | --- |
| Before any traffic | 0 | **0** | 1 — `is_sampler = true` |
| After 20 requests | 20 | **15** (`pgbouncer`, `idle`) | 1 — still `is_sampler = true` |
| After 40 requests | 40 | **15** (`pgbouncer`, `idle`) | 1 — still `is_sampler = true` |

`jobs_reader` sessions appeared **only after** application traffic, and the sole
`neondb_owner` row is the sampling query itself (`is_sampler = true`,
`state = active`, running this very `SELECT`). There is no owner-role session
serving the application.

The role evidence rests on `/`, the only database-backed route exercised. The
detail route `/jobs/<id>` would open the same reader connection, but it was not
used in this run, so it is not claimed as evidence.

An earlier observation that `main` showed only `neondb_owner` is **not** used as
evidence and is not reproduced here: that branch had no traffic at all, so it
cannot discriminate between roles. The before/after transition above is what
distinguishes them.

`jobs_reader` appears as pooled `pgbouncer` sessions in `idle` state rather than
`active` queries — expected with the Neon serverless driver, where each client
query is short-lived and the pooler keeps the backend warm.

## Corroboration from role attributes and grants

Read live from `pg_roles` on the same branch (2026-11-03):

| Role | `rolcanlogin` | `rolsuper` | `rolcreatedb` | `rolcreaterole` |
| --- | --- | --- | --- | --- |
| `jobs_reader` | true | false | false | false |
| `jobs_publisher` | true | false | false | false |
| `neondb_owner` | true | false | true | true |

`migrations/002_roles.sql` does **not** create these roles and does **not** set
`LOGIN`; it raises an exception if they are absent and then grants `SELECT` only
on `jobs` and `publish_meta`. So the migration is a check on *grant scope*, not
on connection identity — the role attributes above and the `pg_stat_activity`
transition are what establish that the dashboard logs in as `jobs_reader`.

## Scope and re-sampling

The sampling proves which role the **running production build** authenticates
as. At the time of the check that build's read-write endpoint was bound to
`drill/2026-11-02` rather than `main` (cause and remediation in
[restore-drill.md](restore-drill.md)), so the observation is about the
deployment, not about the `main` branch.

The `DATABASE_URL` itself is unchanged by the endpoint reassignment, so the same
credential should carry over — but that is an inference, not an observation.
After the endpoint is moved back to `main` and production is redeployed, repeat
the before/after sample on `main` and record the result here. Until that is
done, the PASS below is scoped to the deployed build.

## Result

Result: PASS — the deployed production dashboard authenticates as
`jobs_reader`, not as the table owner.

Task 2 ("switch the dashboard to `jobs_reader`") is therefore **not required**
and is recorded as a no-op rather than silently skipped. The open item is the
re-sample on `main` after the endpoint move.
