#!/usr/bin/env bash
# Write a verified, custom-format logical dump of the production database.
#
# Neon Free keeps six hours of point-in-time recovery and nothing else, so a mistake on
# main that is noticed the next morning has no restore point left. This script is the
# outside copy: it dumps through a direct connection, proves the artifact is readable
# before publishing it, and leaves the previous artifact untouched on any failure.
#
# Usage:
#   NEON_DATABASE_URL_PUBLISHER='postgresql://...' bash scripts/db_dump.sh
#   NEON_DATABASE_URL_PUBLISHER='postgresql://...' DUMP_DIR=backups bash scripts/db_dump.sh
#
# Env contract:
#   NEON_DATABASE_URL_PUBLISHER  required; the DIRECT (non-pooled) host
#   DUMP_DIR                     default .; created when missing
#   DOCKER                       default docker; overridable so tests can stub the client
#
# Exit 0 with backup-YYYYMMDD.dump in DUMP_DIR. Exit 2 for a missing or pooled DSN,
# 1 when the dump or its verification fails. On any failure no artifact is left behind.
set -euo pipefail

dsn="${NEON_DATABASE_URL_PUBLISHER:-}"
# pgbouncer in transaction mode does not keep a pg_dump session on one backend, so a
# pooled host can produce a dump that misses or duplicates data without erroring. The
# direct host is the only one this script may use (docs/database/postgresql-audit-report.md
# SEC-06).
case "$dsn" in
  "")
    echo "NEON_DATABASE_URL_PUBLISHER is required." >&2
    exit 2
    ;;
  *-pooler.*)
    echo "refusing pooled DSN for pg_dump; use the direct (non-pooled) host." >&2
    exit 2
    ;;
esac

dump_dir="${DUMP_DIR:-.}"
docker_bin="${DOCKER:-docker}"
# Ubuntu 24.04 runners ship PostgreSQL 16 clients, which refuse a PG 18 server. The dump
# therefore runs inside the server-matching image, not on the runner.
image="postgres:18"
# A custom dump of this schema is well over 100 KB. 10 KB admits an empty database while
# still catching a connection that produced only a header (which pg_restore --list would
# otherwise accept).
min_bytes=10240

mkdir -p "$dump_dir"
# docker requires an absolute bind-mount source; a relative DUMP_DIR would be resolved
# against the daemon's cwd, not the runner's.
dump_dir=$(cd "$dump_dir" && pwd)

name="backup-$(date -u +%Y%m%d).dump"
tmp_name=".${name}.tmp"
tmp_path="$dump_dir/$tmp_name"
final_path="$dump_dir/$name"

rm -f "$tmp_path"

# PGURL and DUMP_NAME reach the container as environment variables so that neither the
# password nor the file name appears in the docker client's argv, which every user on the
# runner can read from /proc. The container's sh does the expansion.
export PGURL="$dsn"
export DUMP_NAME="$tmp_name"

if ! "$docker_bin" run --rm \
  --user "$(id -u):$(id -g)" \
  --env PGURL \
  --env DUMP_NAME \
  --volume "$dump_dir:/out" \
  "$image" \
  sh -c 'exec pg_dump "$PGURL" --format=custom --no-owner --no-privileges --file "/out/$DUMP_NAME"'; then
  rm -f "$tmp_path"
  echo "pg_dump failed; no backup was written." >&2
  exit 1
fi

size=$(stat -c '%s' "$tmp_path" 2>/dev/null || echo 0)
if [ "$size" -lt "$min_bytes" ]; then
  rm -f "$tmp_path"
  echo "the dump is too small (${size} bytes < ${min_bytes}); no backup was written." >&2
  exit 1
fi

# pg_restore --list parses the whole archive index without touching a server, so it proves
# the file is a complete, readable custom-format dump rather than a network-truncated one.
if ! "$docker_bin" run --rm \
  --user "$(id -u):$(id -g)" \
  --env DUMP_NAME \
  --volume "$dump_dir:/out" \
  "$image" \
  sh -c 'exec pg_restore --list "/out/$DUMP_NAME" >/dev/null'; then
  rm -f "$tmp_path"
  echo "the dump failed pg_restore --list; no backup was written." >&2
  exit 1
fi

# The artifact appears only after both checks pass, and under the name the workflow
# uploads. A concurrent run is prevented by the workflow's concurrency group.
mv "$tmp_path" "$final_path"
echo "Wrote $final_path (${size} bytes) and verified it with pg_restore --list."
