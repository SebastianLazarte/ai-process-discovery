#!/usr/bin/env bash
# Runs on the GitHub runner, in the `deploy` job of the release workflow (ADR 0008, RS-67).
# It asks the demo host to deploy one tag over SSH:
#
#   DEPLOY_HOST=... DEPLOY_SSH_KEY=... DEPLOY_KNOWN_HOSTS=... deploy/release-deploy.sh v1.4.0
#
# The host key is pinned: SSH checks it against DEPLOY_KNOWN_HOSTS only and never accepts a
# new one. The key's authorized_keys entry forces /opt/apd/deploy.sh, so the remote command
# is the tag alone, which deploy.sh reads from SSH_ORIGINAL_COMMAND and validates again.

set -euo pipefail

fail() {
  echo "release-deploy: $*" >&2
  exit 1
}

(($# == 1)) || fail "expected one tag like v1.2.3, got $# arguments"
tag="$1"
if [[ "$tag" == *[!v0-9.]* || ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  fail "expected a tag like v1.2.3, got '${tag}'"
fi
for variable in DEPLOY_HOST DEPLOY_SSH_KEY DEPLOY_KNOWN_HOSTS; do
  [[ -n "${!variable:-}" ]] || fail "$variable is empty; set it in the production environment"
done

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
umask 077
printf '%s\n' "$DEPLOY_SSH_KEY" >"$workdir/key"
printf '%s\n' "$DEPLOY_KNOWN_HOSTS" >"$workdir/known_hosts"

ssh \
  -i "$workdir/key" \
  -o IdentitiesOnly=yes \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$workdir/known_hosts" \
  -o GlobalKnownHostsFile=/dev/null \
  -o ConnectTimeout=20 \
  "${DEPLOY_USER:-apd}@${DEPLOY_HOST}" \
  "$tag"
