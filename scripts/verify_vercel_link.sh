#!/usr/bin/env bash
# Assert that the linked Vercel project is configured the way deploy.yml and preview.yml
# assume, immediately after `vercel pull`.
#
# Root Directory is a dashboard-only project setting; vercel.json has no rootDirectory key,
# so a mismatch cannot be fixed from the repository. Left unchecked it surfaces much later
# as an opaque build error (NEXT_NOT_FOUND) or, worse, as a deployment built from the wrong
# directory. `vercel pull` copies the setting into .vercel/project.json as
# settings.rootDirectory, so it can be asserted here with a message that names the fix.
#
# Usage: bash scripts/verify_vercel_link.sh <expected-root-directory>
set -euo pipefail

expected="${1:-}"
if [ -z "$expected" ]; then
  echo "usage: $0 <expected-root-directory>" >&2
  exit 2
fi

project_json=".vercel/project.json"

if [ ! -f "$project_json" ]; then
  cat >&2 <<MSG
::error::No $project_json after 'vercel pull', so this repository is not linked to a
Vercel project. Check that VERCEL_TOKEN, VERCEL_ORG_ID and VERCEL_PROJECT_ID point at the
right team and project.
MSG
  exit 1
fi

actual=$(node -p "require('./${project_json}').settings?.rootDirectory ?? ''" 2>/dev/null) || {
  cat >&2 <<MSG
::error::$project_json is not valid JSON. Remove .vercel/ and re-run 'vercel pull' (or
'vercel link') to relink the checkout.
MSG
  exit 1
}

if [ "$actual" != "$expected" ]; then
  cat >&2 <<MSG
::error::Vercel project Root Directory is '${actual:-<unset>}', but these workflows expect
'${expected}'. Set it in Vercel > Project > Settings > Root Directory.

Until it matches, the CLI either fails to find the app or builds and deploys the wrong
directory.
MSG
  exit 1
fi

echo "Vercel project linked; Root Directory is '${actual}'."