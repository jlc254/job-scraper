# Widen the community profile — execution checklist

Approved in chat 2026-10-26 (bounded path, option 1 + DevRel kept strong).

1. [x] Add `language_required_patterns` to `FilterSettings` (default empty)
2. [x] Check it in `JobFilters` after `excluded_title`, reason `language_required`
3. [x] Document the key in `config/scoring.example.yaml`
4. [x] Community `scoring.yaml`: region patterns, language patterns, support_keywords,
       skill_dictionary, drop `zapier`, bump `scoring_version` to 2
5. [x] Community `profile.yaml`: strong/potential/stretch title changes, DevRel variants,
       `partial_skills` additions
6. [x] Tests: language positives/negatives, real region strings, support leaves the key unset,
       skill consistency, ordinary-word guards
7. [x] `ruff check .`, `ruff format --check .`, `pytest -q`
8. [x] Fresh `main.py run --only community --dry-run`, compare exclusion counts
9. [x] `graphify update .`
10. [x] Commit locally; give the user push commands (no push from this shell)
