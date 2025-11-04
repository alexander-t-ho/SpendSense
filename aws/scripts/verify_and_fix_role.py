#!/usr/bin/env python3
"""Verify Lambda role exists and has correct trust policy."""

import boto3
import json
import sys
from pathlib import Path

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"
with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

role_name = resources['iam_roles']['lambda']
role_arn = resources['iam_roles']['lambda_arn']

print("=" * 60)
print("Verifying Lambda Execution Role")
print("=" * 60)
print(f"Role Name: {role_name}")
print(f"Role ARN: {role_arn}")
print("=" * 60)
print()

session = boto3.Session(profile_name='default', region_name='us-east-1')
iam_client = session.client('iam')

try:
    # Check if role exists
    response = iam_client.get_role(RoleName=role_name)
    print(f"✅ Role exists: {role_name}")
    print()
    
    # Check trust policy
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    print("Current Trust Policy:")
    print(json.dumps(trust_policy, indent=2))
    print()
    
    # Verify Lambda service is allowed
    statements = trust_policy.get('Statement', [])
    lambda_allowed = False
    
    for stmt in statements:
        if stmt.get('Effect') == 'Allow':
            principal = stmt.get('Principal', {})
            if isinstance(principal, dict) and principal.get('Service') == 'lambda.amazonaws.com':
                lambda_allowed = True
                break
    
    if lambda_allowed:
        print("✅ Trust policy allows Lambda service")
    else:
        print("❌ Trust policy does NOT allow Lambda service")
        print()
        print("The role needs to have a trust policy that allows Lambda to assume it.")
        print("Required trust policy:")
        required_policy = {
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
        print(json.dumps(required_policy, indent=2))
        print()
        print("You need admin credentials to update the trust policy.")
        print("Run: ./aws/scripts/create_lambda_role.sh")
        sys.exit(1)
    
    # Check attached policies
    print("\nAttached Policies:")
    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in attached_policies['AttachedPolicies']:
        print(f"  ✅ {policy['PolicyName']} ({policy['PolicyArn']})")
    
    # Check inline policies
    inline_policies = iam_client.list_role_policies(RoleName=role_name)
    for policy_name in inline_policies['PolicyNames']:
        print(f"  ✅ {policy_name} (inline)")
    
    print()
    print("=" * 60)
    print("✅ Role is properly configured!")
    print("=" * 60)
    
except iam_client.exceptions.NoSuchEntityException:
    print(f"❌ Role does not exist: {role_name}")
    print()
    print("The role needs to be created with the correct trust policy.")
    print("Run: ./aws/scripts/create_lambda_role.sh")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error checking role: {e}")
    print()
    print("This might be a permissions issue. You may need admin credentials.")
    sys.exit(1)

