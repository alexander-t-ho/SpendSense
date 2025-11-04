# AWS Infrastructure for SpendSense

This directory contains AWS infrastructure setup and deployment scripts for SpendSense insights computation.

## Quick Start

### 1. Prerequisites
- AWS CLI installed and configured
- AWS credentials set up (profile: `default`)
- Python dependencies installed: `pip install -r requirements.txt`

### 2. Initial Setup (One-time)
```bash
python aws/scripts/setup_aws_resources.py
```

This creates:
- ✅ S3 buckets (auto-generated unique names)
- ✅ DynamoDB tables
- ✅ IAM roles and policies
- ✅ CloudWatch log groups

### 3. Upload Parquet Files
```bash
python aws/scripts/upload_parquet_to_s3.py
```

### 4. Deploy Lambda Functions
```bash
python aws/scripts/deploy_lambda.py
```

## Resource Information

After running setup, resource information is saved to:
- `aws/config/aws_resources.json` - All resource names and ARNs

## Configuration

Configuration is in `aws/config/aws_config.yaml`:
- **Region**: `us-east-1`
- **Environment**: `development`
- **IAM User**: `alexho27x@gmail.com`

## S3 Buckets

Auto-generated bucket names (unique suffixes):
- `spendsense-parquet-data-{suffix}` - Feature Parquet files
- `spendsense-insights-{suffix}` - Computed insights cache
- `spendsense-historical-{suffix}` - Net worth snapshots and historical data

## DynamoDB Tables

- `spendsense-insights-metadata-dev` - Tracks when insights were computed
- `spendsense-user-preferences-dev` - User feedback and preferences

## Lambda Functions

Five Lambda functions for insights computation:
1. `spendsense-insights-weekly-recap-dev`
2. `spendsense-insights-spending-analysis-dev`
3. `spendsense-insights-net-worth-dev`
4. `spendsense-insights-budget-suggestion-dev`
5. `spendsense-insights-budget-tracking-dev`

## Cost Estimation

**Development (Current):**
- S3: ~$1/month (10GB storage)
- DynamoDB: ~$5/month (on-demand, low usage)
- Lambda: ~$5/month (1M requests, 512MB)
- CloudWatch: ~$2/month (logs)
- **Total: ~$13/month**

## Troubleshooting

### AWS CLI Not Configured
```bash
aws configure
# Enter credentials for alexho27x@gmail.com
```

### Permission Errors
Make sure your IAM user has permissions for:
- S3 (CreateBucket, PutObject, GetObject)
- DynamoDB (CreateTable, PutItem, GetItem)
- IAM (CreateRole, AttachRolePolicy)
- Lambda (CreateFunction, UpdateFunction)
- CloudWatch Logs (CreateLogGroup)

### Check Resources
```bash
# List S3 buckets
aws s3 ls | grep spendsense

# List DynamoDB tables
aws dynamodb list-tables --region us-east-1

# List Lambda functions
aws lambda list-functions --region us-east-1 | grep spendsense
```

## Next Steps

1. ✅ **Setup Complete** - Infrastructure is ready
2. ⏳ **Deploy Lambda Functions** - Implement and deploy Lambda handlers
3. ⏳ **Set up API Gateway** - Connect Lambda functions to REST API
4. ⏳ **Test Integration** - Verify everything works end-to-end

