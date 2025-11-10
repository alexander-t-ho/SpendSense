#!/bin/bash
# Script to update Railway CORS with Vercel URL

set -e

echo "🔧 Railway CORS Update Script"
echo "=============================="
echo ""

# Get Vercel production URL
VERCEL_URL=$(vercel ls --prod 2>&1 | grep "Ready" | head -1 | awk '{print $2}' | sed 's|https://||' | sed 's|http://||')

if [ -z "$VERCEL_URL" ]; then
    echo "❌ Could not determine Vercel URL automatically"
    echo "Please provide your Vercel production URL:"
    read -p "Vercel URL (e.g., spend-sense-xxx.vercel.app): " VERCEL_URL
fi

VERCEL_FULL_URL="https://${VERCEL_URL}"

echo "📍 Vercel URL: $VERCEL_FULL_URL"
echo ""

# Check if Railway is linked
if ! railway status &> /dev/null; then
    echo "⚠️  Railway project not linked. Please link it first:"
    echo "   railway link"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Get current CORS_ORIGINS
echo "📋 Current CORS_ORIGINS:"
railway variables get CORS_ORIGINS 2>&1 || echo "  (not set)"
echo ""

# Update CORS_ORIGINS
echo "🔄 Updating CORS_ORIGINS..."
railway variables set CORS_ORIGINS="http://localhost:3004,${VERCEL_FULL_URL}"

echo ""
echo "✅ CORS updated successfully!"
echo ""
echo "Updated CORS_ORIGINS to include:"
echo "  - http://localhost:3004 (local dev)"
echo "  - ${VERCEL_FULL_URL} (Vercel production)"
echo ""
echo "Your Railway backend should now accept requests from Vercel!"

