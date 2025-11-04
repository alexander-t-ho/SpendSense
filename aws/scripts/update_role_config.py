#!/usr/bin/env python3
"""Update the Lambda role configuration in aws_resources.json."""

import json
import sys
from pathlib import Path

RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

def update_role_config(role_name: str, account_id: str = "971422717446"):
    """Update the role configuration."""
    with open(RESOURCES_PATH, 'r') as f:
        resources = json.load(f)
    
    old_role_name = resources['iam_roles']['lambda']
    old_role_arn = resources['iam_roles']['lambda_arn']
    
    new_role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    
    resources['iam_roles']['lambda'] = role_name
    resources['iam_roles']['lambda_arn'] = new_role_arn
    
    with open(RESOURCES_PATH, 'w') as f:
        json.dump(resources, f, indent=2)
    
    print("=" * 60)
    print("Lambda Role Configuration Updated")
    print("=" * 60)
    print(f"Old Role: {old_role_name}")
    print(f"New Role: {role_name}")
    print(f"New ARN: {new_role_arn}")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Make sure the role has the correct trust policy!")
    print("   The role must allow Lambda service to assume it:")
    print()
    print("   Trust Policy Required:")
    print("   {")
    print('     "Version": "2012-10-17",')
    print('     "Statement": [')
    print('       {')
    print('         "Effect": "Allow",')
    print('         "Principal": {')
    print('           "Service": "lambda.amazonaws.com"')
    print('         },')
    print('         "Action": "sts:AssumeRole"')
    print('       }')
    print('     ]')
    print("   }")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_role_config.py <role-name> [account-id]")
        print()
        print("Example:")
        print("  python update_role_config.py MyLambdaRole")
        print("  python update_role_config.py MyLambdaRole 971422717446")
        sys.exit(1)
    
    role_name = sys.argv[1]
    account_id = sys.argv[2] if len(sys.argv) > 2 else "971422717446"
    
    update_role_config(role_name, account_id)

