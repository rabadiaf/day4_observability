#!/usr/bin/env bash
set -euo pipefail

usage() { echo "Uso: $0 <200|500>"; exit 2; }

CODE="${1:-}"
[[ "$CODE" == "200" || "$CODE" == "500" ]] || usage

LSE=${LSE:-http://localhost:4566}
FUNC=${FUNC:-obs-health}

awsls() { aws --endpoint-url="$LSE" "$@"; }

# warm-up
awsls lambda get-function --function-name "$FUNC" >/dev/null
awsls lambda invoke --function-name "$FUNC" /dev/null >/devnull 2>&1 || true
sleep 1

# reintentos
for i in {1..8}; do
  if awsls lambda update-function-configuration \
        --function-name "$FUNC" \
        --environment "Variables={STATUS_CODE=${CODE}}"; then
    echo "STATUS_CODE=$CODE aplicado (intento $i)"
    exit 0
  fi
  echo "retry $i: warming up & retrying..."
  awsls lambda invoke --function-name "$FUNC" /dev/null >/dev/null 2>&1 || true
  sleep 1
done

echo "No se pudo actualizar STATUS_CODE tras varios intentos"; exit 1

