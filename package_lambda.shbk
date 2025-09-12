
#!/usr/bin/env bash
set -euo pipefail
zip -9 lambda.zip lambda_function.py >/dev/null
echo "lambda.zip created"
aws --endpoint-url=http://localhost:4566 lambda delete-function --function-name obs-health 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 lambda create-function   --function-name obs-health   --runtime python3.11   --role arn:aws:iam::000000000000:role/lambda-ex   --handler lambda_function.lambda_handler   --zip-file fileb://lambda.zip >/dev/null
echo "Lambda obs-health created"
