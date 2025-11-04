#!/usr/bin/env python3
"""Create IAM user for SpendSense project.

This script creates a new IAM user "SpendSense_AlexHo" with appropriate
permissions for SpendSense resources.

Usage:
    python aws/scripts/create_iam_user.py
"""

import boto3
import json
from pathlib import Path
from botocore.exceptions import ClientError

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "aws_config.yaml"
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

try:
    with open(CONFIG_PATH, 'r') as f:
        import yaml
        config = yaml.safe_load(f)
except FileNotFoundError:
    config = {'aws': {'region': 'us-east-1'}}

aws_config = config['aws']
region = aws_config['region']
profile = aws_config.get('profile', 'default')

session = boto3.Session(profile_name=profile, region_name=region)
iam_client = session.client('iam')

NEW_USER_NAME = "SpendSense_AlexHo"


def create_iam_user():
    """Create new IAM user for SpendSense."""
    print("=" * 60)
    print("Creating IAM User for SpendSense")
    print("=" * 60)
    print(f"User Name: {NEW_USER_NAME}")
    print(f"Region: {region}")
    print("=" * 60)
    print()
    
    try:
        # Check if user already exists
        try:
            existing_user = iam_client.get_user(UserName=NEW_USER_NAME)
            print(f"⚠️  User {NEW_USER_NAME} already exists!")
            print(f"   ARN: {existing_user['User']['Arn']}")
            print()
            
            # Check if user has access keys
            try:
                keys = iam_client.list_access_keys(UserName=NEW_USER_NAME)
                if keys['AccessKeyMetadata']:
                    print("⚠️  User already has access keys.")
                    print("   To create new keys, delete old ones first or use existing keys.")
                    use_existing = input("Do you want to create new access keys? (y/n): ").lower().strip()
                    
                    if use_existing == 'y':
                        # Delete old keys first (we'll create new ones)
                        for key in keys['AccessKeyMetadata']:
                            print(f"   Deleting old access key: {key['AccessKeyId']}")
                            iam_client.delete_access_key(
                                UserName=NEW_USER_NAME,
                                AccessKeyId=key['AccessKeyId']
                            )
                    else:
                        print("   Using existing access keys.")
                        return existing_user['User']
                else:
                    print("   User exists but has no access keys. Creating new keys...")
            except ClientError as e:
                print(f"   Error checking access keys: {e}")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # User doesn't exist, create it
                print(f"Creating new IAM user: {NEW_USER_NAME}...")
                user = iam_client.create_user(
                    UserName=NEW_USER_NAME,
                    Tags=[
                        {'Key': 'Project', 'Value': 'SpendSense'},
                        {'Key': 'Environment', 'Value': config.get('environment', 'development')}
                    ]
                )
                print(f"  ✅ Created user: {NEW_USER_NAME}")
                print(f"     ARN: {user['User']['Arn']}")
            else:
                raise
        
        # Create access keys
        print(f"\nCreating access keys for {NEW_USER_NAME}...")
        access_key_response = iam_client.create_access_key(UserName=NEW_USER_NAME)
        
        access_key_id = access_key_response['AccessKey']['AccessKeyId']
        secret_access_key = access_key_response['AccessKey']['SecretAccessKey']
        
        print(f"  ✅ Created access key: {access_key_id}")
        print()
        print("=" * 60)
        print("⚠️  IMPORTANT: Save these credentials securely!")
        print("=" * 60)
        print(f"Access Key ID: {access_key_id}")
        print(f"Secret Access Key: {secret_access_key}")
        print()
        print("⚠️  The secret access key will only be shown once!")
        print("=" * 60)
        print()
        
        # Attach policies
        print("Attaching policies...")
        
        # Policy for SpendSense resources
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::spendsense-*",
                        f"arn:aws:s3:::spendsense-*/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:DeleteItem"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{region}:*:table/spendsense-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:CreateFunction",
                        "lambda:InvokeFunction",
                        "lambda:GetFunction",
                        "lambda:UpdateFunctionCode",
                        "lambda:UpdateFunctionConfiguration",
                        "lambda:DeleteFunction",
                        "lambda:ListFunctions",
                        "lambda:AddPermission",
                        "lambda:RemovePermission"
                    ],
                    "Resource": [
                        f"arn:aws:lambda:{region}:*:function:spendsense-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "apigateway:GET",
                        "apigateway:POST",
                        "apigateway:PUT",
                        "apigateway:DELETE"
                    ],
                    "Resource": [
                        f"arn:aws:apigateway:{region}::/restapis/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "sts:GetCallerIdentity"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        policy_name = f"AlexHoSpendSenseUserPolicy-{config.get('environment', 'dev')}"
        
        try:
            # Create policy
            policy = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Policy for SpendSense project resources"
            )
            policy_arn = policy['Policy']['Arn']
            print(f"  ✅ Created policy: {policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                # Policy exists, get its ARN
                account_id = session.client('sts').get_caller_identity()['Account']
                policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
                print(f"  ⚠️  Policy already exists: {policy_name}")
            else:
                raise
        
        # Attach policy to user
        try:
            iam_client.attach_user_policy(
                UserName=NEW_USER_NAME,
                PolicyArn=policy_arn
            )
            print(f"  ✅ Attached policy to user")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"  ⚠️  Policy already attached")
            else:
                raise
        
        # Save credentials to file (optional, for reference)
        credentials_file = Path(__file__).parent.parent / "config" / ".aws_credentials.txt"
        credentials_content = f"""# SpendSense AWS Credentials
# Generated: {__import__('datetime').datetime.now().isoformat()}
# User: {NEW_USER_NAME}

AWS_ACCESS_KEY_ID={access_key_id}
AWS_SECRET_ACCESS_KEY={secret_access_key}
AWS_DEFAULT_REGION={region}

# To configure AWS CLI:
# aws configure set aws_access_key_id {access_key_id}
# aws configure set aws_secret_access_key {secret_access_key}
# aws configure set default.region {region}

# Or add to ~/.aws/credentials:
# [spendsense]
# aws_access_key_id = {access_key_id}
# aws_secret_access_key = {secret_access_key}
# region = {region}
"""
        
        with open(credentials_file, 'w') as f:
            f.write(credentials_content)
        
        print()
        print("=" * 60)
        print("✅ IAM User Setup Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Configure AWS CLI with new credentials:")
        print(f"   aws configure set aws_access_key_id {access_key_id}")
        print(f"   aws configure set aws_secret_access_key {secret_access_key}")
        print(f"   aws configure set default.region {region}")
        print()
        print("2. Or create a new profile:")
        print(f"   aws configure --profile spendsense")
        print()
        print(f"3. Credentials saved to: {credentials_file}")
        print("   (Keep this file secure - it contains sensitive credentials)")
        print()
        print("4. Verify connection:")
        print("   aws sts get-caller-identity")
        print("   python aws/scripts/verify_aws_connection.py")
        
        return {
            'user_name': NEW_USER_NAME,
            'access_key_id': access_key_id,
            'secret_access_key': secret_access_key,
            'region': region
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print(f"❌ Access denied! You don't have permission to create IAM users.")
            print()
            print("You need IAM permissions to create users. Options:")
            print("1. Ask an AWS administrator to create the user for you")
            print("2. Use your existing credentials (MessagAI_AlexHo)")
            print("3. Create the user manually in AWS Console:")
            print("   https://console.aws.amazon.com/iam/home#/users")
            return None
        else:
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    result = create_iam_user()
    if result:
        print("\n✅ Setup successful!")
    else:
        print("\n⚠️  Setup incomplete - see instructions above")

