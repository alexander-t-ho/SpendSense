#!/usr/bin/env python3
"""Verify AWS connection and list all SpendSense resources.

This script verifies that AWS CLI is properly configured and lists all
SpendSense resources in your AWS account.

Usage:
    python aws/scripts/verify_aws_connection.py
"""

import boto3
import json
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

try:
    with open(RESOURCES_PATH, 'r') as f:
        resources = json.load(f)
except FileNotFoundError:
    print("❌ aws_resources.json not found. Run setup_aws_resources.py first.")
    exit(1)

region = resources['region']
profile = 'default'

print("=" * 60)
print("AWS Connection Verification")
print("=" * 60)
print()

# Test AWS connection
try:
    session = boto3.Session(profile_name=profile, region_name=region)
    sts_client = session.client('sts')
    
    # Get caller identity
    identity = sts_client.get_caller_identity()
    
    print("✅ AWS Connection Successful!")
    print(f"   Account ID: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
    print(f"   Region: {region}")
    print(f"   Profile: {profile}")
    print()
    
except NoCredentialsError:
    print("❌ AWS credentials not found!")
    print("\nPlease configure AWS CLI:")
    print("  aws configure")
    print("\nOr set environment variables:")
    print("  export AWS_ACCESS_KEY_ID=your_access_key")
    print("  export AWS_SECRET_ACCESS_KEY=your_secret_key")
    exit(1)
except Exception as e:
    print(f"❌ Error connecting to AWS: {e}")
    exit(1)

# Verify resources
print("=" * 60)
print("Verifying SpendSense Resources")
print("=" * 60)
print()

s3_client = session.client('s3')
dynamodb_client = session.client('dynamodb')
lambda_client = session.client('lambda')
apigateway_client = session.client('apigateway')
logs_client = session.client('logs')

# Check S3 buckets
print("S3 Buckets:")
s3_buckets = resources['s3_buckets']
for bucket_key, bucket_name in s3_buckets.items():
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        location = s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        if location is None:
            location = 'us-east-1'
        print(f"  ✅ {bucket_name} (Region: {location})")
    except ClientError as e:
        print(f"  ❌ {bucket_name} - Error: {e.response['Error']['Code']}")
print()

# Check DynamoDB tables
print("DynamoDB Tables:")
dynamodb_tables = resources['dynamodb_tables']
for table_key, table_name in dynamodb_tables.items():
    try:
        table = dynamodb_client.describe_table(TableName=table_name)
        status = table['Table']['TableStatus']
        print(f"  ✅ {table_name} (Status: {status})")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  ❌ {table_name} - Not found")
        else:
            print(f"  ❌ {table_name} - Error: {e.response['Error']['Code']}")
print()

# Check Lambda functions
print("Lambda Functions:")
lambda_functions = resources['lambda_functions']
for func_key, func_name in lambda_functions.items():
    try:
        func = lambda_client.get_function(FunctionName=func_name)
        runtime = func['Configuration']['Runtime']
        status = func['Configuration']['State']
        print(f"  ✅ {func_name} (Runtime: {runtime}, Status: {status})")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  ⏳ {func_name} - Not deployed yet")
        else:
            print(f"  ❌ {func_name} - Error: {e.response['Error']['Code']}")
print()

# Check API Gateway
print("API Gateway:")
api_gateway = resources.get('api_gateway', {})
if api_gateway:
    api_id = api_gateway.get('api_id')
    try:
        api = apigateway_client.get_rest_api(restApiId=api_id)
        print(f"  ✅ API: {api['name']} (ID: {api_id})")
        print(f"     URL: {api_gateway.get('api_url', 'N/A')}")
        print(f"     Stage: {api_gateway.get('stage', 'N/A')}")
    except ClientError as e:
        print(f"  ❌ API Gateway - Error: {e.response['Error']['Code']}")
else:
    print("  ⏳ API Gateway not configured")
print()

# Check CloudWatch log groups
print("CloudWatch Log Groups:")
for func_key, func_name in lambda_functions.items():
    log_group_name = f"/aws/lambda/{func_name}"
    try:
        logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
        print(f"  ✅ {log_group_name}")
    except ClientError as e:
        print(f"  ❌ {log_group_name} - Error: {e.response['Error']['Code']}")
print()

print("=" * 60)
print("✅ Verification Complete!")
print("=" * 60)

