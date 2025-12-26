
# Day 4 — Observability & SRE (Lambda /health + alert mock)

**Goal:** Expose a simple health endpoint via API Gateway (LocalStack), log each call with latency, and simulate an alert when /health fails.

## Steps
1) Package and (re)create Lambda.
2) Create or update API Gateway REST API with /health -> Lambda proxy.
3) Curl /health and simulate failure (change code to return 500) to trigger alert script.
4) Document a 5-step runbook.

## Commands
```bash
bash package_lambda.sh
python3 api_setup.py  # prints API invoke URL
bash check_health.sh  # calls the URL and prints OK/ALERT

new user
```
