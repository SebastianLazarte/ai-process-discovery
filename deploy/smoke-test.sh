#!/usr/bin/env bash
# Checks the live demo through Nginx and TLS after a deploy (ADR 0008, RS-67, RS-79):
#
#   deploy/smoke-test.sh https://apd.example.com
#
# The home page and the API health check must answer without an error over HTTPS: / is the
# Next.js client from 2.0.0 (ADR 0016) and /api/health the API. Any error, a certificate
# problem included, fails the job. deploy.sh has already checked both services on the host;
# this proves the public edge.

set -euo pipefail

fail() {
  echo "smoke-test: $*" >&2
  exit 1
}

(($# == 1)) || fail "expected the demo URL, got $# arguments"
base="${1%/}"
[[ "$base" == https://* ]] || fail "expected an https:// URL, got '${base}'"

for path in / /api/health; do
  echo "smoke-test: GET ${base}${path}"
  curl --fail --silent --show-error --output /dev/null \
    --proto '=https' --max-time 20 \
    --retry 5 --retry-delay 5 --retry-all-errors \
    "${base}${path}" || fail "${base}${path} failed over HTTPS"
done
echo "smoke-test: ${base} is up"
