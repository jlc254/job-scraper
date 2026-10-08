# 03. Legal and Responsible Use

Not legal advice. This is the operating policy for the tool.

## Principle
**Technically possible is not the same as permitted.** A site serving HTML to a script does not authorize collection. robots.txt and terms of service are treated as the rule, not an obstacle.

## Source gate (enforced in code)
- `sources.yaml` carries `status`, `verified_on` and `terms_url` per source.
- The runner refuses to start a source whose status is not `verified`.
- For HTML sources the fetcher checks robots.txt (standard-library `urllib.robotparser`, cached per run) before every path and skips disallowed URLs.
- If robots.txt cannot be fetched or parsed, treat the site as disallowed for that run and log it.
- Keyword-search URLs are not fetched where a site disallows them. Use category paths, feeds or APIs instead.

## Permission matrix
| Approach | Typically permitted? | Condition |
|---|---|---|
| Official API with key | Yes | Follow terms, limits, attribution |
| Public feed (RSS/JSON) | Yes | Follow terms, limits, attribution |
| Employer ATS public endpoint | Generally yes | Public, structured, low volume |
| HTML scraping | Only if robots.txt and terms allow | Verified per site and path |
| Browser automation | Only where HTML scraping is allowed and JS rendering is required | Standard, honest browser; no stealth |
| Logged-in scraping | No | Out of scope |
| Bypassing CAPTCHA, fingerprint spoofing, proxy rotation to evade blocks | No | Out of scope |
| Scraping search-engine results | No | Use alerts or official APIs |

If a site blocks us, we stop and use its email alerts. We do not escalate.

## Politeness
- Identifying User-Agent, for example `JobScraper/0.1 (personal job-search tool)`. Adding a contact email is optional and is the owner's own data.
- HTML: at least 3 seconds between requests to the same host, one connection at a time.
- APIs: obey published limits (Remotive at most about 4 requests per day if enabled; Jobicy at most once per hour).
- Honor `429` and `Retry-After`. Never retry aggressively.
- Cache with ETag or Last-Modified where supported.
- One or two runs per day. Job boards do not change faster than that.

## Personal data
| Item | Policy |
|---|---|
| Recruiter names, emails, phone numbers | Not collected. Emails and phone numbers found in descriptions are removed by regex before storage |
| Company name, job title, location | Not personal data. Stored |
| Owner's CV | Stays on the owner's machine. Only `profile.yaml` (skills, titles, preferences) is used |
| Owner's Telegram chat ID and Google service account | Secrets, see doc 08 |

**Kenya:** the Data Protection Act, 2019 and the Office of the Data Protection Commissioner apply to personal data. Because the tool avoids collecting personal data about other people, exposure is minimal. Purely personal use may also fall under an exemption, but the design does not rely on it.

**GDPR:** relevant only if EU residents' personal data were processed. The no-personal-data rule covers this.

## Copyright and attribution
- Store a truncated excerpt (default 1000 characters, set per source by `excerpt_max_chars`, where 0 means store nothing and score from memory), extracted skills and requirements, and the link back. Full text is processed in memory for scoring.
- Always keep `source` and `job_url`. Show the source name in the digest.
- Do not republish or share listings publicly. Sheet access is private to the owner.
- Honor attribution requirements (RemoteOK, Remotive if enabled, others).

## Retention
- Jobs older than 60 days are deleted unless their `application_status` is beyond New.
- Excluded-job audit rows are kept 30 days.
- Logs are kept 30 days (GitHub Actions default retention can be shortened).

## Authentication and sessions
No site logins, no cookies, no stored sessions. Only API keys for official APIs, held as secrets.

## If a source objects
Disable it the same day (`enabled: false`), delete its stored rows on request, and record the change in the verification log.

## Pre-launch checklist
- [ ] Each enabled source has `status: verified`, date and terms link
- [ ] robots.txt checker tested against an allowed and a disallowed path
- [ ] Email and phone scrubbing tested
- [ ] Attribution shown for sources that require it
- [ ] Retention job tested
