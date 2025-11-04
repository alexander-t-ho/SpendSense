# Quick IAM Policy Update via CLI

## Method 1: Using Environment Variables (Recommended)

```bash
# Set your admin credentials (replace with your admin account credentials)
export AWS_ACCESS_KEY_ID=<your-admin-access-key>
export AWS_SECRET_ACCESS_KEY=<your-admin-secret-key>

# Run the update script
./aws/scripts/update_iam_with_admin.sh
```

## Method 2: Direct AWS CLI Commands

If you prefer to run commands directly:

```bash
# 1. Set admin credentials
export AWS_ACCESS_KEY_ID=<your-admin-access-key>
export AWS_SECRET_ACCESS_KEY=<your-admin-secret-key>

# 2. Create policy document file
cat > /tmp/policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::spendsense-*", "arn:aws:s3:::spendsense-*/*"]
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:DeleteItem"],
      "Resource": ["arn:aws:dynamodb:us-east-1:*:table/spendsense-*"]
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
      "Resource": ["arn:aws:lambda:us-east-1:*:function:spendsense-*"]
    },
    {
      "Effect": "Allow",
      "Action": ["apigateway:GET", "apigateway:POST", "apigateway:PUT", "apigateway:DELETE", "apigateway:PATCH"],
      "Resource": ["arn:aws:apigateway:us-east-1::/restapis/*"]
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogGroups", "logs:DescribeLogStreams", "logs:GetLogEvents"],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": ["sts:GetCallerIdentity"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["iam:PassRole"],
      "Resource": "arn:aws:iam::971422717446:role/SpendSense*"
    }
  ]
}
EOF

# 3. Update the policy
aws iam create-policy-version \
    --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development \
    --policy-document file:///tmp/policy.json \
    --set-as-default

# 4. Verify
aws iam get-policy --policy-arn arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development

# 5. Clean up
rm /tmp/policy.json

# 6. Switch back to SpendSense credentials
aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID
aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY
# (Replace with your actual credentials - do not commit secrets to git!)
```

## Method 3: Interactive Script

```bash
# Run the interactive script
./aws/scripts/update_iam_with_admin.sh

# It will prompt you for:
# - AWS Access Key ID
# - AWS Secret Access Key
```

## Where to Get Admin Credentials

1. **Root Account**: Your AWS root account has full permissions
2. **IAM Admin User**: Any IAM user with `IAMFullAccess` or `AdministratorAccess` policy
3. **Your MessagAI_AlexHo account**: If it has IAM permissions

## After Update

Once the policy is updated, switch back to SpendSense credentials and deploy:

```bash
# Verify current user
aws sts get-caller-identity

# Deploy Lambda functions
python aws/scripts/deploy_lambda.py weekly_recap

# Update API Gateway
python aws/scripts/update_lambda_integrations.py
```

