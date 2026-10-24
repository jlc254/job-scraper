# 14. Frontend Dashboard
 
Specification for the Next.js dashboard in `frontend/`. It reads the Neon copy described in doc 13. Written before any code. Status: **design, nothing built**.
 
## Purpose
A faster, clearer view of the jobs the pipeline already finds: better filtering, a 0 to 100 score with the reasons behind it, and an Apply button that opens the posting in a new tab. It is a read-only window. All editing (status, dates, notes) stays in the Google Sheet.
 
## Decisions (add to the log in doc 00)
| ID | Decision | Reason |
|---|---|---|
| D24 | All routes are public. No middleware or authentication is implemented | This is the shipped behavior. Public access republishes scraped listings and exposes any status data in the database; public requests can also wake Neon and consume compute |
| D25 | Next.js (App Router, TypeScript) in `frontend/` inside the `job-scraper` repo. Vercel Root Directory is `frontend` | One repo, two independent halves that meet only at Neon |
| D27 | Almost entirely server components. Filters live in the URL query string | No client state library, bookmarkable views, secrets never reach the browser |
| D28 | Read-only. No forms that write anywhere | Keeps the Sheet as the single place you edit |
 
## Scope
### MVP
- Overview strip: jobs shown, new in the last 7 days, count by tier, count by source, and "data as of" time.
- Job list: search, filters, sort, pagination, score badge, Apply button.
- Job detail page: score breakdown, skills, excerpt, checklist, timestamps, source.
- Loading, empty and error states.
### Not in the MVP
Editing status or notes, bookmarks, CSV export, charts beyond simple counts, multiple users, accounts. Add later only if the MVP proves insufficient.
 
## Pages
### `/` Job list
Each card shows:
| Element | Source column |
|---|---|
| Title, company | title, company |
| Score badge: number plus tier word (Top, Strong, Potential, Weak) | match_score, match_tier |
| Location, work type, eligibility badge | location, work_type, remote_eligibility |
| Salary (only when present) | salary |
| "Posted" and "Found" dates | date_posted, first_seen |
| Deadline note ("closes in 3 days", "closed") | application_deadline |
| Status chip (only when not New) | application_status |
| Repost chip | is_repost |
| Source name | source |
| **Apply** button | job_url |
 
Defaults when the page opens with no filters: hide weak tier, sort by score descending, 25 per page.
 
### `/jobs/[id]` Detail
- Everything on the card.
- **Why this score:** one row per factor (title, skills, location, experience, salary, freshness, industry) with points out of max and the stored reason, built from `match_breakdown.factors`. Show the total and the scoring version.
- **Skills:** matched, partial and missing as labeled chips. Labels carry the meaning, not color alone.
- **Recommended action** and **checklist** (shown with line breaks preserved).
- **Excerpt** as plain text with line breaks preserved. It is a truncated excerpt, so show a "Read the full posting" link to `job_url`.
- Back link that keeps the list's filters.
## Filters and sorting
All filters are URL parameters, validated against allowlists on the server.
| Parameter | Values |
|---|---|
| `q` | free text, searched with Postgres full text on title, company and excerpt |
| `tier` | any of top, strong, potential, weak. Default top, strong, potential |
| `min_score` | 0 to 100 |
| `source` | values present in the data |
| `work_type` | remote, hybrid, onsite, unknown |
| `eligibility` | values present in the data |
| `employment_type` | values present in the data. Low value today: most rows are `unknown` |
| `status` | statuses present in the data |
| `found` | last 1, 7 or 30 days |
| `skill` | a skill name, matched against `skills_matched` |
| `sort` | `score` (default), `newest`, `oldest`, `deadline` (soonest first, jobs without a deadline last) |
| `page` | 1 and up |
 
Filter option lists (sources, statuses and so on) come from a `SELECT DISTINCT` query, so new sources appear automatically. There is deliberately **no experience-level filter**: the Sheet has no such column (doc 13).
 
