# AWS Setup Requirements

This document outlines the AWS information needed to set up the infrastructure for SpendSense insights computation.

## Required Information

Please provide the following information for AWS setup:

### 1. AWS Region
- **Question**: Which AWS region do you want to use? (e.g., `us-east-1`, `us-west-2`, `eu-west-1`)
- **Default**: `us-east-1` (if no preference)
- **Usage**: All AWS resources will be created in this region

### 2. S3 Bucket Names
- **Question**: Preferred bucket names for:
  - Parquet data storage: `spendsense-parquet-data` (or your preference)
  - Insights cache: `spendsense-insights` (or your preference)
  - Historical data: `spendsense-historical` (or your preference)
- **Note**: Bucket names must be globally unique across all AWS accounts
- **Default**: Will use `spendsense-{name}-{random-suffix}` if names are taken

### 3. AWS Access Method
- **Question**: How do you want to provide AWS credentials?
  - Option A: AWS CLI profile (recommended for development)
  - Option B: AWS Access Key ID and Secret Access Key
  - Option C: IAM role (for production/EC2)
- **Default**: AWS CLI profile

### 4. AWS CLI Profile (if using Option A)
- **Question**: What is your AWS CLI profile name?
- **Default**: `default`
- **Command to check**: `aws configure list-profiles`

### 5. Environment
- **Question**: Is this for development, staging, or production?
- **Default**: `development`
- **Usage**: Determines resource naming and tagging

### 6. Budget Preferences
- **Question**: Do you want to set up billing alerts?
  - Yes: What's the monthly budget threshold? (e.g., $50, $100)
  - No: Skip billing alerts
- **Default**: No billing alerts

### 7. Existing Resources
- **Question**: Do you have any existing AWS resources we should use?
  - Existing VPC? (Yes/No)
  - Existing IAM roles? (Yes/No)
  - Existing S3 buckets? (Yes/No)
- **Default**: No existing resources

## Quick Setup Checklist

Once you provide the above information, we'll:
1. ✅ Create S3 buckets for Parquet storage
2. ✅ Set up IAM roles and policies
3. ✅ Create Lambda functions for insights computation
4. ✅ Configure API Gateway endpoints
5. ✅ Set up CloudWatch monitoring
6. ✅ Create deployment scripts
7. ✅ Test the setup with sample data

## Cost Estimation

**Development/Testing (Low Usage):**
- Lambda: ~$5/month
- S3: ~$1/month
- DynamoDB: ~$5/month (on-demand)
- API Gateway: ~$1/month
- CloudWatch: ~$2/month
- **Total: ~$14/month**

**Production (100 users):**
- Lambda: ~$20/month
- S3: ~$5/month
- DynamoDB: ~$10/month (on-demand)
- API Gateway: ~$10/month
- CloudWatch: ~$5/month
- **Total: ~$50/month**

## Next Steps

1. **Provide AWS Information**: Answer the questions above
2. **Review Configuration**: We'll create configuration files
3. **Deploy Infrastructure**: Run deployment scripts
4. **Test Setup**: Verify everything works with sample data
5. **Monitor**: Set up CloudWatch dashboards

## Questions?

If you have any questions about AWS setup, please refer to:
- AWS Lambda Documentation: https://docs.aws.amazon.com/lambda/
- AWS S3 Documentation: https://docs.aws.amazon.com/s3/
- AWS API Gateway Documentation: https://docs.aws.amazon.com/apigateway/

