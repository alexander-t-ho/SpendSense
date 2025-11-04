# AWS Deployment Guide

Complete guide for deploying SpendSense insights computation to AWS.

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure list
   ```

2. **AWS Credentials**
   - Profile: `default`
   - IAM User: `alexho27x@gmail.com`
   - Region: `us-east-1`

3. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Deployment

### Option 1: Deploy Everything (Recommended)
```bash
./aws/scripts/deploy_all.sh
```

### Option 2: Step-by-Step Deployment

#### Step 1: Setup AWS Infrastructure
Creates S3 buckets, DynamoDB tables, IAM roles, and CloudWatch log groups:
```bash
python aws/scripts/setup_aws_resources.py
```

**Expected Output:**
- ✅ 3 S3 buckets created
- ✅ 2 DynamoDB tables created
- ✅ 1 IAM role created
- ✅ 5 CloudWatch log groups created

#### Step 2: Upload Parquet Files to S3
Uploads existing feature Parquet files to S3:
```bash
python aws/scripts/upload_parquet_to_s3.py
```

**Note:** Make sure you've generated Parquet files first:
```bash
python -m features.pipeline --window-days 30
python -m features.pipeline --window-days 180
```

#### Step 3: Deploy Lambda Functions
Packages and deploys all Lambda functions:
```bash
python aws/scripts/deploy_lambda.py
```

Or deploy individual functions:
```bash
python aws/scripts/deploy_lambda.py weekly_recap
python aws/scripts/deploy_lambda.py spending_analysis
```

#### Step 4: Setup API Gateway
Creates REST API with endpoints for all insights:
```bash
python aws/scripts/setup_api_gateway.py
```

**Expected Output:**
- ✅ API Gateway created
- ✅ 5 endpoints configured
- ✅ API deployed to `dev` stage

#### Step 5: Update Lambda Integrations
After Lambda functions are deployed, update API Gateway integrations:
```bash
python aws/scripts/update_lambda_integrations.py
```

## Resource Information

After deployment, all resource information is saved to:
- `aws/config/aws_resources.json`

### Current Resources

**S3 Buckets:**
- `spendsense-parquet-data-bda3bf9a` - Feature Parquet files
- `spendsense-insights-bda3bf9a` - Insights cache
- `spendsense-historical-bda3bf9a` - Historical snapshots

**DynamoDB Tables:**
- `spendsense-insights-metadata-dev` - Computation tracking
- `spendsense-user-preferences-dev` - User feedback

**API Gateway:**
- API ID: `43k2bhxxpi`
- Endpoint: `https://43k2bhxxpi.execute-api.us-east-1.amazonaws.com/dev`
- Stage: `dev`

**Lambda Functions:**
- `spendsense-insights-weekly-recap-dev`
- `spendsense-insights-spending-analysis-dev`
- `spendsense-insights-net-worth-dev`
- `spendsense-insights-budget-suggestion-dev`
- `spendsense-insights-budget-tracking-dev`

## Testing the Deployment

### Test API Gateway Endpoints

```bash
# Get API endpoint from aws_resources.json
API_URL="https://43k2bhxxpi.execute-api.us-east-1.amazonaws.com/dev"

# Test weekly recap (replace USER_ID with actual user ID)
curl "${API_URL}/insights/USER_ID/weekly-recap"

# Test with week_start parameter
curl "${API_URL}/insights/USER_ID/weekly-recap?week_start=2024-11-01"
```

### Test Lambda Functions Directly

```bash
# List Lambda functions
aws lambda list-functions --region us-east-1 | grep spendsense

# Invoke Lambda function directly
aws lambda invoke \
  --function-name spendsense-insights-weekly-recap-dev \
  --payload '{"pathParameters":{"user_id":"YOUR_USER_ID"}}' \
  --region us-east-1 \
  response.json

cat response.json
```

## Monitoring

### CloudWatch Logs

View logs for Lambda functions:
```bash
# Weekly recap logs
aws logs tail /aws/lambda/spendsense-insights-weekly-recap-dev --follow

# All Lambda logs
aws logs tail /aws/lambda --follow
```

### CloudWatch Metrics

View metrics in AWS Console:
- Lambda invocations and errors
- API Gateway request count and latency
- S3 storage usage

## Troubleshooting

### Lambda Function Not Found
**Error:** `Function not found`
**Solution:** Deploy Lambda functions first:
```bash
python aws/scripts/deploy_lambda.py
```

### API Gateway Integration Errors
**Error:** `Integration failed`
**Solution:** Update integrations after Lambda deployment:
```bash
python aws/scripts/update_lambda_integrations.py
```

### Permission Errors
**Error:** `Access Denied`
**Solution:** Check IAM permissions. Your IAM user needs:
- S3: CreateBucket, PutObject, GetObject
- DynamoDB: CreateTable, PutItem, GetItem
- Lambda: CreateFunction, UpdateFunction, InvokeFunction
- API Gateway: Create*, Update*, Deploy*

### Database Access in Lambda
**Current:** Lambda functions use local SQLite file path
**Future:** For production, consider:
- RDS (PostgreSQL/MySQL)
- DynamoDB for transactional data
- S3 for large datasets

## Cost Monitoring

Current estimated costs (development):
- S3: ~$1/month
- DynamoDB: ~$5/month (on-demand)
- Lambda: ~$5/month
- API Gateway: ~$1/month
- CloudWatch: ~$2/month
- **Total: ~$14/month**

Set up billing alerts in AWS Console if needed.

## Next Steps

1. ✅ **Infrastructure Ready** - All AWS resources created
2. ⏳ **Deploy Lambda Functions** - Implement and deploy handlers
3. ⏳ **Test Endpoints** - Verify API Gateway works
4. ⏳ **Frontend Integration** - Connect frontend to API Gateway
5. ⏳ **Production Setup** - Add authentication, rate limiting, etc.

## Configuration

All configuration is in:
- `aws/config/aws_config.yaml` - Main configuration
- `aws/config/aws_resources.json` - Generated resource information

## Support

For issues or questions:
- Check CloudWatch logs for errors
- Verify IAM permissions
- Review AWS Console for resource status
- Check `aws/scripts/README.md` for script details

