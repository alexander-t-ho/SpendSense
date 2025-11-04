#!/bin/bash
# Configure AWS CLI with SpendSense credentials

set -e

echo "============================================================"
echo "Configuring AWS CLI for SpendSense"
echo "============================================================"
echo ""

# Load credentials from file
CREDENTIALS_FILE="$(dirname "$0")/../config/.aws_credentials.txt"

if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "❌ Credentials file not found: $CREDENTIALS_FILE"
    echo "   Run create_iam_user.py first"
    exit 1
fi

# Extract credentials
ACCESS_KEY_ID=$(grep "AWS_ACCESS_KEY_ID=" "$CREDENTIALS_FILE" | cut -d'=' -f2)
SECRET_ACCESS_KEY=$(grep "AWS_SECRET_ACCESS_KEY=" "$CREDENTIALS_FILE" | cut -d'=' -f2)
REGION=$(grep "AWS_DEFAULT_REGION=" "$CREDENTIALS_FILE" | cut -d'=' -f2)

if [ -z "$ACCESS_KEY_ID" ] || [ -z "$SECRET_ACCESS_KEY" ]; then
    echo "❌ Could not extract credentials from file"
    exit 1
fi

echo "Configuring AWS CLI with SpendSense credentials..."
echo ""

# Configure default profile
aws configure set aws_access_key_id "$ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$SECRET_ACCESS_KEY"
aws configure set default.region "$REGION"

echo "✅ AWS CLI configured!"
echo ""

# Verify
echo "Verifying configuration..."
aws sts get-caller-identity

echo ""
echo "✅ Configuration complete!"
echo ""
echo "Current user:"
aws sts get-caller-identity --query 'Arn' --output text

