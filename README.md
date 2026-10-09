# Job Scraper

Personal tool that finds recent customer-care jobs from permitted sources, scores them against one
candidate profile, stores them in a private Google Sheet and sends a Telegram digest twice a day.
Design documents are in the project's `docs` set (00 to 12).

## Prerequisites

Before running the application, ensure you have the following:
- **Python 3.12+**: The project is developed and tested on Python 3.12.
- **Google Sheets API**: A Google Cloud project with the Google Sheets and Google Drive APIs enabled, and a service account JSON key.
- **Telegram Bot**: A bot created via `@BotFather` to send notifications.
- **Environment Variables**: API tokens and configuration values (see `.env.example`).

## Local Use

### 1. Setup
For a detailed step-by-step guide, including virtual environment setup and troubleshooting common errors (like `ModuleNotFoundError`), see the [Detailed Setup Guide](docs/setup-guide.md).

Quick setup:
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Initialize configuration files
cp config/sources.example.yaml config/sources.yaml
cp config/profile.example.yaml config/profile.yaml
cp config/scoring.example.yaml config/scoring.yaml
cp .env.example .env
```
*Note: Edit the created `.env` and `config/*.yaml` files with your actual credentials and profile.*

### 2. Verification & Running
```bash
# Load environment variables (Linux/macOS)
set -a; source .env; set +a

# Run tests to ensure everything is correct
pytest

# Dry run: fetch, filter, score, and print to console (no data saved or sent)
python main.py run --dry-run

# Run with local SQLite storage and no notifications
python main.py run --storage sqlite --no-notify

# Test Telegram notifications (requires TELEGRAM_* variables in .env)
python main.py notify-test
```

### 3. Other Commands
- **Dashboard**: `python main.py dashboard` fills the Dash_* tabs; follow `docs/looker-studio.md` to build the report.
- **Utility commands**: `brief <job_id>`, `calibrate --export/--labels`, `sources check`, `health`, `cleanup`, `recover`.
- **Help**: See `python main.py --help`. Optional thresholds live in `config/settings.yaml` (example provided).


### Development & Maintenance

To ensure code quality and consistency, use `ruff` for linting and formatting.

**Check for violations:**
```bash
# Check for linting errors
ruff check .

# Check for formatting issues
ruff format --check .
```

**Autofix violations:**
```bash
# Fix linting errors automatically
ruff check . --fix

# Format the codebase
ruff format .
```

## Running on GitHub Actions (Private Repository)

`.github/workflows/daily.yml` runs at 06:07 and 16:07 EAT. `ci.yml` runs ruff, mypy, pytest and pip-audit
on every push. Setup, in order:

1. Create a PRIVATE repository and push. Run `gitleaks detect --source . --log-opts="--all"` first.
2. `scripts/lock.sh` (Python 3.12, bash, network) then commit `requirements.txt` and `requirements-dev.txt`.
3. `python scripts/pin_actions.py` (network) then commit the pinned workflows.
4. Repository settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions: add the required secrets (e.g., Telegram tokens, Google credentials).
5. Actions tab, daily-run, Run workflow: try `dry-run`, then `no-notify`, then `normal`.

Day-to-day operation and alerts: see the runbook (doc 12).
