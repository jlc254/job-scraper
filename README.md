# Job scraper

Personal tool that finds recent customer-care jobs from permitted sources, scores them against one
candidate profile, stores them in a private Google Sheet and sends a Telegram digest twice a day.
Design documents are in the project's `docs` set (00 to 12). Per-phase notes are in `PHASE2.md` to `PHASE6.md`.

## Local use

    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.in            # ranges, for local work
    cp config/sources.example.yaml config/sources.yaml
    cp config/profile.example.yaml config/profile.yaml
    cp config/scoring.example.yaml config/scoring.yaml
    cp .env.example .env                          # fill in values, never commit it
    pytest
    python main.py run --dry-run                  # fetch, filter, score, print. Nothing saved or sent
    python main.py run --storage sqlite --no-notify
    python main.py notify-test                    # needs TELEGRAM_* in the environment

Dashboard: `python main.py dashboard` fills the Dash_* tabs; follow `docs/looker-studio.md` to build the report.
Other commands: `brief <job_id>`, `calibrate --export/--labels`, `sources check`, `health`, `cleanup`, `recover`.
See `python main.py --help`. Optional thresholds live in `config/settings.yaml` (example provided).

## Running on GitHub Actions (private repository)

`.github/workflows/daily.yml` runs at 06:07 and 16:07 EAT. `ci.yml` runs ruff, mypy, pytest and pip-audit
on every push. Setup, in order:

1. Create a PRIVATE repository and push. Run `gitleaks detect --source . --log-opts="--all"` first.
2. `scripts/lock.sh` (Python 3.12, bash, network) then commit `requirements.txt` and `requirements-dev.txt`.
3. `python scripts/pin_actions.py` (network) then commit the pinned workflows.
4. Repository settings, Secrets and variables, Actions: add the secrets listed in `PHASE6.md`.
5. Actions tab, daily-run, Run workflow: try `dry-run`, then `no-notify`, then `normal`.

Day-to-day operation and alerts: see the runbook (doc 12).
