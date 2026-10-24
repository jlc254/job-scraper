#!/usr/bin/env bash
# Verify or delete the Neon branch that Vercel's Neon integration creates for a preview
# deployment. The integration names it preview/<git-branch>, so the branch is owned by
# Neon and tied to one PR rather than to a workflow-run lifetime.
#
# Usage:
#   NEON_API_KEY=... NEON_PROJECT_ID=... NEON_BRANCH_NAME=preview/foo \
#     bash scripts/neon_preview_branch.sh verify
#   NEON_API_KEY=... NEON_PROJECT_ID=... NEON_BRANCH_NAME=preview/foo \
#     bash scripts/neon_preview_branch.sh delete
#
# verify: fails unless a non-default branch with exactly that name exists. A missing
#         branch means the integration did not create one, so the deployment would fall
#         back to whatever DATABASE_URL the project holds for previews. Fail closed.
# delete: removes the branch when it exists. A missing branch is success, so a closed PR
#         that never produced a deployment does not turn the cleanup workflow red.
#
# The project's production database is its DEFAULT branch. Both subcommands refuse to act
# on that branch, and the preview/* prefix check refuses any name that is not a preview
# branch, so this script cannot be pointed at production by a malformed ref.
set -euo pipefail

api="${NEON_API_BASE:-https://console.neon.tech/api/v2}"
project="${NEON_PROJECT_ID:?NEON_PROJECT_ID is required}"
branch="${NEON_BRANCH_NAME:?NEON_BRANCH_NAME is required}"
: "${NEON_API_KEY:?NEON_API_KEY is required}"

# preview/ followed by at least one character. `preview/` alone or `preview` is rejected.
case "$branch" in
  preview/?*) ;;
  *)
    echo "::error::refusing to manage '$branch': only preview/<branch> names are allowed." >&2
    exit 1
    ;;
esac

# The API key goes through a config fd, not argv: the process list is readable by every
# user on the runner, and this repository keeps credentials out of command lines.
neon_curl_config() {
  printf 'header = "Authorization: Bearer %s"\n' "$NEON_API_KEY"
}

# Prints "<id> <default>" for the branch, or nothing when it does not exist.
# `limit=100` is the API maximum; the free plan caps a project far below that.
find_branch() {
  curl --silent --show-error --fail-with-body \
    --config <(neon_curl_config) \
    --header "Accept: application/json" \
    "${api}/projects/${project}/branches?limit=100" |
    python3 -c '
import json
import sys

name = sys.argv[1]
for candidate in json.load(sys.stdin).get("branches", []):
    if candidate.get("name") == name:
        print(candidate.get("id", ""), "true" if candidate.get("default") else "false")
        break
' "$branch"
}

verify() {
  local attempt found id is_default
  local attempts="${NEON_VERIFY_ATTEMPTS:-12}"
  local delay="${NEON_VERIFY_DELAY:-5}"
  # The integration creates the branch from a deployment webhook, so allow a short race
  # between `vercel deploy` returning and the branch becoming visible. The overrides exist
  # so tests do not have to wait out the real 60s budget.
  for attempt in $(seq 1 "$attempts"); do
    found=$(find_branch)
    if [ -n "$found" ]; then
      read -r id is_default <<<"$found"
      if [ "$is_default" = "true" ]; then
        echo "::error::'$branch' is the project's default (production) branch; refusing to treat it as a preview." >&2
        exit 1
      fi
      echo "Preview branch '$branch' exists (id $id) and is not the default branch."
      return 0
    fi
    echo "Waiting for Neon preview branch '$branch' (attempt ${attempt}/${attempts})..."
    sleep "$delay"
  done

  cat >&2 <<MSG
::error::No Neon branch named '$branch' after ${attempts} attempt(s). The Vercel Neon
integration did not create a preview branch, so this deployment is not isolated from the
production database. Check that Preview Branching is enabled for the Neon integration
(Vercel > Project > Settings > Integrations > Neon > Preview), and that the deploy passed
--meta githubDeployment=1 --meta githubCommitRef=<branch>.
MSG
  exit 1
}

delete() {
  local found id is_default status
  found=$(find_branch)
  if [ -z "$found" ]; then
    echo "No Neon branch named '$branch'; nothing to delete."
    return 0
  fi
  read -r id is_default <<<"$found"
  if [ "$is_default" = "true" ]; then
    echo "::error::'$branch' is the project's default (production) branch; refusing to delete it." >&2
    exit 1
  fi
  echo "Deleting Neon branch '$branch' (id $id)..."
  # The status code is read instead of relying on --fail so that a 404 between the lookup
  # above and this call is not a failure. That race is benign: the branch is already gone,
  # which is the end state this command exists to reach. Any other non-2xx is loud.
  status=$(curl --silent --show-error \
    --request DELETE \
    --output /dev/null \
    --write-out '%{http_code}' \
    --config <(neon_curl_config) \
    "${api}/projects/${project}/branches/${id}")
  case "$status" in
    2??) echo "Deleted Neon branch '$branch'." ;;
    404) echo "Neon branch '$branch' was already gone; nothing to delete." ;;
    *)
      echo "::error::Deleting Neon branch '$branch' failed with HTTP ${status}." >&2
      exit 1
      ;;
  esac
}

case "${1:-}" in
  verify) verify ;;
  delete) delete ;;
  *)
    echo "usage: $0 <verify|delete>" >&2
    exit 2
    ;;
esac
