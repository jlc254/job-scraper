# 11. Coding Standards
 
## Language and tooling
| Item | Standard |
|---|---|
| Python | 3.12 |
| Formatting and lint | ruff (format and lint), line length 100 |
| Types | Full type hints. mypy in strict mode for `src/` |
| Tests | pytest, respx for HTTP mocks, no live network in CI |
| Dependencies | Minimal. Pinned with hashes. New dependency needs a one-line justification in the PR |
| Security scans | pip-audit, gitleaks pre-commit |
 
## Structure rules
- Follow the layout in doc 04. One adapter per source, one responsibility per module.
- Dependency direction: `scrapers` and `storage` and `notifications` depend on `models` and `utils`. They never import each other. Only the runner wires them together.
- Adapters return data. They never write to storage or send messages.
- Pure functions for normalization, dedupe, filters and scoring so they are easy to test.
## Error handling
- Catch specific exceptions at boundaries (HTTP, parsing, storage). No bare `except`.
- A failed record is dropped and counted. A failed source is recorded and skipped. A failed run alerts.
- Never swallow an error silently. Log it with context (source, run ID, record index) but without secrets or scraped personal data.
## Logging
- Use the standard `logging` module with a JSON formatter and a redaction filter.
- No `print` outside the CLI's intended output.
- Never log headers, tokens, query strings, full descriptions or chat IDs.
## Configuration
- Behavior lives in `config/*.yaml`, validated by pydantic at startup. Fail fast with a clear message.
- Secrets come only from environment variables.
- No hard-coded URLs, weights, keywords or thresholds in code.
## Naming and style
- `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Docstrings on public functions: what, inputs, outputs, failure behavior.
- Functions under about 40 lines. Adapters under about 150 lines.
## Testing conventions
- Every adapter ships with at least one saved real response in `tests/fixtures/` (personal data removed).
- Table-driven tests for dedupe, filters, scoring and scrubbing.
- Golden tests reproduce the scoring examples in doc 06.
- Every bug fix adds a regression test first.
- Target: at least 85% coverage on `matching/`, `utils/` and `parsers/`.
## Git workflow
- Private repository. `main` is always deployable.
- Branch names: `phase-2/himalayas-adapter`, `fix/zero-result-alarm`.
- Commit messages in imperative form: "Add Greenhouse adapter".
- Every change goes through a pull request, even as a solo developer, and CI must pass (ruff, mypy, pytest, pip-audit).
## Pull request checklist
- [ ] Tests added or updated and passing
- [ ] No secrets, no real personal data, no full listings in fixtures
- [ ] If a source changed: verification log and `sources.yaml` status updated
- [ ] If scoring changed: `scoring_version` incremented and golden tests updated
- [ ] Docs updated if behavior or config changed
## Definition of done (per task)
Code, tests, types and lint clean, docs updated, and demonstrated with a dry run.
