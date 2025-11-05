#!/bin/bash
# Create Lambda role using admin profile or credentials

set -e

ACCOUNT_ID="971422717446"
ROLE_NAME="AlexHoSpendSenseLambdaRole-dev"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "============================================================"
echo "Create Lambda Execution Role (Admin Mode)"
echo "============================================================"
echo "Role Name: $ROLE_NAME"
echo "Account ID: $ACCOUNT_ID"
echo "============================================================"
echo ""

# Check for admin profile
ADMIN_PROFILE=""
if [ -n "$AWS_ADMIN_PROFILE" ]; then
    ADMIN_PROFILE="$AWS_ADMIN_PROFILE"
    echo "Using admin profile from environment: $ADMIN_PROFILE"
elif aws configure list-profiles 2>/dev/null | grep -q "admin"; then
    ADMIN_PROFILE="admin"
    echo "Found 'admin' profile, using it..."
elif aws configure list-profiles 2>/dev/null | grep -q "default"; then
    # Check if default has admin permissions
    if aws iam list-users --profile default >/dev/null 2>&1; then
        ADMIN_PROFILE="default"
        echo "Using default profile with admin permissions..."
    fi
fi

# Set AWS profile if found
if [ -n "$ADMIN_PROFILE" ]; then
    export AWS_PROFILE="$ADMIN_PROFILE"
    export AWS_DEFAULT_PROFILE="$ADMIN_PROFILE"
fi

# Check if admin credentials are provided via environment
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$ADMIN_PROFILE" ]; then
    echo "⚠️  No admin profile or credentials found."
    echo ""
    echo "Please provide admin credentials one of these ways:"
    echo ""
    echo "Option 1: Set environment variables:"
    echo "  export AWS_ACCESS_KEY_ID=<admin-key>"
    echo "  export AWS_SECRET_ACCESS_KEY=<admin-secret>"
    echo "  ./aws/scripts/create_role_with_admin.sh"
    echo ""
    echo "Option 2: Use AWS profile:"
    echo "  export AWS_ADMIN_PROFILE=<profile-name>"
    echo "  ./aws/scripts/create_role_with_admin.sh"
    echo ""
    echo "Option 3: Interactive prompt (will be used automatically):"
    echo "  ./aws/scripts/create_lambda_role.sh"
    echo ""
    read -p "Press Enter to continue with interactive prompt, or Ctrl+C to cancel..."
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


