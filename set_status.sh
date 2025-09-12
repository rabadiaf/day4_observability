#!/usr/bin/env bash
set -euo pipefail

STATUS_CODE="${1:-200}"
FUNCTION="obs-health"
ENDPOINT="${LSE:-http://localhost:4566}"

# Invoca la función al menos una vez para que LocalStack "active" el $LATEST
echo "Invoking Lambda $FUNCTION to activate it..."
aws lambda invoke \
  --function-name "$FUNCTION" \
  --endpoint-url "$ENDPOINT" \
  --payload '{}' \
  /dev/null || echo "Warning: initial invoke failed"

# Ahora sí: actualiza STATUS_CODE en las env vars
aws lambda update-function-configuration \
  --function-name "$FUNCTION" \
  --endpoint-url "$ENDPOINT" \
  --environment "Variables={STATUS_CODE=$STATUS_CODE}"

