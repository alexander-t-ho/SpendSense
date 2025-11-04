#!/bin/bash
# Setup AWS CLI for SpendSense project

set -e

echo "============================================================"
echo "AWS CLI Setup for SpendSense"
echo "============================================================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed!"
    echo ""
    echo "Install AWS CLI:"
    echo "  macOS: brew install awscli"
    echo "  Linux: sudo apt-get install awscli"
    echo "  Or visit: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✅ AWS CLI is installed"
aws --version
echo ""

# Check current configuration
echo "Current AWS Configuration:"
aws configure list
echo ""

# Ask user if they want to configure
read -p "Do you want to configure AWS CLI? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Configuring AWS CLI..."
    echo "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region: us-east-1"
    echo "  - Default output format: json"
    echo ""
    
    aws configure
    
    echo ""
    echo "✅ AWS CLI configured!"
    echo ""
    
    # Verify connection
    echo "Verifying connection..."
    aws sts get-caller-identity
    
    echo ""
    echo "✅ Connection verified!"
fi

echo ""
echo "============================================================"
echo "Next Steps:"
echo "============================================================"
echo "1. Verify connection: python aws/scripts/verify_aws_connection.py"
echo "2. Set up resources: python aws/scripts/setup_aws_resources.py"
echo "3. Deploy application: See aws/DEPLOYMENT_GUIDE.md"
echo ""

