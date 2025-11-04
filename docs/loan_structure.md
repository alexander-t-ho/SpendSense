# Loan Account Structure

## Overview

The SpendSense system supports users having multiple loan types (mortgage and/or student loans). Each loan type is stored as a separate Account record with its own `interest_rate` and `next_payment_due_date` fields.

## Structure

### Account Model Fields

For loan accounts (type="loan", subtype="mortgage" or "student_loan"), the following fields are populated:

- `interest_rate` (Float): Interest rate for the loan
  - Mortgages: Typically 3.0% - 7.5%
  - Student Loans: Typically 3.5% - 8.5%
- `next_payment_due_date` (DateTime): Next payment due date

For non-loan accounts (checking, savings, credit cards), these fields are `None`.

### Multiple Loans

Users can have:
- **Neither loan** (most common - ~45% of users)
- **Mortgage only** (~24% of users)
- **Student loan only** (~20% of users)  
- **Both mortgage and student loan** (~11% of users)

When a user has both, they will have:
- One Account record with `subtype="mortgage"` and its own `interest_rate` and `next_payment_due_date`
- One Account record with `subtype="student_loan"` and its own `interest_rate` and `next_payment_due_date`

## Accessing Loan Information

### Method 1: Direct Account Access

```python
# Get all accounts for a user
user = session.query(User).filter(User.id == user_id).first()

# Access mortgage account
mortgage_account = next((acc for acc in user.accounts if acc.subtype == "mortgage"), None)
if mortgage_account:
    mortgage_rate = mortgage_account.interest_rate
    mortgage_due_date = mortgage_account.next_payment_due_date

# Access student loan account
student_loan_account = next((acc for acc in user.accounts if acc.subtype == "student_loan"), None)
if student_loan_account:
    student_rate = student_loan_account.interest_rate
    student_due_date = student_loan_account.next_payment_due_date
```

### Method 2: Using Helper Methods

```python
# Get all loans for a user
user = session.query(User).filter(User.id == user_id).first()
loans = user.get_loan_accounts()

# Access mortgage info (if exists)
if loans['mortgage']:
    mortgage_rate = loans['mortgage']['interest_rate']
    mortgage_due_date = loans['mortgage']['next_payment_due_date']
    mortgage_balance = loans['mortgage']['balance']

# Access student loan info (if exists)
if loans['student_loan']:
    student_rate = loans['student_loan']['interest_rate']
    student_due_date = loans['student_loan']['next_payment_due_date']
    student_balance = loans['student_loan']['balance']

# Check if user has both
has_both = loans['mortgage'] is not None and loans['student_loan'] is not None
```

### Method 3: Individual Account Helper

```python
# For a specific account
account = session.query(Account).filter(Account.subtype == "mortgage").first()
loan_info = account.get_loan_info()

if loan_info:
    print(f"Loan Type: {loan_info['loan_type']}")
    print(f"Interest Rate: {loan_info['interest_rate']}%")
    print(f"Next Payment Due: {loan_info['next_payment_due_date']}")
    print(f"Balance: ${loan_info['balance']:,.2f}")
```

## Example: User with Both Loans

```python
user = session.query(User).filter(User.id == "user-123").first()
loans = user.get_loan_accounts()

# User has both mortgage and student loan
if loans['mortgage'] and loans['student_loan']:
    print("User has both mortgage and student loan:")
    print(f"  Mortgage: {loans['mortgage']['interest_rate']}% interest, due {loans['mortgage']['next_payment_due_date']}")
    print(f"  Student Loan: {loans['student_loan']['interest_rate']}% interest, due {loans['student_loan']['next_payment_due_date']}")
```

## Data Generation

The synthetic data generator creates:
- **35% of users** get a mortgage account
- **30% of users** get a student loan account
- These are independent, so ~11% get both

Each loan account receives:
- Unique `interest_rate` within realistic ranges
- Unique `next_payment_due_date` within the next 30 days
- All loan-specific fields stored in both the Account and Liability records

