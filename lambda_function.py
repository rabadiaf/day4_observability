import os

def lambda_handler(event, context):
    status = int(os.getenv("STATUS_CODE", "200"))
    body = {"status": status, "message": "ok" if status == 200 else "error"}
    return {
        "statusCode": status,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"}
    }

