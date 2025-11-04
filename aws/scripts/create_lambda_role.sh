#!/bin/bash
# Create IAM role for Lambda execution with AlexHo prefix

set -e

ACCOUNT_ID="971422717446"
ROLE_NAME="AlexHoSpendSenseLambdaRole-dev"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "============================================================"
echo "Create Lambda Execution Role"
echo "============================================================"
echo "Role Name: $ROLE_NAME"
echo "Account ID: $ACCOUNT_ID"
echo "============================================================"
echo ""

# Check if admin credentials are provided
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Admin credentials needed to create IAM role."
    echo ""
    read -p "Enter AWS Access Key ID: " ADMIN_ACCESS_KEY
    read -sp "Enter AWS Secret Access Key: " ADMIN_SECRET_KEY
    echo ""
    
    export AWS_ACCESS_KEY_ID="$ADMIN_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$ADMIN_SECRET_KEY"
fi

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
    echo "✅ Role already exists: $ROLE_NAME"
    echo "   ARN: $ROLE_ARN"
else
    echo "Creating IAM role..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "Execution role for AlexHo SpendSense Lambda functions"
    
    echo "✅ Role created: $ROLE_NAME"
fi

# Attach AWS managed policy for Lambda basic execution
echo "Attaching AWS managed policies..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
    2>/dev/null || echo "  (Already attached: AWSLambdaBasicExecutionRole)"

# Create custom policy for S3, DynamoDB, CloudWatch access
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
        "arn:aws:s3:::alexho-spendsense-*/*"
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
        "arn:aws:dynamodb:us-east-1:'${ACCOUNT_ID}':table/alexho-spendsense-*"
      ]
    }
  ]
}'

# Check if policy exists
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
if aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "✅ Policy already exists: $POLICY_NAME"
else
    echo "Creating custom policy for Lambda..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "$POLICY_DOC" \
        --description "Policy for AlexHo SpendSense Lambda functions to access S3 and DynamoDB"
    
    echo "✅ Policy created: $POLICY_NAME"
fi

# Attach custom policy to role
echo "Attaching custom policy to role..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" \
    2>/dev/null || echo "  (Already attached: $POLICY_NAME)"

echo ""
echo "============================================================"
echo "✅ Lambda Role Setup Complete!"
echo "============================================================"
echo ""
echo "Role Details:"
echo "  Name: $ROLE_NAME"
echo "  ARN: $ROLE_ARN"
echo ""
echo "Attached Policies:"
echo "  - AWSLambdaBasicExecutionRole (AWS managed)"
echo "  - $POLICY_NAME (Custom)"
echo ""
echo "Next steps:"
echo "  1. Switch back to SpendSense credentials"
echo "  2. Deploy Lambda functions:"
echo "     python aws/scripts/deploy_lambda.py weekly_recap"
echo ""

