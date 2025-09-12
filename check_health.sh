#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
if [ -z "$URL" ]; then
  URL=$(python3 api_setup.py)
fi

echo "GET $URL"

START=$(date +%s%3N)
HTTP=$(curl -s -o /tmp/health.json -w "%{http_code}" "$URL" || echo "000")
END=$(date +%s%3N)
ELAPSED=$((END - START))

if [ "$HTTP" = "200" ]; then
  echo "OK: $(cat /tmp/health.json)"
  echo "Health check passed in ${ELAPSED} ms"
  exit 0
else
  echo "ALERT: health check failed (status=$HTTP)"
  echo "Health check failed in ${ELAPSED} ms"
  exit 1
fi

