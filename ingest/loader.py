"""Data loader for ingesting CSV/JSON data into SQLite database."""

import pandas as pd
from datetime import datetime
from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session

from ingest.schema import (
    User, Account, Transaction, Liability, Consent,
    init_db, get_session
)


class DataLoader:
    """Load data from CSV/JSON files into database."""
    
    def __init__(self, db_path: str = "data/spendsense.db"):
        """Initialize loader.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        init_db(db_path)
        self.session = get_session(db_path)
    
    def load_users(self, users_df: pd.DataFrame):
        """Load users from DataFrame."""
        loaded_count = 0
        skipped_count = 0
        for _, row in users_df.iterrows():
            # Check if user already exists (by email or id)
            existing_user = self.session.query(User).filter(
                (User.email == row["email"]) | (User.id == row["id"])
            ).first()
            
            if existing_user:
                skipped_count += 1
                continue
            
            user = User(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                created_at=pd.to_datetime(row.get("created_at", datetime.now()))
            )
            self.session.add(user)
            loaded_count += 1
        
        self.session.commit()
        print(f"Loaded {loaded_count} new users, skipped {skipped_count} existing users")
    
    def load_from_csv(self, data_dir: str, clear_existing: bool = False):
        """Load all data from CSV files.
        
        Args:
            data_dir: Directory containing CSV files
            clear_existing: If True, clear existing data before loading
        """
        import os
        
        if clear_existing:
            print("Clearing existing data...")
            from ingest.schema import User, Account, Transaction, Liability
            self.session.query(Transaction).delete()
            self.session.query(Liability).delete()
            self.session.query(Account).delete()
            self.session.query(User).delete()
            self.session.commit()
            print("Existing data cleared.")
        
        users_path = os.path.join(data_dir, "users.csv")
        accounts_path = os.path.join(data_dir, "accounts.csv")
        transactions_path = os.path.join(data_dir, "transactions.csv")
        liabilities_path = os.path.join(data_dir, "liabilities.csv")
        
        # Load in order: users -> accounts -> transactions -> liabilities
        if os.path.exists(users_path):
            users_df = pd.read_csv(users_path)
            self.load_users(users_df)
        
        if os.path.exists(accounts_path):
            accounts_df = pd.read_csv(accounts_path)
            self.load_accounts(accounts_df)
        
        if os.path.exists(transactions_path):
            transactions_df = pd.read_csv(transactions_path)
            self.load_transactions(transactions_df)
        
        if os.path.exists(liabilities_path):
            liabilities_df = pd.read_csv(liabilities_path)
            self.load_liabilities(liabilities_df)
    
    def load_accounts(self, accounts_df: pd.DataFrame):
        """Load accounts from DataFrame."""
        loaded_count = 0
        skipped_count = 0
        for _, row in accounts_df.iterrows():
            # Check if account already exists
            existing_account = self.session.query(Account).filter(
                (Account.id == row["id"]) | (Account.account_id == row["account_id"])
            ).first()
            
            if existing_account:
                skipped_count += 1
                continue
            
            # Helper to handle None/NaN values
            def safe_get(key, default=None):
                val = row.get(key, default)
                return None if pd.isna(val) or val == '' else val
            
            def safe_float(key):
                val = safe_get(key)
                return float(val) if val is not None else None
            
            account = Account(
                    id=row["id"],
                    user_id=row["user_id"],
                    account_id=row["account_id"],
                    name=row["name"],
                    type=row["type"],
                    subtype=row.get("subtype"),
                    iso_currency_code=row.get("iso_currency_code", "USD"),
                    available=safe_float("available"),
                    current=safe_float("current"),
                    limit=safe_float("limit"),
                    amount_due=safe_float("amount_due"),  # Credit card field
                    minimum_payment_due=safe_float("minimum_payment_due"),  # Credit card field
                    interest_rate=safe_float("interest_rate"),  # Loan-specific field
                    next_payment_due_date=pd.to_datetime(row["next_payment_due_date"]) if pd.notna(row.get("next_payment_due_date")) else None,  # Loan-specific field
                    holder_category=row.get("holder_category", "individual"),
                    created_at=pd.to_datetime(row.get("created_at", datetime.now()))
                )
            self.session.add(account)
            loaded_count += 1
        
        self.session.commit()
        print(f"Loaded {loaded_count} new accounts, skipped {skipped_count} existing accounts")
    
    def load_transactions(self, transactions_df: pd.DataFrame):
        """Load transactions from DataFrame."""
        loaded_count = 0
        skipped_count = 0
        for _, row in transactions_df.iterrows():
            # Check if transaction already exists
            existing_transaction = self.session.query(Transaction).filter(
                (Transaction.id == row["id"]) | (Transaction.transaction_id == row["transaction_id"])
            ).first()
            
            if existing_transaction:
                skipped_count += 1
                continue
            
            # Get account_id from account_id column (which should map to Account.account_id)
            account_id = row["account_id"]
            
            # Find the Account record by account_id
            account = self.session.query(Account).filter(
                Account.account_id == account_id
            ).first()
            
            if not account:
                print(f"Warning: Account {account_id} not found for transaction {row['transaction_id']}")
                skipped_count += 1
                continue
            
            transaction = Transaction(
                id=row["id"],
                account_id=account.id,  # Use internal ID, not account_id
                transaction_id=row["transaction_id"],
                date=pd.to_datetime(row["date"]),
                amount=float(row["amount"]),
                merchant_name=row.get("merchant_name"),
                merchant_entity_id=row.get("merchant_entity_id"),
                payment_channel=row.get("payment_channel"),
                primary_category=row.get("primary_category"),
                detailed_category=row.get("detailed_category"),
                pending=bool(row.get("pending", False)),
                created_at=pd.to_datetime(row.get("created_at", datetime.now()))
            )
            self.session.add(transaction)
            loaded_count += 1
        
        self.session.commit()
        print(f"Loaded {loaded_count} new transactions, skipped {skipped_count} existing transactions")
    
    def load_liabilities(self, liabilities_df: pd.DataFrame):
        """Load liabilities from DataFrame."""
        for _, row in liabilities_df.iterrows():
            # Find account by account_id
            account = self.session.query(Account).filter(
                Account.account_id == row["account_id"]
            ).first()
            
            if not account:
                print(f"Warning: Account {row['account_id']} not found for liability")
                continue
            
            # Helper to handle None/NaN values
            def safe_get(key, default=None):
                val = row.get(key, default)
                return None if pd.isna(val) or val == '' else val
            
            def safe_float(key):
                val = safe_get(key)
                return float(val) if val is not None else None
            
            liability = Liability(
                id=row["id"],
                account_id=account.id,
                apr_type=safe_get("apr_type"),
                apr_percentage=safe_float("apr_percentage"),
                minimum_payment_amount=safe_float("minimum_payment_amount"),
                last_payment_amount=safe_float("last_payment_amount"),
                last_payment_date=pd.to_datetime(row["last_payment_date"]) if pd.notna(row.get("last_payment_date")) else None,
                is_overdue=bool(row.get("is_overdue", False)) if pd.notna(row.get("is_overdue")) else False,
                next_payment_due_date=pd.to_datetime(row["next_payment_due_date"]) if pd.notna(row.get("next_payment_due_date")) else None,
                last_statement_balance=safe_float("last_statement_balance"),
                interest_rate=safe_float("interest_rate"),
                liability_type=row.get("liability_type"),
                created_at=pd.to_datetime(row.get("created_at", datetime.now()))
            )
            self.session.add(liability)
        
        self.session.commit()
        print(f"Loaded {len(liabilities_df)} liabilities")
    
    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load data from CSV into SQLite database")
    parser.add_argument("--data-dir", type=str, default="data/synthetic", help="Directory containing CSV files")
    parser.add_argument("--db-path", type=str, default="data/spendsense.db", help="Path to SQLite database")
    
    args = parser.parse_args()
    
    loader = DataLoader(db_path=args.db_path)
    loader.load_from_csv(args.data_dir)
    loader.close()

