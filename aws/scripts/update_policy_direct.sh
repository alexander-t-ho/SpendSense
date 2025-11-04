#!/bin/bash
# Direct IAM policy update using AWS CLI
# This script creates a new policy version with updated Lambda permissions

set -e

POLICY_NAME="AlexHoSpendSenseUserPolicy-development"
POLICY_ARN="arn:aws:iam::971422717446:policy/${POLICY_NAME}"
TEMP_POLICY=$(mktemp)

echo "============================================================"
echo "Updating IAM Policy: ${POLICY_NAME}"
echo "============================================================"
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

echo "Policy document created: $TEMP_POLICY"
echo ""

# Check if we can access IAM
echo "Checking IAM access..."
if ! aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "❌ Cannot access IAM policy. You may need:"
    echo "   1. Different AWS credentials with IAM permissions"
    echo "   2. Use AWS Console instead (see aws/scripts/update_iam_policy_console.md)"
    echo ""
    echo "Current user:"
    aws sts get-caller-identity --query 'Arn' --output text
    rm "$TEMP_POLICY"
    exit 1
fi

echo "✅ IAM access confirmed"
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

# Show Lambda permissions
echo "Lambda permissions in policy:"
aws iam get-policy-version \
    --policy-arn "$POLICY_ARN" \
    --version-id "$NEW_VERSION" \
    --query 'PolicyVersion.Document.Statement[?Action[?contains(@, `lambda`)]]' \
    --output json | python3 -m json.tool 2>/dev/null || echo "  (check policy in AWS Console)"

echo ""
echo "✅ Update complete! You can now deploy Lambda functions."
echo "  python aws/scripts/deploy_lambda.py weekly_recap"

