#!/usr/bin/env bash
# Deploys one release of the public demo (ADR 0008, RS-66, RS-79): back up the database,
# pull the images, run the migrations, start the services and check their health. If a
# check fails, each service starts again on the version it ran before, and the script exits
# with an error.
#
#   sudo -u apd /opt/apd/deploy.sh v2.0.0
#
# Each service keeps its own version in .env (ADR 0016): APD_VERSION for the API and
# APD_WEB_VERSION for the web client. A 2.x tag or later moves both. A 1.x tag moves the API
# only, because a 1.x web image still serves its pages under /app.
#
# The deploy key's authorized_keys entry forces this script, so over SSH the tag arrives in
# SSH_ORIGINAL_COMMAND. That value is only matched against vX.Y.Z, never run.
#
# Migrations follow expand and contract (runbook, "Roll back"), so the previous image keeps
# working on the migrated schema. A wrong migration is undone from the pre-deploy dump.

set -euo pipefail

APD_DIR="${APD_DIR:-/opt/apd}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/apd}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8100/api/health}"
WEB_HEALTH_URL="${WEB_HEALTH_URL:-http://127.0.0.1:8101/}"
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
if [[ "$tag" == *[!v0-9.]* || ! "$tag" =~ ^v(([0-9]+)\.[0-9]+\.[0-9]+)$ ]]; then
  fail "expected a tag like v1.2.3, got '${tag}'"
fi
version="${BASH_REMATCH[1]}"
major="${BASH_REMATCH[2]}"

cd "$APD_DIR"
exec 9>"$APD_DIR/.deploy.lock"
flock --nonblock 9 || fail "another deploy is running"

previous_api="$(sed -n 's/^APD_VERSION=//p' .env)"
previous_web="$(sed -n 's/^APD_WEB_VERSION=//p' .env)"
[[ -n "$previous_api" ]] || fail "APD_VERSION is missing from $APD_DIR/.env"
[[ -n "$previous_web" ]] || fail "APD_WEB_VERSION is missing from $APD_DIR/.env"

if ((10#$major >= 2)); then
  services=(api web)
  next_web="$version"
else
  services=(api)
  next_web="$previous_web"
fi

# Runs docker compose with one version per service; compose reads the rest from .env.
compose() {
  local api_version="$1" web_version="$2"
  shift 2
  APD_VERSION="$api_version" APD_WEB_VERSION="$web_version" docker compose "$@"
}

healthy() {
  local url="$1" attempt
  for ((attempt = 1; attempt <= HEALTH_ATTEMPTS; attempt++)); do
    curl --fail --silent --output /dev/null "$url" && return 0
    sleep "$HEALTH_DELAY"
  done
  return 1
}

all_healthy() {
  healthy "$HEALTH_URL" || return 1
  [[ " ${services[*]} " != *" web "* ]] || healthy "$WEB_HEALTH_URL"
}

mkdir -p "$BACKUP_DIR"
backup="$BACKUP_DIR/pre-deploy-$(date -u +%Y%m%dT%H%M%SZ)-v${previous_api}-to-${tag}.dump"
trap 'rm -f "$backup.partial"' EXIT
log "backing up the database to $backup"
compose "$previous_api" "$previous_web" exec -T postgres \
  pg_dump --username=apd --format=custom apd >"$backup.partial"
mv "$backup.partial" "$backup"

log "pulling $tag for ${services[*]}"
compose "$version" "$next_web" pull "${services[@]}"
log "migrating the database for $tag"
compose "$version" "$next_web" run --rm api alembic upgrade head

log "starting $tag for ${services[*]}"
if compose "$version" "$next_web" up --detach "${services[@]}" && all_healthy; then
  sed -i -e "s/^APD_VERSION=.*/APD_VERSION=${version}/" \
    -e "s/^APD_WEB_VERSION=.*/APD_WEB_VERSION=${next_web}/" .env
  log "$tag is live for ${services[*]}"
else
  log "$tag failed a health check, starting API v$previous_api and web v$previous_web again"
  compose "$previous_api" "$previous_web" up --detach "${services[@]}"
  fail "$tag was rolled back to API v$previous_api and web v$previous_web; the pre-deploy dump is $backup"
fi
