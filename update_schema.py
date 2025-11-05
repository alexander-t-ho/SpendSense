"""Update database schema to add new columns to recommendations table."""

import sqlite3
from pathlib import Path

def update_recommendations_schema(db_path: str = "data/spendsense.db"):
    """Add new columns to recommendations table if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(recommendations)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    # Columns to add
    new_columns = [
        ("action_items", "JSON"),
        ("expected_impact", "TEXT"),
        ("priority", "TEXT"),
        ("approved_by", "TEXT"),
        ("rejected", "BOOLEAN DEFAULT 0"),
        ("rejected_at", "DATETIME"),
        ("rejected_by", "TEXT"),
    ]
    
    added_count = 0
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE recommendations ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
                added_count += 1
            except sqlite3.OperationalError as e:
                print(f"⚠️  Error adding column {column_name}: {e}")
    
    conn.commit()
    conn.close()
    
    if added_count == 0:
        print("✅ All columns already exist in recommendations table")
    else:
        print(f"✅ Added {added_count} new column(s) to recommendations table")

if __name__ == "__main__":
    db_path = Path("data/spendsense.db")
    if not db_path.exists():
        print(f"⚠️  Database not found at {db_path}")
        print("   The database will be created when you start the backend server")
    else:
        print(f"Updating schema for {db_path}...")
        update_recommendations_schema(str(db_path))
        print("Done!")

