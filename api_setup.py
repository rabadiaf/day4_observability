import boto3
import json
import os

ENDPOINT = os.getenv("LSE", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
LAMBDA_ARN = f"arn:aws:lambda:{REGION}:000000000000:function:obs-health"

client = boto3.client("apigateway", endpoint_url=ENDPOINT, region_name=REGION)
lambda_client = boto3.client("lambda", endpoint_url=ENDPOINT, region_name=REGION)

# 1. Crear el REST API
api = client.create_rest_api(name="observability-api")
api_id = api["id"]

# 2. Obtener ID del recurso raíz /
resources = client.get_resources(restApiId=api_id)
root_id = next(r["id"] for r in resources["items"] if r["path"] == "/")

# 3. Crear recurso /health
res = client.create_resource(restApiId=api_id, parentId=root_id, pathPart="health")
res_id = res["id"]

# 4. Agregar método GET
client.put_method(
    restApiId=api_id,
    resourceId=res_id,
    httpMethod="GET",
    authorizationType="NONE"
)

# 5. Integrar con Lambda
client.put_integration(
    restApiId=api_id,
    resourceId=res_id,
    httpMethod="GET",
    type="AWS_PROXY",
    integrationHttpMethod="POST",
    uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{LAMBDA_ARN}/invocations"
)

# 6. Dar permiso a API Gateway para invocar Lambda
try:
    lambda_client.add_permission(
        FunctionName="obs-health",
        StatementId="apigateway-health",
        Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn=f"arn:aws:execute-api:{REGION}:000000000000:{api_id}/*/GET/health"
    )
except lambda_client.exceptions.ResourceConflictException:
    pass  # Ya existe

# 7. Deploy API
client.create_deployment(restApiId=api_id, stageName="dev")

# 8. Imprimir URL final
url = f"http://localhost:4566/restapis/{api_id}/dev/_user_request_/health"
print(url)

