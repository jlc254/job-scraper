#!/usr/bin/env bash
# Runs the job scraper in GitHub Actions. Inputs arrive as environment variables, never
# interpolated into the shell, so a dispatch input cannot inject commands.
set -euo pipefail

case "${MODE:-normal}" in
  normal) args=(run) ;;
  no-notify) args=(run --no-notify) ;;
  dry-run) args=(run --dry-run) ;;
  dashboard) args=(dashboard) ;;  # rebuild the Looker Studio tabs only, fetch nothing
  publish) args=(publish) ;;  # refresh Neon from the Google Sheet only
  *) echo "unknown mode: ${MODE}" >&2; exit 2 ;;
esac

if [[ -n "${SOURCES:-}" && "${MODE:-normal}" != "dashboard" && "${MODE:-normal}" != "publish" ]]; then
  if [[ ! "$SOURCES" =~ ^[a-z0-9_,-]+$ ]]; then
    echo "invalid sources value" >&2
    exit 2
  fi
  args+=(--sources "$SOURCES")
fi

exec python main.py "${args[@]}"
