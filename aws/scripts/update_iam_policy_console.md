# Update IAM Policy via AWS Console

Since the `SpendSense_AlexHo` user doesn't have IAM permissions, you can update the policy using the AWS Console or an admin account.

## Option 1: AWS Console (Recommended)

1. **Log in to AWS Console**:
   - Go to: https://console.aws.amazon.com/iam/
   - Sign in with an account that has IAM permissions (e.g., your root account or admin account)

2. **Navigate to Policies**:
   - Click "Policies" in the left sidebar
   - Search for: `SpendSenseUserPolicy-development`

3. **Edit Policy**:
   - Click on the policy name
   - Click "Edit policy" button
   - Click the "JSON" tab

4. **Update the Lambda Statement**:
   Find the statement with Lambda permissions and replace it with:

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
   Add this statement:

```json
{
    "Effect": "Allow",
    "Action": [
        "iam:PassRole"
    ],
    "Resource": "arn:aws:iam::971422717446:role/SpendSense*"
}
```

6. **Save Changes**:
   - Click "Review policy"
   - Click "Save changes"

## Option 2: Use Admin Account via CLI

If you have access to an admin account (e.g., `MessagAI_AlexHo`), you can temporarily switch:

```bash
# Switch to admin profile
aws configure --profile admin

# Or use environment variables
export AWS_ACCESS_KEY_ID=<admin-access-key>
export AWS_SECRET_ACCESS_KEY=<admin-secret-key>

# Then run the update script
python aws/scripts/update_iam_policy.py
```

## Option 3: Create Policy Document File

Create a file `updated-policy.json` with the full policy document (from `aws/scripts/update_iam_policy.py`), then use AWS CLI with admin credentials:

```bash
aws iam create-policy-version \
  --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development \
  --policy-document file://updated-policy.json \
  --set-as-default \
  --profile admin
```

## Verify Update

After updating, verify the policy:

```bash
aws iam get-policy-version \
  --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development \
  --version-id v2
```

## Test Lambda Deployment

Once permissions are updated, test Lambda deployment:

```bash
python aws/scripts/deploy_lambda.py weekly_recap
```

