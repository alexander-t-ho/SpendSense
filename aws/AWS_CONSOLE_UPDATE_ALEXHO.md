# Update IAM Policy - AlexHo Prefix Version

## What Changed

All resources now use the **`alexho-`** prefix to distinguish from other projects:

- **S3 Buckets**: `alexho-spendsense-*`
- **DynamoDB Tables**: `alexho-spendsense-*`
- **Lambda Functions**: `alexho-spendsense-*`
- **IAM Roles**: `AlexHoSpendSense*`
- **CloudWatch Logs**: Account-scoped to `971422717446`

## Updated Policy JSON

Use this updated policy in AWS Console:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::alexho-spendsense-*",
        "arn:aws:s3:::alexho-spendsense-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:971422717446:table/alexho-spendsense-*"
      ]
    },
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
        "arn:aws:lambda:us-east-1:971422717446:function:alexho-spendsense-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:POST",
        "apigateway:PUT",
        "apigateway:DELETE",
        "apigateway:PATCH"
      ],
      "Resource": [
        "arn:aws:apigateway:us-east-1::/restapis/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:971422717446:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::971422717446:role/AlexHoSpendSense*"
    }
  ]
}
```

## Key Changes from Your Current Policy

1. **Added Lambda permissions**:
   - `lambda:CreateFunction` - Create new Lambda functions
   - `lambda:DeleteFunction` - Delete Lambda functions
   - `lambda:AddPermission` - Add API Gateway permissions
   - `lambda:RemovePermission` - Remove permissions
   - `lambda:GetFunctionConfiguration`, `lambda:TagResource`, etc.

2. **Added IAM PassRole**: Allows Lambda to assume execution roles

3. **Added AlexHo prefix** to all resources:
   - S3: `alexho-spendsense-*`
   - DynamoDB: `alexho-spendsense-*`
   - Lambda: `alexho-spendsense-*`
   - IAM Roles: `AlexHoSpendSense*`

4. **Account-scoped resources**: DynamoDB, Lambda, and CloudWatch Logs are now explicitly scoped to account `971422717446`

## Steps to Update in AWS Console

1. Go to: https://console.aws.amazon.com/iam/
2. **Option A: Update existing policy**:
   - Click **"Policies"** → Search: `SpendSenseUserPolicy-development`
   - Click **"Edit policy"** → **"JSON"** tab
   - **Replace the entire JSON** with the policy above
   - Click **"Review policy"** → **"Save changes"**
3. **Option B: Create new policy with AlexHo prefix** (Recommended):
   - Click **"Policies"** → **"Create policy"**
   - Click **"JSON"** tab → Paste the policy above
   - **Name**: `AlexHoSpendSenseUserPolicy-development`
   - Click **"Create policy"**
   - Attach to user `SpendSense_AlexHo`
   - See `aws/RENAME_POLICY_INSTRUCTIONS.md` for details

## After Updating

Once you save the policy, you'll need to:

1. **Update existing resources** to use the `alexho-` prefix (or create new ones)
2. **Update configuration files** to reflect the new naming
3. **Deploy Lambda functions** with the new naming convention

## Important Notes

- **Existing resources** (S3 buckets, DynamoDB tables, Lambda functions) that were created with the old `spendsense-*` naming will still work, but new resources should use `alexho-spendsense-*`
- The policy allows both old and new naming patterns during migration
- You can gradually migrate resources to use the `alexho-` prefix

