#!/usr/bin/env python3
"""Update IAM policy with additional Lambda permissions.

This script updates the SpendSenseUserPolicy-development policy to include
all necessary Lambda permissions for deploying and managing Lambda functions.

Usage:
    python aws/scripts/update_iam_policy.py
"""

import boto3
import json
from pathlib import Path
from botocore.exceptions import ClientError

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "aws_config.yaml"

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
sts_client = session.client('sts')

POLICY_NAME = "AlexHoSpendSenseUserPolicy-development"


def get_full_policy_document():
    """Get the complete policy document with all permissions."""
    account_id = sts_client.get_caller_identity()['Account']
    
    return {
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
                    "lambda:RemovePermission",
                    "lambda:GetFunctionConfiguration",
                    "lambda:TagResource",
                    "lambda:UntagResource",
                    "lambda:ListTags"
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
                    "apigateway:DELETE",
                    "apigateway:PATCH"
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
                    "logs:DescribeLogStreams",
                    "logs:GetLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sts:GetCallerIdentity"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:PassRole"
                ],
                "Resource": f"arn:aws:iam::{account_id}:role/SpendSense*"
            }
        ]
    }


def update_iam_policy():
    """Update the IAM policy with new permissions."""
    print("=" * 60)
    print("Updating IAM Policy for SpendSense")
    print("=" * 60)
    print(f"Policy Name: {POLICY_NAME}")
    print(f"Region: {region}")
    print("=" * 60)
    print()
    
    try:
        # Get account ID
        account_id = sts_client.get_caller_identity()['Account']
        policy_arn = f"arn:aws:iam::{account_id}:policy/{POLICY_NAME}"
        
        print(f"Looking up policy: {POLICY_NAME}...")
        
        # Get current policy
        try:
            policy = iam_client.get_policy(PolicyArn=policy_arn)
            current_version = policy['Policy']['DefaultVersionId']
            
            print(f"  ✅ Found policy: {policy_arn}")
            print(f"  Current version: {current_version}")
            print()
            
            # Get current policy document
            policy_version = iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=current_version
            )
            current_doc = policy_version['PolicyVersion']['Document']
            
            print("Current policy statements:")
            for i, stmt in enumerate(current_doc['Statement'], 1):
                actions = stmt.get('Action', [])
                if isinstance(actions, str):
                    actions = [actions]
                print(f"  {i}. {stmt.get('Effect')} - {len(actions)} action(s)")
            
            print()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"  ❌ Policy not found: {POLICY_NAME}")
                print("  Run create_iam_user.py first to create the policy.")
                return False
            else:
                raise
        
        # Create new policy document with updated permissions
        new_policy_doc = get_full_policy_document()
        
        print("New policy will include:")
        for i, stmt in enumerate(new_policy_doc['Statement'], 1):
            actions = stmt.get('Action', [])
            if isinstance(actions, str):
                actions = [actions]
            print(f"  {i}. {stmt.get('Effect')} - {len(actions)} action(s)")
            if 'lambda' in str(stmt.get('Action', [])).lower():
                print(f"     → Lambda permissions: {', '.join([a for a in actions if 'lambda' in a.lower()][:3])}...")
        
        print()
        
        # Create new policy version
        print("Creating new policy version...")
        try:
            response = iam_client.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=json.dumps(new_policy_doc),
                SetAsDefault=True
            )
            
            new_version_id = response['PolicyVersion']['VersionId']
            print(f"  ✅ Created new policy version: {new_version_id}")
            print(f"  ✅ Set as default version")
            print()
            
            # List old versions (keep last 4 versions)
            versions = iam_client.list_policy_versions(PolicyArn=policy_arn)
            old_versions = [v for v in versions['Versions'] if v['VersionId'] != new_version_id and not v['IsDefaultVersion']]
            
            if len(old_versions) > 3:
                print(f"Cleaning up old policy versions (keeping last 4)...")
                for old_version in old_versions[3:]:  # Keep last 4, delete older ones
                    try:
                        iam_client.delete_policy_version(
                            PolicyArn=policy_arn,
                            VersionId=old_version['VersionId']
                        )
                        print(f"  ✅ Deleted old version: {old_version['VersionId']}")
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'DeleteConflict':
                            print(f"  ⚠️  Could not delete version {old_version['VersionId']}: {e}")
            
            print()
            print("=" * 60)
            print("✅ Policy Update Complete!")
            print("=" * 60)
            print()
            print("The policy now includes:")
            print("  ✅ Full Lambda permissions (Create, Update, Delete, Invoke, etc.)")
            print("  ✅ S3 permissions")
            print("  ✅ DynamoDB permissions")
            print("  ✅ API Gateway permissions")
            print("  ✅ CloudWatch Logs permissions")
            print("  ✅ IAM PassRole for Lambda execution role")
            print()
            print("Next steps:")
            print("  1. Verify permissions: aws iam get-policy-version --policy-arn {} --version-id {}".format(policy_arn, new_version_id))
            print("  2. Deploy Lambda: python aws/scripts/deploy_lambda.py weekly_recap")
            print()
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'LimitExceeded':
                print(f"  ❌ Policy version limit reached. Deleting oldest version...")
                # Delete oldest non-default version
                versions = iam_client.list_policy_versions(PolicyArn=policy_arn)
                old_versions = [v for v in versions['Versions'] if not v['IsDefaultVersion']]
                if old_versions:
                    oldest = sorted(old_versions, key=lambda x: x['CreateDate'])[0]
                    iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=oldest['VersionId']
                    )
                    print(f"  ✅ Deleted oldest version: {oldest['VersionId']}")
                    # Retry
                    return update_iam_policy()
                else:
                    print("  ❌ No old versions to delete")
                    return False
            elif error_code == 'AccessDenied':
                print(f"  ❌ Access denied! You don't have permission to update IAM policies.")
                print()
                print("Options:")
                print("  1. Use an admin account to update the policy")
                print("  2. Use AWS Console: https://console.aws.amazon.com/iam/")
                print("  3. Ask an AWS administrator to grant IAM permissions")
                return False
            else:
                raise
                
    except ClientError as e:
        print(f"❌ Error: {e}")
        print(f"   Error Code: {e.response['Error']['Code']}")
        print(f"   Error Message: {e.response['Error']['Message']}")
        return False


if __name__ == "__main__":
    success = update_iam_policy()
    if not success:
        print("\n⚠️  Policy update failed. See instructions above.")
        exit(1)

