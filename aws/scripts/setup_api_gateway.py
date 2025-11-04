#!/usr/bin/env python3
"""Setup API Gateway for SpendSense insights Lambda functions.

This script creates an API Gateway REST API with endpoints for all insights Lambda functions.

Usage:
    python aws/scripts/setup_api_gateway.py
"""

import boto3
import json
import yaml
from pathlib import Path
from botocore.exceptions import ClientError

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "aws_config.yaml"
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

aws_config = config['aws']
region = aws_config['region']
profile = aws_config.get('profile', 'default')

session = boto3.Session(profile_name=profile, region_name=region)
apigateway_client = session.client('apigateway')
lambda_client = session.client('lambda')

api_config = config['api_gateway']
api_name = api_config['name']
stage_name = api_config['stage']


def create_api_gateway():
    """Create API Gateway REST API."""
    print("Creating API Gateway...")
    
    try:
        # Create REST API
        api_response = apigateway_client.create_rest_api(
            name=api_name,
            description=api_config['description'],
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )
        
        api_id = api_response['id']
        api_root_id = api_response['rootResourceId']
        
        print(f"  ✅ Created API Gateway: {api_name} (ID: {api_id})")
        
        return api_id, api_root_id
        
    except ClientError as e:
        if 'ConflictException' in str(e):
            # API already exists, find it
            apis = apigateway_client.get_rest_apis()
            for api in apis['items']:
                if api['name'] == api_name:
                    api_id = api['id']
                    resources = apigateway_client.get_resources(restApiId=api_id)
                    api_root_id = resources['items'][0]['id']
                    print(f"  ⚠️  API Gateway already exists: {api_name} (ID: {api_id})")
                    return api_id, api_root_id
        
        print(f"  ❌ Error creating API Gateway: {e}")
        raise


def create_resource(api_id: str, parent_id: str, path_part: str) -> str:
    """Create a resource in API Gateway.
    
    Args:
        api_id: API ID
        parent_id: Parent resource ID
        path_part: Path segment
    
    Returns:
        Resource ID
    """
    try:
        response = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return response['id']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            # Resource exists, find it
            resources = apigateway_client.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == path_part:
                    return resource['id']
        raise


def create_lambda_integration(api_id: str, resource_id: str, lambda_function_name: str, http_method: str = 'GET'):
    """Create Lambda integration for API Gateway resource.
    
    Args:
        api_id: API ID
        resource_id: Resource ID
        lambda_function_name: Lambda function name
        http_method: HTTP method (GET, POST, etc.)
    
    Returns:
        True if integration created, False if Lambda function doesn't exist
    """
    # Check if Lambda function exists
    try:
        lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"    ⚠️  Lambda function {lambda_function_name} not found - skipping integration")
            print(f"       Deploy Lambda function first: python aws/scripts/deploy_lambda.py {lambda_function_name.split('-')[-2]}")
            return False
        raise
    
    # Give API Gateway permission to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'api-gateway-invoke-{api_id}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{region}:*:{api_id}/*/*'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"    Permission already exists for {lambda_function_name}")
        else:
            raise
    
    # Create method
    try:
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='NONE',
            apiKeyRequired=False
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            print(f"    Method {http_method} already exists")
        else:
            raise
    
    # Create integration
    integration_uri = f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
    
    apigateway_client.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=integration_uri
    )
    
    # Create method response
    apigateway_client.put_method_response(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Origin': True
        }
    )
    
    print(f"    ✅ Created {http_method} integration for {lambda_function_name}")
    return True


