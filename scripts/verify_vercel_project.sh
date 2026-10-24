#!/usr/bin/env bash
# Keep the deploy workflows pointed at the directory that actually holds the Next.js app.
#
# The app root is discovered from the repository rather than hard-coded, so moving the
# dashboard cannot silently leave the workflows building or deploying the wrong directory.
#
# Vercel's Root Directory is a dashboard-only project setting: vercel.json has no
# rootDirectory key, so a mismatch cannot be corrected from here. `vercel pull` copies the
# setting into .vercel/project.json as settings.rootDirectory, and the CLI then builds at
# join(repoRoot, rootDirectory) (see packages/cli/src/commands/build/index.ts), which is
# what `link` and `build` below check against.
#
# Usage:
#   bash scripts/verify_vercel_project.sh link    # after `vercel pull`
#   bash scripts/verify_vercel_project.sh build   # after `vercel build`
set -euo pipefail

project_json=".vercel/project.json"

# Echoes the repo-relative directory holding the Next.js app: the one with both a
# next.config.* file and a package.json that depends on next.
resolve_app_root() {
  local dir found="" candidate
  while IFS= read -r dir; do
    candidate="${dir#./}"
    if node -e "const p=require(process.argv[1]);process.exit((p.dependencies&&p.dependencies.next)||(p.devDependencies&&p.devDependencies.next)?0:1)" \
      "./$candidate/package.json" 2>/dev/null; then
      if [ -n "$found" ]; then
        echo "::error::More than one Next.js app in this repository ('$found' and '$candidate')." >&2
        echo "Set Vercel's Root Directory to one of them, or merge the apps." >&2
        return 1
      fi
      found="$candidate"
    fi
  # -maxdepth bounds the walk and node_modules is excluded by name; the app is the only
  # directory here with both a next.config.* and a package.json depending on next.
  done < <(find . -maxdepth 3 -name 'next.config.*' -not -path '*/node_modules/*' \
    -printf '%h\n' | sort -u)

  if [ -z "$found" ]; then
    echo "::error::No Next.js app found (expected a next.config.* beside a package.json depending on 'next')." >&2
    return 1
  fi
  # Vercel stores a repository-root app's Root Directory as the empty string, not ".".
  if [ "$found" = "." ]; then
    found=""
  fi
  printf '%s\n' "$found"
}

app_root=$(resolve_app_root)

check_link() {
  if [ ! -f "$project_json" ]; then
    cat >&2 <<MSG
::error::No $project_json after 'vercel pull', so this checkout is not linked to a Vercel
project. Check that VERCEL_TOKEN, VERCEL_ORG_ID and VERCEL_PROJECT_ID name the right team
and project.
MSG
    return 1
  fi

  # null, missing and empty all mean "not set"; report them the same way.
  actual=$(node -p "require('./${project_json}').settings?.rootDirectory ?? ''" 2>/dev/null) || {
    echo "::error::$project_json is not valid JSON. Remove .vercel/ and re-run 'vercel pull'." >&2
    return 1
  }

  if [ "$actual" != "$app_root" ]; then
    cat >&2 <<MSG
::error::Vercel Root Directory is '${actual:-<unset>}' but the dashboard app is in '${app_root}'.

Set Vercel > Project > Settings > Root Directory to '${app_root}'.

Until it matches, Vercel builds at the wrong directory: either NEXT_NOT_FOUND, or a
deployment built from something other than the dashboard.
MSG
    return 1
  fi
  echo "Root Directory '${app_root}' matches the repository."
}

check_build() {
  # The CLI reports the output as ".vercel/output" relative to the directory it was
  # invoked from, but where it actually lands depends on how the project is linked: the
  # build command resolves its own projectRootDirectory (from the API's `directory`
  # field), which is not necessarily the settings.rootDirectory that `link` checks.
  # Observed on a settings.rootDirectory of "frontend": the output appeared at the
  # repository root. So accept either location and report which was found, instead of
  # pinning a path and failing a perfectly good build.
  local candidate found=""
  for candidate in ".vercel/output" "${app_root:+${app_root}/}.vercel/output"; do
    if [ -d "$candidate" ]; then
      found="$candidate"
      break
    fi
  done

  if [ -z "$found" ]; then
    echo "::error::No build output after 'vercel build'. Looked for '.vercel/output' and '${app_root:+${app_root}/}.vercel/output'." >&2
    return 1
  fi
  echo "Build output found at '${found}'."
}

