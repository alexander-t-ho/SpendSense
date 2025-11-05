# Synthetic Data Integration

This document describes the integration with the external `synthetic-data` library folder.

## Overview

SpendSense supports integration with the synthetic-data library located at `/Users/alexho/synthetic-data`. This integration allows us to:

1. Use the synthetic-data library's generation methods
2. Remove sensitive fields (latitude, longitude, fraud indicators)
3. Add persona-specific markers unique to SpendSense
4. Ensure data aligns with our 5 personas

## Data Safety

All generated data:
- **No fraudulent data**: No `is_fraud` field or fraudulent transactions
- **No location data**: No `latitude` or `longitude` fields
- **Persona-specific**: Data includes markers for our 5 personas:
  - High Utilization
  - Variable Income Budgeter
  - Subscription-Heavy
  - Savings Builder
  - Balanced & Stable

## Usage

### Option 1: Use Synthetic-Data Library Integration

```bash
python -m ingest --num-users 50 --use-synthetic-data-lib --clear-db
```

This will:
- Use the synthetic-data library's generation methods
- Remove latitude, longitude, and fraud fields
- Generate persona-specific data
- Ensure even distribution of all 5 personas (10 users each for 50 users)

### Option 2: Use Standard Generation (Current Method)

```bash
python -m ingest --num-users 50 --clear-db
```

This uses the standard SpendSense generator without the synthetic-data library.

### Option 3: Use Existing CSV as Source

```bash
python -m ingest --num-users 50 --use-csv --csv-path data/transactions_final.csv --clear-db
```

This uses an existing CSV file as the source for transaction patterns.

## Integration Details

### Files

- `ingest/synthetic_data_integration.py`: Integration module that adapts synthetic-data library output to SpendSense format
- `ingest/generator.py`: Updated to support `--use-synthetic-data-lib` flag

### Data Format

The integration ensures all output matches the `transactions_final.csv` format:

```csv
transaction_id,timestamp,date,time,customer_id,merchant_id,merchant_category,
transaction_type,payment_method,amount,amount_category,status,account_balance,
account_id,hour,day_of_week,month,month_name,quarter,year
```

**Excluded Fields:**
- `latitude` - Never included
- `longitude` - Never included
- `is_fraud` - Never included

### Persona Distribution

When using the synthetic-data integration, the system ensures:
- Even distribution: 10 users per persona (for 50 users)
- Persona-specific transaction patterns
- Persona-specific account balances
- Persona-specific spending behaviors

## Requirements

If using the synthetic-data library integration:

1. The synthetic-data library must be available at `/Users/alexho/synthetic-data`
2. The library should have the following structure:
   ```
   synthetic-data/
   ├── synthetic_data/
   │   ├── __init__.py
   │   └── synthetic_data.py
   └── ...
   ```

If the library is not available, the system will fall back to standard generation.

## Notes

- The integration is optional - standard generation works without it
- All generated data is synthetic and safe for development/testing
- No real PII is included in any generated data
- Persona markers ensure realistic behavioral patterns for testing


