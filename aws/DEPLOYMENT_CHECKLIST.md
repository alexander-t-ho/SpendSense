# AWS Lambda Deployment Checklist

## Prerequisites ✅

- [x] IAM policy `AlexHoSpendSenseUserPolicy-development` created and attached
- [x] Lambda function names updated to `alexho-spendsense-*`
- [x] Lambda handlers created for all insights
- [x] Configuration files updated

## Deployment Steps

### Step 1: Create Lambda Execution Role ⏳

**Run with admin credentials:**

```bash
./aws/scripts/create_lambda_role.sh
```

**What this creates:**
- Role: `AlexHoSpendSenseLambdaRole-dev`
- Trust policy: Allows Lambda service to assume role
- Attached policies:
  - `AWSLambdaBasicExecutionRole` (AWS managed)
  - `AlexHoSpendSenseLambdaPolicy-dev` (Custom - S3, DynamoDB access)

### Step 2: Deploy Lambda Functions ⏳

Once the role is created:

```bash
# Deploy all functions
python aws/scripts/deploy_lambda.py all

# Or deploy individually
python aws/scripts/deploy_lambda.py weekly_recap
python aws/scripts/deploy_lambda.py spending_analysis
python aws/scripts/deploy_lambda.py budget_suggestion
python aws/scripts/deploy_lambda.py budget_tracking
python aws/scripts/deploy_lambda.py net_worth
```

**Functions to deploy:**
1. `alexho-spendsense-insights-weekly-recap-dev`
2. `alexho-spendsense-insights-spending-analysis-dev`
3. `alexho-spendsense-insights-budget-suggestion-dev`
4. `alexho-spendsense-insights-budget-tracking-dev`
5. `alexho-spendsense-insights-net-worth-dev`

### Step 3: Update API Gateway Integrations ⏳

After Lambda functions are deployed:

```bash
python aws/scripts/update_lambda_integrations.py
```

This will:
- Link API Gateway endpoints to Lambda functions
- Set up proper permissions for API Gateway to invoke Lambda
- Deploy API to `dev` stage

### Step 4: Verify Deployment ✅

```bash
# List all Lambda functions
aws lambda list-functions --region us-east-1 | grep alexho-spendsense

# Test API Gateway endpoint
API_URL="https://43k2bhxxpi.execute-api.us-east-1.amazonaws.com/dev"
curl "$API_URL/insights/{user_id}/weekly-recap"
```

## Current Status

✅ **Completed:**
- Policy attached to user
- All Lambda handlers created
- Configuration files updated
- Deployment scripts ready

⏳ **Pending (requires admin credentials):**
- Lambda execution role creation
- Lambda function deployment
- API Gateway integration updates

## Troubleshooting

### Role Creation Issues
- Use admin credentials (root account or admin user)
- Verify account ID: `971422717446`
- Check role name: `AlexHoSpendSenseLambdaRole-dev`

### Lambda Deployment Issues
- Verify policy allows `lambda:CreateFunction` for `alexho-spendsense-*`
- Check role ARN matches: `arn:aws:iam::971422717446:role/AlexHoSpendSenseLambdaRole-dev`
- Ensure handler paths are correct

### API Gateway Integration Issues
- Deploy Lambda functions first
- Run `update_lambda_integrations.py` after Lambda deployment
- Check API Gateway stage is deployed

