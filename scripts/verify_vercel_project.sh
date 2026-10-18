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
  # The CLI writes the Build Output API directory to join(repoRoot, rootDirectory, .vercel).
  if [ ! -d "$app_root/.vercel/output" ]; then
    echo "::error::'$app_root/.vercel/output' is missing after 'vercel build'." >&2
    echo "The CLI builds at join(repoRoot, Root Directory), so the build did not run in '${app_root}'." >&2
    return 1
  fi
  echo "Build output for '${app_root}' is present."
}

case "${1:-}" in
  link) check_link ;;
  build) check_build ;;
  *)
    echo "usage: $0 <link|build>" >&2
    exit 2
    ;;
esac