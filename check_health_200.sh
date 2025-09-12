#!/usr/bin/env bash
set -euo pipefail
URL="${1:?uso: check_health_200.sh URL}"
./set_status.sh 200
bash ./check_health.sh "$URL"   # falla si no es 200