# Fails before deploying when a variable the app needs at runtime is empty. An empty
# DATABASE_URL still builds (every page that touches it is force-dynamic) and still
# deploys, so without this the dashboard ships broken and only fails on the first request.
check_secrets() {
  local required=() optional=() name
  for name in VERCEL_TOKEN DATABASE_URL; do
    [ -n "${!name:-}" ] || required+=("$name")
  done
  # These have code defaults, so unset is a preference, not a failure.
  for name in DB_USE_PG DASH_PROFILE_LABELS DASH_DEFAULT_PROFILE; do
    [ -n "${!name:-}" ] || optional+=("$name")
  done

  if [ "${#required[@]}" -gt 0 ]; then
    echo "::error::Required deploy variable(s) not set: ${required[*]}" >&2
    echo "Set them under GitHub Settings > Secrets and variables > Actions." >&2
    if [ -z "${DATABASE_URL:-}" ]; then
      echo "DATABASE_URL is needed at runtime; lib/db.ts throws without it." >&2
    fi
    return 1
  fi

  # Mirror what lib/db.ts accepts, so CI rejects the same values the app would.
  if ! node -e '
      const u = new URL(process.argv[1]);
      if (u.protocol !== "postgres:" && u.protocol !== "postgresql:") process.exit(1);
    ' "$DATABASE_URL" 2>/dev/null; then
    echo "::error::DATABASE_URL is not a postgres:// or postgresql:// URL." >&2
    return 1
  fi

  echo "Required deploy variables are set."
  if [ "${#optional[@]}" -gt 0 ]; then
    echo "Not set, using code defaults: ${optional[*]}"
  fi
}

# Previews get DATABASE_URL from the Neon integration, scoped to a branch created for the
# deployment. There is therefore no static DATABASE_URL to require -- and one being present
# is the failure this check exists to catch, because it would pin every preview to the same
# database (the old DATABASE_URL_PREVIEW secret, or a Preview-scoped Vercel variable).
# NEON_API_KEY and NEON_PROJECT_ID are required so the post-deploy branch check cannot be
# skipped: without them a preview would deploy without proof that it is isolated.
check_preview_secrets() {
  local required=() name
  for name in VERCEL_TOKEN NEON_API_KEY NEON_PROJECT_ID; do
    [ -n "${!name:-}" ] || required+=("$name")
  done

  if [ "${#required[@]}" -gt 0 ]; then
    echo "::error::Required preview variable(s) not set: ${required[*]}" >&2
    echo "Set them under GitHub Settings > Secrets and variables > Actions." >&2
    if [ -z "${NEON_PROJECT_ID:-}" ]; then
      echo "NEON_PROJECT_ID is the Neon project that Vercel's integration branches." >&2
    fi
    return 1
  fi

  if [ -n "${DATABASE_URL:-}" ]; then
    cat >&2 <<'MSG'
::error::DATABASE_URL is set for previews. Previews must use the Neon integration's
per-deployment branch, not a static database URL. Remove DATABASE_URL from preview.yml,
from the DATABASE_URL_PREVIEW secret, and from Vercel's Preview environment.
MSG
    return 1
  fi

  echo "Preview variables are set and no static DATABASE_URL is present."
}

