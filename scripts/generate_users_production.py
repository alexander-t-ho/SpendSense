#!/usr/bin/env python3
"""Script to generate users in production via CLI.
This can be run directly on Railway using: railway run python scripts/generate_users_production.py --num-users 150
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from ingest.generator import SyntheticDataGenerator
from ingest.loader import DataLoader
from ingest.schema import get_session, User, func
from api.main import get_password_hash, get_db_path


def main():
    parser = argparse.ArgumentParser(description="Generate users in production")
    parser.add_argument("--num-users", type=int, default=150, help="Number of users to generate (default 150)")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for generation (default 10)")
    
    args = parser.parse_args()
    
    db_path = get_db_path()
    print(f"Using database: {db_path}")
    
    total_users_to_generate = args.num_users
    batch_size = args.batch_size
    
    print(f"Generating {total_users_to_generate} users in batches of {batch_size}...")
    
    total_created = 0
    batches = (total_users_to_generate + batch_size - 1) // batch_size  # Ceiling division
    
    for batch_num in range(batches):
        remaining = total_users_to_generate - total_created
        current_batch_size = min(batch_size, remaining)
        
        print(f"\n--- Batch {batch_num + 1}/{batches}: Generating {current_batch_size} users ---")
        
        try:
            # Generate users
            print(f"Generating {current_batch_size} users...")
            generator = SyntheticDataGenerator(num_users=current_batch_size)
            data = generator.generate_all()
            
            # Load into database
            print(f"Loading {current_batch_size} users into database...")
            loader = DataLoader(db_path=db_path)
            
            import pandas as pd
            
            users_df = pd.DataFrame(data.get("users", []))
            accounts_df = pd.DataFrame(data.get("accounts", []))
            transactions_df = pd.DataFrame(data.get("transactions", []))
            liabilities_df = pd.DataFrame(data.get("liabilities", []))
            
            # Load users
            if not users_df.empty:
                loader.load_users(users_df)
                print(f"  ✓ Loaded {len(users_df)} users")
            
            # Load accounts
            if not accounts_df.empty:
                loader.load_accounts(accounts_df)
                print(f"  ✓ Loaded {len(accounts_df)} accounts")
            
            # Load transactions
            if not transactions_df.empty:
                loader.load_transactions(transactions_df)
                print(f"  ✓ Loaded {len(transactions_df)} transactions")
            
            # Load liabilities
            if not liabilities_df.empty:
                loader.load_liabilities(liabilities_df)
                print(f"  ✓ Loaded {len(liabilities_df)} liabilities")
            
            loader.close()
            
            # Set passwords for newly created users
            session = get_session(db_path)
            try:
                password_hash = get_password_hash("123456")
                new_users = session.query(User).filter(User.password_hash == None).all()
                updated_count = 0
                for user in new_users:
                    if not user.username:
                        user.username = user.email
                    user.password_hash = password_hash
                    updated_count += 1
                session.commit()
                print(f"  ✓ Set passwords for {updated_count} users")
            finally:
                session.close()
            
            total_created += current_batch_size
            
            # Check total users in database
            session = get_session(db_path)
            try:
                total_users = session.query(func.count(User.id)).scalar()
                print(f"  ✓ Total users in database: {total_users}")
            finally:
                session.close()
            
            print(f"Batch {batch_num + 1} completed successfully!")
            
        except Exception as e:
            import traceback
            print(f"ERROR in batch {batch_num + 1}: {str(e)}")
            print(traceback.format_exc())
            break
    
    print(f"\n=== Generation Complete ===")
    print(f"Total users generated: {total_created}/{total_users_to_generate}")
    
    # Final count
    session = get_session(db_path)
    try:
        total_users = session.query(func.count(User.id)).scalar()
        print(f"Total users in database: {total_users}")
    finally:
        session.close()


if __name__ == "__main__":
    main()

