#!/usr/bin/env bash
# Regenerate requirements.txt and requirements-dev.txt with hashes (doc 08, doc 09).
# Run on Python 3.12 with network access, then commit both files.
set -euo pipefail
cd "$(dirname "$0")/.."

version="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if [[ "$version" != "3.12" ]]; then
  echo "Use Python 3.12 (found $version). The workflow runs 3.12, so lock with the same version." >&2
  exit 1
fi

venv="$(mktemp -d)/lock-venv"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --quiet --upgrade pip "pip-tools>=7"

"$venv/bin/pip-compile" --quiet --generate-hashes --strip-extras --allow-unsafe \
  --output-file requirements.txt requirements.in
"$venv/bin/pip-compile" --quiet --generate-hashes --strip-extras --allow-unsafe \
  --output-file requirements-dev.txt requirements-dev.in

echo "Wrote requirements.txt and requirements-dev.txt. Commit both."
