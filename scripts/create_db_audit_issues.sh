#!/usr/bin/env bash
# Create — or refresh — one GitHub issue per PostgreSQL audit remediation wave.
#
# The wave-to-issue mapping lives in docs/database/issues/wave-N.md. Each file
# carries YAML frontmatter (title, labels, milestone, size, depends_on, blocks)
# followed by the issue body. This script is the only thing that talks to
# GitHub: it creates missing labels and the milestone, creates each issue if its
# exact title does not already exist, then rewrites only the Dependencies block
# so the "Depends on / Blocks" cross-references can resolve to real numbers.
#
# Safe to re-run. Mutations are skipped when DRY_RUN=1.
#
# Usage:
#   ./scripts/create_db_audit_issues.sh            # create / update
#   DRY_RUN=1 ./scripts/create_db_audit_issues.sh  # show what would happen
#
# Requires an authenticated `gh` (2.40+). If GITHUB_TOKEN is set to an invalid
# value, gh prefers it over its keyring — unset it first.

set -euo pipefail

REPO="${REPO:-jlc254/job-scraper}"
MILESTONE="${MILESTONE:-PostgreSQL audit remediation}"
DUE_DATE="${DUE_DATE:-2026-11-13}"
ISSUES_DIR="${ISSUES_DIR:-docs/database/issues}"
DRY_RUN="${DRY_RUN:-0}"

WAVES=(wave-0 wave-1 wave-2 wave-3 wave-4 wave-5)

declare -A ISSUE_NUMBER=()
declare -A ISSUE_TITLE=()
declare -A DEPENDS_ON=()
declare -A BLOCKS=()

TMPDIR_WORK="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_WORK"' EXIT

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
note() { printf '  %s\n' "$*"; }

# --- frontmatter -----------------------------------------------------------

fm() {
  # fm <file> <key> -> value of <key> in the YAML frontmatter, or empty
  python3 - "$1" "$2" <<'PY'
import pathlib, sys
path, key = sys.argv[1], sys.argv[2]
text = pathlib.Path(path).read_text(encoding="utf-8")
if not text.startswith("---\n"):
    sys.exit(0)
parts = text.split("---\n", 2)
if len(parts) < 3:
    sys.exit(0)
for line in parts[1].splitlines():
    if ":" not in line:
        continue
    name, value = line.split(":", 1)
    if name.strip() == key:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        print(value)
        break
PY
}

body_of() {
  # body_of <file> <outfile> -> write the markdown body (after frontmatter)
  python3 - "$1" "$2" <<'PY'
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
if text.startswith("---\n"):
    parts = text.split("---\n", 2)
    text = parts[2] if len(parts) == 3 else text
pathlib.Path(sys.argv[2]).write_text(text.lstrip("\n"), encoding="utf-8")
PY
}

# --- preconditions ---------------------------------------------------------

[[ -d "$ISSUES_DIR" ]] || die "missing $ISSUES_DIR"
for wave in "${WAVES[@]}"; do
  [[ -f "$ISSUES_DIR/$wave.md" ]] || die "missing $ISSUES_DIR/$wave.md"
done

command -v gh >/dev/null || die "gh is not installed"
command -v python3 >/dev/null || die "python3 is required"

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  # gh prefers GITHUB_TOKEN over the stored credential. A stale or truncated
  # value there looks like "not logged in" even when the keyring is fine, so
  # drop it and retry once before giving up.
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    echo "warning: GITHUB_TOKEN was rejected by gh; retrying with the stored credential." >&2
    unset GITHUB_TOKEN
  fi
fi

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  cat >&2 <<'EOF'
error: gh is not authenticated.

      gh auth login

  Or supply a valid token directly:
      export GH_TOKEN=<token with repo scope>
EOF
  exit 1
fi

for wave in "${WAVES[@]}"; do
  file="$ISSUES_DIR/$wave.md"
  ISSUE_TITLE[$wave]="$(fm "$file" title)"
  [[ -n "${ISSUE_TITLE[$wave]}" ]] || die "$file: missing 'title' in frontmatter"
  DEPENDS_ON[$wave]="$(fm "$file" depends_on)"
  BLOCKS[$wave]="$(fm "$file" blocks)"
done

# --- labels ----------------------------------------------------------------

LABEL_SPECS=(
  "db-audit|5319E7|PostgreSQL audit remediation work"
  "wave-0|0E8A16|Wave 0 — verify and de-risk"
  "wave-1|1D76DB|Wave 1 — repository guardrails"
  "wave-2|B60205|Wave 2 — publish path hardening"
  "wave-3|D93F0B|Wave 3 — migration safety"
  "wave-4|FBCA04|Wave 4 — schema hardening"
  "wave-5|C2E0C6|Wave 5 — decisions and closure"
  "priority:high|B60205|Blocks correctness or recoverability"
  "priority:medium|D93F0B|Should land this cycle"
  "priority:low|FBCA04|Documentation and closure"
  "needs-console|BFD4F2|A human must act in the Neon or Vercel console"
)

echo "Repository: $REPO"
echo "Milestone : $MILESTONE (due $DUE_DATE)"
[[ "$DRY_RUN" == "1" ]] && echo "Mode      : dry run — no changes will be made"
echo

echo "Labels"
existing_labels="$(gh label list --repo "$REPO" --limit 200 --json name --jq '.[].name' || true)"
for spec in "${LABEL_SPECS[@]}"; do
  IFS='|' read -r name color description <<<"$spec"
  if grep -Fxq -- "$name" <<<"$existing_labels"; then
    note "= $name"
  elif [[ "$DRY_RUN" == "1" ]]; then
    note "+ $name (would create)"
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$description" >/dev/null
    note "+ $name"
  fi
