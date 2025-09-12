# api_setup.py (idempotente)
import os, boto3, json, time, uuid

ENDPOINT = os.getenv("LSE", "http://localhost:4566")
REGION   = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
NAME     = os.getenv("API_NAME", "observability-api")
FUNC     = "obs-health"
LAMBDA_ARN = f"arn:aws:lambda:{REGION}:000000000000:function:{FUNC}"

apig = boto3.client("apigateway", endpoint_url=ENDPOINT, region_name=REGION)
lam  = boto3.client("lambda",      endpoint_url=ENDPOINT, region_name=REGION)

def find_api_id():
    apis = apig.get_rest_apis().get("items", [])
    for a in apis:
        if a.get("name") == NAME:
            return a["id"]
    return None

api_id = find_api_id()
if not api_id:
    api_id = apig.create_rest_api(name=NAME)["id"]

root_id = next(r["id"] for r in apig.get_resources(restApiId=api_id)["items"] if r["path"] == "/")

# Asegura /health limpio (si ya existe, reutilízalo; si no, créalo)
resources = apig.get_resources(restApiId=api_id)["items"]
health = next((r for r in resources if r.get("path") == "/health"), None)
if not health:
    health = apig.create_resource(restApiId=api_id, parentId=root_id, pathPart="health")
res_id = health["id"]

# Método GET (idempotente)
try:
    apig.put_method(restApiId=api_id, resourceId=res_id, httpMethod="GET", authorizationType="NONE")
except apig.exceptions.ConflictException:
    pass

# Integración proxy a Lambda (idempotente)
uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{LAMBDA_ARN}/invocations"
try:
    apig.put_integration(
        restApiId=api_id, resourceId=res_id, httpMethod="GET",
        type="AWS_PROXY", integrationHttpMethod="POST", uri=uri
    )
except apig.exceptions.ConflictException:
    # Actualiza la integración por si quedó con otra URI
    apig.update_integration(
        restApiId=api_id, resourceId=res_id, httpMethod="GET",
        patchOperations=[{"op":"replace","path":"/uri","value":uri}]
    )

# Permiso para que APIGW invoque a Lambda (idempotente)
sid = f"apigw-health-{uuid.uuid4()}"
try:
    lam.add_permission(
        FunctionName=FUNC, StatementId=sid, Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn=f"arn:aws:execute-api:{REGION}:000000000000:{api_id}/*/GET/health"
    )
except lam.exceptions.ResourceConflictException:
    pass

# Deploy stage dev
apig.create_deployment(restApiId=api_id, stageName="dev")

# Warm-up Lambda (LocalStack a veces lo necesita)
try:
    lam.invoke(FunctionName=FUNC, Payload=b"{}")
except Exception:
    pass

url = f"http://localhost:4566/restapis/{api_id}/dev/_user_request_/health"
print(url)

