#!/usr/bin/env python3
"""Validate that all components are ready for Lambda deployment."""

import json
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description} NOT FOUND: {path}")
        return False

def main():
    """Validate deployment readiness."""
    print("=" * 60)
    print("SpendSense Lambda Deployment Readiness Check")
    print("=" * 60)
    print()
    
    all_ready = True
    
    # Check configuration files
    print("Configuration Files:")
    print("-" * 60)
    all_ready &= check_file("aws/config/aws_config.yaml", "AWS config")
    all_ready &= check_file("aws/config/aws_resources.json", "AWS resources")
    print()
    
    # Check Lambda handlers
    print("Lambda Handlers:")
    print("-" * 60)
    functions = [
        "weekly_recap",
        "spending_analysis",
        "net_worth",
        "budget_suggestion",
        "budget_tracking"
    ]
    
    for func in functions:
        handler_path = f"aws/lambda/{func}/handler.py"
        req_path = f"aws/lambda/{func}/requirements.txt"
        all_ready &= check_file(handler_path, f"Handler: {func}")
        if Path(req_path).exists():
            print(f"  ✅ Requirements: {req_path}")
        else:
            print(f"  ⚠️  No requirements.txt for {func}")
    print()
    
    # Check deployment scripts
    print("Deployment Scripts:")
    print("-" * 60)
    all_ready &= check_file("aws/scripts/deploy_lambda.py", "Deploy script")
    all_ready &= check_file("aws/scripts/create_lambda_role.sh", "Role creation script")
    all_ready &= check_file("aws/scripts/update_lambda_integrations.py", "API Gateway script")
    print()
    
    # Check resources JSON structure
    print("Resource Configuration:")
    print("-" * 60)
    try:
        with open("aws/config/aws_resources.json") as f:
            resources = json.load(f)
        
        required_keys = ["lambda_functions", "iam_roles", "api_gateway"]
        for key in required_keys:
            if key in resources:
                print(f"✅ {key}: configured")
            else:
                print(f"❌ {key}: missing")
                all_ready = False
        
        # Check Lambda role ARN
        if "iam_roles" in resources and "lambda_arn" in resources["iam_roles"]:
            role_arn = resources["iam_roles"]["lambda_arn"]
            print(f"✅ Lambda role ARN: {role_arn}")
        else:
            print("❌ Lambda role ARN not configured")
            all_ready = False
            
    except Exception as e:
        print(f"❌ Error reading resources: {e}")
        all_ready = False
    print()
    
    # Check dependencies
    print("Python Dependencies:")
    print("-" * 60)
    try:
        import boto3
        print("✅ boto3: available")
    except ImportError:
        print("❌ boto3: not installed")
        all_ready = False
    
    try:
        import yaml
        print("✅ pyyaml: available")
    except ImportError:
        print("❌ pyyaml: not installed")
        all_ready = False
    print()
    
    # Summary
    print("=" * 60)
    if all_ready:
        print("✅ All components ready for deployment!")
        print()
        print("Next steps:")
        print("  1. Create Lambda role (requires admin credentials):")
        print("     ./aws/scripts/create_lambda_role.sh")
        print()
        print("  2. Deploy Lambda functions:")
        print("     python aws/scripts/deploy_lambda.py all")
        print()
        print("  3. Update API Gateway:")
        print("     python aws/scripts/update_lambda_integrations.py")
    else:
        print("❌ Some components are missing or misconfigured")
        print("   Please fix the issues above before deploying")
    print("=" * 60)
    
    return 0 if all_ready else 1

if __name__ == "__main__":
    sys.exit(main())