done

# --- milestone -------------------------------------------------------------

echo
echo "Milestone"
milestone_exists="$(
  gh api "repos/$REPO/milestones?state=all&per_page=100" \
    --jq '.[].title' 2>/dev/null | grep -Fx -- "$MILESTONE" || true
)"
if [[ -n "$milestone_exists" ]]; then
  note "= $MILESTONE"
elif [[ "$DRY_RUN" == "1" ]]; then
  note "+ $MILESTONE (would create, due $DUE_DATE)"
else
  gh api -X POST "repos/$REPO/milestones" \
    -f "title=$MILESTONE" \
    -f "due_on=${DUE_DATE}T00:00:00Z" \
    -f "description=Findings from docs/database/postgresql-audit-report.md" >/dev/null
  note "+ $MILESTONE"
fi

# --- issues ----------------------------------------------------------------

echo
echo "Issues"
existing_issues="$(gh issue list --repo "$REPO" --state all --limit 300 --json number,title --jq '.[] | "\(.number)\t\(.title)"' || true)"

for wave in "${WAVES[@]}"; do
  title="${ISSUE_TITLE[$wave]}"
  number="$(awk -F'\t' -v t="$title" '$2 == t { print $1; exit }' <<<"$existing_issues")"
  if [[ -n "$number" ]]; then
    ISSUE_NUMBER[$wave]="$number"
    note "= #$number  $title"
    continue
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    note "+ (new)  $title"
    continue
  fi

  body_file="$TMPDIR_WORK/$wave.body.md"
  body_of "$ISSUES_DIR/$wave.md" "$body_file"
  labels="$(fm "$ISSUES_DIR/$wave.md" labels | tr -d '[:space:]')"
  url="$(gh issue create --repo "$REPO" \
    --title "$title" \
    --body-file "$body_file" \
    --milestone "$MILESTONE" \
    --label "$labels")"
  number="${url##*/}"
  ISSUE_NUMBER[$wave]="$number"
  note "+ #$number  $title"
done

# --- resolve cross-references ---------------------------------------------

ref() {
  # ref <wave> -> "#12 (W3)" or "W3 (not created yet)"
  local wave="$1"
  local index="${wave#wave-}"
  if [[ -n "${ISSUE_NUMBER[$wave]:-}" ]]; then
    printf '#%s (W%s)' "${ISSUE_NUMBER[$wave]}" "$index"
  else
    printf 'W%s (not created yet)' "$index"
  fi
}

link_list() {
  # link_list "wave-1, wave-5" -> "#2 (W1), #7 (W5)"
  local spec="$1"
  local out=""
  local item
  IFS=',' read -ra items <<<"$spec"
  for item in "${items[@]}"; do
    item="$(tr -d '[:space:]' <<<"$item")"
    [[ -n "$item" ]] || continue
    out="${out:+$out, }$(ref "$item")"
  done
  printf '%s' "$out"
}

echo
echo "Dependencies"
for wave in "${WAVES[@]}"; do
  number="${ISSUE_NUMBER[$wave]:-}"
  if [[ -z "$number" ]]; then
    note "- $wave skipped (issue not created)"
    continue
  fi

  depends="$(link_list "${DEPENDS_ON[$wave]}")"
  blocks="$(link_list "${BLOCKS[$wave]}")"

  {
    echo "<!-- deps:start -->"
    if [[ -n "$depends" ]]; then
      echo "- **Depends on:** $depends"
    else
      echo "- **Depends on:** nothing — can start immediately."
    fi
    if [[ -n "$blocks" ]]; then
      echo "- **Blocks:** $blocks"
    else
      echo "- **Blocks:** nothing — this is the closing wave."
    fi
    echo "<!-- deps:end -->"
  } >"$TMPDIR_WORK/$wave.deps.md"

  current_body="$(gh issue view "$number" --repo "$REPO" --json body --jq '.body' || true)"

  if ! grep -Fq '<!-- deps:start -->' <<<"$current_body"; then
    note "! #$number has no deps markers — left untouched"
    continue
  fi

  # Exit 1 when the body already matches, so the common re-run stays silent.
  if ! resolved="$(
    DEPFILE="$TMPDIR_WORK/$wave.deps.md" CURRENT="$current_body" python3 - <<'PY'
import os, re, sys
deps = open(os.environ["DEPFILE"], encoding="utf-8").read().strip()
body = os.environ["CURRENT"]
new = re.sub(
    r"<!-- deps:start -->.*?<!-- deps:end -->",
    lambda _match: deps,
    body,
    count=1,
    flags=re.S,
)
if new == body:
    sys.exit(1)
sys.stdout.write(new)
PY
  )"; then
    note "= #$number unchanged"
  elif [[ "$DRY_RUN" == "1" ]]; then
    note "~ #$number would update dependencies"
  else
    printf '%s\n' "$resolved" >"$TMPDIR_WORK/$wave.body.new.md"
    gh issue edit "$number" --repo "$REPO" --body-file "$TMPDIR_WORK/$wave.body.new.md" >/dev/null
    note "~ #$number dependencies updated"
  fi
done

echo
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Dry run complete. Re-run without DRY_RUN=1 to apply."
else
  echo "Done. Review the milestone:"
  echo "  gh issue list --repo $REPO --milestone \"$MILESTONE\""
fi
