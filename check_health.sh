
#!/usr/bin/env bash
set -euo pipefail
URL="${1:-}"
if [ -z "$URL" ]; then
  URL=$(python3 api_setup.py)
fi
echo "GET $URL"
HTTP=$(curl -s -o /tmp/health.json -w "%{http_code}" "$URL" || echo "000")
if [ "$HTTP" = "200" ]; then
  echo "OK: $(cat /tmp/health.json)"
else
  echo "ALERT: health check failed (status=$HTTP)"
fi
