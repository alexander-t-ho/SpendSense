#!/usr/bin/env python3
"""Migration script to add authentication columns to users table."""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str = "data/spendsense.db"):
    """Add authentication columns to users table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add columns one by one (SQLite doesn't support UNIQUE in ALTER TABLE)
        if 'username' not in columns:
            print("Adding username column...")
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
            print("✓ Added username column")
            # Create unique index separately
            try:
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)")
                print("✓ Created unique index on username")
            except:
                pass  # Index might already exist
        else:
            print("✓ username column already exists")
        
        if 'password_hash' not in columns:
            print("Adding password_hash column...")
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            print("✓ Added password_hash column")
        else:
            print("✓ password_hash column already exists")
        
        if 'is_admin' not in columns:
            print("Adding is_admin column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            # Update existing rows to have is_admin = 0
            cursor.execute("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")
            print("✓ Added is_admin column")
        else:
            print("✓ is_admin column already exists")
        
        conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database to add auth columns")
    parser.add_argument("--db-path", type=str, default="data/spendsense.db", help="Database path")
    
    args = parser.parse_args()
    migrate_database(args.db_path)

