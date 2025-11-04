#!/usr/bin/env python3
"""Upload Parquet files to S3.

This script uploads existing Parquet feature files to the S3 bucket.

Usage:
    python aws/scripts/upload_parquet_to_s3.py
"""

import boto3
import json
from pathlib import Path

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

region = resources['region']
bucket_name = resources['s3_buckets']['parquet_data']

session = boto3.Session(profile_name='default', region_name=region)
s3_client = session.client('s3')

# Local Parquet files directory
LOCAL_PARQUET_DIR = Path(__file__).parent.parent.parent / "data" / "features"


def upload_parquet_files():
    """Upload Parquet files to S3."""
    print("=" * 60)
    print("Uploading Parquet Files to S3")
    print("=" * 60)
    print(f"Bucket: {bucket_name}")
    print(f"Local directory: {LOCAL_PARQUET_DIR}")
    print("=" * 60)
    print()
    
    if not LOCAL_PARQUET_DIR.exists():
        print(f"⚠️  Local Parquet directory not found: {LOCAL_PARQUET_DIR}")
        print("   Run feature computation first to generate Parquet files.")
        return
    
    parquet_files = list(LOCAL_PARQUET_DIR.glob("*.parquet"))
    
    if not parquet_files:
        print("⚠️  No Parquet files found in data/features/")
        print("   Run feature computation first:")
        print("   python -m features.pipeline --window-days 30")
        print("   python -m features.pipeline --window-days 180")
        return
    
    print(f"Found {len(parquet_files)} Parquet file(s):\n")
    
    for parquet_file in parquet_files:
        s3_key = f"features/{parquet_file.name}"
        
        try:
            print(f"Uploading {parquet_file.name}...")
            s3_client.upload_file(
                str(parquet_file),
                bucket_name,
                s3_key
            )
            print(f"  ✅ Uploaded to s3://{bucket_name}/{s3_key}")
            
        except Exception as e:
            print(f"  ❌ Error uploading {parquet_file.name}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Upload Complete!")
    print("=" * 60)


if __name__ == "__main__":
    upload_parquet_files()

