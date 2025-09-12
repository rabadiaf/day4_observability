#!/usr/bin/env python3
import boto3, sys, json

LSE   = "http://localhost:4566"
REG   = "us-east-1"
ACC   = "000000000000"
FUNC  = "obs-health"
STAGE = "dev"
PATH  = "health"

def ensure_api():
    apig = boto3.client("apigateway", endpoint_url=LSE, region_name=REG,
                        aws_access_key_id="test", aws_secret_access_key="test")
    lam  = boto3.client("lambda", endpoint_url=LSE, region_name=REG,
                        aws_access_key_id="test", aws_secret_access_key="test")

    # 1) API obs-api (idempotente)
    apis = apig.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"] == "obs-api"), None)
    if not api:
        api = apig.create_rest_api(name="obs-api")
    api_id = api["id"]

    # 2) /health (idempotente)
    resources = apig.get_resources(restApiId=api_id)["items"]
    root_id = next(r["id"] for r in resources if r["path"] == "/")
    health = next((r for r in resources if r.get("path") == f"/{PATH}"), None)
    if not health:
        health = apig.create_resource(restApiId=api_id, parentId=root_id, pathPart=PATH)
    res_id = health["id"]

    # 3) Método GET (idempotente)
    try:
        apig.put_method(restApiId=api_id, resourceId=res_id, httpMethod="GET",
                        authorizationType="NONE")
    except apig.exceptions.ConflictException:
        pass

    # 4) Integración Lambda proxy
    uri = (
        f"arn:aws:apigateway:{REG}:lambda:path/2015-03-31/functions/"
        f"arn:aws:lambda:{REG}:{ACC}:function:{FUNC}/invocations"
    )
    apig.put_integration(
        restApiId=api_id,
        resourceId=res_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=uri,
    )

    # 5) Permiso Lambda → API GW (comodines) con SID único por API
    source_arn = f"arn:aws:execute-api:{REG}:{ACC}:{api_id}/*/*/*"
    sid = f"apigw-invoke-{api_id}"
    try:
        lam.add_permission(
            FunctionName=FUNC,
            StatementId=sid,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=source_arn,
        )
    except lam.exceptions.ResourceConflictException:
        lam.remove_permission(FunctionName=FUNC, StatementId=sid)
        lam.add_permission(
            FunctionName=FUNC,
            StatementId=sid,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=source_arn,
        )

    # 6) Deploy

    apig.create_deployment(restApiId=api_id, stageName=STAGE)

    # 7) SIEMPRE imprime la URL (solo stdout)
    url = f"{LSE}/restapis/{api_id}/{STAGE}/_user_request_/{PATH}"
    print(url, flush=True)

    # 8) (Opcional) Diagnóstico: NO hacer fallar el script si falla
    try:
        test = apig.test_invoke_method(restApiId=api_id, resourceId=res_id, httpMethod="GET")
        sys.stderr.write(f"[apig.test] status={test.get('status')} body={test.get('body')}\n")
    except Exception as e:
        sys.stderr.write(f"[apig.test] WARNING: {e}\n")

if __name__ == "__main__":
    ensure_api()

