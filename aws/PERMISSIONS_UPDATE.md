# IAM Permissions Update Required

## Issue
The `SpendSense_AlexHo` IAM user needs additional permissions to create and manage Lambda functions.

## Required Permissions

The IAM policy `SpendSenseUserPolicy-development` needs to include these Lambda actions:

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
        "lambda:RemovePermission"
    ],
    "Resource": [
        "arn:aws:lambda:us-east-1:*:function:spendsense-*"
    ]
}
```

## How to Update

### Option 1: AWS Console (Recommended)
1. Go to IAM Console: https://console.aws.amazon.com/iam/
2. Click "Policies" → Search for "SpendSenseUserPolicy-development"
3. Click "Edit policy" → "JSON" tab
4. Find the Lambda statement and update with the actions above
5. Click "Review policy" → "Save changes"

### Option 2: AWS CLI (requires admin access)
```bash
# Get current policy
aws iam get-policy --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development

# Update policy with new version (see aws/scripts/create_iam_user.py for full policy document)
aws iam create-policy-version \
  --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development \
  --policy-document file://updated-policy.json \
  --set-as-default
```

## Verification
After updating permissions, verify:
```bash
aws lambda list-functions --region us-east-1 | grep spendsense
python aws/scripts/deploy_lambda.py weekly_recap
```

## Current Status
- ✅ Parquet files uploaded to S3
- ✅ API Gateway configured
- ⏳ Lambda functions: Waiting for permissions update
- ✅ Local development: Can continue with insights implementation

## Note
You can continue developing insights locally while permissions are being updated. Lambda deployment can happen once permissions are fixed.

