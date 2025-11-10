#!/bin/bash
# Complete Railway CORS setup script for SpendSense
# This script will verify the project and set CORS_ORIGINS

set -e

VERCEL_URL="https://spend-sense-o3df.vercel.app"
BACKEND_URL="https://web-production-d242.up.railway.app"
CORS_VALUE="http://localhost:3004,${VERCEL_URL}"
PROJECT_NAME="respectful-surprise"

echo "🔧 SpendSense Railway CORS Setup"
echo "================================="
echo ""
echo "Vercel URL: ${VERCEL_URL}"
echo "Backend URL: ${BACKEND_URL}"
echo "CORS_ORIGINS: ${CORS_VALUE}"
echo ""

# Step 1: Check if Railway is linked
if ! railway status &> /dev/null; then
    echo "⚠️  Railway project not linked."
    echo ""
    echo "Step 1: Link Railway Project"
    echo "----------------------------"
    echo "Please run this command and select '${PROJECT_NAME}':"
    echo "   railway link"
    echo ""
    echo "When prompted, select option 4 (${PROJECT_NAME})"
    echo ""
    echo "After linking, run this script again:"
    echo "   ./setup_railway_complete.sh"
    echo ""
    exit 1
fi

echo "✅ Step 1: Railway project is linked"
echo ""

# Step 2: Verify domain
echo "Step 2: Verifying Backend Domain"
echo "---------------------------------"
DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' | head -1 || echo "")
if [ ! -z "$DOMAIN" ]; then
    echo "Found domain: ${DOMAIN}"
    if [[ "$DOMAIN" == *"web-production-d242"* ]] || [[ "$DOMAIN" == *"d242"* ]]; then
        echo "✅ Domain matches expected backend URL!"
    else
        echo "⚠️  Warning: Domain doesn't match expected backend URL"
        echo "   Expected: ${BACKEND_URL}"
        echo "   Found: ${DOMAIN}"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted. Please link to the correct project."
            exit 1
        fi
    fi
else
    echo "⚠️  Could not determine domain automatically"
    echo "   Please verify manually that this is the correct project"
fi
echo ""

# Step 3: Show current CORS
echo "Step 3: Current CORS_ORIGINS"
echo "----------------------------"
CURRENT_CORS=$(railway variables 2>&1 | grep -i CORS_ORIGINS || echo "")
if [ ! -z "$CURRENT_CORS" ]; then
    echo "Current: ${CURRENT_CORS}"
else
    echo "Current: (not set)"
fi
echo ""

# Step 4: Set CORS
echo "Step 4: Setting CORS_ORIGINS"
echo "----------------------------"
echo "Setting to: ${CORS_VALUE}"
railway variables --set "CORS_ORIGINS=${CORS_VALUE}"

echo ""
echo "✅ CORS_ORIGINS updated successfully!"
echo ""

# Step 5: Verify
echo "Step 5: Verification"
echo "--------------------"
NEW_CORS=$(railway variables 2>&1 | grep -i CORS_ORIGINS || echo "")
if [ ! -z "$NEW_CORS" ]; then
    echo "✅ Verified: ${NEW_CORS}"
else
    echo "⚠️  Warning: Could not verify CORS_ORIGINS was set"
fi
echo ""

echo "🎉 Setup Complete!"
echo ""
echo "⚠️  IMPORTANT: Restart your Railway service for changes to take effect!"
echo ""
echo "You can restart it:"
echo "  1. In Railway dashboard: Go to your service → Click 'Restart'"
echo "  2. Or redeploy: railway up"
echo ""
echo "After restarting, test your backend:"
echo "  curl ${BACKEND_URL}/"
echo ""
echo "Then test login from your Vercel frontend:"
echo "  ${VERCEL_URL}"

