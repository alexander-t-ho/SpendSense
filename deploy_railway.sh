#!/bin/bash
# Railway CLI Deployment Script for SpendSense

set -e

echo "🚀 Railway CLI Deployment Script"
echo "=================================="
echo ""

# Check if Railway CLI is available
if command -v railway &> /dev/null; then
    echo "✅ Railway CLI found"
    railway --version
elif command -v npx &> /dev/null; then
    echo "⚠️  Railway CLI not installed globally, will use npx"
    RAILWAY_CMD="npx @railway/cli"
else
    echo "❌ Error: Neither railway CLI nor npx found"
    echo "Please install Railway CLI:"
    echo "  npm install -g @railway/cli"
    echo "  OR"
    echo "  curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

# Use npx if railway command not found
if ! command -v railway &> /dev/null; then
    RAILWAY_CMD="npx @railway/cli"
else
    RAILWAY_CMD="railway"
fi

echo ""
echo "Step 1: Login to Railway"
echo "------------------------"
echo "This will open your browser for authentication..."
$RAILWAY_CMD login

echo ""
echo "Step 2: Initialize/Link Railway Project"
echo "----------------------------------------"
echo "Choose one:"
echo "  1) Create new project"
echo "  2) Link to existing project"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    echo "Creating new Railway project..."
    $RAILWAY_CMD init
elif [ "$choice" == "2" ]; then
    echo "Linking to existing Railway project..."
    $RAILWAY_CMD link
else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo ""
echo "Step 3: Set Environment Variables"
echo "----------------------------------"
echo "Setting CORS_ORIGINS (temporary - update after Vercel deploy)..."
$RAILWAY_CMD variables set CORS_ORIGINS="http://localhost:3000"

read -p "Set JWT_SECRET_KEY? (y/n): " set_jwt
if [ "$set_jwt" == "y" ]; then
    read -p "Enter JWT_SECRET_KEY: " jwt_secret
    $RAILWAY_CMD variables set JWT_SECRET_KEY="$jwt_secret"
fi

echo ""
echo "Step 4: Verify Configuration"
echo "-----------------------------"
echo "Checking railway.json..."
if [ -f "railway.json" ]; then
    echo "✅ railway.json found:"
    cat railway.json
else
    echo "⚠️  railway.json not found, but that's okay - Railway will auto-detect"
fi

echo ""
echo "Step 5: Deploy to Railway"
echo "-------------------------"
echo "Starting deployment..."
$RAILWAY_CMD up

echo ""
echo "Step 6: Get Deployment URL"
echo "--------------------------"
echo "Your Railway service URL:"
$RAILWAY_CMD domain

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Copy your Railway URL from above"
echo "2. Deploy frontend to Vercel"
echo "3. Update CORS_ORIGINS with your Vercel URL:"
echo "   $RAILWAY_CMD variables set CORS_ORIGINS=\"http://localhost:3000,https://your-vercel-app.vercel.app\""
echo ""
echo "View logs: $RAILWAY_CMD logs"
echo "Open dashboard: $RAILWAY_CMD open"

