#!/usr/bin/env python3
"""Setup AWS resources for SpendSense insights computation.

This script creates all necessary AWS resources:
- S3 buckets
- DynamoDB tables
- IAM roles and policies
- Lambda functions (structure)
- API Gateway (configuration)
- CloudWatch log groups

Usage:
    python aws/scripts/setup_aws_resources.py
"""

import boto3
import yaml
import json
import uuid
from pathlib import Path
from typing import Dict, Any
from botocore.exceptions import ClientError

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "aws_config.yaml"

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

aws_config = config['aws']
region = aws_config['region']
profile = aws_config.get('profile', 'default')

# Initialize boto3 clients
session = boto3.Session(profile_name=profile, region_name=region)
s3_client = session.client('s3')
dynamodb_client = session.client('dynamodb')
iam_client = session.client('iam')
lambda_client = session.client('lambda')
logs_client = session.client('logs')
apigateway_client = session.client('apigateway')

# Generate unique suffixes for resources
unique_suffix = str(uuid.uuid4())[:8]


def generate_bucket_name(prefix: str) -> str:
    """Generate a unique S3 bucket name."""
    return f"{prefix}-{unique_suffix}"


def create_s3_buckets():
    """Create S3 buckets for Parquet data, insights, and historical data."""
    print("Creating S3 buckets...")
    
    bucket_configs = []
    
    for bucket_key, bucket_config in config['s3']['buckets'].items():
        bucket_name = generate_bucket_name(bucket_config['prefix'])
        
        try:
            # Create bucket
            if region == 'us-east-1':
                # us-east-1 doesn't require LocationConstraint
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            # Enable versioning
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Set lifecycle policy
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': f'{bucket_key}-lifecycle',  # Note: ID must be uppercase
                        'Status': 'Enabled',
                        'Filter': {},  # Apply to all objects
                        'Transitions': [
                            {
                                'Days': bucket_config['lifecycle_days'],
                                'StorageClass': 'GLACIER'
                            }
                        ] if bucket_config['lifecycle_days'] > 30 else []
                    }
                ]
            }
            
            if bucket_config['lifecycle_days'] <= 7:
                # Delete after 7 days instead of transitioning
                lifecycle_config['Rules'][0]['Expiration'] = {'Days': bucket_config['lifecycle_days']}
                lifecycle_config['Rules'][0]['Transitions'] = []
            
            s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            print(f"  ✅ Created bucket: {bucket_name}")
            bucket_configs.append({
                'key': bucket_key,
                'name': bucket_name,
                'prefix': bucket_config['prefix']
            })
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                print(f"  ⚠️  Bucket {bucket_name} already exists")
                bucket_configs.append({
                    'key': bucket_key,
                    'name': bucket_name,
                    'prefix': bucket_config['prefix']
                })
            else:
                print(f"  ❌ Error creating bucket {bucket_name}: {e}")
                raise
    
    return bucket_configs


def create_dynamodb_tables():
    """Create DynamoDB tables for insights metadata and user preferences."""
    print("Creating DynamoDB tables...")
    
    tables_config = config['dynamodb']['tables']
    
    for table_key, table_config in tables_config.items():
        table_name = table_config['name']
        
        try:
            # Build attribute definitions
            attribute_definitions = [
                {'AttributeName': attr['name'], 'AttributeType': attr['type']}
                for attr in table_config['attributes']
            ]
            
            # Build key schema
            key_schema = [
                {'AttributeName': table_config['attributes'][0]['name'], 'KeyType': 'HASH'}  # Partition key
            ]
            
            if len(table_config['attributes']) > 1:
                key_schema.append({
                    'AttributeName': table_config['attributes'][1]['name'],
                    'KeyType': 'RANGE'  # Sort key
                })
            
            dynamodb_client.create_table(
                TableName=table_name,
                AttributeDefinitions=attribute_definitions,
                KeySchema=key_schema,
                BillingMode=table_config['billing_mode']
            )
            
            # Wait for table to be created
            waiter = dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"  ✅ Created table: {table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"  ⚠️  Table {table_name} already exists")
            else:
                print(f"  ❌ Error creating table {table_name}: {e}")
                raise


