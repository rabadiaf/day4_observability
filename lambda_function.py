# lambda_function.py
import os
import json

def lambda_handler(event, context):
    code = int(os.getenv("STATUS_CODE", "200"))
    return {
        "statusCode": code,
        "body": json.dumps({"message": "ok" if code == 200 else "error"}),
        "headers": {"Content-Type": "application/json"}
    }

