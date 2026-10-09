# 07. Reliability and Monitoring
 
Principle: a failure in one source, one job or one message never stops the run.
 
## Failure handling
| Failure | Handling |
|---|---|
| Timeout | Connect 5 s, read 20 s. Retry up to 3 attempts |
| HTTP 5xx, 408 | Retry with exponential backoff (2 s, 4 s, 8 s) plus jitter |
| HTTP 429 | Honor `Retry-After` (cap 5 minutes). Then mark the source rate-limited for this run. No hammering |
| HTTP 401, 403 | No retry. Mark source blocked, alert, stop that source. Never work around |
| HTTP 404 or 410 | No retry. Log and mark the URL invalid |
| Invalid or dangerous URL | Dropped and counted (see SSRF rules in doc 08) |
| Changed HTML or JSON shape | Required-field check per record. If more than 30% of records fail parsing, mark the source degraded and save a sanitized sample for debugging |
| Missing fields | Optional fields become null. Missing required fields (title, company, URL) drop the record and count it |
| Duplicate jobs | Handled by dedupe (doc 05) |
| Zero results | Compare with the source's median of recent runs. A sudden zero raises a degraded alarm (usually a layout or API change) |
| Partial scrape | Keep what parsed, record counts, report as partial |
| Storage failure | Retry once. If still failing, write results to a local `output/` JSON file and alert. No data lost |
| Telegram failure | Retry. If it fails, results remain in the Sheet and the next run resends unsent jobs (via `notified_at`) |
| Whole run crash | Workflow failure alert. Optional dead-man's-switch ping (for example a Healthchecks.io free check) so silence also raises an alarm |
 
## Per-source status
Each source ends a run as one of: `ok`, `degraded`, `partial`, `rate_limited`, `blocked`, `failed`, `skipped`. Three consecutive non-ok runs trigger a prominent alert. A source is never silently dropped.
 
## Logging
- Structured JSON logs with run ID, source, event, counts and timings.
- Levels: INFO for progress, WARNING for degraded, ERROR for failures.
- Redaction: API keys, tokens, chat IDs and query-string secrets are removed before logging (Adzuna sends its key as a query parameter, so URLs are logged without query strings).
- Never log full descriptions or scraped personal data.
## Run report (sent to Telegram and stored in the Runs tab)
```text
RUN 2026-10-01 03:00 UTC  (2m 41s)
himalayas: ok, 34 found, 5 new
greenhouse(6 boards): ok, 12 found, 2 new
adzuna: partial, 0 results for Kenya (check coverage)
Excluded: 9 (7 region-restricted, 2 scam patterns)
```
 
## Testing strategy
| Level | What | How |
|---|---|---|
| Unit | Normalizer, dedupe, filters, scorer, PII scrubber, URL canonicalizer, robots checker | pytest with table-driven cases |
| Contract | Each adapter against saved real responses in `tests/fixtures/` | respx mocks, no live network |
| Integration | Full pipeline with fake storage and fake Telegram | In-memory storage implementation |
| Golden | Scoring examples from doc 06 must produce the documented scores | Regression test on `scoring.yaml` changes |
| Resilience | Timeouts, 429, 500, malformed JSON, empty feed | Injected failures |
| Live smoke (manual) | `sources check` against real sites, low volume | Run by the owner, not in CI |
 
CI (GitHub Actions on push): ruff, mypy, pytest, pip-audit. CI never calls live job sites.
 
