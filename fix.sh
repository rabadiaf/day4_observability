#!/usr/bin/env bash
set -euo pipefail

# === Config ===
LSE=${LSE:-http://localhost:4566}
REG=${REG:-us-east-1}
ACC=${ACC:-000000000000}
FUNC=${FUNC:-obs-health}
PATH_PART=${PATH_PART:-health}   # <--- NO usar PATH
STAGE=${STAGE:-dev}

# Restaura PATH del sistema por si fue pisado
export PATH="${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"

# Ubica binarios
AWS="$(command -v aws)"
JQ="$(command -v jq)"

# Sanity check
"$AWS" --version >/dev/null
"$JQ" --version >/dev/null

# 1) API obs-api (crear si no existe)
API_ID=$("$AWS" --endpoint-url="$LSE" apigateway get-rest-apis \
  | "$JQ" -r '.items[] | select(.name=="obs-api") | .id')
if [[ -z "${API_ID}" || "${API_ID}" == "null" ]]; then
  API_ID=$("$AWS" --endpoint-url="$LSE" apigateway create-rest-api --name obs-api \
    | "$JQ" -r .id)
fi
echo "API_ID=$API_ID"

# 2) Recursos: raíz y /health (crear si falta)
ROOT_ID=$("$AWS" --endpoint-url="$LSE" apigateway get-resources --rest-api-id "$API_ID" \
  | "$JQ" -r '.items[] | select(.path=="/") | .id')
RES_ID=$("$AWS" --endpoint-url="$LSE" apigateway get-resources --rest-api-id "$API_ID" \
  | "$JQ" -r --arg p "/${PATH_PART}" '.items[] | select(.path==$p) | .id')
if [[ -z "${RES_ID}" || "${RES_ID}" == "null" ]]; then
  RES_ID=$("$AWS" --endpoint-url="$LSE" apigateway create-resource \
    --rest-api-id "$API_ID" --parent-id "$ROOT_ID" --path-part "$PATH_PART" \
    | "$JQ" -r .id)
fi
echo "RES_ID=$RES_ID"

# 3) Método GET (idempotente)
"$AWS" --endpoint-url="$LSE" apigateway put-method \
  --rest-api-id "$API_ID" --resource-id "$RES_ID" \
  --http-method GET --authorization-type "NONE" >/dev/null 2>&1 || true

# 4) Integración Lambda proxy (ARN correcto con 'arn:aws:apigateway')
"$AWS" --endpoint-url="$LSE" apigateway put-integration \
  --rest-api-id "$API_ID" --resource-id "$RES_ID" \
  --http-method GET \
  --type AWS_PROXY --integration-http-method POST \
  --uri "arn:aws:apigateway:${REG}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REG}:${ACC}:function:${FUNC}/invocations" >/dev/null

# 5) Permiso para que API GW invoque la Lambda (idempotente)
"$AWS" --endpoint-url="$LSE" lambda add-permission \
  --function-name "$FUNC" \
  --statement-id apigw-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REG}:${ACC}:${API_ID}/*/GET/${PATH_PART}" \
  >/dev/null 2>&1 || true

# 6) Deploy del stage
"$AWS" --endpoint-url="$LSE" apigateway create-deployment \
  --rest-api-id "$API_ID" --stage-name "$STAGE" >/dev/null

# 7) URL final
URL="${LSE}/restapis/${API_ID}/${STAGE}/_user_request_/${PATH_PART}"
echo "$URL"

