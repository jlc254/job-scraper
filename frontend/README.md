# Job dashboard (frontend)

Public, read-only Next.js dashboard for the Neon copy described in docs 13 and 14. The dashboard opens directly without authentication; all editing stays in the Google Sheet.

## Run locally (against local PostgreSQL)

Start the local database from the repository root and create the dashboard schema:

```bash
docker compose up -d db
docker compose exec -T db psql -U postgres -d jobs_dashboard < migrations/001_init.sql
```

For `npm run dev` on the host, copy `.env.example` to `.env.local` and keep its
`localhost:5433` URL. Then run `cd frontend && npm run dev`. For the complete
Compose stack, run `docker compose up --build`; Compose sets the container URL
to `db:5432` automatically. To use a Neon development branch instead, set
`DATABASE_URL` in `.env.local` to that branch's pooled connection URL.

The app chooses the Neon HTTP driver for `*.neon.tech` URLs and the regular
PostgreSQL driver for local database URLs. Vercel Preview/Development should
use the Neon `dev` branch; Production should use the Neon `main` branch.
Development and test errors include the database error message. Production
shows a generic page and writes the error code/message to server logs; database
URLs and credentials are never logged or sent to the browser.

Checks: `npm run typecheck`, `npm test`, `npm run lint`, `npm run build`.

## Before you trust it (O10)
Versions in `package.json` are pinned from memory and were not installed or built where this was written. At scaffold time:
1. Confirm each pinned version exists and is at least two weeks old (`npm view <pkg> time`).
2. Confirm the Next.js major version before upgrading; this frontend currently uses Next.js 15.
3. Run `npm run typecheck && npm test && npm run build` and fix what they report.
4. Confirm array parameters work with the Neon driver: the default tier filter passes a JS array as `ANY($1::text[])`. A first list load that works proves it. If it errors, switch that one parameter to a comma-joined string and `string_to_array`.
5. Confirm the three SQL helpers against real data: `to_char(...)` dates, `search @@ websearch_to_tsquery`, and the `skills_matched @> ARRAY[...]` filter.

## Structure
- `app/page.tsx`: dashboard list at `/`; no login is required.
- `lib/filters.ts`: URL parameters to a validated `Filters` object (allowlists, clamps).
- `lib/sql.ts`: the only place list SQL is assembled. Every value is a bound parameter; ORDER BY comes from an allowlist.
- `lib/queries.ts`, `lib/db.ts`: all database access, reader role only.
- `lib/format.ts`, `lib/breakdown.ts`: Nairobi-time formatting, deadline notes, safe links, defensive `match_breakdown` parsing.
- `app/`: list (`/`), detail (`/jobs/[id]`), loading, error, not-found, `robots.txt`.

## Notes and decisions
- All dashboard routes are public. `robots.txt` asks crawlers not to index the site; it is not an access control.
- Weak jobs are hidden by default and shown when Weak is ticked in the tier filter. Unticking every tier returns the default tiers.
- No Content-Security-Policy header yet: Next.js inline scripts need a nonce setup. Add one if you want it.
- `DATABASE_URL` has no `NEXT_PUBLIC_` prefix and is only read in server code.
- Deploy: Vercel project with Root Directory `frontend`. Production uses the `main` Neon branch, Preview and Development use `dev`.
