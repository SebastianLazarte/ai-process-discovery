#!/usr/bin/env bash
# Nightly backup of the public demo database (ADR 0008, RS-68), run by apd-backup.timer:
#
#   /opt/apd/backup.sh
#
# Writes /var/backups/apd/nightly-<UTC time>.dump, then deletes every dump older than
# RETENTION_DAYS (7), the pre-deploy dumps of deploy.sh included. Old dumps go only after
# tonight's dump is complete, so a failed backup never leaves the folder empty. Dumps never
# leave the host.

set -euo pipefail

APD_DIR="${APD_DIR:-/opt/apd}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/apd}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

fail() {
  echo "backup: $*" >&2
  exit 1
}

[[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]] || fail "RETENTION_DAYS must be a positive number"

cd "$APD_DIR"
mkdir -p "$BACKUP_DIR"
dump="$BACKUP_DIR/nightly-$(date -u +%Y%m%dT%H%M%SZ).dump"
trap 'rm -f "$dump.partial"' EXIT

docker compose exec -T postgres pg_dump --username=apd --format=custom apd >"$dump.partial"
[[ -s "$dump.partial" ]] || fail "pg_dump wrote nothing"
mv "$dump.partial" "$dump"
echo "backup: wrote $dump"

find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.dump' \
  -mmin "+$((RETENTION_DAYS * 24 * 60))" -print -delete |
  sed 's/^/backup: deleted /'
