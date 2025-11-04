# Update IAM Policy via AWS Console - Step by Step

## Quick Steps (5 minutes)

### Step 1: Log in to AWS Console

1. Go to: **https://console.aws.amazon.com/iam/**
2. Sign in with your **root account** or an **admin account** that has IAM permissions

### Step 2: Navigate to Policies

1. In the left sidebar, click **"Policies"**
2. In the search box, type: `SpendSenseUserPolicy-development`
3. Click on the policy name when it appears

### Step 3: Edit the Policy

1. Click the **"Edit policy"** button (top right)
2. Click the **"JSON"** tab (at the top)

### Step 4: Find and Update the Lambda Statement

1. Scroll down to find the statement that contains `"lambda:InvokeFunction"` (around line 148-164)
2. **Replace the entire Lambda statement** with this:

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
    "arn:aws:lambda:us-east-1:971422717446:function:spendsense-*"
  ]
}
```

### Step 5: Add IAM PassRole Statement (if not present)

1. Scroll to the end of the `"Statement"` array
2. Check if there's already a statement with `"iam:PassRole"`
3. If NOT present, add this statement (before the closing `]`):

```json
{
  "Effect": "Allow",
  "Action": [
    "iam:PassRole"
  ],
  "Resource": "arn:aws:iam::971422717446:role/SpendSense*"
}
```

### Step 6: Verify the Complete Policy

Your policy should look like this (with all statements):

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
        "arn:aws:s3:::spendsense-*",
        "arn:aws:s3:::spendsense-*/*"
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
        "arn:aws:dynamodb:us-east-1:971422717446:table/spendsense-*"
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
        "arn:aws:lambda:us-east-1:971422717446:function:spendsense-*"
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
      "Resource": "arn:aws:logs:*:*:*"
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
      "Resource": "arn:aws:iam::971422717446:role/SpendSense*"
    }
  ]
}
```

### Step 7: Save Changes

1. Click **"Review policy"** button (bottom right)
2. Review the summary (should show "Policy changes" with updated Lambda permissions)
3. Click **"Save changes"** button

### Step 8: Verify Update

1. You should see a success message: "Policy updated successfully"
2. The policy should now show the updated version

## Alternative: Use "Visual Editor" (Optional)

If you prefer the visual editor:

1. Click **"Visual editor"** tab instead of JSON
2. Find the statement with Lambda actions
3. Click **"Edit statement"**
4. Add these actions:
   - `lambda:CreateFunction`
   - `lambda:UpdateFunctionCode`
   - `lambda:UpdateFunctionConfiguration`
   - `lambda:DeleteFunction`
   - `lambda:AddPermission`
   - `lambda:RemovePermission`
   - (Keep all existing Lambda actions)
5. Click **"Save changes"**

## After Updating

Once the policy is updated in the console:

1. **Go back to your terminal**
2. **Test the update**:
   ```bash
   # Verify policy was updated
   aws iam get-policy --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development
   
   # Deploy Lambda functions (should work now!)
   python aws/scripts/deploy_lambda.py weekly_recap
   ```

## Troubleshooting

**If you can't find the policy:**
- Make sure you're in the correct AWS account: `971422717446`
- Check the region selector (should be "Global" or "US East (N. Virginia)")
- Try searching for just "SpendSense" without the full name

**If you get "Access Denied" when editing:**
- You need to use an account with IAM permissions (root account or admin user)
- Root account: The email address you use to sign in to AWS
- Admin user: A user with `IAMFullAccess` or `AdministratorAccess` policy

**If you're part of an organization:**
- Make sure you're signed in to the correct account (`971422717446`)
- Organization admins might need to grant you permissions

## Quick Link

Direct link to IAM Policies (if you're already logged in):
**https://console.aws.amazon.com/iam/home#/policies**

