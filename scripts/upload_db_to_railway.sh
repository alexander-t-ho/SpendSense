#!/bin/bash
# Script to upload database to Railway using Railway CLI

set -e

DB_FILE="data/spendsense.db"
RAILWAY_DB_PATH="data/spendsense.db"

echo "Uploading database to Railway..."

# Check if database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file not found at $DB_FILE"
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Error: Railway CLI not found. Install it with: npm i -g @railway/cli"
    exit 1
fi

# Check if linked to Railway project
if ! railway status &> /dev/null; then
    echo "Linking to Railway project..."
    railway link
fi

echo "Copying database to Railway..."
echo "Note: Railway uses persistent volumes. The database will be stored at: $RAILWAY_DB_PATH"

# Use Railway CLI to copy the file
# Railway volumes are mounted, so we can use railway run to copy files
railway run sh -c "mkdir -p data && cat > $RAILWAY_DB_PATH" < "$DB_FILE"

echo "✅ Database uploaded successfully!"
echo ""
echo "Next steps:"
echo "1. Restart your Railway service to use the new database"
echo "2. Verify users: curl https://web-production-ebdc6.up.railway.app/api/stats"

