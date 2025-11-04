#!/bin/bash
# Quick deployment script - checks role and deploys Lambda functions

set -e

ACCOUNT_ID="971422717446"
ROLE_NAME="AlexHoSpendSenseLambdaRole-dev"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "============================================================"
echo "Quick Lambda Deployment Check"
echo "============================================================"
echo ""

# Check if role exists
echo "Checking if Lambda execution role exists..."
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "✅ Role exists: $ROLE_NAME"
    echo ""
    echo "Proceeding with Lambda deployment..."
    echo ""
    python aws/scripts/deploy_lambda.py all
else
    echo "❌ Role not found: $ROLE_NAME"
    echo ""
    echo "Please create the role first with admin credentials:"
    echo "  ./aws/scripts/create_lambda_role.sh"
    echo ""
    echo "Or create it manually in AWS Console:"
    echo "  1. Go to: https://console.aws.amazon.com/iam/"
    echo "  2. Roles → Create role"
    echo "  3. Select: AWS service → Lambda"
    echo "  4. Role name: $ROLE_NAME"
    echo "  5. Attach policies: AWSLambdaBasicExecutionRole"
    echo "  6. Create custom policy for S3/DynamoDB access"
    exit 1
fi

