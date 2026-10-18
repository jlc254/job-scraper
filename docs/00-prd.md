# 00. Product Requirements Document (PRD)

## Purpose
Find recent customer-care and related job openings in Kenya, East Africa, Africa and global-remote roles open to Kenya-based applicants. Rank them against a transparent profile, notify the owner daily, and track applications.

## Owner profile (summary, no personal identifiers)
About 7 years of customer-facing experience across healthcare, FMCG, pay-TV and public service. Multichannel support (phone, email, WhatsApp), order and account support, payment follow-up, complaint resolution. Tools: HubSpot, Zendesk, Zoho, Dynamics 365, Excel, Google Sheets. Languages: English, Swahili. Diploma in Business Management; Cisco Networking certificate. The full profile lives in `config/profile.yaml`. The CV itself never enters the repository.

## Goals
1. Daily list of new, relevant, Kenya-eligible jobs, delivered by Telegram.
2. Every job scored with a visible breakdown, matched skills, gaps and a recommended action.
3. Google Sheet as the working tracker (status, applied date, follow-up date, notes).
4. Runs free on GitHub Actions; can also run on a laptop.
5. One broken source never stops the run.

## Non-goals
- No automatic applying.
- No logging in to job sites, no cookies or sessions.
- No bypassing CAPTCHAs, rate limits, robots.txt, ToS or bot protection. This excludes anti-detect browsers and stealth fetcher modes.
- No collection of personal data (recruiter names, emails, phone numbers).
- No redistribution or publication of scraped listings.

## Success criteria
| Metric | Target |
|---|---|
| Daily digest delivered | 95% of days, before 07:00 EAT |
| Healthy sources | At least 4 at launch |
| Duplicate jobs in a digest | Under 2% |
| Jobs shown as eligible that are actually region-restricted | Under 10% (measured in manual review) |
| Run time | Under 10 minutes |
| Running cost | 0 USD |

## Decisions log
| ID | Decision | Reason |
|---|---|---|
| D1 | Python 3.12, httpx, feedparser, BeautifulSoup/selectolax | Enough for APIs, feeds and simple HTML |
| D2 | Scrapling used only as an optional parser layer, evaluated in Phase 2. No stealth modes. No Camoufox | Stealth tools bypass bot protection, which is out of scope |
| D3 | Google Sheets is the primary store, behind a storage interface | Free, the owner's requested tracker, GitHub Actions is stateless |
| D4 | Telegram for alerts | Free, instant, needs no server |
| D5 | GitHub Actions (private repo), two runs daily at 06:00 and 16:00 EAT (03:00 and 13:00 UTC); laptop for manual runs | Free, secrets built in. Two runs confirmed by owner 1 Oct 2026 |
| D6 | 100-point transparent scoring with hard filters | Explainable, tunable |
| D7 | No auto-apply | Owner requirement |
| D8 | Strip emails and phone numbers from all stored text | Avoids personal data |
| D9 | Store a truncated description excerpt plus link, not full listings (configurable) | Copyright and privacy |
| D10 | Night and rotating shifts acceptable. Relocation roles allowed, scored lower | Confirmed by owner 1 Oct 2026 |
| D11 | No salary floor until the Phase 4 calibration. Salary recorded when listed and shown in the digest | Confirmed by owner 1 Oct 2026. Revisit after labeling about 30 jobs |
| D12 | Source gate: a source is enabled only after verification (see doc 03) | Technically possible does not mean permitted |
| D13 | Remotive retired (closes O3) | About 4 requests a day, a robots.txt conflict, and its jobs overlap Himalayas, We Work Remotely and RemoteOK |
| D14 | Adapters are found through a registry keyed by `id`. One adapter per source. One adapter per ATS platform, with companies as board tokens in `sources.yaml` | A new source is one file plus one config entry. The runner is never edited |
| D15 | `excerpt_max_chars` is a per-source setting (default 1000, 0 = score from memory, store nothing) | A source whose terms forbid storing descriptions can still be used |
| D16 | Email-alert jobs enter through an `Inbox` tab and an Inbox adapter. The Apps Script writes only to that tab | Alert jobs get the same normalization, dedupe, filters and scoring. Keeps the script out of the Jobs tab |
| D17 | Notifications get a base interface (`notifications/base.py`) like storage | A second channel becomes a drop-in |
| D18 | Phase 1 closes on a minimum bar: at least 4 sources verified with a dated log entry and a fixture each. Others stay `pending` or `alerts-only` | Matches the "4 healthy sources at launch" target. Phase 2 needs only 1 to 2 |
| D28 | Fetching is shared. Everything a person owns is per profile: profile and scoring files, Sheet, Telegram chat, digest title, Neon rows | Sources are polite and rate-limited, so they are fetched once. A Sheet is shared per file, so two people on one Sheet would see each other's notes |
| D29 | Profiles are listed in `config/profiles.yaml`. With no file, the old single-profile setup runs unchanged. A profile `id` is permanent | Backward compatible. The id is stored in Neon and in dashboard links |
| D30 | The operator is the first profile in the file. Its Sheet holds source-health history and it alone receives source-health alerts. Other people still see the RUN line in their digest | Alerts about broken adapters are the owner's job, not the second person's |
| D31 | Neon rows are keyed `(profile, job_id)`. `publish_meta`, the row-count guard and the stale-row delete are all per profile | One profile publishing or failing can never delete another's rows |
| D32 | The dashboard has no login (owner's decision). A profile switcher selects the view through `?profile=` | See "Dashboard without a login" for what this exposes |
| D33 | Rows of a profile that is no longer enabled are pruned from Neon, but only on a full publish where every profile published cleanly | A failed Sheet read or `--only` run must never delete data |
| D34 | Location points stay at the defaults, so on-site Nairobi (20) and other Kenyan cities (16) still score for both profiles | Owner's decision |
| D35 | Himalayas treats `EMEA` as `unclear`, like Jobicy and We Work Remotely. This changes the first profile's output too | Doc 06 says EMEA is scored, not excluded. The three adapters disagreed |
| D36 | `skills.py` and `explain.py` were not reviewed and are not changed. The second profile's YAML avoids risky synonyms, and diagnostic tests check how the real extractor behaves | Safest choice without seeing them |
| D37 | Scoring and profile models reject unknown keys, and industry keys are lowercased | The second profile's files had seven blocks that were silently ignored |
| D38 | The `postgres` storage backend supports one profile only | See "Not changed" |

## Open items
| ID | Item | Needed for |
|---|---|---|
| O1 | Verify BrighterMonday, MyJobMag, Fuzu and other Kenyan boards: robots.txt, ToS, feeds | Phase 3 |
| O2 | Confirm whether Adzuna covers Kenya (country list) | Phase 2/3 |
| O3 | ~~Confirm Remotive robots.txt~~ Closed 1 Oct 2026: Remotive retired (D13) | n/a |
| O4 | Choose approach for LinkedIn/Indeed/Glassdoor alerts (manual, or Apps Script inside owner's Google account) | Phase 8 |
| O5 | ~~Digest time~~ Closed 1 Oct 2026: runs at 06:00 and 16:00 EAT (D5) | n/a |
| O6 | Telegram bot exists and the service account is created. Still to do: create the Sheet with tabs Jobs, Excluded, Runs, Inbox, share it with the service account as Editor, and set the GitHub secrets (see doc 09) | Phase 2 |
