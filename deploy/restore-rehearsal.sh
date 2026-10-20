#!/usr/bin/env bash
# Rehearses a restore of the demo database (ADR 0008, RS-68):
#
#   /opt/apd/restore-rehearsal.sh                               # newest nightly dump
#   /opt/apd/restore-rehearsal.sh /var/backups/apd/<file>.dump  # a chosen dump
#
# It loads the dump into a throwaway PostgreSQL container, counts the rows of each table and
# prints a row for the table in "Backups and restore" of docs/runbook/production.md. The
# container has no volume and no network, so the live database is never touched, and it is
# removed when the script ends.

set -euo pipefail
shopt -s nullglob

APD_DIR="${APD_DIR:-/opt/apd}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/apd}"
CONTAINER="${CONTAINER:-apd-restore-rehearsal}"
READY_ATTEMPTS="${READY_ATTEMPTS:-30}"
READY_DELAY="${READY_DELAY:-2}"
TABLES=(processes process_steps analyses recommendation_overrides)

fail() {
  echo "restore-rehearsal: $*" >&2
  exit 1
}

(($# <= 1)) || fail "expected at most one dump, got $# arguments"
if (($# == 1)); then
  dump="$1"
else
  # Names carry the UTC time, so the last one in glob order is the newest.
  dumps=("$BACKUP_DIR"/nightly-*.dump)
  ((${#dumps[@]} > 0)) || fail "no nightly dump in $BACKUP_DIR"
  dump="${dumps[-1]}"
fi
[[ -s "$dump" ]] || fail "$dump is missing or empty"

cd "$APD_DIR"
image="$(docker compose config --images | grep -m 1 '^postgres')" ||
  fail "no postgres image in the compose file"

docker rm --force "$CONTAINER" >/dev/null 2>&1 || true
trap 'docker rm --force "$CONTAINER" >/dev/null 2>&1 || true' EXIT
docker run --detach --name "$CONTAINER" --network none \
  --env POSTGRES_PASSWORD=rehearsal "$image" >/dev/null

# The image runs a socket-only server while it initialises, so wait for TCP on loopback.
ready=""
for ((attempt = 1; attempt <= READY_ATTEMPTS; attempt++)); do
  if docker exec "$CONTAINER" pg_isready --host=127.0.0.1 --username=postgres --quiet; then
    ready=yes
    break
  fi
  sleep "$READY_DELAY"
done
[[ -n "$ready" ]] || fail "the scratch database did not start"

docker exec "$CONTAINER" createdb --username=postgres apd
docker exec --interactive "$CONTAINER" pg_restore --username=postgres --dbname=apd \
  --no-owner --no-privileges --exit-on-error <"$dump"

counts=""
for table in "${TABLES[@]}"; do
  rows="$(docker exec "$CONTAINER" psql --username=postgres --dbname=apd \
    --tuples-only --no-align --command="SELECT count(*) FROM $table")"
  counts+="${counts:+, }$table $rows"
done

echo "restore-rehearsal: $dump restored. Add this row to the runbook:"
echo "| $(date -u +%Y-%m-%d) | $(basename "$dump") | Restored: $counts |"
