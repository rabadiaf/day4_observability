#!/usr/bin/env bash
set -euo pipefail

LSE=${LSE:-http://localhost:4566}

awsls() {
  aws --endpoint-url="$LSE" "$@"
}

# ahora sí:
awsls lambda update-function-configuration \
  --function-name obs-health \
  --environment "Variables={STATUS_CODE=500}"