def setup_insights_endpoints(api_id: str, api_root_id: str):
    """Set up all insights API endpoints.
    
    Args:
        api_id: API ID
        api_root_id: Root resource ID
    """
    print("\nSetting up insights endpoints...")
    
    # Create /insights resource
    insights_resource_id = create_resource(api_id, api_root_id, 'insights')
    print(f"  Created /insights resource")
    
    # Create /{user_id} resource under /insights
    user_id_resource_id = create_resource(api_id, insights_resource_id, '{user_id}')
    print(f"  Created /insights/{{user_id}} resource")
    
    lambda_functions = resources['lambda_functions']
    
    # Weekly recap endpoint: GET /insights/{user_id}/weekly-recap
    weekly_recap_resource_id = create_resource(api_id, user_id_resource_id, 'weekly-recap')
    if create_lambda_integration(api_id, weekly_recap_resource_id, lambda_functions['weekly_recap'], 'GET'):
        print(f"  ✅ Endpoint: GET /insights/{{user_id}}/weekly-recap")
    else:
        print(f"  ⏳ Endpoint: GET /insights/{{user_id}}/weekly-recap (Lambda pending)")
    
    # Spending analysis endpoint: GET /insights/{user_id}/spending-analysis
    spending_analysis_resource_id = create_resource(api_id, user_id_resource_id, 'spending-analysis')
    if create_lambda_integration(api_id, spending_analysis_resource_id, lambda_functions['spending_analysis'], 'GET'):
        print(f"  ✅ Endpoint: GET /insights/{{user_id}}/spending-analysis")
    else:
        print(f"  ⏳ Endpoint: GET /insights/{{user_id}}/spending-analysis (Lambda pending)")
    
    # Net worth endpoint: GET /insights/{user_id}/net-worth
    net_worth_resource_id = create_resource(api_id, user_id_resource_id, 'net-worth')
    if create_lambda_integration(api_id, net_worth_resource_id, lambda_functions['net_worth'], 'GET'):
        print(f"  ✅ Endpoint: GET /insights/{{user_id}}/net-worth")
    else:
        print(f"  ⏳ Endpoint: GET /insights/{{user_id}}/net-worth (Lambda pending)")
    
    # Budget suggestion endpoint: GET /insights/{user_id}/suggested-budget
    budget_suggestion_resource_id = create_resource(api_id, user_id_resource_id, 'suggested-budget')
    if create_lambda_integration(api_id, budget_suggestion_resource_id, lambda_functions['budget_suggestion'], 'GET'):
        print(f"  ✅ Endpoint: GET /insights/{{user_id}}/suggested-budget")
    else:
        print(f"  ⏳ Endpoint: GET /insights/{{user_id}}/suggested-budget (Lambda pending)")
    
    # Budget tracking endpoint: GET /insights/{user_id}/budget-tracking
    budget_tracking_resource_id = create_resource(api_id, user_id_resource_id, 'budget-tracking')
    if create_lambda_integration(api_id, budget_tracking_resource_id, lambda_functions['budget_tracking'], 'GET'):
        print(f"  ✅ Endpoint: GET /insights/{{user_id}}/budget-tracking")
    else:
        print(f"  ⏳ Endpoint: GET /insights/{{user_id}}/budget-tracking (Lambda pending)")


def deploy_api(api_id: str):
    """Deploy API Gateway to stage.
    
    Args:
        api_id: API ID
    """
    print(f"\nDeploying API to stage '{stage_name}'...")
    
    try:
        apigateway_client.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=f'Deployment for {config["environment"]} environment'
        )
        print(f"  ✅ Deployed API to stage: {stage_name}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            # Update existing deployment
            apigateway_client.create_deployment(
                restApiId=api_id,
                stageName=stage_name,
                description=f'Updated deployment for {config["environment"]} environment'
            )
            print(f"  ✅ Updated deployment to stage: {stage_name}")
        else:
            raise


def enable_cors(api_id: str, resource_id: str):
    """Enable CORS for a resource.
    
    Args:
        api_id: API ID
        resource_id: Resource ID
    """
    try:
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        apigateway_client.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Origin': True
            },
            responseModels={
                'application/json': 'Empty'
            }
        )
        
        apigateway_client.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            },
            responseTemplates={
                'application/json': ''
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] != 'ConflictException':
            raise


def main():
    """Main setup function."""
    print("=" * 60)
    print("SpendSense API Gateway Setup")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Profile: {profile}")
    print("=" * 60)
    print()
    
    try:
        # Create API Gateway
        api_id, api_root_id = create_api_gateway()
        print()
        
        # Set up insights endpoints
        setup_insights_endpoints(api_id, api_root_id)
        
        # Enable CORS for root resource
        enable_cors(api_id, api_root_id)
        
        # Deploy API
        deploy_api(api_id)
        
        # Get API endpoint URL
        account_id = session.client('sts').get_caller_identity()['Account']
        api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
        
        print("\n" + "=" * 60)
        print("✅ API Gateway Setup Complete!")
        print("=" * 60)
        print(f"\nAPI Endpoint: {api_url}")
        print("\nAvailable endpoints:")
        print(f"  GET {api_url}/insights/{{user_id}}/weekly-recap")
        print(f"  GET {api_url}/insights/{{user_id}}/spending-analysis")
        print(f"  GET {api_url}/insights/{{user_id}}/net-worth")
        print(f"  GET {api_url}/insights/{{user_id}}/suggested-budget")
        print(f"  GET {api_url}/insights/{{user_id}}/budget-tracking")
        
        # Update resources file
        resources['api_gateway'] = {
            'api_id': api_id,
            'api_url': api_url,
            'stage': stage_name
        }
        
        with open(RESOURCES_PATH, 'w') as f:
            json.dump(resources, f, indent=2)
        
        print(f"\nResource information updated: {RESOURCES_PATH}")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()

