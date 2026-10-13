# Job dashboard (frontend)

Read-only Next.js dashboard for the Neon copy described in docs 13 and 14. All editing stays in the Google Sheet.

## Run locally (against the Neon `dev` branch)
```bash
cd frontend
cp .env.example .env.local     # fill DATABASE_URL (pooled, reader role), DASH_USER, DASH_PASS
npm install                    # creates package-lock.json; commit it
npm run dev                    # http://localhost:3000, browser asks for the Basic Auth login
```
Checks: `npm run typecheck`, `npm test`, `npm run lint`, `npm run build`.

## Before you trust it (O10)
Versions in `package.json` are pinned from memory and were not installed or built where this was written. At scaffold time:
1. Confirm each pinned version exists and is at least two weeks old (`npm view <pkg> time`).
2. Confirm the Next.js major version. This code targets 15 (`middleware.ts`). On Next.js 16 rename it to `proxy.ts` and the exported function to `proxy`.
3. Run `npm run typecheck && npm test && npm run build` and fix what they report.
4. Confirm array parameters work with the Neon driver: the default tier filter passes a JS array as `ANY($1::text[])`. A first list load that works proves it. If it errors, switch that one parameter to a comma-joined string and `string_to_array`.
5. Confirm the three SQL helpers against real data: `to_char(...)` dates, `search @@ websearch_to_tsquery`, and the `skills_matched @> ARRAY[...]` filter.

## Structure
- `middleware.ts`: Basic Auth gate, fails closed. `lib/auth-server.ts` repeats the check inside every page.
- `lib/filters.ts`: URL parameters to a validated `Filters` object (allowlists, clamps).
- `lib/sql.ts`: the only place list SQL is assembled. Every value is a bound parameter; ORDER BY comes from an allowlist.
- `lib/queries.ts`, `lib/db.ts`: all database access, reader role only.
- `lib/format.ts`, `lib/breakdown.ts`: Nairobi-time formatting, deadline notes, safe links, defensive `match_breakdown` parsing.
- `app/`: list (`/`), detail (`/jobs/[id]`), loading, error, not-found, `robots.txt`.

## Notes and decisions
- `robots.txt` is excluded from Basic Auth so crawlers can read "Disallow: /". Everything else needs the login.
- Weak jobs are hidden by default and shown when Weak is ticked in the tier filter. Unticking every tier returns the default tiers.
- No Content-Security-Policy header yet: Next.js inline scripts need a nonce setup. Add one if you want it.
- `DATABASE_URL`, `DASH_USER`, `DASH_PASS` have no `NEXT_PUBLIC_` prefix and are only read in server code.
- Deploy: Vercel project with Root Directory `frontend`. Production uses the `main` Neon branch, Preview and Development use `dev`.
