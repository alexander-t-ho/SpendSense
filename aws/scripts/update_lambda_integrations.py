#!/usr/bin/env python3
"""Update API Gateway Lambda integrations after Lambda functions are deployed.

This script updates API Gateway to connect to Lambda functions that have been deployed.

Usage:
    python aws/scripts/update_lambda_integrations.py
"""

import boto3
import json
from pathlib import Path

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

region = resources['region']
api_gateway = resources.get('api_gateway', {})

if not api_gateway:
    print("❌ API Gateway not found. Run setup_api_gateway.py first.")
    exit(1)

api_id = api_gateway['api_id']

# Get account ID
session = boto3.Session(profile_name='default', region_name=region)
sts_client = session.client('sts')
account_id = sts_client.get_caller_identity()['Account']

apigateway_client = session.client('apigateway')
lambda_client = session.client('lambda')


def update_lambda_integration(endpoint_path: str, lambda_function_name: str):
    """Update Lambda integration for an API Gateway endpoint.
    
    Args:
        endpoint_path: Path like 'insights/{user_id}/weekly-recap'
        lambda_function_name: Lambda function name
    """
    try:
        # Get Lambda function ARN
        lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
        
        # Get API Gateway resources
        resources_response = apigateway_client.get_resources(restApiId=api_id)
        
        # Find the resource for this endpoint - match by full path
        resource_id = None
        full_path = f'/{endpoint_path}'
        
        # Look for exact path match
        for item in resources_response['items']:
            if item.get('path') == full_path:
                resource_id = item['id']
                break
        
        if not resource_id:
            print(f"  ⚠️  Could not find resource for path: {endpoint_path}")
            print(f"      Searched for: {full_path}")
            print(f"      Available paths:")
            for item in resources_response['items']:
                print(f"        - {item.get('path', 'N/A')}")
            return False
        
        # Check if GET method exists, create if not
        try:
            apigateway_client.get_method(restApiId=api_id, resourceId=resource_id, httpMethod='GET')
        except apigateway_client.exceptions.NotFoundException:
            # Create GET method
            print(f"    Creating GET method...")
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET',
                authorizationType='NONE'
            )
        
        # Update integration
        integration_uri = f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        
        # Give API Gateway permission to invoke Lambda
        # Use account ID instead of wildcard for SourceArn
        source_arn = f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*'
        try:
            lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=f'api-gateway-invoke-{api_id}-{resource_id}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
        except lambda_client.exceptions.ResourceConflictException:
            pass  # Permission already exists
        
        print(f"  ✅ Updated integration for {endpoint_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating {endpoint_path}: {e}")
        return False


def main():
    """Update all Lambda integrations."""
    print("=" * 60)
    print("Updating API Gateway Lambda Integrations")
    print("=" * 60)
    print(f"API ID: {api_id}")
    print("=" * 60)
    print()
    
    lambda_functions = resources['lambda_functions']
    endpoints = {
        'insights/{user_id}/weekly-recap': lambda_functions['weekly_recap'],
        'insights/{user_id}/spending-analysis': lambda_functions['spending_analysis'],
        'insights/{user_id}/net-worth': lambda_functions['net_worth'],
        'insights/{user_id}/suggested-budget': lambda_functions['budget_suggestion'],
        'insights/{user_id}/budget-tracking': lambda_functions['budget_tracking'],
    }
    
    updated = 0
    for endpoint_path, lambda_name in endpoints.items():
        if update_lambda_integration(endpoint_path, lambda_name):
            updated += 1
    
    # Redeploy API
    if updated > 0:
        print(f"\nRedeploying API...")
        apigateway_client.create_deployment(
            restApiId=api_id,
            stageName=api_gateway['stage'],
            description='Updated with Lambda integrations'
        )
        print("  ✅ API redeployed")
    
    print("\n" + "=" * 60)
    print(f"✅ Updated {updated}/{len(endpoints)} integrations")
    print("=" * 60)


if __name__ == "__main__":
    main()

