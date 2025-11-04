# Rename IAM Policy to AlexHo Prefix

## Current Policy Name
`SpendSenseUserPolicy-development`

## New Policy Name
`AlexHoSpendSenseUserPolicy-development`

## Option 1: Create New Policy (Recommended)

Since IAM policies cannot be renamed, create a new policy with the AlexHo prefix:

### Steps in AWS Console:

1. **Go to IAM Console**: https://console.aws.amazon.com/iam/
2. **Click "Policies"** → Click **"Create policy"**
3. **Click "JSON" tab**
4. **Copy the policy JSON** from `aws/POLICY_JSON_UPDATED.json`
5. **Paste it into the JSON editor**
6. **Click "Next"**
7. **Name the policy**: `AlexHoSpendSenseUserPolicy-development`
8. **Description**: "IAM policy for AlexHo's SpendSense project - scoped to account 971422717446"
9. **Click "Create policy"**
10. **Attach to user**:
    - Go to "Users" → Find `SpendSense_AlexHo`
    - Click "Add permissions" → "Attach policies directly"
    - Search for `AlexHoSpendSenseUserPolicy-development`
    - Check the box → Click "Add permissions"
11. **Remove old policy** (optional):
    - Go to user → "Permissions" tab
    - Find `SpendSenseUserPolicy-development`
    - Click "Detach" → Confirm

## Option 2: Keep Existing Policy (Temporary)

If you want to keep using the existing policy temporarily:

1. **Update the policy JSON** in AWS Console (use `POLICY_JSON_UPDATED.json`)
2. **The policy will still work** with the old name
3. **Later, create the new policy** with AlexHo prefix and migrate

## Policy ARN

- **Old**: `arn:aws:iam::971422717446:policy/SpendSenseUserPolicy-development`
- **New**: `arn:aws:iam::971422717446:policy/AlexHoSpendSenseUserPolicy-development`

## Updated Configuration

All configuration files have been updated to use:
- Policy Name: `AlexHoSpendSenseUserPolicy-development`
- IAM Role: `AlexHoSpendSenseLambdaRole-dev`

## After Creating New Policy

1. **Attach to user**: `SpendSense_AlexHo`
2. **Test the policy**:
   ```bash
   aws iam list-attached-user-policies --user-name SpendSense_AlexHo
   ```
3. **Verify Lambda permissions**:
   ```bash
   python aws/scripts/deploy_lambda.py weekly_recap
   ```

## Important Notes

- **IAM policies cannot be renamed** - you must create a new one
- **Old policy can be kept** for backward compatibility during migration
- **Resources using old policy** will continue to work
- **New resources** should use the AlexHo-prefixed policy

