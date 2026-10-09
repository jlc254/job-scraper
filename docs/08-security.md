# 08. Security
 
## Assets to protect
API keys and tokens (Telegram, Google service account, Adzuna), the owner's job-search data, the owner's CV (kept off the repo), and the integrity of the pipeline.
 
## Threats and controls
| Risk | Control |
|---|---|
| Leaked secrets | Secrets only in GitHub Secrets and a local `.env` (git-ignored). `.env.example` has placeholders. gitleaks pre-commit hook. Private repository |
| Secrets in logs | Central redaction filter. URLs logged without query strings (Adzuna key travels in the query). Never log request headers |
| Google service account over-privilege | Service account has no project roles. The Sheet is shared with it as Editor and nothing else. Scope limited to Sheets. Rotate the key if exposed |
| Telegram abuse | Bot token secret. The bot sends only to the configured chat ID. It does not read or act on incoming messages |
| Cookies and sessions | None stored. No logins anywhere |
| Database security | Sheet is private to the owner. Do not use link sharing. Enable 2-step verification on the Google account |
| SSRF | Fetch only hosts in the source allowlist. HTTPS only. Reject private, loopback and link-local addresses after DNS resolution. Limit redirects to 3 and re-check each target. Job URLs from scraped data are stored, never fetched automatically unless the host matches the source's registered domain |
| Malicious scraped content | Treat all scraped text as untrusted data. Strip HTML to plain text. No `eval`, no template rendering of scraped text, no shell calls with scraped values. Size limits on responses (for example 5 MB) and on fields |
| Unsafe HTML rendering | Nothing is rendered as HTML. Telegram messages sent as plain text or escaped. Sheet cells written as values, and cells starting with `=`, `+`, `-` or `@` are prefixed so they cannot become formulas |
| Prompt injection (if an LLM is added later) | Scraped text is passed only as clearly delimited data, LLM output is never executed, and the LLM has no tools or secrets |
| Dependency vulnerabilities | Few dependencies, pinned with hashes. `pip-audit` in CI. Dependabot enabled |
| Supply chain (Actions) | Pin third-party Actions to a commit SHA. Workflow `permissions: contents: read`. No `pull_request_target`. Secrets not exposed to forks |
| Data over-retention | 60-day retention job. No third-party personal data collected beyond scraped job listings. Owner's profile and Telegram chat ID are processed for matching and notification. |
| Local machine | Keep `.env` and any service account file outside cloud-synced folders. Restrict file permissions |
 
## Pre-deployment checklist
- [ ] Repo is private and `.gitignore` covers `.env`, `*.json` credentials, `output/`, `logs/`
- [ ] gitleaks passes on full history
- [ ] Redaction test proves a fake key never appears in logs
- [ ] SSRF tests: private IP, redirect to internal host, non-HTTPS
- [ ] Formula-injection test on Sheet writes
- [ ] Sheet shared only with the service account and the owner
- [ ] Secrets set in GitHub, none in code or config
- [ ] `pip-audit` clean, Actions pinned
 