## Apply button
```tsx
<a href={job.job_url} target="_blank" rel="noopener noreferrer">Apply</a>
```
- Render the button only when `job_url` starts with `http://` or `https://`. The database also enforces this with a CHECK constraint. Keep both.
- `rel="noopener noreferrer"` stops the opened page from controlling the dashboard tab.
- Show the source name next to listings that require attribution.
## Security
| Risk | Control |
|---|---|
| Public exposure of scraped listings and any status data | No access control is implemented; every route is public, so listings can be republished publicly and status data is exposed |
| Credentials in transit | Vercel serves HTTPS only |
| Bots waking Neon and burning free compute | Routes are public, so automated requests can reach the database and consume Neon compute |
| SQL injection | Every value is a bound parameter. Sort column and direction come from an allowlist. `page` and `limit` are clamped (limit never above 50) |
| Secrets in the browser | `DATABASE_URL` has no `NEXT_PUBLIC_` prefix and is used only in server code. The built bundle is searched for it before deploy |
| Scraped text as HTML | Rendered only as text. React escapes it. `dangerouslySetInnerHTML` is forbidden |
| Dashboard modifying data | Not possible: the reader role has `SELECT` only |
| Search engines indexing it | `X-Robots-Tag: noindex, nofollow` header and a `robots.txt` that disallows everything |
| Error leakage | Users see a generic message. Logs carry a request ID, never SQL text, URLs with passwords, or notes |
| Preview deployments reaching production data | Vercel's Neon integration creates a branch named `preview/<git-branch>` for each preview deployment and injects that branch's URL. No static Preview `DATABASE_URL` exists, and `preview.yml` fails closed when the branch is missing. Only Production holds the production URL |
 
There is no `middleware.ts`, `proxy.ts`, `auth.ts` or `auth-server.ts` in the shipped frontend. Do not treat the site as private: deploy and operate it as a public dashboard unless access control is implemented separately.
 
## Data access
- Driver: `@neondatabase/serverless` (`neon()` tagged-template queries are parameterized by default) with the **pooled** connection string and the **reader** role. Alternative is `pg`. Choose at scaffold time and pin the exact version, at least two weeks old (O10).
- One small module, `frontend/lib/db.ts`, holds the connection. One module, `frontend/lib/queries.ts`, holds every query. No SQL anywhere else.
- Queries:
  1. `listJobs(filters)` returns rows and a total count for pagination.
  2. `getJob(id)` returns one row.
  3. `overview()` returns total, new in 7 days, tier counts, source counts and `publish_meta.published_at`.
  4. `filterOptions()` returns distinct sources, statuses, work types, eligibility values and employment types.
