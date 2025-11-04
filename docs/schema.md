# Database Schema Documentation

## Overview

SpendSense uses SQLite for relational data storage. The schema is designed to match Plaid's data structure while supporting our application's needs.

## Tables

### users
Stores user information.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Unique user identifier |
| name | String | User's name |
| email | String (UNIQUE) | User's email address |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |

### accounts
Stores financial accounts matching Plaid structure.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Internal account ID |
| user_id | String (FK) | Reference to users.id |
| account_id | String (UNIQUE) | Plaid account ID |
| name | String | Account name |
| type | String | Account type (depository, credit, loan) |
| subtype | String | Account subtype (checking, savings, credit_card, etc.) |
| iso_currency_code | String | Currency code (default: USD) |
| available | Float | Available balance |
| current | Float | Current balance |
| limit | Float | Credit limit (for credit cards) |
| holder_category | String | Account holder type (individual, business) |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |

### transactions
Stores transaction data matching Plaid structure.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Internal transaction ID |
| account_id | String (FK) | Reference to accounts.id |
| transaction_id | String (UNIQUE) | Plaid transaction ID |
| date | DateTime | Transaction date |
| amount | Float | Transaction amount (negative for expenses) |
| merchant_name | String | Merchant name |
| merchant_entity_id | String | Merchant entity ID |
| payment_channel | String | Payment channel (in store, online, other) |
| primary_category | String | Primary personal finance category |
| detailed_category | String | Detailed category |
| pending | Boolean | Whether transaction is pending |
| created_at | DateTime | Record creation timestamp |

### liabilities
Stores liability information for credit cards, mortgages, and loans.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Internal liability ID |
| account_id | String (FK) | Reference to accounts.id |
| apr_type | String | APR type (variable, fixed) |
| apr_percentage | Float | Annual percentage rate |
| minimum_payment_amount | Float | Minimum payment required |
| last_payment_amount | Float | Last payment amount |
| last_payment_date | DateTime | Last payment date |
| is_overdue | Boolean | Whether payment is overdue |
| next_payment_due_date | DateTime | Next payment due date |
| last_statement_balance | Float | Last statement balance |
| interest_rate | Float | Interest rate (for mortgages/loans) |
| liability_type | String | Type (credit_card, mortgage, student_loan) |
| created_at | DateTime | Record creation timestamp |
| updated_at | DateTime | Last update timestamp |

### consents
Tracks user consent for data processing.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Consent record ID |
| user_id | String (FK, UNIQUE) | Reference to users.id |
| consented | Boolean | Whether user has consented |
| consented_at | DateTime | Consent timestamp |
| revoked_at | DateTime | Revocation timestamp |
| created_at | DateTime | Record creation timestamp |
| updated_at | DateTime | Last update timestamp |

### recommendations
Stores generated recommendations for users.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Recommendation ID |
| user_id | String (FK) | Reference to users.id |
| recommendation_type | String | Type (education, partner_offer) |
| title | String | Recommendation title |
| description | Text | Recommendation description |
| rationale | Text | Plain-language rationale |
| content_id | String | Reference to content catalog |
| persona_id | String | Persona that triggered this |
| approved | Boolean | Operator approval status |
| approved_at | DateTime | Approval timestamp |
| flagged | Boolean | Whether flagged for review |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Relationships

- User → Accounts (one-to-many)
- User → Consent (one-to-one)
- User → Recommendations (one-to-many)
- Account → Transactions (one-to-many)
- Account → Liabilities (one-to-many)

## Indexes

Recommended indexes for performance:
- `accounts.user_id` (for user account lookups)
- `transactions.account_id` (for transaction queries)
- `transactions.date` (for time-window queries)
- `consents.user_id` (for consent checks)

## Notes

- All monetary values are stored as Float (consider Decimal for production)
- Timestamps use SQLite's datetime format
- Foreign keys are enforced at application level (SQLite FK support is optional)
- Account IDs use Plaid's format externally, internal IDs for foreign keys

