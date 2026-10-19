#!/usr/bin/env bash
# Checks the live demo through Nginx and TLS after a deploy (ADR 0008, RS-67):
#
#   deploy/smoke-test.sh https://apd.example.com
#
# Every path must answer 2xx over HTTPS. Any error, a certificate problem included, fails the
# job. deploy.sh has already checked /health on the host; this proves the public edge.

set -euo pipefail

fail() {
  echo "smoke-test: $*" >&2
  exit 1
}

(($# == 1)) || fail "expected the demo URL, got $# arguments"
base="${1%/}"
[[ "$base" == https://* ]] || fail "expected an https:// URL, got '${base}'"

for path in /health /ui/; do
  echo "smoke-test: GET ${base}${path}"
  curl --fail --silent --show-error --output /dev/null \
    --proto '=https' --max-time 20 \
    --retry 5 --retry-delay 5 --retry-all-errors \
    "${base}${path}" || fail "${base}${path} did not answer 2xx over HTTPS"
done
echo "smoke-test: ${base} is up"
