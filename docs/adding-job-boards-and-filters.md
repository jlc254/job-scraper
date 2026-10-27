# Adding Job Boards and Job Filters

Yes, you can add both. Most changes to **filters** need only a config edit. Adding a **new job board** needs one new file of about 60 to 100 lines,
unless it is another company on Greenhouse or another We Work Remotely category feed, which are config-only.

**Contents**
- [0. Quick answers](#0-quick-answers)
- [Part A. Job filters](#part-a-job-filters)
- [Part B. Other job boards](#part-b-other-job-boards)
- [Part C. Checklists](#part-c-checklists)
- [Part D. FAQ](#part-d-faq)

> Every code recipe in this guide was tried against the project's real filter, scoring and model code before I wrote it down. They have **not** been run against live websites or your Sheet, because I have no internet access here.

---

## 0. Quick answers

| I want to... | How | Code change? |
|---|---|---|
| Block a phrase, scam wording, or a job title | Edit `filters:` in `config/scoring.yaml` (A2) | No |
| Block specific **companies** | New filter option (recipe A4) | Small |
| Block jobs whose text mentions something ("night shift", "unpaid") | New filter option (recipe A4) | Small |
| Prefer or avoid something without hiding it | Soft scoring in `profile.yaml` / `scoring.yaml` (A3) | No |
| Hide jobs below a salary | Not available as a hard filter (the salary floor only lowers the score). Build it (A5) | Small |
| Search a different type of job | Change keywords, titles and skills (A7) | No |
| Read another company's Greenhouse board | Add it under `boards:` (B3) | No |
| Read another We Work Remotely category | Add its feed under `feeds:` (B3) | No |
| Read a site with a public JSON API or RSS feed | New adapter file (B6) | Yes, one file |
| Read a site that needs an API key | New adapter + a GitHub secret (B8) | Yes |
| Read a Kenyan board with no API | Only if its `robots.txt` and terms allow. New adapter and an HTML parser (B8) | Yes |
| Read LinkedIn, Indeed or Glassdoor | **No.** Their terms forbid scraping. Use their email alerts (not built yet) | n/a |

---

# Part A. Job filters

## A1. How filtering works

There are two different tools. Pick the right one.

| | Hard filter | Soft scoring |
|---|---|---|
| Effect | The job is **removed** and never reaches you | The job stays; its **score** goes up or down |
| Use for | "Never show me this" (scams, wrong region, blocked companies) | "I would rather have this" (titles, skills, industries) |
| Where | `src/jobscraper/matching/filters.py`, settings in `scoring.yaml` under `filters:` | `profile.yaml` and `scoring.yaml` |
| Visible afterwards | `Excluded` tab, the `Excluded: N (...)` line in the run report, `Dash_Excluded` | Score breakdown in the Sheet and in `brief` |

Hard filters run in this fixed order, and the **first** one that matches wins and is the recorded reason:

1. `region_restricted` (source says the job is for other countries, or a phrase like "US residents only")
2. `expired` (deadline already passed)
3. `scam_pattern`
4. `excluded_title`
5. `off_topic` (no support keyword in the title or the first 300 characters)
6. `too_old` (posted more than 30 days ago, unless a deadline is still ahead)

What happens to an excluded job: it is written once to the `Excluded` tab with its reason, it is never stored in `Jobs`, never scored, never notified.
On later runs it is recognised by its row in `Excluded` and skipped silently. Rows stay 30 days.

## A2. Change filters with config only

Open `config/scoring.yaml` and use the `filters:` block.

| Key | Type | Default | What it does |
|---|---|---|---|
| `region_restricted_patterns` | list of regex | US/UK/EU/Canada-only phrases | Excludes jobs whose text matches (case-insensitive) |
| `scam_patterns` | list of regex | registration fee, pay to apply, commission only, WhatsApp-only apply... | Same, reason `scam_pattern` |
| `excluded_title_patterns` | list of regex | telemarketer, telesales, sales rep, business development | Matches the **title** only |
| `support_keywords` | list of words | customer support, help desk, call centre... | A job needs one of these in its title or opening text, or it is `off_topic` |
| `max_age_days` | number | 30 | Older postings are `too_old` |
| `offtopic_chars` | number | 300 | How much of the opening text is searched for a support keyword |

### The one thing that surprises people: a list REPLACES the default list

If you write `scam_patterns:` in your file with one pattern, you lose all the built-in ones. To **add** one, copy the defaults first. This prints them ready to paste
(run from the project folder with your environment active):

```bash
PYTHONPATH=src python -c "
from jobscraper.matching.settings import DEFAULT_SCAM_PATTERNS as d
print('\n'.join('    - ' + chr(39) + x.replace(chr(39), chr(39)*2) + chr(39) for x in d))"
```

Swap `DEFAULT_SCAM_PATTERNS` for `DEFAULT_REGION_PATTERNS`, `DEFAULT_EXCLUDED_TITLES` or `DEFAULT_SUPPORT_KEYWORDS` for the other lists. Then paste under `filters:` and add yours at the end:

```yaml
scoring_version: 2          # raise it whenever you change scoring or filters, so old scores stay explainable
filters:
  scam_patterns:
    - 'registration fee'
    - 'processing fee'
    # ...the rest of the defaults you pasted...
    - 'visa sponsorship fee'          # your addition
  max_age_days: 21
```

Use single quotes in YAML so backslashes in regular expressions stay literal. I tested this exact round trip: pasted defaults plus one addition load as 11 patterns with the defaults intact.

**Regex tips.** Matching ignores capital letters. Use `\b` at a word edge (`\bunpaid\b`), escape dots (`u\.s\.`), and keep patterns specific. A broad pattern like `us only` would also catch "email us only if..."; the built-in patterns treat `US`, `UK`, `EU` as case-sensitive for that reason. Try a pattern before trusting it:

```bash
python -c "import re; print(bool(re.search(r'\bunpaid\b', 'Unpaid internship', re.I)))"
```

> **Leftover option:** a `keywords:` setting under a source in `sources.yaml` is accepted but **does nothing** any more. Do not rely on it.

## A3. Soft preferences (no code)

| You want | Edit | Example |
|---|---|---|
| Prefer certain job titles | `profile.yaml` `titles:` strong / potential / stretch | Add "Client Success Associate" under `strong` |
| Value or lack certain skills | `profile.yaml` `skills:` and `partial_skills:`; `scoring.yaml` `skill_dictionary:` | A skill must exist in `skill_dictionary` before it can be detected in postings |
| Prefer or avoid industries | `profile.yaml` `preferred_industries` / `avoided_industries`, with matching words in `scoring.yaml` `industry_keywords:` | `avoided_industries: [bpo]` gives those jobs 0 of 5 industry points |
| Penalise on-site abroad | `scoring.yaml` `location:` | `other_international: 0` |
| Treat unknown eligibility more harshly | `scoring.yaml` `location:` | `remote_unstated: 5`, `unknown: 5` |
| Weight seniority | `scoring.yaml` `experience:` | `senior_lead: 3`, `manager_director: 0` |
| Reward salary | `profile.yaml` `salary_floor: {amount: 800, currency: USD, period: month}` | A listed salary below the floor scores 2 of 10 instead of 10. It does **not** hide the job |
| Be stricter or looser overall | `scoring.yaml` `tiers:` | Raise `top` from 85 to 88 |

Weights must stay within the design: title 25, skills 25, location 20, experience 10, salary 10, freshness 5, industry 5. Re-run `python main.py calibrate` after changing them.

## A4. Add a new kind of hard filter (recipe)

The six built-in filter types cover most needs. If you want a new **kind**, such as a company blocklist, add a setting and a check. This recipe adds two options
(`excluded_companies` and `excluded_text_patterns`). It touches 2 files, plus tests. Once done, the new reason shows up automatically in the `Excluded` tab, the run report and the dashboard. No other file changes.

**Step 1.** `src/jobscraper/matching/settings.py`, class `FilterSettings`. Add two lines:

```python
class FilterSettings(BaseModel):
    ...
    excluded_companies: list[str] = Field(default_factory=list)  # new
    excluded_text_patterns: list[str] = Field(default_factory=list)  # new
    max_age_days: int = 30
    offtopic_chars: int = 300
```

**Step 2.** `src/jobscraper/matching/filters.py`. Import the company normalizer, prepare the data in `__init__`, and add the checks:

```python
from jobscraper.parsers.names import normalize_company        # new import

class JobFilters:
    def __init__(self, cfg: FilterSettings, today: date) -> None:
        ...
        self._companies = {normalize_company(c) for c in cfg.excluded_companies if c.strip()}   # new
        self._text = _compile(cfg.excluded_text_patterns)                                       # new

    def check(self, job: Job) -> Exclusion | None:
        text = f"{job.title}\n{job.scoring_text}"
        ...region checks stay first...
        if job.company_normalized in self._companies:                        # new, after the region checks
            return Exclusion("blocked_company", job.company)
        if job.application_deadline is not None and job.application_deadline < self._today:
            return Exclusion("expired", job.application_deadline.isoformat())
        for pattern in self._text:                                           # new, before the scam checks
            hit = pattern.search(text)
            if hit:
                return Exclusion("excluded_text", _snippet(hit))
        ...scam, title, off-topic and age checks continue as before...
```

Company names are compared after normalizing (lowercase, punctuation and "Ltd/Inc/PLC" removed), so `Evil Corp` also blocks `EVIL CORP Ltd.`.

**Step 3.** Use it in `config/scoring.yaml`:

```yaml
filters:
  excluded_companies:
    - Evil Corp
    - Quick Cash Recruiters
  excluded_text_patterns:
    - '\bnight shift\b'
    - '\bunpaid\b'
```

These two keys are new and **add** to behaviour: they default to empty, so nothing else is replaced.

**Step 4.** Add tests to `tests/test_matching.py` (it already has helpers `job(...)`, `TODAY`):

```python
def test_company_blocklist_ignores_legal_suffixes():
    f = JobFilters(FilterSettings(excluded_companies=["Evil Corp"]), TODAY)
    verdict = f.check(job(company="EVIL CORP Ltd."))
    assert verdict is not None and verdict.reason == "blocked_company"
    assert f.check(job(company="Good Corp")) is None


def test_text_patterns_exclude_matching_postings():
    f = JobFilters(FilterSettings(excluded_text_patterns=[r"\bnight shift\b"]), TODAY)
    assert (
        f.check(job(scoring_text="Customer support. Night shift only.")).reason == "excluded_text"
    )
```

Run `pytest tests/test_matching.py`. What I verified: with these edits, `EVIL CORP Ltd.` is blocked, "Night shift" and "unpaid" are caught, a clean job passes, and the defaults of the new options are empty.

**Order matters.** Where you put the check decides which reason is recorded when several apply, and cheap, specific checks should come first.

## A5. Other filter ideas

A filter can look at these fields of a job: `title`, `company`, `company_normalized`, `location`, `country`, `work_type`, `employment_type`, `remote_eligibility`,
`posting_country_restrictions`, `salary_min`, `salary_max`, `salary_currency`, `salary_period`, `experience_level`, `date_posted`, `application_deadline`, `source`, and the full scrubbed text in `scoring_text`.

| Idea | Approach | Careful about |
|---|---|---|
| Hard minimum salary | Add `min_salary: {amount, currency, period}` to `FilterSettings`; exclude only when a salary is listed, the currency and period match, and it is below. Reuse the comparison logic in `Scorer._salary` | Most jobs list no salary. Excluding on "unlisted" would remove nearly everything. Mixed currencies are never compared |
| Exclude certain countries | Check `job.country` against a list | `country` is only filled when the location text names a known country |
| Exclude by employment type | Check `job.employment_type` (for example `internship`) | Many sources do not give it, so it is often `unknown` |
| Cap on years of experience | Import `years_asked` from `jobscraper.matching.scorer` and test the text | It only finds a number next to the word "experience" |
| Limit to one source | Do **not** write a filter. Disable the others in `sources.yaml` | |
| Exclude jobs from only one source | Add a hard filter that checks `job.source`. Do **not** return `None` from an adapter's `to_job` for this | An adapter that returns `None` counts as a parse failure. Above 30% of records, the source is marked `degraded` and triggers health alerts |

## A6. After you change a filter

- **Old jobs are not re-judged.** Filters run on jobs fetched in the current run. A job already in `Jobs` is left alone even if it would now fail.
- **Loosening a filter** does not bring back jobs already in `Excluded`. They stay excluded until their row ages out (30 days). To reconsider one now, **delete its row from the `Excluded` tab**; it is evaluated again on the next run if the site still lists it.
- **Try it before you rely on it:** `python main.py run --dry-run` shows the counts, for example `Excluded: 9 (5 region-restricted, 4 off-topic)`. To see the actual excluded jobs: run once with `--storage sqlite --no-notify`, then `python main.py dashboard --storage sqlite --export output/csv` and open `Dash_Excluded.csv`.
- **Review weekly:** the `Excluded` tab is where over-strict filters show up.
- **Change `scoring_version`** whenever you change scoring or filters.

## A7. Searching a different type of job entirely

The project is tuned for customer care. For another family (for example data entry or sales), change these together, or good jobs will be thrown out as `off_topic`:

1. `filters.support_keywords` in `scoring.yaml` (the words a job must contain). Remember this list replaces the default.
2. `profile.yaml` `titles:` (strong, potential, stretch) and `skills:`.
3. `scoring.yaml` `skill_dictionary:` (the skills the program can detect in postings).
4. `excluded_title_patterns` (for example, "sales representative" is excluded by default and would be wrong for a sales search).
5. Re-run `calibrate` on about 30 real jobs.

---

# Part B. Other job boards

## B1. What can be added

The program reads a site only in ways the design allows:

| Allowed | Not allowed (and not possible in this program) |
|---|---|
| An official API or public feed meant for reuse | Logging in to any site, cookies, stored sessions |
| An employer's public job-board endpoint (Greenhouse, Lever, Ashby...) | Getting around CAPTCHAs, rate limits, `robots.txt`, terms or bot protection |
| An HTML page **only if** its `robots.txt` allows that path **and** its terms do not forbid automated access | Stealth browsers, proxy rotation, spoofed fingerprints |
| | Scraping search-engine results; scraping LinkedIn, Indeed or Glassdoor |

"Technically possible" is not "permitted". If a site blocks you, you stop and use its email alerts.

## B2. What you can add, and what it takes

Config only, no code:

| Addition | Where |
|---|---|
| Another company on Greenhouse | `boards:` under `greenhouse` in `sources.yaml` |
| Another We Work Remotely category | `feeds:` under `weworkremotely` |
| A narrower Jobicy query | `query_params:` under `jobicy` |
| More or fewer pages per run | `max_pages` and `page_size` on a source |

New adapter needed. These were reviewed in the design documents; **none has a reader yet**, and every detail below is from the design notes and still to be confirmed with `sources check`:

| Site | Access | Key | Notes from the design documents |
|---|---|---|---|
| RemoteOK | JSON at `remoteok.com/api` | No | Attribution and link back required. The first item in the list is a legal notice and must be skipped |
| Working Nomads | Public JSON feed | No | Confirm terms before enabling |
| Arbeitnow | Public JSON API | No | Mostly Europe, no salary field, low priority |
| Lever | `api.lever.co/v0/postings/{company}?mode=json` | No | One adapter for every company; companies are tokens in config |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{name}` | No | Same pattern as Lever |
| SmartRecruiters | `api.smartrecruiters.com/v1/companies/{id}/postings` | No | Same pattern |
| Workable | A public account endpoint | No | Endpoint needs confirming |
| Adzuna | Free API | App ID and App Key | Kenya coverage was never confirmed. The key travels in the web address, which the program keeps out of logs |
| Jooble | API | Key by request | Confirm terms and country coverage |
| Careerjet | API | Publisher ID | Has a Kenya site. Confirm terms for personal use |
| ReliefWeb | API | Registered app name | NGO and humanitarian roles |
| BrighterMonday, MyJobMag, Fuzu, PSC, Ajira | HTML pages | No | Status `pending`. Sources disagree about their `robots.txt`; keyword-search URLs are reported as disallowed. Category paths only, if at all. Otherwise email alerts |

Companies worth probing on Greenhouse (the design notes say their platform is unknown until tested): M-KOPA, Wave, Andela, Cellulant, Jumia, Sendy, Flutterwave, Paystack, Kopo Kopo, Craft Silicon.
Big employers such as Safaricom, Airtel, Equity, KCB, Teleperformance and TaskUs usually run their own career sites, so each needs its own permission check.

## B3. Config-only additions

**Another Greenhouse company.** Find the board token in the company's careers link (`boards.greenhouse.io/<token>`), then test it returns JSON:

```bash
curl -s -A "JobScraper/0.1 (personal job-search tool)" "https://boards-api.greenhouse.io/v1/boards/<token>/jobs" | head -c 300
```

Add only tokens that return a valid response:

```yaml
  greenhouse:
    enabled: true
    status: verified
    verified_on: 2026-10-05
    terms_url: https://www.greenhouse.com/legal      # the page you reviewed
    boards:
      - {token: examplecorp, name: Example Corp}      # name is shown in the digest
      - othercorp                                     # a bare token also works; the name defaults to the token
```

A wrong token marks just that board failed and the source `partial`. Other boards still run, and a third bad run in a row raises the source-health alert.

**We Work Remotely feeds:** each URL under `feeds:` is one request, and the adapter falls back to the customer-support category when the list is empty. Two source ids share the parser: `weworkremotely` keeps the single support feed (it is in the support profile's allowlist), and `weworkremotely_categories` carries the widened set for the community profile:

```yaml
  weworkremotely:
    feeds:
      - https://weworkremotely.com/categories/remote-customer-support-jobs.rss
  weworkremotely_categories:
    feeds:
      - https://weworkremotely.com/categories/remote-customer-support-jobs.rss
      - https://weworkremotely.com/remote-jobs.rss
      - https://weworkremotely.com/categories/remote-programming-jobs.rss
      - https://weworkremotely.com/categories/remote-product-jobs.rss
      - https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss
      - https://weworkremotely.com/categories/remote-design-jobs.rss
      - https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss
      - https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss
```

This only works for feeds on that same site with the same "Company: Title" format. The same ad often appears in two feeds; it is merged by guid, so the extra feeds cost requests, not duplicate rows.

Two ids per board is the general pattern when one set of feeds should reach only one profile: add a subclass with its own `id` (like `WeWorkRemotelyCategoriesAdapter`), give it the wider `feeds:`, and name it in that profile's `sources:` allowlist. A single id cannot be split, because fetching is shared by every profile in the run.

**Jobicy:** `count` rises to the API's observed maximum of 100 (`query_params: {count: 100}`); the adapter sends one request per run, as their guidance requires. `geo`, `industry` or `tag` also go under `query_params:`, but a single industry **narrows** the feed — read the allowed slugs from `https://jobicy.com/api/v2/remote-jobs?get=industries` first.

**Himalayas:** the API only offers `limit`/`offset` pagination, so breadth comes from `max_pages` (capped at 20). The shipped `max_pages: 10` with `page_size: 20` is 200 ads in 10 requests.

## B4. The permission check (the "source gate")

The program refuses to run a source unless `enabled: true` **and** `status: verified`. Earn that status honestly:

1. **Pick the route.** Official API or feed meant for reuse, or an employer's public job endpoint, or an HTML page whose rules allow it. Nothing else.
2. **`robots.txt`:** fetch it and note whether the paths you need are allowed. For an HTML source, an unreadable `robots.txt` counts as "no".
3. **Terms:** read the terms or API terms for automated access, reuse, storage and attribution. Note the rate limit.
4. **One real call:** confirm the address and the response shape.
5. **Save a sample** with personal data removed (B5).
6. **Record** the date, terms link, access method, rate limit and attribution wording in your verification log (design document 02), and set `verified_on` and `terms_url` in `sources.yaml`.

Also keep to these house rules: an identifying User-Agent, at least 3 seconds between requests to an HTML host, obey published limits and `Retry-After`, one or two runs a day,
no recruiter names, emails or phone numbers stored (the program scrubs them), and only a truncated description excerpt plus the link stored. If a site's terms forbid storing descriptions,
set `excerpt_max_chars: 0` on that source: the program then scores from memory and stores nothing. If a site asks for removal, disable it the same day and delete its rows.

## B5. Get a sample before you write anything

```bash
curl -s -A "JobScraper/0.1 (personal job-search tool)" "https://exampleboard.com/robots.txt"
curl -s -A "JobScraper/0.1 (personal job-search tool)" "https://api.exampleboard.com/v1/jobs?per_page=5" -o sample.json
```

Open `sample.json`, delete any emails and phone numbers, and keep a handful of records. This sample shows you the real field names. **If you would rather not write the adapter yourself, send me the sample and the site's terms link and I will write it.**

## B6. Write the adapter

Create `src/jobscraper/scrapers/exampleboard.py`. This is a working template for a site with a JSON API (a made-up site, `exampleboard`). Replace the names, the address and the field names with your site's. I ran this exact code through the project's filters and scorer against sample records.

```python
"""ExampleBoard adapter (template). Replace the names, URL and field mapping with the real site's."""

from __future__ import annotations

from typing import Any

from jobscraper.models import Job, RawJob, RemoteEligibility, WorkType, make_job_id
from jobscraper.parsers.names import geo_eligibility
from jobscraper.parsers.text import clean_str, html_to_text, parse_date, safe_http_url, truncate
from jobscraper.scrapers.base import Adapter
from jobscraper.scrapers.registry import register
from jobscraper.utils.errors import SchemaError
from jobscraper.utils.http import HttpClient
from jobscraper.utils.pii import scrub_pii

API_URL = "https://api.exampleboard.com/v1/jobs"
SOURCE_URL = "https://exampleboard.com/jobs"
MAX_TEXT_CHARS = 20_000


@register
class ExampleBoardAdapter(Adapter):
    id = "exampleboard"
    display_name = "ExampleBoard"
    allowed_hosts = frozenset({"api.exampleboard.com"})

    def fetch(self, client: HttpClient) -> list[RawJob]:
        raws: list[RawJob] = []
        for page in range(1, self.config.max_pages + 1):
            payload: Any = client.get(
                API_URL, params={"page": page, "per_page": self.config.page_size}
            ).json()
            items = payload.get("results") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                raise SchemaError("ExampleBoard response has no 'results' list")
            raws.extend(
                RawJob(source=self.id, data=item) for item in items if isinstance(item, dict)
            )
            if len(items) < self.config.page_size:
                break
        return raws

    def to_job(self, raw: RawJob) -> Job | None:
        data = raw.data
        title = clean_str(data.get("title"))
        company = clean_str(data.get("company"))
        job_url = safe_http_url(data.get("url"))
        if title is None or company is None or job_url is None:
            return None
        raw_id = data.get("id")
        source_job_id = str(raw_id) if isinstance(raw_id, int | str) and str(raw_id) else job_url
        location = clean_str(data.get("location"))
        remote = data.get("remote") is True
        text = scrub_pii(html_to_text(clean_str(data.get("description_html")) or ""))[
            :MAX_TEXT_CHARS
        ]
        # "unclear" is the safe default: a plain "Remote" must not be treated as a restricted region.
        # Use default="restricted" ONLY if the field is a list of regions the job is open to
        # (as Jobicy's jobGeo is). Then also record the countries so the Excluded tab can show them.
        eligibility = geo_eligibility(location, default="unclear") if remote else "unclear"
        return Job(
            job_id=make_job_id(self.id, source_job_id),
            title=title,
            company=company,
            job_url=job_url,
            source=self.id,
            source_url=SOURCE_URL,
            source_job_id=source_job_id,
            location=location,
            work_type=WorkType.REMOTE if remote else WorkType.UNKNOWN,
            remote_eligibility=RemoteEligibility(eligibility),
            posting_country_restrictions=[location]
            if eligibility == "restricted" and location
            else [],
            description_excerpt=truncate(text, self.config.excerpt_max_chars),
            date_posted=parse_date(data.get("posted_at")),
            first_seen=self.now,
            scoring_text=text,
        )
```

### What each part does

| Part | Meaning |
|---|---|
| `id` | The name used in `sources.yaml`. **Must match exactly** |
| `display_name` | Shown in the digest and dashboard |
| `allowed_hosts` | The **only** host(s) this adapter may contact. The client refuses everything else |
| `fetch(client)` | Gets the raw records. Use only the `client` you are given: it supplies timeouts, retries, politeness and the safety checks |
| `to_job(raw)` | Turns one raw record into a `Job`, or returns `None` if it is unusable. No network access here |
| `@register` | Adds it to the registry so the runner can find it |

### Filling in a Job

| Field | Required | How |
|---|---|---|
| `title`, `company`, `job_url` | **Yes** | Missing or invalid means the record is dropped and counted. `safe_http_url` rejects relative links such as `/jobs/5`, so add the site's base address first |
| `job_id` | Yes | `make_job_id(self.id, source_job_id)`. Use the site's own id. It must be **stable between runs**, or every run will look like new jobs. Fall back to the URL |
| `source`, `source_url`, `source_job_id`, `first_seen` | Yes | As in the template. `first_seen` is always `self.now` |
| `location` | Recommended | The text as posted |
| `work_type` | Recommended | `WorkType.REMOTE`, `HYBRID`, `ONSITE` or `UNKNOWN` |
| `remote_eligibility` | Recommended | `worldwide`, `africa`, `east_africa`, `kenya` count fully (20 location points). `unclear` is scored 10 with an "eligibility unconfirmed" flag. `restricted` means **the job is excluded** |
| `posting_country_restrictions` | If restricted | The countries listed, so the `Excluded` tab shows why |
| `date_posted`, `application_deadline` | Optional | `parse_date` reads unix seconds or milliseconds, ISO dates, and RSS dates |
| `salary_min`, `salary_max`, `salary_currency`, `salary_period` | Optional | Period is `month`, `year` or `hour`. Never convert currencies |
| `employment_type`, `experience_level` | Optional | The enums in `jobscraper.models` |
| `description_excerpt` | Yes | `truncate(scrubbed_text, self.config.excerpt_max_chars)` |
| `scoring_text` | Yes | The full scrubbed text (cap 20,000 characters). Kept in memory for filters and scoring, **never stored** |

Do not set the fingerprint, normalized names, country, scores or tiers. Those are filled in after your adapter returns.

**The eligibility trap.** The helper `geo_eligibility(text, default=...)` reads a region such as "Anywhere", "Africa", "USA". Use `default="unclear"` unless the site's location field is
**strictly a list of regions the job is open to** (like Jobicy's). With `default="restricted"`, a plain "Remote" is read as a closed region and the job is **excluded**. I tested this: "Remote" gives `restricted` with that default and `unclear` with the safe one.

### Helpers you can import

| Helper | From | Use |
|---|---|---|
| `clean_str`, `safe_http_url`, `html_to_text`, `unescape_then_text`, `truncate`, `parse_date` | `jobscraper.parsers.text` | Tidy text, accept only absolute http(s) links, strip HTML (use `unescape_then_text` when the feed escapes its HTML, as Greenhouse does), cut to length, read dates |
| `scrub_pii` | `jobscraper.utils.pii` | Removes emails and phone numbers. **Always apply it** to descriptions |
| `geo_eligibility` | `jobscraper.parsers.names` | Region text to an eligibility value |
| `make_job_id` | `jobscraper.models` | Stable id |
| `SchemaError` and friends | `jobscraper.utils.errors` | Signal a problem with the whole response |

### Rules every adapter follows

1. Contact only hosts listed in `allowed_hosts`, over HTTPS, and only through the `client` you are given. Never import `httpx` or `requests` yourself.
2. Never write to storage, send messages, or read secrets other than your own key.
3. `to_job` is a pure function of the record and the config.
4. Return `None` for an unusable record. If the **whole response** has the wrong shape, raise `SchemaError`: the source is marked failed and the others keep running.
5. Let `BlockedError` and `RateLimitedError` pass through untouched. For multi-part sources (several companies, several feeds), catch other `FetchError`s per part, add a note to `self.partial_errors`, and raise only if every part failed (copy `greenhouse.py`).
6. Treat all scraped text as untrusted: strip HTML, scrub it, never use it in a command or template.
7. Keep it under about 150 lines, with type hints (`mypy` runs in strict mode in CI).
8. **Do not use `to_job` to filter jobs you do not want.** Every `None` counts as a parse failure; above 30% the source is marked `degraded`. Use a hard filter (Part A) instead.

## B7. Register, configure, check, test, enable

1. **Create** the file (B6).
2. **Register it:** add the module to the import line in `src/jobscraper/scrapers/__init__.py`:
   ```python
   from jobscraper.scrapers import exampleboard, greenhouse, himalayas, jobicy, weworkremotely  # noqa: F401
   ```
   Without this, the source fails with "no adapter registered for this id".
3. **Add its config**, switched off and unverified at first:
   ```yaml
     exampleboard:
       enabled: false
       status: pending
       terms_url: https://exampleboard.com/terms
       max_pages: 2
       page_size: 50
       excerpt_max_chars: 1000
   ```
4. **Check it live** (works on `pending` sources; refuses `blocked`, `alerts-only` and `retired` ones):
   ```bash
   python main.py sources check --sources exampleboard
   ```
   You want `OK exampleboard  50 records, 50 mapped`, plus sample titles. `FAIL` with "many records failed to map" means your field names are wrong.
5. **Save a real fixture** and read it before committing:
   ```bash
   python main.py sources check --sources exampleboard --save-fixtures tests/fixtures/captured
   ```
   `tests/test_captured_fixtures.py` picks up `tests/fixtures/captured/exampleboard.json` automatically and fails if the adapter stops understanding the real response.
6. **Write a unit test.** Copy the pattern in `tests/test_adapters.py`:
   ```python
   @respx.mock
   def test_exampleboard_fetch_and_map(make_client, source_config, now):
       respx.get("https://api.exampleboard.com/v1/jobs").respond(
           200, json=load_fixture("exampleboard.json")
       )
       adapter = ExampleBoardAdapter(source_config(max_pages=1), now)
       raws = adapter.fetch(make_client({"api.exampleboard.com"}))
       jobs = [j for j in (adapter.to_job(r) for r in raws) if j]
       assert jobs and jobs[0].source == "exampleboard"
   ```
7. **Dry run:** `python main.py run --dry-run --sources exampleboard`. Read the titles, tiers and the `Excluded:` line.
8. **Enable it:** set `status: verified`, `verified_on: <today>`, the real `terms_url`, and `enabled: true`.
9. **Record** the verification in your log (B4, step 6).
10. **Quality gates:** `pytest`, `ruff format . && ruff check .`, `mypy src`. Commit and push. The next scheduled run includes it.
11. **Watch it.** After 3 runs its health alarms (sudden zero, volume collapse) become active. `python main.py health` shows its history.

## B8. Special cases

**A site that needs a key (Adzuna, Jooble, Careerjet, ReliefWeb).**
- Set `requires_key = "EXAMPLEBOARD_API_KEY"` on the adapter. If that variable is missing, the source is **skipped** (not failed) with "missing EXAMPLEBOARD_API_KEY".
- Read the key inside `fetch` with `os.environ.get(self.requires_key)`. Pass it in `params=` (the program never logs query strings, and the log filter removes known secrets).
- Add the key as a GitHub secret **and** add it to the `env:` block of the **Run** step in `.github/workflows/daily.yml` (the five names already listed there cover Adzuna, Jooble, Careerjet and ReliefWeb). Add it to `.env.example` as an empty line.
- `requires_key` holds one name. For an API with two values (Adzuna's App ID and App Key), check the second yourself and raise `SchemaError("missing ADZUNA_APP_KEY")`.
- **Keys that must go in a header are not supported yet:** the web client's `get` has no `headers` option, so that needs a small change to `utils/http.py` first.
- In tests, set the variable with `monkeypatch.setenv`.

**A site with an RSS feed.** Copy `weworkremotely.py`. It passes the downloaded bytes to `feedparser.parse`, and unknown tags appear as keys on each entry. Records without a company are dropped.

**Another ATS platform (Lever, Ashby, SmartRecruiters, Workable).** One adapter per platform, companies as tokens under `boards:`. Copy `greenhouse.py`, which already handles per-board failure and the `partial` status.

**An HTML-only board (the Kenyan boards).** Only after step B4 says yes.
- Set `kind = "html"` on the adapter. The runner then waits at least 3 seconds between requests to that host.
- Pass `respect_robots=True` on **every** `client.get(...)` call. It is not automatic.
- Use category or listing paths. Keyword-search URLs are reported as disallowed on these sites.
- You need an HTML parser. None is installed. Add `selectolax` or `beautifulsoup4` to `requirements.in` and `requirements-dev.in` is unaffected, then run `scripts/lock.sh` and commit the new lock files.
- `sources check` prints the `robots.txt` verdict for HTML adapters.
- Layout changes will trigger the volume alarms. Keep selectors few and simple.
- `--save-fixtures` saves non-JSON pages with an `.xml` extension and removes personal data. That is fine for the contract test.
- If the check says "disallowed", **stop**. Do not work around it. Use the site's email alerts.

## B9. After it is live

- It appears automatically in the digest (`Source:`), the RUN line, the `Health` tab and the dashboard (`source` column). No other file changes.
- The same job on two boards is merged into one row with both links, preferring the employer's own address.
- **Disable:** set `enabled: false`, commit, note the reason in the verification log. If the site objects, also delete its rows from the Sheet.

## B10. Common mistakes

| Mistake | What you see | Fix |
|---|---|---|
| Forgot the import in `scrapers/__init__.py` | Source `failed`: "no adapter registered for this id" | Add the module name |
| `id` differs from the key in `sources.yaml` | Same | Make them identical |
| Left `status: pending` | Source skipped: "status is 'pending', not 'verified'" | Verify, then set it |
| Host missing from `allowed_hosts` | Source `failed`: "host not in allowlist" | Add the host |
| `geo_eligibility` default `restricted` on a generic "Remote" | Good jobs appear in `Excluded` as `region_restricted` | Use `default="unclear"` |
| Returned `None` to hide jobs | Source marked `degraded` | Use a hard filter |
| Job id built from list position or a timestamp | The same jobs look new every run | Use the site's own id |
| Relative links like `/jobs/5` | Every record dropped, source `degraded` | Prepend the base address |
| Did not scrub the description | Emails or phone numbers stored | Wrap text in `scrub_pii(...)` |
| Too many pages per run | Slow runs, risk of rate limits | Lower `max_pages` |

---

# Part C. Checklists

**Adding a filter**
- [ ] Hard filter or soft scoring? (A1)
- [ ] Config-only? Edit `scoring.yaml` and remember a list replaces the default (A2)
- [ ] New kind of filter: setting added, check added in the right order, config example written (A4)
- [ ] Test added; `pytest tests/test_matching.py` passes
- [ ] `scoring_version` raised
- [ ] `run --dry-run` shows sensible `Excluded:` counts
- [ ] Remember old jobs and existing `Excluded` rows are not re-judged (A6)

**Adding a job board**
- [ ] Permission check done: route, `robots.txt`, terms, rate limit, attribution (B4)
- [ ] Sample saved with personal data removed (B5)
- [ ] Adapter written from the template, with the safe eligibility default (B6)
- [ ] Imported in `scrapers/__init__.py`; `id` matches the config key
- [ ] Config added as `pending`; `sources check` shows `OK`
- [ ] Real fixture saved, read and committed; unit test written
- [ ] `run --dry-run --sources <id>` looks right
- [ ] Set to `verified` with date and terms link; verification log updated
- [ ] If keyed: GitHub secret, workflow `env:` entry, `.env.example` line
- [ ] `pytest`, `ruff`, `mypy` pass; pushed; first three scheduled runs watched

---

# Part D. FAQ

**Can I filter differently for one site?** Not with config. Add a hard filter that checks `job.source` (A5), or narrow the fetch itself with a feed, a board list or `query_params` (B3). There is no per-source keyword option.

**Can I add LinkedIn, Indeed or Glassdoor?** No. Their terms forbid automated access and they block it. The plan was to read their own **email alerts** into a hidden `Inbox` tab through a Google Apps Script in your account. That was not built; ask if you want it.

**Will a new filter or board change jobs I already have?** No. Stored jobs are never re-judged or rescored. Only jobs fetched from now on are affected.

**How many boards is too many?** Each source is isolated, so one failing never stops the others. The practical limits are the 15-minute run limit, the digest size, and your attention. Add one at a time and watch it for three runs.

**Do I need to change the dashboard or the Telegram digest for a new board?** No. Both pick up new sources automatically.

**I do not want to write code. What can I ask for?** Send me the sample (B5), the terms link, and what you want filtered. I write the adapter or the filter; you run the checks and tests on your machine.
