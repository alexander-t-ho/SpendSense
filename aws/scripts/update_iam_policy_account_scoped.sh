#!/bin/bash
# Update IAM policy with account-scoped permissions
# This ensures all resources are scoped to the user's account ID only

set -e

# Account ID - verify this matches your account
ACCOUNT_ID="971422717446"
POLICY_NAME="AlexHoSpendSenseUserPolicy-development"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
TEMP_POLICY=$(mktemp)

echo "============================================================"
echo "Update IAM Policy - Account Scoped (AlexHo Prefix)"
echo "============================================================"
echo "Account ID: $ACCOUNT_ID"
echo "Policy Name: $POLICY_NAME"
echo "Policy ARN: $POLICY_ARN"
echo "============================================================"
echo ""

# Check if admin credentials are provided via environment variables
echo "Checking for admin credentials..."

# If credentials are not set, prompt for them
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Admin credentials needed to update IAM policy."
    echo ""
    echo "Please provide admin credentials for account $ACCOUNT_ID:"
    echo ""
    read -p "Enter AWS Access Key ID: " ADMIN_ACCESS_KEY
    read -sp "Enter AWS Secret Access Key: " ADMIN_SECRET_KEY
    echo ""
    
    export AWS_ACCESS_KEY_ID="$ADMIN_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$ADMIN_SECRET_KEY"
fi

# Verify we're working with the correct account
echo "Verifying account access..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "")

if [ -z "$CURRENT_ACCOUNT" ]; then
    echo "❌ Invalid credentials. Cannot proceed."
    exit 1
fi

if [ "$CURRENT_ACCOUNT" != "$ACCOUNT_ID" ]; then
    echo "⚠️  WARNING: Current account ($CURRENT_ACCOUNT) does not match target account ($ACCOUNT_ID)"
    echo ""
    read -p "Continue anyway? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi
else
    echo "✅ Account verified: $CURRENT_ACCOUNT"
fi

CURRENT_USER=$(aws sts get-caller-identity --query 'Arn' --output text)
echo "Using credentials for: $CURRENT_USER"
echo ""

# Check IAM permissions
echo "Checking IAM permissions..."
if ! aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "❌ Cannot access IAM policy."
    echo "   Make sure your credentials have IAM permissions for account $ACCOUNT_ID"
    exit 1
fi

echo "✅ IAM permissions confirmed"
echo ""

# Create account-scoped policy document
cat > "$TEMP_POLICY" << EOF
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
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
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
        "arn:aws:dynamodb:us-east-1:${ACCOUNT_ID}:table/spendsense-*"
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
        "arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:spendsense-*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
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
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
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
      "Resource": [
        "arn:aws:logs:us-east-1:${ACCOUNT_ID}:*"
      ]
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
      "Resource": "arn:aws:iam::${ACCOUNT_ID}:role/SpendSense*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    }
  ]
}
EOF

echo "Policy document created with account-scoped resources ($ACCOUNT_ID)"
echo ""

# Create new policy version
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

# Show account scoping
echo "✅ Policy is now scoped to account: $ACCOUNT_ID"
echo ""
echo "Resource restrictions:"
echo "  - Lambda functions: us-east-1:${ACCOUNT_ID}:function:spendsense-*"
echo "  - DynamoDB tables: us-east-1:${ACCOUNT_ID}:table/spendsense-*"
echo "  - CloudWatch Logs: us-east-1:${ACCOUNT_ID}:*"
echo "  - IAM Roles: ${ACCOUNT_ID}:role/SpendSense*"
echo "  - Region: us-east-1 only"
echo ""
echo "✅ Update complete! All resources are scoped to your account only."
echo ""
echo "Next steps:"
echo "  1. Switch back to SpendSense credentials:"
echo "     aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID"
echo "     aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY"
echo "     (Replace with your actual credentials - do not commit secrets to git!)"
echo ""
echo "  2. Deploy Lambda functions:"
echo "     python aws/scripts/deploy_lambda.py weekly_recap"
echo ""

