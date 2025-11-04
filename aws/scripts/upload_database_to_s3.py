#!/usr/bin/env python3
"""Upload SQLite database to S3 for Lambda functions to access."""

import boto3
import json
from pathlib import Path

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"
with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

s3_bucket = resources['s3_buckets']['historical']  # Use historical bucket for database
db_path = Path(__file__).parent.parent.parent / "data" / "spendsense.db"

session = boto3.Session(profile_name='default', region_name=resources['region'])
s3_client = session.client('s3')

def upload_database():
    """Upload database to S3."""
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return False
    
    s3_key = "database/spendsense.db"
    
    print("=" * 60)
    print("Uploading Database to S3")
    print("=" * 60)
    print(f"Local path: {db_path}")
    print(f"S3 bucket: {s3_bucket}")
    print(f"S3 key: {s3_key}")
    print("=" * 60)
    print()
    
    try:
        file_size = db_path.stat().st_size
        print(f"Uploading {file_size / 1024 / 1024:.2f} MB...")
        
        s3_client.upload_file(
            str(db_path),
            s3_bucket,
            s3_key,
            ExtraArgs={'ContentType': 'application/x-sqlite3'}
        )
        
        print(f"✅ Database uploaded successfully!")
        print()
        print(f"S3 Location: s3://{s3_bucket}/{s3_key}")
        print()
        print("Next steps:")
        print("  1. Update Lambda handlers to download from S3")
        print("  2. Redeploy Lambda functions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading database: {e}")
        return False

if __name__ == "__main__":
    upload_database()
