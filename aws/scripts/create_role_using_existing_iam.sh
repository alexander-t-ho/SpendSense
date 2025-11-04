#!/bin/bash
# Create Lambda role using existing IAM policies and resources
# This script will reference existing policies and create the role efficiently

set -e

ACCOUNT_ID="971422717446"
ROLE_NAME="AlexHoSpendSenseLambdaRole-dev"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "============================================================"
echo "Create Lambda Role Using Existing IAM"
echo "============================================================"
echo "Role Name: $ROLE_NAME"
echo "Account ID: $ACCOUNT_ID"
echo "============================================================"
echo ""

# Check for admin credentials/profile
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    echo "⚠️  Admin credentials needed to create IAM role."
    echo ""
    echo "Please provide admin credentials one of these ways:"
    echo ""
    echo "Option 1: Set environment variables:"
    echo "  export AWS_ACCESS_KEY_ID=<admin-key>"
    echo "  export AWS_SECRET_ACCESS_KEY=<admin-secret>"
    echo ""
    echo "Option 2: Use admin AWS profile:"
    echo "  export AWS_PROFILE=<admin-profile>"
    echo ""
    echo "Option 3: Interactive prompt (will be used automatically):"
    echo ""
    read -p "Press Enter to continue with interactive prompt, or Ctrl+C to cancel..."
    
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        read -p "Enter AWS Access Key ID: " ADMIN_ACCESS_KEY
        read -sp "Enter AWS Secret Access Key: " ADMIN_SECRET_KEY
        echo ""
        
        export AWS_ACCESS_KEY_ID="$ADMIN_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$ADMIN_SECRET_KEY"
    fi
fi

# Trust policy for Lambda (required)
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
echo "Checking if role exists..."
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "✅ Role exists: $ROLE_NAME"
    echo ""
    echo "Updating trust policy to ensure Lambda can assume it..."
    aws iam update-assume-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-document "$TRUST_POLICY"
    echo "✅ Trust policy updated!"
else
    echo "Creating new role with Lambda trust policy..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "Execution role for AlexHo SpendSense Lambda functions"
    echo "✅ Role created: $ROLE_NAME"
fi

echo ""
echo "Attaching AWS managed policies..."

# Attach AWS managed policy for Lambda basic execution (CloudWatch Logs)
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
    2>/dev/null && echo "  ✅ Attached: AWSLambdaBasicExecutionRole" || echo "  ℹ️  Already attached: AWSLambdaBasicExecutionRole"

# Check if existing policy exists that we can reuse
POLICY_NAME="AlexHoSpendSenseLambdaPolicy-dev"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo ""
echo "Setting up custom policy for S3 and DynamoDB access..."

# Create custom policy that matches the user's existing policy structure
# This reuses the same resource patterns from POLICY_JSON_UPDATED.json
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
if aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "  ✅ Policy already exists: $POLICY_NAME"
    
    # Update the policy document to match current needs
    POLICY_VERSION=$(aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId' --output text)
    echo "  Updating policy version..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document "$POLICY_DOC" \
        --set-as-default \
        > /dev/null 2>&1 && echo "  ✅ Policy updated" || echo "  ℹ️  Policy already up to date"
else
    echo "  Creating custom policy: $POLICY_NAME"
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "$POLICY_DOC" \
        --description "Policy for AlexHo SpendSense Lambda functions to access S3 and DynamoDB (matches user policy structure)"
    echo "  ✅ Policy created: $POLICY_NAME"
fi

# Attach custom policy to role
echo "  Attaching policy to role..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" \
    2>/dev/null && echo "  ✅ Attached: $POLICY_NAME" || echo "  ℹ️  Already attached: $POLICY_NAME"

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
echo "  - AWSLambdaBasicExecutionRole (AWS managed - CloudWatch Logs)"
echo "  - $POLICY_NAME (Custom - S3 & DynamoDB, matches user policy)"
echo ""
echo "Note: Your user policy already has iam:PassRole permission"
echo "      for this role, so you can deploy Lambda functions now!"
echo ""
echo "Next step: Deploy Lambda functions"
echo "  python aws/scripts/deploy_lambda.py all"
echo ""