def create_iam_role(role_name: str, assume_role_policy: Dict[str, Any], policies: list) -> str:
    """Create IAM role with trust policy and attach policies.
    
    Args:
        role_name: Name of the role
        assume_role_policy: Trust policy document
        policies: List of policy documents to attach
    
    Returns:
        Role ARN
    """
    try:
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description=f"SpendSense {role_name} for development"
        )
        role_arn = response['Role']['Arn']
        
        # Attach policies
        for policy_name, policy_document in policies:
            policy_arn = iam_client.create_policy(
                PolicyName=f"{role_name}-{policy_name}",
                PolicyDocument=json.dumps(policy_document)
            )['Policy']['Arn']
            
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        print(f"  ✅ Created IAM role: {role_name}")
        return role_arn
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"  ⚠️  IAM role {role_name} already exists")
            response = iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            print(f"  ❌ Error creating IAM role {role_name}: {e}")
            raise


def create_iam_roles(bucket_names: Dict[str, str]):
    """Create IAM roles for Lambda and API Gateway."""
    print("Creating IAM roles...")
    
    # Lambda execution role
    lambda_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    lambda_policies = [
        ("S3Access", {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
                for bucket_name in bucket_names.values()
            ]
        }),
        ("DynamoDBAccess", {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{region}:*:table/{config['dynamodb']['tables']['insights_metadata']['name']}",
                        f"arn:aws:dynamodb:{region}:*:table/{config['dynamodb']['tables']['user_preferences']['name']}"
                    ]
                }
            ]
        }),
        ("CloudWatchLogs", {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        })
    ]
    
    lambda_role_arn = create_iam_role(
        config['iam']['lambda_role'],
        lambda_trust_policy,
        lambda_policies
    )
    
    return lambda_role_arn


def create_cloudwatch_log_groups():
    """Create CloudWatch log groups for Lambda functions."""
    print("Creating CloudWatch log groups...")
    
    retention_days = config['cloudwatch']['log_retention_days']
    
    for func_key, func_config in config['lambda']['functions'].items():
        log_group_name = f"/aws/lambda/{func_config['name']}"
        
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
            logs_client.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=retention_days
            )
            print(f"  ✅ Created log group: {log_group_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                print(f"  ⚠️  Log group {log_group_name} already exists")
            else:
                print(f"  ❌ Error creating log group {log_group_name}: {e}")


def main():
    """Main setup function."""
    print("=" * 60)
    print("SpendSense AWS Infrastructure Setup")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Profile: {profile}")
    print(f"Environment: {config['environment']}")
    print("=" * 60)
    print()
    
    try:
        # Create S3 buckets
        bucket_configs = create_s3_buckets()
        bucket_names = {bc['key']: bc['name'] for bc in bucket_configs}
        print()
        
        # Create DynamoDB tables
        create_dynamodb_tables()
        print()
        
        # Create IAM roles
        lambda_role_arn = create_iam_roles(bucket_names)
        print()
        
        # Create CloudWatch log groups
        create_cloudwatch_log_groups()
        print()
        
        # Save resource names to a file for reference
        resources = {
            'region': region,
            'environment': config['environment'],
            's3_buckets': bucket_names,
            'dynamodb_tables': {
                key: table_config['name']
                for key, table_config in config['dynamodb']['tables'].items()
            },
            'iam_roles': {
                'lambda': config['iam']['lambda_role'],
                'lambda_arn': lambda_role_arn
            },
            'lambda_functions': {
                key: func_config['name']
                for key, func_config in config['lambda']['functions'].items()
            }
        }
        
        output_file = Path(__file__).parent.parent / "config" / "aws_resources.json"
        with open(output_file, 'w') as f:
            json.dump(resources, f, indent=2)
        
        print("=" * 60)
        print("✅ AWS Infrastructure Setup Complete!")
        print("=" * 60)
        print(f"\nResource information saved to: {output_file}")
        print("\nNext steps:")
        print("1. Deploy Lambda functions: python aws/scripts/deploy_lambda.py")
        print("2. Set up API Gateway: python aws/scripts/setup_api_gateway.py")
        print("3. Upload Parquet files to S3: python aws/scripts/upload_parquet_to_s3.py")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()

