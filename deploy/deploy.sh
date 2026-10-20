#!/usr/bin/env bash
# Deploys one release of the public demo (ADR 0008, RS-66): back up the database, pull the
# image, run the migrations, start it and check /health. If the check fails, the previous
# version starts again and the script exits with an error.
#
#   sudo -u apd /opt/apd/deploy.sh v1.4.0
#
# The deploy key's authorized_keys entry forces this script, so over SSH the tag arrives in
# SSH_ORIGINAL_COMMAND. That value is only matched against vX.Y.Z, never run.
#
# Migrations follow expand and contract (runbook, "Roll back"), so the previous image keeps
# working on the migrated schema. A wrong migration is undone from the pre-deploy dump.

set -euo pipefail

APD_DIR="${APD_DIR:-/opt/apd}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/apd}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8100/health}"
HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-20}"
HEALTH_DELAY="${HEALTH_DELAY:-3}"

log() { echo "deploy: $*"; }
fail() {
  echo "deploy: $*" >&2
  exit 1
}

(($# <= 1)) || fail "expected a tag like v1.2.3, got $# arguments"
tag="${1:-${SSH_ORIGINAL_COMMAND:-}}"
# Only v, digits and dots get past the first check, so no newline or shell syntax reaches
# the regex or any later command.
if [[ "$tag" == *[!v0-9.]* || ! "$tag" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
  fail "expected a tag like v1.2.3, got '${tag}'"
fi
version="${BASH_REMATCH[1]}"

cd "$APD_DIR"
exec 9>"$APD_DIR/.deploy.lock"
flock --nonblock 9 || fail "another deploy is running"

previous="$(sed -n 's/^APD_VERSION=//p' .env)"
[[ -n "$previous" ]] || fail "APD_VERSION is missing from $APD_DIR/.env"

# Runs docker compose with one version of the API image; compose reads the rest from .env.
compose() {
  local image_version="$1"
  shift
  APD_VERSION="$image_version" docker compose "$@"
}

healthy() {
  local attempt
  for ((attempt = 1; attempt <= HEALTH_ATTEMPTS; attempt++)); do
    curl --fail --silent --output /dev/null "$HEALTH_URL" && return 0
    sleep "$HEALTH_DELAY"
  done
  return 1
}

mkdir -p "$BACKUP_DIR"
backup="$BACKUP_DIR/pre-deploy-$(date -u +%Y%m%dT%H%M%SZ)-v${previous}-to-${tag}.dump"
trap 'rm -f "$backup.partial"' EXIT
log "backing up the database to $backup"
compose "$previous" exec -T postgres pg_dump --username=apd --format=custom apd >"$backup.partial"
mv "$backup.partial" "$backup"

log "pulling $tag"
compose "$version" pull api
log "migrating the database for $tag"
compose "$version" run --rm api alembic upgrade head

log "starting $tag"
if compose "$version" up --detach api && healthy; then
  sed -i "s/^APD_VERSION=.*/APD_VERSION=${version}/" .env
  log "$tag is live"
else
  log "$tag failed its health check, starting v$previous again"
  compose "$previous" up --detach api
  fail "$tag was rolled back to v$previous; the pre-deploy dump is $backup"
fi
