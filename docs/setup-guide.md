# Installation & Setup Guide

This guide provides detailed, step-by-step instructions on how to set up the Job Scraper environment and troubleshoot common installation issues.

## 🚀 Quick Start (Linux/macOS)

If you want to get up and running as quickly as possible, run these commands in order:

\`\`\`bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install python-dotenv  # Required: Currently missing from requirements.txt

# 3. Initialize configuration files
cp .env.example .env
cp config/sources.example.yaml config/sources.yaml
cp config/profile.example.yaml config/profile.yaml
cp config/scoring.example.yaml config/scoring.yaml
\`\`\`

---

## 🛠 Detailed Setup Steps

### 1. Using a Virtual Environment (Highly Recommended)
To avoid conflicts with other Python projects on your system, always use a virtual environment.

**On Linux/macOS:**
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
\`\`\`

**On Windows:**
\`\`\`bash
python -m venv venv
venv\\Scripts\\activate
\`\`\`

### 2. Installing Dependencies
The project uses a lock-file system. However, some dependencies may need to be added manually if the lock file is outdated.

\`\`\`bash
# Install locked dependencies
pip install -r requirements.txt

# Manual fix for missing environment loader
pip install python-dotenv
\`\`\`

If you are developing or running tests, you should also install the development dependencies:
\`\`\`bash
pip install -r requirements-dev.txt
\`\`\`

### 3. Configuration
The scraper requires environment variables and YAML configurations to start. **You must initialize these files before running the app.**

1.  **Environment Variables**: Copy the example `.env` file and fill in your keys.
    \`\`\`bash
    cp .env.example .env
    \`\`\`
2.  **Source & Profile Config**: Initialize the YAML files from examples.
    \`\`\`bash
    cp config/sources.example.yaml config/sources.yaml
    cp config/profile.example.yaml config/profile.yaml
    cp config/scoring.example.yaml config/scoring.yaml
    \`\`\`

---

## ❓ Troubleshooting Common Issues

### "ModuleNotFoundError: No module named 'dotenv'"
This happens because \`python-dotenv\` is not listed in the current \`requirements.txt\` file.

**The Fix:**
Ensure your virtual environment is **activated**, then run:
\`\`\`bash
pip install python-dotenv
\`\`\`
*Tip: Using \`python -m pip install\` is the safest way to ensure the package is installed for the exact Python version you are using.*

### "FileNotFoundError" when starting
If the app crashes saying it cannot find a \`.yaml\` or \`.env\` file, it means you skipped the **Configuration** step above. Ensure all \`cp\` commands were executed.

---

## 🏃 Running the Scraper

Once setup is complete, you can verify everything is working with a dry run:

\`\`\`bash
python main.py run --sources jobicy --dry-run
\`\`\`

**Command Breakdown:**
- \`run\`: Executes the scraping pipeline.
- \`--sources jobicy\`: Only scrape from the 'jobicy' source.
- \`--dry-run\`: Fetches and scores jobs but does **not** save them to the database or send notifications.
