#!/usr/bin/env bash
# Delete Neon preview branches that outlived their pull request.
#
# Vercel's Neon integration names the branch it creates for a preview deployment
# preview/<git-branch>, and cleanup-neon-preview.yml deletes it when the PR closes. That
# close event is the only cleanup path, so a PR closed while the workflow was failing, a
# branch deleted through the API, or a workflow disabled at the wrong moment leaves the
# branch behind forever. Neon Free caps the project at ten branches, so a handful of
# orphans is enough to stop new previews from being created.
#
# Usage:
#   NEON_API_KEY=... NEON_PROJECT_ID=... bash scripts/neon_branch_sweep.sh
#   NEON_API_KEY=... NEON_PROJECT_ID=... DRY_RUN=1 bash scripts/neon_branch_sweep.sh
#
# Env contract:
#   NEON_API_KEY    required
#   NEON_PROJECT_ID required
#   MAX_AGE_DAYS    default 7; a positive integer
#   DRY_RUN         default 0; 1 prints what would be deleted and deletes nothing
#
# A branch is deleted only when all three hold: its name starts with preview/, it is not
# the project's default branch, and its updated_at is older than MAX_AGE_DAYS. The list is
# fetched in full and validated before the first DELETE, so a parse error or a default
# branch matching the preview pattern aborts the sweep instead of leaving it half done.
#
# stdout ends with `deleted=<n> kept=<n>`. Exit 0 on success, 1 on any API/parse error,
# 2 on a usage error.
set -euo pipefail

api="${NEON_API_BASE:-https://console.neon.tech/api/v2}"
project="${NEON_PROJECT_ID:?NEON_PROJECT_ID is required}"
: "${NEON_API_KEY:?NEON_API_KEY is required}"
# `-` rather than `:-`: an explicitly empty MAX_AGE_DAYS is an ambiguous configuration
# (usually an unset repository variable interpolated into env), not a request for the
# default. Fail closed instead of silently choosing a deletion threshold for the operator.
max_age="${MAX_AGE_DAYS-7}"
dry_run="${DRY_RUN:-0}"

case "$max_age" in
  '' | *[!0-9]* | 0)
    echo "MAX_AGE_DAYS must be a positive integer, got '$max_age'." >&2
    exit 2
    ;;
esac

# The API key goes through a config fd, not argv: the process list is readable by every
# user on the runner, and this repository keeps credentials out of command lines.
neon_curl_config() {
  printf 'header = "Authorization: Bearer %s"\n' "$NEON_API_KEY"
}

pages=$(mktemp)
records=$(mktemp)
trap 'rm -f "$pages" "$records"' EXIT

# Appends every branch-list page to $pages as one JSON document per line. Neon's list is
# cursor-paginated: pagination.next is opaque and passed back as `cursor`, and it is absent
# on the last page. Sorted updated_at-descending by default, so old branches can sit on a
# later page behind a backlog of recent ones.
collect_branches() {
  local guard=0 args body cursor next
  cursor=""
  while :; do
    args=(--silent --show-error --fail-with-body --max-time 20
      --header "Accept: application/json"
      -G "${api}/projects/${project}/branches"
      --data-urlencode "limit=100")
    if [ -n "$cursor" ]; then
      args+=(--data-urlencode "cursor=$cursor")
    fi
    body=$(curl "${args[@]}" --config <(neon_curl_config)) || {
      echo "::error::Neon's branch list request failed; refusing to sweep." >&2
      return 1
    }
    printf '%s\n' "$body" >>"$pages"
    next=$(printf '%s' "$body" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(2)
if not isinstance(data, dict):
    sys.exit(2)
print((data.get("pagination") or {}).get("next") or "")
') || {
      echo "::error::Neon returned a branch list that could not be parsed; refusing to sweep." >&2
      return 1
    }
    if [ -z "$next" ]; then
      return 0
    fi
    cursor="$next"

    # A well-behaved cursor ends at the last page; this guard only convicts a server that
    # keeps answering with the same or a fresh cursor forever.
    guard=$((guard + 1))
    if [ "$guard" -gt 100 ]; then
      echo "::error::Neon's branch list pagination did not end within 100 pages." >&2
      return 1
    fi
  done
}

