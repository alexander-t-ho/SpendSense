#!/usr/bin/env python3
"""Test Lambda functions and API Gateway endpoints."""

import boto3
import json
import requests
from pathlib import Path

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"
with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

region = resources['region']
api_gateway = resources['api_gateway']
lambda_functions = resources['lambda_functions']

session = boto3.Session(profile_name='default', region_name=region)
lambda_client = session.client('lambda')

print("=" * 60)
print("Testing Lambda Functions")
print("=" * 60)
print()

# Test each Lambda function
for function_key, function_name in lambda_functions.items():
    print(f"Testing {function_key} ({function_name})...")
    
    try:
        # Get function configuration
        func_config = lambda_client.get_function(FunctionName=function_name)
        print(f"  ✅ Function exists")
        print(f"     Runtime: {func_config['Configuration']['Runtime']}")
        print(f"     Handler: {func_config['Configuration']['Handler']}")
        print(f"     State: {func_config['Configuration']['State']}")
        
        # Test invocation with a sample event
        # Note: We'll use a test user_id - you may need to adjust this
        test_event = {
            "pathParameters": {
                "user_id": "user_001"  # Replace with an actual user ID from your database
            },
            "queryStringParameters": None,
            "headers": {},
            "body": None
        }
        
        print(f"  Testing invocation...")
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            status_code = response['StatusCode']
            payload = json.loads(response['Payload'].read())
            
            if status_code == 200:
                print(f"  ✅ Invocation successful (Status: {status_code})")
                if 'errorMessage' in payload:
                    print(f"     ⚠️  Error: {payload.get('errorMessage', 'Unknown error')}")
                else:
                    print(f"     Response received")
            else:
                print(f"  ⚠️  Invocation returned status: {status_code}")
                
        except Exception as e:
            print(f"  ⚠️  Invocation error: {str(e)}")
            print(f"     (This may be expected if user_id doesn't exist or DB isn't accessible)")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()

print("=" * 60)
print("Testing API Gateway Endpoints")
print("=" * 60)
print()

api_base_url = api_gateway['api_url']
test_user_id = "user_001"  # Replace with an actual user ID

endpoints = {
    "weekly-recap": f"{api_base_url}/insights/{test_user_id}/weekly-recap",
    "spending-analysis": f"{api_base_url}/insights/{test_user_id}/spending-analysis",
    "net-worth": f"{api_base_url}/insights/{test_user_id}/net-worth",
    "suggested-budget": f"{api_base_url}/insights/{test_user_id}/suggested-budget",
    "budget-tracking": f"{api_base_url}/insights/{test_user_id}/budget-tracking",
}

for endpoint_name, url in endpoints.items():
    print(f"Testing {endpoint_name}...")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ Success")
            try:
                data = response.json()
                print(f"     Response keys: {list(data.keys())[:5]}...")
            except:
                print(f"     Response: {response.text[:100]}...")
        elif response.status_code == 404:
            print(f"  ⚠️  Not found (user may not exist)")
        elif response.status_code == 500:
            print(f"  ⚠️  Server error: {response.text[:200]}")
        else:
            print(f"  ⚠️  Unexpected status: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()

print("=" * 60)
print("✅ Testing Complete")
print("=" * 60)
print()
print("Note: Some errors may be expected if:")
print("  - Test user_id doesn't exist in database")
print("  - Database isn't accessible from Lambda")
print("  - Lambda functions need database file in /tmp")
print()

