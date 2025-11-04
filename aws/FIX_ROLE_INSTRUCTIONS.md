# Fix Lambda Role Trust Policy - Instructions

## Current Issue
The role `AlexHoSpendSenseLambdaRole-dev` either doesn't exist or doesn't have the correct trust policy to allow Lambda to assume it.

## Solution
You need **admin credentials** to create/update the role. Choose one of these methods:

### Method 1: Set Admin Credentials as Environment Variables

```bash
# Set admin credentials
export AWS_ACCESS_KEY_ID=<your-admin-access-key>
export AWS_SECRET_ACCESS_KEY=<your-admin-secret-key>

# Run the fix script
cd /Users/alexho/SpendSense
./aws/scripts/fix_role_trust_policy.sh
```

### Method 2: Use Admin AWS Profile

If you have an admin profile configured:

```bash
# Set the admin profile
export AWS_PROFILE=<your-admin-profile-name>
export AWS_DEFAULT_PROFILE=<your-admin-profile-name>

# Run the fix script
cd /Users/alexho/SpendSense
./aws/scripts/fix_role_trust_policy.sh
```

### Method 3: Interactive Prompt

The script will prompt you for credentials if they're not set:

```bash
cd /Users/alexho/SpendSense
./aws/scripts/create_lambda_role.sh
```

## What the Script Does

1. **Checks if role exists** - If not, creates it
2. **Updates trust policy** - Sets it to allow Lambda service to assume the role
3. **Attaches policies**:
   - `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
   - `AlexHoSpendSenseLambdaPolicy-dev` (for S3 and DynamoDB access)

## After Fixing the Role

Once the role is fixed, you can deploy Lambda functions:

```bash
python aws/scripts/deploy_lambda.py all
```

## Verification

After running the fix script, you should see:
- ✅ Role exists and trust policy updated
- ✅ Policies attached
- Ready for Lambda deployment

## Troubleshooting

### "AccessDenied" Error
- Make sure you're using admin credentials
- Verify the credentials have IAM permissions

### "Role already exists" but still can't deploy
- The trust policy might not have been updated correctly
- Run the fix script again to update the trust policy

