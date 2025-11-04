#!/bin/bash
# Update IAM policy using admin credentials
# This script allows you to specify a different AWS profile with admin permissions

set -e

echo "============================================================"
echo "Update IAM Policy - Admin Mode"
echo "============================================================"
echo ""

# Check if profile is provided
PROFILE=${1:-admin}

echo "Using AWS profile: $PROFILE"
echo ""

# Check if profile exists
if ! aws configure list-profiles 2>/dev/null | grep -q "^$PROFILE$"; then
    echo "⚠️  Profile '$PROFILE' not found in AWS config."
    echo ""
    echo "Available profiles:"
    aws configure list-profiles 2>/dev/null || echo "  (none found)"
    echo ""
    echo "Usage:"
    echo "  $0 [profile-name]"
    echo ""
    echo "Or set up a profile:"
    echo "  aws configure --profile $PROFILE"
    exit 1
fi

# Verify we can access IAM
echo "Verifying IAM access..."
if ! aws iam get-user --profile $PROFILE > /dev/null 2>&1; then
    echo "❌ Cannot access IAM with profile '$PROFILE'"
    echo "   Make sure this profile has IAM permissions"
    exit 1
fi

echo "✅ IAM access verified"
echo ""

# Create temporary policy document
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_POLICY=$(mktemp)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Generate policy document using Python
python3 << 'PYEOF' > "$TEMP_POLICY"
import json

policy_doc = {
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

print(json.dumps(policy_doc, indent=2))
PYEOF

POLICY_NAME="AlexHoSpendSenseUserPolicy-development"
POLICY_ARN="arn:aws:iam::971422717446:policy/${POLICY_NAME}"

echo "Updating policy: $POLICY_ARN"
echo ""

# Create new policy version
aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document "file://$TEMP_POLICY" \
    --set-as-default \
    --profile "$PROFILE"

echo ""
echo "✅ Policy updated successfully!"
echo ""

# Clean up temp file
rm "$TEMP_POLICY"

# Verify
echo "Verifying new policy version..."
aws iam get-policy-version \
    --policy-arn "$POLICY_ARN" \
    --version-id "$(aws iam get-policy --policy-arn "$POLICY_ARN" --profile "$PROFILE" --query 'Policy.DefaultVersionId' --output text)" \
    --profile "$PROFILE" \
    --query 'PolicyVersion.Document' \
    --output json | python3 -m json.tool | head -20

echo ""
echo "✅ Verification complete!"
echo ""
echo "You can now deploy Lambda functions:"
echo "  python aws/scripts/deploy_lambda.py weekly_recap"

