#!/usr/bin/env python3
"""Update all Lambda handlers to use database helper utility."""

import re
from pathlib import Path

HANDLER_FILES = [
    "aws/lambda/spending_analysis/handler.py",
    "aws/lambda/net_worth/handler.py",
    "aws/lambda/budget_suggestion/handler.py",
    "aws/lambda/budget_tracking/handler.py",
]

REPLACEMENT_CODE = """        # Get database path (downloads from S3 if needed)
        try:
            from utils.db_helper import get_database_path
            db_path = get_database_path()
        except ImportError:
            # Fallback if utils not available
            db_path = os.environ.get('DB_PATH', '/tmp/spendsense.db')"""

PATTERN = r"# Get database path from environment\s+db_path = os\.environ\.get\('DB_PATH', '/tmp/spendsense\.db'\)"

def fix_handler(file_path: Path):
    """Fix a single handler file."""
    content = file_path.read_text()
    
    # Check if already updated
    if "from utils.db_helper import get_database_path" in content:
        print(f"  ✅ {file_path.name} already updated")
        return True
    
    # Replace the pattern
    new_content = re.sub(PATTERN, REPLACEMENT_CODE, content)
    
    if new_content != content:
        file_path.write_text(new_content)
        print(f"  ✅ Updated {file_path.name}")
        return True
    else:
        print(f"  ⚠️  No changes needed in {file_path.name}")
        return False

def main():
    """Update all handlers."""
    print("=" * 60)
    print("Updating Lambda Handlers for Database Access")
    print("=" * 60)
    print()
    
    base_dir = Path(__file__).parent.parent.parent
    
    updated = 0
    for handler_file in HANDLER_FILES:
        file_path = base_dir / handler_file
        if file_path.exists():
            if fix_handler(file_path):
                updated += 1
        else:
            print(f"  ❌ File not found: {file_path}")
    
    print()
    print("=" * 60)
    print(f"✅ Updated {updated} handlers")
    print("=" * 60)

if __name__ == "__main__":
    main()

