# Installation & Setup Guide

This guide provides detailed, step-by-step instructions on how to set up the Job Scraper environment and troubleshoot common installation issues.

## 🚀 Quick Start (Linux/macOS)

If you want to get up and running as quickly as possible, run these commands in order:

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize configuration files
cp .env.example .env
cp config/sources.example.yaml config/sources.yaml
cp config/profile.example.yaml config/profile.yaml
cp config/scoring.example.yaml config/scoring.yaml
```

---

## 🛠 Detailed Setup Steps

### 1. Using a Virtual Environment (Highly Recommended)
To avoid conflicts with other Python projects on your system, always use a virtual environment.

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\\Scripts\\activate
```

### 2. Installing Dependencies
The project uses a lock-file system.

```bash
# Install locked dependencies
pip install -r requirements.txt
```

If you are developing or running tests, you should also install the development dependencies:
```bash
pip install -r requirements-dev.txt
```

### 3. Configuration
The scraper requires environment variables and YAML configurations to start. **You must initialize these files before running the app.**

1.  **Environment Variables**: Copy the example `.env` file and fill in your keys.
    ```bash
    # Linux/macOS
    cp .env.example .env
    # Windows
    copy .env.example .env
    ```
2.  **Source & Profile Config**: Initialize the YAML files from examples.
    ```bash
    # Linux/macOS
    cp config/sources.example.yaml config/sources.yaml
    cp config/profile.example.yaml config/profile.yaml
    cp config/scoring.example.yaml config/scoring.yaml

    # Windows
    copy config\sources.example.yaml config\sources.yaml
    copy config\profile.example.yaml config\profile.yaml
    copy config\scoring.example.yaml config\scoring.yaml
    ```

---

## 🧪 Testing Your Job Boards
To test your job boards one by one, the best way is to use the `run` command in the CLI with the `--sources` flag. This allows you to isolate a single adapter and verify its output without running the entire pipeline.

### 1. Find your Source IDs
First, you need to know the exact IDs of the job boards you have configured. These are defined as the top-level keys in your `config/sources.yaml` file (e.g., `himalayas`, `jobicy`, `weworkremotely`).

### 2. Run a Single Source
Once you have the ID, use the following command:
```bash
python main.py run --sources <source_id>
```
Example:
```bash
python main.py run --sources himalayas
```

### 3. How to Verify the Data
Depending on your storage setup, here is how to check if the data was fetched correctly:

**A. Check the Console Output**
Look for logs such as:
- `Fetching jobs from...`
- `Found X jobs`
- `Stored Y new jobs`
- `Merged duplicates: N, updated rows: M`

**B. Check the Storage (Google Sheets)**
If you are using Google Sheets, open your sheet. You should see new rows appearing specifically for that board.

**C. Check the Local Database (SQLite)**
If you are using SQLite (via `--storage sqlite`), you can query the database:
```bash
sqlite3 output/jobs.db "SELECT * FROM jobs WHERE json_extract(row_json, '$.source') = 'himalayas' LIMIT 5;"
```

**D. Use "Dry Run" for Fast Testing**
To fetch and score data without writing to the database or sending notifications:
```bash
python main.py run --sources himalayas --dry-run
```

**Summary Checklist for Testing a Board:**
1. Command: `python main.py run --sources <id> --dry-run`
2. Watch for: `Found X jobs` in the logs.
3. Verify: Check if the job titles, companies, and links look correct in the output.

---

## ❓ Troubleshooting Common Issues

### "ModuleNotFoundError: No module named 'dotenv'"
This happens if `python-dotenv` is not installed in your current environment.

**The Fix:**
Ensure your virtual environment is **activated**, then run:
```bash
pip install python-dotenv
```

### Missing Configuration Files
If the app crashes saying it cannot find a `.yaml` or `.env` file, it means you skipped the **Configuration** step above. Ensure all `cp` (or `copy`) commands were executed.

---

## 🏃 Running the Scraper

Once setup is complete, you can verify everything is working with a dry run:

```bash
python main.py run --sources jobicy --dry-run
```

**Command Breakdown:**
- `run`: Executes the scraping pipeline.
- `--sources jobicy`: Only scrape from the 'jobicy' source.
- `--dry-run`: Fetches and scores jobs but does **not** save them to the database or send notifications.
