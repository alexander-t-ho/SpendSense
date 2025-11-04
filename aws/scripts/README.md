# AWS Deployment Scripts

This directory contains scripts for deploying and managing AWS infrastructure for SpendSense.

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure list
   ```

2. **Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **AWS credentials**
   - Make sure your AWS CLI profile is configured
   - Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables

## Setup Scripts

### 1. Setup AWS Resources
Creates all AWS infrastructure (S3, DynamoDB, IAM, CloudWatch):
```bash
python aws/scripts/setup_aws_resources.py
```

This will:
- Create S3 buckets for Parquet data, insights cache, and historical data
- Create DynamoDB tables for metadata and user preferences
- Create IAM roles and policies
- Create CloudWatch log groups
- Save resource information to `aws/config/aws_resources.json`

### 2. Deploy Lambda Functions
Deploy Lambda functions for insights computation:
```bash
python aws/scripts/deploy_lambda.py
```

### 3. Setup API Gateway
Configure API Gateway endpoints:
```bash
python aws/scripts/setup_api_gateway.py
```

### 4. Upload Parquet Files to S3
Upload existing Parquet files to S3:
```bash
python aws/scripts/upload_parquet_to_s3.py
```

## Configuration

All configuration is in `aws/config/aws_config.yaml`. Key settings:
- AWS region: `us-east-1`
- Environment: `development`
- IAM user: `alexho27x@gmail.com`

## Resource Names

After running setup, resource names are saved to `aws/config/aws_resources.json`:
- S3 bucket names (auto-generated with unique suffixes)
- DynamoDB table names
- IAM role ARNs
- Lambda function names

## Troubleshooting

### AWS CLI Not Configured
```bash
aws configure
# Enter your Access Key ID, Secret Access Key, region (us-east-1), and output format (json)
```

### Permission Errors
Make sure your AWS IAM user has permissions to:
- Create S3 buckets
- Create DynamoDB tables
- Create IAM roles
- Create Lambda functions
- Create API Gateway

### Region Mismatch
Make sure the region in `aws_config.yaml` matches your AWS CLI default region.

