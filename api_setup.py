
#!/usr/bin/env python3
import boto3, json, time, sys

LSE = "http://localhost:4566"
REG = "us-east-1"

def ensure_api():
    apig = boto3.client("apigateway", endpoint_url=LSE, region_name=REG,
                        aws_access_key_id="test", aws_secret_access_key="test")
    # Create REST API
    apis = apig.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"]=="obs-api"), None)
    if not api:
        api = apig.create_rest_api(name="obs-api")
    api_id = api["id"]
    # Root
    root_id = apig.get_resources(restApiId=api_id)["items"][0]["id"]
    # Create /health if missing
    resources = apig.get_resources(restApiId=api_id)["items"]
    health = next((r for r in resources if r.get("path") == "/health"), None)
    if not health:
        health = apig.create_resource(restApiId=api_id, parentId=root_id, pathPart="health")
    res_id = health["id"]
    # Methods & integration
    try:
        apig.put_method(restApiId=api_id, resourceId=res_id, httpMethod="GET",
                        authorizationType="NONE")
    except apig.exceptions.ConflictException:
        pass
    # Lambda integration (proxy)
    uri = f"arn:aws:apigateway:{REG}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REG}:000000000000:function:obs-health/invocations"
    apig.put_integration(restApiId=api_id, resourceId=res_id, httpMethod="GET",
                         type="AWS_PROXY", integrationHttpMethod="POST", uri=uri)
    # Deploy
    apig.create_deployment(restApiId=api_id, stageName="dev")
    url = f"{LSE}/restapis/{api_id}/dev/_user_request_/health"
    print(url)

if __name__ == "__main__":
    ensure_api()
