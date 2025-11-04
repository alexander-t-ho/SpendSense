"""Main entry point for data ingestion."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.generator import SyntheticDataGenerator
from ingest.loader import DataLoader


def main():
    """Generate and load synthetic data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and load synthetic Plaid-style data")
    parser.add_argument("--num-users", type=int, default=5, help="Number of users (default 5)")
    parser.add_argument("--generate-only", action="store_true", help="Only generate CSV files")
    parser.add_argument("--load-only", action="store_true", help="Only load from CSV files")
    parser.add_argument("--data-dir", type=str, default="data/synthetic", help="Data directory")
    parser.add_argument("--db-path", type=str, default="data/spendsense.db", help="Database path")
    parser.add_argument("--use-csv", action="store_true", help="Use transactions_final.csv as source for transaction data")
    parser.add_argument("--csv-path", type=str, default="data/transactions_final.csv", help="Path to transactions_final.csv")
    parser.add_argument("--use-synthetic-data-lib", action="store_true", help="Use synthetic-data library integration (removes lat/lng and fraud)")
    parser.add_argument("--clear-db", action="store_true", help="Clear existing database data before loading")
    
    args = parser.parse_args()
    
    if not args.load_only:
        # Generate data
        if args.use_csv:
            print("Generating synthetic data from transactions_final.csv...")
        elif args.use_synthetic_data_lib:
            print("Generating synthetic data using synthetic-data library integration...")
        else:
            print("Generating synthetic data...")
        generator = SyntheticDataGenerator(
            num_users=args.num_users,
            use_csv_source=args.use_csv,
            csv_path=args.csv_path,
            use_synthetic_data_lib=args.use_synthetic_data_lib
        )
        generator.generate_all()
        generator.save_to_csv(args.data_dir)
    
    if not args.generate_only:
        # Load data
        print("\nLoading data into database...")
        loader = DataLoader(db_path=args.db_path)
        loader.load_from_csv(args.data_dir, clear_existing=args.clear_db)
        loader.close()
        print("Done!")


if __name__ == "__main__":
    main()

