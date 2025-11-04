#!/bin/bash
# Fix or create Lambda role with correct trust policy
# This script can be run with admin credentials to update an existing role

set -e

ACCOUNT_ID="971422717446"
ROLE_NAME="AlexHoSpendSenseLambdaRole-dev"

echo "============================================================"
echo "Fix Lambda Role Trust Policy"
echo "============================================================"
echo "Role Name: $ROLE_NAME"
echo "Account ID: $ACCOUNT_ID"
echo "============================================================"
echo ""

# Trust policy for Lambda
TRUST_POLICY='{
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
}'

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "✅ Role exists: $ROLE_NAME"
    echo ""
    echo "Updating trust policy to allow Lambda service..."
    aws iam update-assume-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-document "$TRUST_POLICY"
    echo "✅ Trust policy updated!"
else
    echo "⚠️  Role does not exist: $ROLE_NAME"
    echo ""
    echo "Creating role with correct trust policy..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "Execution role for AlexHo SpendSense Lambda functions"
    echo "✅ Role created: $ROLE_NAME"
fi

# Attach AWS managed policy
echo ""
echo "Attaching AWS managed policies..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
    2>/dev/null || echo "  (Already attached: AWSLambdaBasicExecutionRole)"

# Create and attach custom policy for S3/DynamoDB
POLICY_NAME="AlexHoSpendSenseLambdaPolicy-dev"
POLICY_DOC='{
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
        "arn:aws:s3:::alexho-spendsense-*",
        "arn:aws:s3:::alexho-spendsense-*/*",
        "arn:aws:s3:::spendsense-*",
        "arn:aws:s3:::spendsense-*/*"
      ]
    },
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
        "arn:aws:dynamodb:us-east-1:'${ACCOUNT_ID}':table/alexho-spendsense-*",
        "arn:aws:dynamodb:us-east-1:'${ACCOUNT_ID}':table/spendsense-*"
      ]
    }
  ]
}'

POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
if aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "✅ Policy already exists: $POLICY_NAME"
else
    echo "Creating custom policy..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "$POLICY_DOC" \
        --description "Policy for AlexHo SpendSense Lambda functions"
    echo "✅ Policy created: $POLICY_NAME"
fi

echo "Attaching custom policy to role..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" \
    2>/dev/null || echo "  (Already attached: $POLICY_NAME)"

echo ""
echo "============================================================"
echo "✅ Role is ready for Lambda deployment!"
echo "============================================================"
echo ""
echo "Role: $ROLE_NAME"
echo "ARN: arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo ""
echo "Next step: Deploy Lambda functions"
echo "  python aws/scripts/deploy_lambda.py all"
echo ""

