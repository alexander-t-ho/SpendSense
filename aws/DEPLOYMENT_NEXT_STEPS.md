# Lambda Deployment - Next Steps

## Current Status

✅ **Completed:**
- Lambda handler code created for all 5 functions
- Deployment scripts ready
- API Gateway integration script ready
- Configuration files set up

⏳ **Pending:**
- Create Lambda execution role (requires admin credentials)
- Deploy Lambda functions
- Update API Gateway integrations

## Step 1: Create Lambda Execution Role

You need **admin credentials** to create the IAM role. Choose one of these options:

### Option A: Interactive Prompt (Recommended)
```bash
cd /Users/alexho/SpendSense
./aws/scripts/create_lambda_role.sh
```
This will prompt you for admin AWS credentials.

### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=<your-admin-access-key>
export AWS_SECRET_ACCESS_KEY=<your-admin-secret-key>
./aws/scripts/create_role_with_admin.sh
```

### Option C: AWS Profile
```bash
export AWS_ADMIN_PROFILE=<your-admin-profile-name>
./aws/scripts/create_role_with_admin.sh
```

### What This Creates:
- IAM Role: `AlexHoSpendSenseLambdaRole-dev`
- Attached Policies:
  - `AWSLambdaBasicExecutionRole` (CloudWatch Logs)
  - `AlexHoSpendSenseLambdaPolicy-dev` (S3 & DynamoDB access)

## Step 2: Deploy Lambda Functions

Once the role is created, deploy all functions:

```bash
python aws/scripts/deploy_lambda.py all
```

This will deploy:
- `alexho-spendsense-insights-weekly-recap-dev`
- `alexho-spendsense-insights-spending-analysis-dev`
- `alexho-spendsense-insights-net-worth-dev`
- `alexho-spendsense-insights-budget-suggestion-dev`
- `alexho-spendsense-insights-budget-tracking-dev`

## Step 3: Update API Gateway Integrations

Connect API Gateway to the Lambda functions:

```bash
python aws/scripts/update_lambda_integrations.py
```

This will:
- Update API Gateway endpoints to invoke Lambda functions
- Grant API Gateway permission to invoke Lambda
- Redeploy the API

## All-in-One Deployment

You can also run the complete deployment script (it will prompt for credentials if needed):

```bash
./aws/scripts/deploy_all_steps.sh
```

## Verification

After deployment, verify in AWS Console:

1. **Lambda Functions**: https://console.aws.amazon.com/lambda/
   - Check that all 5 functions are deployed
   - Test each function

2. **API Gateway**: https://console.aws.amazon.com/apigateway/
   - Verify endpoints are connected to Lambda
   - Test endpoints

3. **IAM Role**: https://console.aws.amazon.com/iam/
   - Verify `AlexHoSpendSenseLambdaRole-dev` exists
   - Check attached policies

## Troubleshooting

### "AccessDenied" when creating role
- Ensure you're using admin credentials
- Check that your AWS account has IAM permissions

### "Role not found" when deploying
- Verify the role was created successfully
- Check role name matches: `AlexHoSpendSenseLambdaRole-dev`

### Lambda deployment fails
- Check that you have permissions to create Lambda functions
- Verify the role ARN is correct in `aws/config/aws_resources.json`

### API Gateway integration fails
- Ensure Lambda functions are deployed first
- Check API Gateway ID in `aws/config/aws_resources.json`

## Next Steps After Deployment

1. Test Lambda functions individually in AWS Console
2. Test API Gateway endpoints
3. Update frontend to call Lambda endpoints (if migrating from local API)
4. Set up CloudWatch alarms for monitoring
5. Configure Lambda environment variables if needed

