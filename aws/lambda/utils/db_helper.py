"""Database helper for Lambda functions - downloads database from S3 if needed."""

import os
import boto3
import sqlite3
from pathlib import Path
from typing import Optional

# Cache for database path
_db_path_cache: Optional[str] = None

def get_database_path() -> str:
    """Get database path, downloading from S3 if necessary.
    
    Returns:
        Path to the database file
    """
    global _db_path_cache
    
    # Use cached path if available (warm start)
    if _db_path_cache and Path(_db_path_cache).exists():
        return _db_path_cache
    
    # Get paths from environment
    db_path = os.environ.get('DB_PATH', '/tmp/spendsense.db')
    s3_bucket = os.environ.get('S3_BUCKET_HISTORICAL', '')
    s3_key = os.environ.get('DB_S3_KEY', 'database/spendsense.db')
    
    db_file = Path(db_path)
    
    # If no S3 bucket configured, skip download
    if not s3_bucket:
        if db_file.exists():
            return db_path
        raise FileNotFoundError(f"Database not found at {db_path} and S3_BUCKET_HISTORICAL not configured")
    
    # If database doesn't exist, download from S3
    if not db_file.exists() and s3_bucket:
        try:
            print(f"Downloading database from s3://{s3_bucket}/{s3_key}...")
            
            # Ensure directory exists
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Download from S3
            s3_client = boto3.client('s3')
            s3_client.download_file(s3_bucket, s3_key, str(db_file))
            
            print(f"✅ Database downloaded to {db_path}")
            
        except Exception as e:
            print(f"⚠️  Could not download database from S3: {e}")
            print(f"   Database must exist at {db_path} or be uploaded to S3")
            raise
    
    # Verify database exists and is valid
    if not db_file.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. "
            f"Upload to S3: s3://{s3_bucket}/{s3_key}"
        )
    
    # Verify it's a valid SQLite database
    try:
        conn = sqlite3.connect(str(db_file))
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        raise ValueError(f"Invalid database file at {db_path}: {e}")
    
    # Cache the path
    _db_path_cache = db_path
    
    return db_path

