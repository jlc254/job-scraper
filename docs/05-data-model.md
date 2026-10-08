# 05. Data Model

## Job record
| Field | Type | Notes |
|---|---|---|
| job_id | str | Stable: first 12 hex of sha1(source + source_job_id), or of canonical URL if the source has no ID |
| fingerprint | str | sha1 of normalized company + title + location scope (see dedupe) |
| title | str | As posted |
| title_normalized | str | Lowercased, punctuation and level noise removed |
| company | str | As posted |
| company_normalized | str | Lowercased, legal suffixes removed |
| company_domain | str? | From apply URL when available |
| location | str? | Free text as posted |
| country | str? | ISO code when resolvable |
| work_type | enum | remote, hybrid, onsite, unknown |
| employment_type | enum | full_time, part_time, contract, freelance, internship, unknown |
| remote_eligibility | enum | worldwide, africa, east_africa, kenya, timezone_limited, restricted, unclear |
| posting_country_restrictions | list[str] | Extracted phrases such as "US only" |
| timezone_requirement | str? | For example "UTC-5 to UTC+1" |
| language_requirements | list[str] | |
| shift_type | str? | day, night, rotating, unknown |
| salary_min, salary_max | number? | |
| salary_currency | str? | KES, USD and others |
| salary_period | str? | month, year, hour |
| description_excerpt | str | Truncated to the source's `excerpt_max_chars` (default 1000), personal data removed |
| requirements | list[str] | Extracted requirement lines |
| skills_required | list[str] | Canonical skill names |
| skills_preferred | list[str] | |
| experience_level | enum | entry, mid, senior, lead, manager, unknown |
| experience_years_min | int? | |
| education_required | str? | |
| industry | str? | Mapped where possible |
| source | str | Adapter id |
| source_url | str | Board or feed page |
| job_url | str | Canonical link to the posting |
| all_urls | list[str] | Every known URL after merging duplicates |
| source_job_id | str? | |
| date_posted | date? | |
| date_discovered / first_seen / last_seen | datetime | UTC |
| application_deadline | date? | |
| is_active | bool | False when not seen for 7 days |
| status | enum | new, active, expired, excluded |
| match_score | number | 0 to 100 |
| match_tier | enum | top, strong, potential, weak |
| match_breakdown | JSON | Points per factor with reasons |
| skills_matched, skills_missing, transferable | list[str] | |
| recommended_action | str | |
| notified_at | datetime? | Set after digest |
| exclusion_reason | str? | For excluded jobs |

## Google Sheet layout
Tabs: **Jobs**, **Excluded** (30-day audit), **Runs** (one row per run), **Inbox** (email-alert intake).

**Inbox tab.** Written only by the owner's Apps Script, read by the Inbox adapter. Columns: `received_at`, `sender`, `subject`, `job_title`, `company`, `location`, `job_url`, `snippet` (truncated, no personal data), `processed` (set by the runner). The Apps Script never touches the Jobs tab, and no mailbox credentials are stored in GitHub.

Columns are addressed by header name, never by position, so the owner can reorder or add columns.

**System-owned columns (script writes):** job_id, fingerprint, title, company, location, work_type, employment_type, remote_eligibility, salary (formatted), skills_matched, skills_missing, match_score, match_tier, match_breakdown, recommended_action, source, job_url, date_posted, application_deadline, first_seen, last_seen, is_active, notified_at, checklist.

**User-owned columns (script never writes to existing rows):** application_status (dropdown), applied_on, follow_up_date, notes, priority.

New rows are appended. Existing rows only get `last_seen`, `is_active` and rescored fields updated, and only in system-owned columns.

Enumerations: application_status = New, Saved, Applied, Interview, Offer, Rejected, Ignored.

## Deduplication
Checks run in order; the first match wins.
1. **Canonical URL.** Lowercase host, drop fragment, strip tracking parameters (utm_*, fbclid, gclid, ref, source, and similar), remove trailing slash.
2. **Source and source_job_id.**
3. **Fingerprint.** sha1 of company_normalized + title_normalized + location scope (country, or "remote"). Company legal suffixes (ltd, limited, inc, llc, plc, gmbh) and punctuation are removed.
4. **Near-duplicate.** Same company, title similarity at least 90 (rapidfuzz token_set_ratio) and description similarity at least 85 within 30 days.

**Merge policy:** keep the earliest `first_seen`, union `all_urls`, prefer the employer's own domain as `job_url`, keep the richest field values (salary, deadline).

**Reposts:** the same fingerprint returning after more than 30 days is treated as a new posting and flagged "repost".

## Normalization notes
- Titles: remove bracketed text, seniority noise for matching only, and location suffixes.
- Location: map common Kenyan cities and "Remote", "Worldwide", "Africa", "EMEA".
- Salary: parse ranges and currency symbols. Never convert currencies for scoring, only for display if a rate is supplied.
- Dates: relative dates ("2 days ago") converted using the run time.
- Personal data: emails and phone numbers removed from every text field before validation.
