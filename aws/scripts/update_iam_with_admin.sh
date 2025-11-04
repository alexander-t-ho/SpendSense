#!/bin/bash
# Update IAM policy using admin credentials via CLI
# This script prompts for admin credentials or uses environment variables

set -e

POLICY_NAME="AlexHoSpendSenseUserPolicy-development"
POLICY_ARN="arn:aws:iam::971422717446:policy/${POLICY_NAME}"
TEMP_POLICY=$(mktemp)

echo "============================================================"
echo "Update IAM Policy via CLI"
echo "============================================================"
echo ""

# Check if admin credentials are provided via environment variables
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Admin credentials needed to update IAM policy."
    echo ""
    echo "You can provide credentials in two ways:"
    echo ""
    echo "Option A: Environment variables (recommended)"
    echo "  export AWS_ACCESS_KEY_ID=<your-admin-access-key>"
    echo "  export AWS_SECRET_ACCESS_KEY=<your-admin-secret-key>"
    echo "  ./aws/scripts/update_iam_with_admin.sh"
    echo ""
    echo "Option B: Interactive input"
    read -p "Enter AWS Access Key ID: " ADMIN_ACCESS_KEY
    read -p "Enter AWS Secret Access Key: " ADMIN_SECRET_KEY
    
    export AWS_ACCESS_KEY_ID="$ADMIN_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$ADMIN_SECRET_KEY"
fi

# Verify credentials work
echo "Verifying credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Invalid credentials. Please check your AWS Access Key ID and Secret Access Key."
    exit 1
fi

CURRENT_USER=$(aws sts get-caller-identity --query 'Arn' --output text)
echo "✅ Using credentials for: $CURRENT_USER"
echo ""

# Check IAM permissions
echo "Checking IAM permissions..."
if ! aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "❌ No permission to access IAM policies."
    echo "   Make sure your credentials have IAM permissions."
    exit 1
fi

echo "✅ IAM permissions confirmed"
echo ""

# Create policy document
cat > "$TEMP_POLICY" << 'POLICYEOF'
{
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
        "dynamodb:Scan",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/spendsense-*"
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
        "arn:aws:lambda:us-east-1:*:function:spendsense-*"
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
        "arn:aws:apigateway:us-east-1::/restapis/*"
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
      "Resource": "arn:aws:iam::971422717446:role/SpendSense*"
    }
  ]
}
POLICYEOF

echo "Creating new policy version..."
aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document "file://$TEMP_POLICY" \
    --set-as-default

echo ""
echo "✅ Policy updated successfully!"
echo ""

# Clean up
rm "$TEMP_POLICY"

# Verify
echo "Verifying update..."
NEW_VERSION=$(aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId' --output text)
echo "New default version: $NEW_VERSION"
echo ""

# Show summary
echo "✅ Update complete!"
echo ""
echo "The policy now includes:"
echo "  ✅ Full Lambda permissions (Create, Update, Delete, Invoke, etc.)"
echo "  ✅ S3, DynamoDB, API Gateway, CloudWatch Logs permissions"
echo "  ✅ IAM PassRole for Lambda execution role"
echo ""
echo "Next steps:"
echo "  1. Switch back to SpendSense credentials:"
echo "     aws configure set aws_access_key_id $(grep aws_access_key_id ~/.aws/credentials | grep -A 1 '\[default\]' | tail -1 | cut -d'=' -f2 | tr -d ' ')"
echo ""
echo "  2. Deploy Lambda functions:"
echo "     python aws/scripts/deploy_lambda.py weekly_recap"
echo ""

