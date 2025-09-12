import json, time, os

def lambda_handler(event, context):
    t0 = time.time()
    status = int(os.getenv("STATUS_CODE", "200"))
    body = {"ok": status == 200, "ts": time.time()}
    latency_ms = int((time.time() - t0) * 1000)
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"body": body, "latency_ms": latency_ms})
    }

