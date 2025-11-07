#!/bin/bash
# Complete deployment script for Lambda functions
# This script will guide you through creating the role and deploying functions

set -e

ACCOUNT_ID="971422717446"
ROLE_NAME="AlexHoSpendSenseLambdaRole-dev"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "============================================================"
echo "SpendSense Lambda Deployment - Complete Process"
echo "============================================================"
echo ""

# Step 1: Create Lambda Role
echo "Step 1: Creating Lambda Execution Role"
echo "----------------------------------------"
echo ""

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "✅ Lambda role already exists: $ROLE_NAME"
    echo ""
else
    echo "⚠️  Lambda role does not exist."
    echo ""
    echo "You need admin credentials to create the IAM role."
    echo ""
    echo "Options:"
    echo "  1. Run with admin credentials (interactive):"
    echo "     ./aws/scripts/create_lambda_role.sh"
    echo ""
    echo "  2. Set admin credentials as environment variables:"
    echo "     export AWS_ACCESS_KEY_ID=<admin-key>"
    echo "     export AWS_SECRET_ACCESS_KEY=<admin-secret>"
    echo "     ./aws/scripts/create_role_with_admin.sh"
    echo ""
    echo "  3. Use admin AWS profile:"
    echo "     export AWS_ADMIN_PROFILE=<profile-name>"
    echo "     ./aws/scripts/create_role_with_admin.sh"
    echo ""
    
    read -p "Do you want to create the role now? (y/n): " create_role
    if [ "$create_role" = "y" ] || [ "$create_role" = "Y" ]; then
        echo ""
        echo "Running role creation script (will prompt for credentials if needed)..."
        ./aws/scripts/create_lambda_role.sh
        echo ""
    else
        echo ""
        echo "⚠️  Skipping role creation. Please create it manually before deploying Lambda functions."
        echo "   You can run this script again after creating the role."
        exit 1
    fi
fi

# Verify role exists
if ! aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "❌ Role creation failed or role not found. Please create it manually."
    exit 1
fi

echo ""
echo "Step 2: Deploying Lambda Functions"
echo "-----------------------------------"
echo ""

# Step 2: Deploy Lambda Functions
python aws/scripts/deploy_lambda.py all

echo ""
echo "Step 3: Updating API Gateway Integrations"
echo "------------------------------------------"
echo ""

# Step 3: Update API Gateway
if [ -f "aws/scripts/update_lambda_integrations.py" ]; then
    python aws/scripts/update_lambda_integrations.py
else
    echo "⚠️  API Gateway update script not found. Skipping..."
    echo "   You can update API Gateway manually or create the script."
fi

echo ""
echo "============================================================"
echo "✅ Deployment Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Test Lambda functions in AWS Console"
echo "  2. Verify API Gateway endpoints"
echo "  3. Test from frontend application"
echo ""




