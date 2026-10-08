# 02. Source Catalog

Research date: 30 Sep 2026. Everything marked **(verify)** must be confirmed against the official documentation, robots.txt and terms before the adapter is written. Record results in the verification log at the bottom.

## Source gate
A source may be enabled in `config/sources.yaml` only when `status: verified` and one of these holds:
1. It offers an official API or public feed intended for reuse, and we follow its terms and limits.
2. It is an HTML site whose robots.txt allows the specific paths we fetch and whose terms do not prohibit automated access.
3. It is an employer's public job endpoint (Greenhouse, Lever, Ashby and similar) that exposes structured public data.

Everything else is reached only through the site's own email alerts, used manually by the owner.

## Tier A. Public APIs and feeds, no key
| Source | Access | Notes |
|---|---|---|
| Himalayas | Public JSON at himalayas.app/jobs/api (verify) | Cursor pagination, about 20 jobs per page. Good remote coverage. Attribution recommended |
| Jobicy | Public JSON API (verify) | Hourly rate limit, so run at most once per hour. Attribution recommended |
| Arbeitnow | Public JSON API (verify) | Mixed on-site and remote, mostly Europe. No salary field. Low priority |
| RemoteOK | JSON at remoteok.com/api (verify) | Attribution and link back required. First array item is a legal notice, skip it |
| We Work Remotely | RSS by category (verify) | Customer-support category feed is the target |
| Working Nomads | Public JSON feed (verify) | Confirm terms before enabling |
| Remotive | Public JSON at remotive.com/api/remote-jobs | **Retired (D13, closes O3). Do not enable.** Terms require attribution and a link back, recommend at most about 4 requests per day, and forbid resubmitting jobs to other job sites. One third-party project reports the API path is disallowed in robots.txt. It also overlaps Himalayas, We Work Remotely and RemoteOK, so it is not worth the dispute |

## Tier B. Free key required
| Source | Key | Notes |
|---|---|---|
| Adzuna | App ID and App Key, free at developer.adzuna.com | Free within rate limits. Kenya coverage unconfirmed (O2). If unsupported, still useful for South Africa and remote-tagged jobs |
| Jooble | Key by request (verify) | Confirm terms and country coverage |
| Careerjet | Publisher/affiliate ID (verify) | Has Kenya site. Confirm API terms for personal use |
| ReliefWeb | Registered app name (verify) | NGO and humanitarian roles, some support and admin |

## Tier C. Employer job endpoints (structured, public)
| ATS | Endpoint pattern (verify each) |
|---|---|
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` |
| Lever | `api.lever.co/v0/postings/{company}?mode=json` |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{name}` |
| SmartRecruiters | `api.smartrecruiters.com/v1/companies/{id}/postings` |
| Workable | Public account endpoint (verify) |

Rule: a company is added only after its board token returns a valid public response. Candidates to probe (ATS unknown until tested): M-KOPA, Wave, Andela, Cellulant, Jumia, Sendy, Flutterwave, Paystack, Kopo Kopo, Craft Silicon. BPOs and large Kenyan employers (Safaricom, Airtel, Equity, KCB, Teleperformance, TaskUs) usually run their own career sites, so they need a case-by-case permission check.

## Tier D. Kenyan job boards (permission-dependent)
| Board | Findings so far | Plan |
|---|---|---|
| BrighterMonday | Sources disagree: one project says robots.txt blocks bots, another crawled only category paths and treated keyword-search URLs as disallowed | Read robots.txt at runtime. Use only allowed paths. If blocked, use the site's email alerts |
| MyJobMag Kenya | Keyword-search URLs reported as disallowed | Same as above. Check for RSS |
| Fuzu | Reported to have no public RSS | Alerts only unless terms and robots allow |
| Kenyajob.com, MyJobsInKenya, Careerjet Kenya, Corporate Staffing, Career Point Kenya, Jobwebkenya | Not yet checked | Verify robots.txt, ToS, feed availability in Phase 3 |
| Public sector (PSC, Ajira) | Not yet checked | Verify. Public notices are usually low-risk but confirm |

Third-party scrapers for these boards exist on marketplaces. Their existence does not mean the sites permit scraping.