# A Preview-scoped DATABASE_URL in Vercel project settings would apply to every preview
# deployment and could point them at the production database. The Neon integration injects
# a per-deployment value instead, so a stored Preview DATABASE_URL is a regression -- but
# only if a human put it there. The integration also owns a Preview entry, identified by
# configurationId, whose value is overridden per deployment; that one must be ignored or
# every preview is blocked forever. Unowned entries are still rejected, so the old
# DATABASE_URL_PREVIEW link cannot come back unnoticed.
check_preview_env() {
  local required=() name url body out status=0
  for name in VERCEL_TOKEN VERCEL_PROJECT_ID; do
    [ -n "${!name:-}" ] || required+=("$name")
  done
  if [ "${#required[@]}" -gt 0 ]; then
    echo "::error::Cannot check Vercel's Preview environment; not set: ${required[*]}" >&2
    return 1
  fi

  # v10 is the documented collection endpoint; its items carry configurationId, which is
  # how an integration-owned variable is told apart from a hand-added one.
  url="${VERCEL_API_BASE:-https://api.vercel.com}/v10/projects/${VERCEL_PROJECT_ID}/env"
  if [ -n "${VERCEL_ORG_ID:-}" ]; then
    url="${url}?teamId=${VERCEL_ORG_ID}"
  fi

  # The token goes through stdin, not argv: the process list is readable by every user on
  # the runner, and this repository keeps credentials out of command lines.
  body=$(curl --silent --show-error --fail-with-body --max-time 30 \
    --config - "$url" <<EOF
header = "Authorization: Bearer ${VERCEL_TOKEN}"
header = "Accept: application/json"
EOF
  ) || {
    cat >&2 <<'MSG'
::error::Could not read Vercel's project environment variables. Refusing to deploy a
preview without confirming that no Preview-scoped DATABASE_URL exists. Check VERCEL_TOKEN,
VERCEL_ORG_ID and VERCEL_PROJECT_ID, then re-run.
MSG
    return 1
  }

  # Exit 0 = clean, 3 = unowned offenders (listed on stdout), 2 = unparseable response.
  # The distinction matters: a malformed body must not be reported as a database variable
  # the operator then hunts for in the dashboard.
  out=$(printf '%s' "$body" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
    # v10 returns either {"envs": [...]} (possibly paginated) or a bare array.
    envs = data if isinstance(data, list) else data["envs"]
    if not isinstance(envs, list):
        raise TypeError("envs is not a list")
except Exception:
    print("Vercel did not return a project environment variable list.", file=sys.stderr)
    sys.exit(2)


def integration_owned(env):
    """True when an integration, not a person, owns this variable."""
    if env.get("configurationId"):
        return True
    # Marketplace storage products (Neon included) attach a content hint pointing at the
    # store they provision. Their value is replaced per deployment; a hand-added
    # DATABASE_URL has no store behind it.
    hint = env.get("contentHint")
    return isinstance(hint, dict) and bool(hint.get("storeId"))


bad = []
for env in envs:
    if not isinstance(env, dict):
        continue
    if env.get("key") not in {"DATABASE_URL", "DATABASE_URL_UNPOOLED"}:
        continue
    targets = env.get("target") or []
    if isinstance(targets, str):
        targets = [targets]
    if "preview" not in targets:
        continue
    if integration_owned(env):
        continue
    bad.append(env)

for env in bad:
    print(
        "{key} (id={id}, type={type}, target={target}, gitBranch={branch})".format(
            key=env.get("key"),
            id=env.get("id", "<unknown>"),
            type=env.get("type", "<unknown>"),
            target=env.get("target"),
            branch=env.get("gitBranch") or "<all>",
        )
    )
sys.exit(3 if bad else 0)
') || status=$?

  case "$status" in
    0)
      echo "No unowned Preview-scoped DATABASE_URL in Vercel project settings."
      ;;
    3)
      {
        echo "::error::Vercel has a Preview-scoped DATABASE_URL (or DATABASE_URL_UNPOOLED)"
        echo "that was not created by the Neon integration. That is a static link to one"
        echo "database and can point previews at production:"
        printf '%s\n' "$out" | sed 's/^/  - /'
        echo "Remove it under Vercel > Project > Settings > Environment Variables > Preview;"
        echo "the Neon integration injects the preview branch's URL for each deployment."
      } >&2
      return 1
      ;;
    *)
      cat >&2 <<'MSG'
::error::Could not parse Vercel's environment variable response. Refusing to deploy a
preview without confirming that no Preview-scoped DATABASE_URL exists. Re-run once the
Vercel API is healthy.
MSG
      return 1
      ;;
  esac
}

case "${1:-}" in
  link) check_link ;;
  build) check_build ;;
  secrets) check_secrets ;;
  preview-secrets) check_preview_secrets ;;
  preview-env) check_preview_env ;;
  *)
    echo "usage: $0 <link|build|secrets|preview-secrets|preview-env>" >&2
    exit 2
    ;;
esac