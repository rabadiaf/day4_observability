#!/usr/bin/env python3
import boto3

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

    # 1) API obs-api (crear si no existe)
    apis = apig.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"] == "obs-api"), None)
    if not api:
        api = apig.create_rest_api(name="obs-api")
    api_id = api["id"]

    # 2) Recursos: / y /health (crear si falta)
    resources = apig.get_resources(restApiId=api_id)["items"]
    root_id = next(r["id"] for r in resources if r.get("path") == "/")
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

    # 5) Permiso para que API GW invoque la Lambda (usar comodines y SID por API)
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
        # Si ya existía con otro SourceArn, lo reemplazamos
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

    # 7) URL final
    url = f"{LSE}/restapis/{api_id}/{STAGE}/_user_request_/{PATH}"
    print(url)

if __name__ == "__main__":
    ensure_api()

