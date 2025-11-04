#!/bin/bash
# Deploy all AWS resources for SpendSense

set -e

echo "============================================================"
echo "SpendSense Complete AWS Deployment"
echo "============================================================"
echo ""

# Step 1: Setup AWS Resources (if not already done)
echo "Step 1: Setting up AWS resources..."
python aws/scripts/setup_aws_resources.py
echo ""

# Step 2: Upload Parquet files to S3
echo "Step 2: Uploading Parquet files to S3..."
python aws/scripts/upload_parquet_to_s3.py
echo ""

# Step 3: Deploy Lambda functions
echo "Step 3: Deploying Lambda functions..."
python aws/scripts/deploy_lambda.py
echo ""

# Step 4: Setup API Gateway
echo "Step 4: Setting up API Gateway..."
python aws/scripts/setup_api_gateway.py
echo ""

# Step 5: Update Lambda integrations
echo "Step 5: Updating Lambda integrations..."
python aws/scripts/update_lambda_integrations.py
echo ""

echo "============================================================"
echo "✅ Complete AWS Deployment Finished!"
echo "============================================================"