# Reads every page from stdin and prints one record per line:
#   TOTAL<TAB><n>                     branches seen across all pages
#   REFUSE<TAB><name>                 a default branch matching preview/*
#   DELETE<TAB><id><TAB><name><TAB><updated_at>
# Exit code 2 means a page, branch or timestamp did not have the documented shape; the
# caller aborts, and nothing has been deleted yet.
classify() {
  python3 -c '
import datetime
import json
import sys

max_age = int(sys.argv[1])
now = datetime.datetime.now(datetime.timezone.utc)
deletes = []
refusals = []
total = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        page = json.loads(line)
    except Exception:
        sys.exit(2)
    if not isinstance(page, dict):
        sys.exit(2)
    branches = page.get("branches", [])
    if not isinstance(branches, list):
        sys.exit(2)
    for item in branches:
        if not isinstance(item, dict):
            sys.exit(2)
        name = item.get("name")
        branch_id = item.get("id")
        if not isinstance(name, str) or not isinstance(branch_id, str):
            sys.exit(2)
        total += 1
        if item.get("default"):
            if name.startswith("preview/"):
                refusals.append(name)
            continue
        if not name.startswith("preview/"):
            continue
        updated_at = item.get("updated_at")
        if not isinstance(updated_at, str) or not updated_at:
            print("branch %s has no usable updated_at" % name, file=sys.stderr)
            sys.exit(2)
        try:
            moment = datetime.datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            print("branch %s has an unparseable updated_at: %s" % (name, updated_at), file=sys.stderr)
            sys.exit(2)
        if moment.tzinfo is None:
            # A naive timestamp has no unambiguous age; guessing one way could delete a
            # live branch or leave the cap full forever.
            print("branch %s has a timezone-less updated_at: %s" % (name, updated_at), file=sys.stderr)
            sys.exit(2)
        if now - moment > datetime.timedelta(days=max_age):
            deletes.append((branch_id, name, updated_at))

for name in refusals:
    print("REFUSE\t%s" % name)
print("TOTAL\t%d" % total)
for branch_id, name, updated_at in deletes:
    print("DELETE\t%s\t%s\t%s" % (branch_id, name, updated_at))
' "$max_age"
}

delete_branch() {
  local id="$1" name="$2" status
  # The status code is read instead of relying on --fail so that a 404 between the list
  # call and this one is not a failure: the branch is already gone, which is the end state
  # this script exists to reach. Any other non-2xx is loud.
  status=$(curl --silent --show-error --max-time 20 --retry 2 \
    --request DELETE \
    --output /dev/null \
    --write-out '%{http_code}' \
    --config <(neon_curl_config) \
    "${api}/projects/${project}/branches/${id}") || status="000"
  case "$status" in
    2??) echo "Deleted Neon branch '$name' (id $id)." ;;
    404) echo "Neon branch '$name' was already gone; counting it as deleted." ;;
    *)
      echo "::error::Deleting Neon branch '$name' failed with HTTP ${status}." >&2
      return 1
      ;;
  esac
}

collect_branches
if ! classify <"$pages" >"$records"; then
  echo "::error::Neon's branch list could not be classified; refusing to sweep." >&2
  exit 1
fi

mapfile -t record_list <"$records"

# Validate the whole listing before the first DELETE. A default branch that matches the
# preview pattern means the API and this script disagree about what production is, and
# nothing in that listing can be trusted.
for record in "${record_list[@]}"; do
  if [ "${record%%$'\t'*}" = "REFUSE" ]; then
    echo "::error::Neon lists '${record#*$'\t'}' as the default branch but it matches preview/*; refusing to sweep." >&2
    exit 1
  fi
done

total=0
deleted=0
for record in "${record_list[@]}"; do
  kind="${record%%$'\t'*}"
  rest="${record#*$'\t'}"
  case "$kind" in
    TOTAL) total="$rest" ;;
    DELETE)
      id="${rest%%$'\t'*}"
      rest="${rest#*$'\t'}"
      name="${rest%%$'\t'*}"
      updated_at="${rest#*$'\t'}"
      if [ "$dry_run" = "1" ]; then
        echo "Would delete '$name' (id $id, updated $updated_at)."
        continue
      fi
      delete_branch "$id" "$name"
      deleted=$((deleted + 1))
      ;;
  esac
done

echo "deleted=${deleted} kept=$((total - deleted))"