- The first request after about 5 idle minutes can be slower because Neon wakes from scale-to-zero. Pages show a loading state, and the query helper retries once on a connection error.
- Overview counts may be cached for a short period (for example 60 seconds) to spare free compute.
## Display rules
- Times are stored in UTC and shown in Africa/Nairobi using `Intl.DateTimeFormat`. Dates without time (`date_posted`, `application_deadline`) are shown as dates.
- "Closes in N days" uses today's date in Africa/Nairobi. A deadline within 3 days gets emphasis, and a past deadline is labeled "closed".
- Tier colors are decoration only. The tier name is always printed.
- Responsive from a phone width up. The list is a single column of cards on small screens, and the filter panel collapses.
- "Data as of {time}" is shown on every list page, so staleness is visible.
- Known limitation (O9): the eligibility badge reflects the source's own region field. Show a small note on the detail page: "Eligibility comes from the source listing. Read the posting before applying."
## Folder layout
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  # list
│   ├── jobs/[id]/page.tsx        # detail
│   ├── loading.tsx  error.tsx  not-found.tsx
│   └── robots.txt/route.ts       # or a static robots file
├── components/                   # JobCard, ScoreBadge, FilterPanel, ScoreBreakdown, SkillChips, Pagination
├── lib/
│   ├── db.ts  queries.ts  filters.ts  format.ts
├── tests/
├── next.config.mjs               # security and noindex headers
├── package.json  package-lock.json
├── tsconfig.json
├── .env.example                  # placeholders only
└── README.md
```
 
## Environment variables
| Name | Where | Value |
|---|---|---|
| `DATABASE_URL` | `frontend/.env.local`, Vercel Production | Pooled Neon string, **reader** role. Local uses the `dev` branch; Production uses `main`. Previews receive a per-deployment `preview/<git-branch>` URL from the Neon integration, so no Preview value is stored |
 
`frontend/.env.local` is git-ignored. `frontend/.env.example` holds the database variable with an empty value.

### Preview environments
- Each pull request gets its own Neon branch, named `preview/<git-branch>` and created by Vercel's Neon integration when the preview deployment is made.
- The integration injects that branch's `DATABASE_URL` into the deployment. Do not add a Preview-scoped `DATABASE_URL` (or `DATABASE_URL_UNPOOLED`) in Vercel, and do not add a `DATABASE_URL_PREVIEW` secret: either would pin every preview to one database. The integration also lists a Preview entry of its own; `verify_vercel_project.sh` recognises it by its `configurationId` (or a marketplace `contentHint` store) and only rejects variables a person added.
- `preview.yml` refuses to deploy when a static preview database URL is configured, and after deploying it checks that the branch exists. A preview whose branch cannot be confirmed is removed rather than left running against an unknown database; removal is retried, and the run fails if the deployment still cannot be removed.
- `.github/workflows/cleanup-neon-preview.yml` deletes `preview/<git-branch>` when the PR closes. `scripts/neon_preview_branch.sh` refuses any name outside `preview/*` and refuses the project's default (production) branch.
 
## Repository changes needed outside `frontend/`
| File | Change |
|---|---|
| `.gitignore` | Add `frontend/node_modules/`, `frontend/.next/`, `frontend/.env*` while keeping `frontend/.env.example` |
| `.github/workflows/ci.yml` | New separate job: `npm ci`, lint, typecheck, test, build, with `working-directory: frontend`. Run only when `frontend/**` changes |
| `.github/dependabot.yml` | Add an `npm` entry for `/frontend` |
| `.pre-commit-config.yaml` | Nothing. gitleaks already scans the whole repo |
| `README.md` and `docs/` | Add docs 13 and 14 to the index table |
 
## Free-tier assessment (verified 10 Oct 2026)
| Service | Allowance | Source | Note |
|---|---|---|---|
| Vercel Hobby | Roughly 100 GB transfer, about 1 million function invocations and a few hours of Active CPU per month. **Personal, non-commercial use only** | [vercel.com/docs/limits](https://vercel.com/docs/limits) | The figures come from secondary summaries because the official page did not render its tables. Confirm them on Vercel's page before relying on them (verify) |
| Neon Free | 1 GB, 100 CU-hours, 5 GB egress per project | [neon.com/pricing](https://neon.com/pricing) | See doc 13 |
| GitHub Actions | 2,000 minutes per month for private repositories on the Free plan | [github.com/plans](https://github.com/plans) | Two daily runs plus publish use a small fraction |
 
A single-user dashboard is far below every limit. Public automated requests can consume Neon CU-hours. This is free within usage limits. It is not guaranteed to stay free.
 
## Testing
 
### Unit tests (Vitest)
| Case | Expectation |
|---|---|
| Filter parser | Unknown parameters ignored. `sort` outside the allowlist falls back to `score`. `page` below 1 becomes 1. `limit` above 50 is clamped. `min_score` outside 0 to 100 is clamped |
| Query builder | Every value is passed as a bound parameter. A search string containing quotes and semicolons produces no SQL change |
| Deadline formatting | Past, today, tomorrow and 3-days-out cases in Africa/Nairobi |
| Apply link guard | `javascript:` and relative URLs are not rendered as links |
| Breakdown parsing | Missing, null or partial `match_breakdown` renders without error |
 
### Integration tests
Run against the Neon `dev` branch, or a local Postgres loaded with the published sample:
- List returns the expected count with default filters (weak hidden).
- Each filter narrows the result as the SQL says.
- Pagination: page 2 contains different rows, and the total is stable.
- Full-text search finds a known title and company.
- Detail page for an unknown id shows not-found, not an error.
### End-to-end checklist (manual, before deploy)
1. `npm run build` succeeds with no warnings about env vars.
2. Confirm list and detail routes are publicly accessible, as documented.
3. Search, each filter, each sort and pagination behave correctly.
4. Apply opens a new tab to the right posting, and the dashboard tab stays put.
5. Detail page shows factor points that add up to the displayed score.
6. Phone-width layout: no sideways scroll, filters usable.
7. Search the built output (`.next/`) for the database password. It must not appear.
8. With the Neon reader URL, an `INSERT` attempt fails (confirms the role).
9. A preview deployment connects to its own `preview/<git-branch>` Neon branch, not production.
## Local-first order of work
1. Complete doc 13 steps 1 to 4 (database, roles, publish against dev).
2. Scaffold `frontend/` with TypeScript, pinning exact versions.
3. Add `lib/db.ts`, `lib/queries.ts`, `lib/filters.ts` with unit tests first.
4. Build the list page, then filters, then the detail page.
5. Run the full checklist locally against `dev`.
6. Create the Vercel project (Root Directory `frontend`), set Production variables, and deploy. Keep the previous deployment available for rollback (Vercel instant rollback, verify).
7. Add the `publish` workflow step (doc 13) and confirm three scheduled runs update the dashboard.
## Rollback and recovery
- Bad frontend deploy: redeploy the previous Vercel build.
- Wrong or stale data: run `python main.py publish` (manual workflow mode `publish`). It rebuilds Neon from the Sheet.
- Neon lost or corrupted: recreate the tables from `migrations/`, then publish. Nothing else is needed.
- Leaked reader URL: reset the role password in Neon, update Vercel, redeploy.
## Open items
| ID | Item | Needed for |
|---|---|---|
| O10 | At scaffold time, confirm the current Next.js major version, the Node version Vercel supports, and pin dependency versions at least two weeks old | Scaffolding |
| O11 | Whether to add a "follow-ups due" panel (needs `applied_on` and `follow_up_date` pushed, see O8 in doc 13) | Phase after MVP |
