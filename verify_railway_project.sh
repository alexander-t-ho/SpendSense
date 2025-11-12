#!/bin/bash
# Script to verify which Railway project has the SpendSense backend

set -e

BACKEND_URL="https://web-production-d242.up.railway.app"
PROJECT_NAME="Leafly"

echo "🔍 Verifying Railway Project"
echo "============================"
echo ""
echo "Expected Backend URL: ${BACKEND_URL}"
echo "Checking project: ${PROJECT_NAME}"
echo ""

# Check if Railway is linked
if ! railway status &> /dev/null; then
    echo "⚠️  Railway project not linked."
    echo ""
    echo "To verify the project:"
    echo "1. Run: railway link"
    echo "2. Select: ${PROJECT_NAME}"
    echo "3. Then run: railway domain"
    echo "4. Check if the domain matches: ${BACKEND_URL}"
    echo ""
    exit 1
fi

echo "✅ Railway project is linked"
echo ""

# Get current project info
echo "📋 Current Project Info:"
railway status 2>&1
echo ""

# Get domain
echo "🌐 Service Domain:"
railway domain 2>&1 || echo "  (could not get domain)"
echo ""

# Check if domain matches
DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' | head -1 || echo "")
if [ ! -z "$DOMAIN" ]; then
    if [[ "$DOMAIN" == *"web-production-d242"* ]]; then
        echo "✅ MATCH! This project has the correct backend URL"
        echo "   Domain: ${DOMAIN}"
    else
        echo "⚠️  Domain doesn't match expected URL"
        echo "   Found: ${DOMAIN}"
        echo "   Expected: ${BACKEND_URL}"
    fi
else
    echo "⚠️  Could not determine domain automatically"
    echo "   Please check manually in Railway dashboard"
fi

echo ""
echo "📋 Current Environment Variables:"
railway variables 2>&1 | head -20

