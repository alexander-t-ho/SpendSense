# Attach Policy to User via CLI

## Quick Command

```bash
aws iam attach-user-policy \
    --user-name SpendSense_AlexHo \
    --policy-arn arn:aws:iam::971422717446:policy/AlexHoSpendSenseUserPolicy-development
```

## Using the Script

```bash
./aws/scripts/attach_policy_to_user.sh
```

The script will prompt for admin credentials and attach the policy.

## With Environment Variables

```bash
export AWS_ACCESS_KEY_ID=<admin-access-key>
export AWS_SECRET_ACCESS_KEY=<admin-secret-key>
./aws/scripts/attach_policy_to_user.sh
```

## Verify Attachment

```bash
aws iam list-attached-user-policies --user-name SpendSense_AlexHo
```

## Output Example

You should see:
```
POLICYARN                                                          POLICYNAME
arn:aws:iam::971422717446:policy/AlexHoSpendSenseUserPolicy-development    AlexHoSpendSenseUserPolicy-development
```