## Tier E. Restricted (alerts only)
LinkedIn, Indeed and Glassdoor prohibit automated scraping and actively block it. Use their native job alerts. Optional Phase 8: a Google Apps Script running inside the owner's own Google account parses labeled alert emails into the Sheet, so no mailbox credentials are stored in GitHub.

Google search results are not scraped. Google Alerts (email or feed) may be added as a low-priority, noisy source.

## Query set
Titles: customer support, customer service, customer care, customer success, customer experience, help desk, service desk, technical support, contact centre, call centre, client services, account support, order support, billing support, collections, onboarding, complaints, retention, support administrator, chat support, email support.

Where an API supports search, run these as separate queries (bounded, deduplicated). Where only category feeds exist, fetch the category and filter locally with the same keywords. Exclusion terms are in `scoring.yaml`.

## Sources that need a key
Keys are held only as secrets (GitHub Secrets and a local `.env`), never in YAML or code.
| Source | Secret(s) | Notes |
|---|---|---|
| Adzuna | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Key travels in the query string, so URLs are logged without it. Record Kenya coverage (O2) |
| Jooble | `JOOBLE_API_KEY` | Proposed name, confirm against the key you were issued |
| Careerjet | `CAREERJET_AFFID` | Publisher ID. Proposed name |
| ReliefWeb | `RELIEFWEB_APPNAME` | Registered app name. Proposed name |

Rules: a keyed source with a missing secret is marked `skipped` for the run and reported, and never fails the run. Each secret is added to doc 09 and `.env.example` with a placeholder. A key that appears in a log or commit is rotated at once.

## Verification order and procedure
Verify in this order and stop Phase 1 once the exit bar in doc 10 is met. Sources not reached stay `pending`.
1. **Batch 1, no key:** Himalayas, We Work Remotely, Jobicy, RemoteOK, Working Nomads, Arbeitnow.
2. **Batch 2, employer endpoints:** Greenhouse, Lever, Ashby, SmartRecruiters, Workable, then probe company board tokens.
3. **Batch 3, free key:** Adzuna (Kenya coverage, O2), Jooble, Careerjet, ReliefWeb.
4. **Batch 4, Kenyan boards and public sector (O1):** BrighterMonday, MyJobMag, Fuzu, PSC, Ajira. A board that fails the source gate moves to `alerts-only`.
5. **Last:** email-alert setup for every `alerts-only` source, plus LinkedIn, Indeed and Glassdoor (Phase 8, O4).

**Five checks per source** (all recorded in the log below):
1. Fetch robots.txt and note whether the paths or endpoints we need are allowed.
2. Read the terms or API terms for automated access, reuse, storage and attribution.
3. Make one real call and confirm the endpoint and response shape.
4. Save that response, personal data removed, as `tests/fixtures/<source>.json`.
5. Record the date, terms link, rate limit and attribution wording.

**Status values:** `pending`, `verified`, `blocked`, `alerts-only`, `retired`. Only `verified` sources can run. The live checks (steps 1 and 3) are run by the owner from a Linux shell, and the output is pasted into the log.

## Verification log (fill in during Phase 1 and 3)
| Source | Date | robots.txt result | ToS reviewed (link) | Access method | Status | Notes |
|---|---|---|---|---|---|---|
| Himalayas | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Jobicy | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| We Work Remotely | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| RemoteOK | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Remotive | 2026-10-01 | not checked | not needed | none | retired (D13) | Overlap with other sources, low request limit, robots.txt conflict reported |
| Adzuna | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture. Needs key. Kenya coverage (O2) to record |
| Greenhouse boards | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| BrighterMonday | | | | | pending | |
| MyJobMag Kenya | | | | | pending | |
| Fuzu | | | | | pending | |
| Working Nomads | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Arbeitnow | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Lever boards | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Ashby boards | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| SmartRecruiters | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Workable | 2026-10-01 | | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture |
| Jooble | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture. Needs key |
| Careerjet | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture. Needs key |
| ReliefWeb | 2026-10-01 | n/a (API) | (owner to attach) | (owner to record) | verified | Owner-confirmed 1 Oct 2026. Attach robots result, terms link, fixture. Needs key |
| PSC / Ajira | | | | | pending | |
