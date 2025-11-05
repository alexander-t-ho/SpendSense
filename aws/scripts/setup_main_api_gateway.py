#!/usr/bin/env python3
"""Setup API Gateway specifically for main FastAPI application.

This script creates a separate API Gateway for the main FastAPI application,
or updates an existing API Gateway to include the main API endpoints.

Usage:
    python aws/scripts/setup_main_api_gateway.py
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

# Use main API Gateway config
api_config = config['api_gateway']
api_name = api_config['name']
stage_name = api_config['stage']


def get_or_create_api_gateway():
    """Get existing API Gateway or create new one."""
    print("Finding or creating API Gateway...")
    
    try:
        apis = apigateway_client.get_rest_apis()
        for api in apis['items']:
            if api['name'] == api_name:
                api_id = api['id']
                resources_response = apigateway_client.get_resources(restApiId=api_id)
                api_root_id = resources_response['items'][0]['id']
                print(f"  ✅ Found existing API Gateway: {api_name} (ID: {api_id})")
                return api_id, api_root_id
    except Exception as e:
        print(f"  Error checking existing APIs: {e}")
    
    # Create new API Gateway
    try:
        api_response = apigateway_client.create_rest_api(
            name=api_name,
            description=api_config['description'],
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )
        
        api_id = api_response['id']
        api_root_id = api_response['rootResourceId']
        print(f"  ✅ Created new API Gateway: {api_name} (ID: {api_id})")
        return api_id, api_root_id
    except Exception as e:
        print(f"  ❌ Error creating API Gateway: {e}")
        raise


def setup_proxy_integration(api_id: str, api_root_id: str):
    """Set up proxy integration for main FastAPI Lambda."""
    print("\nSetting up proxy integration for main API...")
    
    # Get main API Lambda function
    lambda_config = config['lambda']
    main_api_config = lambda_config['functions'].get('main_api')
    
    if not main_api_config:
        print("  ❌ Main API configuration not found")
        return False
    
    main_api_function_name = main_api_config['name']
    
    # Check if Lambda exists
    try:
        lambda_response = lambda_client.get_function(FunctionName=main_api_function_name)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
        print(f"  ✅ Found Lambda function: {main_api_function_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  ❌ Lambda function {main_api_function_name} not found")
            print(f"     Deploy it first: python aws/scripts/deploy_lambda.py main_api")
            return False
        raise
    
    # Create {proxy+} resource
    try:
        resources_response = apigateway_client.get_resources(restApiId=api_id)
        proxy_resource_id = None
        for resource in resources_response['items']:
            if resource.get('pathPart') == '{proxy+}':
                proxy_resource_id = resource['id']
                print(f"  Found existing /{{proxy+}} resource")
                break
        
        if not proxy_resource_id:
            proxy_resource = apigateway_client.create_resource(
                restApiId=api_id,
                parentId=api_root_id,
                pathPart='{proxy+}'
            )
            proxy_resource_id = proxy_resource['id']
            print(f"  ✅ Created /{{proxy+}} resource")
    except Exception as e:
        print(f"  ❌ Error creating proxy resource: {e}")
        return False
    
    # Add Lambda permission
    try:
        lambda_client.add_permission(
            FunctionName=main_api_function_name,
            StatementId=f'api-gateway-invoke-{api_id}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{region}:*:{api_id}/*/*'
        )
        print(f"  ✅ Added Lambda invoke permission")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"  Permission already exists")
        else:
            print(f"  ⚠️  Error adding permission: {e}")
    
    # Set up methods for proxy resource
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
    integration_uri = f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
    
    for method in methods:
        try:
            # Create method
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=proxy_resource_id,
                httpMethod=method,
                authorizationType='NONE'
            )
            
            # Create integration
            apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=proxy_resource_id,
                httpMethod=method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            print(f"  ✅ Set up {method} method for proxy")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                print(f"  Method {method} already exists")
            else:
                print(f"  ⚠️  Error setting up {method}: {e}")
    
    # Also set up root GET method
    try:
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=api_root_id,
            httpMethod='GET',
            authorizationType='NONE'
        )
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=api_root_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        print(f"  ✅ Set up GET method for root /")
    except ClientError as e:
        if e.response['Error']['Code'] != 'ConflictException':
            print(f"  ⚠️  Error setting up root GET: {e}")
    
    return True


def deploy_api(api_id: str):
    """Deploy API to stage."""
    print(f"\nDeploying API to stage '{stage_name}'...")
    
    try:
        apigateway_client.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=f'Deployment for main API - {config["environment"]}'
        )
        print(f"  ✅ Deployed to stage: {stage_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            # Update deployment
            apigateway_client.create_deployment(
                restApiId=api_id,
                stageName=stage_name,
                description=f'Updated deployment - {config["environment"]}'
            )
            print(f"  ✅ Updated deployment to stage: {stage_name}")
        else:
            raise


def main():
    """Main setup function."""
    print("=" * 60)
    print("SpendSense Main API Gateway Setup")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Profile: {profile}")
    print("=" * 60)
    
    try:
        # Get or create API Gateway
        api_id, api_root_id = get_or_create_api_gateway()
        
        # Set up proxy integration
        if setup_proxy_integration(api_id, api_root_id):
            # Deploy API
            deploy_api(api_id)
            
            # Get API URL
            account_id = session.client('sts').get_caller_identity()['Account']
            api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
            
            print("\n" + "=" * 60)
            print("✅ Main API Gateway Setup Complete!")
            print("=" * 60)
            print(f"\nAPI Endpoint: {api_url}")
            print("\nAll FastAPI endpoints are available via proxy:")
            print(f"  {api_url}/api/stats")
            print(f"  {api_url}/api/users")
            print(f"  {api_url}/api/profile/{{user_id}}")
            print(f"  {api_url}/api/recommendations/{{user_id}}")
            print(f"  ... and all other endpoints")
            
            # Update resources file
            if 'api_gateway' not in resources:
                resources['api_gateway'] = {}
            resources['api_gateway']['main_api_id'] = api_id
            resources['api_gateway']['main_api_url'] = api_url
            
            with open(RESOURCES_PATH, 'w') as f:
                json.dump(resources, f, indent=2)
            
            print(f"\nResource information updated: {RESOURCES_PATH}")
        else:
            print("\n⚠️  Setup incomplete - Lambda function not deployed")
            print("   Deploy Lambda first: python aws/scripts/deploy_lambda.py main_api")
    
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()


