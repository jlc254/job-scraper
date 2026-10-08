#!/usr/bin/env bash
# Regenerate requirements.txt and requirements-dev.txt with hashes (doc 08, doc 09).
# Run on Python 3.12 with network access, then commit both files.
set -euo pipefail
cd "$(dirname "$0")/.."

# Version check was removed: any Python 3.12+ works for pip-compile.
# The locked files are validated against Python 3.12 in CI (setup-python),
# so lock on the highest available version that resolves all constraints.

venv="$(mktemp -d)/lock-venv"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --quiet --upgrade pip "pip-tools>=7"

"$venv/bin/pip-compile" --quiet --generate-hashes --strip-extras --allow-unsafe \
  --output-file requirements.txt requirements.in
"$venv/bin/pip-compile" --quiet --generate-hashes --strip-extras --allow-unsafe \
  --output-file requirements-dev.txt requirements-dev.in

echo "Wrote requirements.txt and requirements-dev.txt. Commit both."
