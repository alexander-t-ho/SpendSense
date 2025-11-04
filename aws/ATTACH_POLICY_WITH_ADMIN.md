# Attach Policy to User - Using Admin Credentials

## Problem
The `SpendSense_AlexHo` user doesn't have IAM permissions to attach policies. You need to use **admin credentials** (root account or admin user).

## Solution

### Option 1: Use Admin Credentials with Script

```bash
# Set admin credentials as environment variables
export AWS_ACCESS_KEY_ID=<your-admin-access-key>
export AWS_SECRET_ACCESS_KEY=<your-admin-secret-key>

# Run the attach script
./aws/scripts/attach_policy_to_user.sh
```

### Option 2: Direct AWS CLI Command with Admin Credentials

```bash
# Set admin credentials
export AWS_ACCESS_KEY_ID=<admin-access-key>
export AWS_SECRET_ACCESS_KEY=<admin-secret-key>

# Attach the policy
aws iam attach-user-policy \
    --user-name SpendSense_AlexHo \
    --policy-arn arn:aws:iam::971422717446:policy/AlexHoSpendSenseUserPolicy-development
```

### Option 3: Use AWS Console (Easiest)

1. Go to: https://console.aws.amazon.com/iam/
2. Sign in with **root account** or **admin account**
3. Click **"Users"** → Find `SpendSense_AlexHo`
4. Click on the user name
5. Click **"Add permissions"** → **"Attach policies directly"**
6. Search for: `AlexHoSpendSenseUserPolicy-development`
7. Check the box → Click **"Add permissions"**

## Verify After Attaching

After attaching with admin credentials, switch back to SpendSense credentials and verify:

```bash
# Switch back to SpendSense credentials
aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID
aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY
# (Replace with your actual credentials - do not commit secrets to git!)

# Verify (this should work now - the user can see their own policies)
aws iam list-attached-user-policies --user-name SpendSense_AlexHo
```

## Important Notes

- **SpendSense_AlexHo user cannot attach policies** - this is a security best practice
- **Use admin credentials** to attach the policy
- **After attaching**, the user will have the permissions defined in the policy
- **The user can see their own policies** after the policy is attached (but cannot modify them)

## Troubleshooting

If you get "Access Denied" errors:
1. Make sure you're using **admin credentials** (root account or admin user)
2. Verify the policy exists: `aws iam get-policy --policy-arn arn:aws:iam::971422717446:policy/AlexHoSpendSenseUserPolicy-development`
3. Verify the user exists: `aws iam get-user --user-name SpendSense_AlexHo`

