"""Utility functions for API."""

import os
from ingest.schema import get_session, init_db


def get_db_path():
    """Get database path from environment or use default."""
    db_path = os.environ.get("DATABASE_URL", "data/spendsense.db")
    # If DATABASE_URL is a full URL (like postgres://), extract path or use as-is
    # For SQLite, we need just the path
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    elif db_path.startswith("postgres://") or db_path.startswith("postgresql://"):
        # For PostgreSQL, we'd need different handling, but for now assume SQLite
        db_path = "data/spendsense.db"
    
    # Ensure database directory exists
    from pathlib import Path
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize database if it doesn't exist
    init_db(db_path)
    
    return db_path

