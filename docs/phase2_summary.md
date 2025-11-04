# Phase 2: Behavioral Signal Detection - Summary

## Implementation Status: ✅ COMPLETE

Phase 2 is fully implemented with all behavioral signal detection modules.

## Modules Implemented

### 1. Subscription Detection (`features/subscriptions.py`)
- **Recurring merchant detection**: Identifies merchants with ≥3 occurrences in 90 days
- **Cadence detection**: Monthly (25-35 days) or weekly (6-8 days) patterns
- **Metrics calculated**:
  - Number of recurring merchants
  - Monthly recurring spend
  - Subscription share of total spend
  - Total subscription spend

### 2. Savings Analysis (`features/savings.py`)
- **Net inflow calculation**: Tracks money flowing into savings accounts
- **Growth rate**: Calculates savings growth percentage over time window
- **Emergency fund coverage**: Savings balance / average monthly expenses (in months)
- **Metrics calculated**:
  - Net inflow (total and monthly)
  - Growth rate percentage
  - Emergency fund coverage (months)
  - Total savings balance
  - Has emergency fund flag (≥3 months)

### 3. Credit Analysis (`features/credit.py`)
- **Utilization calculation**: Balance / limit for each credit card
- **Utilization flags**: ≥30%, ≥50%, ≥80% thresholds
- **Payment pattern detection**: Minimum-payment-only detection
- **Interest charges**: Detects interest/fee transactions
- **Overdue status**: Checks liability records for overdue payments
- **Metrics calculated**:
  - Has credit cards flag
  - High utilization flags (50%, 80%)
  - Interest charges present
  - Minimum payment only pattern
  - Overdue status
  - Per-card details

### 4. Income Stability (`features/income.py`)
- **Payroll ACH detection**: Identifies payroll deposits (≥$1000)
- **Payment frequency**: Weekly, biweekly, monthly, or irregular
- **Frequency variability**: Standard deviation of payment intervals
- **Cash-flow buffer**: Checking balance / average monthly expenses (in months)
- **Variable income detection**: Median pay gap > 45 days AND buffer < 1 month
- **Metrics calculated**:
  - Payroll detected flag
  - Payment frequency and regularity
  - Median pay gap (days)
  - Cash-flow buffer (months)
  - Variable income flag

### 5. Feature Pipeline (`features/pipeline.py`)
- **Orchestration**: Coordinates all feature detectors
- **Time windows**: Supports 30-day and 180-day analysis windows
- **Batch processing**: Computes features for all users
- **Parquet storage**: Saves flattened features to Parquet files for analytics
- **Error handling**: Gracefully handles errors per user

## Data Flow

1. **Input**: SQLite database with users, accounts, transactions, liabilities
2. **Processing**: Feature pipeline computes behavioral signals
3. **Output**: 
   - In-memory dictionaries with nested feature structures
   - Parquet files with flattened features for analytics

## Usage

### Compute features for all users (both windows):
```bash
python -m features.pipeline --db-path data/spendsense.db
```

### Compute features for specific window:
```bash
python -m features.pipeline --window-days 30 --db-path data/spendsense.db
python -m features.pipeline --window-days 180 --db-path data/spendsense.db
```

### Compute features for single user:
```bash
python -m features.pipeline --user-id <user_id> --window-days 30
```

## Output Files

- `data/features/features_30d.parquet` - 30-day window features
- `data/features/features_180d.parquet` - 180-day window features

## Feature Schema

Each feature record includes:
- User ID and time window metadata
- Subscription metrics (recurring merchants, spend, share)
- Savings metrics (inflow, growth, emergency fund)
- Credit metrics (utilization, interest, overdue)
- Income metrics (frequency, buffer, variability)

## Next Steps

Phase 2 is complete and ready for Phase 3: Persona Assignment System.

