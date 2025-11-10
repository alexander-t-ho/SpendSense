#!/bin/bash
# Alternative method to upload database to Railway volume
# This script provides multiple options if railway link doesn't work

set -e

DB_FILE="data/spendsense.db"
RAILWAY_DB_PATH="/app/data/spendsense.db"

echo "=== Railway Database Upload (Volume Method) ==="
echo ""

# Check if database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "❌ Error: Database file not found at $DB_FILE"
    exit 1
fi

echo "✅ Database file found: $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"
echo ""

# Method 1: Try with Railway CLI using project/service flags
echo "Method 1: Using Railway CLI with explicit project/service..."
echo ""

# Check if we can use railway without linking
if command -v railway &> /dev/null; then
    echo "Attempting to upload using Railway CLI..."
    echo "Note: If this fails, you may need to:"
    echo "  1. Create volume via Railway Dashboard first"
    echo "  2. Use Method 2 (manual upload via dashboard)"
    echo ""
    
    # Try to upload directly (this might work if project is already linked via .railway folder)
    if railway run sh -c "mkdir -p /app/data && cat > $RAILWAY_DB_PATH" < "$DB_FILE" 2>&1; then
        echo "✅ Database uploaded successfully via Railway CLI!"
        echo ""
        echo "Verifying upload..."
        railway run sqlite3 "$RAILWAY_DB_PATH" "SELECT COUNT(*) as user_count FROM users;" 2>&1 || echo "⚠️  Could not verify (sqlite3 might not be installed in Railway container)"
        exit 0
    else
        echo "⚠️  Railway CLI upload failed. Trying alternative methods..."
        echo ""
    fi
else
    echo "⚠️  Railway CLI not found. Skipping CLI method."
    echo ""
fi

# Method 2: Provide manual instructions
echo "=== Method 2: Manual Upload via Railway Dashboard ==="
echo ""
echo "Since Railway CLI linking is problematic, use the dashboard:"
echo ""
echo "STEP 1: Create Volume in Railway Dashboard"
echo "  1. Go to: https://railway.app/dashboard"
echo "  2. Select your project"
echo "  3. Select your backend service"
echo "  4. Go to 'Volumes' tab"
echo "  5. Click 'Create Volume'"
echo "  6. Name: 'data'"
echo "  7. Mount Path: '/app/data'"
echo "  8. Size: 1GB (or more if needed)"
echo "  9. Click 'Create'"
echo ""
echo "STEP 2: Set Environment Variable"
echo "  1. In your service, go to 'Variables' tab"
echo "  2. Add new variable:"
echo "     Key: DATABASE_URL"
echo "     Value: sqlite:////app/data/spendsense.db"
echo "  3. Save"
echo ""
echo "STEP 3: Upload Database File"
echo "  After volume is created, you can:"
echo ""
echo "  Option A: Use Railway Shell"
echo "    railway shell"
echo "    # Then in the shell:"
echo "    mkdir -p /app/data"
echo "    # Then copy/paste the database file content or use scp"
echo ""
echo "  Option B: Use Railway Run (if project is accessible)"
echo "    railway run sh -c 'cat > /app/data/spendsense.db' < data/spendsense.db"
echo ""
echo "  Option C: Use Railway's file upload feature (if available)"
echo "    Check Railway dashboard for file upload options"
echo ""
echo "STEP 4: Restart Service"
echo "  After uploading, restart your Railway service to pick up the new database"
echo ""

# Method 3: Provide Python script alternative
echo "=== Method 3: Python Script to Upload ==="
echo ""
echo "You can also create a Python script that uploads via Railway's API:"
echo "  See: scripts/upload_db_via_api.py (if it exists)"
echo ""

echo "=== Current Database Info ==="
echo "Local database: $DB_FILE"
sqlite3 "$DB_FILE" "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as accounts FROM accounts; SELECT COUNT(*) as transactions FROM transactions;" 2>/dev/null || echo "Could not read database stats"
echo ""

echo "Once uploaded, verify with:"
echo "  curl https://web-production-ebdc6.up.railway.app/api/stats"
echo ""

