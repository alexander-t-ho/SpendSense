#!/bin/bash
# Create IAM policy with AlexHo prefix using AWS CLI
# This script creates the AlexHoSpendSenseUserPolicy-development policy

set -e

ACCOUNT_ID="971422717446"
POLICY_NAME="AlexHoSpendSenseUserPolicy-development"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
USER_NAME="SpendSense_AlexHo"
TEMP_POLICY=$(mktemp)

echo "============================================================"
echo "Create IAM Policy via CLI"
echo "============================================================"
echo "Policy Name: $POLICY_NAME"
echo "Account ID: $ACCOUNT_ID"
echo "============================================================"
echo ""

# Check if admin credentials are provided
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Admin credentials needed to create IAM policy."
    echo ""
    echo "Please provide admin credentials for account $ACCOUNT_ID:"
    echo ""
    read -p "Enter AWS Access Key ID: " ADMIN_ACCESS_KEY
    read -sp "Enter AWS Secret Access Key: " ADMIN_SECRET_KEY
    echo ""
    
    export AWS_ACCESS_KEY_ID="$ADMIN_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$ADMIN_SECRET_KEY"
fi

# Verify credentials
echo "Verifying credentials..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "")

if [ -z "$CURRENT_ACCOUNT" ]; then
    echo "❌ Invalid credentials. Cannot proceed."
    exit 1
fi

CURRENT_USER=$(aws sts get-caller-identity --query 'Arn' --output text)
echo "✅ Using credentials for: $CURRENT_USER"
echo ""

# Check if policy already exists
echo "Checking if policy already exists..."
if aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "⚠️  Policy already exists: $POLICY_NAME"
    read -p "Do you want to update it? (yes/no): " UPDATE_POLICY
    if [ "$UPDATE_POLICY" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
    UPDATE_EXISTING=true
else
    UPDATE_EXISTING=false
fi

# Create policy document (without _comment field)
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
        "dynamodb:Scan",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:971422717446:table/alexho-spendsense-*"
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
        "arn:aws:lambda:us-east-1:971422717446:function:alexho-spendsense-*"
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
      "Resource": "arn:aws:logs:us-east-1:971422717446:*"
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
      "Resource": "arn:aws:iam::971422717446:role/AlexHoSpendSense*"
    }
  ]
}
POLICYEOF

if [ "$UPDATE_EXISTING" = true ]; then
    echo "Creating new policy version..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document "file://$TEMP_POLICY" \
        --set-as-default
    
    echo "✅ Policy updated successfully!"
else
    echo "Creating new policy..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "file://$TEMP_POLICY" \
        --description "IAM policy for AlexHo's SpendSense project - scoped to account 971422717446"
    
    echo "✅ Policy created successfully!"
fi

echo ""

# Clean up
rm "$TEMP_POLICY"

# Attach policy to user
echo "Attaching policy to user: $USER_NAME..."
if aws iam list-attached-user-policies --user-name "$USER_NAME" --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN']" --output text | grep -q "$POLICY_ARN"; then
    echo "✅ Policy already attached to user"
else
    aws iam attach-user-policy \
        --user-name "$USER_NAME" \
        --policy-arn "$POLICY_ARN"
    echo "✅ Policy attached to user: $USER_NAME"
fi

echo ""
echo "============================================================"
echo "✅ Complete!"
echo "============================================================"
echo ""
echo "Policy Details:"
echo "  Name: $POLICY_NAME"
echo "  ARN: $POLICY_ARN"
echo "  Attached to: $USER_NAME"
echo ""
echo "Next steps:"
echo "  1. Switch back to SpendSense credentials:"
echo "     aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID"
echo "     aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY"
echo "     (Replace with your actual credentials - do not commit secrets to git!)"
echo ""
echo "  2. Verify policy:"
echo "     aws iam list-attached-user-policies --user-name $USER_NAME"
echo ""
echo "  3. Deploy Lambda functions:"
echo "     python aws/scripts/deploy_lambda.py weekly_recap"
echo ""

