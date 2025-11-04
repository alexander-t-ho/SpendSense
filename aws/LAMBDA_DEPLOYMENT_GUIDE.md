# Lambda Deployment Guide

## Prerequisites

1. ✅ IAM Policy attached to user `SpendSense_AlexHo`
2. ⏳ Lambda execution role created: `AlexHoSpendSenseLambdaRole-dev`
3. ✅ Lambda function names updated to use `alexho-` prefix

## Step-by-Step Deployment

### Step 1: Create Lambda Execution Role

**Run with admin credentials:**

```bash
./aws/scripts/create_lambda_role.sh
```

Or use environment variables:
```bash
export AWS_ACCESS_KEY_ID=<admin-access-key>
export AWS_SECRET_ACCESS_KEY=<admin-secret-key>
./aws/scripts/create_lambda_role.sh
```

**What this does:**
- Creates IAM role: `AlexHoSpendSenseLambdaRole-dev`
- Attaches AWS managed policy: `AWSLambdaBasicExecutionRole`
- Creates and attaches custom policy for S3 and DynamoDB access

### Step 2: Deploy Lambda Functions

Once the role is created, deploy Lambda functions:

```bash
# Deploy a single function
python aws/scripts/deploy_lambda.py weekly_recap

# Deploy all functions
python aws/scripts/deploy_lambda.py all
```

**Functions to deploy:**
- `alexho-spendsense-insights-weekly-recap-dev`
- `alexho-spendsense-insights-spending-analysis-dev`
- `alexho-spendsense-insights-net-worth-dev`
- `alexho-spendsense-insights-budget-suggestion-dev`
- `alexho-spendsense-insights-budget-tracking-dev`

### Step 3: Update API Gateway Integrations

After Lambda functions are deployed, update API Gateway:

```bash
python aws/scripts/update_lambda_integrations.py
```

This will:
- Link API Gateway endpoints to Lambda functions
- Set up proper permissions
- Deploy the API to the `dev` stage

### Step 4: Verify Deployment

```bash
# List Lambda functions
aws lambda list-functions --region us-east-1 | grep alexho-spendsense

# Test API Gateway endpoint
curl https://43k2bhxxpi.execute-api.us-east-1.amazonaws.com/dev/insights/{user_id}/weekly-recap
```

## Troubleshooting

### Error: Role cannot be assumed by Lambda
- Make sure the role has the correct trust policy
- Verify role exists: `aws iam get-role --role-name AlexHoSpendSenseLambdaRole-dev`

### Error: AccessDenied when deploying
- Verify policy is attached: `aws iam list-attached-user-policies --user-name SpendSense_AlexHo`
- Check policy allows `lambda:CreateFunction` for `alexho-spendsense-*` functions

### Error: Function not found
- Deploy the function first: `python aws/scripts/deploy_lambda.py weekly_recap`
- Check function name matches: `alexho-spendsense-insights-weekly-recap-dev`

## Current Status

✅ Policy attached to user
✅ Function names updated to `alexho-` prefix
⏳ Lambda execution role (needs admin credentials)
⏳ Lambda functions deployment
⏳ API Gateway integrations

