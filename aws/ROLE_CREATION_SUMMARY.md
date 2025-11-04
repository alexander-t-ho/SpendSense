# Lambda Role Creation Summary

## What's Been Prepared

I've created a script that will create the Lambda role using your existing IAM structure:

**Script**: `aws/scripts/create_role_using_existing_iam.sh`

## How It Utilizes Existing IAM

1. **Resource Patterns**: Uses the same resource patterns as your existing policy:
   - `alexho-spendsense-*` for S3 buckets
   - `spendsense-*` for S3 buckets (alternative naming)
   - `alexho-spendsense-*` and `spendsense-*` for DynamoDB tables

2. **Policy Structure**: Creates a custom policy that matches your `POLICY_JSON_UPDATED.json` structure

3. **PassRole Permission**: Your user already has `iam:PassRole` permission for `AlexHoSpendSense*` roles, so once the role is created, you can deploy Lambda functions

## What the Role Will Have

- **Trust Policy**: Allows Lambda service to assume the role
- **Attached Policies**:
  - `AWSLambdaBasicExecutionRole` (AWS managed - for CloudWatch Logs)
  - `AlexHoSpendSenseLambdaPolicy-dev` (Custom - for S3 & DynamoDB access)

## To Create the Role

Run the script with admin credentials:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=<admin-key>
export AWS_SECRET_ACCESS_KEY=<admin-secret>
./aws/scripts/create_role_using_existing_iam.sh

# Option 2: Admin profile
export AWS_PROFILE=<admin-profile>
./aws/scripts/create_role_using_existing_iam.sh
```

## After Role Creation

Once the role is created, you can immediately deploy Lambda functions:

```bash
python aws/scripts/deploy_lambda.py all
```

Your user already has all necessary permissions to deploy Lambda functions once the role exists, because:
- ✅ Lambda permissions: `lambda:CreateFunction`, `lambda:UpdateFunctionCode`, etc.
- ✅ PassRole permission: `iam:PassRole` for `AlexHoSpendSense*` roles
- ✅ API Gateway permissions: Already configured
- ✅ CloudWatch Logs permissions: Already configured

## Next Steps

1. Run the role creation script with admin credentials
2. Deploy Lambda functions: `python aws/scripts/deploy_lambda.py all`
3. Update API Gateway: `python aws/scripts/update_lambda_integrations.py`

