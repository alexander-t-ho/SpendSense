# How to Update IAM Permissions for SpendSense_AlexHo

The `SpendSense_AlexHo` user doesn't have IAM permissions (this is a security best practice). You need to update the policy using an account with IAM permissions.

## Quick Solution: AWS Console (Recommended - 2 minutes)

1. **Go to AWS IAM Console**:
   - https://console.aws.amazon.com/iam/
   - Sign in with your root account or admin account

2. **Find the Policy**:
   - Click "Policies" in left sidebar
   - Search: `SpendSenseUserPolicy-development`
   - Click on the policy name

3. **Edit Policy**:
   - Click "Edit policy" button
   - Click "JSON" tab

4. **Find the Lambda Statement** (around line 148):
   Look for:
   ```json
   {
       "Effect": "Allow",
       "Action": [
           "lambda:InvokeFunction",
           "lambda:GetFunction",
           ...
       ],
   ```
   
   **Replace it with:**
   ```json
   {
       "Effect": "Allow",
       "Action": [
           "lambda:CreateFunction",
           "lambda:InvokeFunction",
           "lambda:GetFunction",
           "lambda:UpdateFunctionCode",
           "lambda:UpdateFunctionConfiguration",
           "lambda:DeleteFunction",
           "lambda:ListFunctions",
           "lambda:AddPermission",
           "lambda:RemovePermission",
           "lambda:GetFunctionConfiguration",
           "lambda:TagResource",
           "lambda:UntagResource",
           "lambda:ListTags"
       ],
       "Resource": [
           "arn:aws:lambda:us-east-1:*:function:spendsense-*"
       ]
   }
   ```

5. **Add IAM PassRole** (if not present):
   Add this statement at the end:
   ```json
   {
       "Effect": "Allow",
       "Action": [
           "iam:PassRole"
       ],
       "Resource": "arn:aws:iam::971422717446:role/SpendSense*"
   }
   ```

6. **Save**:
   - Click "Review policy"
   - Click "Save changes"

## Alternative: Use Different AWS Credentials

If you have another AWS account with IAM permissions:

```bash
# Option 1: Use environment variables
export AWS_ACCESS_KEY_ID=<admin-access-key>
export AWS_SECRET_ACCESS_KEY=<admin-secret-key>
./aws/scripts/update_policy_direct.sh

# Option 2: Use a different profile
aws configure --profile admin
AWS_PROFILE=admin ./aws/scripts/update_policy_direct.sh
```

## Verify Update

After updating, verify the policy works:

```bash
# Test Lambda list (should work now)
aws lambda list-functions --region us-east-1 | grep spendsense

# Deploy Lambda function
python aws/scripts/deploy_lambda.py weekly_recap
```

## What Changed

The policy now includes:
- ✅ `lambda:CreateFunction` - Create new Lambda functions
- ✅ `lambda:UpdateFunctionCode` - Update function code
- ✅ `lambda:UpdateFunctionConfiguration` - Update function settings
- ✅ `lambda:DeleteFunction` - Delete functions
- ✅ `lambda:AddPermission` - Add API Gateway permissions
- ✅ `iam:PassRole` - Allow Lambda to assume execution role

## Next Steps

Once permissions are updated:
1. Deploy Lambda functions: `python aws/scripts/deploy_lambda.py all`
2. Update API Gateway integrations: `python aws/scripts/update_lambda_integrations.py`
3. Test API endpoints: See `aws/DEPLOYMENT_GUIDE.md`

