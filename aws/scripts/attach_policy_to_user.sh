#!/bin/bash
# Attach IAM policy to user using AWS CLI

set -e

ACCOUNT_ID="971422717446"
POLICY_NAME="AlexHoSpendSenseUserPolicy-development"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
USER_NAME="SpendSense_AlexHo"

echo "============================================================"
echo "Attach IAM Policy to User"
echo "============================================================"
echo "Policy: $POLICY_NAME"
echo "User: $USER_NAME"
echo "============================================================"
echo ""

# Check current credentials first
CURRENT_CREDS_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "")
CURRENT_CREDS_USER=$(aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null || echo "")

# Check if we need admin credentials
NEED_ADMIN=false
if [ -z "$CURRENT_CREDS_ACCOUNT" ]; then
    NEED_ADMIN=true
elif [[ "$CURRENT_CREDS_USER" == *"SpendSense_AlexHo"* ]]; then
    echo "⚠️  Current credentials are for SpendSense_AlexHo user."
    echo "   This user doesn't have IAM permissions."
    echo "   You need admin credentials to attach policies."
    echo ""
    NEED_ADMIN=true
fi

# Prompt for admin credentials if needed
if [ "$NEED_ADMIN" = true ]; then
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "Admin credentials needed to attach policy."
        echo ""
        echo "Please provide admin credentials for account $ACCOUNT_ID:"
        echo "  (Use root account or an admin user with IAM permissions)"
        echo ""
        read -p "Enter AWS Access Key ID: " ADMIN_ACCESS_KEY
        read -sp "Enter AWS Secret Access Key: " ADMIN_SECRET_KEY
        echo ""
        
        export AWS_ACCESS_KEY_ID="$ADMIN_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$ADMIN_SECRET_KEY"
    fi
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

# Check if policy exists
echo "Checking if policy exists..."
if ! aws iam get-policy --policy-arn "$POLICY_ARN" > /dev/null 2>&1; then
    echo "❌ Policy not found: $POLICY_NAME"
    echo ""
    echo "Please create the policy first:"
    echo "  ./aws/scripts/create_policy_cli.sh"
    exit 1
fi

echo "✅ Policy found: $POLICY_NAME"
echo ""

# Check if user exists
echo "Checking if user exists..."
if ! aws iam get-user --user-name "$USER_NAME" > /dev/null 2>&1; then
    echo "❌ User not found: $USER_NAME"
    echo ""
    echo "Please create the user first:"
    echo "  python aws/scripts/create_iam_user.py"
    exit 1
fi

echo "✅ User found: $USER_NAME"
echo ""

# Check if policy is already attached
echo "Checking if policy is already attached..."
ATTACHED_POLICIES=$(aws iam list-attached-user-policies --user-name "$USER_NAME" --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN']" --output text)

if [ -n "$ATTACHED_POLICIES" ]; then
    echo "✅ Policy is already attached to user"
    echo ""
    echo "Current attached policies for $USER_NAME:"
    aws iam list-attached-user-policies --user-name "$USER_NAME" --output table
    exit 0
fi

# Attach policy to user
echo "Attaching policy to user..."
aws iam attach-user-policy \
    --user-name "$USER_NAME" \
    --policy-arn "$POLICY_ARN"

echo "✅ Policy attached successfully!"
echo ""

# List all attached policies
echo "Attached policies for $USER_NAME:"
aws iam list-attached-user-policies --user-name "$USER_NAME" --output table

echo ""
echo "============================================================"
echo "✅ Complete!"
echo "============================================================"
echo ""
echo "Policy Details:"
echo "  Policy: $POLICY_NAME"
echo "  ARN: $POLICY_ARN"
echo "  User: $USER_NAME"
echo ""
echo "Next steps:"
echo "  1. Switch back to SpendSense credentials:"
echo "     aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID"
echo "     aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY"
echo "     (Replace with your actual credentials - do not commit secrets to git!)"
echo ""
echo "  2. Verify policy attachment:"
echo "     aws iam list-attached-user-policies --user-name $USER_NAME"
echo ""
echo "  3. Test Lambda deployment:"
echo "     python aws/scripts/deploy_lambda.py weekly_recap"
echo ""

